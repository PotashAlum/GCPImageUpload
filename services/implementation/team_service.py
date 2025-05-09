import logging
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException
from models import TeamModel, APIKeyModel, ImageModel, UserModel
from repository import IRepository
from services.interfaces.team_service_interface import ITeamService
from services.interfaces.storage_service_interface import IStorageService

class TeamService(ITeamService):
    def __init__(self, repository: IRepository, storage_service: IStorageService):
        self.logger = logging.getLogger("app")
        self.repository = repository
        self.storage_service = storage_service
    
    async def create_team(
        self,
        name: str,
        description: str
    ) -> TeamModel:
        self.logger.info(f"Creating new team: {name}")
        
        # Check if team name already exists
        if await self.repository.teams.get_team_by_name(name):
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
        
        await self.repository.teams.create_team(team_db)
        return {**team_db}
    
    async def get_team(
        self,
        team_id: str
    ) -> TeamModel:
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return team
    
    async def list_teams(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> List[TeamModel]:
        teams = await self.repository.teams.get_teams(skip, limit)
        return teams
    
    async def delete_team(
        self,
        team_id: str
    ) -> None:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Check if there are any users in the team
        users_in_team = await self.repository.users.get_users_count_by_team_id(team_id)
        if users_in_team > 0:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete team with active users. Reassign or delete users first."
            )
        
        # Delete all images associated with the team
        team_images = await self.repository.images.get_images_by_team_id(team_id)
        
        # Delete the actual image files from storage
        for image in team_images:
            await self.storage_service.delete_file(image["filename"])
        
        # Delete image records from the database
        await self.repository.images.delete_images_by_team_id(team_id)
        
        # Delete the team record
        await self.repository.teams.delete_team(team_id)
        
        return None
    
    async def list_team_api_keys(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[APIKeyModel]:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # This is a bit tricky since we need to get all API keys for all users in the team
        # First, get all users in the team
        team_users = await self.repository.users.get_users_by_team_id(team_id, 0, 1000)  # Assuming a reasonable limit
        
        # Get all API keys for each user
        all_api_keys = []
        for user in team_users:
            user_api_keys = await self.repository.api_keys.get_api_keys_by_user_id(user.id, 0, 100)  # Assuming a reasonable limit
            all_api_keys.extend(user_api_keys)
        
        # Apply pagination manually (not ideal, but works for this example)
        paginated_api_keys = all_api_keys[skip:skip+limit]
        
        return paginated_api_keys
    
    async def get_team_api_key(
        self,
        team_id: str,
        api_key_id: str
    ) -> APIKeyModel:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get the API key
        api_key = await self.repository.api_keys.get_api_key_by_id(api_key_id)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Check if API key belongs to the team
        if api_key.team_id != team_id:
            raise HTTPException(status_code=403, detail="API key does not belong to this team")
        
        return api_key
    
    async def list_team_users(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[UserModel]:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get all users in the team
        users = await self.repository.users.get_users_by_team_id(team_id, skip, limit)
        
        return users
    
    async def get_team_user(
        self,
        team_id: str,
        user_id: str
    ) -> UserModel:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get the user
        user = await self.repository.users.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user belongs to the team
        if user.team_id != team_id:
            raise HTTPException(status_code=403, detail="User does not belong to this team")
        
        return user
    
    async def list_team_images(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[ImageModel]:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get all images for the team
        images = await self.repository.images.get_images_by_team_id(team_id, skip, limit)
        
        return images
    
    async def get_team_image(
        self,
        team_id: str,
        image_id: str
    ) -> ImageModel:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get the image
        image = await self.repository.images.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if image belongs to the team
        if image.team_id != team_id:
            raise HTTPException(status_code=403, detail="Image does not belong to this team")
        
        # Update the URL if it's expired
        image.url = await self.storage_service.generate_signed_url(
            path=image.filename,
            expiration=timedelta(hours=1)
        )
        
        return image
    
    async def delete_team_image(
        self,
        team_id: str,
        image_id: str
    ) -> None:
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get the image
        image = await self.repository.images.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if image belongs to the team
        if image.team_id != team_id:
            raise HTTPException(status_code=403, detail="Image does not belong to this team")
        
        # Delete from storage
        await self.storage_service.delete_file(image.filename)
        
        # Delete from database
        await self.repository.images.delete_image(image_id)
        
        self.logger.info(f"Image {image_id} deleted from team {team_id}")
        return None