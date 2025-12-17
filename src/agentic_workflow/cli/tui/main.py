"""
Text User Interface for Agentic Workflow OS
Provides interactive menus and guided workflows for better UX.
"""

import questionary
from pathlib import Path
import sys
from typing import Optional, Dict, Any

from ..utils import is_in_project, get_project_root, display_error, display_success, display_info, display_warning
from ..handlers import (
    ProjectHandlers,
    WorkflowHandlers,
    SessionHandlers,
    EntryHandlers,
    QueryHandlers
)
from agentic_workflow.core.exceptions import AgenticWorkflowError
from agentic_workflow import __version__


class TUIApp:
    """Main TUI Application Class"""

    def __init__(self, config=None):
        self.config = config
        self.current_context = "project" if config and config.is_project_context else "global"
        self.project_root = config.project.root_path if config and config.project else None
        # Note: session_context removed - controllers now fetch fresh data from services
        self.project_handlers = ProjectHandlers()
        self.workflow_handlers = WorkflowHandlers()
        self.session_handlers = SessionHandlers(config)
        self.entry_handlers = EntryHandlers()
        self.query_handlers = QueryHandlers()
        
        # Initialize operations
        from .operations import ArtifactOperations
        self.artifact_ops = ArtifactOperations(self)
        
        # Initialize controllers
        from .controllers import (
            GlobalMenuController, 
            ProjectMenuController,
            ProjectWizardController,
            ProjectManagementController,
            SystemInfoController,
            WorkflowStatusController,
            ProjectNavigationController,
            AgentOperationsController,
            ArtifactManagementController
        )
        self.global_menu_controller = GlobalMenuController(self)
        self.project_menu_controller = ProjectMenuController(self)
        self.project_wizard_controller = ProjectWizardController(self)
        self.project_management_controller = ProjectManagementController(self)
        self.system_info_controller = SystemInfoController(self)
        self.workflow_status_controller = WorkflowStatusController(self)
        self.project_navigation_controller = ProjectNavigationController(self)
        self.agent_operations_controller = AgentOperationsController(self)
        self.artifact_management_controller = ArtifactManagementController(self)

        # Initialize views
        from .views import ErrorView
        self.error_view = ErrorView()

    def run(self):
        """Main TUI loop"""
        try:
            while True:
                if self.current_context == "global":
                    self.global_menu_controller.run_menu()
                else:
                    new_context = self.project_menu_controller.run_menu()
                    if new_context == "global":
                        self.current_context = "global"
                        self.project_root = None
        except KeyboardInterrupt:
            display_info("Goodbye!")
            sys.exit(0)
        except AgenticWorkflowError as e:
            # Business Logic Errors (Governance, Config, etc.)
            self.error_view.display_error_modal(str(e), title="Operation Failed")
            # Return to main menu
            return
        except Exception as e:
            # Unexpected crashes
            self.error_view.display_error_modal(f"An unexpected error occurred:\n{str(e)}", title="Critical Error")
            raise
            sys.exit(1)

    def _list_projects(self):
        """List existing projects"""
        display_info("Existing Projects")
        display_info("")

        try:
            # Get project data directly from service
            from agentic_workflow.services import ProjectService
            project_service = ProjectService()
            result = project_service.list_projects()

            # Use the new view to render the project list
            from .views import ProjectListView
            view = ProjectListView()
            view.render(result)

        except Exception as e:
            display_error(f"Failed to list projects: {e}")

        questionary.press_any_key_to_continue().ask()


def main():
    """TUI entry point"""
    app = TUIApp()
    app.run()


if __name__ == "__main__":
    main()