"""Prompt helpers for planning mandatory web search queries."""


def web_search_query_planner_prompt(
    worklet_data: list,
    links_data: list,
    custom_prompt: str,
    keywords: list[str],
    domains: list[str],
    count: int,
):
    """Prompt that asks the LLM to output a curated list of web search queries."""

    contents = []

    contents.append(
        {
            "role": "system",
            "parts": (
                "You are an expert research strategist supporting the Samsung PRISM innovation pipeline. "
                "Your task is to propose the exact web searches the downstream agent should execute before drafting project worklets."
            ),
        }
    )

    contents.append(
        {
            "role": "system",
            "parts": (
                "### AVAILABLE CONTEXT\n"
                f"**1. Previous Projects / Worklets:**\n{worklet_data}\n\n"
                f"**2. Data Extracted from External Links:**\n{links_data}\n\n"
                f"**3. Custom User Prompt:**\n{custom_prompt}\n\n"
                f"**4. Focus Keywords:** {keywords}\n\n"
                f"**5. Preferred Domains:** {domains}\n\n"
                "Use these inputs to infer knowledge gaps or areas needing fresh 2025+ information."
            ),
        }
    )

    contents.append(
        {
            "role": "system",
            "parts": (
                "### INSTRUCTIONS\n"
                "- Return JSON only in the schema shown below.\n"
                "- Recommend specific, non-overlapping queries that would surface the latest benchmarks, datasets, regulations, or breakthroughs.\n"
                "- Tailor each query so it can be executed directly on the public web (use natural phrasing, include the year when helpful).\n"
                "- Balance between Samsung business focus, academic relevance, and implementation feasibility for Indian engineering colleges.\n"
                "- Range: Provide between 3 to 8 queries.\n"
            ),
        }
    )

    contents.append(
        {
            "role": "system",
            "parts": (
                "```json\n"
                "{\n"
                '  "web_search_queries": ["<query 1>", "<query 2>", "<query 3>"]\n'
                "}\n"
                "```\n"
                "Do not include commentary, markdown, or justification outside the array."
            ),
        }
    )

    contents.append(
        {
            "role": "user",
            "parts": (
                "Identify the most valuable web searches needed before writing "
                f"{count} project worklets. Provide only the JSON response."
            ),
        }
    )

    return contents
