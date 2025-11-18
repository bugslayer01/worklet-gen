from core.llm.prompts.extraction_prompt import keyword_domain_extraction_prompt
from core.llm.prompts.main_prompt import worklet_generation_prompt
from core.llm.prompts.reference_ranking_prompt import reference_ranking_prompt
from core.llm.prompts.web_search_prompt import web_search_query_planner_prompt
import asyncio
from core.utils.compress_prompt import compress_main_prompt, compress_references
from core.constants import MAX_TOKENS

from pipeline.state import AgentState
from pipeline.tools.search import search_tavily as search_tool
from core.models.worklet import Worklet


async def parallel_search(queries):
    tasks = [search_tool(query, include_favicon=False) for query in queries]
    search_results = await asyncio.gather(*tasks)

    cleaned_results = []
    for idx, query in enumerate(queries):
        if idx < len(search_results) and search_results[idx]:
            res = search_results[idx]

            # Strip unwanted keys
            for r in res.get("results", []):
                r.pop("raw_content", None)
                r.pop("score", None)

            cleaned_results.append(
                {
                    "query": res.get("query", query),
                    "answer": res.get("answer", None),
                    "results": res.get("results", None),
                }
            )
        else:
            # No search result → keep subquery with None values
            cleaned_results.append(
                {
                    "query": query,
                    "answer": None,
                    "results": None,
                }
            )
    return cleaned_results


def build_main_prompt(state: AgentState) -> list:
    modified_state: AgentState = compress_main_prompt(
        state.model_copy(),
        max_tokens=MAX_TOKENS,
        prompt_offset=1100,
        pass_limit=10,
        verbose=True,
    )
    worklet_data = (
        [
            {
                "file_name": doc.file_name,
                "extracted_text": doc.full_text,
            }
            for doc in modified_state.parsed_data.documents
        ]
        if modified_state.parsed_data
        else []
    )
    return worklet_generation_prompt(
        count=modified_state.count,
        keywords=(
            modified_state.keywords_domains.keywords
            if modified_state.keywords_domains
            else []
        ),
        domains=(
            modified_state.keywords_domains.domains
            if modified_state.keywords_domains
            else []
        ),
        custom_prompt=modified_state.custom_prompt or "",
        worklet_data=worklet_data,
        links_data=modified_state.links_data or [],
        web_search_results=modified_state.web_search_results or [],
    )


def build_search_queries_prompt(state: AgentState) -> list:
    modified_state: AgentState = compress_main_prompt(
        state.model_copy(),
        max_tokens=MAX_TOKENS,
        prompt_offset=900,
        pass_limit=10,
        verbose=True,
    )

    worklet_data = (
        [
            {
                "file_name": doc.file_name,
                "extracted_text": doc.full_text,
            }
            for doc in modified_state.parsed_data.documents
        ]
        if modified_state.parsed_data
        else []
    )

    return web_search_query_planner_prompt(
        count=modified_state.count,
        keywords=(
            modified_state.keywords_domains.keywords
            if modified_state.keywords_domains
            else []
        ),
        domains=(
            modified_state.keywords_domains.domains
            if modified_state.keywords_domains
            else []
        ),
        custom_prompt=modified_state.custom_prompt or "",
        worklet_data=worklet_data,
        links_data=modified_state.links_data or [],
    )


def build_extraction_prompt(state: AgentState) -> list:

    modified_state: AgentState = compress_main_prompt(
        state.model_copy(),
        max_tokens=MAX_TOKENS,
        prompt_offset=600,
        pass_limit=10,
        verbose=False,
    )
    worklet_data = (
        [
            {
                "file_name": doc.file_name,
                "extracted_text": doc.full_text,
            }
            for doc in modified_state.parsed_data.documents
        ]
        if modified_state.parsed_data
        else []
    )
    return keyword_domain_extraction_prompt(
        worklet_data=worklet_data,
        links_data=modified_state.links_data,
        custom_prompt=modified_state.custom_prompt,
    )


def build_reference_ranking_prompt(worklet: Worklet) -> list:

    modified_references = compress_references(
        references=worklet.references,
        max_tokens=MAX_TOKENS,
        prompt_offset=400,
        pass_limit=10,
        verbose=False,
    )

    references = {}
    for idx, ref in enumerate(modified_references):
        references[idx] = ref.model_dump()

    return reference_ranking_prompt(
        title=worklet.title, description=worklet.description, references=references
    )
