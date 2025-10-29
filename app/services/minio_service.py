from minio import Minio
from minio.error import S3Error
from io import BytesIO
from typing import Optional
import uuid
from datetime import timedelta

from app.config.settings import Settings


class MinioService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = Minio(
            f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,  # True for HTTPS
        )
        self.bucket_name = settings.MINIO_STORAGE
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")

    def upload_file(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str = "application/octet-stream",
        folder: str = "avatars",
    ) -> str:
        """
        Upload file to MinIO

        Args:
            file_data: File bytes
            file_name: Original file name
            content_type: MIME type
            folder: Folder in bucket

        Returns:
            Object path in MinIO
        """
        try:
            # Generate unique file name
            ext = file_name.split(".")[-1] if "." in file_name else "jpg"
            unique_name = f"{uuid.uuid4()}.{ext}"
            object_name = f"{folder}/{unique_name}"

            # Upload file
            self.client.put_object(
                self.bucket_name,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )

            return object_name
        except S3Error as e:
            raise ValueError(f"MinIO upload error: {str(e)}")

    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Get presigned URL for file

        Args:
            object_name: Object path in MinIO
            expires: URL expiration in seconds

        Returns:
            Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name, object_name, expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            raise ValueError(f"MinIO get URL error: {str(e)}")

    def delete_file(self, object_name: str) -> bool:
        """
        Delete file from MinIO

        Args:
            object_name: Object path in MinIO

        Returns:
            True if deleted successfully
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"MinIO delete error: {e}")
            return False

    def get_file(self, object_name: str) -> bytes:
        """
        Get file data from MinIO

        Args:
            object_name: Object path in MinIO

        Returns:
            File bytes
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise ValueError(f"MinIO get file error: {str(e)}")


# Singleton instance
_minio_service = None


def get_minio_service() -> MinioService:
    """Get MinIO service singleton"""
    global _minio_service
    if _minio_service is None:
        from app.config.dependencies import get_settings

        _minio_service = MinioService(get_settings())
    return _minio_service
