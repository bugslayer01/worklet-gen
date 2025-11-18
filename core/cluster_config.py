# Map every externally referenced name to the canonical cluster id below.
_EXTERNAL_MAPPING = {
    "Ai Domain": "ai",
    "AI": "ai",
    "Artificial Intelligence": "ai",
    "Web Search": "web_search",
    "Search": "web_search",
    "Search Engines": "web_search",
    "Vision": "vision",
    "Image Parsing": "vision",
}


# Define each canonical cluster's values once so aliases stay in sync.
_INTERNAL_CLUSTER_IDS = {
    "ai": {
        "keywords": ["genai","rag"],
        "domains": ["artificial intelligence","machine learning"],
    },
    "web_search": {
        "keywords": ["serpapi", "google", "bing", "search"],
        "domains": ["search engines", "web search"],
    },
    "vision": {
        "keywords": ["gemma", "image parsing", "vision model", "ocr"],
        "domains": ["computer vision","image analysis"],
    },
}


# Logic below


# Expose a flat mapping of alias -> cluster terms for existing call sites.
cluster_config = {
    alias: _INTERNAL_CLUSTER_IDS[canonical]
    for alias, canonical in _EXTERNAL_MAPPING.items()
}

# Case-insensitive convenience mapping (keys are lowercased).
cluster_config_ci = {alias.lower(): terms for alias, terms in cluster_config.items()}

# Lowercase helper maps for efficient, case-insensitive lookup.
_EXTERNAL_MAPPING_LOWER = {
    alias.lower(): canonical for alias, canonical in _EXTERNAL_MAPPING.items()
}
_CANONICAL_LOWER = {
    canonical.lower(): terms for canonical, terms in _INTERNAL_CLUSTER_IDS.items()
}


def get_cluster_terms(name: str) -> dict[str, list[str]] | None:
    """Return the cluster terms for any canonical or alias name.

    Lookup is case-insensitive. Accepts either an alias (e.g. 'Ai Domain') or
    a canonical id (e.g. 'ai' or 'web_search'). Returns the canonical cluster
    dict (with keys like 'keywords' and 'domains') or None if not found.
    """
    if not isinstance(name, str):
        return None

    key = name.strip()
    lower = key.lower()

    # Exact alias match (original casing)
    if key in _EXTERNAL_MAPPING:
        return _INTERNAL_CLUSTER_IDS[_EXTERNAL_MAPPING[key]]

    # Case-insensitive alias / canonical lookup
    if lower in _EXTERNAL_MAPPING_LOWER:
        return _INTERNAL_CLUSTER_IDS.get(_EXTERNAL_MAPPING_LOWER[lower])
    # Exact canonical match

    if key in _INTERNAL_CLUSTER_IDS:
        return _INTERNAL_CLUSTER_IDS[key]

    return _CANONICAL_LOWER.get(lower)
