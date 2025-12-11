"""Configuration management."""

from typing import Any, Dict
from pathlib import Path
import yaml
from loguru import logger


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    path = Path(config_path)
    
    if not path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return get_default_config()
    
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from: {config_path}")
        return config
    
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "llm": {
            "provider": "ollama",
            "model": "llama2",
            "base_url": "http://localhost:11434",
            "temperature": 0.7,
            "timeout": 300
        },
        "vlm": {
            "save_screenshots": True,
            "screenshot_dir": "./screenshots"
        },
        "agents": {
            "max_iterations": 10,
            "verbose": True,
            "pause": 0.5
        },
        "logging": {
            "level": "INFO",
            "log_file": "logs/digital_humain.log"
        }
    }


def save_config(config: Dict[str, Any], config_path: str = "config/config.yaml") -> bool:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration
        
    Returns:
        True if successful
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Saved configuration to: {config_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False
