import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from repository.implementation.mongodb.user_repository import MongoDBUserRepository
from models import UserModel


@pytest.fixture
def user_data():
    return {
        "id": str(uuid.uuid4()),
        "username": "testuser",
        "email": "test@example.com",
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
    db.create_index = AsyncMock()
    db.count_documents = AsyncMock()
    
    return db


@pytest.fixture
def user_repository(mock_db):
    return MongoDBUserRepository(mock_db)


@pytest.mark.asyncio
async def test_setup_indexes(user_repository):
    await user_repository.setup_indexes()
    user_repository.db.create_index.assert_any_call("id", unique=True)
    user_repository.db.create_index.assert_any_call("username", unique=True)
    user_repository.db.create_index.assert_any_call("email", unique=True)
    user_repository.db.create_index.assert_any_call("team_id")
    assert user_repository.db.create_index.call_count == 4


@pytest.mark.asyncio
async def test_create_user(user_repository, user_data):
    await user_repository.create_user(user_data)
    user_repository.db.insert_one.assert_called_once_with(user_data)


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository, user_data):
    user_repository.db.find_one.return_value = user_data
    result = await user_repository.get_user_by_id(user_data["id"])
    
    user_repository.db.find_one.assert_called_once_with({"id": user_data["id"]})
    assert isinstance(result, UserModel)
    assert result.id == user_data["id"]
    assert result.username == user_data["username"]
    assert result.email == user_data["email"]


@pytest.mark.asyncio
async def test_get_user_by_username(user_repository, user_data):
    user_repository.db.find_one.return_value = user_data
    result = await user_repository.get_user_by_username(user_data["username"])
    
    user_repository.db.find_one.assert_called_once_with({"username": user_data["username"]})
    assert isinstance(result, UserModel)
    assert result.username == user_data["username"]


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, user_data):
    user_repository.db.find_one.return_value = user_data
    result = await user_repository.get_user_by_email(user_data["email"])
    
    user_repository.db.find_one.assert_called_once_with({"email": user_data["email"]})
    assert isinstance(result, UserModel)
    assert result.email == user_data["email"]


@pytest.mark.asyncio
async def test_get_users_by_team_id(user_repository, user_data):
    team_id = user_data["team_id"]
    mock_users = [user_data, {**user_data, "id": str(uuid.uuid4()), "username": "anotheruser"}]
    
    # Create properly chained mocks
    cursor_mock = AsyncMock()
    skip_mock = AsyncMock()
    limit_mock = AsyncMock()
    
    limit_mock.to_list.return_value = mock_users
    skip_mock.limit.return_value = limit_mock
    cursor_mock.skip.return_value = skip_mock
    
    user_repository.db.find.return_value = cursor_mock
    
    results = await user_repository.get_users_by_team_id(team_id, 0, 10)
    
    user_repository.db.find.assert_called_once_with({"team_id": team_id})
    assert len(results) == 2
    assert all(isinstance(result, UserModel) for result in results)


@pytest.mark.asyncio
async def test_get_users_count_by_team_id(user_repository, user_data):
    team_id = user_data["team_id"]
    user_repository.db.count_documents.return_value = 5
    
    count = await user_repository.get_users_count_by_team_id(team_id)
    
    user_repository.db.count_documents.assert_called_once_with({"team_id": team_id})
    assert count == 5


@pytest.mark.asyncio
async def test_delete_user(user_repository, user_data):
    await user_repository.delete_user(user_data["id"])
    user_repository.db.delete_one.assert_called_once_with({"id": user_data["id"]})