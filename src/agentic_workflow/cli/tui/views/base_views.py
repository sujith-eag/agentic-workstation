"""
Base view class for data presentation.

This module contains the base view functionality shared across
different view implementations.
"""

from abc import ABC, abstractmethod
from typing import Any
from rich.console import Console

console = Console()

__all__ = ["BaseView"]


class BaseView(ABC):
    """Base class for view components."""

    def __init__(self):
        self.console = console

    @abstractmethod
    def render(self, data: Any) -> None:
        """Render data to the console."""
        pass