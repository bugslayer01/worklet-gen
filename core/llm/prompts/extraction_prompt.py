def keyword_domain_extraction_prompt(
    worklet_data: str,
    links_data: str,
    custom_prompt: str,
):
    """
    Builds a structured system prompt for extracting high-impact keywords and relevant domains
    from multiple sources (existing worklets, data from links, and a custom user prompt)
    in the context of Samsung PRISM's Technology and Innovation initiatives.
    """

    contents = []

    # System Role and Context
    contents.append(
        {
            "role": "system",
            "parts": (
                "You are an expert **Technology and Innovation Advisor** working with **Samsung PRISM**, "
                "an industry-academia collaboration that connects Samsung R&D teams with engineering colleges across India.\n\n"
                "Your goal is to analyze the provided inputs and identify **high-impact technical keywords** and **relevant research or application domains** "
                "from three sources: (1) Existing Projects, (2) Data Extracted from the Links provided, and (3) a Custom User Prompt.\n\n"
                "One or more of these sources may not be provided, return empty lists for them if so.\n\n"
                "You must extract and present this information concisely, accurately, and with strong contextual relevance to innovation and research potential."
            ),
        }
    )

    # Extraction Goals and Rules
    contents.append(
        {
            "role": "system",
            "parts": (
                "### Extraction Objectives\n"
                "**A. Keywords** — Extract concise, high-value keywords that capture:\n"
                "- Technical concepts\n"
                "- Emerging technologies\n"
                "- Problem domains\n"
                "- Solution approaches\n"
                "- Application areas\n\n"
                "**Keyword Rules:**\n"
                "- Each keyword should be **1-3 words** maximum.\n"
                "- Avoid generic or vague terms (e.g., 'project', 'engineering') unless domain-specific.\n"
                "- Avoid repetition unless absolutely essential.\n"
                "- Prioritize novelty, precision, and contextual relevance.\n\n"
                "**B. Domains** — Identify broad, meaningful **application or research domains**, such as (but not limited to):\n"
                "- Generative AI, Healthcare, Smart Cities, AgriTech, FinTech, Cybersecurity, Automotive, EdTech, IoT, Energy, Robotics, ClimateTech, etc.\n\n"
                "**Domain Selection Rules:**\n"
                "- Include any domain that is clearly stated or strongly implied in the custom prompt.\n"
                "- Ensure domains are **specific enough** to indicate the project's purpose or innovation focus.\n"
            ),
        }
    )
    # "- Favor **research- and innovation-oriented** categories.\n"

    # Input Data Sections
    contents.append(
        {
            "role": "system",
            "parts": (
                f"### Provided Inputs\n"
                f"**1. Existing Projects:**\n{worklet_data}\n\n"
                f"**2. Data Extracted from Links:**\n{links_data}\n\n"
                f"**3. Custom User Prompt:**\n{custom_prompt}\n"
            ),
        }
    )

    contents.append(
        {
            "role": "system",
            "parts": (
                "Ensure that:\n"
                "- Keywords and domains are deduplicated.\n"
                "- Each list contains only relevant, high-quality entries.\n"
                "- The response is machine-readable and does not include commentary or extra formatting."
            ),
        }
    )

    # Final User Request
    contents.append(
        {
            "role": "user",
            "parts": (
                "Analyze the inputs carefully and extract the **most relevant keywords and domains** "
                "based on the provided context and rules. "
                "Return the result in the exact JSON format specified."
            ),
        }
    )

    return contents
