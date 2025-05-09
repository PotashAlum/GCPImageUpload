from repository.interfaces.domains.image_repository_interface import IImageRepository
from models import ImageModel
from typing import List, Optional


class MongoDBImageRepository(IImageRepository):
    """MongoDB implementation of the image repository"""
    
    def __init__(self, db, logger=None):
        self.db = db
        self.logger = logger
    
    async def setup_indexes(self):
        """Setup all required indexes for the images collection"""
        await self.db.create_index("id", unique=True)
        await self.db.create_index([("user_id", 1), ("created_at", -1)])
        await self.db.create_index([("team_id", 1), ("created_at", -1)])
    
    async def create_image(self, image) -> ImageModel:
        await self.db.insert_one(image)
        return ImageModel(**image)
    
    async def get_image_by_id(self, image_id: str) -> Optional[ImageModel]:
        image_data = await self.db.find_one({"id": image_id})
        return ImageModel(**image_data) if image_data else None
    
    async def get_images_by_team_id(self, team_id: str, skip: int = 0, limit: int = 10) -> List[ImageModel]:
        cursor = self.db.find({"team_id": team_id})
        cursor = cursor.sort("created_at", -1)
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        images_data = await cursor.to_list(limit)
        return [ImageModel(**image) for image in images_data]
    
    async def get_images_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[ImageModel]:
        cursor = self.db.find({"user_id": user_id})
        cursor = cursor.sort("created_at", -1)
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        images_data = await cursor.to_list(limit)
        return [ImageModel(**image) for image in images_data]
    
    async def delete_image(self, image_id: str) -> None:
        await self.db.delete_one({"id": image_id})
    
    async def delete_images_by_team_id(self, team_id: str) -> None:
        await self.db.delete_many({"team_id": team_id})