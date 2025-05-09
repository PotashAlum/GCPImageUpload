import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException

from services.implementation.authorization_service import AuthorizationService
from models.api_key_model import APIKeyModel
from models.user_model import UserModel
from models.image_model import ImageModel


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    repository.users = AsyncMock()
    repository.api_keys = AsyncMock()
    repository.images = AsyncMock()
    return repository


@pytest.fixture
def authorization_service(mock_repository):
    return AuthorizationService(mock_repository)


@pytest.fixture
def api_key_info():
    return APIKeyModel(
        id="api-key-123",
        name="Test API Key",
        key_prefix="sk_test_",
        key_hash="hashed_key_value",
        key_salt="salt_value",
        role="user",
        user_id="user-123",
        team_id="team-123",
        created_at=datetime.now()
    )


@pytest.fixture
def admin_api_key_info():
    return APIKeyModel(
        id="api-key-456",
        name="Admin API Key",
        key_prefix="sk_test_",
        key_hash="hashed_key_value",
        key_salt="salt_value",
        role="admin",
        user_id="admin-123",
        team_id="team-123",
        created_at=datetime.now()
    )


@pytest.fixture
def root_api_key_info():
    return APIKeyModel(
        id="api-key-789",
        name="Root API Key",
        key_prefix="sk_test_",
        key_hash="hashed_key_value",
        key_salt="salt_value",
        role="root",
        user_id="root",
        team_id="",
        created_at=datetime.now()
    )


def test_extract_path_parameters(authorization_service):
    # Test team ID extraction
    path = "teams/team-123"
    params = authorization_service.extract_path_parameters(path)
    assert params == {"team_id": "team-123"}
    
    # Test team and user ID extraction
    path = "teams/team-123/users/user-456"
    params = authorization_service.extract_path_parameters(path)
    assert params == {"team_id": "team-123", "user_id": "user-456"}
    
    # Test team, user, and API key ID extraction
    path = "teams/team-123/users/user-456/api-keys/key-789"
    params = authorization_service.extract_path_parameters(path)
    assert params == {"team_id": "team-123", "user_id": "user-456", "api_key_id": "key-789"}
    
    # Test team and image ID extraction
    path = "teams/team-123/images/img-456"
    params = authorization_service.extract_path_parameters(path)
    assert params == {"team_id": "team-123", "image_id": "img-456"}
    

@pytest.mark.asyncio
async def test_authorize_request_root_can_do_anything(authorization_service, root_api_key_info):
    method = "GET"
    path = "teams"
    path_params = {}
    
    result = await authorization_service.authorize_request(method, path, root_api_key_info, path_params)
    assert result is True


@pytest.mark.asyncio
async def test_authorize_request_no_permission_rule(authorization_service, api_key_info):
    method = "PUT"
    path = "nonexistent/resource"
    path_params = {}
    
    with pytest.raises(HTTPException) as exc_info:
        await authorization_service.authorize_request(method, path, api_key_info, path_params)
    
    assert exc_info.value.status_code == 403
    assert "No permission rule found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authorize_request_insufficient_role(authorization_service, api_key_info):
    # User trying to access admin-only endpoint
    method = "POST"
    path = "teams/team-123/api-keys"
    path_params = {"team_id": "team-123"}
    
    with pytest.raises(HTTPException) as exc_info:
        await authorization_service.authorize_request(method, path, api_key_info, path_params)
    
    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authorize_request_wrong_team(authorization_service, api_key_info):
    method = "GET"
    path = "teams/team-456/users"
    path_params = {"team_id": "team-456"}  # Different from user's team
    
    with pytest.raises(HTTPException) as exc_info:
        await authorization_service.authorize_request(method, path, api_key_info, path_params)
    
    assert exc_info.value.status_code == 403
    assert "You can only access resources within your team" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authorize_request_user_accessing_other_user(authorization_service, api_key_info):
    method = "GET"
    path = "teams/team-123/users/another-user/images"
    path_params = {"team_id": "team-123", "user_id": "another-user"}  # Different from user's ID
    
    with pytest.raises(HTTPException) as exc_info:
        await authorization_service.authorize_request(method, path, api_key_info, path_params)
    
    assert exc_info.value.status_code == 403
    assert "You can only access your own information" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authorize_request_admin_accessing_team_user(authorization_service, admin_api_key_info):
    method = "GET"
    path = "teams/team-123/users/user-456"
    path_params = {"team_id": "team-123", "user_id": "user-456"}
    
    # Setup mock
    user_model = UserModel(
        id="user-456",
        username="testuser",
        email="test@example.com",
        team_id="team-123",  # Same team as admin
        created_at=datetime.now()
    )
    authorization_service.repository.users.get_user_by_id.return_value = user_model
    
    result = await authorization_service.authorize_request(method, path, admin_api_key_info, path_params)
    
    authorization_service.repository.users.get_user_by_id.assert_called_once_with("user-456")
    assert result is True


@pytest.mark.asyncio
async def test_authorize_request_admin_accessing_other_team_user(authorization_service, admin_api_key_info):
    method = "GET"
    path = "teams/team-123/users/user-456"
    path_params = {"team_id": "team-123", "user_id": "user-456"}
    
    # Setup mock - user from different team
    user_model = UserModel(
        id="user-456",
        username="testuser",
        email="test@example.com",
        team_id="team-789",  # Different team
        created_at=datetime.now()
    )
    authorization_service.repository.users.get_user_by_id.return_value = user_model
    
    with pytest.raises(HTTPException) as exc_info:
        await authorization_service.authorize_request(method, path, admin_api_key_info, path_params)
    
    authorization_service.repository.users.get_user_by_id.assert_called_once_with("user-456")
    assert exc_info.value.status_code == 403
    assert "User does not belong to your team" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authorize_request_user_deleting_own_image(authorization_service, api_key_info):
    method = "DELETE"
    path = "teams/team-123/images/img-456"
    path_params = {"team_id": "team-123", "image_id": "img-456"}
    
    # Setup mock - image uploaded by the user
    image_model = ImageModel(
        id="img-456",
        user_id=api_key_info.user_id,  # Same user
        team_id="team-123",
        filename="test.jpg",
        content_type="image/jpeg",
        size=1024,
        url="http://example.com/test.jpg",
        created_at=datetime.now()
    )
    authorization_service.repository.images.get_image_by_id.return_value = image_model
    
    result = await authorization_service.authorize_request(method, path, api_key_info, path_params)
    
    authorization_service.repository.images.get_image_by_id.assert_called_once_with("img-456")
    assert result is True


@pytest.mark.asyncio
async def test_authorize_request_user_deleting_other_user_image(authorization_service, api_key_info):
    method = "DELETE"
    path = "teams/team-123/images/img-456"
    path_params = {"team_id": "team-123", "image_id": "img-456"}
    
    # Setup mock - image uploaded by another user
    image_model = ImageModel(
        id="img-456",
        user_id="another-user-id",  # Different user
        team_id="team-123",
        filename="test.jpg",
        content_type="image/jpeg",
        size=1024,
        url="http://example.com/test.jpg",
        created_at=datetime.now()
    )
    authorization_service.repository.images.get_image_by_id.return_value = image_model
    
    with pytest.raises(HTTPException) as exc_info:
        await authorization_service.authorize_request(method, path, api_key_info, path_params)
    
    authorization_service.repository.images.get_image_by_id.assert_called_once_with("img-456")
    assert exc_info.value.status_code == 403
    assert "You can only delete your own images" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authorize_request_admin_deleting_any_team_image(authorization_service, admin_api_key_info):
    method = "DELETE"
    path = "teams/team-123/images/img-456"
    path_params = {"team_id": "team-123", "image_id": "img-456"}
    
    # Setup mock - image uploaded by another user
    image_model = ImageModel(
        id="img-456",
        user_id="some-user-id",  # Different from admin
        team_id="team-123",  # Same team
        filename="test.jpg",
        content_type="image/jpeg",
        size=1024,
        url="http://example.com/test.jpg",
        created_at=datetime.now()
    )
    authorization_service.repository.images.get_image_by_id.return_value = image_model
    
    result = await authorization_service.authorize_request(method, path, admin_api_key_info, path_params)
    
    authorization_service.repository.images.get_image_by_id.assert_called_once_with("img-456")
    assert result is True