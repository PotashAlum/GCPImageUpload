# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime
import sys
import pathlib
import io

# Add project root to Python path
project_root = str(pathlib.Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import app
from repository.repository_factory import create_mongo_db_repository
from tests.mocks.gcp_storage_mock import MockStorageClient

# Patch Google Cloud Storage before importing the service factory
import unittest.mock
unittest.mock.patch('google.cloud.storage.Client', MockStorageClient).start()

from services.service_factory import (
    create_api_key_management_service,
    create_api_key_authentication_service,
    create_gcp_storage_service
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_app():
    """Create a fresh test app for testing."""
    return app


@pytest.fixture
async def test_client(test_app):
    """Create a test client for the app."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
async def mongo_client():
    """Create a MongoDB client for testing."""
    # Use mongomock for testing
    import mongomock.motor_asyncio
    client = mongomock.motor_asyncio.AsyncIOMotorClient()
    yield client


@pytest.fixture(scope="session")
async def test_db(mongo_client):
    """Create a test database."""
    db_name = f"test_user_image_db_{uuid.uuid4().hex}"
    db = mongo_client[db_name]
    yield db


@pytest.fixture
async def test_repository(test_db):
    """Create a repository for testing."""
    # Create the repository
    repository = create_mongo_db_repository("mongodb://testing")
    # Override the database
    repository.db = test_db
    # Initialize collections
    await repository.startup_db_client()
    
    yield repository
    
    # Clean up collections
    collections = ["teams", "users", "api_keys", "images", "audit_logs"]
    for collection in collections:
        if hasattr(test_db, collection):
            await getattr(test_db, collection).delete_many({})


@pytest.fixture
async def setup_root_api_key(test_app):
    """Configure app to use the test root API key."""
    root_key = "test-root-key"
    # Override the root API key for testing
    from dependencies import api_key_authentication_service
    api_key_authentication_service.root_key = root_key
    
    return root_key


@pytest.fixture
async def root_api_key(setup_root_api_key):
    """Root API key for testing."""
    return setup_root_api_key


@pytest.fixture
async def mock_storage_client():
    """Create a mock storage client."""
    client = MockStorageClient()
    return client


@pytest.fixture
async def mock_storage_bucket(mock_storage_client):
    """Create a mock storage bucket."""
    bucket_name = "test-bucket"
    bucket = mock_storage_client.bucket(bucket_name)
    return bucket


@pytest.fixture
async def mock_storage_service(mock_storage_bucket):
    """Create a mock storage service that bypasses GCS authentication."""
    service = create_gcp_storage_service(mock_storage_bucket, mock_storage_bucket.name)
    
    # Patch the upload_file method to avoid GCS permission errors
    original_upload_file = service.upload_file
    
    async def patched_upload_file(file, path, content_type=None):
        # Create a fake URL that bypasses actual GCS
        return f"https://storage.example.com/{path}?signed=true"
    
    # Replace the method with our patched version
    service.upload_file = patched_upload_file
    
    return service

@pytest.fixture
async def created_team(test_client, setup_root_api_key):
    """Create a team for testing."""
    team_name = f"TestTeam_{uuid.uuid4().hex[:8]}"
    
    # Create the team
    response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": team_name, "description": "Test Team Description"}
    )
    
    assert response.status_code == 201
    team_data = response.json()
    
    yield team_data
    
    # Clean up
    await test_client.delete(
        f"/teams/{team_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )


@pytest.fixture
async def created_user(test_client, setup_root_api_key, created_team):
    """Create a user for testing."""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    
    # Create the user
    response = await test_client.post(
        f"/teams/{created_team['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": username, "email": email}
    )
    
    assert response.status_code == 201
    user_data = response.json()
    
    yield user_data
    
    # Clean up
    await test_client.delete(
        f"/teams/{created_team['id']}/users/{user_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )


@pytest.fixture
async def created_api_key(test_client, setup_root_api_key, created_team, created_user):
    """Create an API key for testing."""
    # Create the API key
    response = await test_client.post(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Test API Key", "role": "user"}
    )
    
    assert response.status_code == 201
    api_key_data = response.json()
    
    yield api_key_data
    
    # Clean up
    await test_client.delete(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys/{api_key_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )


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
    
    # Clean up
    await test_client.delete(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys/{api_key_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )


@pytest.fixture
def mock_image_file():
    """Create a mock image file for testing."""
    # Create a simple small black pixel JPEG
    test_image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9"
    
    return {
        "file": ("test.jpg", io.BytesIO(test_image_data), "image/jpeg")
    }


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


@pytest.fixture
async def roles_setup(test_client, setup_root_api_key, mock_image_file):
    """Set up roles for testing authorization."""
    # Create a team
    team_response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": f"AuthTeam_{uuid.uuid4().hex[:8]}", "description": "Team for testing auth"}
    )
    team_data = team_response.json()
    
    # Create admin user
    admin_username = f"admin_{uuid.uuid4().hex[:8]}"
    admin_user_response = await test_client.post(
        f"/teams/{team_data['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": admin_username, "email": f"{admin_username}@example.com"}
    )
    admin_user_data = admin_user_response.json()
    
    # Create regular user
    regular_username = f"user_{uuid.uuid4().hex[:8]}"
    regular_user_response = await test_client.post(
        f"/teams/{team_data['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": regular_username, "email": f"{regular_username}@example.com"}
    )
    regular_user_data = regular_user_response.json()
    
    # Create admin API key
    admin_key_response = await test_client.post(
        f"/teams/{team_data['id']}/users/{admin_user_data['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Admin Key", "role": "admin"}
    )
    admin_key_data = admin_key_response.json()
    
    # Create user API key
    user_key_response = await test_client.post(
        f"/teams/{team_data['id']}/users/{regular_user_data['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "User Key", "role": "user"}
    )
    user_key_data = user_key_response.json()
    
    return {
        "team": team_data,
        "admin_user": admin_user_data,
        "regular_user": regular_user_data,
        "admin_key": admin_key_data,
        "user_key": user_key_data
    }