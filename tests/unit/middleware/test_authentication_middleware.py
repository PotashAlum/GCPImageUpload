import pytest
from fastapi import Request, Response, HTTPException
from starlette.datastructures import Headers
from unittest.mock import AsyncMock, MagicMock, patch

from middleware.authentication_middleware import AuthenticationMiddleware
from models.api_key_model import APIKeyModel


@pytest.fixture
def mock_api_key_authentication_service():
    service = AsyncMock()
    return service


@pytest.fixture
def authentication_middleware(mock_api_key_authentication_service):
    app = AsyncMock()
    return AuthenticationMiddleware(app, mock_api_key_authentication_service)


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.headers = {"x-api-key": "test-api-key"}
    request.state = MagicMock()
    request.method = "GET"
    request.url = MagicMock()
    request.url.path = "/teams/123"
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
        created_at="2023-01-01T00:00:00Z"
    )


@pytest.mark.asyncio
async def test_authentication_middleware_success(authentication_middleware, mock_request, api_key_info):
    # Mock the authenticate_api_key method
    authentication_middleware.api_key_authentication_service.authenticate_api_key.return_value = api_key_info
    
    # Mock the call_next function
    mock_response = Response(content="Test response")
    authentication_middleware.app.return_value = mock_response
    
    # Call the middleware
    response = await authentication_middleware.dispatch(mock_request, authentication_middleware.app)
    
    # Verify that authenticate_api_key was called with the correct key
    authentication_middleware.api_key_authentication_service.authenticate_api_key.assert_called_once_with("test-api-key")
    
    # Verify that the authenticated user info was stored in request.state
    assert mock_request.state.api_key_info == api_key_info
    
    # Verify that call_next was called with the request
    authentication_middleware.app.assert_called_once_with(mock_request)
    
    # Verify that the response was returned
    assert response == mock_response


@pytest.mark.asyncio
async def test_authentication_middleware_missing_api_key(authentication_middleware, mock_request):
    # Remove the API key from the request
    mock_request.headers = {}
    
    # Call the middleware
    response = await authentication_middleware.dispatch(mock_request, AsyncMock())
    
    # Verify that authenticate_api_key was not called
    authentication_middleware.api_key_authentication_service.authenticate_api_key.assert_not_called()
    
    # Verify the app function was not called
    authentication_middleware.app.assert_not_called()
    
    # Verify that a 401 response was returned
    assert response.status_code == 401
    assert "API key is missing" in response.body.decode()


@pytest.mark.asyncio
async def test_authentication_middleware_invalid_api_key(authentication_middleware, mock_request):
    # Mock authenticate_api_key to raise an HTTPException
    error = HTTPException(status_code=401, detail="Invalid API key")
    authentication_middleware.api_key_authentication_service.authenticate_api_key.side_effect = error
    
    # Call the middleware
    response = await authentication_middleware.dispatch(mock_request, AsyncMock())
    
    # Verify that authenticate_api_key was called
    authentication_middleware.api_key_authentication_service.authenticate_api_key.assert_called_once_with("test-api-key")
    
    # Verify the app function was not called
    authentication_middleware.app.assert_not_called()
    
    # Verify that a 401 response was returned
    assert response.status_code == 401
    assert "Invalid API key" in response.body.decode()