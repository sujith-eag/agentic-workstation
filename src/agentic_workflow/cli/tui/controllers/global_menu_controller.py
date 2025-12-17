"""
Global menu controller for TUI.

This module contains the controller for global context menu operations.
"""

import questionary
from rich.console import Console
from rich.panel import Panel

from .base_controller import BaseController
from ...utils import display_info

console = Console()


class GlobalMenuController(BaseController):
    """Controller for global context menu operations."""

    def execute(self, *args, **kwargs) -> str:
        """Execute the global menu and return the selected action."""
        console.clear()

        # Header
        header = Panel.fit(
            "[bold blue]Agentic Workflow OS - Global Mode[/bold blue]\n"
            "[dim]Project Management & Creation[/dim]",
            border_style="blue"
        )
        console.print(header)
        display_info("")

        # Menu options
        choice = questionary.select(
            "Select an option:",
            choices=[
                {"name": "Create New Project", "value": "create"},
                {"name": "List Existing Projects", "value": "list"},
                {"name": "Manage Existing Project", "value": "manage"},
                {"name": "System Information", "value": "info"},
                {"name": "Exit", "value": "exit"}
            ],
            use_shortcuts=True
        ).ask()

        return choice

    def execute_create_project(self) -> None:
        """Execute project creation wizard."""
        self.app.project_wizard_controller.execute()

    def execute_list_projects(self) -> None:
        """Execute project listing."""
        self.app._list_projects()

    def execute_manage_project(self) -> None:
        """Execute project management menu."""
        self.app.project_management_controller.execute()

    def execute_system_info(self) -> None:
        """Execute system information display."""
        self.app.system_info_controller.execute()

    def run_menu(self) -> None:
        """Run the complete global menu loop."""
        choice = self.execute()

        if choice == "create":
            self.execute_create_project()
        elif choice == "list":
            self.execute_list_projects()
        elif choice == "manage":
            self.execute_manage_project()
        elif choice == "info":
            self.execute_system_info()
        elif choice == "exit":
            import sys
            sys.exit(0)