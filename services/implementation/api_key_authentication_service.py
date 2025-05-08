from datetime import datetime
import logging
from fastapi import HTTPException
from fastapi.security import APIKeyHeader

from models.api_key_model import APIKeyModel
from services.interfaces.api_key_authentication_interface import IAPIKeyAuthenticationService
from repository import IRepository

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class APIKeyAuthenticationService(IAPIKeyAuthenticationService):
    def __init__(self, root_key: str, repository: IRepository):
        self.logger = logging.getLogger("app")
        self.repository = repository
        self.root_key = root_key
        
    async def authenticate_api_key(self, api_key):
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is missing",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        if api_key == self.root_key:
            rootKeyData = {
                "id": "",
                "name": "Development API Key",
                "key": api_key,
                "role": "root",
                "user_id": "",
                "team_id": "",
                "created_at": datetime.min,
            }
            return APIKeyModel(**rootKeyData)

        # Check if it's a valid user API key
        api_key_doc = await self.repository.get_api_key_by_key(api_key)
        
        if not api_key_doc:
            self.logger.warning(f"Invalid API key attempt")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        return api_key_doc