from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class APIKeyModel(BaseModel):
    id: str
    name: str
    key_prefix: str = Field(description="First 8 characters of the API key for lookup")
    key_hash: str = Field(description="Hashed API key for verification")
    key_salt: str = Field(description="Unique salt used when hashing the API key")
    role: str  # "user", "admin", or "root"
    user_id: str
    team_id: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "apikey789",
                "name": "Development API Key",
                "key_prefix": "sk_test_a",
                "key_hash": "5a41c0f1e351c5a3b6878d1162421c449c8f69c0b07972b7f6e9a4...",
                "key_salt": "8f7189ea87194e3c9f86ad89f341e45a...",
                "role": "user",
                "user_id": "user123",
                "team_id": "team456",
                "created_at": "2025-05-01T12:00:00Z",
            }
        }


class APIKeyCreateResponse(BaseModel):
    """Response model when creating a new API key - includes the full API key"""
    id: str
    name: str
    key: str = Field(description="Full API key - only returned during creation")
    role: str
    user_id: str
    team_id: str
    created_at: datetime