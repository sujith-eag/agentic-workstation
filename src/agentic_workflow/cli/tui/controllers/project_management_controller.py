"""
Management controllers for TUI.

This module contains controllers for management operations.
"""

import logging
from questionary import Choice

from .base_controller import BaseController
from ..ui import InputResult
from agentic_workflow.core.exceptions import ProjectError, FileSystemError

logger = logging.getLogger(__name__)


class ProjectManagementController(BaseController):
    """Controller for project management operations."""

    def __init__(self, project_handlers, **kwargs):
        """Initialize with required dependencies."""
        super().__init__(**kwargs)
        self.project_handlers = project_handlers

    def execute(self, *args, **kwargs) -> None:
        """Execute project management menu."""
        self.feedback.info("Project Management")

        # Get list of projects for selection
        try:
            projects_data = self.project_handlers.list_projects_data()
            projects = projects_data.get('projects', [])

            if not projects:
                self.feedback.warning("No projects found to manage.")
                return

            # Project selection with descriptions
            project_choices = []
            for project in projects:
                desc = project.get('description', '')
                workflow = project.get('workflow', 'unknown')
                choice_text = f"{project['name']} ({workflow})"
                if desc:
                    choice_text += f" - {desc}"
                project_choices.append(Choice(title=choice_text, value=project['name']))

            selected_project = self.input_handler.get_selection(
                choices=project_choices,
                message="Select project to manage:"
            )

            if selected_project is None or selected_project == InputResult.EXIT:
                return

            # Management actions
            action = self.input_handler.get_selection(
                choices=[
                    Choice(title="View Project Status", value="status"),
                    Choice(title="Remove Project", value="remove")
                ],
                message=f"Select action for '{selected_project}':"
            )

            if action is None or action == InputResult.EXIT:
                return

            if action == "status":
                self._show_project_status(selected_project)
            elif action == "remove":
                self._remove_project(selected_project)

        except (ProjectError, FileSystemError) as e:
            self.error_view.display_error_modal(f"Project management error: {e}", title="Project Error")
        except Exception as e:
            logger.exception(f"Unexpected error in project management: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise

    def _show_project_status(self, project_name: str) -> None:
        """Show status for a specific project."""
        try:
            result = self.project_handlers.get_project_status_data(project_name)

            # Use the new view to render the project status
            from ..views import ProjectStatusView
            view = ProjectStatusView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(result)
            self.input_handler.wait_for_user()

        except (ProjectError, FileSystemError) as e:
            self.error_view.display_error_modal(f"Failed to get project status: {e}", title="Status Error")
        except Exception as e:
            logger.exception(f"Unexpected error getting project status: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise

    def _remove_project(self, project_name: str) -> None:
        """Remove a project."""
        confirm = self.input_handler.get_confirmation(
            f"Are you sure you want to remove project '{project_name}'? This action cannot be undone.",
            default=False
        )

        if confirm == InputResult.EXIT:
            return

        if confirm:
            try:
                self.project_handlers.handle_delete(project=project_name, force=False)
                self.feedback.success(f"Project '{project_name}' removed successfully!")
                self.input_handler.wait_for_user()
            except (ProjectError, FileSystemError) as e:
                self.error_view.display_error_modal(f"Failed to remove project: {e}", title="Removal Error")
            except Exception as e:
                logger.exception(f"Unexpected error removing project: {e}")
                self.error_view.display_error_modal(f"Critical error: {e}", title="Critical Error")
                raise
        else:
            self.feedback.info("Project removal cancelled.")
            
__all__ = ["ProjectManagementController"]