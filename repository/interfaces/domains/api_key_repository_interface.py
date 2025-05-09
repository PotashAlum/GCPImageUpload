from abc import ABC, abstractmethod
from typing import List, Optional
from models import APIKeyModel

class IAPIKeyRepository(ABC):
    @abstractmethod
    async def create_api_key(self, api_key) -> APIKeyModel:
        pass
    
    @abstractmethod
    async def get_api_key_by_id(self, api_key_id: str) -> Optional[APIKeyModel]:
        pass
    
    @abstractmethod
    async def get_api_key_by_key(self, api_key: str) -> Optional[APIKeyModel]:
        pass
    
    @abstractmethod
    async def list_api_keys(self, skip: int = 0, limit: int = 10) -> List[APIKeyModel]:
        pass
    
    @abstractmethod
    async def get_api_keys_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[APIKeyModel]:
        pass
    
    @abstractmethod
    async def delete_api_key(self, api_key_id: str) -> None:
        pass
    
    @abstractmethod
    async def delete_user_api_keys(self, user_id: str) -> None:
        pass