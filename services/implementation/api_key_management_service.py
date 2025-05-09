import logging
import secrets
import uuid
from datetime import datetime
from fastapi import HTTPException
from models import APIKeyModel
from services.interfaces.api_key_management_interface import IAPIKeyManagementService
from repository import IRepository

class APIKeyManagementService(IAPIKeyManagementService):
    def __init__(self, repository: IRepository):
        self.logger = logging.getLogger("app")
        self.repository = repository

    async def create_api_key(self, name, role, user_id, team_id) -> APIKeyModel:
        api_key_id = str(uuid.uuid4())
        api_key_value = f"sk_{secrets.token_urlsafe(32)}"
        created_at = datetime.now()
        
        api_key_data = {
            "id": api_key_id,
            "name": name,
            "key": api_key_value,
            "role": role,
            "user_id": user_id,
            "team_id": team_id,
            "created_at": created_at,
        }
        
        api_key_db = await self.repository.api_keys.create_api_key(api_key_data)
        self.logger.info(f"Created new API key {api_key_id}")
        
        return api_key_db

    async def list_api_keys(self) -> list[APIKeyModel]:
        api_keys = await self.repository.api_keys.list_api_keys()
        return api_keys

    async def get_api_key_by_id(self, api_key_id) -> APIKeyModel:
        api_key = await self.repository.api_keys.get_api_key_by_id(api_key_id)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return api_key
    
    async def get_api_key_by_key(self, api_key) -> APIKeyModel:
        api_key = await self.repository.api_keys.get_api_key_by_key(api_key)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return api_key

    async def delete_api_key(self, api_key_id: str):
        # First verify the API key exists
        api_key = await self.repository.api_keys.get_api_key_by_id(api_key_id)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
            
        await self.repository.api_keys.delete_api_key(api_key_id)
        self.logger.info(f"Deleted API key {api_key_id}")