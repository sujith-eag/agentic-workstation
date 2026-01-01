"""
Base action classes for the Command Pattern implementation.

This module defines the abstract base class for all actions in the TUI.

"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ui import InputHandler, FeedbackPresenter, ProgressPresenter


class BaseAction(ABC):
    """Abstract base class for all actions in the TUI.
    
    Uses pure dependency injection - no god object references.
    """

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
    ):
        """Initialize the action with dependencies.
        
        Args:
            input_handler: Input handler for user interactions
            feedback: Feedback presenter for messages
            progress: Progress presenter for spinners
        """
        self.input_handler = input_handler
        self.feedback = feedback
        self.progress = progress
        
        self.name = self.__class__.__name__.replace('Action', '').lower()
        self.description = self.get_description()

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get the display name for this action."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get the description for this action."""
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the action with the given context.

        Args:
            context: Dictionary containing execution context (project_name, etc.)

        Returns:
            True if action succeeded, False if failed, None if cancelled
        """
        pass


__all__ = ["BaseAction"]