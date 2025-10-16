import aiofiles
import asyncio
import os
import re
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, UploadFile
from pipeline.state import AgentState
from core.database import db
from pipeline.builder import Pipeline
from core.utils.sanitize_filename import sanitize_filename
from core.utils.process_array_string import process_array_string

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/")
async def generate(
    thread_id: Annotated[str, Form()],
    thread_name: Annotated[str, Form()],
    count: Annotated[int, Form()],
    links: Annotated[str, Form()],
    custom_prompt: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()] = None,
):

    existing_thread = db.threads.find_one({"thread_id": thread_id})
    if existing_thread:
        return {"error": "Thread ID already exists. Please choose a different ID."}

    file_names = [file.filename for file in files] if files else []
    links_array = process_array_string(links) if links else []
    thread_dict = {
        "thread_id": thread_id,
        "thread_name": thread_name,
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
            "count": count,
            "links": links_array,
            "custom_prompt": custom_prompt,
            "files": files,
        }
    )
    state = AgentState(
        thread_id=thread_id,
        count=count,
        files=files,
        links=links_array,
        custom_prompt=custom_prompt,
    )
    db.threads.insert_one(thread_dict)

    start_time = time.time()
    state = await Pipeline.ainvoke(state)
    state = AgentState.model_validate(state)
    end_time = time.time()
    print(f"Total time taken for the request: {end_time - start_time:.2f} seconds")

    worklets = (
        [worklet.model_dump() for worklet in state.worklets] if state.worklets else []
    )

    return {
        "thread_id": thread_id,
        "worklets": worklets,
        "worklet_count": len(worklets),
    }


# @router.get('/download/{file_name}')
# async def download(file_name: str):
#     new_file_name = sanitize_filename(file_name) + ".pdf"
#     file_path = Path(GENERATED_DIR_PDF) / new_file_name

#     if not file_path.exists():
#         file_path = Path(DESTINATION_DIR_PDF) / new_file_name

#     safe_filename = new_file_name.replace(":", " -")
#     if file_path.exists():
#         return FileResponse(
#             file_path,
#             media_type="application/pdf",
#             filename=safe_filename
#         )
#     return {"error": "File not found"}
# class FilesRequest(BaseModel):
#     files: list[str]

# @router.post("/download_all")
# def download_selected(received_files: FilesRequest, type: str = Query(...)):
#     """
#     Handles the download of selected files by creating a zip archive containing the requested files.
#     Args:
#         received_files (FilesRequest): An object containing a list of file names to be downloaded.
#         type (str): The type of files to download, either "pdf" or "ppt". This is passed as a query parameter.
#     Returns:
#         FileResponse: A response containing the zip file for download if successful.
#         dict: An error message if no files are provided or if the type is invalid.
#     Raises:
#         None
#     Notes:
#         - The function searches for files in two directories based on the type:
#           - For "pdf": Searches in GENERATED_DIR_PDF and DESTINATION_DIR_PDF.
#           - For "ppt": Searches in GENERATED_DIR_PPT and DESTINATION_DIR_PPT.
#         - Files are added to the zip archive if they exist in the specified directories.
#         - If no valid files are found, an error message is returned.
#         - The zip file is created as a temporary file and returned as a downloadable response.
#     """

#     files = received_files.files
#     if not files:
#         return {"error": "No files provided."}

#     # Create a temporary zip file
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
#         zip_path = temp_zip.name

#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         # Make a copy so we can modify files safely
#         remaining_files = files.copy()

#         if(type == "pdf"):
#             # First, search and add files from GENERATED_DIR_PDF
#             for file_name in files:
#                 search_name = file_name + ".pdf"
#                 file_path = os.path.join(GENERATED_DIR_PDF, search_name)
#                 print(file_path)
#                 if os.path.isfile(file_path):
#                     zipf.write(file_path, arcname=search_name)
#                     remaining_files.remove(file_name)

#             # Then, search remaining files in DESTINATION_DIR_PDF
#             for file_name in remaining_files:
#                 search_name = file_name + ".pdf"
#                 file_path = os.path.join(DESTINATION_DIR_PDF, search_name)
#                 if os.path.isfile(file_path):
#                     zipf.write(file_path, arcname=search_name)

#         elif(type == "ppt"):
#             # First, search and add files from GENERATED_DIR_PPT
#             for file_name in files:
#                 search_name = file_name + ".pptx"
#                 file_path = os.path.join(GENERATED_DIR_PPT, search_name)
#                 print(file_path)
#                 if os.path.isfile(file_path):
#                     zipf.write(file_path, arcname=search_name)
#                     remaining_files.remove(file_name)

#             # Then, search remaining files in DESTINATION_DIR_PPT
#             for file_name in remaining_files:
#                 search_name = file_name + ".pptx"
#                 file_path = os.path.join(DESTINATION_DIR_PPT, search_name)
#                 if os.path.isfile(file_path):
#                     zipf.write(file_path, arcname=search_name)
#         else:
#             return {"error": "Invalid type. Must be 'pdf' or 'ppt'."}


#     return FileResponse(zip_path, filename="worklets.zip", media_type="application/zip")
