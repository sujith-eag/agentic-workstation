"""
Agent operations for TUI.

This module contains operation classes that handle agent-related
business logic for the TUI.
"""

from typing import Optional, Any
import questionary

from .base_operations import BaseOperations
from ...utils import display_success, display_error


class AgentOperations(BaseOperations):
    """Operations for managing agents in projects."""

    def execute(self, *args, **kwargs) -> Any:
        """Execute operation - not used directly, use specific methods instead."""
        raise NotImplementedError("Use specific agent operation methods instead")

    def execute_agent_activation(self, agent_id: str, project_name: str) -> bool:
        """Execute agent activation operation."""
        try:
            self.app.session_handlers.handle_activate(
                project=project_name,
                agent_id=agent_id
            )
            self.handle_success(f"Agent {agent_id} activated successfully!")
            return True
        except Exception as e:
            self.handle_error(e, f"agent {agent_id} activation")
            return False

    def execute_agent_handoff(self, from_agent: str, to_agent: str, project_name: str,
                            artifacts: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Execute agent handoff operation."""
        try:
            self.app.entry_handlers.handle_handoff(
                project=project_name,
                from_agent=from_agent,
                to_agent=to_agent,
                artifacts=artifacts if artifacts else None,
                notes=notes if notes else None
            )
            self.handle_success("Handoff recorded successfully!")
            return True
        except Exception as e:
            self.handle_error(e, "handoff recording")
            return False

    def execute_decision_recording(self, title: str, rationale: str, project_name: str,
                                 agent: Optional[str] = None) -> bool:
        """Execute decision recording operation."""
        try:
            self.app.entry_handlers.handle_decision(
                project=project_name,
                title=title,
                rationale=rationale,
                agent=agent if agent else None
            )
            self.handle_success("Decision recorded successfully!")
            return True
        except Exception as e:
            self.handle_error(e, "decision recording")
            return False

    def execute_workflow_end(self, project_name: str) -> bool:
        """Execute workflow end operation."""
        try:
            self.app.session_handlers.handle_end(project=project_name)
            self.handle_success("Workflow ended successfully!")
            return True
        except Exception as e:
            self.handle_error(e, "workflow end")
            return False

    def execute_agent_population(self, project_name: str) -> bool:
        """Execute agent template population operation."""
        try:
            self.app.session_handlers.handle_populate(project=project_name)
            self.handle_success("Agent frontmatter populated successfully!")
            return True
        except Exception as e:
            self.handle_error(e, "agent population")
            return False