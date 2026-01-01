"""
Workflow controllers for TUI.

This module contains controllers for workflow-related operations.
"""

import logging
from .base_controller import BaseController
from agentic_workflow.core.exceptions import ProjectError, WorkflowError

logger = logging.getLogger(__name__)


class WorkflowStatusController(BaseController):
    """Controller for workflow status display."""

    def __init__(self, project_handlers, **kwargs):
        """Initialize with required dependencies."""
        super().__init__(**kwargs)
        self.project_handlers = project_handlers

    def execute(self, *args, **kwargs) -> None:
        """Execute workflow status display."""
        self.feedback.info("Workflow Status")

        try:
            if not self.project_root:
                self.feedback.warning("Not in a project context.")
                return

            project_name = self.project_root.name
            status_data = self.project_handlers.get_project_status_data(project_name)

            from ..views import ProjectStatusView
            view = ProjectStatusView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(status_data)

        except (ProjectError, WorkflowError) as e:
            self.error_view.display_error_modal(f"Failed to get workflow status: {e}", title="Status Error")
        except Exception as e:
            logger.exception(f"Unexpected error getting workflow status: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise

        self.input_handler.wait_for_user()


__all__ = ["WorkflowStatusController"]
