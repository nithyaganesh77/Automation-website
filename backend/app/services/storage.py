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

    @staticmethod
    def validate_magic_bytes(header: bytes, claimed_ext: str) -> str:
        """
        Validate file content types using magic bytes to prevent disguised executables and malicious binaries.
        Only legitimate PDF, PNG, and JPEG binaries are permitted.
        """
        # Block executables, scripts, and bytecode
        if (
            header.startswith(b"MZ") or  # DOS / Windows PE Executable
            header.startswith(b"\x7fELF") or  # Linux Executable
            header.startswith(b"#!") or  # Shell Script Shebang
            header.startswith(b"\xca\xfe\xba\xbe") or  # Mach-O / Java Class
            header.startswith(b"PK\x03\x04")  # Zip / Office / Jar disguise
        ):
            raise HTTPException(
                status_code=400,
                detail="Security violation: Executable binary or archive signature detected. File rejected."
            )

        detected_mime = None
        # PDF signature check: '%PDF-' within the first 1024 bytes
        if b"%PDF-" in header[:1024]:
            detected_mime = "application/pdf"
        elif header.startswith(b"\x89PNG\r\n\x1a\n"):
            detected_mime = "image/png"
        elif header.startswith(b"\xff\xd8\xff"):
            detected_mime = "image/jpeg"

        # Additional library detection if available
        if not detected_mime:
            try:
                import puremagic
                guess = puremagic.from_string(header)
                if guess in ["application/pdf", "image/png", "image/jpeg"]:
                    detected_mime = guess
            except Exception:
                pass

        if not detected_mime:
            try:
                import filetype
                kind = filetype.guess(header)
                if kind and kind.mime in ["application/pdf", "image/png", "image/jpeg"]:
                    detected_mime = kind.mime
            except Exception:
                pass

        allowed_mimes = {"application/pdf", "image/png", "image/jpeg"}
        if not detected_mime or detected_mime not in allowed_mimes:
            raise HTTPException(
                status_code=400,
                detail="Invalid file binary content. Only genuine PDF, PNG, and JPEG files are permitted."
            )

        # Cross-verify claimed extension against validated binary magic type
        if claimed_ext == "pdf" and detected_mime != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="File content does not match .pdf extension (disguised executable/binary rejected)."
            )
        if claimed_ext == "png" and detected_mime != "image/png":
            raise HTTPException(
                status_code=400,
                detail="File content does not match .png extension (disguised binary rejected)."
            )
        if claimed_ext in ["jpg", "jpeg"] and detected_mime != "image/jpeg":
            raise HTTPException(
                status_code=400,
                detail="File content does not match .jpg/.jpeg extension (disguised binary rejected)."
            )

        return detected_mime

    @classmethod
    async def save_upload_file(cls, file: UploadFile, organization_id: str) -> Tuple[str, str, int, str]:
        """
        Validates magic bytes, enforces 10MB limit, and stores file using random UUID.
        Returns: (file_path, file_hash, file_size, safe_display_filename)
        """
        ext, mime = cls.validate_file(file)

        # Read initial 2048 bytes for magic bytes header inspection
        header_bytes = await file.read(2048)
        if not header_bytes:
            raise HTTPException(status_code=400, detail="Cannot upload an empty file.")

        validated_mime = cls.validate_magic_bytes(header_bytes, ext)

        org_dir = os.path.join(settings.UPLOAD_DIR, organization_id)
        os.makedirs(org_dir, exist_ok=True)

        # Generate unique UUID storage filename: {uuid4()}.{ext} (never original user filename)
        unique_id = str(uuid.uuid4())
        stored_filename = f"{unique_id}.{ext}"
        destination_path = os.path.abspath(os.path.join(org_dir, stored_filename))

        # Enforce strict path containment within organization directory (anti-traversal)
        if not destination_path.startswith(os.path.abspath(org_dir)):
            raise HTTPException(status_code=400, detail="Path traversal attempt detected in uploaded filename.")

        # Sanitize display filename for database metadata only
        raw_name = (file.filename or "uploaded_document").replace("\\", "/")
        raw_basename = os.path.basename(raw_name)
        sanitized_display = re.sub(r'[^a-zA-Z0-9_.-]', '_', raw_basename).lstrip(".")
        if not sanitized_display or sanitized_display == ext:
            sanitized_display = f"{unique_id}.{ext}"

        sha256_hash = hashlib.sha256()
        total_size = len(header_bytes)
        sha256_hash.update(header_bytes)

        if total_size > settings.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024*1024)} MB"
            )

        with open(destination_path, "wb") as buffer:
            buffer.write(header_bytes)
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
                object_name = f"{organization_id}/{stored_filename}"
                with open(destination_path, "rb") as f_data:
                    minio_cli.put_object(
                        settings.MINIO_BUCKET,
                        object_name,
                        f_data,
                        length=total_size,
                        content_type=validated_mime
                    )
            except Exception as e:
                logger.warning(f"Failed to sync to MinIO: {e}")

        return destination_path, file_hash, total_size, sanitized_display
