from copy import deepcopy
from typing import Literal, List

from fastapi import APIRouter, HTTPException
from fastapi import status
from pydantic import BaseModel, Field, ValidationError

from core.database import db
from core.llm.client import invoke_llm
from core.constants import WORKLET_GENERATOR_LLM
from core.llm.prompts.iteration_prompt import build_iteration_prompt
from core.models.worklet import Worklet
from core.utils.worklet_store import (
    STRING_FIELDS as STRING_FIELD_NAMES,
    ARRAY_FIELDS as ARRAY_FIELD_NAMES,
    OBJECT_FIELDS as OBJECT_FIELD_NAMES,
    upgrade_legacy_worklet_record,
    extract_iteration_value as store_extract_iteration_value,
)
from core.utils.fix_dashes import fix_dashes
import aiofiles


MAX_MODEL_ATTEMPTS = 10


router = APIRouter(prefix="/iterate", tags=["iterate"])


STRING_FIELDS = set(STRING_FIELD_NAMES)
ARRAY_FIELDS = set(ARRAY_FIELD_NAMES)
OBJECT_FIELDS = set(OBJECT_FIELD_NAMES)

ALL_FIELDS = STRING_FIELDS | ARRAY_FIELDS | OBJECT_FIELDS


class IterateRequest(BaseModel):
    worklet_id: str = Field(
        ..., description="Unique identifier for the worklet to iterate"
    )
    worklet_iteration_id: str = Field(
        ..., description="Identifier of the worklet iteration being updated"
    )
    field: Literal[
        "title",
        "problem_statement",
        "description",
        "challenge_use_case",
        "deliverables",
        "kpis",
        "prerequisites",
        "infrastructure_requirements",
        "tech_stack",
        "milestones",
    ]
    index: int = Field(
        ..., ge=0, description="Existing iteration index to seed the update"
    )
    prompt: str = Field(
        ..., min_length=1, description="Instruction describing the desired update"
    )


class StringFieldResponse(BaseModel):
    updated_value: str


class ArrayFieldResponse(BaseModel):
    updated_value: List[str]


class ObjectFieldResponse(BaseModel):
    updated_value: dict


def _extract_iteration_value(
    field_name: str, field_payload: dict, target_index: int | None
) -> object:
    try:
        return store_extract_iteration_value(field_payload, index=target_index)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Field '{field_name}' has no iterations available.",
        ) from exc
    except IndexError as exc:
        index_message = (
            str(target_index)
            if target_index is not None
            else str(field_payload.get("selected_index", 0))
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Index {index_message} is out of range for field '{field_name}'.",
        ) from exc


def _hydrate_worklet(
    worklet_id: str, iteration_record: dict, override_field: str, override_index: int
) -> Worklet:
    raw_reasoning = iteration_record.get("reasoning", "")
    if isinstance(raw_reasoning, dict):
        raw_reasoning = _extract_iteration_value(
            "reasoning",
            raw_reasoning,
            raw_reasoning.get("selected_index", 0),
        )
    elif raw_reasoning is None:
        raw_reasoning = ""

    payload = {
        "worklet_id": worklet_id,
        "references": deepcopy(iteration_record.get("references", [])),
        "reasoning": (
            raw_reasoning if isinstance(raw_reasoning, str) else str(raw_reasoning)
        ),
    }

    for field_name in ALL_FIELDS:
        field_payload = iteration_record.get(field_name)
        if field_payload is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Field '{field_name}' is missing from the worklet iteration.",
            )

        selected_index = override_index if field_name == override_field else None

        payload[field_name] = _extract_iteration_value(
            field_name, field_payload, selected_index
        )

        if isinstance(payload, Worklet):
            payload = fix_dashes(payload)

    try:
        return Worklet.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to hydrate worklet payload for iteration.",
        ) from exc


def _resolve_schema_and_description(field_name: str):
    if field_name in STRING_FIELDS:
        return StringFieldResponse, "a concise, high-quality string"
    if field_name in ARRAY_FIELDS:
        return (
            ArrayFieldResponse,
            "an ordered list of meaningful bullet points as strings",
        )
    return (
        ObjectFieldResponse,
        "a JSON object keyed by timeframe with string descriptions",
    )


@router.post("/", status_code=status.HTTP_200_OK)
async def iterate_worklet(payload: IterateRequest):
    thread = db.threads.find_one(
        {"worklets.worklet_id": payload.worklet_id},
        {"_id": 1, "worklets": 1},
    )

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet not found for iteration.",
        )

    worklets = thread.get("worklets", [])
    worklet_record = next(
        (item for item in worklets if item.get("worklet_id") == payload.worklet_id),
        None,
    )

    if worklet_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet not found in thread document.",
        )

    if "iterations" not in worklet_record or not isinstance(
        worklet_record.get("iterations"), list
    ):
        upgraded = upgrade_legacy_worklet_record(worklet_record)
        db.threads.update_one(
            {"_id": thread.get("_id"), "worklets.worklet_id": payload.worklet_id},
            {"$set": {"worklets.$": upgraded}},
        )
        worklet_record = upgraded

    iterations = worklet_record.get("iterations") or []
    if not iterations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No iterations exist for this worklet.",
        )

    iteration_record = next(
        (
            item
            for item in iterations
            if item.get("iteration_id") == payload.worklet_iteration_id
        ),
        None,
    )

    if iteration_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet iteration not found.",
        )

    if payload.field not in iteration_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{payload.field}' does not exist on the worklet iteration.",
        )

    field_payload = iteration_record[payload.field]

    _ = _extract_iteration_value(payload.field, field_payload, payload.index)

    worklet = _hydrate_worklet(
        worklet_record["worklet_id"], iteration_record, payload.field, payload.index
    )

    response_schema, field_description = _resolve_schema_and_description(payload.field)

    iteration_prompt = build_iteration_prompt(
        worklet=worklet,
        field=payload.field,
        field_type_description=field_description,
        user_prompt=payload.prompt,
    )

    async with aiofiles.open("debug_iteration_prompt.json", "w", encoding="utf-8") as f:
        await f.write(iteration_prompt)

    new_value = None
    last_error_detail = None

    for attempt in range(1, MAX_MODEL_ATTEMPTS + 1):
        try:
            llm_response = await invoke_llm(
                gpu_model=WORKLET_GENERATOR_LLM.model,
                response_schema=response_schema,
                contents=iteration_prompt,
                port=WORKLET_GENERATOR_LLM.port,
            )
        except Exception as exc:
            last_error_detail = f"Attempt {attempt} failed to invoke model: {exc}"
            continue

        candidate_value = llm_response.updated_value

        if payload.field in ARRAY_FIELDS:
            if not isinstance(candidate_value, list) or not all(
                isinstance(item, str) for item in candidate_value
            ):
                last_error_detail = f"Attempt {attempt} produced invalid list output for field '{payload.field}'."
                continue
        elif payload.field in STRING_FIELDS:
            if not isinstance(candidate_value, str):
                last_error_detail = f"Attempt {attempt} produced non-string output for field '{payload.field}'."
                continue
        elif payload.field in OBJECT_FIELDS:
            if not isinstance(candidate_value, dict):
                last_error_detail = f"Attempt {attempt} produced non-object output for field '{payload.field}'."
                continue

        new_value = candidate_value
        break

    if new_value is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=last_error_detail
            or "Iteration model failed to produce a valid response after multiple attempts.",
        )

    existing_iterations = field_payload.get("iterations", [])
    existing_iterations = list(existing_iterations)
    updated_iterations = [*existing_iterations, new_value]
    updated_index = len(updated_iterations) - 1

    update_result = db.threads.update_one(
        {"_id": thread["_id"]},
        {
            "$set": {
                f"worklets.$[worklet].iterations.$[iteration].{payload.field}.iterations": updated_iterations,
                f"worklets.$[worklet].iterations.$[iteration].{payload.field}.selected_index": updated_index,
            }
        },
        array_filters=[
            {"worklet.worklet_id": payload.worklet_id},
            {"iteration.iteration_id": payload.worklet_iteration_id},
        ],
    )

    if update_result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to update the worklet after iteration.",
        )

    return {
        "worklet_id": payload.worklet_id,
        "worklet_iteration_id": payload.worklet_iteration_id,
        "field": payload.field,
        "selected_index": updated_index,
        "iterations": updated_iterations,
    }
