def reference_search_keyword_prompt(input: str):
    """
    Builds a minimal, structured prompt for generating precise search keywords or phrases
    suitable for use in both Google Scholar and GitHub repository searches
    based on a given problem statement/title.
    """

    contents = []

    # === ROLE & INSTRUCTION ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "You are a precise and minimal **keyword generator** that creates search phrases "
                "for both **Google Scholar** (academic research) and **GitHub** (code repositories).\n\n"
                "Your goal is to extract or infer two concise and relevant search phrases based on the given problem statement/title:\n"
                "1. A **Google Scholar keyword** — focusing on the academic or conceptual core (model, framework, or research topic).\n"
                "2. A **GitHub keyword** — focusing on practical implementation terms, frameworks, tools, or code projects related to the topic that might actually turn up useful repositories.\n\n"
            ),
        }
    )

    # === EXAMPLES ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### Example Outputs\n"
                "{\n"
                '  "google_scholar": "self-supervised dialog emotion",\n'
                '  "github": "dialog emotion recognition deep learning"\n'
                "}\n\n"
                "{\n"
                '  "google_scholar": "multilingual large language model",\n'
                '  "github": "multilingual llm open source"\n'
                "}\n\n"
                "{\n"
                '  "google_scholar": "deep packet inspection",\n'
                '  "github": "dpi network monitoring tool"\n'
                "}"
            ),
        }
    )

    # === USER INPUT ===
    contents.append(
        {
            "role": "user",
            "parts": (
                f"Generate the most suitable Google Scholar and GitHub search keywords for this problem statement/title:\n"
                f"'{input}'\n\n"
            ),
        }
    )

    return contents
