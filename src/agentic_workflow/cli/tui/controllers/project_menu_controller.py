"""
Project menu controller for TUI.

This module contains the controller for project context menu operations.
"""

import questionary
from rich.console import Console
from rich.panel import Panel

from .base_controller import BaseController
from ...utils import display_info

console = Console()


class ProjectMenuController(BaseController):
    """Controller for project context menu operations."""

    def execute(self, *args, **kwargs) -> str:
        """Execute the project menu and return the selected action."""
        console.clear()

        project_name = self.app.project_root.name if self.app.project_root else "Unknown"

        # Header
        header = Panel.fit(
            f"[bold green]Agentic Workflow OS - Project: {project_name}[/bold green]\n"
            "[dim]Workflow Operations & Agent Management[/dim]",
            border_style="green"
        )
        console.print(header)
        display_info("")

        # Menu options
        choice = questionary.select(
            "Select an option:",
            choices=[
                {"name": "View Workflow Status", "value": "status"},
                {"name": "Agent Operations", "value": "agents"},
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

    def execute_artifact_management(self) -> None:
        """Execute artifact management."""
        self.app.artifact_management_controller.run_menu()

    def run_menu(self) -> str:
        """Run the complete project menu loop and return context change."""
        choice = self.execute()

        if choice == "status":
            self.execute_workflow_status()
        elif choice == "agents":
            self.execute_agent_operations()
        elif choice == "artifacts":
            self.execute_artifact_management()
        elif choice == "navigate":
            self.execute_project_navigation()
        elif choice == "exit":
            return "global"  # Signal context change
        
        return "project"  # Stay in project context