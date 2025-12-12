"""
Pydantic models for Agentic Workflow configuration.

This module defines the type-safe configuration schemas for the cascading
configuration system. All configurations are validated using Pydantic V2.
"""

from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class SystemConfig(BaseModel):
    """
    Global system configuration (Layer 2).
    Resides in ~/.config/agentic/config.yaml
    """
    # Core Workspace Settings
    default_workspace: Path = Field(
        default=Path.home() / "AgenticProjects",
        description="Default root directory for all new projects"
    )
    # User Experience
    editor_command: str = Field(
        default="code",
        description="Command to open files/artifacts (e.g., 'code', 'vim', 'nano')"
    )
    tui_enabled: bool = Field(
        default=True,
        description="Enable interactive TUI features by default"
    )
    check_updates: bool = Field(
        default=True,
        description="Check for package updates on startup"
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Default logging level"
    )

    @field_validator("default_workspace")
    @classmethod
    def validate_workspace_path(cls, v: Path) -> Path:
        """Ensure path is absolute and resolvable"""
        return v.expanduser().resolve()


class ProjectConfig(BaseModel):
    """
    Project-specific configuration (Layer 3).
    Resides in <project_root>/.agentic/config.yaml
    """
    workflow: str = Field(
        description="Name of the active workflow type"
    )
    root_path: Path = Field(
        description="Absolute path to the project root"
    )
    strict_mode: bool = Field(
        default=True,
        description="Enforce strict governance rules"
    )
    excluded_paths: List[str] = Field(
        default_factory=list,
        description="Paths to exclude from processing"
    )
    custom_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow-specific overrides"
    )


class WorkflowRules(BaseModel):
    """
    Immutable workflow rules loaded from workflow.json (Layer 4).
    """
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    gates: Dict[str, Any] = Field(default_factory=dict)
    required_artifacts: List[str] = Field(default_factory=list)
    governance: Dict[str, Any] = Field(default_factory=dict)


class RuntimeConfig(BaseModel):
    """
    The final merged configuration object used by the engine.
    Combines all layers with proper precedence.
    """
    system: SystemConfig = Field(default_factory=SystemConfig)
    project: Optional[ProjectConfig] = None
    workflow_rules: WorkflowRules = Field(default_factory=WorkflowRules)
    verbose: bool = Field(default=False, description="Runtime verbosity flag")
    force: bool = Field(default=False, description="Force operations")

    @property
    def is_project_context(self) -> bool:
        """Check if we're in a project context"""
        return self.project is not None