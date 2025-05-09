from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogModel(BaseModel):
    id: str
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    status: str
    status_code: int
    ip_address: str
    user_agent: str
    details: Optional[dict] = None
    timestamp: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "log123",
                "user_id": "user123",
                "team_id": "team123",
                "action": "GET",
                "resource_type": "image",
                "resource_id": "img123",
                "status": "success",
                "status_code": 200,
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "details": {"message": "ImageModel viewed"},
                "timestamp": "2025-05-01T12:35:00Z"
            }
        }