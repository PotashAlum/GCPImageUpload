from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TeamModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "team456",
                "name": "Marketing Team",
                "description": "Team responsible for marketing activities",
                "created_at": "2025-05-01T12:00:00Z"
            }
        }