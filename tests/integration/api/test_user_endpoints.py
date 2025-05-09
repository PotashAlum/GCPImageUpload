import pytest
from httpx import AsyncClient
import uuid

from models import UserModel


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


@pytest.mark.asyncio
async def test_create_user_success(test_client, setup_root_api_key, created_team):
    """Test creating a user successfully."""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    
    response = await test_client.post(
        f"/teams/{created_team['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": username, "email": email}
    )
    
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["username"] == username
    assert user_data["email"] == email
    assert user_data["team_id"] == created_team["id"]
    assert "id" in user_data
    assert "created_at" in user_data


@pytest.mark.asyncio
async def test_create_user_duplicate_username(test_client, setup_root_api_key, created_team, created_user):
    """Test creating a user with a duplicate username."""
    response = await test_client.post(
        f"/teams/{created_team['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": created_user["username"], "email": "different@example.com"}
    )
    
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_duplicate_email(test_client, setup_root_api_key, created_team, created_user):
    """Test creating a user with a duplicate email."""
    response = await test_client.post(
        f"/teams/{created_team['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": "differentusername", "email": created_user["email"]}
    )
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user(test_client, setup_root_api_key, created_team, created_user):
    """Test getting a user."""
    response = await test_client.get(
        f"/teams/{created_team['id']}/users/{created_user['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["id"] == created_user["id"]
    assert user_data["username"] == created_user["username"]
    assert user_data["email"] == created_user["email"]
    assert user_data["team_id"] == created_team["id"]


@pytest.mark.asyncio
async def test_list_team_users(test_client, setup_root_api_key, created_team, created_user):
    """Test listing users in a team."""
    response = await test_client.get(
        f"/teams/{created_team['id']}/users",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    
    # Verify our created user is in the list
    user_ids = [user["id"] for user in users]
    assert created_user["id"] in user_ids


@pytest.mark.asyncio
async def test_delete_user(test_client, setup_root_api_key, created_team):
    """Test deleting a user."""
    # First create a user
    username = f"userToDelete_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    
    create_response = await test_client.post(
        f"/teams/{created_team['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": username, "email": email}
    )
    
    assert create_response.status_code == 201
    user_data = create_response.json()
    
    # Now delete the user
    delete_response = await test_client.delete(
        f"/teams/{created_team['id']}/users/{user_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert delete_response.status_code == 204
    
    # Verify the user is gone
    get_response = await test_client.get(
        f"/teams/{created_team['id']}/users/{user_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert get_response.status_code == 404