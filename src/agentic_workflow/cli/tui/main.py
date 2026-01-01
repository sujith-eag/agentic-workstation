"""
Text User Interface for Agentic Workflow OS
Provides interactive menus and guided workflows for better UX.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from rich.console import Console
from agentic_workflow.core.exceptions import WorkflowError, ProjectError

logger = logging.getLogger(__name__)

from ..handlers import (
    ProjectHandlers,
    WorkflowHandlers,
    SessionHandlers,
    EntryHandlers,
    QueryHandlers,
    ArtifactHandlers,
)
from agentic_workflow.cli.theme import Theme
from .ui import LayoutManager, InputHandler, FeedbackPresenter, ProgressPresenter
from agentic_workflow.core.exceptions import AgenticWorkflowError
from .types import ContextState
from .container import DependencyContainer


@dataclass
class TUIContext:
    """Shared UI dependencies for the TUI runtime."""

    console: Console
    layout: LayoutManager
    input_handler: InputHandler
    theme: Any
    feedback: FeedbackPresenter
    progress: ProgressPresenter


class TUIApp:
    """Main TUI Application Class"""

    def __init__(self, config=None, console: Optional[Console] = None):
        """Initialize the TUI application with configuration.
        
        Args:
            config: Runtime configuration
            console: Optional shared console instance (defaults to creating new one)
        """
        self.config = config
        self.current_context: ContextState = ContextState.PROJECT if config and config.is_project_context else ContextState.GLOBAL
        self.project_root = config.project.root_path if config and config.project else None
        
        # Initialize DependencyContainer (pass console for injection if provided)
        self.container = DependencyContainer(config, console=console)
        
        # Resolve ALL services from container (including handlers)
        self.console = self.container.resolve('console')
        self.layout = self.container.resolve('layout')
        self.input_handler = self.container.resolve('input_handler')
        self.theme = self.container.resolve('theme')
        self.feedback = self.container.resolve('feedback')
        self.progress = self.container.resolve('progress')
        self.error_view = self.container.resolve('error_view')
        
        # Resolve handlers from container (they are already registered with config)
        self.project_handlers = self.container.resolve('project_handlers')
        self.workflow_handlers = self.container.resolve('workflow_handlers')
        self.session_handlers = self.container.resolve('session_handlers')
        self.entry_handlers = self.container.resolve('entry_handlers')
        self.query_handlers = self.container.resolve('query_handlers')
        self.artifact_handlers = self.container.resolve('artifact_handlers')
        
        # Register project_root for runtime state (set after project selection)
        self.container.register_singleton('project_root', lambda: self.project_root)
        
        self.context = TUIContext(
            console=self.console,
            layout=self.layout,
            input_handler=self.input_handler,
            theme=self.theme,
            feedback=self.feedback,
            progress=self.progress,
        )
        
        # Initialize controllers with explicit dependencies
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
        
        # Create controllers using explicit DI
        controller_deps = {
            'console': self.console,
            'layout': self.layout,
            'input_handler': self.input_handler,
            'feedback': self.feedback,
            'error_view': self.error_view,
            'query_handlers': self.query_handlers,
            'project_root': self.project_root,
            'theme': self.theme,
        }
        
        # Create leaf controllers first (no dependencies on other controllers)
        self.project_wizard_controller = ProjectWizardController(
            session_handlers=self.session_handlers,
            workflow_handlers=self.workflow_handlers,
            progress=self.progress,
            **controller_deps
        )
        self.project_management_controller = ProjectManagementController(
            project_handlers=self.project_handlers,
            **controller_deps
        )
        self.system_info_controller = SystemInfoController(
            project_handlers=self.project_handlers,
            workflow_handlers=self.workflow_handlers,
            **controller_deps
        )
        self.workflow_status_controller = WorkflowStatusController(
            project_handlers=self.project_handlers,
            **controller_deps
        )
        self.project_navigation_controller = ProjectNavigationController(**controller_deps)
        
        # AgentOperationsController needs container for action creation
        self.agent_operations_controller = AgentOperationsController(
            container=self.container,
            **controller_deps
        )
        self.artifact_management_controller = ArtifactManagementController(
            artifact_handlers=self.artifact_handlers,
            progress=self.progress,
            **controller_deps
        )
        
        # Create menu controllers that depend on other controllers
        self.global_menu_controller = GlobalMenuController(
            project_wizard_controller=self.project_wizard_controller,
            project_management_controller=self.project_management_controller,
            system_info_controller=self.system_info_controller,
            project_handlers=self.project_handlers,
            **controller_deps
        )
        self.project_menu_controller = ProjectMenuController(
            workflow_status_controller=self.workflow_status_controller,
            agent_operations_controller=self.agent_operations_controller,
            artifact_management_controller=self.artifact_management_controller,
            project_navigation_controller=self.project_navigation_controller,
            **controller_deps
        )


    def run(self):
        """Main TUI loop"""
        try:
            if self.current_context == ContextState.GLOBAL:
                # Global menu handles its own loop and exits when done
                self.global_menu_controller.run_menu()
                return  # Exit after global menu completes
            else:
                # Project menu loop
                while True:
                    new_context = self.project_menu_controller.run_menu()
                    if new_context == ContextState.GLOBAL:
                        self.current_context = ContextState.GLOBAL
                        self.project_root = None
                        break  # Go back to global
        except KeyboardInterrupt:
            self.feedback.info("Goodbye!")
            return  # Exit gracefully
        except SystemExit:
            # Handle SystemExit from menu cancellation
            return
        except AgenticWorkflowError as e:
            # Business Logic Errors (Governance, Config, etc.)
            logger.error(f"Business logic error in TUI: {e}")
            self.error_view.display_error_modal(str(e), title="Operation Failed")
            # Return to main menu
            return
        except Exception as e:
            # Unexpected crashes - log with full traceback
            logger.exception(f"Critical unexpected error in TUI: {e}")
            self.error_view.display_error_modal(f"An unexpected error occurred:\n{str(e)}", title="Critical Error")
            raise

    def _list_projects(self):
        """List existing projects"""
        self.feedback.info("Existing Projects")
        self.feedback.info("")

        try:
            result = self.project_handlers.list_projects_data()

            # Use the new view to render the project list
            from .views import ProjectListView
            view = ProjectListView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(result)

        except (ProjectError, WorkflowError) as e:
            logger.error(f"Failed to list projects: {e}")
            self.error_view.display_error_modal(f"Failed to list projects: {e}", title="Project List Error")
        except Exception as e:
            logger.exception(f"Unexpected error listing projects: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise

        self.input_handler.wait_for_user()


def main():
    """TUI entry point"""
    app = TUIApp()
    app.run()


if __name__ == "__main__":
    main()


__all__ = ["TUIApp", "TUIContext", "main"]
