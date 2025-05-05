from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str
    team_id: str
    full_name: Optional[str] = None

class User(UserBase):
    id: str
    team_id: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user123",
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "team_id": "team456",
                "created_at": "2025-05-01T12:00:00Z"
            }
        }

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id: str
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

class APIKeyBase(BaseModel):
    name: str
    expires_at: Optional[datetime] = None

class APIKeyCreate(APIKeyBase):
    pass

class APIKey(APIKeyBase):
    id: str
    user_id: str
    key: str
    created_at: datetime
    is_active: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "id": "apikey789",
                "user_id": "user123",
                "name": "Development API Key",
                "key": "sk_test_abcdefghijklmnopqrstuvwxyz",
                "created_at": "2025-05-01T12:00:00Z",
                "expires_at": "2026-05-01T12:00:00Z",
                "is_active": True
            }
        }

class ImageBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class ImageCreate(ImageBase):
    pass

class ImageMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    color_space: Optional[str] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None
    camera_model: Optional[str] = None
    capture_date: Optional[datetime] = None

class Image(ImageBase):
    id: str
    user_id: str
    team_id: str
    filename: str
    content_type: str
    size: int
    url: str
    metadata: Optional[ImageMetadata] = None
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "img123",
                "user_id": "user123",
                "team_id": "team456",
                "title": "My vacation photo",
                "description": "Beautiful sunset at the beach",
                "filename": "sunset.jpg",
                "content_type": "image/jpeg",
                "size": 1024567,
                "url": "https://storage.googleapis.com/user-images-bucket/team456/img123_sunset.jpg",
                "metadata": {
                    "width": 1920,
                    "height": 1080,
                    "format": "JPEG",
                    "color_space": "RGB",
                    "location": "Malibu, CA",
                    "tags": ["sunset", "beach", "vacation"],
                    "camera_model": "iPhone 14 Pro",
                    "capture_date": "2025-04-15T18:30:00Z"
                },
                "created_at": "2025-05-01T12:30:00Z"
            }
        }

class AuditLog(BaseModel):
    id: str
    user_id: Optional[str] = None
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
                "action": "GET",
                "resource_type": "image",
                "resource_id": "img123",
                "status": "success",
                "status_code": 200,
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "details": {"message": "Image viewed"},
                "timestamp": "2025-05-01T12:35:00Z"
            }
        }