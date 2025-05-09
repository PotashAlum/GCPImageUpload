from abc import ABC, abstractmethod
from typing import List
from models import UserModel

class IUserService(ABC):
    """
    Interface for user service operations.
    Defines the contract that any user service implementation must follow.
    """
    
    @abstractmethod
    async def create_user(
        self,
        username: str,
        email: str,
        team_id: str
    ) -> UserModel:
        """
        Create a new user
        
        Args:
            username: Username for the new user
            email: Email for the new user
            team_id: ID of the team the user belongs to
            
        Returns:
            The created user model
            
        Raises:
            HTTPException: If team not found or username/email already exists
        """
        pass
    
    @abstractmethod
    async def get_user(
        self,
        user_id: str
    ) -> UserModel:
        """
        Get a user by ID
        
        Args:
            user_id: ID of the user
            
        Returns:
            User model
            
        Raises:
            HTTPException: If user not found
        """
        pass
    
    @abstractmethod
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> List[UserModel]:
        """
        List all users with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of user models
        """
        pass
    
    @abstractmethod
    async def delete_user(
        self,
        user_id: str
    ) -> None:
        """
        Delete a user by ID
        
        Args:
            user_id: ID of the user
            
        Raises:
            HTTPException: If user not found
        """
        pass