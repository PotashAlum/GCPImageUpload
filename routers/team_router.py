from fastapi import APIRouter, HTTPException
from typing import List
import logging

from models import TeamModel, APIKeyModel, ImageModel, UserModel
from dependencies import team_service

# Initialize router
router = APIRouter(prefix="/teams", tags=["teams"])

# Get the application logger
app_logger = logging.getLogger("app")

@router.post("/", response_model=TeamModel, status_code=201)
async def create_team(name, description):
    return await team_service.create_team(name, description)

@router.get("/{team_id}", response_model=TeamModel)
async def get_team(team_id: str):
    return await team_service.get_team(team_id)

@router.get("/", response_model=List[TeamModel])
async def list_teams(
    skip: int = 0, 
    limit: int = 10
):
    return await team_service.list_teams(skip, limit)

@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: str):
    await team_service.delete_team(team_id)
    return None

@router.get("/{team_id}/api-keys", response_model=List[APIKeyModel])
async def list_team_api_keys(
    team_id: str,
    skip: int = 0,
    limit: int = 10
):
    return await team_service.list_team_api_keys(team_id, skip, limit)

@router.get("/{team_id}/api-keys/{api_key_id}", response_model=APIKeyModel)
async def get_team_api_key(
    team_id: str,
    api_key_id: str
):
    return await team_service.get_team_api_key(team_id, api_key_id)

@router.get("/{team_id}/users", response_model=List[UserModel])
async def list_team_users(
    team_id: str,
    skip: int = 0,
    limit: int = 10
):
    return await team_service.list_team_users(team_id, skip, limit)

@router.get("/{team_id}/users/{user_id}", response_model=UserModel)
async def get_team_user(
    team_id: str,
    user_id: str
):
    return await team_service.get_team_user(team_id, user_id)

@router.get("/{team_id}/images", response_model=List[ImageModel])
async def list_team_images(
    team_id: str,
    skip: int = 0,
    limit: int = 10
):
    return await team_service.list_team_images(team_id, skip, limit)

@router.get("/{team_id}/images/{image_id}", response_model=ImageModel)
async def get_team_image(
    team_id: str,
    image_id: str
):
    return await team_service.get_team_image(team_id, image_id)

@router.delete("/{team_id}/images/{image_id}", status_code=204)
async def delete_team_image(
    team_id: str,
    image_id: str
):
    await team_service.delete_team_image(team_id, image_id)
    return None