# Error Handling Guide

This guide helps you handle errors effectively when using the GAME SDK. We'll cover common error scenarios, how to handle them, and best practices for error management.

## Quick Reference

```python
from game_sdk.game.exceptions import (
    APIError,
    AuthenticationError,
    ValidationError
)

try:
    agent = Agent(
        api_key="your_api_key",
        name="Test Agent",
        agent_description="A test agent",
        agent_goal="Testing error handling",
        get_agent_state_fn=lambda x, y: {"status": "ready"}
    )
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except ValidationError as e:
    print(f"Invalid input: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Common Error Types

### AuthenticationError
Raised when there are issues with authentication.

```python
try:
    token = get_access_token(api_key)
except AuthenticationError as e:
    if e.status_code == 401:
        print("Invalid API key")
    elif e.status_code == 403:
        print("API key lacks necessary permissions")
```

Common causes:
- Invalid API key
- Expired API key
- Missing API key
- Insufficient permissions

### ValidationError
Raised when input data is invalid.

```python
try:
    agent = Agent(
        api_key=api_key,
        name="",  # Empty name will raise ValidationError
        agent_description="Description",
        agent_goal="Goal",
        get_agent_state_fn=lambda x, y: {"status": "ready"}
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
```

Common causes:
- Missing required fields
- Invalid data types
- Empty required strings
- Malformed data structures

### APIError
Raised for general API communication issues.

```python
try:
    response = post(base_url, api_key, "agents", data)
except APIError as e:
    if e.status_code == 404:
        print("Resource not found")
    elif e.status_code == 429:
        print("Rate limit exceeded")
    elif e.status_code >= 500:
        print("Server error - try again later")
```

Common causes:
- Network connectivity issues
- Rate limiting
- Server errors
- Invalid endpoints
- Malformed requests

## Best Practices

### 1. Use Specific Exception Handling
```python
# Good 
try:
    agent.create_worker(worker_config)
except AuthenticationError:
    # Handle auth issues
except ValidationError:
    # Handle validation issues
except APIError:
    # Handle API issues

# Avoid 
try:
    agent.create_worker(worker_config)
except Exception:  # Too broad
    pass
```

### 2. Log Error Details
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    agent.create_worker(worker_config)
except APIError as e:
    logger.error(f"Failed to create worker: {e}", exc_info=True)
    logger.debug(f"Request details: {e.response_json}")
```

### 3. Implement Retries for Transient Errors
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def create_agent_with_retry(api_key, name, description, goal):
    try:
        return Agent(
            api_key=api_key,
            name=name,
            agent_description=description,
            agent_goal=goal,
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )
    except APIError as e:
        if e.status_code >= 500:  # Only retry on server errors
            raise
        else:
            raise e from None
```

### 4. Provide Context in Error Messages
```python
def create_worker(self, config):
    if not config.get('id'):
        raise ValidationError(
            "Worker ID is required. "
            "Please provide a unique identifier for the worker."
        )
    # ... rest of the function
```

## Specific Error Scenarios

### Network and Connectivity Issues

```python
from requests.exceptions import RequestException, Timeout, ConnectionError

try:
    agent.create_worker(config)
except ConnectionError:
    logger.error("Unable to connect to the API. Check your internet connection.")
except Timeout:
    logger.error("Request timed out. The API is taking too long to respond.")
except RequestException as e:
    logger.error(f"Network error: {e}")
```

### Rate Limiting and Throttling

```python
from time import sleep

def handle_rate_limits(func):
    def wrapper(*args, **kwargs):
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if e.status_code == 429:  # Too Many Requests
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited. Waiting {delay} seconds...")
                        sleep(delay)
                        continue
                raise
    return wrapper

@handle_rate_limits
def create_multiple_agents(configs):
    return [Agent(**config) for config in configs]
```

### Invalid Configuration

```python
def validate_agent_config(config):
    errors = []
    
    # Check required fields
    required_fields = ['name', 'agent_description', 'agent_goal']
    for field in required_fields:
        if not config.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate field lengths
    if len(config.get('name', '')) > 100:
        errors.append("Agent name must be less than 100 characters")
    
    # Check for invalid characters
    import re
    if not re.match(r'^[a-zA-Z0-9\s-_]+$', config.get('name', '')):
        errors.append("Agent name contains invalid characters")
    
    if errors:
        raise ValidationError("\n".join(errors))
```

### API Version Mismatches

```python
def check_api_compatibility():
    try:
        response = requests.get(f"{config.api_url}/version")
        api_version = response.json().get('version')
        sdk_version = game_sdk.__version__
        
        if not is_compatible_version(api_version, sdk_version):
            logger.warning(
                f"API version {api_version} may be incompatible with "
                f"SDK version {sdk_version}. Please update your SDK."
            )
    except Exception as e:
        logger.error(f"Failed to check API compatibility: {e}")
```

### Worker Creation Failures

```python
def create_worker_safely(agent, worker_config):
    try:
        # Validate worker configuration
        if not worker_config.get('action_space'):
            raise ValidationError("Worker must have at least one action")
            
        # Attempt to create worker
        worker = agent.create_worker(worker_config)
        
        # Verify worker creation
        if not worker.verify_connection():
            raise APIError("Worker created but connection verification failed")
            
        return worker
        
    except ValidationError as e:
        logger.error(f"Invalid worker configuration: {e}")
        raise
    except APIError as e:
        if e.status_code == 409:  # Conflict
            logger.error("Worker with this ID already exists")
        elif e.status_code == 413:  # Payload Too Large
            logger.error("Worker configuration exceeds size limit")
        else:
            logger.error(f"Failed to create worker: {e}")
        raise
```

### State Function Errors

```python
def safe_state_function(func):
    def wrapper(function_result, current_state):
        try:
            state = func(function_result, current_state)
            if not isinstance(state, dict):
                raise ValidationError("State must be a dictionary")
            return state
        except Exception as e:
            logger.error(f"State function failed: {e}")
            # Return a safe default state
            return {"status": "error", "error": str(e)}
    return wrapper

@safe_state_function
def get_agent_state(function_result, current_state):
    # Your state function logic here
    return {"status": "ready", "data": process_state(current_state)}
```

### Plugin Integration Errors

```python
def load_plugin_safely(plugin_name, config):
    try:
        # Attempt to import plugin
        plugin_module = importlib.import_module(f"game_sdk.plugins.{plugin_name}")
        
        # Validate plugin interface
        required_methods = ['initialize', 'execute', 'cleanup']
        for method in required_methods:
            if not hasattr(plugin_module, method):
                raise ValidationError(f"Plugin missing required method: {method}")
        
        # Initialize plugin
        plugin = plugin_module.initialize(config)
        
        return plugin
    except ImportError:
        logger.error(f"Plugin '{plugin_name}' not found")
        raise
    except Exception as e:
        logger.error(f"Failed to load plugin '{plugin_name}': {e}")
        raise
```

## Error Response Format

When an error occurs, the response will contain:

```python
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {
            # Additional error context
        }
    }
}
```

Example error handling:
```python
try:
    response = agent.create_worker(config)
except APIError as e:
    error = e.response_json.get('error', {})
    error_code = error.get('code')
    error_message = error.get('message')
    error_details = error.get('details', {})
    
    logger.error(f"Error {error_code}: {error_message}")
    logger.debug(f"Error details: {error_details}")
```

## Common Error Codes

| Code | Description | Recommended Action |
|------|-------------|-------------------|
| `AUTH_001` | Invalid API key | Verify your API key is correct |
| `AUTH_002` | Expired API key | Request a new API key |
| `VAL_001` | Missing required field | Check required fields in documentation |
| `VAL_002` | Invalid data format | Verify data matches expected format |
| `API_001` | Rate limit exceeded | Implement rate limiting or backoff |
| `API_002` | Server error | Retry with exponential backoff |

## Debugging Tips

1. Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. Use the test environment:
```python
from game_sdk.game.config import config
config.set("environment", "test")
```

3. Check response details:
```python
except APIError as e:
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response_json}")
    print(f"Headers: {e.response_headers}")
```

## Getting Help

If you encounter an error you can't resolve:

1. Check the [GitHub Issues](https://github.com/game-by-virtuals/game-python/issues)
2. Join our [Discord Community](https://discord.gg/virtuals)
3. Contact support at support@virtuals.io
