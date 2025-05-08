from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ImageMetaDataModel(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    color_space: Optional[str] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None
    camera_model: Optional[str] = None
    capture_date: Optional[datetime] = None


class ImageModel(BaseModel):
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    user_id: str
    team_id: str
    filename: str
    content_type: str
    size: int
    url: str
    metadata: Optional[ImageMetaDataModel] = None
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