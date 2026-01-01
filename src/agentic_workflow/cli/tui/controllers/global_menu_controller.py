"""
Global menu controller for TUI.

This module contains the controller for global context menu operations.
"""

from questionary import Choice
from typing import TYPE_CHECKING

from .base_controller import BaseController
from ..branding import display_branding_splash
from agentic_workflow.cli.theme import Theme
from ..ui import InputResult

if TYPE_CHECKING:
    from . import ProjectWizardController, ProjectManagementController, SystemInfoController
    from ...handlers import ProjectHandlers


class GlobalMenuController(BaseController):
    """Controller for global context menu operations."""

    def __init__(
        self,
        project_wizard_controller: 'ProjectWizardController',
        project_management_controller: 'ProjectManagementController',
        system_info_controller: 'SystemInfoController',
        project_handlers: 'ProjectHandlers',
        **kwargs
    ):
        """Initialize with controller dependencies."""
        super().__init__(**kwargs)
        self.project_wizard_controller = project_wizard_controller
        self.project_management_controller = project_management_controller
        self.system_info_controller = system_info_controller
        self.project_handlers = project_handlers

    def execute(self, *args, **kwargs) -> str:
        """Execute the global menu and return the selected action."""
        # Display the AGENTIC header
        display_branding_splash("Global", self.console, theme_map=self.theme.get_color_map())

        # Menu options
        choice = self.input_handler.get_selection(
            choices=[
                Choice(title="Create New Project", value="create"),
                Choice(title="List Existing Projects", value="list"),
                Choice(title="Manage Existing Project", value="manage"),
                Choice(title="System Information", value="info")
            ],
            message="Select an option:"
        )

        return choice

    def execute_create_project(self) -> bool:
        """Execute project creation wizard.
        
        Returns:
            True if project was created, False otherwise
        """
        return self.project_wizard_controller.execute()

    def execute_list_projects(self) -> None:
        """Execute project listing."""
        self.feedback.info("Existing Projects")
        self.feedback.info("")

        try:
            result = self.project_handlers.list_projects_data()

            # Use the new view to render the project list
            from ..views import ProjectListView
            view = ProjectListView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(result)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Unexpected error listing projects: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise

        self.input_handler.wait_for_user()

    def execute_manage_project(self) -> None:
        """Execute project management menu."""
        self.project_management_controller.execute()

    def execute_system_info(self) -> None:
        """Execute system information display."""
        self.system_info_controller.execute()

    def run_menu(self) -> None:
        """Run the complete global menu loop."""
        while True:
            result = self.execute()

            if result == InputResult.EXIT:
                self.feedback.success("Goodbye!")
                return  # Exit gracefully - let TUIApp handle cleanup
            elif result == "create":
                if self.execute_create_project():
                    # Project was created successfully, exit the TUI
                    self.feedback.success("Goodbye!")
                    return  # Exit gracefully - let TUIApp handle cleanup
            elif result == "list":
                self.execute_list_projects()
            elif result == "manage":
                self.execute_manage_project()
            elif result == "info":
                self.execute_system_info()
            # Continue the loop for any other case


__all__ = ["GlobalMenuController"]