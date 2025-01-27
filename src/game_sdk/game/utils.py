"""
Utility functions for the GAME SDK.

This module provides core utility functions for interacting with the GAME API,
including authentication, agent creation, and worker management.

The module handles:
- API authentication and token management
- HTTP request handling with proper error handling
- Agent and worker creation
- Response parsing and validation

Example:
    # Create an agent
    agent_id = create_agent(
        base_url="https://api.virtuals.io",
        api_key="your_api_key",
        name="My Agent",
        description="A helpful agent",
        goal="To assist users"
    )
"""

import json
import requests
from typing import Dict, Any, Optional, List
from requests.exceptions import ConnectionError, Timeout, JSONDecodeError
from game_sdk.game.exceptions import APIError, AuthenticationError, ValidationError


def post(
    base_url: str,
    api_key: str,
    endpoint: str,
    data: Dict[str, Any] = None,
    params: Dict[str, Any] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """Make a POST request to the GAME API.

    This function handles all POST requests to the API, including proper
    error handling, response validation, and authentication.

    Args:
        base_url (str): Base URL for the API
        api_key (str): API key for authentication
        endpoint (str): API endpoint to call
        data (Dict[str, Any], optional): Request payload
        params (Dict[str, Any], optional): URL parameters
        timeout (int, optional): Request timeout in seconds. Defaults to 30.

    Returns:
        Dict[str, Any]: Parsed response data from the API

    Raises:
        AuthenticationError: If API key is invalid
        ValidationError: If request data is invalid
        APIError: For other API-related errors including network issues
        
    Example:
        response = post(
            base_url="https://api.virtuals.io",
            api_key="your_api_key",
            endpoint="/v2/agents",
            data={"name": "My Agent"}
        )
    """
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=data,
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout
        )

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 400:
            raise ValidationError(response.json().get("error", {}).get("message", "Invalid request"))
        elif response.status_code == 429:
            raise APIError("Rate limit exceeded", status_code=429)
        elif response.status_code >= 500:
            raise APIError("Server error", status_code=response.status_code)

        try:
            if response.text:
                return response.json().get("data", {})
            return {}
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response")

    except requests.exceptions.ConnectionError as e:
        raise APIError(f"Connection failed: {str(e)}")
    except requests.exceptions.Timeout as e:
        raise APIError(f"Connection timeout: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise APIError(f"Request failed: {str(e)}")


def create_agent(
    base_url: str,
    api_key: str,
    name: str,
    description: str,
    goal: str
) -> str:
    """Create a new agent instance.

    This function creates a new agent with the specified parameters.
    An agent can be either a standalone agent or one with a task generator.

    Args:
        base_url (str): Base URL for the API
        api_key (str): API key for authentication
        name (str): Name of the agent
        description (str): Description of the agent's capabilities
        goal (str): The agent's primary goal or purpose

    Returns:
        str: ID of the created agent

    Raises:
        ValidationError: If name is empty or invalid
        APIError: If agent creation fails
        AuthenticationError: If API key is invalid

    Example:
        agent_id = create_agent(
            base_url="https://api.virtuals.io",
            api_key="your_api_key",
            name="Support Agent",
            description="Helps users with support requests",
            goal="To provide excellent customer support"
        )
    """
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Name cannot be empty")

    create_agent_response = post(
        base_url,
        api_key,
        endpoint="/v2/agents",
        data={
            "name": name,
            "description": description,
            "goal": goal,
        }
    )

    agent_id = create_agent_response.get("id")
    if not agent_id:
        raise APIError("Failed to create agent: missing id in response")

    return agent_id


def create_workers(
    base_url: str,
    api_key: str,
    workers: List[Any]
) -> str:
    """Create worker instances for an agent.

    This function creates one or more workers that can be assigned tasks
    by the agent. Each worker has its own description and action space.

    Args:
        base_url (str): Base URL for the API
        api_key (str): API key for authentication
        workers (List[Any]): List of worker configurations

    Returns:
        str: ID of the created worker map

    Raises:
        APIError: If worker creation fails
        ValidationError: If worker configuration is invalid
        AuthenticationError: If API key is invalid

    Example:
        worker_map_id = create_workers(
            base_url="https://api.virtuals.io",
            api_key="your_api_key",
            workers=[worker_config1, worker_config2]
        )
    """
    worker_configs = []
    for worker in workers:
        worker_configs.append({
            "id": worker.id,
            "description": worker.worker_description,
            "instruction": worker.instruction,
            "action_space": [f.get_function_def() for f in worker.action_space]
        })

    create_worker_response = post(
        base_url,
        api_key,
        endpoint="/v2/workers",
        data={"workers": worker_configs}
    )

    map_id = create_worker_response.get("id")
    if not map_id:
        raise APIError("Failed to create worker: missing id in response")

    return map_id
