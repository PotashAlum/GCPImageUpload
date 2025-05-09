from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from middleware import AuditMiddleware, AuthenticationMiddleware
from middleware.authorization_middleware import AuthorizationMiddleware
from routers import audit_log_router, team_router
from dependencies import repository, api_key_authentication_service, authorization_service, audit_log_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database connection
    await repository.startup_db_client()
    yield
    # Close database connection when shutting down
    await repository.shutdown_db_client()

# Initialize FastAPI
app = FastAPI(
    title="Team Image Management API",
    description="A secure API for team-based image management with hierarchical access control",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add audit logging middleware
app.add_middleware(
    AuditMiddleware, 
    audit_log_service=audit_log_service
)

# Add authorization middleware
app.add_middleware(
    AuthorizationMiddleware, 
    authorization_service=authorization_service
)

# Add authentication middleware
app.add_middleware(
    AuthenticationMiddleware, 
    api_key_authentication_service=api_key_authentication_service
)

# Include only the team router - all operations now go through team-based endpoints
app.include_router(team_router.router)

# Include audit logs for admin purposes
app.include_router(audit_log_router.router)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring services
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)