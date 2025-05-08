from abc import ABC, abstractmethod
from models import APIKeyModel
from typing import List


class IAPIKeyManagementService(ABC):
    """
    Interface for API key service operations.
    Defines the contract that any API key service implementation must follow.
    """
    
    @abstractmethod
    async def create_api_key(self, name: str, role: str, user_id: str, team_id: str) -> APIKeyModel:
        """
        Create a new API key with the specified name
        
        Args:
            name: Name identifier for the API key
            role: either admin or user, defines what operations the key can be used for
            user_id: The user this key is attached to
            team_id: The team that the user is part of
            
        Returns:
            Dictionary containing the created API key data
        """
        pass
    
    @abstractmethod
    async def list_api_keys(self) -> List[APIKeyModel]:
        """
        List all available API keys
        
        Returns:
            List of API key data dictionaries
        """
        pass
    
    @abstractmethod
    async def get_api_key_by_id(self, api_key_id: str) -> APIKeyModel:
        """
        Retrieve an API key by its ID
        
        Args:
            api_key_id: Unique identifier for the API key
            
        Returns:
            API key data dictionary
            
        Raises:
            HTTPException: If API key is not found
        """
        pass

    @abstractmethod
    async def get_api_key_by_key(self, api_key: str) -> APIKeyModel:
        """
        Retrieve info about an API key by its key value
        
        Args:
            api_key: The key
            
        Returns:
            API key data
            
        Raises:
            HTTPException: If API key is not found
        """
        pass
    
    @abstractmethod
    async def delete_api_key(self, api_key_id: str) -> None:
        """
        Delete an API key by its ID
        
        Args:
            api_key_id: Unique identifier for the API key
            
        Raises:
            HTTPException: If API key is not found
        """
        pass