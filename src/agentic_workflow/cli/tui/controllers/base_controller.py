"""
Base controller classes for TUI menu navigation.

This module contains base controller functionality shared across
different menu controller implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

from rich.panel import Panel
from rich.text import Text

from ...utils import display_error, display_success


class BaseController(ABC):
    """Base class for menu controllers."""

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the controller's main logic."""
        pass

    def display_context_header(self, title: str) -> None:
        """Display a persistent context header with project and agent info."""
        # Get project name
        project_name = "No Project"
        if self.app.project_root:
            project_name = self.app.project_root.name

        # Get active agent
        active_agent = "No Active Agent"
        try:
            from agentic_workflow.services import LedgerService
            ledger_service = LedgerService()
            session_data = ledger_service.get_active_session(project_name)
            if session_data and session_data.get('agent_id'):
                active_agent = session_data['agent_id']
        except Exception:
            # If we can't get session data, keep default
            pass

        # Create header content
        header_text = Text()
        header_text.append("Agentic OS", style="bold blue")
        header_text.append(" :: ", style="dim")
        header_text.append(f"[Project: {project_name}]", style="bold cyan")
        header_text.append(" ", style="dim")
        header_text.append(f"[Agent: {active_agent}]", style="bold green")
        header_text.append(" :: ", style="dim")
        header_text.append(title, style="bold yellow")

        # Create and display header panel
        header_panel = Panel(
            header_text,
            border_style="blue",
            padding=(0, 1)
        )

        # Import console here to avoid circular imports
        from rich.console import Console
        console = Console()
        console.print(header_panel)
        console.print()  # Add spacing

    def handle_error(self, error: Exception, operation: str) -> None:
        """Handle controller errors consistently."""
        display_error(f"Failed to {operation}: {error}")

    def handle_success(self, message: str) -> None:
        """Handle controller success consistently."""
        display_success(message)