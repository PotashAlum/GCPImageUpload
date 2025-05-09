from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from services.interfaces.api_key_authentication_interface import IAPIKeyAuthenticationService

logger = logging.getLogger("app")

class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key_authentication_service: IAPIKeyAuthenticationService):
        super().__init__(app)
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
            
            # Store the authenticated user info in request state for later use
            request.state.api_key_info = api_key_info
            
            # Process the request
            return await call_next(request)
            
        except HTTPException as e:
            logger.warning(f"Authentication failure for request: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers or {"WWW-Authenticate": "ApiKey"},
            )