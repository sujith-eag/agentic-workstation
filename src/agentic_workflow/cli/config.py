#!/usr/bin/env python3
"""Configuration management for Agentic Workflow CLI."""
import tomllib
from pathlib import Path
from typing import Dict, Any
import click

# Default configuration
DEFAULT_CONFIG = {
    "default_workflow": "planning",
    "projects_dir": "./projects",
    "theme": "dark",
    "verbose": False,
    "log_level": "INFO",
    "cache_enabled": False,
    "retry_count": 0,
    "api_port": 8000,
    "web_host": "127.0.0.1",
    "web_port": 8000,
    "update_check_interval": 86400,  # 24 hours
}

def load_config(config_path: Path = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults.

    Priority order:
    1. Command-line options (handled elsewhere)
    2. User config file (~/.agentic.toml)
    3. Project config file (if in project directory)
    4. Explicit config file (via --config)
    5. Defaults
    """
    config = DEFAULT_CONFIG.copy()

    # Load user config
    user_config = Path.home() / '.agentic.toml'
    if user_config.exists():
        try:
            with open(user_config, 'rb') as f:
                user_data = tomllib.load(f)
                config.update(user_data)
        except Exception:
            # Silently ignore user config errors
            pass

    # Load project config (if in project directory)
    project_config = Path.cwd() / 'agentic.toml'
    if project_config.exists():
        try:
            with open(project_config, 'rb') as f:
                project_data = tomllib.load(f)
                config.update(project_data)
        except Exception:
            # Silently ignore project config errors
            pass

    # Load explicit config file
    if config_path and config_path.exists():
        try:
            with open(config_path, 'rb') as f:
                explicit_data = tomllib.load(f)
                config.update(explicit_data)
        except Exception as e:
            raise click.ClickException(f"Error loading config file {config_path}: {e}")

    return config

def save_config(config: Dict[str, Any], config_path: Path):
    """Save configuration to file."""
    try:
        import tomli_w
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)
    except ImportError:
        # Fallback to basic TOML writing if tomli_w not available
        import toml
        with open(config_path, 'w') as f:
            toml.dump(config, f)
    except Exception as e:
        raise click.ClickException(f"Error saving config file {config_path}: {e}")

def get_config_value(key: str, default=None, config: Dict = None):
    """Get a configuration value with fallback."""
    if config and key in config:
        return config[key]
    return default