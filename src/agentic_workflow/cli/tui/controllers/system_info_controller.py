"""
Display controllers for TUI.

This module contains controllers for displaying information.
"""

import sys
import logging
from pathlib import Path

from .base_controller import BaseController
from ..error_handler import safe_fetch
from agentic_workflow import __version__

logger = logging.getLogger(__name__)


class SystemInfoController(BaseController):
    """Controller for system information display."""

    def __init__(self, project_handlers, workflow_handlers, **kwargs):
        """Initialize with required dependencies."""
        super().__init__(**kwargs)
        self.project_handlers = project_handlers
        self.workflow_handlers = workflow_handlers

    def execute(self, *args, **kwargs) -> None:
        """Execute system information display."""
        self.feedback.info("System Information")

        # Get real system information with safe_fetch
        project_count = safe_fetch(
            lambda: self.project_handlers.list_projects_data().get('count', 0),
            operation_name="fetch_project_count",
            fallback_value=0,
            expected_exceptions=(Exception,)
        )

        # Count workflows
        workflow_count = safe_fetch(
            lambda: len(self.workflow_handlers.list_workflows_data()),
            operation_name="fetch_workflow_count",
            fallback_value=0,
            expected_exceptions=(Exception,)
        )

        # Prepare data for the view
        system_data = {
            'version': __version__,
            'python_version': f"{sys.version.split()[0]}",
            'platform': sys.platform,
            'project_count': project_count,
            'workflow_count': workflow_count,
            'working_directory': str(Path.cwd())
        }

        # Use the new view to render system information
        from ..views import SystemInfoView
        view = SystemInfoView(console=self.console, theme_map=self.theme.get_color_map())
        view.render(system_data)

        self.input_handler.wait_for_user()


__all__ = ["SystemInfoController"]