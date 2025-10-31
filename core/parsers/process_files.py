import json
import os
from typing import List

import aiofiles
import asyncio

from core.models.document import Documents
from core.parsers.main import extract_document
import time
from app.broadcast import update_message, stop_broadcasting


# ppt, pdf, xlsx, doc, docx, txt, html, png, jpeg, jpg, md
async def process_files(
    files_data: List[dict],
    thread_id: str,
) -> Documents:
    """
    Process a list of uploaded files:
    - Pass each file to the document parser.
    - Store the parsed result as JSON in `data/threads/{thread_id}/parsed/`.
    - Accumulate all parsed documents into a Documents object.

    Returns:
        Documents: A structured object containing parsed documents.
    """
    parsed_dir = f"data/threads/{thread_id}/parsed"
    try:
        os.makedirs(parsed_dir, exist_ok=True)
    except Exception as e:
        print(f"[init] Failed to create parsed dir {parsed_dir}: {e}")

    documents = Documents(documents=[], thread_id=thread_id)
    start_time = time.time()

    # Helper to process one file
    async def process_file(file_data):
        try:
            try:
                await update_message(
                    {"message": f"Processing {file_data['title']}"},
                    topic=f"{thread_id}/status_update",
                )
            except Exception as e:
                print(f"[emit-error] progress emit failed: {e}")

            parsed_data = None
            try:
                parsed_data = await extract_document(
                    path=file_data.get("path"),
                    title=file_data.get("title", "Untitled"),
                    file_name=file_data.get("file_name"),
                    thread_id=thread_id,
                )
            except Exception as e:
                print(f"[parse-error] {file_data.get('file_name')}: {e}")
                return None

            if parsed_data is None:
                print(
                    f"Warning: Failed to parse file {file_data.get('file_name')}, skipping..."
                )
                return None

            parsed_dict = parsed_data.model_dump()
            parsed_dict["thread_id"] = thread_id
            
            try:
                parsed_json = json.dumps(parsed_dict, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[json-error] Failed to serialize parsed data: {e}")
                return parsed_data

            try:
                name, _ = os.path.splitext(file_data.get("file_name", "document"))
                json_file_path = os.path.join(parsed_dir, f"{name}.json")
                async with aiofiles.open(json_file_path, "w", encoding="utf-8") as f:
                    await f.write(parsed_json)
            except Exception as e:
                print(f"[write-error] Failed to write {json_file_path}: {e}")

            return parsed_data
        except Exception as e:
            print(
                f"[unexpected] process_file crashed for {file_data.get('file_name')}: {e}"
            )
            return None

    batch_size = 10
    # Process in batches
    for i in range(0, len(files_data), batch_size):
        batch = files_data[i : i + batch_size]
        try:
            results = await asyncio.gather(
                *(process_file(file_data) for file_data in batch),
                return_exceptions=True,
            )
        except Exception as e:
            print(f"[batch-error] Failed batch starting at {i}: {e}")
            results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"[task-exception] {result}")
                continue
            if result:
                documents.documents.append(result)

    end_time = time.time()
    try:
        print(
            f"Processed {len(files_data)} files in {end_time - start_time:.2f} seconds"
        )
    except Exception as e:
        print(f"[summary-error] {e}")
    return documents
