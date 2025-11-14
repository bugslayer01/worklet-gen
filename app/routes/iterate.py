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
import aiofiles


MAX_MODEL_ATTEMPTS = 10


router = APIRouter(prefix="/iterate", tags=["iterate"])


STRING_FIELDS = {
    "title",
    "problem_statement",
    "description",
    "challenge_use_case",
    "deliverables",
    "infrastructure_requirements",
    "tech_stack",
}

ARRAY_FIELDS = {"kpis", "prerequisites"}

OBJECT_FIELDS = {"milestones"}

ALL_FIELDS = STRING_FIELDS | ARRAY_FIELDS | OBJECT_FIELDS


class IterateRequest(BaseModel):
    worklet_id: str = Field(
        ..., description="Unique identifier for the worklet to iterate"
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
    field_name: str, field_payload: dict, target_index: int
) -> object:
    iterations = field_payload.get("iterations", [])
    if not iterations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Field '{field_name}' has no iterations available.",
        )

    if target_index < 0 or target_index >= len(iterations):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Index {target_index} is out of range for field '{field_name}'.",
        )

    return deepcopy(iterations[target_index])


def _hydrate_worklet(
    worklet_record: dict, override_field: str, override_index: int
) -> Worklet:
    raw_reasoning = worklet_record.get("reasoning", "")
    if isinstance(raw_reasoning, dict):
        raw_reasoning = _extract_iteration_value(
            "reasoning",
            raw_reasoning,
            raw_reasoning.get("selected_index", 0),
        )
    elif raw_reasoning is None:
        raw_reasoning = ""

    payload = {
        "worklet_id": worklet_record["worklet_id"],
        "references": deepcopy(worklet_record.get("references", [])),
        "reasoning": (
            raw_reasoning if isinstance(raw_reasoning, str) else str(raw_reasoning)
        ),
    }

    for field_name in ALL_FIELDS:
        field_payload = worklet_record.get(field_name)
        if field_payload is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Field '{field_name}' is missing from the worklet record.",
            )

        if field_name == override_field:
            selected_index = override_index
        else:
            selected_index = field_payload.get("selected_index", 0)

        payload[field_name] = _extract_iteration_value(
            field_name, field_payload, selected_index
        )

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
        {"worklets": 1},
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

    if payload.field not in worklet_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{payload.field}' does not exist on the worklet.",
        )

    _ = _extract_iteration_value(
        payload.field, worklet_record[payload.field], payload.index
    )

    worklet = _hydrate_worklet(worklet_record, payload.field, payload.index)

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

    field_payload = worklet_record[payload.field]
    existing_iterations = field_payload.get("iterations", [])
    existing_iterations = list(existing_iterations)
    updated_iterations = [*existing_iterations, new_value]
    updated_index = len(updated_iterations) - 1

    update_result = db.threads.update_one(
        {"_id": thread["_id"], "worklets.worklet_id": payload.worklet_id},
        {
            "$set": {
                f"worklets.$.{payload.field}.iterations": updated_iterations,
                f"worklets.$.{payload.field}.selected_index": updated_index,
            }
        },
    )

    if update_result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to update the worklet after iteration.",
        )

    return {
        "worklet_id": payload.worklet_id,
        "field": payload.field,
        "selected_index": updated_index,
        "iterations": updated_iterations,
    }
