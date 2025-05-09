from abc import ABC, abstractmethod
from typing import List, Optional
from models import ImageModel

class IImageRepository(ABC):
    @abstractmethod
    async def create_image(self, image) -> ImageModel:
        pass
    
    @abstractmethod
    async def get_image_by_id(self, image_id: str) -> Optional[ImageModel]:
        pass
    
    @abstractmethod
    async def get_images_by_team_id(self, team_id: str, skip: int = 0, limit: int = 10) -> List[ImageModel]:
        pass
    
    @abstractmethod
    async def get_images_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[ImageModel]:
        pass
    
    @abstractmethod
    async def delete_image(self, image_id: str) -> None:
        pass
    
    @abstractmethod
    async def delete_images_by_team_id(self, team_id: str) -> None:
        pass