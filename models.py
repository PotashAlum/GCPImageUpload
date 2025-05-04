from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "user123",
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "created_at": "2025-05-01T12:00:00Z"
            }
        }

class ImageBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class ImageCreate(ImageBase):
    pass

class Image(ImageBase):
    id: str
    user_id: str
    filename: str
    content_type: str
    size: int
    url: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "img123",
                "user_id": "user123",
                "title": "My vacation photo",
                "description": "Beautiful sunset at the beach",
                "filename": "sunset.jpg",
                "content_type": "image/jpeg",
                "size": 1024567,
                "url": "https://storage.googleapis.com/user-images-bucket/user123/img123_sunset.jpg",
                "created_at": "2025-05-01T12:30:00Z"
            }
        }
