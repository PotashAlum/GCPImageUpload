from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile
from models import ImageModel

class IImageService(ABC):
    """
    Interface for image service operations.
    Defines the contract that any image service implementation must follow.
    """
    
    @abstractmethod
    async def upload_team_image(
        self,
        user_id: str,
        team_id: str,
        file: UploadFile,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> ImageModel:
        """
        Upload a new image for a team
        
        Args:
            user_id: ID of the user uploading the image
            team_id: ID of the team the image belongs to
            file: Image file to upload
            title: Optional title for the image
            description: Optional description for the image
            tags: Optional comma-separated list of tags
            
        Returns:
            Image model with metadata
            
        Raises:
            HTTPException: If team not found or file is not a valid image
        """
        pass
    
    @abstractmethod
    async def list_team_images(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> List[ImageModel]:
        """
        List images for a specific team
        
        Args:
            team_id: ID of the team
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of image models
            
        Raises:
            HTTPException: If team not found
        """
        pass
    
    @abstractmethod
    async def get_team_image(
        self,
        image_id: str
    ) -> ImageModel:
        """
        Get a specific image by ID
        
        Args:
            image_id: ID of the image
            
        Returns:
            Image model with metadata and updated URL
            
        Raises:
            HTTPException: If image not found
        """
        pass
    
    @abstractmethod
    async def delete_image(
        self,
        image_id: str
    ) -> None:
        """
        Delete an image by ID
        
        Args:
            image_id: ID of the image
            
        Raises:
            HTTPException: If image not found
        """
        pass