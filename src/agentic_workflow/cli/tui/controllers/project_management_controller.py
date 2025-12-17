"""
Management controllers for TUI.

This module contains controllers for management operations.
"""

import questionary

from .base_controller import BaseController
from ...utils import display_error, display_info, display_success, display_warning


class ProjectManagementController(BaseController):
    """Controller for project management operations."""

    def execute(self, *args, **kwargs) -> None:
        """Execute project management menu."""
        display_info("Project Management")
        display_info("")

        # Get list of projects for selection
        try:
            # Use ProjectHandlers for listing projects
            from ...handlers import ProjectHandlers
            project_handlers = ProjectHandlers()
            
            # Get project data from handlers (same as list_projects)
            # We need to call the service method directly since handle_list displays output
            from agentic_workflow.services import ProjectService
            project_service = ProjectService()
            result = project_service.list_projects()
            projects = result['projects']

            if not projects:
                display_warning("No projects found to manage.")
                questionary.press_any_key_to_continue().ask()
                return

            # Project selection with descriptions
            project_choices = []
            for project in projects:
                desc = project.get('description', '')
                workflow = project.get('workflow', 'unknown')
                choice_text = f"{project['name']} ({workflow})"
                if desc:
                    choice_text += f" - {desc}"
                project_choices.append(choice_text)

            selected_choice = questionary.select(
                "Select project to manage:",
                choices=project_choices
            ).ask()

            # Extract project name from selection
            project_name = selected_choice.split(' (')[0]

            # Management actions
            action = questionary.select(
                f"Select action for '{project_name}':",
                choices=[
                    {"name": "View Project Status", "value": "status"},
                    {"name": "Remove Project", "value": "remove"},
                    {"name": "Cancel", "value": "cancel"}
                ]
            ).ask()

            if action == "status":
                self._show_project_status(project_name, project_service)
            elif action == "remove":
                self._remove_project(project_name)
            elif action == "cancel":
                return

        except Exception as e:
            display_error(f"Project management error: {e}")

        questionary.press_any_key_to_continue().ask()

    def _show_project_status(self, project_name: str, project_service) -> None:
        """Show status for a specific project."""
        try:
            # Get project status directly using the project service
            result = project_service.get_project_status(project_name)

            # Use the new view to render the project status
            from ..views import ProjectStatusView
            view = ProjectStatusView()
            view.render(result)

        except Exception as e:
            display_error(f"Failed to get project status: {e}")

    def _remove_project(self, project_name: str) -> None:
        """Remove a project."""
        confirm = questionary.confirm(
            f"Are you sure you want to remove project '{project_name}'? This action cannot be undone.",
            default=False
        ).ask()

        if confirm:
            try:
                self.app.project_handlers.handle_delete(project=project_name, force=False)
                display_success(f"Project '{project_name}' removed successfully!")
            except Exception as e:
                display_error(f"Failed to remove project: {e}")
        else:
            display_info("Project removal cancelled.")