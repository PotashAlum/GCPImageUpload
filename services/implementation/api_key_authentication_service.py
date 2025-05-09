from datetime import datetime
import logging
import hashlib
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
        self.KEY_PREFIX_LENGTH = 8  # Must match value in APIKeyManagementService
        self.PBKDF2_ITERATIONS = 100000  # Must match value in APIKeyManagementService
        
    async def authenticate_api_key(self, api_key):
        """Authenticate an API key without storing the actual key in the database"""
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key is missing",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # Special case for root key
        if api_key == self.root_key:
            root_key_data = {
                "id": "root",
                "name": "Root API Key",
                "key_prefix": "",
                "key_hash": "",
                "key_salt": "",
                "role": "root",
                "user_id": "root",
                "team_id": "",
                "created_at": datetime.now(),
            }
            return APIKeyModel(**root_key_data)

        # Extract prefix from provided key for efficient lookup
        if len(api_key) < self.KEY_PREFIX_LENGTH:
            self.logger.warning(f"API key too short")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        key_prefix = api_key[:self.KEY_PREFIX_LENGTH]
        
        # Find potential matching keys by prefix
        potential_keys = await self.repository.api_keys.get_api_keys_by_prefix(key_prefix)
        
        if not potential_keys:
            self.logger.warning(f"No API keys found with prefix {key_prefix}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # Check each potential key by verifying the hash
        for stored_key in potential_keys:
            # Compute hash of provided key with the stored salt and iterations
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256', 
                api_key.encode(), 
                stored_key.key_salt.encode(), 
                self.PBKDF2_ITERATIONS
            ).hex()
            
            # If hashes match, this is the right key
            if computed_hash == stored_key.key_hash:
                return stored_key
        
        # No matching key found
        self.logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )