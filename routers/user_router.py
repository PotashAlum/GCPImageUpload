from fastapi import APIRouter
from typing import List
import logging

from models import UserModel
from dependencies import user_service

# Initialize router
router = APIRouter(prefix="/users", tags=["users"])

# Get the application logger
app_logger = logging.getLogger("app")

@router.post("/", response_model=UserModel, status_code=201)
async def create_user(username, email, team_id):
    return await user_service.create_user(username, email, team_id)

@router.get("/{user_id}", response_model=UserModel)
async def get_user(user_id: str):
    return await user_service.get_user(user_id)

@router.get("/", response_model=List[UserModel])
async def list_users(
    skip: int = 0, 
    limit: int = 10,
):
    return await user_service.list_users(skip, limit)

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str):
    await user_service.delete_user(user_id)
    return None