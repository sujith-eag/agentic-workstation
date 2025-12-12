"""
Workflow controllers for TUI.

This module contains controllers for workflow-related operations.
"""

from rich.table import Table
from rich.console import Console

from .base_controller import BaseController
from ...utils import display_error, display_info, display_warning

console = Console()


class WorkflowStatusController(BaseController):
    """Controller for workflow status display."""

    def execute(self, *args, **kwargs) -> None:
        """Execute workflow status display."""
        display_info("Workflow Status")
        display_info("")

        try:
            # Get project status directly from service
            from ...services import ProjectService
            project_service = ProjectService()
            result = project_service.get_project_status()

            if result['status'] == 'not_in_project':
                display_error("Not in a project directory")
                display_info("Use 'Create New Project' to create a new project")
            elif result.get('config'):
                # Format project status in a nice table
                config = result['config']
                table = Table()
                table.add_column("Property", style="cyan", no_wrap=True)
                table.add_column("Value", style="yellow")

                for key, value in config.items():
                    if isinstance(value, dict):
                        table.add_row(key, str(value))
                    else:
                        table.add_row(key, str(value))

                console.print(table)
            else:
                display_warning("Project found but no configuration available")

        except Exception as e:
            display_error(f"Failed to get workflow status: {e}")

        import questionary
        questionary.press_any_key_to_continue().ask()