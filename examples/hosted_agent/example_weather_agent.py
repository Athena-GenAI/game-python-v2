"""
Weather Example

This example demonstrates how to create a hosted agent that provides weather information
and clothing recommendations for different cities.

Example usage:
    python example_weather_agent.py
"""

import os
import logging
import requests
from typing import Dict, Any
from game_sdk.hosted_game.agent import Agent, Function, FunctionArgument, FunctionConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
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

def main():
    """Run the weather example."""
    try:
        # Get API key from environment
        api_key = os.getenv("VIRTUALS_API_KEY")
        if not api_key:
            raise ValueError("VIRTUALS_API_KEY environment variable not set")

        # Create the agent
        agent = Agent(
            api_key=api_key,
            goal="provide weather information",
            description="A helpful weather assistant that provides weather information and clothing recommendations",
            world_info="This agent can provide weather information for New York, Miami, and Boston"
        )

        # Add the weather function
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

        # Example: Test the agent with a query
        logger.info("🌤️ Testing weather agent...")
        result = agent.react(
            session_id="weather-session",
            platform="example",
            event="message from user: What's the weather like in New York?",
            task="get weather information for New York"
        )

        if result:
            logger.info("✅ Agent response received")
            logger.info(f"Response: {result}")
        else:
            logger.error("❌ No response from agent")

    except Exception as e:
        logger.error(f"❌ Error running weather example: {str(e)}")
        raise

if __name__ == "__main__":
    main()
