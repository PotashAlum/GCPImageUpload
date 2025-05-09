import logging
from datetime import timedelta
from typing import Optional
from fastapi import UploadFile

from services.interfaces.storage_service_interface import IStorageService

class GCPStorageService(IStorageService):
    def __init__(self, bucket, bucket_name: str):
        self.logger = logging.getLogger("app")
        self.bucket = bucket
        self.bucket_name = bucket_name
    
    async def upload_file(
        self,
        file: UploadFile,
        path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to Google Cloud Storage.
        
        Args:
            file: The file to upload
            path: The path/key where the file should be stored
            content_type: Optional content type of the file
            
        Returns:
            The URL to access the file
        """
        blob = self.bucket.blob(path)
        
        # Use provided content type or get it from the file
        file_content_type = content_type or file.content_type
        
        # Upload the file
        blob.upload_from_file(file.file, content_type=file_content_type)
        
        # Generate a signed URL for immediate access
        expiration = timedelta(hours=1)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET"
        )
        
        self.logger.info(f"File uploaded to GCS: {path}")
        return signed_url
    
    async def generate_signed_url(
        self,
        path: str,
        expiration: Optional[timedelta] = None,
        method: str = "GET"
    ) -> str:
        """
        Generate a signed URL for a file in Google Cloud Storage.
        
        Args:
            path: The path/key of the file
            expiration: How long the URL should be valid (default: 1 hour)
            method: HTTP method (GET, PUT, etc.)
            
        Returns:
            A signed URL for the file
        """
        blob = self.bucket.blob(path)
        
        # Default expiration is 1 hour
        if expiration is None:
            expiration = timedelta(hours=1)
        
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method=method
        )
        
        return signed_url
    
    async def delete_file(
        self,
        path: str
    ) -> None:
        """
        Delete a file from Google Cloud Storage.
        
        Args:
            path: The path/key of the file to delete
        """
        blob = self.bucket.blob(path)
        blob.delete()
        
        self.logger.info(f"File deleted from GCS: {path}")
        return None