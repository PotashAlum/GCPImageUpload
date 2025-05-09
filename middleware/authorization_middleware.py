from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from services.interfaces.authorization_service_interface import IAuthorizationService

logger = logging.getLogger("app")

class AuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, authorization_service: IAuthorizationService):
        super().__init__(app)
        self.authorization_service = authorization_service

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip authorization for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
            
        try:
            # Get the authenticated user info from request state (set by AuthenticationMiddleware)
            api_key_info = request.state.api_key_info
            if not api_key_info:
                logger.error("Authorization middleware used before authentication middleware")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"},
                )
            
            # Normalize path and extract params
            path = request.url.path.strip("/")
            path_params = self.authorization_service.extract_path_parameters(path)
            
            # Check if the user is authorized to access this endpoint
            await self.authorization_service.authorize_request(
                request.method, path, api_key_info, path_params
            )
            
            # If authorized, proceed with the request
            return await call_next(request)
            
        except HTTPException as e:
            if hasattr(request.state, "api_key_info"):
                api_key_info = request.state.api_key_info
                logger.warning(f"Authorization failure for user {api_key_info.user_id}: {request.method} {request.url.path}")
            else:
                logger.warning(f"Authorization failure: {request.method} {request.url.path}")
                
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=e.headers or {"WWW-Authenticate": "ApiKey"},
            )
        except Exception as e:
            logger.error(f"Unexpected error in authorization middleware: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )