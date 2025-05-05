from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, Request
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid
import os
import logging
from logging.handlers import RotatingFileHandler
import secrets
import imghdr
from motor.motor_asyncio import AsyncIOMotorClient
from google.cloud import storage
from PIL import Image as PILImage
from io import BytesIO
import json
import hashlib
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    User, UserBase, 
    Team, TeamBase, TeamCreate,
    APIKey, APIKeyBase, APIKeyCreate, 
    Image, ImageBase, ImageCreate, ImageMetadata,
    AuditLog
)

# Initialize FastAPI
app = FastAPI(title="User Image Management Service")

# Configure logging
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Application logger
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)
app_handler = RotatingFileHandler(
    os.path.join(log_directory, "app.log"),
    maxBytes=10485760,  # 10MB
    backupCount=5
)
app_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app_logger.addHandler(app_handler)

# Audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
audit_handler = RotatingFileHandler(
    os.path.join(log_directory, "audit.log"),
    maxBytes=10485760,  # 10MB
    backupCount=10
)
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(message)s'
))
audit_logger.addHandler(audit_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "user-images-bucket")
ROOT_API_KEY = os.getenv("ROOT_API_KEY", "root-admin-key")

# Database connection
client = AsyncIOMotorClient(MONGODB_URI)
db = client.user_image_db
users_collection = db.users
teams_collection = db.teams
api_keys_collection = db.api_keys
images_collection = db.images
audit_logs_collection = db.audit_logs

# GCS client
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

# API Key Security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Audit log middleware
class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        # Extract relevant request information
        method = request.method
        path = request.url.path
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        api_key = request.headers.get("x-api-key", None)
        
        response = await call_next(request)
        
        # Get user ID from API key if possible
        user_id = None
        if api_key:
            api_key_doc = await api_keys_collection.find_one({"key": api_key})
            if api_key_doc:
                user_id = api_key_doc["user_id"]
        
        # Create audit log entry
        log_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": method,
            "resource_type": path.split("/")[1] if len(path.split("/")) > 1 else "root",
            "resource_id": path.split("/")[2] if len(path.split("/")) > 2 else None,
            "status": "success" if response.status_code < 400 else "failure",
            "status_code": response.status_code,
            "ip_address": ip,
            "user_agent": user_agent,
            "details": {
                "path": path,
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
            },
            "timestamp": datetime.now()
        }
        
        # Log to file
        audit_logger.info(json.dumps(log_entry, indent=4, sort_keys=True, default=str))
        
        # Store in database
        await audit_logs_collection.insert_one(log_entry)
        
        return response

# Add audit middleware
app.add_middleware(AuditMiddleware)

# Helper for authenticating API keys
async def authenticate_api_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check if it's the root API key
    if api_key == ROOT_API_KEY:
        app_logger.info("Root API key used for authentication")
        return {"is_root": True, "user_id": None, "team_id": None}
    
    # Check if it's a valid user API key
    api_key_doc = await api_keys_collection.find_one({
        "key": api_key,
        "is_active": True,
    })
    
    if not api_key_doc:
        app_logger.warning(f"Invalid API key attempt: {api_key[:5]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check if the API key has expired
    if api_key_doc.get("expires_at") and api_key_doc["expires_at"] < datetime.now():
        app_logger.warning(f"Expired API key used: {api_key[:5]}...")
        raise HTTPException(
            status_code=401,
            detail="API key has expired",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Get user info
    user = await users_collection.find_one({"id": api_key_doc["user_id"]})
    if not user:
        app_logger.error(f"API key associated with non-existent user: {api_key_doc['user_id']}")
        raise HTTPException(
            status_code=401,
            detail="User associated with API key not found",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return {
        "is_root": False,
        "user_id": user["id"],
        "team_id": user["team_id"],
        "api_key_id": api_key_doc["id"]
    }

# Helper function to check team membership and permissions
async def verify_team_access(user_id: str, team_id: str):
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["team_id"] != team_id:
        app_logger.warning(f"User {user_id} attempted to access team {team_id}")
        raise HTTPException(status_code=403, detail="You don't have permission to access this team's resources")

# Setup database on startup
@app.on_event("startup")
async def startup_db_client():
    app_logger.info("Starting application...")
    
    # Create indexes
    await users_collection.create_index("username", unique=True)
    await users_collection.create_index("email", unique=True)
    await teams_collection.create_index("name", unique=True)
    await api_keys_collection.create_index("key", unique=True)
    
    app_logger.info("Database setup completed")

@app.on_event("shutdown")
async def shutdown_db_client():
    app_logger.info("Shutting down application...")
    client.close()
    app_logger.info("MongoDB connection closed")

# CRUD operations for Teams
@app.post("/teams/", response_model=Team, status_code=201)
async def create_team(team: TeamCreate, auth: Dict = Depends(authenticate_api_key)):
    app_logger.info(f"Creating new team: {team.name}")
    
    # Check if team name already exists
    if await teams_collection.find_one({"name": team.name}):
        raise HTTPException(status_code=400, detail="Team name already exists")
    
    # Create new team
    team_id = str(uuid.uuid4())
    created_at = datetime.now()
    
    team_db = {
        "id": team_id,
        "name": team.name,
        "description": team.description,
        "created_at": created_at
    }
    
    await teams_collection.insert_one(team_db)
    return {**team_db}

@app.get("/teams/{team_id}", response_model=Team)
async def get_team(team_id: str, auth: Dict = Depends(authenticate_api_key)):
    # Root or team member can access
    if not auth["is_root"]:
        await verify_team_access(auth["user_id"], team_id)
    
    team = await teams_collection.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team

@app.get("/teams/", response_model=List[Team])
async def list_teams(
    skip: int = 0, 
    limit: int = 10, 
    auth: Dict = Depends(authenticate_api_key)
):
    # If root, show all teams
    if auth["is_root"]:
        teams = await teams_collection.find().skip(skip).limit(limit).to_list(limit)
        return teams
    
    # Otherwise, just show the user's team
    user = await users_collection.find_one({"id": auth["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    team = await teams_collection.find_one({"id": user["team_id"]})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return [team]

@app.put("/teams/{team_id}", response_model=Team)
async def update_team(
    team_id: str, 
    team: TeamBase, 
    auth: Dict = Depends(authenticate_api_key)
):
    # Only root can update teams
    if not auth["is_root"]:
        raise HTTPException(status_code=403, detail="Only administrators can update teams")
    
    existing_team = await teams_collection.find_one({"id": team_id})
    if not existing_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Update team fields
    update_data = team.dict(exclude_unset=True)
    
    # Check name uniqueness if updating
    if "name" in update_data and update_data["name"] != existing_team["name"]:
        if await teams_collection.find_one({"name": update_data["name"]}):
            raise HTTPException(status_code=400, detail="Team name already taken")
    
    await teams_collection.update_one(
        {"id": team_id},
        {"$set": update_data}
    )
    
    updated_team = await teams_collection.find_one({"id": team_id})
    return updated_team

@app.delete("/teams/{team_id}", status_code=204)
async def delete_team(team_id: str, auth: Dict = Depends(authenticate_api_key)):
    # Only root can delete teams
    if not auth["is_root"]:
        raise HTTPException(status_code=403, detail="Only administrators can delete teams")
    
    # Check if team exists
    team = await teams_collection.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if there are any users in the team
    users_in_team = await users_collection.count_documents({"team_id": team_id})
    if users_in_team > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete team with active users. Reassign or delete users first."
        )
    
    # Delete all images associated with the team
    team_images = await images_collection.find({"team_id": team_id}).to_list(None)
    
    # Delete the actual image files from GCS
    for image in team_images:
        blob = bucket.blob(image["filename"])
        blob.delete()
    
    # Delete image records from the database
    await images_collection.delete_many({"team_id": team_id})
    
    # Delete the team record
    delete_result = await teams_collection.delete_one({"id": team_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return None

# CRUD operations for Users
@app.post("/users/", response_model=User, status_code=201)
async def create_user(
    user: UserBase, 
    auth: Dict = Depends(authenticate_api_key)
):
    app_logger.info(f"Creating new user: {user.username}")
    
    # Check if team exists
    team = await teams_collection.find_one({"id": user.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if username already exists
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    
    user_db = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "team_id": user.team_id,
        "created_at": created_at
    }
    
    await users_collection.insert_one(user_db)
    return {**user_db}

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, auth: Dict = Depends(authenticate_api_key)):
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if requester has permission to access this user
    if not auth["is_root"] and auth["user_id"] != user_id and auth["team_id"] != user["team_id"]:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to access this user"
        )
    
    return user

@app.get("/users/", response_model=List[User])
async def list_users(
    skip: int = 0, 
    limit: int = 10, 
    team_id: Optional[str] = None, 
    auth: Dict = Depends(authenticate_api_key)
):
    # Build query
    query = {}
    
    # If team_id is provided, filter by team
    if team_id:
        # Verify access to the team
        if not auth["is_root"]:
            await verify_team_access(auth["user_id"], team_id)
        query["team_id"] = team_id
    elif not auth["is_root"]:
        # Non-root users can only see users in their team
        query["team_id"] = auth["team_id"]
    
    users = await users_collection.find(query).skip(skip).limit(limit).to_list(limit)
    return users

@app.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str, 
    user: UserBase, 
    auth: Dict = Depends(authenticate_api_key)
):
    existing_user = await users_collection.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions: either it's your own account, or you're an admin
    if not auth["is_root"] and auth["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to update this user"
        )
    
    # Update user fields
    update_data = user.dict(exclude_unset=True)
    
    # Check username uniqueness if updating
    if "username" in update_data and update_data["username"] != existing_user["username"]:
        if await users_collection.find_one({"username": update_data["username"]}):
            raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check email uniqueness if updating
    if "email" in update_data and update_data["email"] != existing_user["email"]:
        if await users_collection.find_one({"email": update_data["email"]}):
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Update team if provided (only admins can do this)
    if user.team_id != existing_user["team_id"]:
        if not auth["is_root"]:
            raise HTTPException(
                status_code=403, 
                detail="Only administrators can change a user's team"
            )
        
        # Verify team exists
        team = await teams_collection.find_one({"id": user.team_id})
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        update_data["team_id"] = user.team_id
    
    await users_collection.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    updated_user = await users_collection.find_one({"id": user_id})
    return updated_user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str, auth: Dict = Depends(authenticate_api_key)):
    # Only root or the user themselves can delete their account
    if not auth["is_root"] and auth["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to delete this user"
        )
    
    # Check if user exists
    existing_user = await users_collection.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # First, delete all API keys associated with the user
    await api_keys_collection.delete_many({"user_id": user_id})
    
    # Next, delete all images uploaded by the user
    user_images = await images_collection.find({"user_id": user_id}).to_list(None)
    
    # Delete the actual image files from GCS
    for image in user_images:
        blob = bucket.blob(image["filename"])
        blob.delete()
    
    # Delete image records from the database
    await images_collection.delete_many({"user_id": user_id})
    
    # Delete the user record
    delete_result = await users_collection.delete_one({"id": user_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return None

# CRUD operations for API Keys
@app.post("/users/{user_id}/api-keys/", response_model=APIKey, status_code=201)
async def create_api_key(
    user_id: str,
    api_key: APIKeyCreate,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check permissions: either it's your own account, or you're an admin
    if not auth["is_root"] and auth["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to create API keys for this user"
        )
    
    # Check if user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new API key
    api_key_id = str(uuid.uuid4())
    api_key_value = f"sk_{secrets.token_urlsafe(32)}"
    created_at = datetime.now()
    
    api_key_db = {
        "id": api_key_id,
        "user_id": user_id,
        "name": api_key.name,
        "key": api_key_value,
        "created_at": created_at,
        "expires_at": api_key.expires_at,
        "is_active": True
    }
    
    await api_keys_collection.insert_one(api_key_db)
    app_logger.info(f"Created new API key {api_key_id} for user {user_id}")
    
    return {**api_key_db}

@app.get("/users/{user_id}/api-keys/", response_model=List[APIKey])
async def list_user_api_keys(
    user_id: str,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check permissions: either it's your own account, or you're an admin
    if not auth["is_root"] and auth["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view API keys for this user"
        )
    
    # Check if user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's API keys
    api_keys = await api_keys_collection.find({"user_id": user_id}).to_list(None)
    return api_keys

@app.get("/users/{user_id}/api-keys/{api_key_id}", response_model=APIKey)
async def get_api_key(
    user_id: str,
    api_key_id: str,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check permissions: either it's your own account, or you're an admin
    if not auth["is_root"] and auth["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to view this API key"
        )
    
    # Check if user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the specific API key
    api_key = await api_keys_collection.find_one({"id": api_key_id, "user_id": user_id})
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return api_key

@app.put("/users/{user_id}/api-keys/{api_key_id}", response_model=APIKey)
async def update_api_key(
    user_id: str,
    api_key_id: str,
    api_key_update: APIKeyBase,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check permissions: either it's your own account, or you're an admin
    if not auth["is_root"] and auth["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to update this API key"
        )
    
    # Check if user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the API key
    api_key = await api_keys_collection.find_one({"id": api_key_id, "user_id": user_id})
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Update API key metadata
    update_data = api_key_update.dict(exclude_unset=True)
    
    await api_keys_collection.update_one(
        {"id": api_key_id, "user_id": user_id},
        {"$set": update_data}
    )
    
    updated_api_key = await api_keys_collection.find_one({"id": api_key_id, "user_id": user_id})
    return updated_api_key

@app.delete("/users/{user_id}/api-keys/{api_key_id}", status_code=204)
async def delete_api_key(
    user_id: str,
    api_key_id: str,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check permissions: either it's your own account, or you're an admin
    if not auth["is_root"] and auth["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to delete this API key"
        )
    
    # Check if user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Make sure not deleting the API key currently in use
    if not auth["is_root"] and auth["api_key_id"] == api_key_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the API key currently in use"
        )
    
    # Delete from database
    delete_result = await api_keys_collection.delete_one({"id": api_key_id, "user_id": user_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    app_logger.info(f"Deleted API key {api_key_id} for user {user_id}")
    return None

# Image operations with team ownership
@app.post("/teams/{team_id}/images/", response_model=Image, status_code=201)
async def upload_team_image(
    team_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated list of tags
    file: UploadFile = File(...),
    auth: Dict = Depends(authenticate_api_key)
):
    # Check if user has access to this team
    if not auth["is_root"]:
        await verify_team_access(auth["user_id"], team_id)
    
    # Verify team exists
    team = await teams_collection.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if the file is an image
    contents = await file.read()
    await file.seek(0)
    
    image_format = imghdr.what(None, contents)
    if not image_format:
        raise HTTPException(status_code=400, detail="File is not a valid image")
    
    # Generate unique ID for the image
    image_id = str(uuid.uuid4())
    
    # Create a GCS filename with team identifier
    original_filename = file.filename
    cloud_filename = f"{team_id}/{image_id}_{original_filename}"
    
    # Upload to GCS
    blob = bucket.blob(cloud_filename)
    blob.upload_from_file(file.file, content_type=file.content_type)
    
    # Generate a publicly accessible URL
    url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{cloud_filename}"
    
    # Extract metadata from the image if possible
    metadata = {}
    try:
        img = PILImage.open(BytesIO(contents))
        metadata = {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "color_space": img.mode
        }
        
        # Try to extract EXIF data
        exif_data = img._getexif()
        if exif_data:
            # Extract camera model if available
            if 272 in exif_data:  # Model tag in EXIF
                metadata["camera_model"] = exif_data[272]
            
            # Extract capture date if available
            if 36867 in exif_data:  # DateTimeOriginal tag in EXIF
                try:
                    metadata["capture_date"] = datetime.strptime(
                        exif_data[36867], 
                        "%Y:%m:%d %H:%M:%S"
                    )
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        app_logger.warning(f"Error extracting image metadata: {str(e)}")
    
    # Process tags if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # Create image record in database
    image_data = {
        "id": image_id,
        "user_id": auth["user_id"],
        "team_id": team_id,
        "title": title,
        "description": description,
        "filename": cloud_filename,
        "content_type": file.content_type,
        "size": len(contents),
        "url": url,
        "metadata": {
            **metadata,
            "tags": tag_list
        },
        "created_at": datetime.now()
    }
    
    await images_collection.insert_one(image_data)
    app_logger.info(f"Image {image_id} uploaded to team {team_id} by user {auth['user_id']}")
    
    return image_data

@app.get("/teams/{team_id}/images/", response_model=List[Image])
async def list_team_images(
    team_id: str,
    skip: int = 0,
    limit: int = 10,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check if user has access to this team
    if not auth["is_root"]:
        await verify_team_access(auth["user_id"], team_id)
    
    # Verify team exists
    team = await teams_collection.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team's images
    images = await images_collection.find({"team_id": team_id}).skip(skip).limit(limit).to_list(limit)
    return images

@app.get("/teams/{team_id}/images/{image_id}", response_model=Image)
async def get_team_image(
    team_id: str,
    image_id: str,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check if user has access to this team
    if not auth["is_root"]:
        await verify_team_access(auth["user_id"], team_id)
    
    # Verify team exists
    team = await teams_collection.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get the specific image
    image = await images_collection.find_one({"id": image_id, "team_id": team_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    app_logger.info(f"Image {image_id} viewed by user {auth['user_id']}")
    return image

@app.put("/teams/{team_id}/images/{image_id}", response_model=Image)
async def update_team_image(
    team_id: str,
    image_id: str,
    image_update: ImageBase,
    tags: Optional[str] = None,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check if user has access to this team
    if not auth["is_root"]:
        await verify_team_access(auth["user_id"], team_id)
    
    # Verify team exists
    team = await teams_collection.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Find the image
    image = await images_collection.find_one({"id": image_id, "team_id": team_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Update image metadata
    update_data = image_update.dict(exclude_unset=True)
    
    # Process tags if provided
    if tags is not None:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        if "metadata" not in update_data:
            update_data["metadata"] = {}
        update_data["metadata"]["tags"] = tag_list
    
    # Preserve existing metadata if we're updating it
    if "metadata" in update_data and image.get("metadata"):
        update_data["metadata"] = {**image["metadata"], **update_data["metadata"]}
    
    await images_collection.update_one(
        {"id": image_id, "team_id": team_id},
        {"$set": update_data}
    )
    
    updated_image = await images_collection.find_one({"id": image_id, "team_id": team_id})
    app_logger.info(f"Image {image_id} metadata updated by user {auth['user_id']}")
    return updated_image

@app.delete("/teams/{team_id}/images/{image_id}", status_code=204)
async def delete_team_image(
    team_id: str,
    image_id: str,
    auth: Dict = Depends(authenticate_api_key)
):
    # Check if user has access to this team
    if not auth["is_root"]:
        await verify_team_access(auth["user_id"], team_id)
    
    # Verify team exists
    team = await teams_collection.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Find the image
    image = await images_collection.find_one({"id": image_id, "team_id": team_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete from GCS
    blob = bucket.blob(image["filename"])
    blob.delete()
    
    # Delete from database
    await images_collection.delete_one({"id": image_id, "team_id": team_id})
    
    app_logger.info(f"Image {image_id} deleted by user {auth['user_id']}")
    return None

# Audit log endpoints
@app.get("/audit-logs/", response_model=List[AuditLog])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    auth: Dict = Depends(authenticate_api_key)
):
    # Only root can view audit logs
    if not auth["is_root"]:
        raise HTTPException(
            status_code=403, 
            detail="Only administrators can view audit logs"
        )
    
    # Build query
    query = {}
    
    if user_id:
        query["user_id"] = user_id
    
    if resource_type:
        query["resource_type"] = resource_type
    
    if action:
        query["action"] = action
    
    if status:
        query["status"] = status
    
    date_query = {}
    if from_date:
        date_query["$gte"] = from_date
    
    if to_date:
        date_query["$lte"] = to_date
    
    if date_query:
        query["timestamp"] = date_query
    
    # Get logs
    logs = await audit_logs_collection.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    return logs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)