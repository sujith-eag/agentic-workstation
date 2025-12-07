"""Project metadata operations.

This module provides functions for loading and saving project metadata.
Eliminates duplicate implementations across session modules.

Usage:
    from core.project import load_project_meta, get_project_workflow_name
    
    meta = load_project_meta('myproject')
    workflow = get_project_workflow_name('myproject')
"""
from pathlib import Path
from typing import Dict, Optional, Any
import json

from .paths import get_projects_dir

# Project config filename (JSON format)
PROJECT_CONFIG_FILE = "project_config.json"


def get_project_dir(project_name: str) -> Path:
    """Get absolute path to project directory.
    
    Args:
        project_name: Name of the project.
        
    Returns:
        Path to the project directory (may not exist).
    """
    return get_projects_dir() / project_name


def project_exists(project_name: str) -> bool:
    """Check if a project exists.
    
    Args:
        project_name: Name of the project.
        
    Returns:
        True if project directory exists and has project_config.json.
    """
    project_dir = get_project_dir(project_name)
    return project_dir.exists() and (project_dir / PROJECT_CONFIG_FILE).exists()


def load_project_meta(project_name: str) -> Optional[Dict[str, Any]]:
    """Load project's workflow metadata from project_config.json.
    
    This is the canonical function for loading project metadata.
    Replaces duplicate implementations in:
    - session/gate_checker.py
    - session/invoke_agent.py
    - session/stage_manager.py
    - session/sync_planning.py
    - session/activate_agent.py
    - session/refresh_project.py
    
    Args:
        project_name: Name of the project.
        
    Returns:
        Dict containing project metadata, or None if not found.
    """
    project_dir = get_project_dir(project_name)
    config_file = project_dir / PROJECT_CONFIG_FILE
    
    if not config_file.exists():
        return None
    
    with open(config_file, 'r') as f:
        return json.load(f)


def save_project_meta(project_name: str, data: Dict[str, Any]) -> None:
    """Save project's workflow metadata to project_config.json.
    
    Args:
        project_name: Name of the project.
        data: Metadata dict to save.
        
    Raises:
        FileNotFoundError: If project directory doesn't exist.
    """
    project_dir = get_project_dir(project_name)
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")
    
    config_file = project_dir / PROJECT_CONFIG_FILE
    with open(config_file, 'w') as f:
        json.dump(data, f, indent=2)


def get_project_workflow_name(project_name: str) -> Optional[str]:
    """Get the workflow name for a project.
    
    Args:
        project_name: Name of the project.
        
    Returns:
        Workflow name (e.g., 'planning', 'implementation'), or None if not found.
    """
    meta = load_project_meta(project_name)
    if meta is None:
        return None
    return meta.get('workflow')


def get_project_stage(project_name: str) -> Optional[str]:
    """Get the current stage for a project (if workflow has stages).
    
    Args:
        project_name: Name of the project.
        
    Returns:
        Current stage name, or None if not applicable.
    """
    meta = load_project_meta(project_name)
    if meta is None:
        return None
    return meta.get('current_stage')


def update_project_meta(project_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update specific fields in project metadata.
    
    Args:
        project_name: Name of the project.
        updates: Dict of fields to update.
        
    Returns:
        Updated metadata dict.
        
    Raises:
        FileNotFoundError: If project doesn't exist.
    """
    meta = load_project_meta(project_name)
    if meta is None:
        raise FileNotFoundError(f"Project not found: {project_name}")
    
    meta.update(updates)
    save_project_meta(project_name, meta)
    return meta
