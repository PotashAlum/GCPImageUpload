import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import secrets
import hashlib
from datetime import datetime
from fastapi import HTTPException

from services.implementation.api_key_management_service import APIKeyManagementService
from models import APIKeyModel, APIKeyCreateResponse


@pytest.fixture
def mock_repository():
    repository = AsyncMock()
    api_keys = AsyncMock()
    repository.api_keys = api_keys
    return repository


@pytest.fixture
def api_key_data():
    return {
        "id": "test-key-id",
        "name": "Test API Key",
        "key_prefix": "sk_test_a",
        "key_hash": "hashed_key_value",
        "key_salt": "salt_value",
        "role": "user",
        "user_id": "test-user-id",
        "team_id": "test-team-id",
        "created_at": datetime.now()
    }


@pytest.fixture
def api_key_management_service(mock_repository):
    return APIKeyManagementService(mock_repository)


@pytest.mark.asyncio
async def test_create_api_key(api_key_management_service):
    # Mock UUID and secrets
    test_uuid = "test-uuid-value"
    test_secret = "test-secret-value"
    test_salt = "test-salt-value"
    test_hash = "test-hash-value"
    
    name = "New API Key"
    role = "user"
    user_id = "user-123"
    team_id = "team-456"
    
    # Patch the required modules
    with patch('uuid.uuid4', return_value=MagicMock(return_value=test_uuid, __str__=lambda _: test_uuid)), \
         patch('secrets.token_urlsafe', return_value=test_secret), \
         patch('os.urandom', return_value=MagicMock(hex=lambda: test_salt)), \
         patch('hashlib.pbkdf2_hmac', return_value=MagicMock(hex=lambda: test_hash)):
        
        # Call the method
        result = await api_key_management_service.create_api_key(name, role, user_id, team_id)
        
        # Verify the repository call
        api_key_management_service.repository.api_keys.create_api_key.assert_called_once()
        
        # Verify the created API key model
        call_args = api_key_management_service.repository.api_keys.create_api_key.call_args[0][0]
        assert call_args["id"] == test_uuid
        assert call_args["name"] == name
        assert call_args["role"] == role
        assert call_args["user_id"] == user_id
        assert call_args["team_id"] == team_id
        assert call_args["key_prefix"] == f"sk_{test_secret}"[:api_key_management_service.KEY_PREFIX_LENGTH]
        assert call_args["key_hash"] == test_hash
        assert call_args["key_salt"] == test_salt
        
        # Verify the response
        assert isinstance(result, APIKeyCreateResponse)
        assert result.id == test_uuid
        assert result.name == name
        assert result.role == role
        assert result.user_id == user_id
        assert result.team_id == team_id
        assert result.key == f"sk_{test_secret}"


@pytest.mark.asyncio
async def test_get_api_key_by_id(api_key_management_service, api_key_data):
    # Setup mock
    key_model = APIKeyModel(**api_key_data)
    api_key_management_service.repository.api_keys.get_api_key_by_id.return_value = key_model
    
    # Call the method
    result = await api_key_management_service.get_api_key_by_id(api_key_data["id"])
    
    # Verify
    api_key_management_service.repository.api_keys.get_api_key_by_id.assert_called_once_with(api_key_data["id"])
    assert result == key_model


@pytest.mark.asyncio
async def test_get_api_key_by_id_not_found(api_key_management_service):
    # Setup mock
    api_key_management_service.repository.api_keys.get_api_key_by_id.return_value = None
    
    # Call the method
    with pytest.raises(HTTPException) as exc_info:
        await api_key_management_service.get_api_key_by_id("non-existent-id")
    
    # Verify
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "API key not found"


@pytest.mark.asyncio
async def test_delete_api_key(api_key_management_service, api_key_data):
    # Setup mock
    key_model = APIKeyModel(**api_key_data)
    api_key_management_service.repository.api_keys.get_api_key_by_id.return_value = key_model
    
    # Call the method
    await api_key_management_service.delete_api_key(api_key_data["id"])
    
    # Verify
    api_key_management_service.repository.api_keys.get_api_key_by_id.assert_called_once_with(api_key_data["id"])
    api_key_management_service.repository.api_keys.delete_api_key.assert_called_once_with(api_key_data["id"])


@pytest.mark.asyncio
async def test_delete_api_key_not_found(api_key_management_service):
    # Setup mock
    api_key_management_service.repository.api_keys.get_api_key_by_id.return_value = None
    
    # Call the method
    with pytest.raises(HTTPException) as exc_info:
        await api_key_management_service.delete_api_key("non-existent-id")
    
    # Verify
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "API key not found"
    api_key_management_service.repository.api_keys.delete_api_key.assert_not_called()