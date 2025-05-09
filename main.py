from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from middleware import AuditMiddleware, AuthenticationMiddleware

from routers import audit_log_router, image_router, team_router, user_router, api_key_router
from dependencies import repository, api_key_authentication_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    await repository.startup_db_client()
    yield
    await repository.shutdown_db_client()

# Initialize FastAPI
app = FastAPI(title="User ImageModel Management Service", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add audit middleware
app.add_middleware(AuditMiddleware, 
                   repository = repository)
app.add_middleware(AuthenticationMiddleware, 
                   repository = repository, 
                   api_key_authentication_service = api_key_authentication_service)


# Include routers
app.include_router(api_key_router.router)
app.include_router(team_router.router)
app.include_router(user_router.router)
app.include_router(image_router.router)
app.include_router(audit_log_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
