import pytest
from httpx import AsyncClient
import uuid

@pytest.fixture
async def roles_setup(test_client, setup_root_api_key):
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
        json={"username": admin_username, "email": f"admin_{uuid.uuid4().hex[:8]}@example.com"}
    )
    admin_user_data = admin_user_response.json()
    
    # Create regular user
    regular_username = f"user_{uuid.uuid4().hex[:8]}"
    regular_user_response = await test_client.post(
        f"/teams/{team_data['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": regular_username, "email": f"user_{uuid.uuid4().hex[:8]}@example.com"}
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


@pytest.mark.asyncio
async def test_root_access(test_client, setup_root_api_key):
    """Test that root can access everything."""
    # Root can list all teams
    teams_response = await test_client.get(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert teams_response.status_code == 200
    
    # Root can access audit logs
    logs_response = await test_client.get(
        "/audit-logs/",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert logs_response.status_code == 200


@pytest.mark.asyncio
async def test_admin_vs_user_access(test_client, roles_setup):
    """Test different access levels for admin vs user roles."""
    team = roles_setup["team"]
    admin_key = roles_setup["admin_key"]["key"]
    user_key = roles_setup["user_key"]["key"]
    
    # Admin can list team API keys
    admin_list_keys = await test_client.get(
        f"/teams/{team['id']}/api-keys",
        headers={"X-API-Key": admin_key}
    )
    assert admin_list_keys.status_code == 200
    
    # User cannot list team API keys
    user_list_keys = await test_client.get(
        f"/teams/{team['id']}/api-keys",
        headers={"X-API-Key": user_key}
    )
    assert user_list_keys.status_code == 403
    
    # Admin can create users
    new_username = f"newuser_{uuid.uuid4().hex[:8]}"
    admin_create_user = await test_client.post(
        f"/teams/{team['id']}/users",
        headers={"X-API-Key": admin_key},
        json={"username": new_username, "email": f"{new_username}@example.com"}
    )
    assert admin_create_user.status_code == 201
    
    # User cannot create users
    new_username2 = f"newuser_{uuid.uuid4().hex[:8]}"
    user_create_user = await test_client.post(
        f"/teams/{team['id']}/users",
        headers={"X-API-Key": user_key},
        json={"username": new_username2, "email": f"{new_username2}@example.com"}
    )
    assert user_create_user.status_code == 403


@pytest.mark.asyncio
async def test_resource_ownership(test_client, roles_setup, mock_image_file):
    """Test that users can only access their own resources."""
    team = roles_setup["team"]
    admin_user = roles_setup["admin_user"]
    regular_user = roles_setup["regular_user"]
    admin_key = roles_setup["admin_key"]["key"]
    user_key = roles_setup["user_key"]["key"]
    
    # Upload an image as regular user
    files = {"file": mock_image_file["file"]}
    data = {
        "user_id": regular_user["id"],
        "title": "User Image",
        "description": "Image uploaded by regular user",
    }
    
    upload_response = await test_client.post(
        f"/teams/{team['id']}/images",
        headers={"X-API-Key": user_key},
        files=files,
        data=data
    )
    
    assert upload_response.status_code == 201
    user_image = upload_response.json()
    
    # Upload an image as admin
    files = {"file": mock_image_file["file"]}
    data = {
        "user_id": admin_user["id"],
        "title": "Admin Image",
        "description": "Image uploaded by admin",
    }
    
    admin_upload_response = await test_client.post(
        f"/teams/{team['id']}/images",
        headers={"X-API-Key": admin_key},
        files=files,
        data=data
    )
    
    assert admin_upload_response.status_code == 201
    admin_image = admin_upload_response.json()
    
    # Regular user can view their own image
    user_view_own = await test_client.get(
        f"/teams/{team['id']}/images/{user_image['id']}",
        headers={"X-API-Key": user_key}
    )
    assert user_view_own.status_code == 200
    
    # Regular user can view admin's image (any team member can view team images)
    user_view_admin = await test_client.get(
        f"/teams/{team['id']}/images/{admin_image['id']}",
        headers={"X-API-Key": user_key}
    )
    assert user_view_admin.status_code == 200
    
    # Regular user can delete their own image
    user_delete_own = await test_client.delete(
        f"/teams/{team['id']}/images/{user_image['id']}",
        headers={"X-API-Key": user_key}
    )
    assert user_delete_own.status_code == 204
    
    # Regular user cannot delete admin's image
    user_delete_admin = await test_client.delete(
        f"/teams/{team['id']}/images/{admin_image['id']}",
        headers={"X-API-Key": user_key}
    )
    assert user_delete_admin.status_code == 403
    
    # Admin can delete any image in their team
    admin_delete = await test_client.delete(
        f"/teams/{team['id']}/images/{admin_image['id']}",
        headers={"X-API-Key": admin_key}
    )
    assert admin_delete.status_code == 204


@pytest.mark.asyncio
async def test_cross_team_access(test_client, setup_root_api_key, roles_setup):
    """Test that teams cannot access each other's resources."""
    # Create a second team with a user
    team2_response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": f"SecondTeam_{uuid.uuid4().hex[:8]}", "description": "Second team for testing"}
    )
    team2_data = team2_response.json()
    
    # Create user in second team
    team2_user_response = await test_client.post(
        f"/teams/{team2_data['id']}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": f"team2user_{uuid.uuid4().hex[:8]}", "email": f"team2_{uuid.uuid4().hex[:8]}@example.com"}
    )
    team2_user_data = team2_user_response.json()
    
    # Create API key for team2 user
    team2_key_response = await test_client.post(
        f"/teams/{team2_data['id']}/users/{team2_user_data['id']}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Team 2 Key", "role": "user"}
    )
    team2_key_data = team2_key_response.json()
    
    # Team 1 user cannot access Team 2 resources
    team1_accessing_team2 = await test_client.get(
        f"/teams/{team2_data['id']}/users",
        headers={"X-API-Key": roles_setup["user_key"]["key"]}
    )
    assert team1_accessing_team2.status_code == 403
    
    # Team 2 user cannot access Team 1 resources
    team2_accessing_team1 = await test_client.get(
        f"/teams/{roles_setup['team']['id']}/users",
        headers={"X-API-Key": team2_key_data["key"]}
    )
    assert team2_accessing_team1.status_code == 403