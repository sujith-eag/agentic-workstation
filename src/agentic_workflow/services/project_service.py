"""
Project service for Agentic Workflow Platform.

This service handles project-related operations like initialization,
activation, and management.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
import yaml

# Use tomllib for TOML files (Python 3.11+), fallback to tomli for older versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ..core.exceptions import (
    ProjectError, ProjectNotFoundError, ProjectValidationError,
    validate_required, validate_path_exists
)
from ..core.config_service import ConfigurationService
from ..core.project_generation import create_project_from_workflow

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project operations."""

    def __init__(self):
        self.config_service = ConfigurationService()
        # Initial config load, will be refreshed per command context if needed
        # But for now, we assume standard load. 
        # Ideally, we should pass 'project_path' if known, but for __init__ we don't know it yet.
        # We can lazy load or dynamic load.
        # The existing code did `get_config_for_command()` which auto-detected project root.
        # Our load_config() does similar detection if path is None.
        self.config = self.config_service.load_config()

    def project_exists(self, project_name: str) -> bool:
        """
        Check if a project exists.

        Args:
            project_name: Name of the project

        Returns:
            True if project exists, False otherwise
        """
        validate_required(project_name, "project_name", "project_exists")

        from ..core.path_resolution import find_repo_root
        repo_root = find_repo_root()
        projects_dir = repo_root / self.config.get('directories', {}).get('projects', 'projects')
        project_path = projects_dir / project_name
        return project_path.exists() and project_path.is_dir()

    def initialize_project(
        self,
        project_name: str,
        workflow_type: str = 'planning',
        description: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize a new project.

        Args:
            project_name: Name of the project
            workflow_type: Type of workflow to use
            force: Whether to overwrite existing project

        Returns:
            Dictionary with initialization results

        Raises:
            ProjectError: If initialization fails
        """
        validate_required(project_name, "project_name", "initialize_project")
        validate_required(workflow_type, "workflow_type", "initialize_project")

        try:
            logger.info(f"Initializing project '{project_name}' with workflow '{workflow_type}'")

            # Create project using existing logic
            projects_dir = Path(self.config.get('directories', {}).get('projects', 'projects'))
            project_path = projects_dir / project_name

            # Create project from workflow
            merged_config = create_project_from_workflow(workflow_type, project_name, project_path)

            # Initialize session files and project structure
            try:
                from ..session.init_project import init_project
                init_project(project_name, workflow_type, description)
                logger.info(f"Initialized session files for project '{project_name}'")
            except Exception as e:
                logger.warning(f"Failed to initialize session files: {e}")

            return {
                'project_name': project_name,
                'workflow_type': workflow_type,
                'agent_count': len(merged_config.get('agents', {})),
                'directory_count': len(merged_config.get('directories', {})),
                'directories_created': merged_config.get('directories_created', []),
                'status': 'initialized'
            }

        except Exception as e:
            logger.error(f"Failed to initialize project '{project_name}': {e}")
            raise ProjectError(
                f"Project initialization failed: {e}",
                context={'project_name': project_name, 'workflow_type': workflow_type},
                cause=e
            )

    def refresh_project(self, project_name: str) -> Dict[str, Any]:
        """
        Refresh an existing project.

        Args:
            project_name: Name of the project

        Returns:
            Dictionary with refresh results

        Raises:
            ProjectError: If refresh fails
        """
        validate_required(project_name, "project_name", "refresh_project")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        # Placeholder - implement refresh logic
        logger.info(f"Refreshing project '{project_name}'")
        return {
            'project_name': project_name,
            'updated_agents': 0,
            'updated_artifacts': 0,
            'status': 'refreshed'
        }

    def activate_agent(self, project_name: str, agent_id: str) -> Dict[str, Any]:
        """
        Activate an agent in a project.

        Args:
            project_name: Name of the project
            agent_id: ID of the agent to activate

        Returns:
            Dictionary with activation results

        Raises:
            ProjectError: If activation fails
        """
        validate_required(project_name, "project_name", "activate_agent")
        validate_required(agent_id, "agent_id", "activate_agent")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        from ..core.path_resolution import find_repo_root
        repo_root = find_repo_root()
        projects_dir = repo_root / self.config.get('directories', {}).get('projects', 'projects')
        project_path = projects_dir / project_name

        if not project_path.exists():
             raise ProjectNotFoundError(f"Project directory '{project_name}' not found at {project_path}")

        from ..core.session_manager import SessionManager
        try:
            manager = SessionManager(project_path)
            manager.activate_agent(agent_id)
        except Exception as e:
            raise ProjectError(f"Activation failed: {e}", cause=e)

        return {
            'project_name': project_name,
            'agent_id': agent_id,
            'status': 'activated'
        }

    def end_session(self, project_name: str) -> Dict[str, Any]:
        """
        End the current session for a project.

        Args:
            project_name: Name of the project

        Returns:
            Dictionary with session end results

        Raises:
            ProjectError: If session end fails
        """
        validate_required(project_name, "project_name", "end_session")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        # Placeholder - implement session end logic
        logger.info(f"Ending session for project '{project_name}'")
        return {
            'project_name': project_name,
            'archived_agents': 0,
            'status': 'completed'
        }

    def populate_frontmatter(self, project_name: str) -> Dict[str, Any]:
        """
        Populate agent frontmatter from manifest data.

        Args:
            project_name: Name of the project

        Returns:
            Dictionary with population results

        Raises:
            ProjectError: If population fails
        """
        validate_required(project_name, "project_name", "populate_frontmatter")

        if not self.project_exists(project_name):
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        # Placeholder - implement frontmatter population logic
        logger.info(f"Populating frontmatter for project '{project_name}'")
        return {
            'project_name': project_name,
            'processed_agents': 0,
            'updated_files': 0,
            'status': 'completed'
        }

    def _load_project_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Load project config from either TOML or JSON file.
        
        Args:
            config_path: Path to config file (without extension)
            
        Returns:
            Config data dict, or empty dict if file not found
        """
        # Try TOML first (preferred format)
        toml_file = config_path.with_suffix('.toml')
        if toml_file.exists():
            try:
                with open(toml_file, 'rb') as f:
                    return tomllib.load(f)
            except Exception as e:
                logger.warning(f"Failed to load TOML config {toml_file}: {e}")
        
        # Try JSON (agentic.json)
        json_file = config_path.with_suffix('.json')
        if json_file.exists():
            try:
                import json
                with open(json_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load JSON config {json_file}: {e}")
        
        # Try legacy project_config.json for backward compatibility
        legacy_json_file = config_path.parent / 'project_config.json'
        if legacy_json_file.exists():
            try:
                import json
                with open(legacy_json_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load legacy config {legacy_json_file}: {e}")
        
        return {}
    
    def list_projects(self) -> Dict[str, Any]:
        """
        List all available projects with their metadata.

        Returns:
            Dictionary containing project list and metadata

        Raises:
            ProjectError: If listing fails
        """
        try:
            logger.info("Listing all projects")

            projects_dir = Path(self.config.get('directories', {}).get('projects', 'projects'))
            projects = []

            if not projects_dir.exists():
                return {
                    'projects': [],
                    'count': 0,
                    'message': 'No projects directory found'
                }

            for item in projects_dir.iterdir():
                if item.is_dir():
                    config_data = self._load_project_config(item / 'agentic')
                    
                    if config_data:
                        projects.append({
                            'name': item.name,
                            'workflow': config_data.get('workflow', 'unknown'),
                            'description': config_data.get('description', ''),
                            'created': config_data.get('created', 'unknown'),
                            'version': config_data.get('version', 'unknown')
                        })
                    else:
                        # No config file found, but directory exists
                        projects.append({
                            'name': item.name,
                            'workflow': 'unknown',
                            'description': '',  # Blank for consistency with projects that have config but no description field
                            'created': 'unknown',
                            'version': 'unknown'
                        })

            return {
                'projects': projects,
                'count': len(projects),
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise ProjectError(f"Failed to list projects: {e}", cause=e)

    def remove_project(self, project_name: str, force: bool = False) -> Dict[str, Any]:
        """
        Remove a project safely.

        Args:
            project_name: Name of the project to remove
            force: Whether to skip confirmation prompts

        Returns:
            Dictionary with removal results

        Raises:
            ProjectError: If removal fails
        """
        validate_required(project_name, "project_name", "remove_project")

        try:
            logger.info(f"Removing project '{project_name}'")

            if not self.project_exists(project_name):
                raise ProjectNotFoundError(f"Project '{project_name}' not found")

            projects_dir = Path(self.config.get('directories', {}).get('projects', 'projects'))
            project_path = projects_dir / project_name

            # Remove project directory
            import shutil
            shutil.rmtree(project_path)

            logger.info(f"Successfully removed project '{project_name}'")
            return {
                'project_name': project_name,
                'status': 'removed',
                'path': str(project_path)
            }

        except Exception as e:
            logger.error(f"Failed to remove project '{project_name}': {e}")
            raise ProjectError(
                f"Failed to remove project '{project_name}': {e}",
                context={'project_name': project_name},
                cause=e
            )

    def get_project_status(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive project status.

        Args:
            project_name: Specific project name, or None for current project

        Returns:
            Dictionary with project status information

        Raises:
            ProjectError: If status retrieval fails
        """
        try:
            if project_name:
                # Get specific project status
                logger.info(f"Getting status for project '{project_name}'")

                if not self.project_exists(project_name):
                    raise ProjectNotFoundError(f"Project '{project_name}' not found")

                projects_dir = Path(self.config.get('directories', {}).get('projects', 'projects'))
                project_data = self._load_project_config(projects_dir / project_name / 'agentic')

                if project_data:
                    return {
                        'project_name': project_name,
                        'status': 'found',
                        'config': project_data,
                        'path': str(projects_dir / project_name)
                    }
                else:
                    return {
                        'project_name': project_name,
                        'status': 'found',
                        'config': None,
                        'message': 'No configuration file found',
                        'path': str(projects_dir / project_name)
                    }
            else:
                # Get current project status (from current directory)
                from ..core.path_resolution import find_project_root

                project_root = find_project_root()
                if not project_root:
                    return {
                        'status': 'not_in_project',
                        'message': 'Not in a project directory'
                    }

                config_data = self._load_project_config(project_root / 'agentic')
                if config_data:
                    return {
                        'project_name': config_data.get('name', 'unknown'),
                        'status': 'current',
                        'config': config_data,
                        'path': str(project_root)
                    }
                else:
                    return {
                        'status': 'current',
                        'config': None,
                        'message': 'No configuration file found',
                        'path': str(project_root)
                    }

        except Exception as e:
            logger.error(f"Failed to get project status: {e}")
            raise ProjectError(f"Failed to get project status: {e}", cause=e)
