import time
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pipeline.state import AgentState
from core.database import db
from pipeline.builder import Pipeline
from core.utils.process_array_string import process_array_string
from app.broadcast import update_message
from core.utils.transform_worklet import transform_worklet

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/")
async def generate(
    thread_id: Annotated[str, Form()],
    thread_name: Annotated[str, Form()],
    cluster_id: Annotated[str, Form()],
    count: Annotated[int, Form()],
    links: Annotated[str, Form()],
    custom_prompt: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()] = None,
):
    await update_message(
        {"message": "Intializing pipeline..."},
        topic=f"{thread_id}/status_update",
    )
    existing_thread = db.threads.find_one({"thread_id": thread_id})
    if existing_thread:
        # Conflict: a resource with the same thread_id already exists
        raise HTTPException(
            status_code=409,
            detail="Thread ID already exists. Please choose a different ID.",
        )

    cluster = db.clusters.find_one({"cluster_id": cluster_id})
    if not cluster:
        raise HTTPException(
            status_code=404,
            detail="Cluster not found.",
        )

    file_names = [file.filename for file in files] if files else []
    links_array = process_array_string(links) if links else []
    thread_dict = {
        "thread_id": thread_id,
        "thread_name": thread_name,
        "cluster_id": cluster_id,
        "count": count,
        "links": links_array,
        "custom_prompt": custom_prompt,
        "files": file_names,
        "worklets": [],
        "worklet_files": [],
        "generated": False,
        "created_at": datetime.now(),
    }
    print(
        {
            "thread_id": thread_id,
            "thread_name": thread_name,
            "cluster_id": cluster_id,
            "count": count,
            "links": links_array,
            "custom_prompt": custom_prompt,
            "files": files,
        }
    )
    state = AgentState(
        cluster_name=cluster["name"],
        thread_id=thread_id,
        count=count,
        files=files,
        links=links_array,
        custom_prompt=custom_prompt,
    )
    db.threads.insert_one(thread_dict)
    db.clusters.update_one(
        {"cluster_id": cluster_id},
        {"$set": {"updated_at": datetime.now()}},
    )

    start_time = time.time()
    state = await Pipeline.ainvoke(state)
    state = AgentState.model_validate(state)
    end_time = time.time()
    print(f"WORKLET GENERATION COMPLETED: {end_time - start_time:.2f} seconds")

    worklets = (
        [worklet.model_dump() for worklet in state.worklets] if state.worklets else []
    )

    transformed_worklets = [transform_worklet(w) for w in worklets]

    return {
        "thread_id": thread_id,
        "worklets": transformed_worklets,
        "worklet_count": len(transformed_worklets),
    }
