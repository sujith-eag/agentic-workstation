"""
Base controller classes for TUI menu navigation.

This module contains base controller functionality shared across
different menu controller implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

from ...utils import display_error, display_success


class BaseController(ABC):
    """Base class for menu controllers."""

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the controller's main logic."""
        pass

    def handle_error(self, error: Exception, operation: str) -> None:
        """Handle controller errors consistently."""
        display_error(f"Failed to {operation}: {error}")

    def handle_success(self, message: str) -> None:
        """Handle controller success consistently."""
        display_success(message)