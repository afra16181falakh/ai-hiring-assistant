import os
import aiofiles
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.parser import extract_text_from_pdf

async def read_uploaded_file_to_text(uploaded_file: UploadFile) -> str:
    temp_path = os.path.join(settings.UPLOAD_DIR, uploaded_file.filename)
    try:
        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await uploaded_file.read()
            await out_file.write(content)

        if uploaded_file.filename.lower().endswith(".pdf"):
            file_text = extract_text_from_pdf(temp_path)
        else:
            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_text = f.read()

        if not file_text.strip():
            raise ValueError(f"{uploaded_file.filename} is empty or could not be read as text.")
        return file_text
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)