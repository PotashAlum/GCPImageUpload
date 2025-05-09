from repository.interfaces.domains.user_repository_interface import IUserRepository
from models import UserModel
from typing import List, Optional


class MongoDBUserRepository(IUserRepository):
    """MongoDB implementation of the user repository"""
    
    def __init__(self, db, logger=None):
        self.db = db
        self.logger = logger
    
    async def setup_indexes(self):
        """Setup all required indexes for the users collection"""
        await self.db.create_index("id", unique=True)
        await self.db.create_index("username", unique=True)
        await self.db.create_index("email", unique=True)
        await self.db.create_index("team_id")
    
    async def create_user(self, user) -> UserModel:
        await self.db.insert_one(user)
        return UserModel(**user)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        user_data = await self.db.find_one({"id": user_id})
        return UserModel(**user_data) if user_data else None
    
    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        user_data = await self.db.find_one({"username": username})
        return UserModel(**user_data) if user_data else None
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        user_data = await self.db.find_one({"email": email})
        return UserModel(**user_data) if user_data else None
    
    async def get_users(self, skip: int, limit: int) -> List[UserModel]:
        users_data = await self.db.find().skip(skip).limit(limit).to_list(limit)
        return [UserModel(**user) for user in users_data]
    
    async def get_users_by_team_id(self, team_id: str, skip: int = 0, limit: int = 10) -> List[UserModel]:
        users_data = await self.db.find({"team_id": team_id}).skip(skip).limit(limit).to_list(limit)
        return [UserModel(**user) for user in users_data]
    
    async def get_users_count_by_team_id(self, team_id: str) -> int:
        return await self.db.count_documents({"team_id": team_id})
    
    async def delete_user(self, user_id: str) -> None:
        await self.db.delete_one({"id": user_id})