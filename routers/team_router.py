from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body, Path
from typing import List, Optional
import logging

from models import TeamModel, APIKeyModel, ImageModel, UserModel
from dependencies import team_service, api_key_management_service, image_service, user_service
from models.api_key_model import APIKeyCreateResponse

# Initialize router
router = APIRouter(prefix="/teams", tags=["Teams"])

# Get the application logger
app_logger = logging.getLogger("app")

# ###################
# # TEAM OPERATIONS #
# ###################

@router.post("/", response_model=TeamModel, status_code=201)
async def create_team(
    name: str = Body(..., description="Team name"),
    description: str = Body(None, description="Team description")
):
    """
    Create a new team (root only)
    """
    return await team_service.create_team(name, description)

@router.get("/", response_model=List[TeamModel])
async def list_teams(
    skip: int = Query(0, description="Skip records for pagination"),
    limit: int = Query(10, description="Limit number of records returned")
):
    """
    List all teams (root only)
    """
    return await team_service.list_teams(skip, limit)

@router.get("/{team_id}", response_model=TeamModel)
async def get_team(
    team_id: str = Path(..., description="Team ID")
):
    """
    Get team details (team members can access)
    """
    return await team_service.get_team(team_id)

@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: str = Path(..., description="Team ID")
):
    """
    Delete a team and all its resources (root only)
    """
    await team_service.delete_team(team_id)
    

# #########################
# # TEAM USER OPERATIONS  #
# #########################

@router.post("/{team_id}/users", response_model=UserModel, status_code=201)
async def create_team_user(
    team_id: str = Path(..., description="Team ID"),
    username: str = Body(..., description="Username"),
    email: str = Body(..., description="Email address")
):
    """
    Create a new user in a team (admin+)
    """
    return await user_service.create_user(username, email, team_id)

@router.get("/{team_id}/users", response_model=List[UserModel])
async def list_team_users(
    team_id: str = Path(..., description="Team ID"),
    skip: int = Query(0, description="Skip records for pagination"),
    limit: int = Query(10, description="Limit number of records returned")
):
    """
    List users in a team (all team members can access)
    """
    return await team_service.list_team_users(team_id, skip, limit)

@router.get("/{team_id}/users/{user_id}", response_model=UserModel)
async def get_team_user(
    team_id: str = Path(..., description="Team ID"),
    user_id: str = Path(..., description="User ID")
):
    """
    Get a specific team user (all team members can access)
    """
    return await team_service.get_team_user(team_id, user_id)

@router.delete("/{team_id}/users/{user_id}", status_code=204)
async def delete_team_user(
    user_id: str = Path(..., description="User ID")
):
    """
    Delete a team user (admin+)
    """
    await user_service.delete_user(user_id)
    

# #########################
# # TEAM API KEY OPERATIONS #
# #########################

@router.post("/{team_id}/users/{user_id}/api-keys", response_model=APIKeyCreateResponse, status_code=201)
async def create_team_api_key(
    team_id: str = Path(..., description="Team ID"),
    user_id: str = Path(..., description="User ID"),
    name: str = Body(..., description="API key name"),
    role: str = Body("user", description="API key role (admin or user)"),
):
    """
    Create a new API key for a team (admin+)
    
    Note: The complete API key will only be returned ONCE at creation time.
    Store it securely as you won't be able to retrieve it later.
    """
    if role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
        
    return await api_key_management_service.create_api_key(name, role, user_id, team_id)

@router.get("/{team_id}/api-keys", response_model=List[APIKeyModel])
async def list_team_api_keys(
    team_id: str = Path(..., description="Team ID"),
    skip: int = Query(0, description="Skip records for pagination"),
    limit: int = Query(10, description="Limit number of records returned")
):
    """
    List API keys for a team (admin+)
    """
    return await team_service.list_team_api_keys(team_id, skip, limit)

@router.get("/{team_id}/api-keys/{api_key_id}", response_model=APIKeyModel)
async def get_team_api_key(
    api_key_id: str = Path(..., description="API key ID")
):
    """
    Get a specific team API key (admin+)
    """
    return await api_key_management_service.get_api_key_by_id(api_key_id)

@router.delete("/{team_id}/api-keys/{api_key_id}", status_code=204)
async def delete_team_api_key(
    api_key_id: str = Path(..., description="API key ID")
):
    """
    Delete a team API key (admin+)
    """
    await api_key_management_service.delete_api_key(api_key_id)
    

# ############################
# # TEAM USER API KEY OPERATIONS #
# ############################

@router.get("/{team_id}/users/{user_id}/api-keys", response_model=List[APIKeyModel])
async def list_team_user_api_keys(
    user_id: str = Path(..., description="User ID"),
    skip: int = Query(0, description="Skip records for pagination"),
    limit: int = Query(10, description="Limit number of records returned")
):
    """
    List API keys for a specific user in a team (user can only see their own)
    """
    return await api_key_management_service.get_api_keys_by_user_id(user_id, skip, limit)

@router.get("/{team_id}/users/{user_id}/api-keys/{api_key_id}", response_model=APIKeyModel)
async def get_team_user_api_key(
    api_key_id: str = Path(..., description="API key ID")
):
    """
    Get a specific API key for a user in a team (user can only see their own)
    """
    return await api_key_management_service.get_api_key_by_id(api_key_id)

@router.delete("/{team_id}/users/{user_id}/api-keys/{api_key_id}", status_code=204)
async def delete_team_user_api_key(
    api_key_id: str = Path(..., description="API key ID")
):
    """
    Delete a specific API key for a user in a team (user can only delete their own)
    """
    await api_key_management_service.delete_api_key(api_key_id)
    

# ########################
# # TEAM IMAGE OPERATIONS #
# ########################

@router.post("/{team_id}/images", response_model=ImageModel, status_code=201)
async def upload_team_image(
    team_id: str = Path(..., description="Team ID"),
    user_id: str = Body(..., description="User ID uploading the image"),
    title: Optional[str] = Body(None, description="Image title"),
    description: Optional[str] = Body(None, description="Image description"),
    tags: Optional[str] = Body(None, description="Comma-separated list of tags"),
    file: UploadFile = File(..., description="Image file to upload")
):    
    """
    Upload an image to a team (any team member can upload)
    """
    return await image_service.upload_team_image(
        user_id=user_id,
        team_id=team_id,
        title=title,
        description=description,
        tags=tags,
        file=file
    )

@router.get("/{team_id}/images", response_model=List[ImageModel])
async def list_team_images(
    team_id: str = Path(..., description="Team ID"),
    skip: int = Query(0, description="Skip records for pagination"),
    limit: int = Query(10, description="Limit number of records returned")
):
    """
    List all images in a team (any team member can access)
    """
    return await team_service.list_team_images(team_id, skip, limit)

@router.get("/{team_id}/images/{image_id}", response_model=ImageModel)
async def get_team_image(
    image_id: str = Path(..., description="Image ID")
):
    """
    Get a specific team image (any team member can access)
    """
    return await image_service.get_team_image(image_id)

@router.delete("/{team_id}/images/{image_id}", status_code=204)
async def delete_team_image(
    image_id: str = Path(..., description="Image ID")
):
    """
    Delete a team image (admins can delete any image, users only their own)
    """
    await image_service.delete_image(image_id)
    

# ############################
# # TEAM USER IMAGE OPERATIONS #
# ############################

@router.get("/{team_id}/users/{user_id}/images", response_model=List[ImageModel])
async def list_team_user_images(
    user_id: str = Path(..., description="User ID"),
    skip: int = Query(0, description="Skip records for pagination"),
    limit: int = Query(10, description="Limit number of records returned")
):
    """
    List images for a specific user in a team
    """
    return await image_service.get_images_by_user_id(user_id, skip, limit)

@router.get("/{team_id}/users/{user_id}/images/{image_id}", response_model=ImageModel)
async def get_team_user_image(
    image_id: str = Path(..., description="Image ID")
):
    """
    Get a specific image for a user in a team
    """
    return await image_service.get_team_image(image_id)

@router.delete("/{team_id}/users/{user_id}/images/{image_id}", status_code=204)
async def delete_team_user_image(
    image_id: str = Path(..., description="Image ID")
):
    """
    Delete a specific image for a user in a team (user can only delete their own)
    """
    await image_service.delete_image(image_id)
    