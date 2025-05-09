import pytest
import json
from fastapi import Request, Response
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from middleware.audit_middleware import AuditMiddleware
from models.api_key_model import APIKeyModel


@pytest.fixture
def mock_audit_log_service():
    service = AsyncMock()
    return service


@pytest.fixture
def audit_middleware(mock_audit_log_service):
    app = AsyncMock()
    return AuditMiddleware(app, mock_audit_log_service)


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    request.method = "GET"
    request.url = MagicMock()
    request.url.path = "/teams/123/images"
    request.client = MagicMock()
    request.client.host = "192.168.1.1"
    request.headers = {"user-agent": "test-user-agent"}
    return request


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
        created_at=datetime(2023, 1, 1)
    )


@pytest.mark.asyncio
async def test_audit_middleware_with_api_key_info(audit_middleware, mock_request, api_key_info):
    # Set the API key info in the request state
    mock_request.state.api_key_info = api_key_info
    
    # Mock response
    mock_response = Response(content="Test response", status_code=200)
    audit_middleware.app.return_value = mock_response
    
    # Use patch.object to patch the actual audit_logger instance in the middleware
    with patch('middleware.audit_middleware.audit_logger') as mock_logger:
        # Call the middleware
        response = await audit_middleware.dispatch(mock_request, audit_middleware.app)
        
        # Verify that call_next was called with the request
        audit_middleware.app.assert_called_once_with(mock_request)
        
        # Verify that create_audit_log was called
        audit_middleware.audit_log_service.create_audit_log.assert_called_once()
        
        # Get the audit log entry
        log_entry = audit_middleware.audit_log_service.create_audit_log.call_args[0][0]
        assert log_entry["user_id"] == api_key_info.user_id
        assert log_entry["team_id"] == api_key_info.team_id
        assert log_entry["action"] == "GET"
        assert log_entry["resource_type"] == "teams"
        assert log_entry["resource_id"] == "123"
        assert log_entry["status"] == "success"
        assert log_entry["status_code"] == 200
        assert log_entry["ip_address"] == "192.168.1.1"
        assert log_entry["user_agent"] == "test-user-agent"
        assert log_entry["details"]["path"] == "/teams/123/images"
        
        # Verify that the logger was called
        mock_logger.info.assert_called_once()
        
        # Verify that the response was returned
        assert response == mock_response


@pytest.mark.asyncio
async def test_audit_middleware_without_api_key_info(audit_middleware, mock_request):
    # Don't set the API key info in the request state
    mock_request.state.api_key_info = None
    
    # Mock response
    mock_response = Response(content="Test response", status_code=401)
    audit_middleware.app.return_value = mock_response
    
    # Use patch.object to patch the actual audit_logger instance in the middleware
    with patch('middleware.audit_middleware.audit_logger') as mock_logger:
        # Call the middleware
        response = await audit_middleware.dispatch(mock_request, audit_middleware.app)
        
        # Verify that call_next was called with the request
        audit_middleware.app.assert_called_once_with(mock_request)
        
        # Verify that create_audit_log was called
        audit_middleware.audit_log_service.create_audit_log.assert_called_once()
        
        # Get the audit log entry
        log_entry = audit_middleware.audit_log_service.create_audit_log.call_args[0][0]
        assert log_entry["user_id"] is None
        assert log_entry["team_id"] is None
        assert log_entry["action"] == "GET"
        assert log_entry["status"] == "failure"
        assert log_entry["status_code"] == 401
        
        # Verify that the logger was called
        mock_logger.info.assert_called_once()
        
        # Verify that the response was returned
        assert response == mock_response


@pytest.mark.asyncio
async def test_audit_middleware_with_error_response(audit_middleware, mock_request, api_key_info):
    # Set the API key info in the request state
    mock_request.state.api_key_info = api_key_info
    
    # Mock response with error status
    mock_response = Response(content="Error response", status_code=500)
    audit_middleware.app.return_value = mock_response
    
    # Use patch.object to patch the actual audit_logger instance in the middleware
    with patch('middleware.audit_middleware.audit_logger'):
        # Call the middleware
        response = await audit_middleware.dispatch(mock_request, audit_middleware.app)
        
        # Verify that create_audit_log was called
        audit_middleware.audit_log_service.create_audit_log.assert_called_once()
        
        # Get the audit log entry
        log_entry = audit_middleware.audit_log_service.create_audit_log.call_args[0][0]
        assert log_entry["status"] == "failure"
        assert log_entry["status_code"] == 500
        
        # Verify that the response was returned
        assert response == mock_response