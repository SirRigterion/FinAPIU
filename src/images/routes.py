import os
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from src.core.config import settings
import aiofiles
from secrets import token_hex

async def save_file(file: UploadFile, directory: str) -> str:
    allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    filename = f"{file.filename.split('.')[0]}_{token_hex(4)}.{file_extension}"
    file_path = os.path.join(directory, filename)
    
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(await file.read())
    return filename

router = APIRouter(prefix="/images", tags=["images"])

import logging

@router.get("/{file:path}")
async def get_image(file: str):
    logging.info(f"Original file path: {file}")
    cleaned_file = os.path.normpath(file.strip()).replace(os.sep + os.sep, os.sep)
    cleaned_file = cleaned_file.lstrip(os.sep).lstrip(os.altsep or '')
    
    if ".." in cleaned_file or os.path.isabs(cleaned_file):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if cleaned_file.startswith("uploads/"):
        cleaned_file = cleaned_file[len("uploads/"):].lstrip(os.sep)
    
    image_path = os.path.join(settings.UPLOAD_DIR, cleaned_file)
    logging.info(f"Final image path: {image_path}")
    
    if not os.path.exists(image_path) or not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail=f"Image not found at {image_path}")
    
    return FileResponse(image_path)