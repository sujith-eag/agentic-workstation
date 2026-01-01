"""
Project command handlers for Agentic Workflow CLI.
Focus: Static project management (List, Delete).
"""

from typing import Optional, Dict, Any
import logging
from pathlib import Path

from ...core.exceptions import (
    ProjectError, ProjectNotFoundError, 
    handle_error, validate_required
)
from ...core.paths import find_project_root
from agentic_workflow.services import ProjectService
from ..formatting import shorten_path
from ..display import display_action_result, display_info, display_warning, display_table
from rich.console import Console

logger = logging.getLogger(__name__)

class ProjectHandlers:
    """Handlers for static project management."""

    def __init__(self, console: Console):
        """Initialize the ProjectHandlers with required services."""
        self.console = console
        self.project_service = ProjectService()

    # --- TUI-friendly helpers (data only, no display) ---
    def list_projects_data(self) -> Dict[str, Any]:
        """Return raw project listing data without rendering."""
        return self.project_service.list_projects()

    def get_project_status_data(self, project_name: str) -> Dict[str, Any]:
        """Return raw project status data without rendering."""
        return self.project_service.get_project_status(project_name)

    def handle_list(
        self,
        name: Optional[str] = None,
        output_format: str = 'table'
    ) -> None:
        """Handle project listing command."""
        try:
            logger.info("Listing projects" if not name else f"Showing project '{name}'")

            if name:
                # Show specific project details
                result = self.project_service.get_project_status(name)
                if result['status'] == 'found':
                    if result.get('config'):
                        self._format_project_output(result['config'], output_format, f"Project: {name}")
                    else:
                        display_warning(f"Project '{name}' found but no configuration available", self.console)
                        display_info(f"Location: {shorten_path(result.get('path', 'unknown'), project_root=find_project_root(), cwd=Path.cwd())}", self.console)
                else:
                    raise ProjectNotFoundError(f"Project '{name}' not found")
            else:
                # List all projects
                result = self.project_service.list_projects()
                if result['count'] > 0:
                    self._format_projects_list(result['projects'], output_format)
                else:
                    display_info("No projects found", self.console)

        except Exception as e:
            handle_error(e, "project listing", {"project_name": name})

    def handle_delete(
        self,
        project: str,
        force: bool = False
    ) -> None:
        """Handle project deletion (Renamed from remove for consistency)."""
        try:
            validate_required(project, "project", "delete")

            # Check existence first
            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(f"Project '{project}' not found")

            logger.info(f"Deleting project '{project}'")

            # Execute deletion
            result = self.project_service.remove_project(project, force)

            display_action_result(
                action=f"Project '{project}' deleted successfully",
                success=True,
                console=self.console,
                details=[f"Location: {result.get('path', 'unknown')}"]
            )

        except Exception as e:
            handle_error(e, "project deletion", {"project": project})

    def _format_project_output(self, project_data: Dict[str, Any], output_format: str, title: str) -> None:
        """Format project data for output."""
        if output_format in ('json', 'yaml'):
            # For single project, wrap in list for display_table
            display_table([project_data], self.console, title=title, format_type=output_format)
        else:
            # Convert nested dict to flat format for table display
            flat_data = []
            for key, value in project_data.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flat_data.append({'Property': f"{key}.{sub_key}", 'Value': str(sub_value)})
                else:
                    flat_data.append({'Property': key, 'Value': str(value)})
            display_table(flat_data, self.console, title=title, columns=['Property', 'Value'])

    def _format_projects_list(self, projects: list, output_format: str) -> None:
        """Format projects list for output."""
        display_table(
            data=projects,
            console=self.console,
            title="Available Projects",
            columns=['name', 'workflow', 'description'],
            format_type=output_format
        )


__all__ = ["ProjectHandlers"]