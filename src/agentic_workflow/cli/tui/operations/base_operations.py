"""
Base operations class for business logic.

This module contains the base operations functionality shared across
different operation implementations.
"""

from abc import ABC, abstractmethod
from typing import Any

from ...utils import display_error, display_success

__all__ = ["BaseOperations"]


class BaseOperations(ABC):
    """Base class for operation handlers."""

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the operation. Subclasses should override with specific implementations."""
        raise NotImplementedError("Subclasses must implement execute method")

    def handle_error(self, error: Exception, operation: str) -> None:
        """Handle operation errors consistently."""
        display_error(f"Failed to {operation}: {error}")

    def handle_success(self, message: str) -> None:
        """Handle operation success consistently."""
        display_success(message)