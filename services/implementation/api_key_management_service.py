import logging
import secrets
from typing import List
import uuid
import hashlib
import os
from datetime import datetime
from fastapi import HTTPException
from models import APIKeyModel, APIKeyCreateResponse
from services.interfaces.api_key_management_interface import IAPIKeyManagementService
from repository import IRepository

class APIKeyManagementService(IAPIKeyManagementService):
    def __init__(self, repository: IRepository):
        self.logger = logging.getLogger("app")
        self.repository = repository
        self.KEY_PREFIX_LENGTH = 8  # Length of key prefix to store for lookup
        self.PBKDF2_ITERATIONS = 100000  # Number of iterations for PBKDF2

    async def create_api_key(self, name, role, user_id, team_id) -> APIKeyCreateResponse:
        """Create a new API key with secure hashing"""
        api_key_id = str(uuid.uuid4())
        api_key_value = f"sk_{secrets.token_urlsafe(32)}"
        created_at = datetime.now()
        
        # Store only the prefix for lookup
        key_prefix = api_key_value[:self.KEY_PREFIX_LENGTH]
        
        # Generate a random salt for this key
        salt = os.urandom(32).hex()
        
        # Hash the API key using PBKDF2 (more secure than simple hashing)
        # In a production environment, consider using Argon2 instead
        key_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            api_key_value.encode(), 
            salt.encode(), 
            self.PBKDF2_ITERATIONS
        ).hex()
        
        # Store the hash and salt, NOT the actual key
        api_key_data = {
            "id": api_key_id,
            "name": name,
            "key_prefix": key_prefix,
            "key_hash": key_hash,
            "key_salt": salt,
            "role": role,
            "user_id": user_id,
            "team_id": team_id,
            "created_at": created_at,
        }
        
        # Store in database (without the actual key)
        await self.repository.api_keys.create_api_key(api_key_data)
        self.logger.info(f"Created new API key {api_key_id}")
        
        # Return the complete response with the actual key
        # This is the ONLY time the key is available in full
        return APIKeyCreateResponse(
            id=api_key_id,
            name=name,
            key=api_key_value,  # Only time we return the full key
            role=role,
            user_id=user_id,
            team_id=team_id,
            created_at=created_at
        )

    async def list_api_keys(self) -> list[APIKeyModel]:
        api_keys = await self.repository.api_keys.list_api_keys()
        return api_keys

    async def get_api_key_by_id(self, api_key_id) -> APIKeyModel:
        api_key = await self.repository.api_keys.get_api_key_by_id(api_key_id)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return api_key

    async def get_api_key_by_key(self, api_key: str) -> APIKeyModel:
        """
        Get API key information by verifying the provided key.
        Note: This method performs the same verification as the authentication service
        but is included in the management service for completeness.
        
        Args:
            api_key: The full API key to verify
            
        Returns:
            APIKeyModel if key is valid
            
        Raises:
            HTTPException: If API key is not found or invalid
        """
        if not api_key or len(api_key) < self.KEY_PREFIX_LENGTH:
            raise HTTPException(status_code=404, detail="Invalid API key format")
            
        # Extract prefix for efficient lookup
        key_prefix = api_key[:self.KEY_PREFIX_LENGTH]
        
        # Find potential matching keys by prefix
        potential_keys = await self.repository.api_keys.get_api_keys_by_prefix(key_prefix)
        
        if not potential_keys:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Check each potential key by verifying the hash
        for stored_key in potential_keys:
            # Compute hash of provided key with the stored salt
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
        raise HTTPException(status_code=404, detail="API key not found")

    async def get_api_keys_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[APIKeyModel]:
        """
        Get API keys for a specific user
        
        Args:
            user_id: The user ID to get API keys for
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of API key models
        """
        api_keys = await self.repository.api_keys.get_api_keys_by_user_id(user_id, skip, limit)
        return api_keys

    async def delete_api_key(self, api_key_id: str):
        # First verify the API key exists
        api_key = await self.repository.api_keys.get_api_key_by_id(api_key_id)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
            
        await self.repository.api_keys.delete_api_key(api_key_id)
        self.logger.info(f"Deleted API key {api_key_id}")