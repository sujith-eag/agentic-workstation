"""
Configuration System for Agentic Workflow Platform

This module provides a dual configuration system:
- Application config: Global settings in config/agentic_workflow.yaml
- Project config: Project-specific settings in config.yaml

Key Design Decisions:
- Auto-detection of config files based on current working directory
- Deep merge with project config taking precedence over app config
- Environment variable substitution using ${VAR_NAME} syntax
- In-memory caching with file modification time checking
- Comprehensive error handling with detailed messages
- Schema-based validation using jsonschema

Author: AI Assistant
Date: December 6, 2025
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from datetime import datetime
import jsonschema
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Constants
APP_CONFIG_FILENAME = "agentic_workflow.yaml"
PROJECT_CONFIG_FILENAME = "config.yaml"
CONFIG_DIR = "config"
SCHEMA_DIR = "_schemas"
SCHEMA_FILENAME = "config_schema.json"

# Custom exceptions
class ConfigError(Exception):
    """Base exception for configuration errors"""
    pass

class ConfigNotFoundError(ConfigError):
    """Raised when a configuration file is not found"""
    pass

class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails"""
    pass

class ConfigMergeError(ConfigError):
    """Raised when configuration merging fails"""
    pass

@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self) -> bool:
        return self.is_valid

# Global cache for loaded configs
_config_cache = {}

def _get_cache_key(config_type: str, path: Path) -> str:
    """Generate cache key for config files"""
    return f"{config_type}:{path}"

def _is_cache_valid(cache_key: str, file_path: Path) -> bool:
    """Check if cached config is still valid"""
    if cache_key not in _config_cache:
        return False

    cached_mtime = _config_cache[cache_key].get('mtime')
    if cached_mtime is None:
        return False

    try:
        current_mtime = file_path.stat().st_mtime
        return current_mtime <= cached_mtime
    except (OSError, AttributeError):
        return False

def _get_cached_config(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get config from cache if valid"""
    if cache_key in _config_cache:
        return _config_cache[cache_key].get('data')
    return None

def _set_cached_config(cache_key: str, config: Dict[str, Any], file_path: Path) -> None:
    """Store config in cache with modification time"""
    try:
        mtime = file_path.stat().st_mtime
    except (OSError, AttributeError):
        mtime = None

    _config_cache[cache_key] = {
        'data': config,
        'mtime': mtime,
        'loaded_at': datetime.now()
    }

def _clear_config_cache() -> None:
    """Clear all cached configurations"""
    global _config_cache
    _config_cache = {}

def _substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Substitute environment variables in config values"""
    def _substitute_value(value: Any) -> Any:
        if isinstance(value, str):
            # Replace ${VAR_NAME} with environment variable
            import re
            def replace_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            return re.sub(r'\$\{([^}]+)\}', replace_var, value)
        elif isinstance(value, dict):
            return {k: _substitute_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_substitute_value(item) for item in value]
        else:
            return value

    return _substitute_value(config)

def _deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries with override taking precedence

    Design Decision: Override dict takes precedence over base dict
    for all non-dict values. For nested dicts, merge recursively.
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            # Override takes precedence
            result[key] = value

    return result

def find_repo_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the repository root by looking for common indicators

    Design Decision: Look for .git directory, src/ directory, or config/ directory
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Walk up the directory tree
    for path in [current] + list(current.parents):
        if (path / '.git').is_dir() or \
           (path / 'src').is_dir() or \
           (path / 'config').is_dir():
            return path

    # Fallback to current directory
    return start_path

def find_project_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the project root by looking for config.yaml

    Design Decision: Look for config.yaml file in current or parent directories
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Check current directory first
    if (current / PROJECT_CONFIG_FILENAME).is_file():
        return current

    # Walk up the directory tree
    for path in current.parents:
        if (path / PROJECT_CONFIG_FILENAME).is_file():
            return path

    # Fallback to current directory
    return start_path

def load_app_config(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load application configuration

    Design Decision: Auto-detect repo root, look for config/agentic_workflow.yaml
    """
    if repo_root is None:
        repo_root = find_repo_root()

    config_path = repo_root / CONFIG_DIR / APP_CONFIG_FILENAME
    cache_key = _get_cache_key('app', config_path)

    # Check cache first
    if _is_cache_valid(cache_key, config_path):
        cached_config = _get_cached_config(cache_key)
        if cached_config is not None:
            logger.debug(f"Loaded app config from cache: {config_path}")
            return cached_config

    # Load from file
    if not config_path.is_file():
        raise ConfigNotFoundError(f"Application config not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # Substitute environment variables
        config = _substitute_env_vars(config)

        # Cache the result
        _set_cached_config(cache_key, config, config_path)

        logger.info(f"Loaded app config: {config_path}")
        return config

    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse app config {config_path}: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load app config {config_path}: {e}")

def load_project_config(project_path: Path) -> Dict[str, Any]:
    """
    Load project configuration

    Design Decision: Look for config.yaml in project directory
    """
    config_path = project_path / PROJECT_CONFIG_FILENAME
    cache_key = _get_cache_key('project', config_path)

    # Check cache first
    if _is_cache_valid(cache_key, config_path):
        cached_config = _get_cached_config(cache_key)
        if cached_config is not None:
            logger.debug(f"Loaded project config from cache: {config_path}")
            return cached_config

    # Load from file
    if not config_path.is_file():
        logger.warning(f"Project config not found: {config_path}, using empty config")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # Substitute environment variables
        config = _substitute_env_vars(config)

        # Cache the result
        _set_cached_config(cache_key, config, config_path)

        logger.info(f"Loaded project config: {config_path}")
        return config

    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse project config {config_path}: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load project config {config_path}: {e}")

def merge_configs(app_config: Dict[str, Any], project_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge application and project configurations

    Design Decision: Project config takes precedence over app config
    """
    try:
        merged = _deep_merge_dicts(app_config, project_config)
        logger.debug("Successfully merged app and project configs")
        return merged
    except Exception as e:
        raise ConfigMergeError(f"Failed to merge configurations: {e}")

def get_config_for_command(project_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get merged configuration for CLI command execution

    Design Decision: Auto-detect project root, load and merge both configs
    """
    if project_path is None:
        project_path = find_project_root()

    try:
        app_config = load_app_config()
        project_config = load_project_config(project_path)
        merged_config = merge_configs(app_config, project_config)

        logger.debug(f"Loaded merged config for project: {project_path}")
        return merged_config

    except Exception as e:
        logger.error(f"Failed to load config for command: {e}")
        raise

def validate_config(config: Dict[str, Any], schema_type: str) -> ValidationResult:
    """
    Validate configuration against schema

    Design Decision: Use jsonschema for validation with custom error formatting
    """
    try:
        # Load schema
        repo_root = find_repo_root()
        schema_path = repo_root / "manifests" / SCHEMA_DIR / SCHEMA_FILENAME

        if not schema_path.is_file():
            return ValidationResult(
                is_valid=False,
                errors=[f"Schema file not found: {schema_path}"],
                warnings=[]
            )

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        # Get schema for specific type
        config_schema = schema.get(schema_type, {})
        if not config_schema:
            return ValidationResult(
                is_valid=False,
                errors=[f"Schema type '{schema_type}' not found in schema"],
                warnings=[]
            )

        # Validate
        jsonschema.validate(config, config_schema)

        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )

    except jsonschema.ValidationError as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Validation error at {e.absolute_path}: {e.message}"],
            warnings=[]
        )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Validation failed: {e}"],
            warnings=[]
        )

def save_project_config(config: Dict[str, Any], project_path: Path) -> None:
    """
    Save project configuration to file

    Design Decision: Create backup of existing config, format YAML nicely
    """
    config_path = project_path / PROJECT_CONFIG_FILENAME

    # Create backup if file exists
    if config_path.is_file():
        backup_path = config_path.with_suffix('.yaml.backup')
        try:
            config_path.replace(backup_path)
            logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    try:
        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save config with nice formatting
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Clear cache for this file
        cache_key = _get_cache_key('project', config_path)
        if cache_key in _config_cache:
            del _config_cache[cache_key]

        logger.info(f"Saved project config: {config_path}")

    except Exception as e:
        raise ConfigError(f"Failed to save project config {config_path}: {e}")

def update_config_value(config: Dict[str, Any], key_path: str, value: Any, create_path: bool = False) -> Dict[str, Any]:
    """
    Update a nested configuration value

    Design Decision: Support dot-notation for nested keys (e.g., 'governance.strictness.level')
    """
    keys = key_path.split('.')
    current = config

    # Navigate to the parent of the target key
    for key in keys[:-1]:
        if key not in current:
            if create_path:
                current[key] = {}
            else:
                raise ConfigError(f"Path not found: {'.'.join(keys[:-1])}")
        current = current[key]

    # Set the value
    current[keys[-1]] = value
    return config

# Placeholder functions to be implemented
def generate_project_config(workflow_type: str, project_name: str, app_config: Dict[str, Any], workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate project config from workflow data - implemented in project_generation.py"""
    from .project_generation import generate_project_config as impl
    return impl(workflow_type, project_name, app_config, workflow_data)

def extract_governance_from_workflow(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract governance rules from workflow data - implemented in project_generation.py"""
    from .project_generation import extract_governance_from_workflow as impl
    return impl(workflow_data)