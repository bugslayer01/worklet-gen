def web_search_decision_prompt(
    worklet_data: str,
    links_data: str,
    custom_prompt: str,
    keywords: str,
    domains: str,
):
    """
    Builds a structured system prompt that helps decide whether a web search is required
    for contextual enrichment when generating new Samsung PRISM problem statements.
    """

    contents = []

    # === ROLE & CONTEXT ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "You are an expert **Technology and Innovation Advisor** working for **Samsung PRISM** — "
                "an industry-academia collaboration initiative connecting Samsung R&D teams with Tier 1 and Tier 2 "
                "engineering colleges across India.\n\n"
                "Your role is to analyze the provided data sources and determine whether **a web search is required** "
                "to enrich, validate, or clarify the available information before generating problem statements."
            ),
        }
    )

    # === INPUT DATA ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### Provided Inputs\n"
                f"**1. Previous project References:**\n{worklet_data}\n\n"
                f"**2. Extracted Data from External Links:**\n{links_data}\n\n"
                f"**3. Custom User Prompt:**\n{custom_prompt}\n\n"
                f"**4. Previously Extracted Keywords:**\n{keywords}\n\n"
                f"**5. Previously Identified Domains:**\n{domains}\n"
            ),
        }
    )

    # === INFORMATION GATHERING & WEB SEARCH LOGIC ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### INFORMATION GATHERING\n"
                "You may use **internal knowledge** and the **provided materials** to reason and generate insights.\n\n"
                "However, if any **gap, ambiguity, or outdated information** is detected — especially regarding "
                "keywords, domains, or the custom prompt — you **must trigger a web search** to obtain the most recent data.\n\n"
                "**Default bias:** When in doubt, prefer to trigger a web search.\n\n"
                "You may use web searches to clarify or enrich:\n"
                "- Missing or unclear technical terms\n"
                "- Outdated tools, frameworks, or datasets\n"
                "- New trends, models, or standards relevant to the domains\n"
                "- 2025+ innovations or updates in the field\n"
                "- Missing contextual understanding of the user’s intent\n"
            ),
        }
    )

    # === DECISION PATHWAYS ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### DECISION PATHWAYS\n\n"
                "**Option 1 — Sufficient Information Available:**\n"
                "If the provided documents and internal knowledge are adequate for generating innovative, "
                "current, and relevant problem statements:\n\n"
                "```json\n"
                "{\n"
                "  \"websearch\": false\n"
                "}\n"
                "```\n\n"
                "**Option 2 — External Information Needed:**\n"
                "If you identify any missing or unclear information requiring external validation or enrichment, "
                "return a structured JSON response listing targeted web queries:\n\n"
                "```json\n"
                "{\n"
                "  \"websearch\": true,\n"
                "  \"search\": [\n"
                "    \"<search query 1>\",\n"
                "    \"<search query 2>\",\n"
                "    \"<search query 3>\"\n"
                "  ]\n"
                "}\n"
                "```\n\n"
                "You may include as many queries as necessary to comprehensively cover all gaps."
            ),
        }
    )

    # === CONSTRAINTS ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### MANDATORY CONSTRAINTS\n"
                "1. **Value Proposition** — Each eventual problem statement derived from this step must enable at least one of:\n"
                "   - A **Commercial PoC** opportunity for Samsung\n"
                "   - A **Publishable research paper**\n"
                "   - A **Viable patent filing**\n\n"
                "2. **Feasibility** —\n"
                "   - Should be **achievable by Tier 1-2 Indian engineering colleges**.\n"
                "   - Should rely on **moderate infrastructure** (e.g., open-source tools, limited cloud credits, public datasets).\n\n"
                "3. **Web Enrichment Requirement** —\n"
                "   - When possible, supplement information using the **latest (2025 or newer)** tools, models, frameworks, APIs, and benchmarks.\n"
                "   - If uncertain about a keyword, technology, or trend, trigger a web search.\n\n"
                "4. **Freshness** —\n"
                "   - Ensure all references and technologies are aligned with **current industry and research standards**.\n"
                "   - Avoid outdated methodologies unless explicitly required.\n\n"
                "5. **Query Design Freedom** —\n"
                "   - Formulate as many web search queries as necessary.\n"
                "   - Each query should target a **specific gap or enrichment opportunity**.\n"
            ),
        }
    )

    # === FINAL USER REQUEST ===
    contents.append(
        {
            "role": "user",
            "parts": (
                "Based on the provided information, determine whether a web search is required. "
                "If so, output the structured JSON with relevant, specific search queries. "
                "Otherwise, indicate that no search is needed. "
                "Return the response in **strict JSON format only**, with no extra text or commentary."
            ),
        }
    )

    return contents
