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
# from agentic_workflow.generators.structure import (
#     create_project_directories,
# )
# from agentic_workflow.generators.runtime import (
#     generate_artifact_files,
#     generate_agent_files,
#     generate_workflow_script,
#     initialize_runtime_state
# )
from agentic_workflow.core.governance_extraction import extract_governance_from_workflow

# Setup logging
logger = logging.getLogger(__name__)


def create_project_from_workflow(workflow_type: str, project_name: str, target_path: Path) -> Dict[str, Any]:
    """
    Create a complete project using the new atomic pipeline.
    """
    from ..core.config_service import ConfigurationService
    from ..generators.pipeline import InitPipeline

    config_service = ConfigurationService()
    config = config_service.load_config()

    pipeline = InitPipeline(config)
    pipeline.run(str(target_path), workflow_type)

    return {"status": "created", "path": target_path}


# Update the placeholder functions in config.py
def _update_config_placeholders():
    """Update placeholder functions in config.py with actual implementations."""
    # Import the config module
    from . import config as config_module

    # Replace placeholder functions with implementations from generators/core
    config_module.generate_project_config = generate_project_config
    config_module.extract_governance_from_workflow = extract_governance_from_workflow

    logger.info("Updated config.py placeholder functions with actual implementations")