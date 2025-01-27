"""
Custom Agent Example

This example demonstrates how to create a custom agent with platform-specific functions.
The agent searches for music recommendations when queried.

Example usage:
    python example-custom.py
"""

import os
import logging
from game_sdk.hosted_game.agent import Agent, Function, FunctionArgument, FunctionConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the custom agent example."""
    try:
        # Get API key from environment
        api_key = os.getenv("VIRTUALS_API_KEY")
        if not api_key:
            raise ValueError("VIRTUALS_API_KEY environment variable not set")

        # Create the agent
        agent = Agent(
            api_key=api_key,
            goal="search for best songs",
            description="A helpful music assistant that provides song recommendations",
            world_info="This agent can search for and recommend great music across different genres"
        )

        # Add custom search function for Telegram platform
        agent.add_custom_function(
            Function(
                fn_name="custom_search_internet",
                fn_description="search the internet for the best songs",
                args=[
                    FunctionArgument(
                        name="query",
                        type="string",
                        description="The query to search for"
                    )
                ],
                config=FunctionConfig(
                    method="get",
                    url="https://google.com",
                    platform="telegram",  # this function will only be used for telegram
                    success_feedback="I found the best songs",
                    error_feedback="I couldn't find the best songs"
                )
            )
        )

        # Test the agent with a music recommendation query
        logger.info("🎵 Testing music recommendation agent...")
        result = agent.react(
            session_id="session-telegram",
            platform="telegram",
            event="message from user: give me some great music?",
            task="reply with a music recommendation"
        )

        if result:
            logger.info("✅ Agent response received")
            logger.info(f"Response: {result}")
        else:
            logger.error("❌ No response from agent")

    except Exception as e:
        logger.error(f"❌ Error running custom agent example: {str(e)}")
        raise

if __name__ == "__main__":
    main()
