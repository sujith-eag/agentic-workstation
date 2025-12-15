"""
Workflow controllers for TUI.

This module contains controllers for workflow-related operations.
"""

from .base_controller import BaseController
from ...utils import display_error, display_info, display_warning


class WorkflowStatusController(BaseController):
    """Controller for workflow status display."""

    def execute(self, *args, **kwargs) -> None:
        """Execute workflow status display."""
        display_info("Workflow Status")
        display_info("")

        try:
            # Get project name from app context
            project_name = self.app.project_root.name if self.app.project_root else None
            
            # Use QueryHandlers for status display
            self.app.query_handlers.handle_status(project=project_name)

        except Exception as e:
            display_error(f"Failed to get workflow status: {e}")

        import questionary
        questionary.press_any_key_to_continue().ask()