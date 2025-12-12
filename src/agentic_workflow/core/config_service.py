"""
Cascading Configuration Service for Agentic Workflow.

Implements the 5-layer configuration system:
1. Defaults (hardcoded)
2. User Global (~/.config/agentic/config.yaml)
3. Project Local (<project>/.agentic/config.yaml)
4. Workflow Definition (workflow.json)
5. Runtime Flags (CLI args)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import platformdirs
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .schema import SystemConfig, ProjectConfig, WorkflowRules, RuntimeConfig
from .exceptions import ConfigError
import logging

logger = logging.getLogger(__name__)

__all__ = ["ConfigurationService", "find_project_root", "find_repo_root"]


class ConfigurationService:
    """Service for loading and merging the 5-layer configuration cascade."""

    def __init__(self) -> None:
        """Initialize the ConfigurationService."""
        self.global_config_path = self._get_global_config_path()

    def _get_global_config_path(self) -> Path:
        """Get the path to the global config file."""
        config_dir = Path(platformdirs.user_config_dir("agentic", "agentic"))
        return config_dir / "config.yaml"

    def ensure_system_configured(self) -> None:
        """Check for Layer 2 config; trigger TUI if missing and interactive."""
        if not self.global_config_path.exists():
            if sys.stdin.isatty() and sys.stdout.isatty():
                from ..cli.tui.setup import run_setup_wizard
                run_setup_wizard()
            else:
                # Headless fallback: create default config
                self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default global config for headless environments."""
        try:
            config = SystemConfig()
            self.global_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.global_config_path, "w") as f:
                yaml.dump(config.model_dump(), f, default_flow_style=False)
        except Exception as e:
            raise ConfigError(f"Failed to create default config: {e}")

    def find_project_root(self, start_path: Optional[Path] = None) -> Optional[Path]:
        """Find the project root by looking for .agentic/ directory or project_index.md."""
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()
        while current != current.parent:
            if (current / ".agentic").is_dir() or (current / "project_index.md").exists():
                return current
            current = current.parent
        return None

    def load_config(self, context_path: Optional[Path] = None, verbose: bool = False, force: bool = False) -> RuntimeConfig:
        """Load the complete merged configuration."""
        self.ensure_system_configured()

        config = RuntimeConfig(verbose=verbose, force=force)

        # Layer 1: Defaults (already set in RuntimeConfig)

        # Layer 2: User Global
        if self.global_config_path.exists():
            global_data = self._load_yaml(self.global_config_path)
            config.system = SystemConfig(**global_data)

        # Layer 3 & 4: Project and Workflow
        project_root = self.find_project_root(context_path)
        if project_root:
            # Project config from <project>/.agentic/config.yaml
            project_config_path = project_root / ".agentic" / "config.yaml"
            if project_config_path.exists():
                project_data = self._load_yaml(project_config_path)
                project_data['root_path'] = str(project_root)  # Add root_path
                config.project = ProjectConfig(**project_data)

                # Workflow rules (Layer 4)
                workflow_name = config.project.workflow
                from ..generation.canonical_loader import load_canonical_workflow
                workflow_data = load_canonical_workflow(workflow_name)
                config.workflow_rules = WorkflowRules(**workflow_data.get("workflow", {}))

        return config

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file safely."""
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigError(f"Failed to load config from {path}: {e}")

    def _load_toml(self, path: Path) -> Dict[str, Any]:
        """Load TOML file safely."""
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            raise ConfigError(f"Failed to load config from {path}: {e}")

    def deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        return result


# Standalone utility functions for backward compatibility
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


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the project root by looking for .agentic/ directory or project_index.md
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        if (current / ".agentic").is_dir() or (current / "project_index.md").exists():
            return current
        current = current.parent
    return None
