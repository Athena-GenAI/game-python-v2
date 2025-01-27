"""
Example script demonstrating worker creation and testing.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from game_sdk.game.agent import Agent
from game_sdk.game.exceptions import ValidationError, APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_worker(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Create a test worker with a comprehensive action space.
    
    Args:
        api_key: Your API key
    
    Returns:
        Dict containing the worker configuration if successful, None otherwise
    """
    try:
        # Create an agent first
        agent = Agent(
            api_key=api_key,
            name="Worker Test Agent",
            agent_description="Testing worker creation and functionality",
            agent_goal="Demonstrate worker testing",
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )
        
        # Define a test worker with various action types
        worker_config = {
            "id": f"test_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "A test worker with various actions",
            "instruction": "Execute test actions to verify functionality",
            "action_space": [
                {
                    "name": "send_message",
                    "description": "Send a test message",
                    "parameters": {
                        "message": {
                            "type": "string",
                            "description": "Message content",
                            "maxLength": 1000
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Message priority",
                            "minimum": 1,
                            "maximum": 5
                        }
                    }
                },
                {
                    "name": "process_data",
                    "description": "Process test data",
                    "parameters": {
                        "data": {
                            "type": "object",
                            "description": "Data to process",
                            "properties": {
                                "type": {"type": "string"},
                                "value": {"type": "number"}
                            }
                        }
                    }
                },
                {
                    "name": "update_status",
                    "description": "Update worker status",
                    "parameters": {
                        "status": {
                            "type": "string",
                            "description": "New status",
                            "enum": ["active", "idle", "error"]
                        }
                    }
                }
            ]
        }
        
        # Create the worker
        worker = agent.create_worker(worker_config)
        logger.info(f"Created worker with ID: {worker_config['id']}")
        
        return worker_config
        
    except Exception as e:
        logger.error(f"Failed to create worker: {e}")
        return None

def test_worker_actions(agent: Agent, worker_config: Dict[str, Any]) -> bool:
    """
    Test all actions defined in the worker's action space.
    
    Args:
        agent: Agent instance
        worker_config: Worker configuration dictionary
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        worker = agent.get_worker(worker_config["id"])
        
        # Test each action
        test_cases = [
            # Test send_message
            {
                "action": "send_message",
                "parameters": {
                    "message": "Test message",
                    "priority": 1
                }
            },
            # Test process_data
            {
                "action": "process_data",
                "parameters": {
                    "data": {
                        "type": "test",
                        "value": 42
                    }
                }
            },
            # Test update_status
            {
                "action": "update_status",
                "parameters": {
                    "status": "active"
                }
            }
        ]
        
        for test_case in test_cases:
            try:
                logger.info(f"Testing action: {test_case['action']}")
                result = worker.execute_action(
                    test_case["action"],
                    test_case["parameters"]
                )
                logger.info(f"Action result: {result}")
                
            except Exception as e:
                logger.error(f"Action {test_case['action']} failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Worker testing failed: {e}")
        return False

def main():
    """Main function to demonstrate worker creation and testing."""
    api_key = "your_api_key"  # Replace with your API key
    
    # Create worker
    worker_config = create_test_worker(api_key)
    if not worker_config:
        logger.error("Failed to create worker")
        return
    
    # Create agent for testing
    try:
        agent = Agent(
            api_key=api_key,
            name="Worker Test Agent",
            agent_description="Testing worker functionality",
            agent_goal="Test worker actions",
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )
        
        # Test worker actions
        success = test_worker_actions(agent, worker_config)
        if success:
            logger.info("✨ All worker tests passed!")
        else:
            logger.error("❌ Some worker tests failed")
            
    except Exception as e:
        logger.error(f"Testing failed: {e}")

if __name__ == "__main__":
    main()
