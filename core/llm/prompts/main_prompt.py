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
                "You are an expert **Technology and Innovation Advisor** specializing in industry-academia collaboration.\n\n"
                "Your role is to analyze all provided data - internal documents, extracted link data, approved web search results, and user context - "
                "and generate structured, high-impact project ideas and problem statements suitable for academic-industry partnerships.\n\n"
                "**Critical Requirement:** For each project, you must first identify the current State-of-the-Art (SOTA) benchmarks, methods, and performance metrics in that problem domain. "
                "Problem statements and KPIs must be explicitly designed to meet or exceed current SOTA standards.\n\n"
                "**Domain Focus:** Prioritize problem statements related to mobile devices, IoT devices, edge computing, and software systems."
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
                "   - Research-focused exploration of novel solutions (not necessarily tied to immediate commercial applications)\n"
                "   - High-quality research publication opportunity\n"
                "   - DO NOT give problem statements related to agriculture, manufacturing, education, retail and defence sector\n"
                "   - Novel, patent-worthy intellectual property\n\n"
                "2. **SOTA Awareness (CRITICAL):**\n"
                "   - Identify current State-of-the-Art methods, benchmarks, and performance metrics for the problem domain\n"
                "   - Problem statements must explicitly aim to match or exceed current SOTA\n"
                "   - All KPIs must be benchmarked against SOTA with clear reasoning for target values\n"
                "   - Include SOTA baselines from recent papers (2024-2025 preferred)\n\n"
                "3. **Feasibility:**\n"
                "   - Projects should be achievable within academic research environments\n"
                "   - Must use accessible infrastructure (open-source tools, reasonable compute resources, public datasets)\n"
                "   - Balance ambition (targeting SOTA) with practical constraints\n\n"
                "4. **Freshness:**\n"
                "   - Highlight 2025-or-newer tools, models, frameworks, datasets, and benchmarks\n"
                "   - Avoid deprecated or outdated approaches\n\n"
                "5. **Structure:** Return valid JSON following the schema below. All text must be plain strings without markdown or commentary. Represent deliverables as an array of strings (no embedded newline characters).\n\n"
                "```json\n"
                "{\n"
                '  "worklets": [\n'
                "    {\n"
                '      "title": "<concise project title>",\n'
                '      "problem_statement": "<At least a 50 word problem summary. Explicitly mention how this aims to advance beyond or match current SOTA. Explain the research significance or industry relevance and why this problem is worth exploring>",\n'
                '      "description": "<context/background up to 100 words>",\n'
                '      "reasoning": "<LLM rationale behind proposing this idea, including how it relates to current SOTA>",\n'
                '      "challenge_use_case": "<At least 2 relevant use cases or scenarios>",\n'
                '      "deliverables": [\n'
                '        "<Expected output such as app, model, system, dataset, etc.>",\n'
                '        "<Domain-relevant top-tier international conferences/journals to target (e.g., NeurIPS, CVPR, ACL, ICML, IEEE journals)>",\n'
                '        "<Patent or commercialization opportunity>",\n'
                '        "<Any additional deliverable>"\n'
                "      ],\n"
                '      "kpis": ["<kpi 1>", "<kpi 2>", "<kpi 3>"...]"<Array of strings with a minimum of 6-7 kpi strings with each string in the following format - "Name: <Metric name>; Measure: <What it measures>; Target: <Target value for this project>; SOTA baseline: <Current SOTA baseline value with source/reference if available>; Reasoning: <Detailed reasoning explaining why this target is ambitious yet achievable and how it compares to SOTA>">",\n'
                '      "prerequisites": ["<prereq 1>", "<prereq 2>", "<prereq 3>", "<prereq 4>", "<prereq 5>", "<prereq 6>"...],\n'
                '      "infrastructure_requirements": "<hardware resources required>",\n'
                '      "tech_stack": "<languages, libraries, APIs, frameworks>",\n'
                '      "milestones": <example output: {"M2": "<checkpoint>", "M4": "<checkpoint>", "M6": "<final deliverable>"}>\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "```\n"
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
