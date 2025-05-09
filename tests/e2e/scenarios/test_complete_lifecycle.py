import pytest
from httpx import AsyncClient
import io
import uuid
import asyncio
from datetime import datetime


@pytest.mark.asyncio
async def test_team_lifecycle(test_client, setup_root_api_key):
    """
    Test a complete team lifecycle from creation to deletion.
    
    Steps:
    1. Create a team
    2. Create admin and regular users
    3. Create API keys for each user
    4. Upload images
    5. Verify access rights
    6. Delete resources in correct order
    """
    # Step 1: Create a team
    team_name = f"LifecycleTeam_{uuid.uuid4().hex[:8]}"
    team_response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": team_name, "description": "Team for lifecycle testing"}
    )
    assert team_response.status_code == 201
    team_data = team_response.json()
    team_id = team_data["id"]
    
    # Step 2: Create admin and regular users
    admin_username = f"admin_{uuid.uuid4().hex[:8]}"
    admin_email = f"{admin_username}@example.com"
    admin_response = await test_client.post(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": admin_username, "email": admin_email}
    )
    assert admin_response.status_code == 201
    admin_data = admin_response.json()
    admin_id = admin_data["id"]
    
    regular_username = f"user_{uuid.uuid4().hex[:8]}"
    regular_email = f"{regular_username}@example.com"
    user_response = await test_client.post(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": regular_username, "email": regular_email}
    )
    assert user_response.status_code == 201
    user_data = user_response.json()
    user_id = user_data["id"]
    
    # Step 3: Create API keys for each user
    admin_key_response = await test_client.post(
        f"/teams/{team_id}/users/{admin_id}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Admin Lifecycle Key", "role": "admin"}
    )
    assert admin_key_response.status_code == 201
    admin_key_data = admin_key_response.json()
    admin_key = admin_key_data["key"]
    
    user_key_response = await test_client.post(
        f"/teams/{team_id}/users/{user_id}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "User Lifecycle Key", "role": "user"}
    )
    assert user_key_response.status_code == 201
    user_key_data = user_key_response.json()
    user_key = user_key_data["key"]
    
    # Step 4: Upload images
    # Create a simple test image
    test_image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9"
    
    # Upload image as admin
    admin_image_file = ("admin_test.jpg", io.BytesIO(test_image_data), "image/jpeg")
    admin_image_response = await test_client.post(
        f"/teams/{team_id}/images",
        headers={"X-API-Key": admin_key},
        files={"file": admin_image_file},
        data={
            "user_id": admin_id,
            "title": "Admin Test Image",
            "description": "Image uploaded by admin",
            "tags": "admin,test,lifecycle"
        }
    )
    assert admin_image_response.status_code == 201
    admin_image_data = admin_image_response.json()
    admin_image_id = admin_image_data["id"]
    
    # Upload image as regular user
    user_image_file = ("user_test.jpg", io.BytesIO(test_image_data), "image/jpeg")
    user_image_response = await test_client.post(
        f"/teams/{team_id}/images",
        headers={"X-API-Key": user_key},
        files={"file": user_image_file},
        data={
            "user_id": user_id,
            "title": "User Test Image",
            "description": "Image uploaded by regular user",
            "tags": "user,test,lifecycle"
        }
    )
    assert user_image_response.status_code == 201
    user_image_data = user_image_response.json()
    user_image_id = user_image_data["id"]
    
    # Step 5: Verify access rights
    # Everyone can list team images
    team_images_response = await test_client.get(
        f"/teams/{team_id}/images",
        headers={"X-API-Key": user_key}
    )
    assert team_images_response.status_code == 200
    team_images = team_images_response.json()
    assert len(team_images) == 2
    
    # Admin can list team users
    team_users_response = await test_client.get(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": admin_key}
    )
    assert team_users_response.status_code == 200
    team_users = team_users_response.json()
    assert len(team_users) == 2
    
    # Regular user can only delete their own image
    user_delete_admin_image = await test_client.delete(
        f"/teams/{team_id}/images/{admin_image_id}",
        headers={"X-API-Key": user_key}
    )
    assert user_delete_admin_image.status_code == 403
    
    # Admin can delete any image
    admin_delete_user_image = await test_client.delete(
        f"/teams/{team_id}/images/{user_image_id}",
        headers={"X-API-Key": admin_key}
    )
    assert admin_delete_user_image.status_code == 204
    
    # Step 6: Delete resources in correct order
    # Delete admin's image
    admin_delete_own_image = await test_client.delete(
        f"/teams/{team_id}/images/{admin_image_id}",
        headers={"X-API-Key": admin_key}
    )
    assert admin_delete_own_image.status_code == 204
    
    # Delete API keys
    delete_user_key = await test_client.delete(
        f"/teams/{team_id}/users/{user_id}/api-keys/{user_key_data['id']}",
        headers={"X-API-Key": admin_key}
    )
    assert delete_user_key.status_code == 204
    
    delete_admin_key = await test_client.delete(
        f"/teams/{team_id}/users/{admin_id}/api-keys/{admin_key_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_admin_key.status_code == 204
    
    # Delete users
    delete_user = await test_client.delete(
        f"/teams/{team_id}/users/{user_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_user.status_code == 204
    
    delete_admin = await test_client.delete(
        f"/teams/{team_id}/users/{admin_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_admin.status_code == 204
    
    # Delete team
    delete_team = await test_client.delete(
        f"/teams/{team_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_team.status_code == 204


@pytest.mark.asyncio
async def test_user_image_management_flow(test_client, setup_root_api_key):
    """
    Test a user uploading, viewing, and deleting images.
    
    Steps:
    1. Create a team
    2. Create a user
    3. Create a user API key
    4. Upload multiple images
    5. List and filter images
    6. Get image details
    7. Delete images
    8. Clean up
    """
    # Step 1: Create a team
    team_name = f"ImageFlowTeam_{uuid.uuid4().hex[:8]}"
    team_response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": team_name, "description": "Team for image flow testing"}
    )
    assert team_response.status_code == 201
    team_data = team_response.json()
    team_id = team_data["id"]
    
    # Step 2: Create a user
    username = f"imageuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    user_response = await test_client.post(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": username, "email": email}
    )
    assert user_response.status_code == 201
    user_data = user_response.json()
    user_id = user_data["id"]
    
    # Step 3: Create a user API key
    key_response = await test_client.post(
        f"/teams/{team_id}/users/{user_id}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Image Flow Key", "role": "user"}
    )
    assert key_response.status_code == 201
    key_data = key_response.json()
    api_key = key_data["key"]
    
    # Step 4: Upload multiple images
    test_image_data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9"
    
    # Upload first image
    image1_file = ("logo1.jpg", io.BytesIO(test_image_data), "image/jpeg")
    image1_response = await test_client.post(
        f"/teams/{team_id}/images",
        headers={"X-API-Key": api_key},
        files={"file": image1_file},
        data={
            "user_id": user_id,
            "title": "Company Logo 1",
            "description": "First company logo",
            "tags": "logo,brand,company"
        }
    )
    assert image1_response.status_code == 201
    image1_data = image1_response.json()
    
    # Upload second image
    image2_file = ("profile1.jpg", io.BytesIO(test_image_data), "image/jpeg")
    image2_response = await test_client.post(
        f"/teams/{team_id}/images",
        headers={"X-API-Key": api_key},
        files={"file": image2_file},
        data={
            "user_id": user_id,
            "title": "Profile Photo 1",
            "description": "First profile photo",
            "tags": "profile,photo,headshot"
        }
    )
    assert image2_response.status_code == 201
    image2_data = image2_response.json()
    
    # Upload third image
    image3_file = ("banner1.jpg", io.BytesIO(test_image_data), "image/jpeg")
    image3_response = await test_client.post(
        f"/teams/{team_id}/images",
        headers={"X-API-Key": api_key},
        files={"file": image3_file},
        data={
            "user_id": user_id,
            "title": "Website Banner 1",
            "description": "First website banner",
            "tags": "banner,website,marketing"
        }
    )
    assert image3_response.status_code == 201
    image3_data = image3_response.json()
    
    # Step 5: List and filter images
    # List all user's images
    user_images_response = await test_client.get(
        f"/teams/{team_id}/users/{user_id}/images",
        headers={"X-API-Key": api_key}
    )
    assert user_images_response.status_code == 200
    user_images = user_images_response.json()
    assert len(user_images) == 3
    
    # Step 6: Get image details
    image_details_response = await test_client.get(
        f"/teams/{team_id}/images/{image1_data['id']}",
        headers={"X-API-Key": api_key}
    )
    assert image_details_response.status_code == 200
    image_details = image_details_response.json()
    assert image_details["title"] == "Company Logo 1"
    assert "url" in image_details
    assert "metadata" in image_details
    assert "tags" in image_details["metadata"]
    
    # Step 7: Delete images
    delete_image1 = await test_client.delete(
        f"/teams/{team_id}/images/{image1_data['id']}",
        headers={"X-API-Key": api_key}
    )
    assert delete_image1.status_code == 204
    
    delete_image2 = await test_client.delete(
        f"/teams/{team_id}/images/{image2_data['id']}",
        headers={"X-API-Key": api_key}
    )
    assert delete_image2.status_code == 204
    
    delete_image3 = await test_client.delete(
        f"/teams/{team_id}/images/{image3_data['id']}",
        headers={"X-API-Key": api_key}
    )
    assert delete_image3.status_code == 204
    
    # Step 8: Clean up
    # Delete API key
    delete_key = await test_client.delete(
        f"/teams/{team_id}/users/{user_id}/api-keys/{key_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_key.status_code == 204
    
    # Delete user
    delete_user = await test_client.delete(
        f"/teams/{team_id}/users/{user_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_user.status_code == 204
    
    # Delete team
    delete_team = await test_client.delete(
        f"/teams/{team_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_team.status_code == 204


@pytest.mark.asyncio
async def test_api_key_management_flow(test_client, setup_root_api_key):
    """
    Test creating, using, and revoking API keys.
    
    Steps:
    1. Create a team
    2. Create admin and regular users
    3. Create multiple API keys for each user
    4. Use each key to access resources
    5. Revoke keys and verify they no longer work
    6. Clean up
    """
    # Step 1: Create a team
    team_name = f"KeyMgmtTeam_{uuid.uuid4().hex[:8]}"
    team_response = await test_client.post(
        "/teams/",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": team_name, "description": "Team for API key management testing"}
    )
    assert team_response.status_code == 201
    team_data = team_response.json()
    team_id = team_data["id"]
    
    # Step 2: Create admin and regular users
    admin_username = f"keyadmin_{uuid.uuid4().hex[:8]}"
    admin_email = f"{admin_username}@example.com"
    admin_response = await test_client.post(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": admin_username, "email": admin_email}
    )
    assert admin_response.status_code == 201
    admin_data = admin_response.json()
    admin_id = admin_data["id"]
    
    regular_username = f"keyuser_{uuid.uuid4().hex[:8]}"
    regular_email = f"{regular_username}@example.com"
    user_response = await test_client.post(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": setup_root_api_key},
        json={"username": regular_username, "email": regular_email}
    )
    assert user_response.status_code == 201
    user_data = user_response.json()
    user_id = user_data["id"]
    
    # Step 3: Create multiple API keys for each user
    # Admin keys
    admin_key1_response = await test_client.post(
        f"/teams/{team_id}/users/{admin_id}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Admin Key 1", "role": "admin"}
    )
    assert admin_key1_response.status_code == 201
    admin_key1_data = admin_key1_response.json()
    
    admin_key2_response = await test_client.post(
        f"/teams/{team_id}/users/{admin_id}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "Admin Key 2", "role": "admin"}
    )
    assert admin_key2_response.status_code == 201
    admin_key2_data = admin_key2_response.json()
    
    # User keys
    user_key1_response = await test_client.post(
        f"/teams/{team_id}/users/{user_id}/api-keys",
        headers={"X-API-Key": setup_root_api_key},
        json={"name": "User Key 1", "role": "user"}
    )
    assert user_key1_response.status_code == 201
    user_key1_data = user_key1_response.json()
    
    user_key2_response = await test_client.post(
        f"/teams/{team_id}/users/{user_id}/api-keys",
        headers={"X-API-Key": admin_key1_data["key"]},  # Use admin key to create user key
        json={"name": "User Key 2", "role": "user"}
    )
    assert user_key2_response.status_code == 201
    user_key2_data = user_key2_response.json()
    
    # Step 4: Use each key to access resources
    # Use admin key 1
    admin_key1_test = await test_client.get(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": admin_key1_data["key"]}
    )
    assert admin_key1_test.status_code == 200
    
    # Use admin key 2
    admin_key2_test = await test_client.get(
        f"/teams/{team_id}/api-keys",
        headers={"X-API-Key": admin_key2_data["key"]}
    )
    assert admin_key2_test.status_code == 200
    
    # Use user key 1
    user_key1_test = await test_client.get(
        f"/teams/{team_id}/users/{user_id}",
        headers={"X-API-Key": user_key1_data["key"]}
    )
    assert user_key1_test.status_code == 200
    
    # Use user key 2
    user_key2_test = await test_client.get(
        f"/teams/{team_id}",
        headers={"X-API-Key": user_key2_data["key"]}
    )
    assert user_key2_test.status_code == 200
    
    # Step 5: Revoke keys and verify they no longer work
    # Revoke admin key 1
    revoke_admin_key1 = await test_client.delete(
        f"/teams/{team_id}/users/{admin_id}/api-keys/{admin_key1_data['id']}",
        headers={"X-API-Key": admin_key2_data["key"]}  # Use admin key 2 to revoke admin key 1
    )
    assert revoke_admin_key1.status_code == 204
    
    # Verify admin key 1 no longer works
    admin_key1_after_revoke = await test_client.get(
        f"/teams/{team_id}/users",
        headers={"X-API-Key": admin_key1_data["key"]}
    )
    assert admin_key1_after_revoke.status_code == 401
    
    # Revoke user key 1
    revoke_user_key1 = await test_client.delete(
        f"/teams/{team_id}/users/{user_id}/api-keys/{user_key1_data['id']}",
        headers={"X-API-Key": user_key2_data["key"]}  # User can revoke their own key
    )
    assert revoke_user_key1.status_code == 204
    
    # Verify user key 1 no longer works
    user_key1_after_revoke = await test_client.get(
        f"/teams/{team_id}/users/{user_id}",
        headers={"X-API-Key": user_key1_data["key"]}
    )
    assert user_key1_after_revoke.status_code == 401
    
    # Step 6: Clean up
    # Delete remaining API keys
    delete_admin_key2 = await test_client.delete(
        f"/teams/{team_id}/users/{admin_id}/api-keys/{admin_key2_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_admin_key2.status_code == 204
    
    delete_user_key2 = await test_client.delete(
        f"/teams/{team_id}/users/{user_id}/api-keys/{user_key2_data['id']}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_user_key2.status_code == 204
    
    # Delete users
    delete_admin = await test_client.delete(
        f"/teams/{team_id}/users/{admin_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_admin.status_code == 204
    
    delete_user = await test_client.delete(
        f"/teams/{team_id}/users/{user_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_user.status_code == 204
    
    # Delete team
    delete_team = await test_client.delete(
        f"/teams/{team_id}",
        headers={"X-API-Key": setup_root_api_key}
    )
    assert delete_team.status_code == 204