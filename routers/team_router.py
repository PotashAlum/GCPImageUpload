from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
import uuid
from datetime import datetime
import logging

from models import TeamModel

from dependencies import repository, bucket


# Initialize router
router = APIRouter(prefix="/teams", tags=["teams"])

# Get the application logger
app_logger = logging.getLogger("app")

@router.post("/", response_model=TeamModel, status_code=201)
async def create_team(name, description):
    app_logger.info(f"Creating new team: {name}")
    
    # Check if team name already exists
    if await repository.get_team_by_name(name):
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
    
    await repository.create_team(team_db)
    return {**team_db}

@router.get("/{team_id}", response_model=TeamModel)
async def get_team(team_id: str):
    team = await repository.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team

@router.get("/", response_model=List[TeamModel])
async def list_teams(
    skip: int = 0, 
    limit: int = 10
):
    teams = await repository.get_teams(skip, limit)
    return teams

@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: str):    
    # Check if team exists
    team = await repository.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if there are any users in the team
    users_in_team = await repository.get_users_count_by_team_id(team_id)
    if users_in_team > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete team with active users. Reassign or delete users first."
        )
    
    # Delete all images associated with the team
    team_images = await repository.get_images_by_team_id(team_id)
    
    # Delete the actual image files from GCS
    for image in team_images:
        blob = bucket.blob(image["filename"])
        blob.delete()
    
    # Delete image records from the database
    await repository.delete_images_by_team_id(team_id)
    
    # Delete the team record
    delete_result = await repository.delete_team(team_id)
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return None
