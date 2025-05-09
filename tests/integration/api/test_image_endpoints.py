import pytest
import io
from httpx import AsyncClient
import uuid

from models import ImageModel


@pytest.fixture
def mock_image_file():
    """Create a mock image file for testing."""
    # Create a simple small black pixel
    return {
        "file": ("test.jpg", io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9"), "image/jpeg")
    }


@pytest.fixture
async def created_admin_api_key(test_client, setup_root_api_key, created_team, created_user):
    """Create an admin API key for testing."""
    # Create the API key with admin role
    response = await test_client.post(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Admin API Key", "role": "admin"}
    )
    
    assert response.status_code == 201
    api_key_data = response.json()
    
    yield api_key_data


@pytest.fixture
async def uploaded_image(test_client, created_team, created_user, created_api_key, mock_image_file):
    """Upload an image for testing."""
    # Create the form data with the image file
    files = {"file": mock_image_file["file"]}
    
    # Add the form fields
    data = {
        "user_id": created_user["id"],
        "title": "Test Image",
        "description": "Test image description",
        "tags": "test,image"
    }
    
    # Upload the image
    response = await test_client.post(
        f"/teams/{created_team['id']}/images",
        headers={"X-API-Key": created_api_key["key"]},
        files=files,
        data=data
    )
    
    assert response.status_code == 201
    image_data = response.json()
    
    yield image_data
    
    # Clean up - use the API key to delete the image
    await test_client.delete(
        f"/teams/{created_team['id']}/images/{image_data['id']}",
        headers={"X-API-Key": created_api_key["key"]}
    )


@pytest.mark.asyncio
async def test_upload_image_success(test_client, created_team, created_user, created_api_key, mock_image_file):
    """Test uploading an image successfully."""
    # Create the form data with the image file
    files = {"file": mock_image_file["file"]}
    
    # Add the form fields
    data = {
        "user_id": created_user["id"],
        "title": "Test Upload Image",
        "description": "Test upload image description",
        "tags": "test,upload,image"
    }
    
    # Upload the image
    response = await test_client.post(
        f"/teams/{created_team['id']}/images",
        headers={"X-API-Key": created_api_key["key"]},
        files=files,
        data=data
    )
    
    assert response.status_code == 201
    image_data = response.json()
    assert image_data["title"] == "Test Upload Image"
    assert image_data["description"] == "Test upload image description"
    assert image_data["user_id"] == created_user["id"]
    assert image_data["team_id"] == created_team["id"]
    assert "id" in image_data
    assert "filename" in image_data
    assert "url" in image_data
    assert "content_type" in image_data
    assert "metadata" in image_data
    
    # Verify tags were properly stored
    assert "tags" in image_data["metadata"]
    tags = image_data["metadata"]["tags"]
    assert "test" in tags
    assert "upload" in tags
    assert "image" in tags


@pytest.mark.asyncio
async def test_get_image(test_client, created_team, created_api_key, uploaded_image):
    """Test retrieving an image."""
    response = await test_client.get(
        f"/teams/{created_team['id']}/images/{uploaded_image['id']}",
        headers={"X-API-Key": created_api_key["key"]}
    )
    
    assert response.status_code == 200
    image_data = response.json()
    assert image_data["id"] == uploaded_image["id"]
    assert image_data["title"] == uploaded_image["title"]
    assert image_data["description"] == uploaded_image["description"]
    assert "url" in image_data


@pytest.mark.asyncio
async def test_list_team_images(test_client, created_team, created_api_key, uploaded_image):
    """Test listing team images."""
    response = await test_client.get(
        f"/teams/{created_team['id']}/images",
        headers={"X-API-Key": created_api_key["key"]}
    )
    
    assert response.status_code == 200
    images = response.json()
    assert isinstance(images, list)
    
    # Verify our uploaded image is in the list
    image_ids = [image["id"] for image in images]
    assert uploaded_image["id"] in image_ids


@pytest.mark.asyncio
async def test_list_user_images(test_client, created_team, created_user, created_api_key, uploaded_image):
    """Test listing user images."""
    response = await test_client.get(
        f"/teams/{created_team['id']}/users/{created_user['id']}/images",
        headers={"X-API-Key": created_api_key["key"]}
    )
    
    assert response.status_code == 200
    images = response.json()
    assert isinstance(images, list)
    
    # Verify our uploaded image is in the list
    image_ids = [image["id"] for image in images]
    assert uploaded_image["id"] in image_ids


@pytest.mark.asyncio
async def test_delete_image(test_client, created_team, created_user, created_api_key, mock_image_file):
    """Test deleting an image."""
    # First upload an image
    files = {"file": mock_image_file["file"]}
    data = {
        "user_id": created_user["id"],
        "title": "Image To Delete",
        "description": "This image will be deleted",
    }
    
    upload_response = await test_client.post(
        f"/teams/{created_team['id']}/images",
        headers={"X-API-Key": created_api_key["key"]},
        files=files,
        data=data
    )
    
    assert upload_response.status_code == 201
    image_data = upload_response.json()
    
    # Now delete the image
    delete_response = await test_client.delete(
        f"/teams/{created_team['id']}/images/{image_data['id']}",
        headers={"X-API-Key": created_api_key["key"]}
    )
    
    assert delete_response.status_code == 204
    
    # Verify the image is gone
    get_response = await test_client.get(
        f"/teams/{created_team['id']}/images/{image_data['id']}",
        headers={"X-API-Key": created_api_key["key"]}
    )
    
    assert get_response.status_code == 404