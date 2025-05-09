import pytest
from fastapi import Request, Response, HTTPException
from unittest.mock import AsyncMock, MagicMock, patch

from middleware.authorization_middleware import AuthorizationMiddleware
from models.api_key_model import APIKeyModel


@pytest.fixture
def mock_authorization_service():
    service = AsyncMock()
    service.extract_path_parameters = MagicMock()
    return service


@pytest.fixture
def authorization_middleware(mock_authorization_service):
    app = AsyncMock()
    return AuthorizationMiddleware(app, mock_authorization_service)


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    request.method = "GET"
    request.url = MagicMock()
    request.url.path = "/teams/123/images"
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
async def test_authorization_middleware_options_request(authorization_middleware, mock_request):
    # Set request method to OPTIONS (CORS preflight)
    mock_request.method = "OPTIONS"
    
    # Mock response
    mock_response = Response(content="Test response")
    authorization_middleware.app.return_value = mock_response
    
    # Call the middleware
    response = await authorization_middleware.dispatch(mock_request, authorization_middleware.app)
    
    # Verify that authorize_request was not called
    authorization_middleware.authorization_service.authorize_request.assert_not_called()
    
    # Verify that call_next was called with the request
    authorization_middleware.app.assert_called_once_with(mock_request)
    
    # Verify that the response was returned
    assert response == mock_response


@pytest.mark.asyncio
async def test_authorization_middleware_success(authorization_middleware, mock_request, api_key_info):
    # Set the API key info in the request state
    mock_request.state.api_key_info = api_key_info
    
    # Mock path parameters
    path_params = {"team_id": "123"}
    authorization_middleware.authorization_service.extract_path_parameters.return_value = path_params
    
    # Mock authorize_request to return True
    authorization_middleware.authorization_service.authorize_request.return_value = True
    
    # Mock response
    mock_response = Response(content="Test response")
    authorization_middleware.app.return_value = mock_response
    
    # Call the middleware
    response = await authorization_middleware.dispatch(mock_request, authorization_middleware.app)
    
    # Verify that extract_path_parameters was called
    authorization_middleware.authorization_service.extract_path_parameters.assert_called_once_with("teams/123/images")
    
    # Verify that authorize_request was called
    authorization_middleware.authorization_service.authorize_request.assert_called_once_with(
        "GET", "teams/123/images", api_key_info, path_params
    )
    
    # Verify that call_next was called with the request
    authorization_middleware.app.assert_called_once_with(mock_request)
    
    # Verify that the response was returned
    assert response == mock_response


@pytest.mark.asyncio
async def test_authorization_middleware_missing_api_key_info(authorization_middleware, mock_request):
    # Don't set the API key info in the request state
    mock_request.state.api_key_info = None
    
    # Call the middleware
    response = await authorization_middleware.dispatch(mock_request, AsyncMock())
    
    # Verify that authorize_request was not called
    authorization_middleware.authorization_service.authorize_request.assert_not_called()
    
    # Verify the app function was not called
    authorization_middleware.app.assert_not_called()
    
    # Verify that a 500 response was returned
    assert response.status_code == 500
    assert "Internal server error" in response.body.decode()


@pytest.mark.asyncio
async def test_authorization_middleware_unauthorized(authorization_middleware, mock_request, api_key_info):
    # Set the API key info in the request state
    mock_request.state.api_key_info = api_key_info
    
    # Mock path parameters
    path_params = {"team_id": "456"}  # Different team than user's
    authorization_middleware.authorization_service.extract_path_parameters.return_value = path_params
    
    # Mock authorize_request to raise an HTTPException
    error = HTTPException(status_code=403, detail="Access denied")
    authorization_middleware.authorization_service.authorize_request.side_effect = error
    
    # Call the middleware
    response = await authorization_middleware.dispatch(mock_request, AsyncMock())
    
    # Verify that authorize_request was called
    authorization_middleware.authorization_service.authorize_request.assert_called_once()
    
    # Verify the app function was not called
    authorization_middleware.app.assert_not_called()
    
    # Verify that a 403 response was returned
    assert response.status_code == 403
    assert "Access denied" in response.body.decode()


@pytest.mark.asyncio
async def test_authorization_middleware_unexpected_error(authorization_middleware, mock_request, api_key_info):
    # Set the API key info in the request state
    mock_request.state.api_key_info = api_key_info
    
    # Mock path parameters
    path_params = {"team_id": "123"}
    authorization_middleware.authorization_service.extract_path_parameters.return_value = path_params
    
    # Mock authorize_request to raise a generic exception
    authorization_middleware.authorization_service.authorize_request.side_effect = Exception("Unexpected error")
    
    # Call the middleware
    response = await authorization_middleware.dispatch(mock_request, AsyncMock())
    
    # Verify that authorize_request was called
    authorization_middleware.authorization_service.authorize_request.assert_called_once()
    
    # Verify the app function was not called
    authorization_middleware.app.assert_not_called()
    
    # Verify that a 500 response was returned
    assert response.status_code == 500
    assert "Internal server error" in response.body.decode()