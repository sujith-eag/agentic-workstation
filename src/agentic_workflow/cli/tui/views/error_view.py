"""
Error view for TUI.

This module contains views for displaying errors.
"""

from rich.console import Console
from rich.panel import Panel

console = Console()


class ErrorView:
    """View for displaying error messages."""

    def display_error_modal(self, message: str, title: str = "Error") -> None:
        """Display an error modal and wait for user input."""
        console.clear()
        error_panel = Panel(
            f"[bold white]{message}[/bold white]",
            title=f"[bold red]{title}[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print(error_panel)
        input("\nPress Enter to continue...")