import time
import os
import asyncio

from pipeline.graph_helpers import (
    build_extraction_prompt,
    build_main_prompt,
    build_search_queries_prompt,
    parallel_search,
    build_reference_ranking_prompt,
)
from pipeline.state import AgentState
from core.models.worklet import SimpleDomainsKeywords

# from core.constants import *
from core.utils.generate_files import generate_file
from core.llm.client import invoke_llm
from core.models.worklet import Worklet
from core.llm.outputs import (
    KeywordsExtractionResult,
    WebSearchQueryResult,
    WorkletGenerationResult,
    ReferenceKeywordResult,
    ReferenceSortingResult,
    Sources,
)
from core.references.generate_references import generate_references
from core.constants import SWITCHES
from core.constants import (
    KEYWORD_DOMAIN_EXTRACTION_LLM,
    WORKLET_GENERATOR_LLM,
    REFERENCE_KEYWORD_LLM,
    REFERENCE_RANKING_LLM,
    REFERENCE_KEYWORD_LLM2,
    REFERENCE_RANKING_LLM2,
)
from core.services.upload_files import upload_files
from core.parsers.process_files import process_files
from core.models.document import Documents
from pipeline.tools.extract import extract_links
from core.llm.prompts.reference_keyword_prompt import (
    reference_search_keyword_prompt as keyword_prompt,
)
from core.database import db
from app.socket_handler import sio
from core.utils.get_approved_items import get_approved_items
from core.utils.get_approved_queries import get_approved_queries
from core.utils.fix_dashes import fix_dashes
from app.broadcast import update_message, stop_broadcasting
from core.utils.transform_worklet import transform_worklet
from core.cluster_config import get_cluster_terms

os.makedirs("debug", exist_ok=True)


async def process_input(state: AgentState) -> AgentState:
    s = time.time()

    async def process_files_task():
        if state.files and len(state.files) > 0:
            await update_message(
                {"message": "Uploading and processing files..."},
                topic=f"{state.thread_id}/status_update",
            )
            files_data = await upload_files(state.files, state.thread_id)
            if not files_data:
                print({"error": "No files uploaded or failed to upload files"})
                return None
            print(f"Raw file paths: {files_data}")
            parsed_data: Documents = await process_files(files_data, state.thread_id)
            if not parsed_data.documents:
                print({"error": "No documents could be processed successfully"})
                return None
            return parsed_data
        return None

    async def process_links_task():
        if state.links and len(state.links) > 0:
            await update_message(
                {"message": "Extracting data from links..."},
                topic=f"{state.thread_id}/status_update",
            )
            links_data = await extract_links(state.links)
            if not links_data:
                print(
                    {"error": "No links data extracted or failed to extract links data"}
                )
                return None
            print(f"Extracted links data: {links_data}")
            return links_data
        return None

    # Run both tasks in parallel
    parsed_data, links_data = await asyncio.gather(
        process_files_task(), process_links_task()
    )

    if parsed_data:
        state.parsed_data = parsed_data
    if links_data:
        state.links_data = links_data

    print(f"Input processing took {time.time() - s:.2f} seconds")
    return state


async def extract_keywords_domains(state: AgentState) -> AgentState:
    s = time.time()
    if SWITCHES["EXTRACT_KEYWORDS_DOMAINS"]:
        prompt = build_extraction_prompt(state)

        await update_message(
            {"message": "Extracting keywords and domains..."},
            topic=f"{state.thread_id}/status_update",
        )

        result: KeywordsExtractionResult = await invoke_llm(
            gpu_model=KEYWORD_DOMAIN_EXTRACTION_LLM.model,
            response_schema=KeywordsExtractionResult,
            contents=prompt,
            port=KEYWORD_DOMAIN_EXTRACTION_LLM.port,
        )

    else:
        # Use empty keywords and domains if extraction is disabled
        result = KeywordsExtractionResult(
            keywords=Sources(worklet=[], link=[], custom_prompt=[]),
            domains=Sources(worklet=[], link=[], custom_prompt=[]),
        )

    hardcoded_terms = get_cluster_terms(state.cluster_name)
    if hardcoded_terms:
        for term in hardcoded_terms.get("keywords", []):
            if term not in result.keywords.custom_prompt:
                result.keywords.custom_prompt.append(term)

        for term in hardcoded_terms.get("domains", []):
            if term not in result.domains.custom_prompt:
                result.domains.custom_prompt.append(term)

    updated_domains, updated_keywords = await get_approved_items(
        result.domains.model_dump(), result.keywords.model_dump(), state.thread_id
    )
    result = SimpleDomainsKeywords(domains=updated_domains, keywords=updated_keywords)
    state.keywords_domains = result
    print(f"Keyword extraction took {time.time() - s:.2f} seconds")
    return state


async def generate_web_search_queries(state: AgentState) -> AgentState:
    s = time.time()
    state.web_search = False
    state.web_search_results = []
    state.web_search_queries = []
    prompt = build_search_queries_prompt(state)

    await update_message(
        {"message": "Gathering web search queries..."},
        topic=f"{state.thread_id}/status_update",
    )

    result: WebSearchQueryResult = await invoke_llm(
        gpu_model=WORKLET_GENERATOR_LLM.model,
        response_schema=WebSearchQueryResult,
        contents=prompt,
        port=WORKLET_GENERATOR_LLM.port,
    )

    # Clean queries while preserving order
    cleaned_queries = [q.strip() for q in result.web_search_queries if q.strip()]
    state.web_search_queries = cleaned_queries

    print(
        "Web search query planning produced "
        f"{len(cleaned_queries)} queries in {time.time() - s:.2f} seconds"
    )
    return state


async def generate_worklets(state: AgentState) -> AgentState:
    s = time.time()
    prompt = build_main_prompt(state)

    await update_message(
        {"message": "Generating worklets..."}, topic=f"{state.thread_id}/status_update"
    )

    result: WorkletGenerationResult = await invoke_llm(
        gpu_model=WORKLET_GENERATOR_LLM.model,
        response_schema=WorkletGenerationResult,
        contents=prompt,
        port=WORKLET_GENERATOR_LLM.port,
    )

    state.generation_output = result
    print(f"Worklet generation took {time.time() - s:.2f} seconds")
    return state


async def web_search(state: AgentState) -> AgentState:
    queries = state.web_search_queries or []
    if not queries:
        print("No web search queries were generated; skipping search stage.")
        state.web_search = False
        state.web_search_results = []
        return state

    state.web_search = True
    s = time.time()

    approved_queries = await get_approved_queries(queries, state.thread_id)
    state.web_search_queries = approved_queries

    if not approved_queries:
        print("Approved web search queries list is empty; skipping web search stage.")
        state.web_search = False
        state.web_search_results = []
        return state

    await update_message(
        {"message": "Web search invoked..."}, topic=f"{state.thread_id}/status_update"
    )

    print(f"Performing web search for queries: {approved_queries}")
    web_search_results = await parallel_search(approved_queries)

    state.web_search_results = web_search_results
    print(f"Web search took {time.time() - s:.2f} seconds")
    await update_message(
        {"message": "Web search completed."}, topic=f"{state.thread_id}/status_update"
    )
    return state


async def references(state: AgentState) -> AgentState:
    if not state.generation_output or not state.generation_output.worklets:
        return state

    s = time.time()

    async def process_single_worklet(worklet, llm_config):
        """Process a single worklet with reference keyword generation and fetching"""
        await update_message(
            {"message": f"Generating references for worklet: {worklet.title}..."},
            topic=f"{state.thread_id}/status_update",
        )
        default_keywords = ReferenceKeywordResult(
            google_scholar_keyword=worklet.title, github_keyword=worklet.title
        )

        if SWITCHES["GENERATE_KEYWORD"]:
            prompt = keyword_prompt(worklet.title or worklet.problem_statement)
            try:
                result: ReferenceKeywordResult = await invoke_llm(
                    gpu_model=llm_config.model,
                    contents=prompt,
                    response_schema=ReferenceKeywordResult,
                    port=llm_config.port,
                )
                keywords = result or default_keywords

            except Exception as e:
                print(
                    f"Error extracting reference keyword for worklet '{worklet.title}': {e}"
                )
                keywords = default_keywords
        else:
            keywords = default_keywords

        references = await generate_references(keywords)

        return Worklet(
            **worklet.model_dump(),
            references=references,
            worklet_id=str(time.time()),
        )

    # Parallelize worklet processing, alternating between the two LLM configs
    worklets = state.generation_output.worklets
    tasks = []

    for idx, worklet in enumerate(worklets):
        # Alternate between LLM1 and LLM2 to keep both ports busy
        llm_config = REFERENCE_KEYWORD_LLM if idx % 2 == 0 else REFERENCE_KEYWORD_LLM2
        tasks.append(process_single_worklet(worklet, llm_config))

    # Process all worklets in parallel
    state.worklets = await asyncio.gather(*tasks)

    print(f"Reference generation took {time.time() - s:.2f} seconds")
    return state


async def rank_references(state: AgentState) -> AgentState:
    if not SWITCHES["RANK_REFERENCES"]:
        return state

    s = time.time()

    async def rank_single_worklet(worklet, llm_config):
        """Rank references for a single worklet"""
        try:
            await update_message(
                {"message": f"Ranking references for worklet: {worklet.title}..."},
                topic=f"{state.thread_id}/status_update",
            )
            if not worklet.references or len(worklet.references) == 0:
                return worklet

            prompt = build_reference_ranking_prompt(worklet)

            result: ReferenceSortingResult = await invoke_llm(
                gpu_model=llm_config.model,
                response_schema=ReferenceSortingResult,
                contents=prompt,
                port=llm_config.port,
            )

            sorted_indices = result.sorted_indices
            sorted_references = [
                worklet.references[i]
                for i in sorted_indices
                if i < len(worklet.references)
            ]
            worklet.references = sorted_references
            worklet = fix_dashes(worklet)
            print(f"Ranked references for worklet '{worklet.title}': {sorted_indices}")
            return worklet
        except Exception as e:
            print(f"Error ranking references for worklet '{worklet.title}': {e}")
            # Return worklet unchanged if ranking fails
            return worklet

    try:
        # Parallelize ranking, alternating between the two ranking LLM configs
        tasks = []
        for idx, worklet in enumerate(state.worklets):
            # Alternate between RANKING_LLM1 and RANKING_LLM2 to keep both ports busy
            llm_config = (
                REFERENCE_RANKING_LLM if idx % 2 == 0 else REFERENCE_RANKING_LLM2
            )
            tasks.append(rank_single_worklet(worklet, llm_config))

        # Process all rankings in parallel
        state.worklets = await asyncio.gather(*tasks)

        print(f"Reference ranking took {time.time() - s:.2f} seconds")
    except Exception as e:
        print(f"Error in rank_references function: {e}")
        print("Continuing without ranking references.")
        # Leave all references unchanged

    return state


async def generate_files(state: AgentState) -> AgentState:

    if not state.worklets or len(state.worklets) == 0:
        return state

    # update the worklet files in the db
    db.threads.update_one(
        {"thread_id": state.thread_id},
        {
            "$set": {
                "worklets": [transform_worklet(w.model_dump()) for w in state.worklets]
            }
        },
    )

    s = time.time()
    for idx, worklet in enumerate(state.worklets):
        await generate_file(worklet=worklet, thread_id=state.thread_id)

    print(f"{idx + 1} File generation took {time.time() - s:.2f} seconds")
    db.threads.update_one({"thread_id": state.thread_id}, {"$set": {"generated": True}})
    return state
