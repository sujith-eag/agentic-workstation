"""
Agent operations controller for TUI.

This module contains the controller for agent operations menu.
Uses DependencyContainer to create actions with proper dependencies.
"""

from questionary import Choice
from typing import TYPE_CHECKING

from .base_controller import BaseController
from ..actions import (
    ActivateAgentAction,
    HandoffAction,
    DecisionAction,
    FeedbackAction,
    BlockerAction,
    IterationAction,
    AssumptionAction,
    EndWorkflowAction,
)
from ..ui import InputResult

if TYPE_CHECKING:
    from ..container import DependencyContainer


class AgentOperationsController(BaseController):
    """Controller for agent operations menu."""

    def __init__(self, container: 'DependencyContainer', **kwargs):
        """Initialize the agent operations controller.
        
        Args:
            container: Dependency injection container for creating actions
            **kwargs: Controller dependencies (console, layout, etc.)
        """
        super().__init__(**kwargs)
        self.container = container
        
        # Create actions using dependency injection from container
        input_handler = self.container.resolve('input_handler')
        feedback = self.container.resolve('feedback')
        progress = self.container.resolve('progress')
        session_handlers = self.container.resolve('session_handlers')
        entry_handlers = self.container.resolve('entry_handlers')
        query_handlers = self.container.resolve('query_handlers')
        
        self.actions = {
            'activate': ActivateAgentAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                session_handlers=session_handlers
            ),
            'handoff': HandoffAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                entry_handlers=entry_handlers,
                query_handlers=query_handlers
            ),
            'decision': DecisionAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                entry_handlers=entry_handlers
            ),
            'feedback': FeedbackAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                entry_handlers=entry_handlers
            ),
            'blocker': BlockerAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                entry_handlers=entry_handlers
            ),
            'iteration': IterationAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                entry_handlers=entry_handlers
            ),
            'assumption': AssumptionAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                entry_handlers=entry_handlers
            ),
            'end': EndWorkflowAction(
                input_handler=input_handler,
                feedback=feedback,
                progress=progress,
                session_handlers=session_handlers
            ),
        }

    def execute(self, *args, **kwargs) -> None:
        """Execute the agent operations menu."""
        self.run_menu()

    def run_menu(self) -> None:
        """Run the agent operations menu."""
        while True:  # Loop to allow retry on failure
            self.display_context_header("Agent Operations")
            project_name = self.project_root.name if self.project_root else "Unknown"

            # FIXED: Use the dictionary KEY as the value to ensure lookup succeeds
            choices = [
                Choice(title=action.display_name, value=key)
                for key, action in self.actions.items()
            ]

            # Agent operations menu
            choice = self.input_handler.get_selection(
                choices=choices,
                message="Select agent operation:"
            )

            if choice == InputResult.EXIT or choice is None:
                return  # Cancelled - exit to project menu

            # Dispatch
            if choice in self.actions:
                context = {'project_name': project_name}
                result = self.actions[choice].execute(context)
                
                if result is False:
                    # Action failed - stay in menu for retry
                    self.feedback.warning("Operation failed. Please try again or select a different option.")
                    self.input_handler.wait_for_user()
                    continue  # Re-show menu
                elif result is True:
                    # Action succeeded - return to project menu
                    self.input_handler.wait_for_user()
                    return
                else:
                    # Action cancelled (None) - return to project menu
                    return


__all__ = ["AgentOperationsController"]