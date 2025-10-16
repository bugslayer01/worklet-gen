from core.llm.prompts.extraction_prompt import keyword_domain_extraction_prompt
from core.llm.prompts.main_prompt import unified_problem_generation_prompt
import asyncio
from typing import Dict, List

from pipeline.state import AgentState
from pipeline.tools.search import search_tavily as search_tool

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


def build_main_prompt(state: AgentState) -> str:
    worklet_data = (
        [
            {
                "file_name": doc.file_name,
                "extracted_text": doc.full_text,
            }
            for doc in state.parsed_data.documents
        ]
        if state.parsed_data
        else []
    )
    return unified_problem_generation_prompt(
        count=state.count,
        keywords=(
            state.keywords_domains.keywords
            if state.keywords_domains
            else []
        ),
        domains=(
            state.keywords_domains.domains
            if state.keywords_domains
            else []
        ),
        custom_prompt=state.custom_prompt or "",
        worklet_data=worklet_data,
        links_data=state.links_data,
        web_search_used=state.web_search or False,
        web_search_results=(
            state.web_search_results or None if state.web_search else None
        ),
    )


def build_extraction_prompt(state: AgentState) -> str:
    worklet_data = (
        [
            {
                "file_name": doc.file_name,
                "extracted_text": doc.full_text,
            }
            for doc in state.parsed_data.documents
        ]
        if state.parsed_data
        else []
    )
    return keyword_domain_extraction_prompt(
        worklet_data=worklet_data,
        links_data=state.links_data,
        custom_prompt=state.custom_prompt,
    )
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
    # LIMIT CONTEXT ABOVE
