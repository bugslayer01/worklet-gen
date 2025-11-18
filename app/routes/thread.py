from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io, zipfile
import unicodedata
import re
from urllib.parse import quote
from core.models.worklet import Worklet
from core.utils.generate_files import create_pdf, create_ppt
from core.utils.worklet_store import iteration_to_worklet
from core.utils.sanitize_filename import sanitize_filename
from core.utils.fix_dashes import fix_dashes
from core.database import db
from copy import deepcopy


# Fields categorization to support normalized extraction from transformed records
_STRING_FIELDS = {
    "title",
    "problem_statement",
    "description",
    "reasoning",
    "challenge_use_case",
    "infrastructure_requirements",
    "tech_stack",
}
_ARRAY_FIELDS = {"deliverables", "kpis", "prerequisites"}
_OBJECT_FIELDS = {"milestones"}


def _pick_selected_value(field_payload):
    """Given a stored field payload, return the selected iteration value.

    Supports both the transformed schema (object with selected_index & iterations)
    and the legacy/raw schema (string/list/object).
    """
    if isinstance(field_payload, dict) and "iterations" in field_payload:
        iterations = field_payload.get("iterations") or []
        if not isinstance(iterations, list) or len(iterations) == 0:
            return None
        idx = field_payload.get("selected_index", 0)
        try:
            idx = int(idx)
        except Exception:
            idx = 0
        if idx < 0 or idx >= len(iterations):
            idx = 0
        return deepcopy(iterations[idx])

    # Fallback: return the payload as-is (could be str/list/dict)
    return deepcopy(field_payload)


def _normalize_string_list(raw_value):
    """Coerce arbitrary input into a list of trimmed, non-empty strings."""

    if raw_value in (None, ""):
        return []
    if isinstance(raw_value, list):
        items = raw_value
    elif isinstance(raw_value, (tuple, set)):
        items = list(raw_value)
    elif isinstance(raw_value, str):
        items = re.split(r"[\r\n]+|\s*[;\u2022]\s*", raw_value)
    else:
        items = [raw_value]

    normalized = []
    for item in items:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_worklet_record(record: dict) -> dict:
    """Convert a transformed worklet record from the DB into the plain Worklet dict.

    Raises if required keys are missing; callers may catch and skip invalid entries.
    """
    normalized = {
        "worklet_id": record.get("worklet_id"),
        "references": deepcopy(record.get("references", [])),
    }
    iterations = record.get("iterations")
    if isinstance(iterations, list) and iterations:
        idx = record.get("selected_iteration_index", 0)
        try:
            idx = int(idx)
        except Exception:
            idx = 0
        if idx < 0 or idx >= len(iterations):
            idx = 0
        iteration_payload = iterations[idx]
        worklet_model = iteration_to_worklet(iteration_payload)
        normalized = worklet_model.model_dump()
        normalized["worklet_id"] = record.get(
            "worklet_id", normalized.get("worklet_id")
        )
        return normalized

    # Strings
    for f in _STRING_FIELDS:
        value = _pick_selected_value(record.get(f))
        if isinstance(value, str):
            normalized[f] = value
        elif value is None:
            normalized[f] = ""
        else:
            normalized[f] = str(value)

    # Arrays
    for f in _ARRAY_FIELDS:
        val = _pick_selected_value(record.get(f))
        normalized[f] = _normalize_string_list(val)

    # Objects
    for f in _OBJECT_FIELDS:
        val = _pick_selected_value(record.get(f))
        normalized[f] = val if isinstance(val, dict) else (val or {})

    return normalized


router = APIRouter(prefix="/thread", tags=["thread"])


def _content_disposition(filename: str) -> str:
    """Build a RFC 5987/6266 compatible Content-Disposition header value.

    Starlette encodes header values using latin-1. Non-ASCII filenames will
    raise UnicodeEncodeError if passed directly. To support Unicode filenames
    we provide an ASCII fallback `filename=` and a UTF-8 encoded `filename*`.
    """
    # ASCII-only fallback (strip quotes/unsafe chars)
    fallback = (
        unicodedata.normalize("NFKD", filename)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    if not fallback:
        fallback = "download"
    # Keep it safe for HTTP header tokens
    fallback = re.sub(r"[^A-Za-z0-9._-]", "_", fallback)
    # RFC 5987 percent-encoded UTF-8 for the actual filename
    encoded = quote(filename)
    return f"attachment; filename={fallback}; filename*=UTF-8''{encoded}"


@router.get("/all")
async def get_all_threads(cluster_id: str | None = None):
    query = {"cluster_id": cluster_id} if cluster_id else {}
    threads = db.threads.find(query, {"_id": 0})
    return {"threads": list(threads)}


@router.delete("/delete/{thread_id}")
async def delete_thread(thread_id: str):
    if not thread_id:
        # Bad Request when required path parameter is missing/empty
        raise HTTPException(status_code=400, detail="Thread ID is required")

    result = db.threads.delete_one({"thread_id": thread_id})
    if result.deleted_count == 1:
        return {"message": f"Thread {thread_id} deleted successfully"}
    # Not Found when the resource does not exist
    raise HTTPException(status_code=404, detail="Thread not found")


@router.get("/{thread_id}")
async def get_thread(thread_id: str):
    thread = db.threads.find_one({"thread_id": thread_id}, {"_id": 0})  # exclude _id
    if thread:
        return thread
    raise HTTPException(status_code=404, detail="Thread not found")


@router.get("/{thread_id}/download/all/{file_type}")
async def download_all_worklets(thread_id: str, file_type: str):
    if file_type not in {"pdf", "pptx"}:
        raise HTTPException(status_code=400, detail="file_type must be 'pdf' or 'pptx'")

    thread = db.threads.find_one({"thread_id": thread_id})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    worklets = thread.get("worklets", [])
    if not worklets:
        raise HTTPException(status_code=404, detail="No worklets found for this thread")

    thread_name = sanitize_filename(thread.get("thread_name", thread_id)) or thread_id

    # If only one worklet, just return single file (optional optimization)
    # if len(worklets) == 1:
    #     single = worklets[0]
    #     worklet_model = Worklet(**single)
    #     filename_base = (
    #         sanitize_filename(worklet_model.title) or worklet_model.worklet_id
    #     )
    #     if file_type == "pdf":
    #         data = create_pdf(
    #             filename=f"{filename_base}.pdf", worklet=worklet_model, in_memory=True
    #         )
    #         media_type = "application/pdf"
    #         download_name = f"{filename_base}.pdf"
    #     else:
    #         data = create_ppt(
    #             output_filename=f"{filename_base}.pptx",
    #             worklet=worklet_model,
    #             in_memory=True,
    #         )
    #         media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    #         download_name = f"{filename_base}.pptx"
    #     if data is None:
    #         raise HTTPException(status_code=500, detail="Failed creating file")
    #     return StreamingResponse(
    #         io.BytesIO(data),
    #         media_type=media_type,
    #         headers={"Content-Disposition": f"attachment; filename={download_name}"},
    #     )

    # Multiple worklets -> zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for w in worklets:
            try:
                normalized = _normalize_worklet_record(w)
                worklet_model = Worklet(**normalized)
                worklet_model = fix_dashes(worklet_model)
            except Exception:
                continue  # skip invalid
            filename_base = (
                sanitize_filename(worklet_model.title) or worklet_model.worklet_id
            )
            if file_type == "pdf":
                data = create_pdf(
                    filename=f"{filename_base}.pdf",
                    worklet=worklet_model,
                    in_memory=True,
                )
                if data:
                    zf.writestr(f"{filename_base}.pdf", data)
            else:
                data = create_ppt(
                    output_filename=f"{filename_base}.pptx",
                    worklet=worklet_model,
                    in_memory=True,
                )
                if data:
                    zf.writestr(f"{filename_base}.pptx", data)
    zf_name = f"{thread_name}_worklets_{file_type}.zip"
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": _content_disposition(zf_name)},
    )


@router.get("/{thread_id}/download/{worklet_id}/{file_type}")
async def download_worklet(thread_id: str, worklet_id: str, file_type: str):
    if file_type not in {"pdf", "pptx"}:
        raise HTTPException(status_code=400, detail="file_type must be 'pdf' or 'pptx'")

    thread = db.threads.find_one({"thread_id": thread_id})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    worklets = thread.get("worklets", [])
    target = next((w for w in worklets if w.get("worklet_id") == worklet_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Worklet not found in thread")

    # Normalize transformed record into the plain Worklet shape and validate
    try:
        normalized = _normalize_worklet_record(target)
        worklet_model = Worklet(**normalized)
        worklet_model = fix_dashes(worklet_model)

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Stored worklet is invalid or missing required fields",
        )
    filename_base = sanitize_filename(worklet_model.title) or worklet_model.worklet_id
    if file_type == "pdf":
        data = create_pdf(
            filename=f"{filename_base}.pdf", worklet=worklet_model, in_memory=True
        )
        media_type = "application/pdf"
        download_name = f"{filename_base}.pdf"
    else:
        data = create_ppt(
            output_filename=f"{filename_base}.pptx",
            worklet=worklet_model,
            in_memory=True,
        )
        media_type = (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        download_name = f"{filename_base}.pptx"

    if data is None:
        raise HTTPException(status_code=500, detail="Failed creating file")

    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": _content_disposition(download_name)},
    )
