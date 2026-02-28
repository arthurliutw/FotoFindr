import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

from config import settings
from db import insert_photo
from models import UploadResponse
from pipeline.runner import run_pipeline

router = APIRouter()


def _save_locally(file_bytes: bytes, photo_id: str) -> str:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    path = upload_dir / f"{photo_id}.jpg"
    path.write_bytes(file_bytes)
    return f"/uploads/{photo_id}.jpg"


@router.post("/", response_model=UploadResponse)
async def upload_photo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    file_bytes = await file.read()

    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large.")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image files are accepted.")

    photo_id = str(uuid.uuid4())
    storage_url = _save_locally(file_bytes, photo_id)

    insert_photo(photo_id, user_id, storage_url)

    # Kick off async AI pipeline
    background_tasks.add_task(run_pipeline, photo_id, user_id, storage_url, file_bytes)

    return UploadResponse(photo_id=photo_id, storage_url=storage_url)
