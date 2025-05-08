import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import imghdr
from io import BytesIO
from PIL import Image as PILImage

from models import ImageModel
from dependencies import repository, bucket, GCS_BUCKET_NAME

app_logger = logging.getLogger("app")
router = APIRouter(prefix="/images", tags=["Images"])

@router.post("/", response_model=ImageModel, status_code=201)
async def upload_team_image(
    user_id: str,
    team_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated list of tags
    file: UploadFile = File(...),
):    
    team = await repository.get_team_by_id(team_id)
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
    
    expiration = timedelta(hours=1)  # Set expiration time as needed
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET"
    )
    
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
        "user_id": user_id,
        "team_id": team_id,
        "title": title,
        "description": description,
        "filename": cloud_filename,
        "content_type": file.content_type,
        "size": len(contents),
        "url": signed_url,
        "metadata": {
            **metadata,
            "tags": tag_list
        },
        "created_at": datetime.now()
    }
    
    await repository.create_image(image_data)
    app_logger.info(f"ImageModel {image_id} uploaded to team {team_id} by user {user_id}")
    
    return image_data

@router.get("/", response_model=List[ImageModel])
async def list_team_images(
    team_id: str,
    skip: int = 0,
    limit: int = 10,
):
    team = await repository.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team's images
    images = await repository.get_images_by_team_id(team_id, skip, limit)
    return images

@router.get("/{image_id}", response_model=ImageModel)
async def get_team_image(image_id: str):
    # Get the specific image
    image = await repository.get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="ImageModel not found")
    
    blob = bucket.blob(image.filename)
    expiration = timedelta(hours=1)
    image.url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET"
    )

    app_logger.info(f"ImageModel {image_id}")
    return image

@router.delete("/{image_id}", status_code=204)
async def delete_team_image(
    user_id: str,
    team_id: str,
    image_id: str
):
    
    team = await repository.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get the specific image
    image = await repository.get_image_by_id({"id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="ImageModel not found")
    
    # Delete from GCS
    blob = bucket.blob(image["filename"])
    blob.delete()
    
    # Delete from database
    await repository.images_collection(image_id)
    
    app_logger.info(f"ImageModel {image_id} deleted by user {user_id}")
    return None
