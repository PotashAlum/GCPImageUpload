import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from repository.implementation.mongodb.team_repository import MongoDBTeamRepository
from models import TeamModel


@pytest.fixture
def team_data():
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Team",
        "description": "Test Description",
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
    
    return db


@pytest.fixture
def team_repository(mock_db):
    return MongoDBTeamRepository(mock_db)


@pytest.mark.asyncio
async def test_setup_indexes(team_repository):
    await team_repository.setup_indexes()
    team_repository.db.create_index.assert_any_call("id", unique=True)
    team_repository.db.create_index.assert_any_call("name", unique=True)
    assert team_repository.db.create_index.call_count == 2


@pytest.mark.asyncio
async def test_create_team(team_repository, team_data):
    await team_repository.create_team(team_data)
    team_repository.db.insert_one.assert_called_once_with(team_data)
    

@pytest.mark.asyncio
async def test_get_team_by_id(team_repository, team_data):
    team_repository.db.find_one.return_value = team_data
    result = await team_repository.get_team_by_id(team_data["id"])
    
    team_repository.db.find_one.assert_called_once_with({"id": team_data["id"]})
    assert isinstance(result, TeamModel)
    assert result.id == team_data["id"]
    assert result.name == team_data["name"]
    assert result.description == team_data["description"]


@pytest.mark.asyncio
async def test_get_team_by_id_not_found(team_repository):
    team_repository.db.find_one.return_value = None
    result = await team_repository.get_team_by_id("non_existent_id")
    
    team_repository.db.find_one.assert_called_once_with({"id": "non_existent_id"})
    assert result is None


@pytest.mark.asyncio
async def test_get_team_by_name(team_repository, team_data):
    team_repository.db.find_one.return_value = team_data
    result = await team_repository.get_team_by_name(team_data["name"])
    
    team_repository.db.find_one.assert_called_once_with({"name": team_data["name"]})
    assert isinstance(result, TeamModel)
    assert result.name == team_data["name"]


@pytest.mark.asyncio
async def test_get_teams(team_repository, team_data):
    mock_teams = [team_data, {**team_data, "id": str(uuid.uuid4()), "name": "Another Team"}]
    
    # Create properly chained mocks
    cursor_mock = AsyncMock()
    skip_mock = AsyncMock()
    limit_mock = AsyncMock()
    
    limit_mock.to_list.return_value = mock_teams
    skip_mock.limit.return_value = limit_mock
    cursor_mock.skip.return_value = skip_mock
    
    team_repository.db.find.return_value = cursor_mock
    
    results = await team_repository.get_teams(0, 10)
    
    team_repository.db.find.assert_called_once()
    assert len(results) == 2
    assert all(isinstance(result, TeamModel) for result in results)


@pytest.mark.asyncio
async def test_delete_team(team_repository, team_data):
    await team_repository.delete_team(team_data["id"])
    team_repository.db.delete_one.assert_called_once_with({"id": team_data["id"]})