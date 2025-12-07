"""
Project Generation System for Agentic Workflow Platform.

This module orchestrates project generation by delegating to specialized generators:
- Config generation: generators/config.py
- Structure generation: generators/structure.py
- Runtime generation: generators/runtime.py

Key Design Decisions:
- Workflow data drives project configuration generation
- Governance rules extracted from workflow manifests
- Agent configurations derived from workflow agent definitions
- Directory structure follows workflow specifications

Author: AI Assistant
Date: December 6, 2025
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .config_service import ConfigurationService

# Import specialized generators
from agentic_workflow.generators.config import generate_project_config
from agentic_workflow.generators.structure import (
    create_project_directories,
)
from agentic_workflow.generators.runtime import (
    generate_artifact_files,
    generate_agent_files,
    generate_workflow_script,
    initialize_runtime_state
)
from agentic_workflow.core.governance_extraction import extract_governance_from_workflow

from ..cli.utils import display_success

# Setup logging
logger = logging.getLogger(__name__)


def create_project_from_workflow(workflow_type: str, project_name: str, target_path: Path) -> Dict[str, Any]:
    """
    Create a complete project configuration from workflow type.

    This function acts as the orchestrator, coordinating the generation process:
    1. Load configuration and workflow data
    2. detailed project configuration
    3. Create physical directory structure
    4. Generate runtime artifacts and scripts

    Args:
        workflow_type: Type of workflow to instantiate (e.g., 'planning')
        project_name: Name of the new project
        target_path: Root path for the new project

    Returns:
        Dict containing the final merged configuration.

    Raises:
        ConfigError: If project creation fails at any step.
    """
    try:
        # Load workflow data
        from ..generation.canonical_loader import load_canonical_workflow
        try:
             workflow_data = load_canonical_workflow(workflow_type)
        except Exception as e:
             raise ConfigError(f"Workflow type '{workflow_type}' not found: {e}")

        # Load app config using new service
        config_service = ConfigurationService()
        app_config = config_service.load_config(target_path)

        # Generate project config
        project_config = generate_project_config(workflow_type, project_name, app_config, workflow_data)

        # Merge with app config for complete configuration
        merged_config = {**app_config, **project_config}

        # Create project directory structure
        target_path.mkdir(parents=True, exist_ok=True)

        # Create standard project directories
        directories_created = create_project_directories(target_path, merged_config, workflow_data)

        # Generate initial artifacts
        generate_artifact_files(target_path, merged_config, workflow_data)

        # Generate agent files
        generate_agent_files(target_path, merged_config)

        # Generate workflow executable script
        generate_workflow_script(target_path, merged_config, workflow_data)

        # Initialize runtime state (logs, contexts, docs)
        initialize_runtime_state(target_path, merged_config, workflow_data)

        display_success(f"Successfully created project config for {project_name}")
        return merged_config | {'directories_created': directories_created}

    except Exception as e:
        logger.error(f"Failed to create project from workflow {workflow_type}: {e}")
        raise ConfigError(f"Project creation failed: {e}")


# Update the placeholder functions in config.py
def _update_config_placeholders():
    """Update placeholder functions in config.py with actual implementations."""
    # Import the config module
    from . import config as config_module

    # Replace placeholder functions with implementations from generators/core
    config_module.generate_project_config = generate_project_config
    config_module.extract_governance_from_workflow = extract_governance_from_workflow

    logger.info("Updated config.py placeholder functions with actual implementations")