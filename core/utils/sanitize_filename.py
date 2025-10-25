import re


def sanitize_filename(filename: str) -> str:
    """Replace filesystem-unfriendly chars with underscores."""
    return re.sub(r'[\/:*?"<>|]', "_", filename)
