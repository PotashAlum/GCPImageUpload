import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from repository.implementation.mongodb.image_repository import MongoDBImageRepository
from models import ImageModel


@pytest.fixture
def image_data():
    return {
        "id": str(uuid.uuid4()),
        "title": "Test Image",
        "description": "Test Description",
        "user_id": str(uuid.uuid4()),
        "team_id": str(uuid.uuid4()),
        "filename": "test_image.jpg",
        "content_type": "image/jpeg",
        "size": 1024,
        "url": "https://example.com/test_image.jpg",
        "metadata": {
            "width": 800,
            "height": 600,
            "format": "JPEG",
            "tags": ["test", "image"]
        },
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
def image_repository(mock_db):
    return MongoDBImageRepository(mock_db)


@pytest.mark.asyncio
async def test_setup_indexes(image_repository):
    await image_repository.setup_indexes()
    image_repository.db.create_index.assert_any_call("id", unique=True)
    image_repository.db.create_index.assert_any_call([("user_id", 1), ("created_at", -1)])
    image_repository.db.create_index.assert_any_call([("team_id", 1), ("created_at", -1)])
    assert image_repository.db.create_index.call_count == 3


@pytest.mark.asyncio
async def test_create_image(image_repository, image_data):
    await image_repository.create_image(image_data)
    image_repository.db.insert_one.assert_called_once_with(image_data)


@pytest.mark.asyncio
async def test_get_image_by_id(image_repository, image_data):
    image_repository.db.find_one.return_value = image_data
    result = await image_repository.get_image_by_id(image_data["id"])
    
    image_repository.db.find_one.assert_called_once_with({"id": image_data["id"]})
    assert isinstance(result, ImageModel)
    assert result.id == image_data["id"]
    assert result.title == image_data["title"]
    assert result.filename == image_data["filename"]


@pytest.mark.asyncio
async def test_get_images_by_team_id(image_repository, image_data):
    team_id = image_data["team_id"]
    mock_images = [image_data, {**image_data, "id": str(uuid.uuid4()), "title": "Another Image"}]
    
    # Create properly chained mocks
    cursor_mock = AsyncMock()
    sort_mock = AsyncMock()
    skip_mock = AsyncMock()
    limit_mock = AsyncMock()
    
    limit_mock.to_list.return_value = mock_images
    skip_mock.limit.return_value = limit_mock
    sort_mock.skip.return_value = skip_mock
    cursor_mock.sort.return_value = sort_mock
    
    image_repository.db.find.return_value = cursor_mock
    
    results = await image_repository.get_images_by_team_id(team_id, 0, 10)
    
    image_repository.db.find.assert_called_once_with({"team_id": team_id})
    assert len(results) == 2
    assert all(isinstance(result, ImageModel) for result in results)


@pytest.mark.asyncio
async def test_get_images_by_user_id(image_repository, image_data):
    user_id = image_data["user_id"]
    mock_images = [image_data, {**image_data, "id": str(uuid.uuid4()), "title": "Another Image"}]
    
    # Create properly chained mocks
    cursor_mock = AsyncMock()
    sort_mock = AsyncMock()
    skip_mock = AsyncMock()
    limit_mock = AsyncMock()
    
    limit_mock.to_list.return_value = mock_images
    skip_mock.limit.return_value = limit_mock
    sort_mock.skip.return_value = skip_mock
    cursor_mock.sort.return_value = sort_mock
    
    image_repository.db.find.return_value = cursor_mock
    
    results = await image_repository.get_images_by_user_id(user_id, 0, 10)
    
    image_repository.db.find.assert_called_once_with({"user_id": user_id})
    assert len(results) == 2
    assert all(isinstance(result, ImageModel) for result in results)


@pytest.mark.asyncio
async def test_delete_image(image_repository, image_data):
    await image_repository.delete_image(image_data["id"])
    image_repository.db.delete_one.assert_called_once_with({"id": image_data["id"]})


@pytest.mark.asyncio
async def test_delete_images_by_team_id(image_repository, image_data):
    team_id = image_data["team_id"]
    await image_repository.delete_images_by_team_id(team_id)
    image_repository.db.delete_many.assert_called_once_with({"team_id": team_id})