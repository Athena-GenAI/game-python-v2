# Worker Creation and Testing Guide

This guide walks you through the process of creating and testing workers in the GAME SDK. Workers are essential components that execute actions and maintain state for your agents.

## Quick Start

```python
from game_sdk.game.agent import Agent
from game_sdk.game.exceptions import ValidationError, APIError

# Create an agent first
agent = Agent(
    api_key="your_api_key",
    name="Test Agent",
    agent_description="Testing worker creation",
    agent_goal="Create and test workers",
    get_agent_state_fn=lambda x, y: {"status": "ready"}
)

# Define worker configuration
worker_config = {
    "id": "test_worker_1",
    "description": "A test worker",
    "instruction": "Execute test actions",
    "action_space": [
        {
            "name": "greet",
            "description": "Send a greeting",
            "parameters": {
                "message": {"type": "string", "description": "Greeting message"}
            }
        }
    ]
}

# Create the worker
worker = agent.create_worker(worker_config)
```

## Worker Configuration

### Required Fields

- `id`: Unique identifier for the worker
- `description`: Brief description of the worker's purpose
- `instruction`: Detailed instructions for the worker
- `action_space`: List of actions the worker can perform

### Action Space Definition

Each action in the action space must have:
- `name`: Action identifier
- `description`: What the action does
- `parameters`: Input parameters for the action (optional)

Example action with parameters:
```python
{
    "name": "send_message",
    "description": "Send a message to a channel",
    "parameters": {
        "channel": {
            "type": "string",
            "description": "Target channel",
            "enum": ["general", "random", "support"]
        },
        "message": {
            "type": "string",
            "description": "Message content",
            "maxLength": 1000
        },
        "priority": {
            "type": "integer",
            "description": "Message priority (1-5)",
            "minimum": 1,
            "maximum": 5
        }
    }
}
```

## Testing Your Worker

### 1. Basic Connectivity Test

```python
def test_worker_connection(worker):
    """Test if the worker is properly connected."""
    try:
        status = worker.get_status()
        assert status["connected"], "Worker is not connected"
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
```

### 2. Action Space Validation

```python
def validate_action_space(worker):
    """Validate worker's action space configuration."""
    try:
        actions = worker.get_actions()
        for action in actions:
            # Check required fields
            assert "name" in action, "Action missing name"
            assert "description" in action, "Action missing description"
            
            # Validate parameters if present
            if "parameters" in action:
                for param_name, param_config in action["parameters"].items():
                    assert "type" in param_config, f"Parameter {param_name} missing type"
                    assert "description" in param_config, f"Parameter {param_name} missing description"
        return True
    except AssertionError as e:
        print(f"Action space validation failed: {e}")
        return False
```

### 3. Test Action Execution

```python
def test_action_execution(worker, action_name, parameters):
    """Test executing a specific action."""
    try:
        result = worker.execute_action(action_name, parameters)
        return result
    except Exception as e:
        print(f"Action execution failed: {e}")
        return None
```

### Complete Testing Script

Here's a complete script to test your worker:

```python
def test_worker(api_key: str, worker_config: dict):
    """
    Comprehensive worker testing function.
    
    Args:
        api_key: Your API key
        worker_config: Worker configuration dictionary
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        # 1. Create agent
        agent = Agent(
            api_key=api_key,
            name="Test Agent",
            agent_description="Testing worker",
            agent_goal="Validate worker functionality",
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )
        
        # 2. Create worker
        worker = agent.create_worker(worker_config)
        print("✓ Worker created successfully")
        
        # 3. Test connection
        if not test_worker_connection(worker):
            return False
        print("✓ Worker connection verified")
        
        # 4. Validate action space
        if not validate_action_space(worker):
            return False
        print("✓ Action space validated")
        
        # 5. Test each action
        for action in worker_config["action_space"]:
            # Create test parameters based on action definition
            test_params = {}
            if "parameters" in action:
                for param_name, param_config in action["parameters"].items():
                    # Generate test value based on parameter type
                    if param_config["type"] == "string":
                        test_params[param_name] = "test_value"
                    elif param_config["type"] == "integer":
                        test_params[param_name] = param_config.get("minimum", 1)
                    # Add more type handling as needed
            
            result = test_action_execution(worker, action["name"], test_params)
            if result is None:
                print(f"✗ Action {action['name']} test failed")
                return False
            print(f"✓ Action {action['name']} tested successfully")
        
        return True
        
    except Exception as e:
        print(f"Worker testing failed: {e}")
        return False

# Example usage
if __name__ == "__main__":
    api_key = "your_api_key"
    worker_config = {
        "id": "test_worker",
        "description": "Test worker",
        "instruction": "Execute test actions",
        "action_space": [
            {
                "name": "greet",
                "description": "Send a greeting",
                "parameters": {
                    "message": {
                        "type": "string",
                        "description": "Greeting message"
                    }
                }
            }
        ]
    }
    
    success = test_worker(api_key, worker_config)
    if success:
        print("\n✨ All worker tests passed!")
    else:
        print("\n❌ Worker testing failed")
```

## Common Issues and Solutions

### Connection Issues

If your worker fails to connect:
1. Check your API key is valid
2. Verify network connectivity
3. Ensure worker ID is unique
4. Check if you've reached your worker limit

### Action Space Issues

Common action space problems:
1. Missing required fields
2. Invalid parameter types
3. Parameter constraints not met
4. Duplicate action names

### State Management

Tips for managing worker state:
1. Always return a dictionary from state functions
2. Include error handling in state functions
3. Keep state data minimal and relevant
4. Handle state transitions gracefully

```python
def get_worker_state(function_result, current_state):
    """Example of a robust state function."""
    try:
        # Process function result
        result_status = function_result.get("status", "unknown")
        
        # Update state based on result
        new_state = {
            "status": result_status,
            "last_action": function_result.get("action"),
            "last_updated": datetime.now().isoformat(),
            "error": None
        }
        
        # Handle errors
        if result_status == "error":
            new_state["error"] = function_result.get("error")
            new_state["status"] = "error"
        
        return new_state
        
    except Exception as e:
        # Return safe error state
        return {
            "status": "error",
            "error": str(e),
            "last_updated": datetime.now().isoformat()
        }
```

## Best Practices

1. **Unique IDs**: Use descriptive, unique IDs for workers
2. **Error Handling**: Implement comprehensive error handling
3. **Testing**: Test all actions with various inputs
4. **Documentation**: Document action parameters and expected results
5. **State Management**: Keep worker state clean and relevant
6. **Monitoring**: Log important worker events and state changes

## Getting Help

If you encounter issues:
1. Check the error message in the response
2. Review the [Error Handling Guide](error-handling.md)
3. Search existing [GitHub Issues](https://github.com/game-by-virtuals/game-python/issues)
4. Join our [Discord Community](https://discord.gg/virtuals)
5. Contact support at support@virtuals.io
