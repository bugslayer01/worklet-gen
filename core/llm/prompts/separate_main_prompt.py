# Not being used currently, but kept for reference
def problem_generation_prompt(
    worklet_data: str,
    links_data: str,
    web_search_used: bool,
    web_results: str,
    custom_prompt: str,
    keywords: str,
    domains: str,
    count: int,
):
    """
    Builds a structured system prompt for generating feasible, high-impact Samsung PRISM
    problem statements using provided data, prior analyses, and user-defined requirements.
    """

    contents = []

    # === ROLE & CONTEXT ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "You are an expert **Technology and Innovation Advisor** for **Samsung PRISM** — "
                "an industry-academia collaboration that connects Samsung R&D teams with Tier 1 and Tier 2 "
                "engineering colleges across India.\n\n"
                "Your task is to **analyze the provided materials** — including internal documents, extracted data, "
                "prior keyword/domain information, and web search results — and generate **precisely defined, feasible project ideas** "
                "aligned with Samsung's research and innovation goals."
            ),
        }
    )

    # === INPUTS PROVIDED ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### INPUTS PROVIDED\n"
                f"**1. Existing Worklets(Projects) for Reference:**\n{worklet_data}\n\n"
                f"**2. Data Extracted from External Links:**\n{links_data}\n\n"
                f"**3. Web Search Results (from previous interactions):**\n{web_results}\n\n"
                f"**4. Keywords:** {keywords}\n\n"
                f"**5. Domains:** {domains}\n\n"
                f"**6. User Prompt (Primary Directive):**\n{custom_prompt}\n\n"
                "If any instruction in the general guidelines conflicts with the user prompt, **the user prompt takes precedence.**"
                "One or more of these sources may not be provided.\n\n"
            ),
        }
    )

    # === DIFFERENTIATION BETWEEN KEYWORDS & DOMAINS ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### KEY DIFFERENTIATION\n"
                "- **Keywords:** Specific technologies, methods, models, or frameworks.\n"
                "  *Examples:* 'federated learning', 'YOLOv8', 'quantization', 'LoRaWAN', 'diffusion models'.\n"
                "- **Domains:** Broad application or research areas.\n"
                "  *Examples:* 'Healthcare', 'Cybersecurity', 'Smart Cities', 'AgriTech', 'EdTech', 'SpaceTech', 'AR/VR', 'Climate Tech'.\n\n"
                "Each generated project problem statement must combine at least one domain with relevant keywords, reflecting real-world innovation potential."
            ),
        }
    )

    # === MANDATORY CONSTRAINTS ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### MANDATORY CONSTRAINTS\n"
                "1. **Domain Focus:**\n"
                f"   - Each project must involve **at least one domain** from: {domains}\n"
                "   - Cross-domain intersections are encouraged.\n"
                "   - Do not introduce unrelated or irrelevant domains.\n\n"
                "2. **Keyword Focus:**\n"
                f"   - Use provided **keywords** ({keywords}) as central elements of each project idea.\n"
                "   - Ensure that the keywords define the core technical approach or method.\n"
                "   - Avoid generic, unrelated, or obsolete terminology.\n\n"
                "3. **Value Proposition:**\n"
                "   - Each project must enable at least one of the following:\n"
                "     • Commercial PoC potential for Samsung\n"
                "     • Publishable academic research\n"
                "     • Patentable novelty\n\n"
                "4. **Feasibility:**\n"
                "   - Must be executable by Tier 1-2 Indian engineering colleges.\n"
                "   - Should use moderate infrastructure: open-source tools, limited cloud credits, GPUs, and public datasets.\n\n"
                "5. **Web Enrichment:**\n"
                "   - Use 2025 (or latest) benchmarks, tools, APIs, and frameworks.\n"
                "   - If uncertain or lacking clarity, trigger a web search.\n"
                "   - Query for multiple related technologies or trends simultaneously if needed.\n\n"
                "6. **Quantity:**\n"
                f"   - Generate **exactly {count} project problem statements**.\n\n"
                "7. **KPIs:**\n"
                "   - Include 3-4 measurable, realistic metrics per problem.\n"
                "   - Examples: “Accuracy ≥ 92%”, “Latency ≤ 200ms”, “Energy reduction ≥ 15%”.\n\n"
                "8. **Freshness:**\n"
                "   - Use cutting-edge frameworks, models, and datasets relevant to 2025 or later.\n"
                "   - Exclude outdated methods unless explicitly justified.\n\n"
                "9. **Prompt Adherence:**\n"
                f"   - The user prompt below overrides any other instruction:\n{custom_prompt}\n\n"
                "10. **Output Validity:**\n"
                "   - Return a **valid JSON only**.\n"
                "   - No additional text, markdown, commentary, or disclaimers.\n"
                "   - Any deviation from the JSON structure renders the output invalid."
            ),
        }
    )

    # === OUTPUT FORMAT SPECIFICATION ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### OUTPUT FORMAT\n"
                "Return your response as a **valid JSON object**:\n\n"
                "```json\n"
                "{\n"
                "  \"worklets\": [\n"
                "    {\n"
                "      \"Title\": \"<one-line title>\",\n"
                "      \"Problem Statement\": \"<28-33 word summary>\",\n"
                "      \"Description\": \"<context/background, max 100 words>\",\n"
                "      \"Challenge / Use Case\": \"<specific pain point or scenario>\",\n"
                "      \"Deliverables\": \"<expected outputs - app, model, system, dataset, etc.>\",\n"
                "      \"KPIs\": [\n"
                "        \"<metric 1>\",\n"
                "        \"<metric 2>\",\n"
                "        \"<metric 3>\",\n"
                "        \"<metric 4>\"\n"
                "      ],\n"
                "      \"Prerequisites\": [\n"
                "        \"<prerequisite 1>\",\n"
                "        \"<prerequisite 2>\",\n"
                "        \"<prerequisite 3>\",\n"
                "        \"<prerequisite 4>\",\n"
                "        \"<prerequisite 5>\",\n"
                "        \"<prerequisite 6>\"\n"
                "      ],\n"
                "      \"Infrastructure Requirements\": \"<minimum and recommended hardware specs>\",\n"
                "      \"Tentative Tech Stack\": \"<languages, libraries, platforms, APIs, etc.>\",\n"
                "      \"Milestones (6 months)\": {\n"
                "        \"M2\": \"<checkpoint>\",\n"
                "        \"M4\": \"<checkpoint>\",\n"
                "        \"M6\": \"<final deliverable>\"\n"
                "      }\n"
                "    }\n"
                "  ]\n"
                "}\n"
                "```\n\n"
                "**Important:** Only output the JSON as specified — no preamble, explanation, or markdown formatting."
            ),
        }
    )

    # === FINAL USER REQUEST ===
    contents.append(
        {
            "role": "user",
            "parts": (
                f"Generate exactly **{count}** feasible, research-aligned, and industry-relevant project problem statements "
                "based on the provided inputs and constraints. "
                "Ensure strict adherence to the JSON schema and no inclusion of extra commentary or markdown."
            ),
        }
    )

    return contents
