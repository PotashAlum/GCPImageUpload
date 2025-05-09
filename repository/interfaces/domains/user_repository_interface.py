from abc import ABC, abstractmethod
from typing import List, Optional
from models import UserModel

class IUserRepository(ABC):
    @abstractmethod
    async def create_user(self, user) -> UserModel:
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        pass
    
    @abstractmethod
    async def get_users(self, skip: int, limit: int) -> List[UserModel]:
        pass
    
    @abstractmethod
    async def get_users_by_team_id(self, team_id: str, skip: int = 0, limit: int = 10) -> List[UserModel]:
        pass
    
    @abstractmethod
    async def get_users_count_by_team_id(self, team_id: str) -> int:
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> None:
        pass