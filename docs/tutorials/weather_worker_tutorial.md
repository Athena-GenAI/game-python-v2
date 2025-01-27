# Creating and Testing a Weather Reporter Worker

This tutorial walks through creating and testing a simple Weather Reporter worker. We'll create a worker that can report weather conditions and provide recommendations. This example is perfect for both developers and non-developers to understand how workers function in the GAME SDK.

## What We're Building

Our Weather Reporter worker will:
1. Report current weather conditions
2. Provide clothing recommendations
3. Give activity suggestions
4. Track weather history

## Prerequisites

- GAME SDK installed (`pip install game-sdk`)
- API key from Virtuals.io
- Basic Python knowledge (for developers)
- Python 3.7 or higher

## Step 1: Understanding Worker Components

A worker in GAME SDK has these key components:
- **ID**: Unique identifier for the worker
- **Description**: What the worker does
- **Instructions**: How to use the worker
- **Action Space**: What actions the worker can perform

## Step 2: Creating the Weather Reporter Worker

### For Non-Developers
Think of the worker as a helpful assistant that can:
- Understand weather data
- Make smart recommendations
- Remember weather patterns
- Help plan activities

### For Developers
Here's the code to create our weather reporter:

```python
from game_sdk.game.agent import Agent
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_weather_reporter(api_key):
    """Create a weather reporter worker."""
    try:
        # Create an agent to manage our worker
        agent = Agent(
            api_key=api_key,
            name="Weather Assistant",
            agent_description="An AI that reports weather and gives recommendations",
            agent_goal="Help users make weather-informed decisions",
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )

        # Define the worker configuration
        worker_config = {
            "id": f"weather_reporter_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "A smart weather reporting and recommendation system",
            "instruction": """
                This worker can:
                1. Report current weather conditions
                2. Provide clothing recommendations
                3. Suggest activities based on weather
                4. Track weather history
            """,
            "action_space": [
                {
                    "name": "get_weather",
                    "description": "Get current weather conditions",
                    "parameters": {
                        "location": {
                            "type": "string",
                            "description": "City name or zip code"
                        }
                    }
                },
                {
                    "name": "get_clothing_recommendation",
                    "description": "Get clothing recommendations for current weather",
                    "parameters": {
                        "location": {
                            "type": "string",
                            "description": "City name or zip code"
                        },
                        "activity": {
                            "type": "string",
                            "description": "Planned activity (e.g., 'outdoor sports', 'casual walk')",
                            "optional": True
                        }
                    }
                },
                {
                    "name": "suggest_activities",
                    "description": "Get activity suggestions based on weather",
                    "parameters": {
                        "location": {
                            "type": "string",
                            "description": "City name or zip code"
                        },
                        "preference": {
                            "type": "string",
                            "description": "Preferred type (indoor/outdoor)",
                            "enum": ["indoor", "outdoor", "both"]
                        }
                    }
                },
                {
                    "name": "get_weather_history",
                    "description": "Get weather history for a location",
                    "parameters": {
                        "location": {
                            "type": "string",
                            "description": "City name or zip code"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days of history",
                            "minimum": 1,
                            "maximum": 7
                        }
                    }
                }
            ]
        }

        # Create the worker
        worker = agent.create_worker(worker_config)
        logger.info(f"Created weather reporter worker with ID: {worker_config['id']}")
        return worker, worker_config

    except Exception as e:
        logger.error(f"Failed to create weather reporter: {e}")
        return None, None
```

## Step 3: Testing the Worker

### For Non-Developers
Testing ensures our worker can:
- Understand different locations
- Give accurate recommendations
- Handle errors gracefully
- Remember weather history

### For Developers
Here's how to test the weather reporter:

```python
def test_weather_reporter(worker, config):
    """Run tests on the weather reporter worker."""
    test_cases = [
        # Test weather reporting
        {
            "action": "get_weather",
            "parameters": {
                "location": "New York, NY"
            },
            "description": "Getting weather for New York"
        },
        # Test clothing recommendations
        {
            "action": "get_clothing_recommendation",
            "parameters": {
                "location": "Miami, FL",
                "activity": "beach day"
            },
            "description": "Getting clothing recommendations for Miami beach day"
        },
        # Test activity suggestions
        {
            "action": "suggest_activities",
            "parameters": {
                "location": "Seattle, WA",
                "preference": "both"
            },
            "description": "Getting activity suggestions for Seattle"
        },
        # Test weather history
        {
            "action": "get_weather_history",
            "parameters": {
                "location": "Boston, MA",
                "days": 3
            },
            "description": "Getting weather history for Boston"
        }
    ]

    for test in test_cases:
        try:
            logger.info(f"\nExecuting: {test['description']}")
            result = worker.execute_action(
                test["action"],
                test["parameters"]
            )
            logger.info(f"Result: {result}")
            logger.info("✓ Test passed")

        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False

    return True
```

## Step 4: Running the Complete Example

### For Non-Developers
To use the weather reporter:
1. Get your API key from Virtuals.io
2. Run the example script
3. Check the results in your terminal

### For Developers
Here's the complete script:

```python
def main():
    """Run the weather reporter example."""
    # Replace with your API key
    api_key = "your_api_key_here"

    # Create the weather reporter
    worker, config = create_weather_reporter(api_key)
    if not worker:
        logger.error("Failed to create weather reporter")
        return

    # Test the worker
    success = test_weather_reporter(worker, config)
    if success:
        logger.info("\n✨ All weather reporter tests passed!")
    else:
        logger.error("\n❌ Some weather reporter tests failed")

if __name__ == "__main__":
    main()
```

## Understanding the Results

### For Non-Developers
When you run the tests, you'll see:
- Weather conditions for different cities
- Clothing suggestions based on weather
- Activity recommendations
- Weather history data

Each test will show either:
- ✓ (check mark): Test worked correctly
- ❌ (X mark): Test had a problem

### For Developers
The test results will show:
- API responses
- Error messages (if any)
- State changes
- Performance metrics

## Common Issues and Solutions

### For Everyone
1. **Location not found**
   - Check spelling
   - Use zip codes instead
   - Try a nearby city

2. **No recommendations**
   - Check if weather data is available
   - Verify activity type is valid
   - Try different preferences

3. **Connection problems**
   - Check internet connection
   - Verify API key is valid
   - Try again in a few minutes

### For Developers
1. **API Rate Limits**
   ```python
   # Add rate limiting
   from time import sleep
   sleep(1)  # Wait between requests
   ```

2. **Error Handling**
   ```python
   try:
       result = worker.execute_action(...)
   except APIError as e:
       if e.status_code == 429:  # Rate limit
           sleep(5)
           retry_action()
   ```

## Best Practices

### For Everyone
1. Use specific locations
2. Start with simple queries
3. Check error messages
4. Report issues if found

### For Developers
1. Implement rate limiting
2. Add error handling
3. Log important events
4. Validate inputs
5. Test edge cases

## Next Steps

### For Everyone
1. Try different locations
2. Test various activities
3. Compare recommendations
4. Track weather patterns

### For Developers
1. Add more weather data sources
2. Implement caching
3. Add unit tests
4. Enhance error handling
5. Optimize performance

## Getting Help

Need assistance? Try these resources:
1. [GAME SDK Documentation](https://docs.virtuals.io)
2. [GitHub Issues](https://github.com/game-by-virtuals/game-python/issues)
3. [Discord Community](https://discord.gg/virtuals)
4. Email: support@virtuals.io
