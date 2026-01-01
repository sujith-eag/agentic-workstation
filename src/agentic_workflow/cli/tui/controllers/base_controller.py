"""
Base controller classes for TUI menu navigation.

This module contains base controller functionality shared across
different menu controller implementations.

"""

from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING
from pathlib import Path

from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from agentic_workflow.cli.theme import Theme
from ..ui import LayoutManager, InputHandler, FeedbackPresenter
from ..error_handler import safe_fetch

if TYPE_CHECKING:
    from ..views.error_view import ErrorView
    from ...handlers import QueryHandlers


class BaseController(ABC):
    """Base class for menu controllers.
    
    Uses pure dependency injection - no god object references.
    """

    def __init__(
        self,
        console: Console,
        layout: LayoutManager,
        input_handler: InputHandler,
        feedback: FeedbackPresenter,
        error_view: 'ErrorView',
        query_handlers: 'QueryHandlers',
        project_root: Optional[Path],
        theme: Any,
    ):
        """Initialize the base controller with dependencies.
        
        Args:
            console: Console for output
            layout: Layout manager
            input_handler: Input handler
            feedback: Feedback presenter
            error_view: Error view for displaying errors
            query_handlers: Query handlers for fetching data
            project_root: Current project root path (None for global context)
            theme: Theme for styling
        """
        self.console = console
        self.layout = layout
        self.input_handler = input_handler
        self.feedback = feedback
        self.error_view = error_view
        self.query_handlers = query_handlers
        self.project_root = project_root
        self.theme = theme

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the controller's main logic."""
        pass

    def display_context_header(self, title: str) -> None:
        """Display a persistent context header with project and agent info."""
        header_theme = self.theme.header_theme()
        # Get project name
        project_name = "No Project"
        if self.project_root:
            project_name = self.project_root.name

        # Get active agent
        active_agent = "No Active Agent"
        if project_name != "No Project" and self.query_handlers:
            active_agent = safe_fetch(
                lambda: self.query_handlers.get_active_session(project_name)['agent_id'],
                operation_name="fetch_active_agent_for_header",
                fallback_value="No Active Agent",
                expected_exceptions=(KeyError, TypeError, AttributeError)
            )

        # Create header content
        header_text = Text()
        header_text.append("Agentic OS", style=header_theme.get("title", Theme.SECONDARY))
        header_text.append(" :: ", style=header_theme.get("accent", Theme.DIM))
        header_text.append(f"[Project: {project_name}]", style=header_theme.get("title", Theme.PRIMARY))
        header_text.append(" ", style=header_theme.get("accent", Theme.DIM))
        header_text.append(f"[Agent: {active_agent}]", style=header_theme.get("subtitle", Theme.SUCCESS))
        header_text.append(" :: ", style=header_theme.get("accent", Theme.DIM))
        header_text.append(title, style=header_theme.get("accent", Theme.ACCENT))

        # Create and display header panel
        header_panel = Panel(
            header_text,
            border_style=header_theme.get("border", Theme.BORDER),
            padding=(0, 1)
        )

        # Render header without an extra footer to avoid repeated navigation hints
        self.console.print(header_panel)
        self.console.print()


__all__ = ["BaseController"]