import os
import hashlib
import uuid
import io
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.core.logging import logger

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    Minio = None
    S3Error = None


class StorageService:
    _minio_client = None

    @classmethod
    def get_minio_client(cls):
        if cls._minio_client is None and Minio:
            try:
                cls._minio_client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE
                )
                # Check/Create bucket
                if not cls._minio_client.bucket_exists(settings.MINIO_BUCKET):
                    cls._minio_client.make_bucket(settings.MINIO_BUCKET)
            except Exception as e:
                logger.warning(f"MinIO storage unavailable: {e}. Falling back to local storage.")
                cls._minio_client = None
        return cls._minio_client

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[str, str]:
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

    @classmethod
    async def save_upload_file(cls, file: UploadFile, organization_id: str) -> Tuple[str, str, int, str]:
        """
        Saves uploaded file to local partition and mirrors to MinIO if enabled.
        Returns: (file_path, file_hash, file_size, safe_filename)
        """
        ext, mime = cls.validate_file(file)
        
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

        # If MinIO is enabled, sync to local MinIO object store
        minio_cli = cls.get_minio_client()
        if minio_cli:
            try:
                object_name = f"{organization_id}/{safe_filename}"
                with open(destination_path, "rb") as f_data:
                    minio_cli.put_object(
                        settings.MINIO_BUCKET,
                        object_name,
                        f_data,
                        length=total_size,
                        content_type=mime
                    )
            except Exception as e:
                logger.warning(f"Failed to sync to MinIO: {e}")

        return destination_path, file_hash, total_size, file.filename
