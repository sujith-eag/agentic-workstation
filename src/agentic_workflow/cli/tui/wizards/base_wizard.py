"""
Base wizard class for guided workflows.

This module contains the base wizard functionality shared across
different wizard implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from rich.console import Console

from ...utils import display_error, display_success, display_info, display_warning

console = Console()

__all__ = ["BaseWizard"]


class BaseWizard(ABC):
    """Base class for wizard workflows."""

    def __init__(self, app):
        self.app = app
        self.console = console

    @abstractmethod
    def run(self) -> Any:
        """Execute the wizard workflow."""
        pass

    def validate_input(self, value: str, field_name: str) -> Optional[str]:
        """Validate user input. Return error message or None if valid."""
        if not value or not value.strip():
            return f"{field_name} cannot be empty"
        return None

    def show_progress(self, message: str) -> None:
        """Show progress message."""
        display_info(message)

    def show_success(self, message: str) -> None:
        """Show success message."""
        display_success(message)

    def show_error(self, message: str) -> None:
        """Show error message."""
        display_error(message)