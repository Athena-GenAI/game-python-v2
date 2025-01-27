import unittest
from unittest.mock import Mock, patch
from game_sdk.game.agent import Agent
from datetime import datetime
import logging

class TestWeatherWorker(unittest.TestCase):
    @patch('game_sdk.game.utils.get_access_token')
    @patch('game_sdk.game.utils.post')
    def setUp(self, mock_post, mock_get_token):
        """Set up test fixtures before each test method."""
        # Mock API responses
        mock_get_token.return_value = "mock_token"
        mock_post.return_value = {"id": "test_agent_id"}  # Changed to match expected structure
        
        # Mock API key for testing
        self.api_key = "test_api_key"
        self.worker_id = "test_weather_worker"
        
        # Create a mock agent
        self.agent = Agent(
            api_key=self.api_key,
            name="Test Weather Assistant",
            agent_description="Test weather reporter",
            agent_goal="Test weather reporting functionality",
            get_agent_state_fn=lambda x, y: {"status": "ready"}
        )
        
        # Create the worker configuration
        self.worker_config = {
            "id": f"test_weather_reporter_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Test weather reporting system",
            "instruction": "Test weather reporting capabilities",
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
                }
            ]
        }
        
        # Mock the get_worker method
        with patch.object(self.agent, 'get_worker') as mock_get_worker:
            mock_worker = Mock()
            mock_worker.config = self.worker_config
            mock_get_worker.return_value = mock_worker
            self.worker = self.agent.get_worker(self.worker_id)

    def test_worker_creation(self):
        """Test if worker is created correctly."""
        self.assertIsNotNone(self.worker)
        self.assertEqual(self.worker.config["description"], "Test weather reporting system")

    def test_get_weather(self):
        """Test the get_weather action."""
        # Mock the execute_action method
        with patch.object(self.worker, 'execute_action') as mock_execute:
            # Set up the mock return value
            mock_execute.return_value = {
                "temperature": 72,
                "condition": "sunny",
                "humidity": 45
            }
            
            # Test the action
            result = self.worker.execute_action(
                "get_weather",
                {"location": "New York, NY"}
            )
            
            # Verify the results
            self.assertIn("temperature", result)
            self.assertIn("condition", result)
            self.assertIn("humidity", result)
            
            # Verify the mock was called correctly
            mock_execute.assert_called_once_with(
                "get_weather",
                {"location": "New York, NY"}
            )

    def test_invalid_location(self):
        """Test handling of invalid location."""
        with patch.object(self.worker, 'execute_action') as mock_execute:
            mock_execute.side_effect = ValueError("Invalid location")
            
            with self.assertRaises(ValueError):
                self.worker.execute_action(
                    "get_weather",
                    {"location": "InvalidCity123"}
                )

    def test_missing_parameters(self):
        """Test handling of missing parameters."""
        with patch.object(self.worker, 'execute_action') as mock_execute:
            mock_execute.side_effect = ValueError("Missing required parameter: location")
            
            with self.assertRaises(ValueError):
                self.worker.execute_action("get_weather", {})

if __name__ == '__main__':
    unittest.main()
