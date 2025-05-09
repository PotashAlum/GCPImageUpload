import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional

from models import ImageModel
from dependencies import image_service

app_logger = logging.getLogger("app")
router = APIRouter(prefix="/images", tags=["Images"])

@router.post("/", response_model=ImageModel, status_code=201)
async def upload_team_image(
    user_id: str,
    team_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated list of tags
    file: UploadFile = File(...),
):    
    return await image_service.upload_team_image(
        user_id=user_id,
        team_id=team_id,
        title=title,
        description=description,
        tags=tags,
        file=file
    )

@router.get("/", response_model=List[ImageModel])
async def list_team_images(
    team_id: str,
    skip: int = 0,
    limit: int = 10,
):
    return await image_service.list_team_images(
        team_id=team_id,
        skip=skip,
        limit=limit
    )

@router.get("/{image_id}", response_model=ImageModel)
async def get_team_image(image_id: str):
    return await image_service.get_team_image(image_id)

@router.delete("/{image_id}", status_code=204)
async def delete_image(image_id: str):
    await image_service.delete_image(image_id)
    return None