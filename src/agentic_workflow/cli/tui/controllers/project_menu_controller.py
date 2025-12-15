"""
Project menu controller for TUI.

This module contains the controller for project context menu operations.
"""

import questionary
from rich.console import Console
from rich.panel import Panel

from .base_controller import BaseController
from ...utils import display_info, display_error
from ..views import DashboardView

console = Console()


class ProjectMenuController(BaseController):
    """Controller for project context menu operations."""

    def execute(self, *args, **kwargs) -> str:
        """Execute the project menu and return the selected action."""
        console.clear()

        project_name = self.app.project_root.name if self.app.project_root else "Unknown"

        # Fetch latest status and session data from services (stateless approach)
        try:
            # Get status from ProjectService
            from agentic_workflow.services import ProjectService, LedgerService
            project_service = ProjectService()
            ledger_service = LedgerService()
            
            status_result = {}
            status_data = project_service.get_project_status(project_name)
            if status_data.get('status') == 'found':
                status_result = status_data.get('config', {})
            
            # Get fresh session data from LedgerService
            session_data = ledger_service.get_active_session(project_name) or {}
            session_context = {
                'active_agent': session_data.get('agent_id'),
                'last_action': session_data.get('last_action', 'No recent activity')
            }
            
            # Get recent activity
            recent_activity = ledger_service.get_recent_activity(project_name, limit=5)
            
        except Exception:
            # If data fetch fails, use empty defaults
            status_result = {}
            session_context = {'active_agent': None, 'last_action': 'No recent activity'}
            recent_activity = []

        # Render dashboard with fresh data
        dashboard = DashboardView()
        dashboard.render(
            project_name=project_name,
            session_context=session_context,
            status=status_result,
            recent_activity=recent_activity
        )

        display_info("")

        # Menu options
        choice = questionary.select(
            "Select an option:",
            choices=[
                {"name": "View Workflow Status", "value": "status"},
                {"name": "Agent Operations", "value": "agents"},
                {"name": "List Pending Handoffs", "value": "list-pending"},
                {"name": "List Active Blockers", "value": "list-blockers"},
                {"name": "Artifact Management", "value": "artifacts"},
                {"name": "Project Navigation", "value": "navigate"},
                {"name": "Return to Global Mode", "value": "exit"}
            ],
            use_shortcuts=True
        ).ask()

        return choice

    def execute_workflow_status(self) -> None:
        """Execute workflow status display."""
        self.app.workflow_status_controller.execute()

    def execute_agent_operations(self) -> None:
        """Execute agent operations menu."""
        self.app.agent_operations_controller.run_menu()

    def execute_list_pending(self) -> None:
        """Execute list pending handoffs."""
        self.display_context_header("Pending Handoffs")
        
        project_name = self.app.project_root.name if self.app.project_root else "Unknown"
        try:
            self.app.query_handlers.handle_list_pending(project=project_name)
        except Exception as e:
            self.app.error_view.display_error_modal(str(e))
        
        questionary.press_any_key_to_continue().ask()

    def execute_list_blockers(self) -> None:
        """Execute list active blockers."""
        self.display_context_header("Active Blockers")
        
        project_name = self.app.project_root.name if self.app.project_root else "Unknown"
        try:
            self.app.query_handlers.handle_list_blockers(project=project_name)
        except Exception as e:
            self.app.error_view.display_error_modal(str(e))
        
        questionary.press_any_key_to_continue().ask()

    def execute_project_navigation(self) -> None:
        """Execute project navigation display."""
        # Assuming app has project_navigation_controller initialized
        if hasattr(self.app, 'project_navigation_controller'):
            self.app.project_navigation_controller.execute()
        else:
            display_error("Navigation controller not initialized.")
            questionary.press_any_key_to_continue().ask()

    def run_menu(self) -> str:
        """Run the complete project menu loop and return context change."""
        choice = self.execute()

        if choice == "status":
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
        elif choice == "exit":
            return "global"  # Signal context change
        
        return "project"  # Stay in project context