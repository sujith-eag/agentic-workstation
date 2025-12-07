"""
Configuration Service for Agentic Workflow.

Implements the 3-layer configuration loading strategy:
1. Defaults (packaged in resources)
2. User Global (`~/.config/agentic/config.toml`)
3. Project Local (`agentic.toml`)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import tomli as toml  # Using pyproject.toml standard lib in 3.11+, but let's assume <3.11 for safety or use tomllib
# Note: Python 3.11+ has tomllib. For compatibility, we might need 'tomli' in requirements.
# Checking python version or using hack. For now, let's stick to standard if 3.11, or yaml as fallback?
# The request said "config.toml", so TOML is expected.
# I will use a simple wrapper.

try:
    import tomllib as toml
except ImportError:
    try:
        import tomli as toml
    except ImportError:
        # Fallback to a simple TOML parser or fail?
        # Let's handle this by adding tomli to requirements if distinct from python 3.11
        # For this environment (3.12), tomllib is available.
        pass

try:
    import platformdirs
except ImportError:
    platformdirs = None

from importlib import resources

from agentic_workflow.exceptions import ConfigError
import logging
logger = logging.getLogger(__name__)

class ConfigurationService:
    """Service to load and merge configurations."""

    def __init__(self):
        self.app_name = "agentic-workflow"
        self.headers = {}
        
    def _get_user_config_dir(self) -> Path:
        """Get user config directory with fallback."""
        if platformdirs:
            return Path(platformdirs.user_config_dir(self.app_name, "agentic"))
        else:
            # Fallback to standard XDG location
            config_home = os.environ.get('XDG_CONFIG_HOME')
            if config_home:
                return Path(config_home) / "agentic"
            return Path.home() / ".config" / "agentic"

    def load_config(self, project_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load merged configuration.
        
        Order of precedence (later overrides earlier):
        1. Defaults (resources/defaults.toml)
        2. User Global (XDG_CONFIG_HOME/agentic/config.toml)
        3. Project Local (agentic.toml in project_path or CWD parents)
        """
        config = {}
        
        # 1. Defaults
        defaults = self._load_defaults()
        config = self._deep_merge(config, defaults)
        
        # 2. User Global
        user_config = self._load_user_global()
        config = self._deep_merge(config, user_config)
        
        # 3. Project Local
        project_config = self._load_project_local(project_path)
        config = self._deep_merge(config, project_config)
        
        return config

    def _load_defaults(self) -> Dict[str, Any]:
        """Load default config from package resources."""
        try:
            # For python 3.9+ imports
            # Check if resources module exists and has files
            # Just read the file we created
            # Note: We put it in 'agentic_workflow.resources'
            
            # Using new traversing API
            t = resources.files('agentic_workflow.resources').joinpath('defaults.toml')
            if t.is_file():
                with t.open('rb') as f:
                    return toml.load(f)
            return {}
        except Exception as e:
            # Fallback for development if not installed
            # Try finding it relative to this file
            fallback = Path(__file__).parent.parent / "resources" / "defaults.toml"
            if fallback.exists():
                with open(fallback, 'rb') as f:
                    return toml.load(f)
            logger.warning(f"Could not load default config: {e}")
            return {}

    def _load_user_global(self) -> Dict[str, Any]:
        """Load user global config."""
        config_dir = self._get_user_config_dir()
        config_file = config_dir / "config.toml"
        
        if config_file.exists():
            try:
                with open(config_file, 'rb') as f:
                    return toml.load(f)
            except Exception as e:
                logger.warning(f"Failed to load user config {config_file}: {e}")
        return {}

    def _load_project_local(self, start_path: Optional[Path]) -> Dict[str, Any]:
        """Load project local config by searching parents."""
        if start_path is None:
            start_path = Path.cwd()
            
        current = start_path.resolve()
        
        # Search up to root
        # Check for 'agentic.toml'
        for path in [current] + list(current.parents):
            config_file = path / "agentic.toml"
            if config_file.is_file():
                try:
                    with open(config_file, 'rb') as f:
                        data = toml.load(f)
                        # Inject project root
                        data['_project_root'] = str(path)
                        return data
                except Exception as e:
                    logger.warning(f"Failed to load project config {config_file}: {e}")
                    
        return {}

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
