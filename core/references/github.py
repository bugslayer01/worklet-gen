import requests
import time

from core.models.worklet import Reference


def get_github_references(keyword):
    url = "https://api.github.com/search/repositories"
    params = {"q": keyword, "per_page": 10}

    def make_request():
        return requests.get(url, params=params)

    response = make_request()

    if response.status_code != 200:
        time.sleep(1)
        response = make_request()

    if response.status_code == 200:
        data = response.json()
    result = []
    for item in data.get("items", []):
        description = item.get("description", "")
        if description:
            description = slice_to_100_words(description)
        else:
            description = ""
        result.append(
            Reference(
                title=item["name"],
                description=description,
                link=item["html_url"],
                tag="github",
            )
        )

        return result
    else:
        return []


def slice_to_100_words(text):
    words = text.split()
    if len(words) <= 100:
        return text
    else:
        return " ".join(words[:100])
