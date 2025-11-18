from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from core.models.worklet import Worklet

STRING_FIELDS: tuple[str, ...] = (
    "title",
    "problem_statement",
    "description",
    "challenge_use_case",
    "infrastructure_requirements",
    "tech_stack",
)

ARRAY_FIELDS: tuple[str, ...] = (
    "deliverables",
    "kpis",
    "prerequisites",
)

OBJECT_FIELDS: tuple[str, ...] = ("milestones",)

ITERATABLE_FIELDS: tuple[str, ...] = STRING_FIELDS + ARRAY_FIELDS + OBJECT_FIELDS


def _normalize_array_field(value: Any) -> List[str]:
    """Coerce raw values into a clean list of non-empty strings."""

    if isinstance(value, list):
        items = value
    elif isinstance(value, (tuple, set)):
        items = list(value)
    elif isinstance(value, str):
        # Split on common delimiters while keeping meaningful phrases intact
        splits = re.split(r"[\r\n]+|\s*[;\u2022]\s*", value)
        items = [segment for segment in splits if segment is not None]
    elif value in (None, ""):
        items = []
    else:
        items = [value]

    normalized: List[str] = []
    for item in items:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def build_initial_iteration(worklet_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create an initial worklet iteration from a freshly generated worklet payload."""

    iteration_id = uuid4().hex
    timestamp = datetime.now(tz=timezone.utc)

    iteration: Dict[str, Any] = {
        "iteration_id": iteration_id,
        "created_at": timestamp,
        "worklet_id": worklet_payload.get("worklet_id"),
        "reasoning": str(worklet_payload.get("reasoning", "") or ""),
        "references": deepcopy(worklet_payload.get("references", [])),
    }

    for field in STRING_FIELDS:
        iteration[field] = {
            "selected_index": 0,
            "iterations": [str(worklet_payload.get(field, "") or "")],
        }

    for field in ARRAY_FIELDS:
        value = worklet_payload.get(field)
        iteration[field] = {
            "selected_index": 0,
            "iterations": [_normalize_array_field(value)],
        }

    for field in OBJECT_FIELDS:
        value = worklet_payload.get(field) or {}
        iteration[field] = {
            "selected_index": 0,
            "iterations": [dict(value) if isinstance(value, dict) else {}],
        }

    return iteration


def build_iteration_from_worklet(
    worklet_id: str,
    worklet: Worklet,
    *,
    references: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:
    """Construct a stored iteration from a Worklet model and optional references."""

    payload = worklet.model_dump()
    payload["worklet_id"] = worklet_id
    if references is not None:
        payload["references"] = list(references)

    return build_initial_iteration(payload)


def upgrade_legacy_worklet_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap a legacy worklet record (without iteration container) into the new structure."""

    iteration: Dict[str, Any] = {
        "iteration_id": uuid4().hex,
        "created_at": datetime.now(tz=timezone.utc),
        "worklet_id": record.get("worklet_id"),
        "reasoning": str(record.get("reasoning", "") or ""),
        "references": deepcopy(record.get("references", [])),
    }

    for field in ITERATABLE_FIELDS:
        iteration[field] = deepcopy(record.get(field))

    upgraded = {
        "worklet_id": record.get("worklet_id"),
        "selected_iteration_index": int(record.get("selected_iteration_index", 0)),
        "iterations": [iteration],
    }

    return upgraded


def extract_iteration_value(
    field_payload: Dict[str, Any], index: Optional[int] = None
) -> Any:
    """Return a deepcopy of the requested iteration value from a field payload."""

    iterations = (
        field_payload.get("iterations") if isinstance(field_payload, dict) else None
    )
    if not isinstance(iterations, list) or len(iterations) == 0:
        raise ValueError("Field has no iterations to extract")

    target_index = (
        index if index is not None else int(field_payload.get("selected_index", 0))
    )
    if target_index < 0 or target_index >= len(iterations):
        raise IndexError("Iteration index out of range")

    return deepcopy(iterations[target_index])


def iteration_to_worklet(iteration: Dict[str, Any]) -> Worklet:
    """Hydrate a Worklet model from a stored iteration."""

    payload = {
        "worklet_id": iteration.get("worklet_id", ""),
        "references": deepcopy(iteration.get("references", [])),
        "reasoning": str(iteration.get("reasoning", "") or ""),
    }

    for field in STRING_FIELDS:
        payload[field] = (
            extract_iteration_value(iteration[field]) if field in iteration else ""
        )

    for field in ARRAY_FIELDS:
        payload[field] = _normalize_array_field(
            extract_iteration_value(iteration[field]) if field in iteration else []
        )

    for field in OBJECT_FIELDS:
        payload[field] = (
            extract_iteration_value(iteration[field]) if field in iteration else {}
        )

    return Worklet.model_validate(payload)
