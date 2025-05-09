import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from repository.implementation.mongodb.audit_log_repository import MongoDBauditLogRepository
from models import AuditLogModel


@pytest.fixture
def audit_log_data():
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "team_id": str(uuid.uuid4()),
        "action": "GET",
        "resource_type": "image",
        "resource_id": str(uuid.uuid4()),
        "status": "success",
        "status_code": 200,
        "ip_address": "127.0.0.1",
        "user_agent": "test-agent",
        "details": {"path": "/teams/123/images/456"},
        "timestamp": datetime.now()
    }


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.insert_one = AsyncMock()
    db.find = AsyncMock()
    db.create_index = AsyncMock()
    
    return db


@pytest.fixture
def audit_log_repository(mock_db):
    repo = MongoDBauditLogRepository(mock_db)
    # Set audit_logs_collection to mock_db for the test
    repo.audit_logs_collection = mock_db
    return repo


@pytest.mark.asyncio
async def test_setup_indexes(audit_log_repository):
    await audit_log_repository.setup_indexes()
    audit_log_repository.db.create_index.assert_called_once_with("timestamp", expireAfterSeconds=7776000)


@pytest.mark.asyncio
async def test_create_audit_log(audit_log_repository, audit_log_data):
    result = await audit_log_repository.create_audit_log(audit_log_data)
    
    audit_log_repository.db.insert_one.assert_called_once_with(audit_log_data)
    assert isinstance(result, AuditLogModel)
    assert result.id == audit_log_data["id"]
    assert result.action == audit_log_data["action"]
    assert result.status == audit_log_data["status"]


@pytest.mark.asyncio
async def test_get_audit_logs(audit_log_repository, audit_log_data):
    query = {"user_id": audit_log_data["user_id"]}
    mock_logs = [audit_log_data, {**audit_log_data, "id": str(uuid.uuid4()), "action": "POST"}]
    
    # Create a properly chained mock
    cursor_mock = AsyncMock()
    sort_mock = AsyncMock()
    skip_mock = AsyncMock()
    limit_mock = AsyncMock()
    
    limit_mock.to_list.return_value = mock_logs
    skip_mock.limit.return_value = limit_mock
    sort_mock.skip.return_value = skip_mock
    cursor_mock.sort.return_value = sort_mock
    
    audit_log_repository.audit_logs_collection.find.return_value = cursor_mock
    
    results = await audit_log_repository.get_audit_logs(query, 0, 10)
    
    audit_log_repository.audit_logs_collection.find.assert_called_once_with(query)
    assert len(results) == 2
    assert all(isinstance(result, AuditLogModel) for result in results)