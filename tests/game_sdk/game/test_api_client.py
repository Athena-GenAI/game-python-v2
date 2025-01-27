"""Tests for the GameAPIClient class."""

import pytest
import requests
from game_sdk.game.api_client import GameAPIClient
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError
from game_sdk.game.custom_types import ActionResponse, Function, FunctionResult, FunctionResultStatus


@pytest.fixture
def api_client():
    """Create a GameAPIClient instance for testing."""
    return GameAPIClient("test-api-key")


@pytest.fixture
def mock_functions():
    """Create a list of test functions."""
    return [
        Function(name="test_fn", description="Test function", fn=lambda: None),
        Function(name="another_fn", description="Another test function", fn=lambda: None)
    ]


def test_init_with_valid_api_key():
    """Test GameAPIClient initialization with valid API key."""
    client = GameAPIClient("test-api-key")
    assert client.api_key == "test-api-key"
    assert client.base_url == "https://api.virtuals.io"
    assert client.session.headers["Authorization"] == "Bearer test-api-key"
    assert client.session.headers["Content-Type"] == "application/json"


def test_init_with_invalid_api_key():
    """Test GameAPIClient initialization with invalid API key."""
    with pytest.raises(ValueError, match="API key is required"):
        GameAPIClient("")


def test_set_worker_task_success(api_client, requests_mock):
    """Test successful task setting."""
    submission_id = "test-submission-123"
    requests_mock.post(
        f"{api_client.base_url}/v2/tasks",
        json={"data": {"submissionId": submission_id}}
    )

    result = api_client.set_worker_task(
        description="Test worker",
        instruction="Test instruction",
        task="Test task"
    )

    assert result == submission_id
    assert requests_mock.last_request.json() == {
        "description": "Test worker",
        "instruction": "Test instruction",
        "task": "Test task"
    }


def test_set_worker_task_auth_error(api_client, requests_mock):
    """Test authentication error during task setting."""
    requests_mock.post(
        f"{api_client.base_url}/v2/tasks",
        status_code=401,
        json={"error": {"message": "Invalid API key"}}
    )

    with pytest.raises(AuthenticationError):
        api_client.set_worker_task(
            description="Test worker",
            instruction="Test instruction",
            task="Test task"
        )


def test_get_worker_action_success(api_client, requests_mock, mock_functions):
    """Test successful action retrieval."""
    action_data = {
        "action": {
            "action_type": "FUNCTION",
            "function_name": "test_fn",
            "parameters": {"param1": "value1"}
        }
    }
    requests_mock.post(
        f"{api_client.base_url}/v2/actions",
        json={"data": action_data}
    )

    result = api_client.get_worker_action(
        description="Test worker",
        instruction="Test instruction",
        state={"test": "state"},
        functions=mock_functions
    )

    assert isinstance(result, ActionResponse)
    assert result.action_type == "FUNCTION"
    assert result.function_name == "test_fn"
    assert result.parameters == {"param1": "value1"}

    # Verify request payload
    assert requests_mock.last_request.json() == {
        "description": "Test worker",
        "instruction": "Test instruction",
        "state": {"test": "state"},
        "functions": [f.toJson() for f in mock_functions]
    }


def test_get_worker_action_with_function_result(api_client, requests_mock, mock_functions):
    """Test action retrieval with previous function result."""
    requests_mock.post(
        f"{api_client.base_url}/v2/actions",
        json={"data": {"action": {}}}
    )

    function_result = FunctionResult(
        function_name="test_fn",
        status=FunctionResultStatus.SUCCESS,
        result={"test": "result"}
    )

    api_client.get_worker_action(
        description="Test worker",
        instruction="Test instruction",
        state={"test": "state"},
        functions=mock_functions,
        function_result=function_result
    )

    # Verify function result was included in request
    request_data = requests_mock.last_request.json()
    assert "functionResult" in request_data
    assert request_data["functionResult"]["function_name"] == "test_fn"
    assert request_data["functionResult"]["status"] == "SUCCESS"
    assert request_data["functionResult"]["result"] == {"test": "result"}


def test_request_retry_on_server_error(api_client, requests_mock):
    """Test request retry behavior on server error."""
    # Mock 2 failed attempts and 1 success
    requests_mock.post(
        f"{api_client.base_url}/v2/tasks",
        [
            {"status_code": 500, "json": {"error": {"message": "Server error"}}},
            {"status_code": 500, "json": {"error": {"message": "Server error"}}},
            {"json": {"data": {"submissionId": "test-123"}}}
        ]
    )

    result = api_client.set_worker_task(
        description="Test worker",
        instruction="Test instruction",
        task="Test task"
    )

    assert result == "test-123"
    assert requests_mock.call_count == 3


def test_request_validation_error(api_client, requests_mock):
    """Test handling of validation errors."""
    requests_mock.post(
        f"{api_client.base_url}/v2/tasks",
        status_code=400,
        json={"error": {"message": "Invalid request data"}}
    )

    with pytest.raises(ValidationError):
        api_client.set_worker_task(
            description="Test worker",
            instruction="Test instruction",
            task="Test task"
        )


def test_request_rate_limit(api_client, requests_mock):
    """Test handling of rate limit errors."""
    requests_mock.post(
        f"{api_client.base_url}/v2/tasks",
        status_code=429,
        json={"error": {"message": "Rate limit exceeded"}}
    )

    with pytest.raises(APIError):
        api_client.set_worker_task(
            description="Test worker",
            instruction="Test instruction",
            task="Test task"
        )


def test_request_timeout(api_client, requests_mock):
    """Test handling of request timeouts."""
    requests_mock.post(
        f"{api_client.base_url}/v2/tasks",
        exc=requests.exceptions.Timeout
    )

    with pytest.raises(APIError):
        api_client.set_worker_task(
            description="Test worker",
            instruction="Test instruction",
            task="Test task"
        )
