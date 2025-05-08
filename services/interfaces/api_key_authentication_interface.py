from abc import ABC, abstractmethod
from typing import Optional

class IAPIKeyAuthenticationService(ABC):
    """
    Abstract base class defining the interface for authentication functionality.
    Implementations should provide user and root API key authentication
    """

    @abstractmethod
    async def authenticate_api_key(self, api_key: str) -> Optional[str]:
        """
        Authenticate a user API key.
        
        Args:
            api_key: The API key to authenticate
            
        Returns:
            key role or None
            
        Raises:
            HTTPException: When authentication fails
        """
        pass