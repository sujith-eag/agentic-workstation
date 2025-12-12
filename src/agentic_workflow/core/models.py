"""
In-memory models for project generation and validation.
"""

from pydantic import BaseModel
from pathlib import Path
from typing import Dict, Any, List

__all__ = ["VirtualFile", "ProjectModel", "PipelineResult"]


class VirtualFile(BaseModel):
    """Represents a file to be created during initialization."""
    path: Path
    content: str
    is_template: bool = True


class ProjectModel(BaseModel):
    """In-memory representation of a project before commit."""
    name: str
    root_path: Path
    workflow_type: str
    context_data: Dict[str, Any]  # Data for template rendering


class PipelineResult(BaseModel):
    """Result of pipeline execution for UI rendering."""
    success: bool
    message: str
    created_files: List[Path]
    updated_files: List[Path]
    skipped_files: List[Path]
    target_path: Path