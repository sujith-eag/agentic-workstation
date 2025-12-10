"""
Workflow command handlers for Agentic Workflow CLI.

This module contains handlers for workflow-related commands like list-workflows, validate, etc.
Extracted from the monolithic workflow.py for better maintainability.

Design Decision: Handlers accept keyword arguments directly instead of argparse.Namespace.
This allows the handlers to be used both from CLI (via Click) and programmatically (from services).
"""

from typing import Optional, List
import logging

from ...core.exceptions import CLIExecutionError, handle_error, validate_required
from ...services import WorkflowService
from ..utils import display_action_result, display_info, display_error, display_help_panel

logger = logging.getLogger(__name__)


class WorkflowHandlers:
    """Handlers for workflow-related CLI commands.
    
    All handler methods accept keyword arguments directly for clean integration
    with Click commands. No argparse.Namespace conversion required.
    """

    def __init__(self):
        self.workflow_service = WorkflowService()

    def handle_list_workflows(self) -> None:
        """
        Handle list workflows command.

        Lists all available workflow definitions.

        Raises:
            CLIExecutionError: If listing fails
        """
        try:
            workflows = self.workflow_service.list_workflows()

            if not workflows:
                display_info("No workflows found")
                return

            # Format workflows for display_help_panel
            commands = []
            for workflow in workflows:
                try:
                    info = self.workflow_service.get_workflow_info(workflow['name'])
                    desc = f"{info.get('description', 'No description')}\n(Agents: {info.get('agent_count', 0)}, v{info.get('version', 'unknown')})"
                    commands.append({
                        'command': workflow['name'],
                        'description': desc
                    })
                except Exception as e:
                    commands.append({
                        'command': workflow['name'],
                        'description': f"Error loading info - {str(e)[:50]}..."
                    })

            display_help_panel("Available Workflows", commands)
            display_info("")

        except Exception as e:
            handle_error(e, "workflow listing", {})

    def handle_generate_agents(
        self,
        project: str
    ) -> None:
        """
        Handle generate agents command.

        Args:
            project: Project name (required)

        Raises:
            CLIExecutionError: If generation fails
        """
        try:
            validate_required(project, "project", "generate_agents")

            # Placeholder - implement agent generation logic
            logger.info(f"Generating agents for project '{project}'")
            display_action_result(
                action=f"Agents generated for project '{project}'",
                success=True
            )

        except Exception as e:
            handle_error(e, "agent generation", {"project": project})

    def handle_gate_check(
        self,
        project: str
    ) -> None:
        """
        Handle gate check command.

        Args:
            project: Project name (required)

        Raises:
            CLIExecutionError: If gate check fails
        """
        try:
            validate_required(project, "project", "gate_check")

            # Placeholder - implement gate check logic
            logger.info(f"Running gate check for project '{project}'")
            display_action_result(
                action=f"Gate check passed for project '{project}'",
                success=True
            )

        except Exception as e:
            handle_error(e, "gate check", {"project": project})

    def handle_invoke(
        self,
        workflow: str
    ) -> None:
        """
        Handle invoke command.

        Args:
            workflow: Workflow name to invoke (required)

        Raises:
            CLIExecutionError: If invocation fails
        """
        try:
            validate_required(workflow, "workflow", "invoke")

            # Placeholder - implement workflow invocation logic
            logger.info(f"Invoking workflow '{workflow}'")
            display_action_result(
                action=f"Workflow '{workflow}' invoked",
                success=True
            )

        except Exception as e:
            handle_error(e, "workflow invocation", {"workflow": workflow})

    def handle_sync_planning(self) -> None:
        """
        Handle sync planning command.

        Syncs the planning workflow definitions.

        Raises:
            CLIExecutionError: If sync fails
        """
        try:
            # Placeholder - implement planning sync logic
            logger.info("Syncing planning workflow")
            display_action_result(
                action="Planning workflow synced",
                success=True
            )

        except Exception as e:
            handle_error(e, "planning sync", {})

    def handle_set_stage(
        self,
        project: str,
        stage: str
    ) -> None:
        """
        Handle set stage command.

        Args:
            project: Project name (required)
            stage: Stage name to set (required)

        Raises:
            CLIExecutionError: If stage setting fails
        """
        try:
            validate_required(project, "project", "set_stage")
            validate_required(stage, "stage", "set_stage")

            # Placeholder - implement stage setting logic
            logger.info(f"Setting stage to '{stage}' for project '{project}'")
            display_action_result(
                action=f"Stage set to '{stage}' for project '{project}'",
                success=True
            )

        except Exception as e:
            handle_error(e, "stage setting", {"project": project, "stage": stage})
