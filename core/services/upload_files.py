import os
from datetime import datetime
from typing import List
from app.socket_handler import sio
import aiofiles


async def upload_files(files, thread_id: str) -> List[dict]:
    """
    Asynchronously upload each file to the 'data/threads/{thread_id}/uploads' directory.
    Each file is renamed to include a timestamp: filename_{timestamp}.{extension}.

    Args:
        files (list): List of UploadFile objects.

    Returns:
        List[dict]: List of metadata dictionaries for each uploaded file.
    """
    upload_dir = os.path.join("data", "threads", thread_id, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    files_data = []

    for file in files:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        name, ext = os.path.splitext(file.filename)
        file_name = f"{name}_{timestamp}{ext}"
        file_path = os.path.join(upload_dir, file_name)
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        files_data.append({
            "title": file.filename,
            "file_name": file_name,
            "path": file_path,
        })

    return files_data
