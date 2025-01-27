"""
Example of handling plugin-related errors in the GAME SDK.
"""

import logging
import importlib
from typing import Any, Dict, Optional
from game_sdk.game.exceptions import ValidationError, APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginError(Exception):
    """Custom exception for plugin-related errors."""
    pass

def validate_plugin_interface(plugin_module: Any) -> None:
    """Validate that a plugin module implements the required interface."""
    required_methods = ['initialize', 'execute', 'cleanup']
    
    for method in required_methods:
        if not hasattr(plugin_module, method):
            raise ValidationError(
                f"Plugin missing required method: {method}. "
                f"All plugins must implement: {', '.join(required_methods)}"
            )

def load_plugin_safely(plugin_name: str, config: Dict[str, Any]) -> Optional[Any]:
    """
    Safely load and initialize a plugin.
    
    Args:
        plugin_name: Name of the plugin to load
        config: Plugin configuration dictionary
    
    Returns:
        Initialized plugin instance or None if loading fails
    """
    try:
        # Attempt to import plugin
        logger.info(f"Loading plugin: {plugin_name}")
        plugin_module = importlib.import_module(f"game_sdk.plugins.{plugin_name}")
        
        # Validate plugin interface
        validate_plugin_interface(plugin_module)
        
        # Initialize plugin
        logger.info("Initializing plugin...")
        plugin = plugin_module.initialize(config)
        
        # Test plugin execution
        logger.info("Testing plugin execution...")
        test_result = plugin.execute({"test": True})
        if not test_result:
            raise PluginError("Plugin execution test failed")
        
        return plugin
        
    except ImportError as e:
        logger.error(f"Failed to import plugin '{plugin_name}': {e}")
        logger.info("Available plugins: twitter, discord, slack")
        return None
        
    except ValidationError as e:
        logger.error(f"Plugin validation failed: {e}")
        return None
        
    except PluginError as e:
        logger.error(f"Plugin error: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error loading plugin '{plugin_name}': {e}")
        return None

def cleanup_plugin_safely(plugin: Any) -> bool:
    """
    Safely cleanup plugin resources.
    
    Args:
        plugin: Plugin instance to cleanup
    
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    try:
        logger.info("Cleaning up plugin resources...")
        plugin.cleanup()
        return True
    except Exception as e:
        logger.error(f"Failed to cleanup plugin: {e}")
        return False

def demonstrate_plugin_handling():
    """Demonstrate handling of plugin-related errors."""
    # 1. Try loading a non-existent plugin
    plugin = load_plugin_safely("nonexistent_plugin", {})
    if not plugin:
        logger.info("Successfully handled non-existent plugin error")
    
    # 2. Try loading with invalid config
    plugin = load_plugin_safely("twitter", {
        "api_key": "",  # Invalid empty API key
        "api_secret": "secret"
    })
    if not plugin:
        logger.info("Successfully handled invalid config error")
    
    # 3. Load a valid plugin
    plugin = load_plugin_safely("twitter", {
        "api_key": "valid_key",
        "api_secret": "valid_secret"
    })
    
    if plugin:
        # 4. Demonstrate safe cleanup
        if cleanup_plugin_safely(plugin):
            logger.info("Successfully cleaned up plugin")
        else:
            logger.warning("Plugin cleanup failed")

if __name__ == "__main__":
    demonstrate_plugin_handling()
