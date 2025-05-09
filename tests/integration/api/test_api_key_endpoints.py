import pytest
from httpx import AsyncClient
import uuid

from models import APIKeyModel, APIKeyCreateResponse


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


@pytest.mark.asyncio
async def test_create_api_key_success(test_client, setup_root_api_key, created_team, created_user):
    """Test creating an API key successfully."""
    response = await test_client.post(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "New API Key", "role": "user"}
    )
    
    assert response.status_code == 201
    api_key_data = response.json()
    assert api_key_data["name"] == "New API Key"
    assert api_key_data["role"] == "user"
    assert api_key_data["user_id"] == created_user["id"]
    assert api_key_data["team_id"] == created_team["id"]
    assert "id" in api_key_data
    assert "key" in api_key_data  # Full key is returned only at creation time
    assert "created_at" in api_key_data


@pytest.mark.asyncio
async def test_create_api_key_invalid_role(test_client, setup_root_api_key, created_team, created_user):
    """Test creating an API key with an invalid role."""
    response = await test_client.post(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Invalid Role Key", "role": "invalid_role"}
    )
    
    assert response.status_code == 400
    assert "Role must be 'admin' or 'user'" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_api_key(test_client, setup_root_api_key, created_team, created_user, created_api_key):
    """Test getting an API key."""
    response = await test_client.get(
        f"/teams/{created_team['id']}/api-keys/{created_api_key['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert response.status_code == 200
    api_key_data = response.json()
    assert api_key_data["id"] == created_api_key["id"]
    assert api_key_data["name"] == created_api_key["name"]
    assert api_key_data["user_id"] == created_user["id"]
    assert api_key_data["team_id"] == created_team["id"]
    assert "key" not in api_key_data  # Full key is NOT returned after creation


@pytest.mark.asyncio
async def test_list_user_api_keys(test_client, setup_root_api_key, created_team, created_user, created_api_key):
    """Test listing API keys for a user."""
    response = await test_client.get(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert response.status_code == 200
    api_keys = response.json()
    assert isinstance(api_keys, list)
    
    # Verify our created API key is in the list
    api_key_ids = [api_key["id"] for api_key in api_keys]
    assert created_api_key["id"] in api_key_ids


@pytest.mark.asyncio
async def test_delete_api_key(test_client, setup_root_api_key, created_team, created_user):
    """Test deleting an API key."""
    # First create an API key
    create_response = await test_client.post(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Key To Delete", "role": "user"}
    )
    
    assert create_response.status_code == 201
    api_key_data = create_response.json()
    
    # Now delete the API key
    delete_response = await test_client.delete(
        f"/teams/{created_team['id']}/users/{created_user['id']}/api-keys/{api_key_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert delete_response.status_code == 204
    
    # Verify the API key is gone
    get_response = await test_client.get(
        f"/teams/{created_team['id']}/api-keys/{api_key_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_use_created_api_key(test_client, created_team, created_user, created_api_key):
    """Test using a newly created API key to access resources."""
    # Use the API key to access team information
    response = await test_client.get(
        f"/teams/{created_team['id']}",
        headers={"X-API-Key": created_api_key["key"]}
    )
    
    assert response.status_code == 200
    team_data = response.json()
    assert team_data["id"] == created_team["id"]