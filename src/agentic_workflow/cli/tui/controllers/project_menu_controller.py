"""
Project menu controller for TUI.

This module contains the controller for project context menu operations.
"""

from questionary import Choice
from typing import TYPE_CHECKING

from .base_controller import BaseController
from ..branding import display_branding_splash
from ..ui import InputResult
from ..views import DashboardView
from ..types import ContextState
from ..error_handler import safe_fetch
from agentic_workflow.core.exceptions import ProjectError, WorkflowError

if TYPE_CHECKING:
    from . import WorkflowStatusController, AgentOperationsController, ArtifactManagementController, ProjectNavigationController


class ProjectMenuController(BaseController):
    """Controller for project context menu operations."""

    def __init__(
        self,
        workflow_status_controller: 'WorkflowStatusController',
        agent_operations_controller: 'AgentOperationsController',
        artifact_management_controller: 'ArtifactManagementController',
        project_navigation_controller: 'ProjectNavigationController',
        **kwargs
    ):
        """Initialize with controller dependencies."""
        super().__init__(**kwargs)
        self.workflow_status_controller = workflow_status_controller
        self.agent_operations_controller = agent_operations_controller
        self.artifact_management_controller = artifact_management_controller
        self.project_navigation_controller = project_navigation_controller

    def execute(self, *args, **kwargs) -> str:
        """Execute the project menu and return the selected action."""
        # Display AGENTIC header
        display_branding_splash("Project", self.console, theme_map=self.theme.get_color_map())

        project_name = self.project_root.name if self.project_root else "Unknown"

        # Fetch latest status and session data via handlers using safe_fetch
        dashboard_data = safe_fetch(
            lambda: self.query_handlers.get_dashboard_data(project_name),
            operation_name="fetch_dashboard_data",
            fallback_value={'status': {}, 'session_context': {'active_agent': None, 'last_action': 'No recent activity'}, 'recent_activity': []},
            expected_exceptions=(ProjectError, WorkflowError, KeyError)
        )
        
        status_result = dashboard_data.get('status', {})
        session_context = dashboard_data.get('session_context', {'active_agent': None, 'last_action': 'No recent activity'})
        recent_activity = dashboard_data.get('recent_activity', [])

        # Render dashboard with fresh data
        dashboard = DashboardView(console=self.console, theme_map=self.theme.dashboard_theme())
        dashboard.render(
            project_name=project_name,
            session_context=session_context,
            status=status_result,
            recent_activity=recent_activity
        )

        # Menu options
        choice = self.input_handler.get_selection(
            choices=[
                Choice(title="View Workflow Status", value="status"),
                Choice(title="Agent Operations", value="agents"),
                Choice(title="List Pending Handoffs", value="list-pending"),
                Choice(title="List Active Blockers", value="list-blockers"),
                Choice(title="Artifact Management", value="artifacts"),
                Choice(title="Project Navigation", value="navigate")
            ],
            message="Select an option:"
        )

        return choice

    def execute_workflow_status(self) -> None:
        """Execute workflow status display."""
        self.workflow_status_controller.execute()

    def execute_agent_operations(self) -> None:
        """Execute agent operations menu."""
        self.agent_operations_controller.run_menu()

    def execute_list_pending(self) -> None:
        """Execute list pending handoffs."""
        import logging
        logger = logging.getLogger(__name__)
        
        self.display_context_header("Pending Handoffs")
        
        project_name = self.project_root.name if self.project_root else "Unknown"
        try:
            self.query_handlers.handle_list_pending(project=project_name)
        except (ProjectError, WorkflowError) as e:
            self.error_view.display_error_modal(f"Failed to list pending handoffs: {e}", title="Handoff Error")
        except Exception as e:
            logger.exception(f"Unexpected error listing pending handoffs: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise
        
        self.input_handler.wait_for_user()

    def execute_list_blockers(self) -> None:
        """Execute list active blockers."""
        import logging
        logger = logging.getLogger(__name__)
        
        self.display_context_header("Active Blockers")
        
        project_name = self.project_root.name if self.project_root else "Unknown"
        try:
            self.query_handlers.handle_list_blockers(project=project_name)
        except (ProjectError, WorkflowError) as e:
            self.error_view.display_error_modal(f"Failed to list blockers: {e}", title="Blocker Error")
        except Exception as e:
            logger.exception(f"Unexpected error listing blockers: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise
        
        self.input_handler.wait_for_user()

    def execute_artifact_management(self) -> None:
        """Execute artifact management."""
        self.artifact_management_controller.execute()

    def execute_project_navigation(self) -> None:
        """Execute project navigation display."""
        self.project_navigation_controller.execute()

    def run_menu(self) -> ContextState:
        """Run the complete project menu loop and return context change."""
        choice = self.execute()

        if choice is None or choice == InputResult.EXIT:
            return ContextState.GLOBAL  # Exit project context on cancel/ctrl+C
        elif choice == "status":
            self.execute_workflow_status()
        elif choice == "agents":
            self.execute_agent_operations()
        elif choice == "list-pending":
            self.execute_list_pending()
        elif choice == "list-blockers":
            self.execute_list_blockers()
        elif choice == "artifacts":
            self.execute_artifact_management()
        elif choice == "navigate":
            self.execute_project_navigation()

        return ContextState.PROJECT  # Stay in project context


__all__ = ["ProjectMenuController"]