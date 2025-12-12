"""
Base menu class for TUI navigation.

This module contains the base menu functionality shared across
different menu controllers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import questionary
from rich.console import Console

from ...utils import display_error, display_success, display_info, display_warning

console = Console()

__all__ = ["BaseMenu"]


class BaseMenu(ABC):
    """Base class for menu controllers."""

    def __init__(self, app):
        self.app = app
        self.console = console

    @abstractmethod
    def show(self) -> None:
        """Display the menu and handle user interaction."""
        pass

    def get_user_choice(self, message: str, choices: List[Dict[str, Any]]) -> Any:
        """Get user selection from a list of choices."""
        return questionary.select(message, choices=choices).ask()

    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Get user confirmation for an action."""
        return questionary.confirm(message, default=default).ask()

    def get_text_input(self, message: str, default: str = "") -> str:
        """Get text input from user."""
        return questionary.text(message, default=default).ask()

    def press_any_key_to_continue(self) -> None:
        """Wait for user to continue."""
        questionary.press_any_key_to_continue().ask()