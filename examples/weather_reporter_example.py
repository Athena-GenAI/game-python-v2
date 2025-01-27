"""
Example of creating and testing a Weather Reporter worker.

This script demonstrates how to create and test a worker that provides
weather information and recommendations using the hosted agent functionality
from example_weather_agent.py.

"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import requests

from game_sdk.hosted_game.agent import Agent, Function, FunctionArgument, FunctionConfig
from game_sdk.game.exceptions import ValidationError, APIError

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_weather_handler(query: str) -> Dict[str, Any]:
    """Handle weather requests and return formatted data."""
    try:
        # Fetch weather data from our example API
        response = requests.get('https://dylanburkey.com/assets/weather.json')
        response.raise_for_status()
        data = response.json()
        
        # Extract city from query (simple approach)
        city = query.lower().replace("what's the weather like in ", "").replace("?", "").strip()
        
        # Find the matching city in the weather data
        for location in data.get("weather", []):
            if location["location"].lower() == city.lower():
                return {
                    "city": city,
                    "temperature": location["temperature"],
                    "condition": location["condition"],
                    "humidity": location["humidity"],
                    "clothing": location["clothing"]
                }
        
        return {"error": f"No weather data available for {city}"}
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch weather data: {e}")
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid weather data format: {e}")
        return {"error": f"Invalid weather data format: {str(e)}"}

def create_weather_reporter(api_key: str) -> Tuple[Optional[Agent], Optional[Dict[str, Any]]]:
    """
    Create a weather reporter agent.
    
    Args:
        api_key: Your API key
    
    Returns:
        Tuple containing (agent, config) if successful, (None, None) otherwise
    """
    try:
        logger.debug(f"Creating agent with API key: {api_key[:8]}...")

        # Create the agent
        agent = Agent(
            api_key=api_key,
            goal="provide weather information and recommendations",
            description="A helpful weather assistant that provides weather information and clothing recommendations",
            world_info="This agent can provide weather information for New York, Miami, and Boston"
        )

        # Define the weather function
        weather_fn = Function(
            fn_name="get_weather",
            fn_description="Get weather information and clothing recommendations for a city",
            args=[
                FunctionArgument(
                    name="query",
                    description="The city to get weather information for (New York, Miami, or Boston)",
                    type="string"
                )
            ],
            config=FunctionConfig(
                method="get",
                url="https://dylanburkey.com/assets/weather.json",
                success_feedback="Here's the weather information",
                error_feedback="Sorry, I couldn't get the weather information",
                platform="example"
            )
        )
        agent.custom_functions.append(weather_fn)
        
        logger.info(f"Created weather reporter agent")
        
        # Create a config dictionary for testing
        config = {
            "id": f"weather_reporter_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "A smart weather reporting and recommendation system",
            "supported_cities": ["New York", "Miami", "Boston"]
        }
        
        return agent, config

    except Exception as e:
        logger.error(f"Failed to create weather reporter: {e}", exc_info=True)
        return None, None

def test_weather_reporter(agent: Agent, config: Dict[str, Any]) -> bool:
    """
    Run tests on the weather reporter.
    
    Args:
        agent: Agent instance to test
        config: Configuration dictionary
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    test_cases = [
        {
            "query": "What's the weather like in New York?",
            "task": "get weather information for New York",
            "description": "Getting weather for New York"
        },
        {
            "query": "What's the weather like in Miami?",
            "task": "get weather information for Miami",
            "description": "Getting weather for Miami"
        },
        {
            "query": "What's the weather like in Boston?",
            "task": "get weather information for Boston",
            "description": "Getting weather for Boston"
        }
    ]

    for test in test_cases:
        try:
            logger.info(f"\nExecuting: {test['description']}")
            result = agent.react(
                session_id=f"test-session-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                platform="example",
                event=f"message from user: {test['query']}",
                task=test['task']
            )
            
            if result:
                logger.info(f"Result: {result}")
                logger.info("✓ Test passed")
            else:
                logger.error("❌ No response from agent")
                return False

        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False

    return True

def main():
    """Run the weather reporter example."""
    try:
        # Get API key from environment
        api_key = os.getenv("VIRTUALS_API_KEY")  # Note: Using VIRTUALS_API_KEY instead of GAME_API_KEY
        if not api_key:
            logger.error("VIRTUALS_API_KEY not found in environment")
            return

        logger.debug("Starting weather reporter creation")
        # Create the weather reporter
        agent, config = create_weather_reporter(api_key)
        if not agent:
            logger.error("Failed to create weather reporter")
            return

        # Test the agent
        logger.debug("Starting weather reporter tests")
        success = test_weather_reporter(agent, config)
        if success:
            logger.info("\n✨ All weather reporter tests passed!")
        else:
            logger.error("\n❌ Some weather reporter tests failed")
            
    except Exception as e:
        logger.error(f"Main execution failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()
