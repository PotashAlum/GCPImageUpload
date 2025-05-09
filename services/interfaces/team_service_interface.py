from abc import ABC, abstractmethod
from typing import List
from models import TeamModel, APIKeyModel, ImageModel, UserModel

class ITeamService(ABC):
    """
    Interface for team service operations.
    Defines the contract that any team service implementation must follow.
    """
    
    @abstractmethod
    async def create_team(
        self,
        name: str,
        description: str
    ) -> TeamModel:
        """
        Create a new team
        
        Args:
            name: Name of the team
            description: Description of the team
            
        Returns:
            The created team model
            
        Raises:
            HTTPException: If team name already exists
        """
        pass
    
    @abstractmethod
    async def get_team(
        self,
        team_id: str
    ) -> TeamModel:
        """
        Get a team by ID
        
        Args:
            team_id: ID of the team
            
        Returns:
            Team model
            
        Raises:
            HTTPException: If team not found
        """
        pass
    
    @abstractmethod
    async def list_teams(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> List[TeamModel]:
        """
        List all teams with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of team models
        """
        pass
    
    @abstractmethod
    async def delete_team(
        self,
        team_id: str
    ) -> None:
        """
        Delete a team by ID
        
        Args:
            team_id: ID of the team
            
        Raises:
            HTTPException: If team not found or has active users
        """
        pass
    
    @abstractmethod
    async def list_team_api_keys(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[APIKeyModel]:
        """
        List API keys for a team
        
        Args:
            team_id: ID of the team
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of API key models
            
        Raises:
            HTTPException: If team not found
        """
        pass
    
    @abstractmethod
    async def get_team_api_key(
        self,
        team_id: str,
        api_key_id: str
    ) -> APIKeyModel:
        """
        Get a specific API key for a team
        
        Args:
            team_id: ID of the team
            api_key_id: ID of the API key
            
        Returns:
            API key model
            
        Raises:
            HTTPException: If team or API key not found, or API key doesn't belong to team
        """
        pass
    
    @abstractmethod
    async def list_team_users(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[UserModel]:
        """
        List users for a team
        
        Args:
            team_id: ID of the team
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of user models
            
        Raises:
            HTTPException: If team not found
        """
        pass
    
    @abstractmethod
    async def get_team_user(
        self,
        team_id: str,
        user_id: str
    ) -> UserModel:
        """
        Get a specific user for a team
        
        Args:
            team_id: ID of the team
            user_id: ID of the user
            
        Returns:
            User model
            
        Raises:
            HTTPException: If team or user not found, or user doesn't belong to team
        """
        pass
    
    @abstractmethod
    async def list_team_images(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[ImageModel]:
        """
        List images for a team
        
        Args:
            team_id: ID of the team
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of image models
            
        Raises:
            HTTPException: If team not found
        """
        pass
    
    @abstractmethod
    async def get_team_image(
        self,
        team_id: str,
        image_id: str
    ) -> ImageModel:
        """
        Get a specific image for a team
        
        Args:
            team_id: ID of the team
            image_id: ID of the image
            
        Returns:
            Image model with updated URL
            
        Raises:
            HTTPException: If team or image not found, or image doesn't belong to team
        """
        pass
    
    @abstractmethod
    async def delete_team_image(
        self,
        team_id: str,
        image_id: str
    ) -> None:
        """
        Delete a specific image for a team
        
        Args:
            team_id: ID of the team
            image_id: ID of the image
            
        Raises:
            HTTPException: If team or image not found, or image doesn't belong to team
        """
        pass