from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import logging

from models import UserModel

from dependencies import repository

# Initialize router
router = APIRouter(prefix="/users", tags=["users"])

# Get the application logger
app_logger = logging.getLogger("app")

@router.post("/", response_model=UserModel, status_code=201)
async def create_user(username, email, team_id):
    app_logger.info(f"Creating new user: {username}")
    
    # Check if team exists
    team = await repository.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if username already exists
    if await repository.get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    if await repository.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    
    user_db = {
        "id": user_id,
        "username": username,
        "email": email,
        "team_id": team_id,
        "created_at": created_at
    }
    
    await repository.create_user(user_db)
    return {**user_db}

@router.get("/{user_id}", response_model=UserModel)
async def get_user(user_id: str):
    
    user = await repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/", response_model=List[UserModel])
async def list_users(
    skip: int = 0, 
    limit: int = 10,
):
    users = await repository.get_users(skip, limit)
    return users

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str):
    
    # Check if user exists
    existing_user = await repository.get_user_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # First, delete all API keys associated with the user
    await repository.delete_user_api_keys(user_id)
    
    # Delete the user record
    delete_result = await repository.delete_user(user_id)
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return None
