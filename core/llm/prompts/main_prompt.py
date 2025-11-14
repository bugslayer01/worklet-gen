def worklet_generation_prompt(
    worklet_data: list,
    links_data: list,
    web_search_results: list,
    custom_prompt: str,
    keywords: list[str],
    domains: list[str],
    count: int,
):
    """Prompt that focuses purely on generating worklets using the collected context."""

    contents = []

    contents.append(
        {
            "role": "system",
            "parts": (
                "You are an expert **Technology and Innovation Advisor** working with **Samsung PRISM** program - \n\n"
                "an industry-academia initiative linking Samsung R&D teams with Tier 1 and Tier 2 engineering colleges across India.\n\n"
                "Your role is to analyze all the provided data - internal documents, extracted link data, approved web search results and user context, and"
                "generate structured, high-impact project worklets(problem statements/projects) for engineering colleges partnering with Samsung Research Institute."
            ),
        }
    )

    contents.append(
        {
            "role": "system",
            "parts": (
                "### PROVIDED INPUTS\n"
                f"**1. Previous Projects / Worklets:**\n{worklet_data}\n\n"
                f"**2. Data Extracted from External Links:**\n{links_data}\n\n"
                f"**3. Web Search Results:**\n{web_search_results}\n\n"
                f"**4. Custom User Prompt:**\n{custom_prompt}\n\n"
                f"**5. Focus Keywords:** {keywords}\n\n"
                f"**6. Preferred Domains:** {domains}\n\n"
                "Use every relevant insight from the above sources."
            ),
        }
    )

    contents.append(
        {
            "role": "system",
            "parts": (
                "### CONSTRAINTS\n"
                "1. **Value Proposition:** Each project must enable at least one of:\n"
                "   - Commercial proof-of-concept for Samsung\n"
                "   - High-quality research publication opportunity\n"
                "   - Novel, patent-worthy intellectual property\n\n"
                "2. **Feasibility:**\n"
                "   - Projects should be achievable by Tier 1-2 Indian engineering colleges\n"
                "   - Must use moderate infrastructure (open-source tools, limited cloud credits, public datasets)\n\n"
                "3. **Freshness:**\n"
                "   - Highlight 2025-or-newer tools, models, frameworks, datasets, and benchmarks\n"
                "   - Avoid deprecated or outdated approaches\n\n"
                "4. **Structure:** Return valid JSON following the schema below. All text must be plain strings without markdown or commentary.\n\n"
                "```json\n"
                "{\n"
                '  "worklets": [\n'
                "    {\n"
                '      "title": "<concise project title>",\n'
                '      "problem_statement": "<Atleast a 50 word problem summary. Mention why Samsung Research Institute(SRI) should focus on this>",\n'
                '      "description": "<context/background up to 100 words>",\n'
                '      "reasoning": "<LLM rationale behind proposing this idea>",\n'
                '      "challenge_use_case": "<Atleast 2 relevant use cases or scenarios>",\n'
                '      "deliverables": "<expected outputs - app, model, system, dataset, etc. Include domain relevant, top in class and international standard paper publications, conferences, journals or forums. Look for patent possibilities.>",\n'
                '      "kpis": <Mention reasoning behind every KPI and mention SOTA wherever possible>,\n'
                '      "prerequisites": ["<prereq 1>", "<prereq 2>", "<prereq 3>", "<prereq 4>", "<prereq 5>", "<prereq 6>"],\n'
                '      "infrastructure_requirements": "<hardware resources required>",\n'
                '      "tech_stack": "<languages, libraries, APIs, frameworks>",\n'
                '      "milestones": <example output: {"M2": "<checkpoint>", "M4": "<checkpoint>", "M6": "<final deliverable>"}>\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "```"
            ),
        }
    )

    contents.append(
        {
            "role": "user",
            "parts": (
                "Generate exactly "
                f"{count} future-ready project worklets that maximise impact for Samsung Research Institute. "
                "All recommendations must align with the constraints and incorporate the freshest insights from the approved sources."
            ),
        }
    )

    return contents
