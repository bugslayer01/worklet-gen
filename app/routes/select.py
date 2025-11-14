from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.database import db


router = APIRouter(prefix="/select", tags=["select"])


VALID_FIELDS: set[str] = {
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
}


class SelectFieldRequest(BaseModel):
    worklet_id: str = Field(..., description="Identifier of the target worklet")
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
    selected_index: int = Field(
        ..., ge=0, description="Index to select within the iterations array"
    )


@router.post("/", status_code=status.HTTP_200_OK)
async def select_iteration(payload: SelectFieldRequest):
    thread = db.threads.find_one(
        {"worklets.worklet_id": payload.worklet_id},
        {"_id": 1, "worklets": 1},
    )

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet not found.",
        )

    worklet = next(
        (
            w
            for w in thread.get("worklets", [])
            if w.get("worklet_id") == payload.worklet_id
        ),
        None,
    )

    if worklet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worklet not found in thread document.",
        )

    if payload.field not in VALID_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{payload.field}' is not selectable.",
        )

    field_payload = worklet.get(payload.field)
    if field_payload is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Field '{payload.field}' is missing from the stored worklet.",
        )

    iterations = field_payload.get("iterations", [])
    if not iterations:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Field '{payload.field}' has no iterations to select.",
        )

    if payload.selected_index < 0 or payload.selected_index >= len(iterations):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Index {payload.selected_index} is out of bounds for field '{payload.field}'.",
        )

    update_result = db.threads.update_one(
        {"_id": thread["_id"], "worklets.worklet_id": payload.worklet_id},
        {
            "$set": {
                f"worklets.$.{payload.field}.selected_index": payload.selected_index
            }
        },
    )

    if update_result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to update selected index; worklet may have changed.",
        )

    return {
        "success": True,
        "worklet_id": payload.worklet_id,
        "field": payload.field,
        "selected_index": payload.selected_index,
    }
