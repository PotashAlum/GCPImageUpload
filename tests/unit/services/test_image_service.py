import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import io
from datetime import datetime, timedelta
from fastapi import HTTPException, UploadFile
from PIL import Image as PILImage

from services.implementation.image_service import ImageService
from models import TeamModel, ImageModel


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    repository.teams = AsyncMock()
    repository.images = AsyncMock()
    return repository


@pytest.fixture
def mock_storage_service():
    storage_service = AsyncMock()
    return storage_service


@pytest.fixture
def image_service(mock_repository, mock_storage_service):
    return ImageService(mock_repository, mock_storage_service)


@pytest.fixture
def team_data():
    return TeamModel(
        id="team-123",
        name="Test Team",
        description="Test Description",
        created_at=datetime.now()
    )


@pytest.fixture
def image_data():
    return {
        "id": "img-456",
        "user_id": "user-123",
        "team_id": "team-123",
        "title": "Test Image",
        "description": "Test Description",
        "filename": "team-123/img-456_test.jpg",
        "content_type": "image/jpeg",
        "size": 1024,
        "url": "https://example.com/test.jpg",
        "metadata": {
            "width": 800,
            "height": 600,
            "format": "JPEG",
            "color_space": "RGB",
            "tags": ["test", "demo"]
        },
        "created_at": datetime.now()
    }


@pytest.fixture
def mock_upload_file():
    # Create a mock UploadFile
    file = AsyncMock(spec=UploadFile)
    file.filename = "test.jpg"
    file.content_type = "image/jpeg"
    file.file = io.BytesIO(b"fake image content")
    file.read = AsyncMock(return_value=b"fake image content")
    file.seek = AsyncMock()
    return file


@pytest.mark.asyncio
async def test_upload_team_image(image_service, team_data, mock_upload_file):
    # Mock setup
    image_service.repository.teams.get_team_by_id.return_value = team_data
    image_service.storage_service.upload_file.return_value = "https://example.com/test.jpg"
    
    # Generate a predictable UUID
    test_uuid = "img-456"
    with patch('uuid.uuid4', return_value=MagicMock(return_value=test_uuid, __str__=lambda _: test_uuid)), \
         patch('imghdr.what', return_value="jpeg"), \
         patch.object(PILImage, 'open') as mock_pil_open:
        
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.width = 800
        mock_img.height = 600
        mock_img.format = "JPEG"
        mock_img.mode = "RGB"
        mock_img._getexif.return_value = None
        mock_pil_open.return_value = mock_img
        
        # Call the method
        result = await image_service.upload_team_image(
            user_id="user-123",
            team_id="team-123",
            file=mock_upload_file,
            title="Test Image",
            description="Test Description",
            tags="test,demo"
        )
        
        # Verify
        image_service.repository.teams.get_team_by_id.assert_called_once_with("team-123")
        mock_upload_file.read.assert_called_once()
        mock_upload_file.seek.assert_called_once_with(0)
        
        # Verify storage service call
        image_service.storage_service.upload_file.assert_called_once()
        storage_call_args = image_service.storage_service.upload_file.call_args[1]
        assert storage_call_args["file"] == mock_upload_file
        assert storage_call_args["path"].startswith("team-123/")
        assert storage_call_args["path"].endswith("_test.jpg")
        
        # Verify create_image call
        image_service.repository.images.create_image.assert_called_once()
        create_image_args = image_service.repository.images.create_image.call_args[0][0]
        assert create_image_args["id"] == test_uuid
        assert create_image_args["user_id"] == "user-123"
        assert create_image_args["team_id"] == "team-123"
        assert create_image_args["title"] == "Test Image"
        assert create_image_args["description"] == "Test Description"
        assert create_image_args["filename"].startswith("team-123/img-456")
        assert create_image_args["content_type"] == "image/jpeg"
        assert create_image_args["url"] == "https://example.com/test.jpg"
        assert create_image_args["metadata"]["width"] == 800
        assert create_image_args["metadata"]["height"] == 600
        assert create_image_args["metadata"]["format"] == "JPEG"
        assert set(create_image_args["metadata"]["tags"]) == {"test", "demo"}
        
        # Verify result
        assert result["id"] == test_uuid
        assert result["user_id"] == "user-123"
        assert result["team_id"] == "team-123"
        assert result["title"] == "Test Image"
        assert result["url"] == "https://example.com/test.jpg"


@pytest.mark.asyncio
async def test_upload_team_image_team_not_found(image_service, mock_upload_file):
    # Mock setup
    image_service.repository.teams.get_team_by_id.return_value = None
    
    # Call the method
    with pytest.raises(HTTPException) as exc_info:
        await image_service.upload_team_image(
            user_id="user-123",
            team_id="nonexistent-team",
            file=mock_upload_file
        )
    
    # Verify
    image_service.repository.teams.get_team_by_id.assert_called_once_with("nonexistent-team")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Team not found"


@pytest.mark.asyncio
async def test_upload_team_image_invalid_image(image_service, team_data, mock_upload_file):
    # Mock setup
    image_service.repository.teams.get_team_by_id.return_value = team_data
    
    # Mock imghdr to return None (not an image)
    with patch('imghdr.what', return_value=None):
        # Call the method
        with pytest.raises(HTTPException) as exc_info:
            await image_service.upload_team_image(
                user_id="user-123",
                team_id="team-123",
                file=mock_upload_file
            )
        
        # Verify
        image_service.repository.teams.get_team_by_id.assert_called_once_with("team-123")
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "File is not a valid image"


@pytest.mark.asyncio
async def test_get_team_image(image_service, image_data):
    # Mock setup
    image_model = ImageModel(**image_data)
    image_service.repository.images.get_image_by_id.return_value = image_model
    image_service.storage_service.generate_signed_url.return_value = "https://example.com/new-signed-url.jpg"
    
    # Call the method
    result = await image_service.get_team_image("img-456")
    
    # Verify
    image_service.repository.images.get_image_by_id.assert_called_once_with("img-456")
    image_service.storage_service.generate_signed_url.assert_called_once()
    assert image_service.storage_service.generate_signed_url.call_args[1]["path"] == image_data["filename"]
    
    # Verify result
    assert result.id == image_data["id"]
    assert result.url == "https://example.com/new-signed-url.jpg"  # Should have the new URL


@pytest.mark.asyncio
async def test_get_team_image_not_found(image_service):
    # Mock setup
    image_service.repository.images.get_image_by_id.return_value = None
    
    # Call the method
    with pytest.raises(HTTPException) as exc_info:
        await image_service.get_team_image("nonexistent-image")
    
    # Verify
    image_service.repository.images.get_image_by_id.assert_called_once_with("nonexistent-image")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Image not found"


@pytest.mark.asyncio
async def test_delete_image(image_service, image_data):
    # Mock setup
    image_model = ImageModel(**image_data)
    image_service.repository.images.get_image_by_id.return_value = image_model
    
    # Call the method
    await image_service.delete_image("img-456")
    
    # Verify
    image_service.repository.images.get_image_by_id.assert_called_once_with("img-456")
    image_service.storage_service.delete_file.assert_called_once_with(image_data["filename"])
    image_service.repository.images.delete_image.assert_called_once_with("img-456")


@pytest.mark.asyncio
async def test_delete_image_not_found(image_service):
    # Mock setup
    image_service.repository.images.get_image_by_id.return_value = None
    
    # Call the method
    with pytest.raises(HTTPException) as exc_info:
        await image_service.delete_image("nonexistent-image")
    
    # Verify
    image_service.repository.images.get_image_by_id.assert_called_once_with("nonexistent-image")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Image not found"