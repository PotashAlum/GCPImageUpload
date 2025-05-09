import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from repository.implementation.mongodb.api_key_repository import MongoDBAPIKeyRepository
from models import APIKeyModel


@pytest.fixture
def api_key_data():
    return {
        "id": str(uuid.uuid4()),
        "name": "Test API Key",
        "key_prefix": "sk_test_",
        "key_hash": "hashed_key_value",
        "key_salt": "key_salt_value",
        "role": "user",
        "user_id": str(uuid.uuid4()),
        "team_id": str(uuid.uuid4()),
        "created_at": datetime.now()
    }


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.find_one = AsyncMock()
    db.find = AsyncMock()
    db.insert_one = AsyncMock()
    db.delete_one = AsyncMock()
    db.delete_many = AsyncMock()
    db.create_index = AsyncMock()
    
    return db


@pytest.fixture
def api_key_repository(mock_db):
    return MongoDBAPIKeyRepository(mock_db)


@pytest.mark.asyncio
async def test_setup_indexes(api_key_repository):
    await api_key_repository.setup_indexes()
    api_key_repository.db.create_index.assert_any_call("id", unique=True)
    api_key_repository.db.create_index.assert_any_call("key_prefix")
    api_key_repository.db.create_index.assert_any_call("user_id")
    api_key_repository.db.create_index.assert_any_call("team_id")
    assert api_key_repository.db.create_index.call_count == 4


@pytest.mark.asyncio
async def test_create_api_key(api_key_repository, api_key_data):
    await api_key_repository.create_api_key(api_key_data)
    api_key_repository.db.insert_one.assert_called_once_with(api_key_data)


@pytest.mark.asyncio
async def test_get_api_key_by_id(api_key_repository, api_key_data):
    api_key_repository.db.find_one.return_value = api_key_data
    result = await api_key_repository.get_api_key_by_id(api_key_data["id"])
    
    api_key_repository.db.find_one.assert_called_once_with({"id": api_key_data["id"]})
    assert isinstance(result, APIKeyModel)
    assert result.id == api_key_data["id"]
    assert result.name == api_key_data["name"]
    assert result.key_prefix == api_key_data["key_prefix"]


@pytest.mark.asyncio
async def test_get_api_keys_by_prefix(api_key_repository, api_key_data):
    prefix = api_key_data["key_prefix"]
    mock_keys = [api_key_data, {**api_key_data, "id": str(uuid.uuid4()), "name": "Another Key"}]
    
    # Create a properly chained mock
    cursor_mock = AsyncMock()
    cursor_mock.to_list.return_value = mock_keys
    api_key_repository.db.find.return_value = cursor_mock
    
    results = await api_key_repository.get_api_keys_by_prefix(prefix)
    
    api_key_repository.db.find.assert_called_once_with({"key_prefix": prefix})
    assert len(results) == 2
    assert all(isinstance(result, APIKeyModel) for result in results)


@pytest.mark.asyncio
async def test_get_api_keys_by_user_id(api_key_repository, api_key_data):
    user_id = api_key_data["user_id"]
    mock_keys = [api_key_data, {**api_key_data, "id": str(uuid.uuid4()), "name": "Another Key"}]
    
    # Create a properly chained mock
    cursor_mock = AsyncMock()
    skip_mock = AsyncMock()
    limit_mock = AsyncMock()
    
    limit_mock.to_list.return_value = mock_keys
    skip_mock.limit.return_value = limit_mock
    cursor_mock.skip.return_value = skip_mock
    
    api_key_repository.db.find.return_value = cursor_mock
    
    results = await api_key_repository.get_api_keys_by_user_id(user_id, 0, 10)
    
    api_key_repository.db.find.assert_called_once_with({"user_id": user_id})
    assert len(results) == 2
    assert all(isinstance(result, APIKeyModel) for result in results)


@pytest.mark.asyncio
async def test_delete_api_key(api_key_repository, api_key_data):
    await api_key_repository.delete_api_key(api_key_data["id"])
    api_key_repository.db.delete_one.assert_called_once_with({"id": api_key_data["id"]})


@pytest.mark.asyncio
async def test_delete_user_api_keys(api_key_repository, api_key_data):
    user_id = api_key_data["user_id"]
    await api_key_repository.delete_user_api_keys(user_id)
    api_key_repository.db.delete_many.assert_called_once_with({"user_id": user_id})