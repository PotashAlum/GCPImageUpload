import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hashlib
from datetime import datetime
from fastapi import HTTPException

from services.implementation.api_key_authentication_service import APIKeyAuthenticationService
from models.api_key_model import APIKeyModel


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
def authentication_service(mock_repository):
    root_key = "root-admin-key"
    return APIKeyAuthenticationService(root_key, mock_repository)


@pytest.mark.asyncio
async def test_authenticate_root_key(authentication_service):
    root_key = "root-admin-key"
    result = await authentication_service.authenticate_api_key(root_key)
    
    assert isinstance(result, APIKeyModel)
    assert result.id == "root"
    assert result.role == "root"
    assert result.user_id == "root"


@pytest.mark.asyncio
async def test_authenticate_api_key_missing_key(authentication_service):
    with pytest.raises(HTTPException) as exc_info:
        await authentication_service.authenticate_api_key(None)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "API key is missing"


@pytest.mark.asyncio
async def test_authenticate_api_key_too_short(authentication_service):
    with pytest.raises(HTTPException) as exc_info:
        await authentication_service.authenticate_api_key("short")
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid API key"


@pytest.mark.asyncio
async def test_authenticate_api_key_no_matching_prefix(authentication_service, api_key_data):
    key_prefix = "sk_test_a"
    full_key = f"{key_prefix}bcdefg12345"
    
    # Configure mock to return empty list (no matching keys)
    authentication_service.repository.api_keys.get_api_keys_by_prefix.return_value = []
    
    with pytest.raises(HTTPException) as exc_info:
        await authentication_service.authenticate_api_key(full_key)
    
    authentication_service.repository.api_keys.get_api_keys_by_prefix.assert_called_once_with(key_prefix)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid API key"


@pytest.mark.asyncio
async def test_authenticate_api_key_successful(authentication_service, api_key_data):
    key_prefix = "sk_test_a"
    full_key = f"{key_prefix}bcdefg12345"
    
    # Create a key model to return
    key_model = APIKeyModel(**api_key_data)
    
    # Configure mocks
    authentication_service.repository.api_keys.get_api_keys_by_prefix.return_value = [key_model]
    
    # Mock the PBKDF2 hash function to return the expected hash
    with patch('hashlib.pbkdf2_hmac') as mock_pbkdf2:
        mock_pbkdf2.return_value.hex.return_value = api_key_data["key_hash"]
        
        # Call the function
        result = await authentication_service.authenticate_api_key(full_key)
        
        # Verify the call
        authentication_service.repository.api_keys.get_api_keys_by_prefix.assert_called_once_with(key_prefix)
        mock_pbkdf2.assert_called_once_with(
            'sha256', 
            full_key.encode(), 
            api_key_data["key_salt"].encode(), 
            authentication_service.PBKDF2_ITERATIONS
        )
        
        assert isinstance(result, APIKeyModel)
        assert result.id == api_key_data["id"]
        assert result.role == api_key_data["role"]
        assert result.user_id == api_key_data["user_id"]


@pytest.mark.asyncio
async def test_authenticate_api_key_hash_mismatch(authentication_service, api_key_data):
    key_prefix = "sk_test_a"
    full_key = f"{key_prefix}bcdefg12345"
    
    # Create a key model to return
    key_model = APIKeyModel(**api_key_data)
    
    # Configure mocks
    authentication_service.repository.api_keys.get_api_keys_by_prefix.return_value = [key_model]
    
    # Mock the PBKDF2 hash function to return a DIFFERENT hash
    with patch('hashlib.pbkdf2_hmac') as mock_pbkdf2:
        mock_pbkdf2.return_value.hex.return_value = "wrong_hash_value"
        
        # Call the function
        with pytest.raises(HTTPException) as exc_info:
            await authentication_service.authenticate_api_key(full_key)
        
        # Verify the call
        authentication_service.repository.api_keys.get_api_keys_by_prefix.assert_called_once_with(key_prefix)
        mock_pbkdf2.assert_called_once()
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid API key"