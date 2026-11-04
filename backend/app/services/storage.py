import os
import re
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
    _minio_checked = False
    _minio_available = False

    @classmethod
    def get_minio_client(cls):
        if settings.STORAGE_TYPE != "minio":
            return None

        if not cls._minio_checked and Minio:
            cls._minio_checked = True
            try:
                cli = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE
                )
                # Quick bucket check with short timeout
                if not cli.bucket_exists(settings.MINIO_BUCKET):
                    cli.make_bucket(settings.MINIO_BUCKET)
                cls._minio_client = cli
                cls._minio_available = True
                logger.info("MinIO object storage initialized and connected.")
            except Exception as e:
                cls._minio_client = None
                cls._minio_available = False
                logger.warning(f"MinIO storage unavailable ({e}). Using local storage engine.")
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
        raw_name = (file.filename or "uploaded_document").replace("\\", "/")
        raw_basename = os.path.basename(raw_name)
        sanitized_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', raw_basename)
        sanitized_name = sanitized_name.lstrip(".")
        if not sanitized_name:
            sanitized_name = f"doc_{unique_id}.{ext if ext else 'dat'}"
        safe_filename = f"{unique_id}_{sanitized_name}"
        destination_path = os.path.abspath(os.path.join(org_dir, safe_filename))

        # Enforce strict path containment within organization directory
        if not destination_path.startswith(os.path.abspath(org_dir)):
            raise HTTPException(status_code=400, detail="Path traversal attempt detected in uploaded filename.")

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

        return destination_path, file_hash, total_size, sanitized_name
