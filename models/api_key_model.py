from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class APIKeyModel(BaseModel):
    id: str
    name: str
    key: str
    role: str  # "user", "admin", or "root"
    user_id: str
    team_id: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "apikey789",
                "name": "Development API Key",
                "key": "sk_test_abcdefghijklmnopqrstuvwxyz",
                "role": "user",
                "user_id": "user123",
                "team_id": "team456",
                "created_at": "2025-05-01T12:00:00Z",
            }
        }