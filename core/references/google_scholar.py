from core.models.worklet import Reference
from core.references.scholar_package import CustomGoogleScholarOrganic


def get_google_scholar_references(keyword):
    """
    Fetches references from Google Scholar based on the provided keyword.
    This function uses a custom parser to scrape organic results from Google Scholar.
    It processes the results to extract the title, link, and description of each paper,
    and formats them into a structured list of dictionaries.
    Args:
        keyword (str): The search keyword to query Google Scholar.
    Returns:
        list: A list of dictionaries, where each dictionary contains:
            - "Title" (str): The title of the paper, with certain tags like [PDF], [HTML], and [DOC] removed.
            - "Link" (str): The URL link to the paper.
            - "Description" (str): A brief description of the paper, truncated to 100 words if available.
              If no description is found, a default message is provided.
            - "Tag" (str): A tag indicating the source, set to "scholar".
    Raises:
        Exception: If an error occurs during the scraping process, it is caught and logged,
                   and an empty list is returned.
    """

    try:
        custom_parser_get_organic_results = (
            CustomGoogleScholarOrganic().scrape_google_scholar_organic_results(
                query=keyword, pagination=False, save_to_csv=False, save_to_json=False
            )
        )

        result = []
        for i in custom_parser_get_organic_results:
            title = i.get("title", "")
            title = (
                title.replace("[PDF]", "").replace("[HTML]", "").replace("[DOC]", "")
            )
            description = i.get("snippet", "")
            if description:
                description = slice_to_100_words(description)
            else:
                description = "Did not find any description for this paper just sort them as you see fit try to keep one with tag scholar in front"
            result.append(
                Reference(
                    title=title,
                    link=i.get("title_link", ""),
                    description=description,
                    tag="scholar",
                )
            )
        return result

    except Exception as e:
        print(f"Error while fetching Google Scholar references: {e}")
        return []


def slice_to_100_words(text):
    words = text.split()
    if len(words) <= 500:
        return text
    else:
        return " ".join(words[:500])
