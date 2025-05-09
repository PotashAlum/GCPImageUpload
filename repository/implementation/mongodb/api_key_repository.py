from repository.interfaces.domains.api_key_repository_interface import IAPIKeyRepository
from models import APIKeyModel
from typing import List, Optional


class MongoDBAPIKeyRepository(IAPIKeyRepository):
    """MongoDB implementation of the API key repository"""
    
    def __init__(self, db, logger=None):
        self.db = db
        self.logger = logger
    
    async def setup_indexes(self):
        """Setup all required indexes for the API keys collection"""
        await self.db.create_index("id", unique=True)
        await self.db.create_index("key_prefix")  # Index for faster prefix lookup
        await self.db.create_index("user_id")
        await self.db.create_index("team_id")
    
    async def create_api_key(self, api_key) -> APIKeyModel:
        await self.db.insert_one(api_key)
        return APIKeyModel(**api_key)
    
    async def get_api_key_by_id(self, api_key_id: str) -> Optional[APIKeyModel]:
        api_key_data = await self.db.find_one({"id": api_key_id})
        return APIKeyModel(**api_key_data) if api_key_data else None
    
    async def get_api_keys_by_prefix(self, key_prefix: str) -> List[APIKeyModel]:
        """Get API keys that match the provided prefix"""
        cursor = self.db.find({"key_prefix": key_prefix})
        api_keys_data = await cursor.to_list(length=100)  # Limit for safety
        return [APIKeyModel(**api_key) for api_key in api_keys_data]
    
    async def list_api_keys(self, skip: int = 0, limit: int = 10) -> List[APIKeyModel]:
        cursor = self.db.find()
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        api_keys_data = await cursor.to_list(limit)
        return [APIKeyModel(**api_key) for api_key in api_keys_data]
    
    async def get_api_keys_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[APIKeyModel]:
        cursor = self.db.find({"user_id": user_id})
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        api_keys_data = await cursor.to_list(limit)
        return [APIKeyModel(**api_key) for api_key in api_keys_data]
    
    async def delete_api_key(self, api_key_id: str) -> None:
        await self.db.delete_one({"id": api_key_id})
    
    async def delete_user_api_keys(self, user_id: str) -> None:
        await self.db.delete_many({"user_id": user_id})