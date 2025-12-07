"""
Structure generator for project creation.

This module handles the creation of the physical directory structure and
the writing of the initial JSON manifest files (workflow, agents, artifacts, instructions).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..cli.utils import display_success

logger = logging.getLogger(__name__)

def create_project_directories(target_path: Path, config: Dict[str, Any], workflow_data: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Create standard project directory structure.

    Args:
        target_path: Project root directory
        config: Merged configuration containing directory mappings
        workflow_data: Optional workflow data to create agent-specific subdirectories

    Returns:
        List of created directory names
    """
    # Standard directories to create
    standard_dirs = [
        'agent_files',
        'agent_context',
        'agent_log',
        'artifacts',
        'docs',
        'input',
        'package'
    ]

    created_dirs = []

    # Create directories
    for dir_name in standard_dirs:
        dir_path = target_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_name)
            logger.info(f"Created directory: {dir_path}")

    # Create agent-specific subdirectories in artifacts
    if workflow_data:
        agents_data = workflow_data.get('agents', {})
        if isinstance(agents_data, list):
            agents = agents_data
        else:
            agents = agents_data.get('agents', [])
        artifacts_dir = target_path / 'artifacts'

        for agent in agents:
            agent_id = agent.get('id', '')
            agent_slug = agent.get('slug', '')
            agent_type = agent.get('agent_type', 'core')

            # Skip artifact directory for orchestrators (managed at root/context level)
            if agent_type == 'orchestrator':
                continue

            if agent_id and agent_slug:
                # Create directory like A-01_planning
                agent_dir_name = f"{agent_id}_{agent_slug}"
                agent_dir_path = artifacts_dir / agent_dir_name
                if not agent_dir_path.exists():
                    agent_dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(f"artifacts/{agent_dir_name}")
                    display_success(f"Created agent artifact directory: {agent_dir_path}")

    display_success(f"Created project directory structure in: {target_path}")
    return created_dirs

