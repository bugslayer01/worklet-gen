def reference_ranking_prompt(
    title: str,
    description: str,
    references: dict,
):
    """
    Builds a structured system prompt for ranking reference works
    by relevance to a given project idea.

    The model must output ONLY a list of sorted indices in decreasing order of relevance.
    Example: [3, 0, 2, 1]
    """

    contents = []

    # === ROLE & CONTEXT ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "You are an **Expert Technology and Innovation Advisor** for **Samsung PRISM** — "
                "an industry-academia collaboration connecting Samsung R&D teams with Tier 1 and Tier 2 engineering colleges in India.\n\n"
                "Your task is to analyze the given reference works and sort them by **relevance** to the specified project idea."
            ),
        }
    )

    # === INPUT DESCRIPTION ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### INPUTS PROVIDED\n"
                "- A list of **Reference Works**, where each reference includes:\n"
                "  - `Title`\n"
                "  - `Link`\n"
                "  - `Description`\n"
                "  - `Tag`\n"
                "  - `reference_id`\n\n"
                "- A **target project idea** defined by the following:\n"
                f"  **Title:** {title}\n"
                f"  **Description:** {description}\n\n"
                "You must analyze how relevant each reference is to this project idea and then sort them accordingly."
            ),
        }
    )

    # === OUTPUT CONSTRAINTS ===
    contents.append(
        {
            "role": "system",
            "parts": (
                "### MANDATORY OUTPUT CONSTRAINTS\n"
                "1. Produce an array of indices sorted in **decreasing order of relevance**.\n"
                "2. Indices correspond exactly to the order of items in the original input list (0-indexed).\n"
                "3. Do **not** include any explanations, commentary, or additional formatting.\n"
                "Sorting must be in **decreasing order of relevance** — most relevant first."
            ),
        }
    )

    # === INPUT REFERENCES ===
    contents.append(
        {
            "role": "user",
            "parts": (
                f"Here are the references to analyze:\n\n{references}\n\n"
            ),
        }
    )

    return contents
