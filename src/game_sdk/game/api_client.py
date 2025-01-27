"""
API client module for the GAME SDK.

This module provides a dedicated API client for making requests to the GAME API,
handling authentication, errors, and response parsing consistently.
"""

import requests
from typing import Dict, Any, Optional
from game_sdk.game.config import config
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError
from game_sdk.game.custom_types import ActionResponse, FunctionResult
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class GameAPIClient:
    """Client for interacting with the GAME API.

    This class handles all API communication, including authentication,
    request retries, and error handling.

    Attributes:
        api_key (str): API key for authentication
        base_url (str): Base URL for API requests
        session (requests.Session): Reusable session for API requests
    """

    def __init__(self, api_key: str):
        """Initialize the API client.

        Args:
            api_key (str): API key for authentication

        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = config.api_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(APIError)
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request with automatic retries.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            data (Optional[Dict[str, Any]]): Request payload
            params (Optional[Dict[str, Any]]): Query parameters

        Returns:
            Dict[str, Any]: Parsed response data

        Raises:
            AuthenticationError: If API key is invalid
            ValidationError: If request data is invalid
            APIError: For other API-related errors
        """
        try:
            response = self.session.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                json=data,
                params=params,
                timeout=30
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 400:
                raise ValidationError(response.json().get("error", {}).get("message", "Invalid request"))
            elif response.status_code == 429:
                raise APIError("Rate limit exceeded", status_code=429)
            elif response.status_code >= 500:
                raise APIError("Server error", status_code=response.status_code)

            return response.json().get("data", {})

        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def set_worker_task(self, description: str, instruction: str, task: str) -> str:
        """Set a task for a worker.

        Args:
            description (str): Worker description
            instruction (str): Worker instructions
            task (str): Task to assign

        Returns:
            str: Task submission ID
        """
        data = {
            "description": description,
            "instruction": instruction,
            "task": task
        }
        response = self._request("POST", "/v2/tasks", data=data)
        return response.get("submissionId")

    def get_worker_action(
        self,
        description: str,
        instruction: str,
        state: Dict[str, Any],
        functions: list,
        task: Optional[str] = None,
        function_result: Optional[FunctionResult] = None
    ) -> Optional[ActionResponse]:
        """Get the next action for a worker.

        Args:
            description (str): Worker description
            instruction (str): Worker instructions
            state (Dict[str, Any]): Current worker state
            functions (list): Available functions
            task (Optional[str]): Current task
            function_result (Optional[FunctionResult]): Previous function result

        Returns:
            Optional[ActionResponse]: Next action to take
        """
        data = {
            "description": description,
            "instruction": instruction,
            "state": state,
            "functions": [f.toJson() for f in functions]
        }

        if task:
            data["task"] = task

        if function_result:
            data["functionResult"] = function_result.toJson()

        response = self._request("POST", "/v2/actions", data=data)
        
        if response and response.get("action"):
            return ActionResponse(**response["action"])
        
        return None
