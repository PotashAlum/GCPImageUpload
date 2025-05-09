from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional
from fastapi import UploadFile

class IStorageService(ABC):
    @abstractmethod
    async def upload_file(
        self,
        file: UploadFile,
        path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to storage.
        
        Args:
            file: The file to upload
            path: The path/key where the file should be stored
            content_type: Optional content type of the file
            
        Returns:
            The URL to access the file
        """
        pass
    
    @abstractmethod
    async def generate_signed_url(
        self,
        path: str,
        expiration: Optional[timedelta] = None,
        method: str = "GET"
    ) -> str:
        """
        Generate a signed URL for the file.
        
        Args:
            path: The path/key of the file
            expiration: How long the URL should be valid
            method: HTTP method (GET, PUT, etc.)
            
        Returns:
            A signed URL for the file
        """
        pass
    
    @abstractmethod
    async def delete_file(
        self,
        path: str
    ) -> None:
        """
        Delete a file from storage.
        
        Args:
            path: The path/key of the file to delete
        """
        pass