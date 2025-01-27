"""
Example of handling network-related errors in the GAME SDK.
"""

import logging
import time
from requests.exceptions import RequestException, Timeout, ConnectionError
from game_sdk.game.agent import Agent
from game_sdk.game.exceptions import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_network_errors(api_key: str, max_retries: int = 3):
    """Demonstrate handling of various network errors."""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            agent = Agent(
                api_key=api_key,
                name="Network Test Agent",
                agent_description="Testing network error handling",
                agent_goal="Demonstrate network resilience",
                get_agent_state_fn=lambda x, y: {"status": "ready"}
            )
            logger.info("Successfully created agent")
            return agent
            
        except ConnectionError:
            retry_count += 1
            logger.error(
                f"Connection error (attempt {retry_count}/{max_retries}). "
                "Check your internet connection."
            )
            
        except Timeout:
            retry_count += 1
            logger.error(
                f"Request timed out (attempt {retry_count}/{max_retries}). "
                "The API is taking too long to respond."
            )
            
        except RequestException as e:
            retry_count += 1
            logger.error(f"Network error (attempt {retry_count}/{max_retries}): {e}")
        
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # Exponential backoff
            logger.info(f"Waiting {wait_time} seconds before retrying...")
            time.sleep(wait_time)
    
    logger.error("Failed to create agent after maximum retry attempts")
    return None

def demonstrate_network_handling():
    """Run through various network error scenarios."""
    api_key = "your_api_key_here"
    
    # 1. Basic network error handling
    agent = handle_network_errors(api_key)
    
    if agent:
        # 2. Handle rate limiting
        try:
            # Simulate multiple rapid requests
            for _ in range(10):
                agent.create_worker({
                    "id": "test_worker",
                    "description": "Test worker",
                    "instruction": "Test instruction",
                    "action_space": []
                })
        except APIError as e:
            if e.status_code == 429:
                logger.error("Rate limit exceeded. Implement rate limiting.")
            else:
                logger.error(f"API error: {e}")

if __name__ == "__main__":
    demonstrate_network_handling()
