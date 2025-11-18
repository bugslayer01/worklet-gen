from __future__ import annotations

from copy import deepcopy
from typing import Optional

import aiofiles
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.constants import WORKLET_GENERATOR_LLM
from core.database import db
from core.llm.client import invoke_llm
from core.llm.outputs import Worklet as WorkletOutput
from core.llm.prompts.worklet_enhancement_prompt import (
    build_worklet_enhancement_prompt,
)
from core.models.worklet import Worklet
from core.utils.worklet_store import (
    build_iteration_from_worklet,
    iteration_to_worklet,
    upgrade_legacy_worklet_record,
)
from core.utils.fix_dashes import fix_dashes
MAX_MODEL_ATTEMPTS = 10

router = APIRouter(prefix="/worklet-iterations", tags=["worklet-iterations"])


class EnhanceWorkletRequest(BaseModel):
    worklet_id: str = Field(..., description="Identifier of the worklet to enhance")
    worklet_iteration_id: str = Field(
        ..., description="Identifier of the iteration used as the enhancement base"
    )
    prompt: str = Field(
        ..., min_length=1, description="Instruction for the enhancement"
    )


class EnhanceWorkletResponse(BaseModel):
    worklet_id: str
    selected_iteration_index: int
    iteration: dict


class SelectWorkletIterationRequest(BaseModel):
    worklet_id: str = Field(..., description="Identifier of the worklet")
    worklet_iteration_id: str = Field(..., description="Iteration to set as default")


class SelectWorkletIterationResponse(BaseModel):
    success: bool
    worklet_id: str
    selected_iteration_index: int


async def _load_worklet_record(worklet_id: str) -> dict:
    thread = db.threads.find_one(
        {"worklets.worklet_id": worklet_id},
        {"_id": 1, "worklets": 1},
    )

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet not found.",
        )

    worklet_record = next(
        (
            item
            for item in thread.get("worklets", [])
            if item.get("worklet_id") == worklet_id
        ),
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
            {"_id": thread["_id"], "worklets.worklet_id": worklet_id},
            {"$set": {"worklets.$": upgraded}},
        )
        worklet_record = upgraded

    return {"thread_id": thread["_id"], "record": worklet_record}


def _find_iteration(record: dict, iteration_id: str) -> dict:
    iteration = next(
        (
            item
            for item in (record.get("iterations") or [])
            if item.get("iteration_id") == iteration_id
        ),
        None,
    )
    if iteration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet iteration not found.",
        )
    return iteration


def _serialize_iteration(iteration: dict) -> dict:
    payload = deepcopy(iteration)
    created_at = payload.get("created_at")
    if created_at is not None:
        payload["created_at"] = created_at.isoformat()
    return payload


@router.post("/enhance", response_model=EnhanceWorkletResponse)
async def enhance_worklet(payload: EnhanceWorkletRequest):
    payload.prompt = payload.prompt.strip()
    if not payload.prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty.",
        )

    container = await _load_worklet_record(payload.worklet_id)
    thread_id = container["thread_id"]
    worklet_record = container["record"]

    iterations = worklet_record.get("iterations") or []
    base_iteration = _find_iteration(worklet_record, payload.worklet_iteration_id)

    base_worklet: Worklet = iteration_to_worklet(base_iteration)
    enhancement_prompt = build_worklet_enhancement_prompt(
        base_worklet,
        payload.prompt,
    )

    async with aiofiles.open(
        "debug_worklet_enhancement_prompt.json", "w", encoding="utf-8"
    ) as handle:
        await handle.write(enhancement_prompt)

    enhanced_worklet: Optional[WorkletOutput] = None
    last_error: Optional[str] = None

    for attempt in range(1, MAX_MODEL_ATTEMPTS + 1):
        try:
            enhanced_worklet = await invoke_llm(
                gpu_model=WORKLET_GENERATOR_LLM.model,
                response_schema=WorkletOutput,
                contents=enhancement_prompt,
                port=WORKLET_GENERATOR_LLM.port,
            )
            break
        except Exception as exc:
            last_error = f"Attempt {attempt} failed to invoke model: {exc}"

    if enhanced_worklet is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=last_error
            or "Enhancement model failed to produce a valid response.",
        )

    if not isinstance(enhanced_worklet, WorkletOutput):
        enhanced_worklet = fix_dashes(enhanced_worklet)

    new_iteration = build_iteration_from_worklet(
        worklet_record["worklet_id"],
        enhanced_worklet,
        references=base_iteration.get("references", []),
    )

    new_index = len(iterations)

    update_result = db.threads.update_one(
        {"_id": thread_id, "worklets.worklet_id": payload.worklet_id},
        {
            "$push": {"worklets.$.iterations": new_iteration},
            "$set": {"worklets.$.selected_iteration_index": new_index},
        },
    )

    if update_result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to persist new worklet iteration.",
        )

    return EnhanceWorkletResponse(
        worklet_id=payload.worklet_id,
        selected_iteration_index=new_index,
        iteration=_serialize_iteration(new_iteration),
    )


@router.post("/select-default", response_model=SelectWorkletIterationResponse)
async def select_default_iteration(payload: SelectWorkletIterationRequest):
    container = await _load_worklet_record(payload.worklet_id)
    thread_id = container["thread_id"]
    worklet_record = container["record"]

    iterations = worklet_record.get("iterations") or []
    selected_index = next(
        (
            idx
            for idx, iteration in enumerate(iterations)
            if iteration.get("iteration_id") == payload.worklet_iteration_id
        ),
        None,
    )

    if selected_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet iteration not found.",
        )

    update_result = db.threads.update_one(
        {"_id": thread_id, "worklets.worklet_id": payload.worklet_id},
        {"$set": {"worklets.$.selected_iteration_index": selected_index}},
    )

    if update_result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to update the default worklet iteration.",
        )

    return SelectWorkletIterationResponse(
        success=True,
        worklet_id=payload.worklet_id,
        selected_iteration_index=selected_index,
    )
