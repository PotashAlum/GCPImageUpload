# services/implementation/authorization_service.py
from fastapi import HTTPException
import logging
from typing import Dict, Optional

from models.api_key_model import APIKeyModel
from repository.interfaces.repository_interface import IRepository
from services.interfaces.authorization_service_interface import IAuthorizationService

logger = logging.getLogger("app")

# Define permission rules with minimum required role
# Format: {HTTP_METHOD: {resource_path_pattern: minimum_role}}
PERMISSION_RULES = {
    "POST": {
        "teams": "root",
        "teams/{team_id}/api-keys": "admin",
        "teams/{team_id}/users": "admin",
        "teams/{team_id}/images": "user",
    },
    "PUT": {
        "teams/{team_id}": "admin",
        "teams/{team_id}/api-keys/{api_key_id}": "admin",
        "teams/{team_id}/users/{user_id}": "admin",
        "teams/{team_id}/images/{image_id}": "admin",
        "teams/{team_id}/users/{user_id}/images/{image_id}": "user",
    },
    "GET": {
        "teams": "root",
        "teams/{team_id}": "user",
        "teams/{team_id}/api-keys": "admin",
        "teams/{team_id}/api-keys/{api_key_id}": "admin",
        "teams/{team_id}/users": "user",
        "teams/{team_id}/users/{user_id}": "user",
        "teams/{team_id}/images": "user",
        "teams/{team_id}/images/{image_id}": "user",
        "teams/{team_id}/users/{user_id}/api-keys": "user",
        "teams/{team_id}/users/{user_id}/api-keys/{api_key_id}": "user",
        "teams/{team_id}/users/{user_id}/images": "user",
        "teams/{team_id}/users/{user_id}/images/{image_id}": "user",
        "audit-logs": "root",
    },
    "DELETE": {
        "teams/{team_id}": "root",
        "teams/{team_id}/api-keys/{api_key_id}": "admin",
        "teams/{team_id}/users/{user_id}": "admin",
        "teams/{team_id}/images/{image_id}": "admin",
        "teams/{team_id}/users/{user_id}/api-keys/{api_key_id}": "user",
        "teams/{team_id}/users/{user_id}/images/{image_id}": "user",
    }
}

# Role hierarchy for permission checks
ROLE_HIERARCHY = {
    "root": ["root", "admin", "user"],
    "admin": ["admin", "user"],
    "user": ["user"]
}

class AuthorizationService(IAuthorizationService):
    def __init__(self, repository: IRepository):
        self.repository = repository
        self.logger = logging.getLogger("app")
    
    def extract_path_parameters(self, path: str) -> Dict[str, str]:
        """Extract resource IDs from the path"""
        path_parts = path.split("/")
        params = {}
        
        # Extract IDs based on position and naming pattern
        for i in range(len(path_parts) - 1):
            if path_parts[i] == "teams" and i + 1 < len(path_parts):
                params["team_id"] = path_parts[i+1]
            elif path_parts[i] == "users" and i + 1 < len(path_parts):
                params["user_id"] = path_parts[i+1]
            elif path_parts[i] == "images" and i + 1 < len(path_parts):
                params["image_id"] = path_parts[i+1]
            elif path_parts[i] == "api-keys" and i + 1 < len(path_parts):
                params["api_key_id"] = path_parts[i+1]
        
        return params

    async def authorize_request(self, method: str, path: str, api_key_info: APIKeyModel, path_params: Dict) -> bool:
        """Perform all authorization checks for the request"""
        # Root can do anything
        if api_key_info.role == "root":
            return True
            
        # Find matching permission rule
        matched_pattern = self._find_matching_pattern(method, path)
        
        if not matched_pattern:
            self.logger.warning(f"No permission rule found for {method} {path}")
            raise HTTPException(
                status_code=403,
                detail="Access denied: No permission rule found",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Check if user's role is allowed for this pattern
        required_role = PERMISSION_RULES[method][matched_pattern]
        if not self._is_role_authorized(api_key_info.role, required_role):
            self.logger.warning(f"Role {api_key_info.role} not allowed for {method} {path}")
            raise HTTPException(
                status_code=403,
                detail="Access denied: Insufficient permissions",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Check resource ownership
        await self._verify_resource_ownership(api_key_info, path_params, method)
        
        return True
    
    def _is_role_authorized(self, user_role: str, required_role: str) -> bool:
        """
        Check if the user's role is sufficient for the required role
        """
        allowed_roles = ROLE_HIERARCHY.get(user_role, [])
        return required_role in allowed_roles
        
    def _find_matching_pattern(self, method: str, path: str) -> Optional[str]:
        """Find the most specific pattern matching the request path"""
        if method not in PERMISSION_RULES:
            return None
            
        path_parts = path.split("/")
        matching_patterns = []
        
        for pattern in PERMISSION_RULES[method]:
            pattern_parts = pattern.split("/")
            
            # Skip if length doesn't match
            if len(pattern_parts) != len(path_parts):
                continue
                
            # Check if pattern matches
            matches = True
            for i, (pattern_part, path_part) in enumerate(zip(pattern_parts, path_parts)):
                if pattern_part.startswith("{") and pattern_part.endswith("}"):
                    # Parameter placeholder, always matches
                    continue
                elif pattern_part != path_part:
                    matches = False
                    break
                    
            if matches:
                matching_patterns.append(pattern)
        
        if not matching_patterns:
            return None
            
        # Return the most specific pattern (with most static parts)
        return max(
            matching_patterns,
            key=lambda p: sum(1 for part in p.split("/") if not (part.startswith("{") and part.endswith("}")))
        )

    async def _verify_resource_ownership(self, api_key_info: APIKeyModel, path_params: Dict, method: str):
        """Verify that the user has ownership of the resources they're trying to access"""
        # Root can access anything
        if api_key_info.role == "root":
            return True
        
        # Check team access - user must be part of the team they're accessing
        if "team_id" in path_params and api_key_info.team_id != path_params["team_id"]:
            self.logger.warning(f"User attempted to access another team's resource")
            raise HTTPException(
                status_code=403,
                detail="Access denied: You can only access resources within your team",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # User ID access check - regular users can only access their own data
        if "user_id" in path_params:
            if api_key_info.role == "user" and api_key_info.user_id != path_params["user_id"]:
                self.logger.warning(f"User attempted to access another user's information")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: You can only access your own information",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            elif api_key_info.role == "admin":
                # Admin needs to verify user belongs to their team
                user = await self.repository.users.get_user_by_id(path_params["user_id"])
                if not user or user.team_id != api_key_info.team_id:
                    self.logger.warning(f"Admin attempted to access user from another team")
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: User does not belong to your team",
                        headers={"WWW-Authenticate": "ApiKey"},
                    )
        
        # API key access check
        if "api_key_id" in path_params:
            api_key = await self.repository.api_keys.get_api_key_by_id(path_params["api_key_id"])
            
            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")
                
            if api_key_info.role == "user" and api_key.user_id != api_key_info.user_id:
                self.logger.warning(f"User attempted to access another user's API key")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: You can only access your own API keys",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            elif api_key_info.role == "admin" and api_key.team_id != api_key_info.team_id:
                self.logger.warning(f"Admin attempted to access API key from another team")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: API key does not belong to your team",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
        
        # Image access check - extra verification for DELETE operations
        if "image_id" in path_params:
            image = await self.repository.images.get_image_by_id(path_params["image_id"])
            
            if not image:
                raise HTTPException(status_code=404, detail="Image not found")
                
            if image.team_id != api_key_info.team_id:
                self.logger.warning(f"User attempted to access image from another team")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: Image does not belong to your team",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
                
            # For DELETE operations, users can only delete their own images unless they are admins
            if method == "DELETE" and api_key_info.role == "user" and image.user_id != api_key_info.user_id:
                self.logger.warning(f"User attempted to delete another user's image")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: You can only delete your own images",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
        
        return True