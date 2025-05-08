from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserModel(BaseModel):
    id: str
    username: str
    email: str
    team_id: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user123",
                "username": "johndoe",
                "email": "john@example.com",
                "team_id": "team456",
                "created_at": "2025-05-01T12:00:00Z",
            }
        }