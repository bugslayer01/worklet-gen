from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import io, zipfile
import unicodedata
import re
from urllib.parse import quote
from core.models.worklet import Worklet
from core.utils.generate_files import create_pdf, create_ppt
from core.utils.sanitize_filename import sanitize_filename
from core.database import db

router = APIRouter(prefix="/thread", tags=["thread"])


def _content_disposition(filename: str) -> str:
    """Build a RFC 5987/6266 compatible Content-Disposition header value.

    Starlette encodes header values using latin-1. Non-ASCII filenames will
    raise UnicodeEncodeError if passed directly. To support Unicode filenames
    we provide an ASCII fallback `filename=` and a UTF-8 encoded `filename*`.
    """
    # ASCII-only fallback (strip quotes/unsafe chars)
    fallback = (
        unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    )
    if not fallback:
        fallback = "download"
    # Keep it safe for HTTP header tokens
    fallback = re.sub(r"[^A-Za-z0-9._-]", "_", fallback)
    # RFC 5987 percent-encoded UTF-8 for the actual filename
    encoded = quote(filename)
    return f"attachment; filename={fallback}; filename*=UTF-8''{encoded}"


@router.get("/all")
async def get_all_threads():
    threads = db.threads.find({}, {"_id": 0})
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
    if file_type not in {"pdf", "ppt"}:
        raise HTTPException(status_code=400, detail="file_type must be 'pdf' or 'ppt'")

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
                worklet_model = Worklet(**w)
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
    if file_type not in {"pdf", "ppt"}:
        raise HTTPException(status_code=400, detail="file_type must be 'pdf' or 'ppt'")

    thread = db.threads.find_one({"thread_id": thread_id})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    worklets = thread.get("worklets", [])
    target = next((w for w in worklets if w.get("worklet_id") == worklet_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Worklet not found in thread")

    # Validate via model
    worklet_model = Worklet(**target)
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
