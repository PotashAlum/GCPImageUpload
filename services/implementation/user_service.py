import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import HTTPException
from models import UserModel
from repository import IRepository
from services.interfaces.user_service_interface import IUserService

class UserService(IUserService):
    def __init__(self, repository: IRepository):
        self.logger = logging.getLogger("app")
        self.repository = repository
    
    async def create_user(
        self,
        username: str,
        email: str,
        team_id: str
    ) -> UserModel:
        self.logger.info(f"Creating new user: {username}")
        
        # Check if team exists
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Check if username already exists
        if await self.repository.users.get_user_by_username(username):
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email already exists
        if await self.repository.users.get_user_by_email(email):
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
        
        await self.repository.users.create_user(user_db)
        return {**user_db}
    
    async def get_user(
        self,
        user_id: str
    ) -> UserModel:
        user = await self.repository.users.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> List[UserModel]:
        users = await self.repository.users.get_users(skip, limit)
        return users
    
    async def delete_user(
        self,
        user_id: str
    ) -> None:
        # Check if user exists
        existing_user = await self.repository.users.get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # First, delete all API keys associated with the user
        await self.repository.api_keys.delete_user_api_keys(user_id)
        
        # Delete the user record
        await self.repository.users.delete_user(user_id)
        
        return None