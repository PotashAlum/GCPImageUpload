from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime, timedelta
import logging

from models import TeamModel

from dependencies import repository, bucket
from models import APIKeyModel, ImageModel, UserModel

# Initialize router
router = APIRouter(prefix="/teams", tags=["teams"])

# Get the application logger
app_logger = logging.getLogger("app")

@router.post("/", response_model=TeamModel, status_code=201)
async def create_team(name, description):
    app_logger.info(f"Creating new team: {name}")
    
    # Check if team name already exists
    if await repository.teams.get_team_by_name(name):
        raise HTTPException(status_code=400, detail="Team name already exists")
    
    # Create new team
    team_id = str(uuid.uuid4())
    created_at = datetime.now()
    
    team_db = {
        "id": team_id,
        "name": name,
        "description": description,
        "created_at": created_at
    }
    
    await repository.teams.create_team(team_db)
    return {**team_db}

@router.get("/{team_id}", response_model=TeamModel)
async def get_team(team_id: str):
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team

@router.get("/", response_model=List[TeamModel])
async def list_teams(
    skip: int = 0, 
    limit: int = 10
):
    teams = await repository.teams.get_teams(skip, limit)
    return teams

@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: str):    
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if there are any users in the team
    users_in_team = await repository.users.get_users_count_by_team_id(team_id)
    if users_in_team > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete team with active users. Reassign or delete users first."
        )
    
    # Delete all images associated with the team
    team_images = await repository.images.get_images_by_team_id(team_id)
    
    # Delete the actual image files from GCS
    for image in team_images:
        blob = bucket.blob(image["filename"])
        blob.delete()
    
    # Delete image records from the database
    await repository.images.delete_images_by_team_id(team_id)
    
    # Delete the team record
    await repository.teams.delete_team(team_id)
    
    return None

@router.get("/{team_id}/api-keys", response_model=List[APIKeyModel])
async def list_team_api_keys(
    team_id: str,
    skip: int = 0,
    limit: int = 10
):
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # This is a bit tricky since we need to get all API keys for all users in the team
    # First, get all users in the team
    team_users = await repository.users.get_users_by_team_id(team_id, 0, 1000)  # Assuming a reasonable limit
    
    # Get all API keys for each user
    all_api_keys = []
    for user in team_users:
        user_api_keys = await repository.api_keys.get_api_keys_by_user_id(user.id, 0, 100)  # Assuming a reasonable limit
        all_api_keys.extend(user_api_keys)
    
    # Apply pagination manually (not ideal, but works for this example)
    paginated_api_keys = all_api_keys[skip:skip+limit]
    
    return paginated_api_keys

@router.get("/{team_id}/api-keys/{api_key_id}", response_model=APIKeyModel)
async def get_team_api_key(
    team_id: str,
    api_key_id: str
):
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get the API key
    api_key = await repository.api_keys.get_api_key_by_id(api_key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Check if API key belongs to the team
    if api_key.team_id != team_id:
        raise HTTPException(status_code=403, detail="API key does not belong to this team")
    
    return api_key

@router.get("/{team_id}/users", response_model=List[UserModel])
async def list_team_users(
    team_id: str,
    skip: int = 0,
    limit: int = 10
):
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get all users in the team
    users = await repository.users.get_users_by_team_id(team_id, skip, limit)
    
    return users

@router.get("/{team_id}/users/{user_id}", response_model=UserModel)
async def get_team_user(
    team_id: str,
    user_id: str
):
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get the user
    user = await repository.users.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user belongs to the team
    if user.team_id != team_id:
        raise HTTPException(status_code=403, detail="User does not belong to this team")
    
    return user

@router.get("/{team_id}/images", response_model=List[ImageModel])
async def list_team_images(
    team_id: str,
    skip: int = 0,
    limit: int = 10
):
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get all images for the team
    images = await repository.images.get_images_by_team_id(team_id, skip, limit)
    
    return images

@router.get("/{team_id}/images/{image_id}", response_model=ImageModel)
async def get_team_image(
    team_id: str,
    image_id: str
):
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get the image
    image = await repository.images.get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if image belongs to the team
    if image.team_id != team_id:
        raise HTTPException(status_code=403, detail="Image does not belong to this team")
    
    # Update the URL if it's expired
    blob = bucket.blob(image.filename)
    expiration = timedelta(hours=1)
    image.url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET"
    )
    
    return image

@router.delete("/{team_id}/images/{image_id}", status_code=204)
async def delete_team_image(
    team_id: str,
    image_id: str
):
    # Check if team exists
    team = await repository.teams.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get the image
    image = await repository.images.get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if image belongs to the team
    if image.team_id != team_id:
        raise HTTPException(status_code=403, detail="Image does not belong to this team")
    
    # Delete from GCS
    blob = bucket.blob(image.filename)
    blob.delete()
    
    # Delete from database
    await repository.images.delete_image(image_id)
    
    app_logger.info(f"Image {image_id} deleted from team {team_id}")
    return None