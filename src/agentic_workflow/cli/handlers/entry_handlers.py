"""
Entry command handlers for Agentic Workflow CLI.

This module contains handlers for entry-related commands like handoff, decision, etc.
Extracted from the monolithic workflow.py for better maintainability.
"""

import argparse
from typing import Optional, List
import logging

from ...core.exceptions import CLIExecutionError, handle_error, validate_required
from ...services import LedgerService
from ..utils import display_success
from ..utils import display_action_result

logger = logging.getLogger(__name__)


class EntryHandlers:
    """Handlers for entry-related CLI commands."""

    def __init__(self):
        self.ledger_service = LedgerService()

    def handle_handoff(self, args: argparse.Namespace) -> None:
        """
        Handle agent handoff command.

        Args:
            args: Parsed command line arguments

        Raises:
            CLIExecutionError: If handoff fails
        """
        try:
            validate_required(args.project, "project", "handoff")
            validate_required(args.from_agent, "from_agent", "handoff")
            validate_required(args.to_agent, "to_agent", "handoff")

            project_name = args.project
            from_agent = args.from_agent
            to_agent = args.to_agent
            artifacts = getattr(args, 'artifacts', None)
            notes = getattr(args, 'notes', None)

            if artifacts:
                artifacts = [art.strip() for art in artifacts.split(',')]

            # Validate handoff against workflow rules
            from ...validation.validate_ledger import validate_workflow_handoff
            workflow_errors = validate_workflow_handoff(project_name, from_agent, to_agent)
            if workflow_errors:
                error_msg = f"Workflow validation failed: {'; '.join(workflow_errors)}"
                raise CLIExecutionError(error_msg)

            logger.info(f"Recording handoff in project '{project_name}': {from_agent} -> {to_agent}")

            result = self.ledger_service.record_handoff(
                project_name=project_name,
                from_agent=from_agent,
                to_agent=to_agent,
                artifacts=artifacts,
                notes=notes
            )

            display_action_result(
                action=f"Handoff recorded: {from_agent} -> {to_agent}",
                success=True,
                details=[f"Artifacts: {', '.join(artifacts)}"] if artifacts else None
            )

        except Exception as e:
            handle_error(e, "agent handoff", {
                "project": getattr(args, 'project', None),
                "from_agent": getattr(args, 'from_agent', None),
                "to_agent": getattr(args, 'to_agent', None)
            })

    def handle_decision(self, args: argparse.Namespace) -> None:
        """
        Handle decision recording command.

        Args:
            args: Parsed command line arguments

        Raises:
            CLIExecutionError: If decision recording fails
        """
        try:
            validate_required(args.project, "project", "decision")
            validate_required(args.title, "title", "decision")
            validate_required(args.rationale, "rationale", "decision")

            project_name = args.project
            title = args.title
            rationale = args.rationale
            agent_id = getattr(args, 'agent', None)

            logger.info(f"Recording decision in project '{project_name}': {title}")

            result = self.ledger_service.record_decision(
                project_name=project_name,
                title=title,
                rationale=rationale,
                agent_id=agent_id
            )

            display_action_result(
                action=f"Decision recorded: {title}",
                success=True,
                details=[f"Agent: {agent_id}"] if agent_id else None
            )

        except Exception as e:
            handle_error(e, "decision recording", {
                "project": getattr(args, 'project', None),
                "title": getattr(args, 'title', None)
            })

    def handle_feedback(self, args: argparse.Namespace) -> None:
        """
        Handle feedback recording command.

        Args:
            args: Parsed command line arguments

        Raises:
            CLIExecutionError: If feedback recording fails
        """
        try:
            validate_required(args.project, "project", "feedback")
            validate_required(args.target, "target", "feedback")
            validate_required(args.severity, "severity", "feedback")
            validate_required(args.summary, "summary", "feedback")

            # Placeholder - implement feedback logic
            logger.info(f"Recording feedback for {args.target} in project '{args.project}'")
            display_success(f"Feedback recorded for {args.target}")

        except Exception as e:
            handle_error(e, "feedback recording", {
                "project": getattr(args, 'project', None),
                "target": getattr(args, 'target', None)
            })

    def handle_iteration(self, args: argparse.Namespace) -> None:
        """
        Handle iteration recording command.

        Args:
            args: Parsed command line arguments

        Raises:
            CLIExecutionError: If iteration recording fails
        """
        try:
            validate_required(args.project, "project", "iteration")
            validate_required(args.trigger, "trigger", "iteration")

            # Placeholder - implement iteration logic
            logger.info(f"Recording iteration in project '{args.project}': {args.trigger}")
            display_success(f"Iteration recorded: {args.trigger}")

        except Exception as e:
            handle_error(e, "iteration recording", {
                "project": getattr(args, 'project', None),
                "trigger": getattr(args, 'trigger', None)
            })

    def handle_session(self, args: argparse.Namespace) -> None:
        """
        Handle session context command.

        Args:
            args: Parsed command line arguments

        Raises:
            CLIExecutionError: If session recording fails
        """
        try:
            validate_required(args.project, "project", "session")
            validate_required(args.agent, "agent", "session")

            # Placeholder - implement session logic
            logger.info(f"Recording session context for {args.agent} in project '{args.project}'")
            display_success(f"Session context recorded for {args.agent}")

        except Exception as e:
            handle_error(e, "session recording", {
                "project": getattr(args, 'project', None),
                "agent": getattr(args, 'agent', None)
            })

    def handle_assumption(self, args: argparse.Namespace) -> None:
        """
        Handle assumption recording command.

        Args:
            args: Parsed command line arguments

        Raises:
            CLIExecutionError: If assumption recording fails
        """
        try:
            validate_required(args.project, "project", "assumption")
            validate_required(args.text, "text", "assumption")

            # Placeholder - implement assumption logic
            logger.info(f"Recording assumption in project '{args.project}': {args.text}")
            display_success(f"Assumption recorded")

        except Exception as e:
            handle_error(e, "assumption recording", {
                "project": getattr(args, 'project', None)
            })

    def handle_blocker(self, args: argparse.Namespace) -> None:
        """
        Handle blocker recording command.

        Args:
            args: Parsed command line arguments

        Raises:
            CLIExecutionError: If blocker recording fails
        """
        try:
            validate_required(args.project, "project", "blocker")
            validate_required(args.title, "title", "blocker")
            validate_required(args.description, "description", "blocker")

            # Placeholder - implement blocker logic
            logger.info(f"Recording blocker in project '{args.project}': {args.title}")
            display_success(f"Blocker recorded: {args.title}")

        except Exception as e:
            handle_error(e, "blocker recording", {
                "project": getattr(args, 'project', None),
                "title": getattr(args, 'title', None)
            })
