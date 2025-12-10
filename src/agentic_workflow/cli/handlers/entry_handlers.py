"""
Entry command handlers for Agentic Workflow CLI.

This module contains handlers for entry-related commands like handoff, decision, etc.
Extracted from the monolithic workflow.py for better maintainability.

Design Decision: Handlers accept keyword arguments directly instead of argparse.Namespace.
This allows the handlers to be used both from CLI (via Click) and programmatically (from services).
"""

from typing import Optional, List
import logging

from ...core.exceptions import CLIExecutionError, handle_error, validate_required
from ...services import LedgerService
from ..utils import display_action_result, display_success

logger = logging.getLogger(__name__)


class EntryHandlers:
    """Handlers for entry-related CLI commands.
    
    All handler methods accept keyword arguments directly for clean integration
    with Click commands. No argparse.Namespace conversion required.
    """

    def __init__(self):
        self.ledger_service = LedgerService()

    def handle_handoff(
        self,
        project: str,
        from_agent: str,
        to_agent: str,
        artifacts: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        Handle agent handoff command.

        Args:
            project: Project name (required)
            from_agent: Source agent ID (required)
            to_agent: Target agent ID (required)
            artifacts: Comma-separated artifact list
            notes: Handoff notes

        Raises:
            CLIExecutionError: If handoff fails
        """
        try:
            validate_required(project, "project", "handoff")
            validate_required(from_agent, "from_agent", "handoff")
            validate_required(to_agent, "to_agent", "handoff")

            artifact_list = None
            if artifacts:
                artifact_list = [art.strip() for art in artifacts.split(',')]

            # Validate handoff against workflow rules
            from ...validation.validate_ledger import validate_workflow_handoff
            workflow_errors = validate_workflow_handoff(project, from_agent, to_agent)
            if workflow_errors:
                error_msg = f"Workflow validation failed: {'; '.join(workflow_errors)}"
                raise CLIExecutionError(error_msg)

            logger.info(f"Recording handoff in project '{project}': {from_agent} -> {to_agent}")

            result = self.ledger_service.record_handoff(
                project_name=project,
                from_agent=from_agent,
                to_agent=to_agent,
                artifacts=artifact_list,
                notes=notes
            )

            display_action_result(
                action=f"Handoff recorded: {from_agent} -> {to_agent}",
                success=True,
                details=[f"Artifacts: {', '.join(artifact_list)}"] if artifact_list else None
            )

        except Exception as e:
            handle_error(e, "agent handoff", {
                "project": project,
                "from_agent": from_agent,
                "to_agent": to_agent
            })

    def handle_decision(
        self,
        project: str,
        title: str,
        rationale: str,
        agent: Optional[str] = None
    ) -> None:
        """
        Handle decision recording command.

        Args:
            project: Project name (required)
            title: Decision title (required)
            rationale: Decision rationale (required)
            agent: Agent ID (optional)

        Raises:
            CLIExecutionError: If decision recording fails
        """
        try:
            validate_required(project, "project", "decision")
            validate_required(title, "title", "decision")
            validate_required(rationale, "rationale", "decision")

            logger.info(f"Recording decision in project '{project}': {title}")

            result = self.ledger_service.record_decision(
                project_name=project,
                title=title,
                rationale=rationale,
                agent_id=agent
            )

            display_action_result(
                action=f"Decision recorded: {title}",
                success=True,
                details=[f"Agent: {agent}"] if agent else None
            )

        except Exception as e:
            handle_error(e, "decision recording", {"project": project, "title": title})

    def handle_feedback(
        self,
        project: str,
        target: str,
        severity: str,
        summary: str
    ) -> None:
        """
        Handle feedback recording command.

        Args:
            project: Project name (required)
            target: Feedback target (required)
            severity: Severity level (required)
            summary: Feedback summary (required)

        Raises:
            CLIExecutionError: If feedback recording fails
        """
        try:
            validate_required(project, "project", "feedback")
            validate_required(target, "target", "feedback")
            validate_required(severity, "severity", "feedback")
            validate_required(summary, "summary", "feedback")

            # Placeholder - implement feedback logic
            logger.info(f"Recording feedback for {target} in project '{project}'")
            display_success(f"Feedback recorded for {target}")

        except Exception as e:
            handle_error(e, "feedback recording", {"project": project, "target": target})

    def handle_iteration(
        self,
        project: str,
        trigger: str
    ) -> None:
        """
        Handle iteration recording command.

        Args:
            project: Project name (required)
            trigger: Iteration trigger (required)

        Raises:
            CLIExecutionError: If iteration recording fails
        """
        try:
            validate_required(project, "project", "iteration")
            validate_required(trigger, "trigger", "iteration")

            # Placeholder - implement iteration logic
            logger.info(f"Recording iteration in project '{project}': {trigger}")
            display_success(f"Iteration recorded: {trigger}")

        except Exception as e:
            handle_error(e, "iteration recording", {"project": project, "trigger": trigger})

    def handle_session(
        self,
        project: str,
        agent: str
    ) -> None:
        """
        Handle session context command.

        Args:
            project: Project name (required)
            agent: Agent ID (required)

        Raises:
            CLIExecutionError: If session recording fails
        """
        try:
            validate_required(project, "project", "session")
            validate_required(agent, "agent", "session")

            # Placeholder - implement session logic
            logger.info(f"Recording session context for {agent} in project '{project}'")
            display_success(f"Session context recorded for {agent}")

        except Exception as e:
            handle_error(e, "session recording", {"project": project, "agent": agent})

    def handle_assumption(
        self,
        project: str,
        text: str
    ) -> None:
        """
        Handle assumption recording command.

        Args:
            project: Project name (required)
            text: Assumption text (required)

        Raises:
            CLIExecutionError: If assumption recording fails
        """
        try:
            validate_required(project, "project", "assumption")
            validate_required(text, "text", "assumption")

            # Placeholder - implement assumption logic
            logger.info(f"Recording assumption in project '{project}': {text}")
            display_success(f"Assumption recorded")

        except Exception as e:
            handle_error(e, "assumption recording", {"project": project})

    def handle_blocker(
        self,
        project: str,
        title: str,
        description: str
    ) -> None:
        """
        Handle blocker recording command.

        Args:
            project: Project name (required)
            title: Blocker title (required)
            description: Blocker description (required)

        Raises:
            CLIExecutionError: If blocker recording fails
        """
        try:
            validate_required(project, "project", "blocker")
            validate_required(title, "title", "blocker")
            validate_required(description, "description", "blocker")

            # Placeholder - implement blocker logic
            logger.info(f"Recording blocker in project '{project}': {title}")
            display_success(f"Blocker recorded: {title}")

        except Exception as e:
            handle_error(e, "blocker recording", {"project": project, "title": title})
