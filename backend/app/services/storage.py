import os
import hashlib
import uuid
import shutil
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.core.config import settings


class StorageService:
    @staticmethod
    def compute_sha256(file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[str, str]:
        """Validate filename extension and MIME type against allowed list."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file extension: .{ext}. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        mime = file.content_type or "application/octet-stream"
        return ext, mime

    @staticmethod
    async def save_upload_file(file: UploadFile, organization_id: str) -> Tuple[str, str, int, str]:
        """
        Saves uploaded file to the organization's partitioned storage directory.
        Returns (saved_file_path, file_hash, file_size_bytes, safe_filename).
        """
        ext, mime = StorageService.validate_file(file)
        
        org_dir = os.path.join(settings.UPLOAD_DIR, organization_id)
        os.makedirs(org_dir, exist_ok=True)

        unique_id = str(uuid.uuid4())
        safe_filename = f"{unique_id}_{file.filename}"
        destination_path = os.path.join(org_dir, safe_filename)

        sha256_hash = hashlib.sha256()
        total_size = 0

        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(65536):
                total_size += len(chunk)
                if total_size > settings.MAX_FILE_SIZE_BYTES:
                    buffer.close()
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024*1024)} MB"
                    )
                sha256_hash.update(chunk)
                buffer.write(chunk)

        file_hash = sha256_hash.hexdigest()
        return destination_path, file_hash, total_size, file.filename
