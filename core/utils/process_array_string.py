from typing import Optional, Union, List, Sequence
import json
import re


def process_array_string(
    input_data: Optional[Union[str, List[str]]],
    separators: Optional[Sequence[str]] = None,
    dedupe: bool = False,
) -> List[str]:
    """Normalize an input (string or list) to a list of non-empty strings.

    The function accepts:
    - None -> returns []
    - list[str] -> trims items and filters out empty items
    - str -> attempts to parse as JSON first. If JSON parsing succeeds and
      yields a list or a single string, those values are used. Otherwise the
      string is split using the provided separators (default: comma, newline,
      semicolon) and trimmed.

    Parameters:
    - input_data: optional string or list of strings
    - separators: optional sequence of separator strings; if None defaults to
      [',', '\n', ';']
    - dedupe: if True, remove duplicate entries while preserving first-occurrence order

    Returns: a list of trimmed, non-empty strings.
    """
    if input_data is None:
        return []

    # Normalise separators
    if separators is None:
        separators = [",", "\n", ";"]

    def _clean_item(x: object) -> Optional[str]:
        if x is None:
            return None
        s = str(x).strip()
        return s if s != "" else None

    items: List[str] = []

    # If already a list/tuple, process elements
    if isinstance(input_data, (list, tuple)):
        for el in input_data:
            # If an element itself is a string that looks like a delimited list,
            # split it further (e.g. ["a,b", "c"]) — helps generalization.
            if isinstance(el, str) and any(sep in el for sep in separators):
                # reuse string-handling logic below by setting s and falling
                # through
                s = el
                # split
                pattern = "|".join(re.escape(sep) for sep in separators)
                parts = re.split(pattern, s)
                for p in parts:
                    c = _clean_item(p)
                    if c:
                        items.append(c)
            else:
                c = _clean_item(el)
                if c:
                    items.append(c)
        if dedupe:
            seen = set()
            out: List[str] = []
            for v in items:
                if v not in seen:
                    seen.add(v)
                    out.append(v)
            return out
        return items

    # Now input_data is a string-like object
    if not isinstance(input_data, str):
        # Fallback: coerce to string
        input_str = str(input_data)
    else:
        input_str = input_data

    input_str = input_str.strip()
    if input_str == "":
        return []

    # Try JSON parsing first (handles JSON arrays and JSON strings)
    try:
        parsed = json.loads(input_str)
        if isinstance(parsed, list):
            for el in parsed:
                c = _clean_item(el)
                if c:
                    items.append(c)
        else:
            # single JSON value (string/number/etc.) -> coerce to one-element list
            c = _clean_item(parsed)
            if c:
                items.append(c)
    except (json.JSONDecodeError, TypeError):
        # Not valid JSON: split using separators
        pattern = "|".join(re.escape(sep) for sep in separators)
        parts = re.split(pattern, input_str)
        for p in parts:
            c = _clean_item(p)
            if c:
                items.append(c)

    if dedupe:
        seen = set()
        out: List[str] = []
        for v in items:
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out

    return items


__all__ = ["process_array_string"]
