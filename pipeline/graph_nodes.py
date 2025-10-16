import json
import time
import os
import aiofiles
import asyncio

from pipeline.graph_helpers import (
    build_extraction_prompt,
    build_main_prompt,
    parallel_search,
)
from pipeline.state import AgentState
from pipeline.tools.search import search_tavily as search_tool
from core.models.worklet import SimpleDomainsKeywords

# from core.constants import *
from core.utils.generate_files import generate_file
from core.llm.client import invoke_llm
from core.models.worklet import Worklet
from core.llm.outputs import (
    KeywordsExtractionResult,
    WorkletGenerationResult,
    ReferenceKeywordResult,
    ReferenceSortingResult,
)
from core.references.generate_references import generate_references
from core.constants import WEB_SEARCH, REFERENCES
from core.constants import (
    KEYWORD_DOMAIN_EXTRACTION_LLM,
    WORKLET_GENERATOR_LLM,
    REFERENCE_KEYWORD_LLM,
    REFERENCE_SORT_LLM,
)
from core.services.upload_files import upload_files
from core.parsers.process_files import process_files
from core.models.document import Documents
from pipeline.tools.extract import extract_links
from core.llm.prompts.reference_sorting_prompt import reference_sorting_prompt
from core.llm.prompts.reference_keyword_prompt import (
    reference_search_keyword_prompt as keyword_prompt,
)
from core.database import db
from app.socket_handler import sio
from core.utils.get_approved_items import get_approved_items
from core.utils.get_approved_queries import get_approved_queries
from core.utils.fix_dashes import fix_dashes
os.makedirs("debug", exist_ok=True)


# parallilize both of these
async def process_input(state: AgentState) -> AgentState:
    print(state.links)
    print(type(state.links))
    print("before this" * 50)
    s = time.time()
    if state.files and len(state.files) > 0:
        await sio.emit(
            "status_update", {"message": "Uploading and processing files..."}
        )
        files_data = await upload_files(state.files, state.thread_id)
        if not files_data:
            print({"error": "No files uploaded or failed to upload files"})
        print(f"Raw file paths: {files_data}")
        parsed_data: Documents = await process_files(files_data, state.thread_id)
        if not parsed_data.documents:
            return {"error": "No documents could be processed successfully"}
        state.parsed_data = parsed_data

    if state.links and len(state.links) > 0:
        await sio.emit("status_update", {"message": "Extracting data from links..."})
        links_data = await extract_links(state.links)
        if not links_data:
            print({"error": "No links data extracted or failed to extract links data"})
        print(f"Extracted links data: {links_data}")
        state.links_data = links_data

    print(f"Input processing took {time.time() - s:.2f} seconds")
    return state


async def extract_keywords_domains(state: AgentState) -> AgentState:
    s = time.time()
    prompt = build_extraction_prompt(state)
    with open("debug/extraction_prompt.txt", "w", encoding="utf-8") as f:
        f.write(str(prompt))

    await sio.emit(
        f"{state.thread_id}/status_update",
        {"message": "Extracting keywords and domains..."},
    )

    result: KeywordsExtractionResult = await invoke_llm(
        gpu_model=KEYWORD_DOMAIN_EXTRACTION_LLM.model,
        response_schema=KeywordsExtractionResult,
        contents=prompt,
        port=KEYWORD_DOMAIN_EXTRACTION_LLM.port,
    )
    with open("debug/keywords_domains.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(result.model_dump(), indent=2))

    updated_domains, updated_keywords = await get_approved_items(
        result.domains.model_dump(), result.keywords.model_dump(), state.thread_id
    )
    result = SimpleDomainsKeywords(domains=updated_domains, keywords=updated_keywords)
    state.keywords_domains = result
    print(f"Keyword extraction took {time.time() - s:.2f} seconds")
    return state


async def generate_worklets(state: AgentState) -> AgentState:
    s = time.time()
    prompt = build_main_prompt(state)

    with open("debug/main_prompt.txt", "w", encoding="utf-8") as f:
        f.write(str(prompt))

    await sio.emit(
        f"{state.thread_id}/status_update", {"message": "Generating worklets..."}
    )

    result: WorkletGenerationResult = await invoke_llm(
        gpu_model=WORKLET_GENERATOR_LLM.model,
        response_schema=WorkletGenerationResult,
        contents=prompt,
        port=WORKLET_GENERATOR_LLM.port,
    )
    with open("debug/worklet_generation.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(result.model_dump(), indent=2))
    state.generation_output = result
    print(f"Worklet generation took {time.time() - s:.2f} seconds")
    return state


async def web_search(state: AgentState) -> AgentState:
    if (
        not state.generation_output.web_search
        or not state.generation_output.web_search_queries
        or len(state.generation_output.web_search_queries) == 0
    ):
        return state

    state.web_search = True
    s = time.time()
    queries = state.generation_output.web_search_queries
    if not queries:
        print("No web search queries provided, skipping web search.")
        return state

    queries = await get_approved_queries(queries, state.thread_id)
    await sio.emit(
        f"{state.thread_id}/status_update", {"message": "Web search invoked..."}
    )

    print(f"Performing web search for queries: {queries}")
    web_search_results = await parallel_search(queries)
    with open("debug/web_search_results.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(web_search_results, indent=2))
    state.web_search_results = web_search_results
    print(f"Web search took {time.time() - s:.2f} seconds")
    await sio.emit(
        f"{state.thread_id}/status_update", {"message": "Web search completed."}
    )
    return state


async def references(state: AgentState) -> AgentState:
    if not state.generation_output or not state.generation_output.worklets:
        return state

    s = time.time()
    for worklet in state.generation_output.worklets:
        await sio.emit(
            f"{state.thread_id}/status_update",
            {"message": f"Generating references for worklet: {worklet.title}..."},
        )
        prompt = keyword_prompt(worklet.title or worklet.problem_statement)
        try:
            result: ReferenceKeywordResult = await invoke_llm(
                gpu_model=REFERENCE_KEYWORD_LLM.model,
                contents=prompt,
                response_schema=ReferenceKeywordResult,
                port=REFERENCE_KEYWORD_LLM.port,
            )
            keywords = result or ReferenceKeywordResult(
                google_scholar_keyword=worklet.title, github_keyword=worklet.title
            )
            with open(
                f"debug/reference_keyword_{worklet.title}.txt", "w", encoding="utf-8"
            ) as f:
                f.write(str(result.model_dump()))
        except Exception as e:
            print(
                f"Error extracting reference keyword for worklet '{worklet.title}': {e}"
            )
            keywords = ReferenceKeywordResult(
                google_scholar_keyword=worklet.title, github_keyword=worklet.title
            )
        references = await generate_references(keywords)
        with open(f"debug/references_{worklet.title}.json", "w", encoding="utf-8") as f:
            f.write(json.dumps([ref.model_dump() for ref in references], indent=2))
        state.worklets.append(
            Worklet(
                **worklet.model_dump(),
                references=references,
                worklet_id=str(time.time()),
            )
        )

    print(f"Reference generation took {time.time() - s:.2f} seconds")
    return state


# remove this for the cpu version
async def sort_references(state: AgentState) -> AgentState:
    for worklet in state.worklets:
        await sio.emit(
            f"{state.thread_id}/status_update",
            {"message": f"Sorting references for worklet: {worklet.title}..."},
        )
        if not worklet.references or len(worklet.references) == 0:
            continue

        references = {}
        for idx, ref in enumerate(worklet.references):
            references[idx] = ref.model_dump()
        prompt = reference_sorting_prompt(
            title=worklet.title, description=worklet.description, references=references
        )

        result: ReferenceSortingResult = await invoke_llm(
            gpu_model=REFERENCE_SORT_LLM.model,
            response_schema=ReferenceSortingResult,
            contents=prompt,
            port=REFERENCE_SORT_LLM.port,
        )
        sorted_indices = result.sorted_indices
        sorted_references = [
            worklet.references[i] for i in sorted_indices if i < len(worklet.references)
        ]
        worklet.references = sorted_references
        worklet = fix_dashes(worklet)
        print(f"Sorted references for worklet '{worklet.title}': {sorted_indices}")
    return state


async def generate_files(state: AgentState) -> AgentState:

    if not state.worklets or len(state.worklets) == 0:
        return state

    # update the worklet files in the db
    db.threads.update_one(
        {"thread_id": state.thread_id},
        {"$set": {"worklets": [w.model_dump() for w in state.worklets]}},
    )

    s = time.time()
    await sio.emit(
        f"{state.thread_id}/status_update",
        {"message": f"Generating files for worklets..."},
    )
    for idx, worklet in enumerate(state.worklets):
        await generate_file(worklet=worklet, thread_id=state.thread_id)
        await sio.emit(
            f"{state.thread_id}/file_generated", {"filename": f"{worklet.title}"}
        )

    print(f"{idx + 1} File generation took {time.time() - s:.2f} seconds")
    db.threads.update_one({"thread_id": state.thread_id}, {"$set": {"generated": True}})
    return state


def router(state: AgentState) -> str:
    if state.generation_output.web_search:
        return WEB_SEARCH
    else:
        return REFERENCES
