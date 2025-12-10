"""
Session command handlers for Agentic Workflow CLI.

This module contains handlers for session-related commands like init, activate, end, etc.
Extracted from the monolithic workflow.py for better maintainability.

Design Decision: Handlers accept keyword arguments directly instead of argparse.Namespace.
This allows the handlers to be used both from CLI (via Click) and programmatically (from services).
"""

from pathlib import Path
from typing import Optional, Dict, Any
import logging

from ...core.exceptions import (
    ProjectError, ProjectNotFoundError, CLIExecutionError,
    handle_error, validate_required, validate_path_exists
)
from ...services import ProjectService, WorkflowService
from ..utils import display_success, display_project_summary

logger = logging.getLogger(__name__)


class SessionHandlers:
    """Handlers for session-related CLI commands.
    
    All handler methods accept keyword arguments directly for clean integration
    with Click commands. No argparse.Namespace conversion required.
    """

    def __init__(self):
        self.project_service = ProjectService()
        self.workflow_service = WorkflowService()

    def handle_init(
        self,
        project: str,
        workflow: Optional[str] = None,
        description: Optional[str] = None,
        force: bool = False
    ) -> None:
        """
        Handle project initialization command.

        Args:
            project: Project name (required)
            workflow: Workflow type (default: 'planning')
            description: Project description
            force: Overwrite existing project if True

        Raises:
            CLIExecutionError: If initialization fails
        """
        try:
            validate_required(project, "project", "init")

            workflow_type = workflow or 'planning'

            logger.info(f"Initializing project '{project}' with workflow '{workflow_type}'")

            # Check if project already exists
            if self.project_service.project_exists(project):
                if not force:
                    raise ProjectError(
                        f"Project '{project}' already exists. Use --force to overwrite.",
                        error_code="PROJECT_EXISTS",
                        context={"project": project}
                    )
                logger.warning(f"Overwriting existing project '{project}'")

            # Initialize project
            result = self.project_service.initialize_project(
                project_name=project,
                workflow_type=workflow_type,
                description=description,
                force=force
            )

            logger.info(f"Successfully initialized project '{project}'")
            display_success(f"Project '{project}' initialized successfully")
            display_success(f"  - Workflow: {workflow_type}")
            display_success(f"  - Agents: {result.get('agent_count', 0)}")
            display_success(f"  - Directories: {result.get('directory_count', 0)}")

            # Display detailed project summary
            directories = result.get('directories_created', [
                'agent_files', 'agent_context', 'agent_log', 
                'artifacts', 'docs', 'input', 'package'
            ])
            
            # Get the first agent to activate (second in pipeline after orchestrator)
            first_agent = "A-01"  # default fallback
            try:
                manifest = self.workflow_service.get_workflow_manifest(workflow_type)
                pipeline = manifest.get('workflow', {}).get('pipeline', {}).get('order', [])
                if len(pipeline) > 1:
                    first_agent = pipeline[1]
            except Exception:
                pass  # Use default if workflow loading fails
            
            next_steps = [
                f"cd projects/{project}",
                "./workflow status", 
                f"./workflow activate {first_agent}"
            ]
            display_project_summary(project, workflow_type, directories, next_steps)

        except Exception as e:
            handle_error(e, "project initialization", {"project": project})

    def handle_refresh(
        self,
        project: str
    ) -> None:
        """
        Handle project refresh command.

        Args:
            project: Project name (required)

        Raises:
            CLIExecutionError: If refresh fails
        """
        try:
            validate_required(project, "project", "refresh")

            logger.info(f"Refreshing project '{project}'")

            # Check if project exists
            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(
                    f"Project '{project}' not found",
                    context={"project": project}
                )

            # Refresh project
            result = self.project_service.refresh_project(project)

            logger.info(f"Successfully refreshed project '{project}'")
            display_success(f"Project '{project}' refreshed successfully")
            display_success(f"  - Updated agents: {result.get('updated_agents', 0)}")
            display_success(f"  - Updated artifacts: {result.get('updated_artifacts', 0)}")

        except Exception as e:
            handle_error(e, "project refresh", {"project": project})

    def handle_activate(
        self,
        project: str,
        agent_id: str
    ) -> None:
        """
        Handle agent activation command.

        Args:
            project: Project name (required)
            agent_id: Agent ID to activate (required)

        Raises:
            CLIExecutionError: If activation fails
        """
        try:
            validate_required(project, "project", "activate")
            validate_required(agent_id, "agent_id", "activate")

            logger.info(f"Activating agent '{agent_id}' in project '{project}'")

            # Check if project exists
            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(
                    f"Project '{project}' not found",
                    context={"project": project}
                )

            # Activate agent
            result = self.project_service.activate_agent(project, agent_id)

            logger.info(f"Successfully activated agent '{agent_id}' in project '{project}'")
            display_success(f"Agent '{agent_id}' activated in project '{project}'")
            display_success(f"  - Role: {result.get('role', 'Unknown')}")
            display_success(f"  - Session ID: {result.get('session_id', 'N/A')}")

        except Exception as e:
            handle_error(e, "agent activation", {"project": project, "agent_id": agent_id})

    def handle_end(
        self,
        project: str
    ) -> None:
        """
        Handle session end command.

        Args:
            project: Project name (required)

        Raises:
            CLIExecutionError: If session end fails
        """
        try:
            validate_required(project, "project", "end")

            logger.info(f"Ending session for project '{project}'")

            # Check if project exists
            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(
                    f"Project '{project}' not found",
                    context={"project": project}
                )

            # End session
            result = self.project_service.end_session(project)

            logger.info(f"Successfully ended session for project '{project}'")
            display_success(f"Session ended for project '{project}'")
            display_success(f"  - Archived agents: {result.get('archived_agents', 0)}")
            display_success(f"  - Final status: {result.get('status', 'completed')}")

        except Exception as e:
            handle_error(e, "session end", {"project": project})

    def handle_populate(
        self,
        project: str
    ) -> None:
        """
        Handle agent frontmatter population command.

        Args:
            project: Project name (required)

        Raises:
            CLIExecutionError: If population fails
        """
        try:
            validate_required(project, "project", "populate")

            logger.info(f"Populating agent frontmatter for project '{project}'")

            # Check if project exists
            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(
                    f"Project '{project}' not found",
                    context={"project": project}
                )

            # Populate frontmatter
            result = self.project_service.populate_frontmatter(project)

            logger.info(f"Successfully populated frontmatter for project '{project}'")
            display_success(f"Agent frontmatter populated for project '{project}'")
            display_success(f"  - Processed agents: {result.get('processed_agents', 0)}")
            display_success(f"  - Updated files: {result.get('updated_files', 0)}")

        except Exception as e:
            handle_error(e, "frontmatter population", {"project": project})

    def handle_delete(
        self,
        project: str,
        force: bool = False
    ) -> None:
        """
        Handle project deletion command.

        Args:
            project: Project name (required)
            force: Skip confirmation if True

        Raises:
            CLIExecutionError: If deletion fails
        """
        try:
            validate_required(project, "project", "delete")

            logger.info(f"Deleting project '{project}'")

            # Check if project exists
            if not self.project_service.project_exists(project):
                raise ProjectNotFoundError(
                    f"Project '{project}' not found",
                    context={"project": project}
                )

            # Note: Confirmation should be handled by CLI command layer
            # Handler assumes caller has already confirmed if needed

            # Remove project
            self.project_service.remove_project(project)

            logger.info(f"Successfully deleted project '{project}'")
            display_success(f"Project '{project}' deleted successfully")

        except Exception as e:
            handle_error(e, "project deletion", {"project": project})
