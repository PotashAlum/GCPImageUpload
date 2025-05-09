import pytest
from httpx import AsyncClient
import uuid
from datetime import datetime

from models import TeamModel


@pytest.fixture
async def setup_root_api_key(test_app, root_api_key):
    """Configure app to use the test root API key."""
    # Override the root API key for testing
    from dependencies import api_key_authentication_service
    api_key_authentication_service.root_key = root_api_key
    
    return root_api_key


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


@pytest.mark.asyncio
async def test_create_team_success(test_client, setup_root_api_key):
    """Test creating a team successfully."""
    team_name = f"TestTeam_{uuid.uuid4().hex[:8]}"
    
    response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": team_name, "description": "Test Team Description"}
    )
    
    assert response.status_code == 201
    team_data = response.json()
    assert team_data["name"] == team_name
    assert team_data["description"] == "Test Team Description"
    assert "id" in team_data
    assert "created_at" in team_data


@pytest.mark.asyncio
async def test_create_team_without_api_key(test_client):
    """Test creating a team without an API key."""
    team_name = f"TestTeam_{uuid.uuid4().hex[:8]}"
    
    response = await test_client.post(
        "/teams/",
        json={"name": team_name, "description": "Test Team Description"}
    )
    
    assert response.status_code == 401
    assert "API key is missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_team_with_invalid_api_key(test_client):
    """Test creating a team with an invalid API key."""
    team_name = f"TestTeam_{uuid.uuid4().hex[:8]}"
    
    response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": "invalid-api-key"},
        json={"name": team_name, "description": "Test Team Description"}
    )
    
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_team_duplicate_name(test_client, setup_root_api_key, created_team):
    """Test creating a team with a duplicate name."""
    # Try creating a team with the same name
    response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": created_team["name"], "description": "Another description"}
    )
    
    assert response.status_code == 400
    assert "Team name already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_team_by_id(test_client, setup_root_api_key, created_team):
    """Test getting a team by ID."""
    response = await test_client.get(
        f"/teams/{created_team['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert response.status_code == 200
    team_data = response.json()
    assert team_data["id"] == created_team["id"]
    assert team_data["name"] == created_team["name"]
    assert team_data["description"] == created_team["description"]


@pytest.mark.asyncio
async def test_get_team_not_found(test_client, setup_root_api_key):
    """Test getting a non-existent team."""
    non_existent_id = str(uuid.uuid4())
    
    response = await test_client.get(
        f"/teams/{non_existent_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert response.status_code == 404
    assert "Team not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_team(test_client, setup_root_api_key):
    """Test deleting a team."""
    # First create a team
    team_name = f"TeamToDelete_{uuid.uuid4().hex[:8]}"
    
    create_response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": team_name, "description": "Team to delete"}
    )
    
    assert create_response.status_code == 201
    team_data = create_response.json()
    
    # Now delete the team
    delete_response = await test_client.delete(
        f"/teams/{team_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert delete_response.status_code == 204
    
    # Verify the team is gone
    get_response = await test_client.get(
        f"/teams/{team_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_teams(test_client, setup_root_api_key, created_team):
    """Test listing all teams."""
    response = await test_client.get(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key}
    )
    
    assert response.status_code == 200
    teams = response.json()
    assert isinstance(teams, list)
    
    # Verify our created team is in the list
    team_ids = [team["id"] for team in teams]
    assert created_team["id"] in team_ids