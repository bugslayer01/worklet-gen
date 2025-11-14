from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.database import db

router = APIRouter(prefix="/clusters", tags=["clusters"])


class ClusterCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Display name for the cluster")


class ClusterUpdateRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, description="Updated display name for the cluster"
    )


def _normalize_name(name: str) -> str:
    normalized = (name or "").strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cluster name cannot be empty.",
        )
    return normalized


def _generate_cluster_id() -> str:
    """Generate a short, unique cluster identifier."""
    while True:
        candidate = uuid4().hex[:8]
        if not db.clusters.find_one({"cluster_id": candidate}):
            return candidate


def _serialize_cluster(doc: dict) -> dict:
    return {
        "cluster_id": doc.get("cluster_id"),
        "name": doc.get("name"),
        "created_at": (
            doc.get("created_at").isoformat() if doc.get("created_at") else None
        ),
        "updated_at": (
            doc.get("updated_at").isoformat() if doc.get("updated_at") else None
        ),
    }


@router.get("/")
async def list_clusters():
    clusters = db.clusters.find({}).sort("created_at", -1)
    return {"clusters": [_serialize_cluster(cluster) for cluster in clusters]}


@router.get("/{cluster_id}")
async def get_cluster(cluster_id: str):
    cluster = db.clusters.find_one({"cluster_id": cluster_id})
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found"
        )
    return _serialize_cluster(cluster)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_cluster(payload: ClusterCreateRequest):
    name = _normalize_name(payload.name)
    cluster_id = _generate_cluster_id()
    now = datetime.now()
    cluster_doc = {
        "cluster_id": cluster_id,
        "name": name,
        "created_at": now,
        "updated_at": now,
    }

    db.clusters.insert_one(cluster_doc)
    return _serialize_cluster(cluster_doc)


@router.patch("/{cluster_id}")
async def update_cluster(cluster_id: str, payload: ClusterUpdateRequest):
    name = _normalize_name(payload.name)
    result = db.clusters.update_one(
        {"cluster_id": cluster_id},
        {"$set": {"name": name, "updated_at": datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found"
        )
    cluster = db.clusters.find_one({"cluster_id": cluster_id})
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found"
        )
    return _serialize_cluster(cluster)


@router.delete("/{cluster_id}")
async def delete_cluster(cluster_id: str):
    cluster = db.clusters.find_one({"cluster_id": cluster_id})
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found"
        )

    thread_result = db.threads.delete_many({"cluster_id": cluster_id})
    db.clusters.delete_one({"cluster_id": cluster_id})

    return {
        "message": f"Cluster {cluster_id} deleted",
        "deleted_threads": thread_result.deleted_count,
    }
