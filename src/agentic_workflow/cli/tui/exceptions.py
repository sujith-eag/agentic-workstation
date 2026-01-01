"""TUI-specific exceptions.

This module defines exceptions specific to TUI operations that don't
fit into the core exception hierarchy.
"""

from agentic_workflow.core.exceptions import CLIError


class TUIError(CLIError):
    """Base exception for TUI-specific errors."""
    pass


class TUIInputError(TUIError):
    """User input was cancelled or invalid."""
    pass


class TUINavigationError(TUIError):
    """Navigation between menus failed."""
    pass


class TUIRenderError(TUIError):
    """Failed to render TUI component."""
    pass


__all__ = [
    "TUIError",
    "TUIInputError",
    "TUINavigationError",
    "TUIRenderError",
]
