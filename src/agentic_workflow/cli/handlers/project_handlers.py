"""
Project command handlers for Agentic Workflow CLI.

This module contains handlers for project-related commands like init, list, remove, status.
Extracted from the monolithic project.py for better maintainability.

Design Decision: Handlers accept keyword arguments directly instead of argparse.Namespace.
This allows the handlers to be used both from CLI (via Click) and programmatically (from services).
"""

from pathlib import Path
from typing import Optional, Dict, Any
import logging

from ...core.exceptions import (
    ProjectError, ProjectNotFoundError, ProjectValidationError,
    handle_error, validate_required
)
from ...services import ProjectService
from ...workflow import load_workflow
from ..utils import display_action_result, display_info, display_error, display_warning, display_project_summary, shorten_path
from agentic_workflow.core.paths import get_projects_dir

logger = logging.getLogger(__name__)


class ProjectHandlers:
    """Handlers for project-related CLI commands.
    
    All handler methods accept keyword arguments directly for clean integration
    with Click commands. No argparse.Namespace conversion required.
    """

    def __init__(self):
        self.project_service = ProjectService()

    def handle_init(
        self,
        name: str,
        workflow: Optional[str] = None,
        description: Optional[str] = None,
        force: bool = False
    ) -> None:
        """
        Handle project initialization command.

        Args:
            name: Project name (required)
            workflow: Workflow type to use (default: 'planning')
            description: Project description
            force: Overwrite existing project if True

        Raises:
            ProjectError: If initialization fails
        """
        try:
            validate_required(name, "name", "project_init")

            project_name = name
            workflow_type = workflow or 'planning'

            logger.info(f"Initializing project '{project_name}' with workflow '{workflow_type}'")

            # Validate project name (basic validation)
            if not project_name.replace('-', '').replace('_', '').isalnum():
                raise ProjectValidationError(
                    "Invalid project name. Use only letters, numbers, hyphens, and underscores.",
                    context={"project_name": project_name}
                )

            # Check if project already exists
            if self.project_service.project_exists(project_name) and not force:
                raise ProjectError(
                    f"Project '{project_name}' already exists. Use --force to overwrite.",
                    error_code="PROJECT_EXISTS",
                    context={"project_name": project_name}
                )

            # Initialize project
            result = self.project_service.initialize_project(
                project_name=project_name,
                workflow_type=workflow_type
            )

            # Create project configuration file
            projects_dir = Path(self.project_service.config.get('directories', {}).get('projects', 'projects'))
            project_path = projects_dir / project_name
            config_file = project_path / 'agentic.toml'

            project_config = {
                'name': project_name,
                'workflow': workflow_type,
                'description': description or f"Agentic workflow project: {project_name}",
                'created': str(Path.cwd()),
                'version': '1.0.0',
            }

            # Write TOML format
            toml_content = f"""name = "{project_config['name']}"
workflow = "{project_config['workflow']}"
description = "{project_config['description']}"
created = "{project_config['created']}"
version = "{project_config['version']}"
"""
            with open(config_file, 'w') as f:
                f.write(toml_content)

            # Display success with standardized formatting
            directories = result.get('directories_created', [])

            # Load workflow to get first agent information for next steps
            wf = load_workflow(workflow_type)
            first_agent_id = wf.pipeline_order[1] if len(wf.pipeline_order) > 1 else wf.pipeline_order[0]
            first_agent = wf.get_agent(first_agent_id)
            first_agent_name = first_agent.get('role', first_agent_id) if first_agent else first_agent_id

            next_steps = [
                f"cd {project_path}",
                f"./workflow activate {first_agent_id}  # Start with {first_agent_name}",
                "./workflow populate        # Generate agent files"
            ]

            display_project_summary(project_name, workflow_type, directories, next_steps)

        except Exception as e:
            handle_error(e, "project initialization", {"project_name": name})

    def handle_list(
        self,
        name: Optional[str] = None,
        output_format: str = 'table'
    ) -> None:
        """
        Handle project listing command.

        Args:
            name: Specific project name to show (optional)
            output_format: Output format - 'table', 'json', or 'yaml'

        Raises:
            ProjectError: If listing fails
        """
        try:
            logger.info("Listing projects" if not name else f"Showing project '{name}'")

            if name:
                # Show specific project details
                result = self.project_service.get_project_status(name)

                if result['status'] == 'found':
                    if result.get('config'):
                        self._format_project_output(result['config'], output_format, f"Project: {name}")
                    else:
                        display_warning(f"Project '{name}' found but no configuration available")
                        display_info(f"Location: {shorten_path(result.get('path', 'unknown'))}")
                else:
                    raise ProjectNotFoundError(f"Project '{name}' not found")
            else:
                # List all projects
                result = self.project_service.list_projects()

                if result['count'] > 0:
                    # Format as list for display
                    projects_data = result['projects']
                    self._format_projects_list(projects_data, output_format)
                else:
                    display_info("No projects found")
                    if result.get('message'):
                        display_info(f"Note: {result['message']}")

        except Exception as e:
            handle_error(e, "project listing", {"project_name": name})

    def handle_remove(
        self,
        name: str,
        force: bool = False
    ) -> None:
        """
        Handle project removal command.

        Args:
            name: Project name to remove (required)
            force: Force removal without confirmation

        Raises:
            ProjectError: If removal fails
        """
        try:
            validate_required(name, "name", "project_remove")

            logger.info(f"Removing project '{name}'")

            # Note: Confirmation logic should be handled in CLI command, not handler
            # This handler assumes confirmation has already been obtained

            result = self.project_service.remove_project(name, force)

            display_action_result(
                action=f"Project '{name}' removed successfully",
                success=True,
                details=[f"Location: {result.get('path', 'unknown')}"]
            )

        except Exception as e:
            handle_error(e, "project removal", {"project_name": name})

    def handle_status(self) -> None:
        """
        Handle project status command.

        Shows the status of the current project (detected from CWD).

        Raises:
            ProjectError: If status retrieval fails
        """
        try:
            logger.info("Getting current project status")

            result = self.project_service.get_project_status()

            if result['status'] == 'not_in_project':
                display_error("Not in a project directory")
                display_info("Use 'agentic project init <name>' to create a new project")
                return

            if result.get('config'):
                self._format_project_output(result['config'], 'table', "Current Project Status")
            else:
                display_warning("Project found but no configuration available")
                display_info(f"Location: {shorten_path(result.get('path', 'unknown'))}")

        except Exception as e:
            handle_error(e, "project status", {})

    def _format_project_output(self, project_data: Dict[str, Any], output_format: str, title: str) -> None:
        """Format project data for output."""
        if output_format == 'json':
            import json
            display_info(json.dumps(project_data, indent=2))
        elif output_format == 'yaml':
            import yaml
            display_info(yaml.dump(project_data, default_flow_style=False))
        else:  # table format
            display_info(f"\n{title}")
            display_info("=" * len(title))
            for key, value in project_data.items():
                if isinstance(value, dict):
                    display_info(f"{key}:")
                    for sub_key, sub_value in value.items():
                        display_info(f"  {sub_key}: {sub_value}")
                else:
                    display_info(f"{key}: {value}")
            display_info("")

    def _format_projects_list(self, projects: list, output_format: str) -> None:
        """Format projects list for output."""
        if output_format == 'json':
            import json
            display_info(json.dumps(projects, indent=2))
        elif output_format == 'yaml':
            import yaml
            display_info(yaml.dump(projects, default_flow_style=False))
        else:  # table format
            display_info("\nAvailable Projects")
            display_info("=" * 18)
            for project in projects:
                display_info(f"Name: {project['name']}")
                display_info(f"  Workflow: {project['workflow']}")
                display_info(f"  Description: {project['description']}")
                display_info("")