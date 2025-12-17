"""Resolve path strings into concrete filesystem Paths for runtime configs.

This module implements configuration-driven path resolution used by the
CLI and services: it expands environment variables, detects special
prefixes (``${REPO_ROOT}``, ``${PROJECT_ROOT}``), and returns a
structured ``ResolvedPath`` describing resolution metadata.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, TypedDict
from dataclasses import dataclass
import logging

from .config_service import find_project_root, find_repo_root

# Setup logging
logger = logging.getLogger(__name__)

# Path type constants
PATH_TYPE_ABSOLUTE = "absolute"
PATH_TYPE_RELATIVE_PROJECT = "relative_project"
PATH_TYPE_RELATIVE_REPO = "relative_repo"
PATH_TYPE_RELATIVE_CURRENT = "relative_current"


# Public API exported from this module
__all__ = [
    "ResolvedPath",
    "resolve_path",
    "resolve_config_paths",
    "get_project_dirs",
    "get_workflow_paths",
    "ensure_project_dirs_exist",
    "validate_project_structure",
    "get_script_paths",
    "get_agent_file_path",
    "get_artifact_path",
    "get_log_path",
    "get_context_path",
]

@dataclass
class ResolvedPath:
    """Represent a resolved `Path` with metadata for config-driven resolution.

    The dataclass exposes the resolved absolute `path`, the original input
    string, the `path_type` detected, the `base_path` used for resolution,
    and boolean flags describing existence and file/directory status.
    """
    path: Path
    original_path: str
    path_type: str
    base_path: Path
    exists: bool
    is_file: bool
    is_dir: bool

    def __str__(self) -> str:
        """Return the string form of the resolved Path for logging or display."""
        return str(self.path)

    def __fspath__(self) -> str:
        """Return the filesystem path string for consumption by I/O APIs."""
        return str(self.path)

class PathResolutionError(Exception):
    """Raised when path resolution fails during config or path handling."""
    pass

def _expand_env_vars_in_path(path_str: str) -> str:
    """Expand environment variables in a path string to their values."""
    return os.path.expandvars(path_str)

def _detect_path_type(path_str: str) -> str:
    """Detect whether a path string is absolute or repo/project/current relative.

    Design Decision: Use prefixes to indicate path type:
    - Absolute paths start with / or drive letter (Windows)
    - ${REPO_ROOT}/... for repo-relative paths
    - ${PROJECT_ROOT}/... for project-relative paths
    - Everything else is relative to current directory
    """
    path_str = path_str.strip()

    # Check for absolute paths
    if Path(path_str).is_absolute():
        return PATH_TYPE_ABSOLUTE

    # Check for special prefixes
    if path_str.startswith("${REPO_ROOT}/") or path_str.startswith("${REPO_ROOT}\\"):
        return PATH_TYPE_RELATIVE_REPO
    elif path_str.startswith("${PROJECT_ROOT}/") or path_str.startswith("${PROJECT_ROOT}\\"):
        return PATH_TYPE_RELATIVE_PROJECT

    # Default to relative to current directory
    return PATH_TYPE_RELATIVE_CURRENT

def _get_base_path(path_type: str, project_path: Optional[Path] = None, repo_path: Optional[Path] = None) -> Path:
    """Return the base `Path` used to resolve a path of the given type."""
    if path_type == PATH_TYPE_ABSOLUTE:
        return Path("/")
    elif path_type == PATH_TYPE_RELATIVE_REPO:
        return repo_path or find_repo_root()
    elif path_type == PATH_TYPE_RELATIVE_PROJECT:
        return project_path or find_project_root()
    elif path_type == PATH_TYPE_RELATIVE_CURRENT:
        return Path.cwd()
    else:
        raise PathResolutionError(f"Unknown path type: {path_type}")

def resolve_path(path_str: str, project_path: Optional[Path] = None, repo_path: Optional[Path] = None) -> ResolvedPath:
    """Resolve a path string into a `ResolvedPath` using project/repo context.

    Supports absolute paths and special prefixes `${REPO_ROOT}` and `${PROJECT_ROOT}`.
    """
    if not path_str or not path_str.strip():
        raise PathResolutionError("Empty path string provided")

    # Expand environment variables
    expanded_path = _expand_env_vars_in_path(path_str)
    original_path = path_str

    # Detect path type
    path_type = _detect_path_type(expanded_path)

    # Get base path
    base_path = _get_base_path(path_type, project_path, repo_path)

    # Remove prefix if present
    if path_type == PATH_TYPE_RELATIVE_REPO:
        clean_path = expanded_path.replace("${REPO_ROOT}", "").lstrip("/\\")
    elif path_type == PATH_TYPE_RELATIVE_PROJECT:
        clean_path = expanded_path.replace("${PROJECT_ROOT}", "").lstrip("/\\")
    else:
        clean_path = expanded_path

    # Resolve the path
    if path_type == PATH_TYPE_ABSOLUTE:
        resolved_path = Path(clean_path)
    else:
        resolved_path = base_path / clean_path

    # Resolve any remaining relative components
    resolved_path = resolved_path.resolve()

    # Check if path exists and get metadata
    exists = resolved_path.exists()
    is_file = resolved_path.is_file() if exists else False
    is_dir = resolved_path.is_dir() if exists else False

    logger.debug(f"Resolved path '{original_path}' -> '{resolved_path}' (type: {path_type}, exists: {exists})")

    return ResolvedPath(
        path=resolved_path,
        original_path=original_path,
        path_type=path_type,
        base_path=base_path,
        exists=exists,
        is_file=is_file,
        is_dir=is_dir
    )

class ConfigMapping(TypedDict, total=False):
    """Typed mapping describing path-related configuration sections.

    - `directories`: mapping of logical directory names to relative/absolute paths
    - `workflow`: mapping of workflow-related filenames to paths
    - `scripts`: mapping of named script entries to path strings
    """
    directories: Dict[str, str]
    workflow: Dict[str, str]
    scripts: Dict[str, str]


def resolve_config_paths(config: ConfigMapping, project_path: Optional[Path] = None, repo_path: Optional[Path] = None) -> Dict[str, ResolvedPath]:
    """Recursively resolve path-like strings in `config` and return ResolvedPath map.

    Walks the provided configuration mapping and resolves any string that looks
    like a filesystem path into a `ResolvedPath`. The returned mapping keys
    are dotted keys describing the original location (e.g. ``config.directories.agent_files``).
    """
    resolved_paths = {}

    def _resolve_value(key_path: str, value: Any) -> Any:
        if isinstance(value, str):
            # Check if it looks like a path (contains / or \)
            if "/" in value or "\\" in value:
                try:
                    resolved = resolve_path(value, project_path, repo_path)
                    resolved_paths[key_path] = resolved
                    return str(resolved.path)
                except PathResolutionError as e:
                    logger.warning(f"Failed to resolve path '{value}' for '{key_path}': {e}")
                    return value
        elif isinstance(value, dict):
            return {k: _resolve_value(f"{key_path}.{k}", v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_resolve_value(f"{key_path}[{i}]", item) for i, item in enumerate(value)]
        return value

    # Resolve paths in config
    resolved_config = _resolve_value("config", config)

    return resolved_paths

def get_project_dirs(config: ConfigMapping, project_path: Path) -> Dict[str, Path]:
    """Return a mapping of canonical project directory names to absolute Paths.

    Uses `config['directories']` when present and falls back to sensible
    defaults under the provided `project_path`.
    """
    dirs_config = config.get('directories', {})

    # Default directory structure
    default_dirs = {
        'agent_files': 'agent_files',
        'agent_context': 'agent_context',
        'agent_log': 'agent_log',
        'artifacts': 'artifacts',
        'docs': 'docs',
        'input': 'input',
        'package': 'package',
        'scripts': 'scripts'
    }

    # Override with config values
    project_dirs = {}
    for dir_name, default_path in default_dirs.items():
        config_path = dirs_config.get(dir_name, default_path)
        try:
            resolved = resolve_path(config_path, project_path=project_path)
            project_dirs[dir_name] = resolved.path
        except PathResolutionError as e:
            logger.warning(f"Failed to resolve {dir_name} directory '{config_path}': {e}")
            # Fallback to default relative to project
            project_dirs[dir_name] = project_path / default_path

    return project_dirs

def get_workflow_paths(config: ConfigMapping, project_path: Path) -> Dict[str, Path]:
    """Return canonical workflow-related file Paths resolved relative to `project_path`.

    Ensures workflow file names are treated as project-relative when not
    explicitly absolute or prefixed with `${REPO_ROOT}`/`${PROJECT_ROOT}`.
    """
    workflow_config = config.get('workflow', {})

    # Default workflow paths
    default_paths = {
        'workflow_file': 'workflow.json',
        'agents_file': 'agents.json',
        'artifacts_file': 'artifacts.json',
        'instructions_file': 'instructions.json',
        'governance_file': 'governance.md'
    }

    workflow_paths = {}
    for file_name, default_path in default_paths.items():
        config_path = workflow_config.get(file_name, default_path)
        try:
            # For workflow files, treat relative paths as project-relative by default
            if not config_path.startswith(("${REPO_ROOT}", "${PROJECT_ROOT}", "/")) and not Path(config_path).is_absolute():
                config_path = f"${{PROJECT_ROOT}}/{config_path}"
            resolved = resolve_path(config_path, project_path=project_path)
            workflow_paths[file_name] = resolved.path
        except PathResolutionError as e:
            logger.warning(f"Failed to resolve {file_name} '{config_path}': {e}")
            # Fallback to default relative to project
            workflow_paths[file_name] = project_path / default_path

    return workflow_paths

def ensure_project_dirs_exist(project_dirs: Dict[str, Path]) -> None:
    """Create any missing project directories from the provided mapping."""
    for dir_name, dir_path in project_dirs.items():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_name}: {dir_path} - {e}")

def validate_project_structure(project_path: Path, config: ConfigMapping) -> List[str]:
    """Validate project directories and required workflow files, returning a list of issues."""
    issues: List[str] = []

    # Get expected directories
    project_dirs = get_project_dirs(config, project_path)

    # Check directories exist
    for dir_name, dir_path in project_dirs.items():
        if not dir_path.exists():
            issues.append(f"Missing directory: {dir_path}")
        elif not dir_path.is_dir():
            issues.append(f"Path exists but is not a directory: {dir_path}")

    # Get expected workflow files
    workflow_paths = get_workflow_paths(config, project_path)

    # Check workflow files exist (some may be optional)
    required_files = ['workflow_file', 'agents_file']
    for file_name in required_files:
        file_path = workflow_paths[file_name]
        if not file_path.exists():
            issues.append(f"Missing required file: {file_path}")

    return issues

def get_script_paths(config: ConfigMapping, repo_path: Optional[Path] = None) -> Dict[str, Path]:
    """Return resolved Paths for named CLI scripts declared in `config['scripts']`.

    If `repo_path` is omitted the repository root is located using the
    configuration service helper.
    """
    scripts_config = config.get('scripts', {})

    if repo_path is None:
        repo_path = find_repo_root()

    # Default script paths
    default_scripts = {
        'workflow_cli': 'scripts/workflow',
        'project_cli': 'projects/{project_name}/workflow',
        'validation_script': 'scripts/validation/validate_session.py'
    }

    script_paths = {}
    for script_name, default_path in default_scripts.items():
        config_path = scripts_config.get(script_name, default_path)
        try:
            resolved = resolve_path(config_path, repo_path=repo_path)
            script_paths[script_name] = resolved.path
        except PathResolutionError as e:
            logger.warning(f"Failed to resolve {script_name} script '{config_path}': {e}")
            # Fallback to default relative to repo
            script_paths[script_name] = repo_path / default_path

    return script_paths

# Utility functions for common path operations
def get_agent_file_path(project_dirs: Dict[str, Path], agent_id: str, file_type: str = 'md') -> Path:
    """Return the Path to an agent file inside the project's `agent_files` dir."""
    return project_dirs['agent_files'] / f"{agent_id}.{file_type}"

def get_artifact_path(project_dirs: Dict[str, Path], artifact_name: str) -> Path:
    """Return the Path to an artifact inside the project's `artifacts` dir."""
    return project_dirs['artifacts'] / artifact_name

def get_log_path(project_dirs: Dict[str, Path], log_type: str, timestamp: Optional[str] = None) -> Path:
    """Return the Path to a log file inside the project's `agent_log` directory."""
    if timestamp:
        return project_dirs['agent_log'] / f"{log_type}_{timestamp}.log"
    else:
        return project_dirs['agent_log'] / f"{log_type}.log"

def get_context_path(project_dirs: Dict[str, Path], context_type: str) -> Path:
    """Return the Path for a context JSON file inside `agent_context`."""
    return project_dirs['agent_context'] / f"{context_type}.json"