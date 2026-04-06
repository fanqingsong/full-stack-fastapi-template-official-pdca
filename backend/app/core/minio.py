"""MinIO client and utility functions for file storage."""

import io
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class MinIOClient:
    """MinIO client wrapper for file operations."""

    def __init__(self) -> None:
        """Initialize MinIO client (lazy initialization)."""
        self._client: Minio | None = None
        self.bucket_name = settings.MINIO_BUCKET_NAME

    @property
    def client(self) -> Minio:
        """Get or create MinIO client."""
        if self._client is None:
            self._client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=settings.MINIO_SECURE,
                region=settings.MINIO_REGION,
            )
            self._ensure_bucket_exists()
        return self._client

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self._client.bucket_exists(self.bucket_name):
                self._client.make_bucket(self.bucket_name, location=settings.MINIO_REGION)
        except S3Error as e:
            raise RuntimeError(f"Failed to create MinIO bucket: {e}") from e

    def upload_file(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        content_type: str,
    ) -> str:
        """
        Upload a file to MinIO.

        Args:
            file_data: File data as bytes or file-like object
            filename: Name to give the file in storage
            content_type: MIME type of the file

        Returns:
            The object name in the bucket

        Raises:
            RuntimeError: If upload fails
        """
        try:
            if isinstance(file_data, bytes):
                file_data = io.BytesIO(file_data)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=filename,
                data=file_data,
                length=file_data.getbuffer().nbytes if hasattr(file_data, "getbuffer") else -1,
                content_type=content_type,
            )
            return filename
        except S3Error as e:
            raise RuntimeError(f"Failed to upload file: {e}") from e

    def delete_file(self, filename: str) -> None:
        """
        Delete a file from MinIO.

        Args:
            filename: Name of the file to delete

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            self.client.remove_object(bucket_name=self.bucket_name, object_name=filename)
        except S3Error as e:
            raise RuntimeError(f"Failed to delete file: {e}") from e

    def get_file_url(self, filename: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for file download.

        Args:
            filename: Name of the file
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL for downloading the file

        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            return self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=filename,
                expires=expires_in,
            )
        except S3Error as e:
            raise RuntimeError(f"Failed to generate file URL: {e}") from e

    def get_file(self, filename: str) -> bytes:
        """
        Download a file from MinIO.

        Args:
            filename: Name of the file to download

        Returns:
            File content as bytes

        Raises:
            RuntimeError: If download fails
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=filename,
            )
            return response.read()
        except S3Error as e:
            raise RuntimeError(f"Failed to download file: {e}") from e

    def list_files(self, prefix: str = "") -> list[dict]:
        """
        List all files in the bucket.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file information dictionaries

        Raises:
            RuntimeError: If listing fails
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True,
            )
            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                }
                for obj in objects
            ]
        except S3Error as e:
            raise RuntimeError(f"Failed to list files: {e}") from e


# Global MinIO client instance
minio_client = MinIOClient()
