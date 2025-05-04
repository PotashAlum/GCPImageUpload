from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import os
from motor.motor_asyncio import AsyncIOMotorClient
from google.cloud import storage
import imghdr

from models import Image, ImageBase, User, UserBase, UserCreate

# Initialize FastAPI
app = FastAPI(title="User Image Management Service")

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
API_KEYS = os.getenv("API_KEYS", "test-key-1,test-key-2").split(",")

# Database connection
client = AsyncIOMotorClient(MONGODB_URI)
db = client.user_image_db
users_collection = db.users
images_collection = db.images

# GCS client
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET_NAME)

# Dependency for API key authentication
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Helper for extracting user_id from the API key (in a real system, this would validate JWTs or session tokens)
# This is a simplified approach - in a real app, API keys would be mapped to specific users
async def get_user_from_api_key(x_api_key: str = Depends(verify_api_key)):
    # For this demo, we're just checking if the API key is valid
    # In a real app, you'd query a database to get the user associated with this API key
    return None  # We'll require explicit user_id in endpoints for simplicity

# CRUD operations for Users
@app.post("/users/", response_model=User, status_code=201)
async def create_user(user: UserCreate, api_key: str = Depends(verify_api_key)):
    # Check if username already exists
    if await users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    
    user_db = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "created_at": created_at
    }
    
    await users_collection.insert_one(user_db)
    return {**user_db}

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, api_key: str = Depends(verify_api_key)):
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[User])
async def list_users(skip: int = 0, limit: int = 10, api_key: str = Depends(verify_api_key)):
    users = await users_collection.find().skip(skip).limit(limit).to_list(limit)
    return users

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: UserBase, api_key: str = Depends(verify_api_key)):
    existing_user = await users_collection.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    
    await users_collection.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    updated_user = await users_collection.find_one({"id": user_id})
    return updated_user

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str, api_key: str = Depends(verify_api_key)):
    # First, delete all images associated with the user
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

# Image operations
@app.post("/users/{user_id}/images/", response_model=Image, status_code=201)
async def upload_image(
    user_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    # Verify user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if the file is an image
    contents = await file.read()
    await file.seek(0)
    
    image_format = imghdr.what(None, contents)
    if not image_format:
        raise HTTPException(status_code=400, detail="File is not a valid image")
    
    # Generate unique ID for the image
    image_id = str(uuid.uuid4())
    
    # Create a GCS filename
    original_filename = file.filename
    ext = original_filename.split(".")[-1] if "." in original_filename else image_format
    cloud_filename = f"{user_id}/{image_id}_{original_filename}"
    
    # Upload to GCS
    blob = bucket.blob(cloud_filename)
    blob.upload_from_file(file.file, content_type=file.content_type)
    
    # Generate a publicly accessible URL
    url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{cloud_filename}"
    
    # Create image record in database
    image_data = {
        "id": image_id,
        "user_id": user_id,
        "title": title,
        "description": description,
        "filename": cloud_filename,
        "content_type": file.content_type,
        "size": len(contents),
        "url": url,
        "created_at": datetime.now(timezone.utc)
    }
    
    await images_collection.insert_one(image_data)
    return image_data

@app.get("/users/{user_id}/images/", response_model=List[Image])
async def list_user_images(
    user_id: str,
    skip: int = 0,
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    # Verify user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's images
    images = await images_collection.find({"user_id": user_id}).skip(skip).limit(limit).to_list(limit)
    return images

@app.get("/users/{user_id}/images/{image_id}", response_model=Image)
async def get_image(
    user_id: str,
    image_id: str,
    api_key: str = Depends(verify_api_key)
):
    # Verify user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get the specific image
    image = await images_collection.find_one({"id": image_id, "user_id": user_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return image

@app.put("/users/{user_id}/images/{image_id}", response_model=Image)
async def update_image(
    user_id: str,
    image_id: str,
    image_update: ImageBase,
    api_key: str = Depends(verify_api_key)
):
    # Verify user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the image
    image = await images_collection.find_one({"id": image_id, "user_id": user_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Update image metadata
    update_data = image_update.dict(exclude_unset=True)
    
    await images_collection.update_one(
        {"id": image_id, "user_id": user_id},
        {"$set": update_data}
    )
    
    updated_image = await images_collection.find_one({"id": image_id, "user_id": user_id})
    return updated_image

@app.delete("/users/{user_id}/images/{image_id}", status_code=204)
async def delete_image(
    user_id: str,
    image_id: str,
    api_key: str = Depends(verify_api_key)
):
    # Verify user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the image
    image = await images_collection.find_one({"id": image_id, "user_id": user_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete from GCS
    blob = bucket.blob(image["filename"])
    blob.delete()
    
    # Delete from database
    await images_collection.delete_one({"id": image_id, "user_id": user_id})
    
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)


