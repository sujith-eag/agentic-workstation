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
from ..utils import display_success, display_project_summary, display_action_result, display_info

logger = logging.getLogger(__name__)


class SessionHandlers:
    """Handlers for session-related CLI commands.
    
    All handler methods accept keyword arguments directly for clean integration
    with Click commands. No argparse.Namespace conversion required.
    """

    def __init__(self, config=None):
        self.config = config
        self.project_service = ProjectService(config)
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

            # Initialize project using ProjectService
            result = self.project_service.init_project(
                project_name=project,
                workflow_name=workflow_type,
                description=description,
                force=force
            )
            
            logger.info(f"Successfully initialized project '{project}'")
            
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
                f"cd \"{result.target_path}\"",
                "./workflow status", 
                f"./workflow activate {first_agent}"
            ]
            
            # Get directories from workflow manifest
            directories = []
            try:
                manifest = self.workflow_service.get_workflow_manifest(workflow_type)
                workflow_dirs = manifest.get('workflow', {}).get('directories', {})
                
                # Extract directory names (exclude 'root' and 'templates' which are special)
                for key, value in workflow_dirs.items():
                    if key not in ['root', 'templates'] and isinstance(value, str):
                        # Remove any path prefixes like 'artifacts/', 'agent_files/', etc.
                        dir_name = value.rstrip('/')
                        directories.append(dir_name)
            except Exception:
                pass  # Use fallback if manifest loading fails
            
            # Fallback to default directories if none found
            if not directories:
                directories = [
                    "agent_files",
                    "agent_context", 
                    "agent_log",
                    "artifacts",
                    "docs",
                    "input",
                    "package"
                ]
            
            display_project_summary(project, workflow_type, directories, next_steps)
            
            # Display success message after the summary table
            display_success(f"Project '{project}' initialized successfully")
            display_success(f"  - Workflow: {workflow_type}")
            display_success(f"  - Location: {result.target_path}")
            display_success(f"  - Created: {len(result.created_files)} files")
            if result.updated_files:
                display_success(f"  - Updated: {len(result.updated_files)} files")
            if result.skipped_files:
                display_info(f"  - Skipped: {len(result.skipped_files)} files")

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
            display_success(f"  - Created: {len(result.created_files)} files")
            display_success(f"  - Updated: {len(result.updated_files)} files")
            if result.skipped_files:
                display_info(f"  - Skipped: {len(result.skipped_files)} files")

        except Exception as e:
            handle_error(e, "project refresh", {"project": project})

    def handle_activate(
        self,
        agent_id: str,
        project: Optional[str] = None
    ) -> None:
        """
        Handle agent activation command.

        Args:
            agent_id: Agent ID to activate (required)
            project: Project name (optional, auto-detected in project context)

        Raises:
            CLIExecutionError: If activation fails
        """
        try:
            validate_required(agent_id, "agent_id", "activate")
            
            # Auto-detect project if not provided
            if not project:
                if not self.config or not self.config.is_project_context:
                    raise CLIExecutionError("No project specified and not in project context")
                project = Path.cwd().name  # Use current directory name

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
            
            # Build status messages
            status_lines = []
            if result.get('stage_advanced'):
                status_lines.append(f"Stage advanced: {result.get('previous_stage')} → {result.get('current_stage')}")
            status_lines.extend([
                f"Role: {result.get('role', 'Unknown')}", 
                f"Session ID: {result.get('session_id', 'N/A')}"
            ])
            
            display_action_result(
                f"Agent '{agent_id}' activated in project '{project}'",
                True,
                status_lines
            )

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
            display_action_result(
                f"Session ended for project '{project}'",
                True,
                [f"Archived agents: {result.get('archived_agents', 0)}", 
                 f"Final status: {result.get('status', 'completed')}"]
            )

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

            # Populate frontmatter (now handled by refresh_project with agents=True)
            success = self.project_service.refresh_project(project, agents=True, docs=False, index=False, github=False, session=False)

            if not success:
                raise ProjectError(f"Failed to refresh agent files for project '{project}'")

            logger.info(f"Successfully populated frontmatter for project '{project}'")
            display_action_result(
                f"Agent frontmatter populated for project '{project}'",
                True
            )

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
            display_action_result(f"Project '{project}' deleted successfully", True)

        except Exception as e:
            handle_error(e, "project deletion", {"project": project})
