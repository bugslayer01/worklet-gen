import requests
import time

from core.models.worklet import Reference


def get_github_references(keyword):
    url = "https://api.github.com/search/repositories"
    params = {"q": keyword, "per_page": 10}

    def make_request():
        try:
            return requests.get(url, params=params, timeout=10)
        except requests.RequestException:
            return None

    # Try a couple of times with a short backoff
    retries = 2
    backoff = 1
    response = None
    data = {}
    for attempt in range(retries):
        response = make_request()
        if response is None:
            time.sleep(backoff)
            continue
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                data = {}
            break
        # not a 200, wait and retry
        time.sleep(backoff)

    # If we never got a successful response, return empty list safely
    if response is None or response.status_code != 200:
        return []

    result = []
    for item in data.get("items", []):
        description = item.get("description") or ""
        if description:
            description = slice_to_100_words(description)
        result.append(
            Reference(
                title=item.get("name", ""),
                description=description,
                link=item.get("html_url", ""),
                tag="github",
            )
        )

    return result


def slice_to_100_words(text):
    words = text.split()
    if len(words) <= 100:
        return text
    else:
        return " ".join(words[:100])
