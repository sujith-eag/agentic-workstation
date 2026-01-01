"""
Workflow action classes for the Command Pattern implementation.

This module contains concrete action classes for agent operations.

Refactoring Status: Phase 3 - Pure DI (No self.app references)
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from questionary import Choice

from .base_action import BaseAction
from ..ui import InputResult
from ..error_handler import handle_tui_errors, safe_fetch

if TYPE_CHECKING:
    from ..ui import InputHandler, FeedbackPresenter, ProgressPresenter
    from ...handlers import SessionHandlers, EntryHandlers, QueryHandlers


class ActivateAgentAction(BaseAction):
    """Action for activating an agent."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        session_handlers: 'SessionHandlers',
    ):
        """Initialize with dependencies.
        
        Args:
            input_handler: Input handler for user input
            feedback: Feedback presenter for messages
            progress: Progress presenter for spinners
            session_handlers: Session handlers for agent operations
        """
        super().__init__(input_handler, feedback, progress)
        self.session_handlers = session_handlers

    @property
    def display_name(self) -> str:
        return "Activate Agent"

    def get_description(self) -> str:
        return "Activate an agent for the current workflow session"

    @handle_tui_errors("activate_agent", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the activate agent action."""
        project_name = context.get('project_name', 'Unknown')

        agent_id = self.input_handler.get_text("Enter agent ID to activate:")
        if agent_id == InputResult.EXIT or not agent_id:
            return None

        with self.progress.spinner(f"Activating agent {agent_id}..."):
            self.session_handlers.handle_activate(
                project=project_name,
                agent_id=agent_id
            )
        self.feedback.success(f"Agent {agent_id} activated successfully!")
        return True


class HandoffAction(BaseAction):
    """Action for recording agent handoffs."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        entry_handlers: 'EntryHandlers',
        query_handlers: 'QueryHandlers',
    ):
        """Initialize with dependencies."""
        super().__init__(input_handler, feedback, progress)
        self.entry_handlers = entry_handlers
        self.query_handlers = query_handlers

    @property
    def display_name(self) -> str:
        return "Record Agent Handoff"

    def get_description(self) -> str:
        return "Record a handoff between agents with artifacts and notes"

    @handle_tui_errors("record_handoff", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the handoff action."""
        project_name = context.get('project_name', 'Unknown')

        # Prefetch active agent via handler using safe_fetch
        active_agent = safe_fetch(
            lambda: self.query_handlers.get_active_session(project_name)['agent_id'],
            operation_name="fetch_active_agent_for_handoff",
            fallback_value="Unknown",
            expected_exceptions=(KeyError, TypeError, AttributeError)
        )

        # Pre-fill from_agent with active agent
        from_agent = self.input_handler.get_text("From agent ID:", default=active_agent)
        if from_agent == InputResult.EXIT:
            return None

        to_agent = self.input_handler.get_text(
            "To agent ID:",
            validate=lambda x: len(x.strip()) > 0 or "To agent ID is required"
        )
        if to_agent == InputResult.EXIT:
            return None

        artifacts = self.input_handler.get_text("Artifacts (comma-separated, optional):")
        if artifacts == InputResult.EXIT:
            return None

        notes = self.input_handler.get_text("Handoff notes (optional):")
        if notes == InputResult.EXIT:
            return None

        if from_agent and to_agent:
            with self.progress.spinner("Recording agent handoff..."):
                self.entry_handlers.handle_handoff(
                    project=project_name,
                    from_agent=from_agent,
                    to_agent=to_agent,
                    artifacts=artifacts if artifacts else None,
                    notes=notes if notes else None
                )
            self.feedback.success("Handoff recorded successfully!")
            return True
        return None


class DecisionAction(BaseAction):
    """Action for recording decisions."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        entry_handlers: 'EntryHandlers',
    ):
        """Initialize with dependencies."""
        super().__init__(input_handler, feedback, progress)
        self.entry_handlers = entry_handlers

    @property
    def display_name(self) -> str:
        return "Record Decision"

    def get_description(self) -> str:
        return "Record a decision with rationale"

    @handle_tui_errors("record_decision", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the decision action."""
        project_name = context.get('project_name', 'Unknown')

        title = self.input_handler.get_text(
            "Decision title:",
            validate=lambda x: len(x.strip()) > 0 or "Decision title is required"
        )
        if title == InputResult.EXIT:
            return None

        rationale = self.input_handler.get_text(
            "Decision rationale:",
            validate=lambda x: len(x.strip()) > 0 or "Decision rationale is required"
        )
        if rationale == InputResult.EXIT:
            return None

        agent = self.input_handler.get_text("Agent ID (optional):")
        if agent == InputResult.EXIT:
            return None

        if title and rationale:
            with self.progress.spinner("Recording decision..."):
                self.entry_handlers.handle_decision(
                    project=project_name,
                    title=title,
                    rationale=rationale,
                    agent=agent if agent else None
                )
            self.feedback.success("Decision recorded successfully!")
            return True
        return None


class FeedbackAction(BaseAction):
    """Action for recording feedback."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        entry_handlers: 'EntryHandlers',
    ):
        """Initialize with dependencies."""
        super().__init__(input_handler, feedback, progress)
        self.entry_handlers = entry_handlers

    @property
    def display_name(self) -> str:
        return "Record Feedback"

    def get_description(self) -> str:
        return "Record feedback on agents or artifacts"

    @handle_tui_errors("record_feedback", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the feedback action."""
        project_name = context.get('project_name', 'Unknown')

        target = self.input_handler.get_text("Feedback target (agent or artifact):")
        if target == InputResult.EXIT or not target:
            return None

        severity = self.input_handler.get_selection(
            choices=[
                Choice(title="Low", value="low"),
                Choice(title="Medium", value="medium"),
                Choice(title="High", value="high")
            ],
            message="Severity:"
        )
        if severity == InputResult.EXIT:
            return None

        summary = self.input_handler.get_text("Feedback summary:")
        if summary == InputResult.EXIT or not summary:
            return None

        if target and severity and summary:
            with self.progress.spinner("Recording feedback..."):
                self.entry_handlers.handle_feedback(
                    project=project_name,
                    target=target,
                    severity=severity,
                    summary=summary
                )
            self.feedback.success("Feedback recorded successfully!")
            return True
        return None


class BlockerAction(BaseAction):
    """Action for recording blockers."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        entry_handlers: 'EntryHandlers',
    ):
        """Initialize with dependencies."""
        super().__init__(input_handler, feedback, progress)
        self.entry_handlers = entry_handlers

    @property
    def display_name(self) -> str:
        return "Record Blocker"

    def get_description(self) -> str:
        return "Record workflow blockers and affected agents"

    @handle_tui_errors("record_blocker", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the blocker action."""
        project_name = context.get('project_name', 'Unknown')

        title = self.input_handler.get_text("Blocker title:")
        if title == InputResult.EXIT or not title:
            return None

        description = self.input_handler.get_text("Blocker description:")
        if description == InputResult.EXIT or not description:
            return None

        blocked_agents = self.input_handler.get_text("Blocked agents (comma-separated, optional):")
        if blocked_agents == InputResult.EXIT:
            return None

        if title and description:
            with self.progress.spinner("Recording blocker..."):
                self.entry_handlers.handle_blocker(
                    project=project_name,
                    title=title,
                    description=description,
                    blocked_agents=blocked_agents.split(',') if blocked_agents else None
                )
            self.feedback.success("Blocker recorded successfully!")
            return True
        return None


class IterationAction(BaseAction):
    """Action for recording iterations."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        entry_handlers: 'EntryHandlers',
    ):
        """Initialize with dependencies."""
        super().__init__(input_handler, feedback, progress)
        self.entry_handlers = entry_handlers

    @property
    def display_name(self) -> str:
        return "Record Iteration"

    def get_description(self) -> str:
        return "Record workflow iterations and version changes"

    @handle_tui_errors("record_iteration", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the iteration action."""
        project_name = context.get('project_name', 'Unknown')

        trigger = self.input_handler.get_text("What triggered this iteration:")
        if trigger == InputResult.EXIT or not trigger:
            return None

        impacted_agents = self.input_handler.get_text("Impacted agents (comma-separated):")
        if impacted_agents == InputResult.EXIT or not impacted_agents:
            return None

        description = self.input_handler.get_text("Iteration description:")
        if description == InputResult.EXIT or not description:
            return None

        version_bump = self.input_handler.get_selection(
            choices=[
                Choice(title="Patch", value="patch"),
                Choice(title="Minor", value="minor"),
                Choice(title="Major", value="major")
            ],
            message="Version bump:"
        )
        if version_bump == InputResult.EXIT:
            return None

        if trigger and impacted_agents and description and version_bump:
            with self.progress.spinner("Recording iteration..."):
                self.entry_handlers.handle_iteration(
                    project=project_name,
                    trigger=trigger,
                    impacted_agents=impacted_agents.split(','),
                    description=description,
                    version_bump=version_bump
                )
            self.feedback.success("Iteration recorded successfully!")
            return True
        return None


class AssumptionAction(BaseAction):
    """Action for recording assumptions."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        entry_handlers: 'EntryHandlers',
    ):
        """Initialize with dependencies."""
        super().__init__(input_handler, feedback, progress)
        self.entry_handlers = entry_handlers

    @property
    def display_name(self) -> str:
        return "Record Assumption"

    def get_description(self) -> str:
        return "Record workflow assumptions and their rationale"

    @handle_tui_errors("record_assumption", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the assumption action."""
        project_name = context.get('project_name', 'Unknown')

        assumption = self.input_handler.get_text("Assumption:")
        if assumption == InputResult.EXIT or not assumption:
            return None

        rationale = self.input_handler.get_text("Rationale:")
        if rationale == InputResult.EXIT or not rationale:
            return None

        if assumption and rationale:
            with self.progress.spinner("Recording assumption..."):
                self.entry_handlers.handle_assumption(
                    project=project_name,
                    assumption=assumption,
                    rationale=rationale
                )
            self.feedback.success("Assumption recorded successfully!")
            return True
        return None


class EndWorkflowAction(BaseAction):
    """Action for ending the workflow."""

    def __init__(
        self,
        input_handler: 'InputHandler',
        feedback: 'FeedbackPresenter',
        progress: 'ProgressPresenter',
        session_handlers: 'SessionHandlers',
    ):
        """Initialize with dependencies."""
        super().__init__(input_handler, feedback, progress)
        self.session_handlers = session_handlers

    @property
    def display_name(self) -> str:
        return "End Workflow"

    def get_description(self) -> str:
        return "End the current workflow session"

    @handle_tui_errors("end_workflow", fallback_value=False)
    def execute(self, context: Dict[str, Any]) -> Optional[bool]:
        """Execute the end workflow action."""
        project_name = context.get('project_name', 'Unknown')

        confirm = self.input_handler.get_confirmation("Are you sure you want to end the workflow?", default=False)
        if confirm == InputResult.EXIT:
            return None

        if confirm:
            with self.progress.spinner("Ending workflow session..."):
                self.session_handlers.handle_end(project=project_name)
            self.feedback.success("Workflow ended successfully!")
            return True
        return None


__all__ = [
    "ActivateAgentAction",
    "HandoffAction",
    "DecisionAction",
    "FeedbackAction",
    "BlockerAction",
    "IterationAction",
    "AssumptionAction",
    "EndWorkflowAction",
]