"""
Display controllers for TUI.

This module contains controllers for displaying information.
"""

import sys
from pathlib import Path

from .base_controller import BaseController
from ...utils import display_info
from agentic_workflow import __version__


class SystemInfoController(BaseController):
    """Controller for system information display."""

    def execute(self, *args, **kwargs) -> None:
        """Execute system information display."""
        display_info("System Information")
        display_info("")

        # Get real system information
        # Count projects using ProjectService
        project_count = 0
        try:
            from agentic_workflow.services import ProjectService
            project_service = ProjectService()
            result = project_service.list_projects()
            project_count = result['count']
        except:
            project_count = 0  # fallback

        # Count workflows
        workflow_count = 0
        try:
            from agentic_workflow.services import WorkflowService
            workflow_service = WorkflowService()
            workflows = workflow_service.list_workflows()
            workflow_count = len(workflows)
        except:
            workflow_count = 4  # fallback

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
        view = SystemInfoView()
        view.render(system_data)

        import questionary
        questionary.press_any_key_to_continue().ask()