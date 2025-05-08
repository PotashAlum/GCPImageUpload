from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from typing import Dict, Optional

from models.api_key_model import APIKeyModel

logger = logging.getLogger("app")

# Define permission rules
# Format: {HTTP_METHOD: {resource_path_pattern: [allowed_roles]}}
PERMISSION_RULES = {
    "POST": {
        "users": ["root", "admin"],
        "teams": ["root"],
        "api-keys": ["root", "admin"],
        "images": ["root", "admin", "user"]
    },
    "PUT": {
        "users/{user_id}": ["root", "admin"],
        "teams/{team_id}": ["root", "admin"],
        "images/{image_id}": ["root", "admin", "user"]
    },
    "GET": {
        "users": ["root"],
        "users/{user_id}": ["root", "admin", "user"],
        "users/{user_id}/images": ["root", "admin", "user"],
        
        "teams": ["root"],
        "teams/{team_id}": ["root", "admin", "user"],
        "teams/{team_id}/api-keys": ["root", "admin"],
        "teams/{team_id}/api-keys/{api_key_id}": ["root", "admin", "user"],
        "teams/{team_id}/users": ["root", "admin"],
        "teams/{team_id}/users/{user_id}": ["root", "admin", "user"],
        "teams/{team_id}/images": ["root", "admin", "user"],
        "teams/{team_id}/images/{image_id}": ["root", "admin", "user"],
        
        "api-keys": ["root"],
        "api-keys/{api_key_id}": ["root", "admin", "user"],
        
        "images": ["root"],
        "images/{image_id}": ["root", "admin", "user"],

        "audit_logs": ["root"]
    },
    "DELETE": {
        "users/{user_id}": ["root", "admin"],
        "api-keys/{api_key_id}": ["root", "admin", "user"],
        "teams/{team_id}": ["root"],
        "teams/{team_id}/images/{image_id}": ["root", "admin", "user"]
    }
}

class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, repository, api_key_authentication_service):
        super().__init__(app)
        self.repository = repository
        self.api_key_authentication_service = api_key_authentication_service

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract API key from headers
        api_key = request.headers.get("x-api-key")
        if not api_key:
            logger.warning(f"Authentication failure - missing API key: {request.method} {request.url.path}")
            return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API key is missing"},
                    headers={"WWW-Authenticate": "ApiKey"},
                )
        
        # Authenticate API key and get user info
        try:
            api_key_info = await self.api_key_authentication_service.authenticate_api_key(api_key)
        except HTTPException as e:
            logger.warning(f"Authentication failure for request: {request.method} {request.url.path}")
            return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                    headers=e.headers or {"WWW-Authenticate": "ApiKey"},
                )
        
        try:
            # Normalize path and extract params
            path = request.url.path.strip("/")
            path_params = self.extract_path_parameters(path)
            
            # Find matching permission pattern and check permissions
            await self.authorize_request(request.method, path, api_key_info, path_params)
            
            # Process the request
            return await call_next(request)
            
        except HTTPException as e:
            logger.warning(f"Authorization failure for user {api_key_info.user_id}: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers or {"WWW-Authenticate": "ApiKey"},
            )

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
            elif path_parts[i] == "api_keys" and i + 1 < len(path_parts):
                params["api_key_id"] = path_parts[i+1]
        
        return params

    async def authorize_request(self, method: str, path: str, api_key_info: APIKeyModel, path_params: Dict):
        """Perform all authorization checks for the request"""
        # Root can do anything
        if api_key_info.role == "root":
            return True
            
        # Find matching permission rule
        matched_pattern = self._find_matching_pattern(method, path)
        
        if not matched_pattern:
            logger.warning(f"No permission rule found for {method} {path}")
            raise HTTPException(
                status_code=403,
                detail="Access denied: No permission rule found",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Check if user's role is allowed for this pattern
        allowed_roles = PERMISSION_RULES[method][matched_pattern]
        if api_key_info.role not in allowed_roles:
            logger.warning(f"Role {api_key_info.role} not allowed for {method} {path}")
            raise HTTPException(
                status_code=403,
                detail="Access denied: Insufficient permissions",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Check resource ownership
        await self._verify_resource_ownership(api_key_info, path_params)
        
        return True
        
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

    async def _verify_resource_ownership(self, api_key_info: APIKeyModel, path_params: Dict):
        """Verify that the user has ownership of the resources they're trying to access"""
        # Root can access anything
        if api_key_info.role == "root":
            return True
        
        # Check team access
        if "team_id" in path_params and api_key_info.team_id != path_params["team_id"]:
            logger.warning(f"User attempted to access another team's resource")
            raise HTTPException(
                status_code=403,
                detail="Access denied: You can only access resources within your team",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # User ID access check
        if "user_id" in path_params:
            if api_key_info.role == "user" and api_key_info.user_id != path_params["user_id"]:
                logger.warning(f"User attempted to access another user's information")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: You can only access your own information",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            elif api_key_info.role == "admin":
                # Admin needs to verify user belongs to their team
                user = await self.repository.get_user_by_id(path_params["user_id"])
                if not user or user.team_id != api_key_info.team_id:
                    logger.warning(f"Admin attempted to access user from another team")
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: User does not belong to your team",
                        headers={"WWW-Authenticate": "ApiKey"},
                    )
        
        # API key access check
        if "api_key_id" in path_params:
            api_key = await self.repository.get_api_key_by_id(path_params["api_key_id"])
            
            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")
                
            if api_key_info.role == "user" and api_key.user_id != api_key_info.user_id:
                logger.warning(f"User attempted to access another user's API key")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: You can only access your own API keys",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            elif api_key_info.role == "admin" and api_key.team_id != api_key_info.team_id:
                logger.warning(f"Admin attempted to access API key from another team")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: API key does not belong to your team",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
        
        # Image access check
        if "image_id" in path_params:
            image = await self.repository.get_image_by_id(path_params["image_id"])
            
            if not image:
                raise HTTPException(status_code=404, detail="Image not found")
                
            if image.team_id != api_key_info.team_id:
                logger.warning(f"User attempted to access image from another team")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: Image does not belong to your team",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
        
        return True