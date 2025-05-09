import logging
import uuid
import imghdr
from io import BytesIO
from PIL import Image as PILImage
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, UploadFile

from models import ImageModel
from repository import IRepository
from services.interfaces.image_service_interface import IImageService

class ImageService(IImageService):
    def __init__(self, repository: IRepository, bucket, bucket_name: str):
        self.logger = logging.getLogger("app")
        self.repository = repository
        self.bucket = bucket
        self.bucket_name = bucket_name
    
    async def upload_team_image(
        self,
        user_id: str,
        team_id: str,
        file: UploadFile,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> ImageModel:
        team = await self.repository.teams.get_team_by_id(team_id)
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
        blob = self.bucket.blob(cloud_filename)
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
            self.logger.warning(f"Error extracting image metadata: {str(e)}")
        
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
        
        await self.repository.images.create_image(image_data)
        self.logger.info(f"Image {image_id} uploaded to team {team_id} by user {user_id}")
        
        return image_data
    
    async def list_team_images(
        self,
        team_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> List[ImageModel]:
        team = await self.repository.teams.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get team's images
        images = await self.repository.images.get_images_by_team_id(team_id, skip, limit)
        return images
    
    async def get_team_image(
        self,
        image_id: str
    ) -> ImageModel:
        # Get the specific image
        image = await self.repository.images.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        blob = self.bucket.blob(image.filename)
        expiration = timedelta(hours=1)
        image.url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET"
        )

        self.logger.info(f"Image {image_id}")
        return image
    
    async def delete_image(
        self,
        image_id: str
    ) -> None:
        # Get the specific image
        image = await self.repository.images.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete from GCS
        blob = self.bucket.blob(image.filename)
        blob.delete()
        
        # Delete from database
        await self.repository.images.delete_image(image_id)
        
        self.logger.info(f"Image {image_id} deleted")
        return None