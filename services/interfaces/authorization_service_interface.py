# services/interfaces/authorization_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Optional

from models.api_key_model import APIKeyModel

class IAuthorizationService(ABC):
    """
    Abstract base class defining the interface for authorization functionality.
    Implementations should provide permission checking and resource ownership verification.
    """

    @abstractmethod
    async def authorize_request(self, method: str, path: str, api_key_info: APIKeyModel, path_params: Dict) -> bool:
        """
        Authorize a request based on the API key information and request details.
        
        Args:
            method: HTTP method of the request
            path: Path of the request
            api_key_info: Information about the authenticated API key
            path_params: Extracted path parameters
            
        Returns:
            True if authorized, raises exception otherwise
            
        Raises:
            HTTPException: When authorization fails
        """
        pass
    
    @abstractmethod
    def extract_path_parameters(self, path: str) -> Dict[str, str]:
        """
        Extract resource IDs from the path
        
        Args:
            path: The request path
            
        Returns:
            Dictionary of extracted parameters
        """
        pass