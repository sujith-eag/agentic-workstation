#!/usr/bin/env python3
"""Gate checker for implementation workflow.

This module checks pre-conditions before agent activation,
ensuring stage gates are satisfied.

Usage:
    from session.gate_checker import check_gate
    
    result = check_gate('myproject', 'I2')
    if not result['passed']:
        for reason in result['reasons']:
            print(f"Gate failure: {reason}")
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from agentic_workflow.workflow.canonical import (
    load_workflow_json,
    load_agents_json,
)

# Use core modules instead of duplicated code
from agentic_workflow.core.project import load_project_meta
from agentic_workflow.core.paths import WORKFLOWS_DIR, PROJECTS_DIR
from agentic_workflow.cli.utils import display_success, display_error


def load_workflow_config(workflow_name: str) -> Optional[Dict]:
    """Load workflow configuration from canonical JSON."""
    return load_workflow_json(workflow_name) or None


def load_workflow_agents(workflow_name: str) -> Optional[Dict]:
    """Load workflow agents configuration from canonical JSON."""
    return load_agents_json(workflow_name) or None


def get_agent_config(workflow_name: str, agent_id: str) -> Optional[Dict]:
    """Get configuration for a specific agent."""
    agents_data = load_workflow_agents(workflow_name)
    if not agents_data:
        return None
    
    all_agents = agents_data.get('agents', []) + agents_data.get('on_demand_agents', [])
    
    for agent in all_agents:
        if agent.get('id') == agent_id:
            return agent
    
    return None


def check_stage_gate(project_name: str, agent_id: str, workflow_config: Dict) -> List[str]:
    """Check if current stage allows agent activation.
    
    Returns:
        List of failure reasons (empty if passed)
    """
    failures = []
    
    # Load project workflow state
    project_wf = load_project_meta(project_name)
    if not project_wf:
        failures.append("Project workflow metadata not found (project_config.json)")
        return failures
    
    current_stage = project_wf.get('current_stage', 'INTAKE')
    workflow_name = project_wf.get('workflow', 'planning')
    
    # Get agent config
    agent_config = get_agent_config(workflow_name, agent_id)
    if not agent_config:
        failures.append(f"Agent {agent_id} not found in workflow configuration")
        return failures
    
    # Get required stage for this agent (if defined)
    required_stage = agent_config.get('stage')
    if required_stage:
        # Check stage order
        stages = workflow_config.get('stages', [])
        stage_names = [s.get('id') for s in stages]
        
        if required_stage in stage_names and current_stage in stage_names:
            required_idx = stage_names.index(required_stage)
            current_idx = stage_names.index(current_stage)
            
            if current_idx < required_idx:
                failures.append(
                    f"Stage '{current_stage}' is before required stage '{required_stage}' for agent {agent_id}"
                )
    
    return failures


def check_artifact_gate(project_name: str, agent_id: str, workflow_name: str) -> List[str]:
    """Check if required artifacts exist.
    
    Returns:
        List of failure reasons (empty if passed)
    """
    failures = []
    
    project_dir = PROJECTS_DIR / project_name
    agent_config = get_agent_config(workflow_name, agent_id)
    
    if not agent_config:
        return failures  # Already checked in stage gate
    
    # Check consumes_core artifacts (required)
    core_artifacts = agent_config.get('consumes_core', [])
    for artifact in core_artifacts:
        # Check common locations
        found = False
        search_paths = [
            project_dir / "input" / "planning_artifacts" / f"{artifact}.md",
            project_dir / "input" / f"{artifact}.md",
            project_dir / "artifacts" / f"{artifact}.md",
        ]
        
        for path in search_paths:
            if path.exists():
                found = True
                break
        
        if not found:
            failures.append(f"Required core artifact missing: {artifact}")
    
    return failures


def check_handoff_gate(project_name: str, agent_id: str) -> List[str]:
    """Check if required handoffs exist from upstream agents.
    
    Returns:
        List of failure reasons (empty if passed)
    """
    failures = []
    
    # For implementation workflow, check for handoff from previous agent in pipeline
    # This is a simplified check - can be enhanced based on workflow configuration
    
    project_dir = PROJECTS_DIR / project_name
    exchange_log = project_dir / "agent_log" / "exchange_log.md"
    
    if not exchange_log.exists():
        # First agent doesn't need handoff
        if agent_id not in ['I0', 'A00', 'orchestrator']:
            failures.append("No exchange_log.md found - cannot verify handoffs")
        return failures
    
    # Parse agent index from ID
    try:
        if agent_id.startswith('I'):
            agent_num = int(agent_id[1:])
        elif agent_id.startswith('A'):
            agent_num = int(agent_id[1:])
        else:
            return failures  # Can't determine upstream
        
        if agent_num == 0:
            return failures  # First agent, no upstream
        
        # Check for handoff from previous agent
        with open(exchange_log, 'r') as f:
            content = f.read()
        
        prefix = 'I' if agent_id.startswith('I') else 'A'
        prev_agent = f"{prefix}{agent_num - 1:02d}" if agent_num > 1 else f"{prefix}0"
        
        # Look for handoff pattern
        if f"to: {agent_id}" not in content and f"→ {agent_id}" not in content:
            failures.append(f"No handoff found to {agent_id} from upstream")
    
    except (ValueError, IndexError):
        pass  # Can't parse agent number, skip this check
    
    return failures


def check_blocker_gate(project_name: str, agent_id: str) -> List[str]:
    """Check if there are any active blockers affecting this agent.
    
    Returns:
        List of failure reasons (empty if passed)
    """
    failures = []
    
    project_dir = PROJECTS_DIR / project_name
    context_log = project_dir / "agent_log" / "context_log.md"
    
    if not context_log.exists():
        return failures
    
    with open(context_log, 'r') as f:
        content = f.read()
    
    # Look for BLOCKER entries that reference this agent
    # This is a simplified check - can be enhanced with YAML parsing
    if f"blocked: {agent_id}" in content or f"blocked_agents: [{agent_id}" in content:
        failures.append(f"Active blocker exists for agent {agent_id}")
    
    return failures


def check_gate(project_name: str, agent_id: str) -> Dict[str, Any]:
    """Main gate check function.
    
    Args:
        project_name: Name of the project
        agent_id: Agent ID to check gates for
        
    Returns:
        Dict with:
        - passed: bool - True if all gates passed
        - reasons: List[str] - Failure reasons if any
        - message: str - Success message if passed
    """
    project_dir = PROJECTS_DIR / project_name
    
    # Check project exists
    if not project_dir.exists():
        return {
            'passed': False,
            'reasons': [f"Project '{project_name}' not found"]
        }
    
    # Load project workflow info
    project_wf = load_project_meta(project_name)
    if not project_wf:
        return {
            'passed': False,
            'reasons': ["Project workflow metadata not found (project_config.json)"]
        }
    
    workflow_name = project_wf.get('workflow', 'planning')
    
    # Load workflow config
    workflow_config = load_workflow_config(workflow_name)
    if not workflow_config:
        return {
            'passed': False,
            'reasons': [f"Workflow configuration '{workflow_name}' not found"]
        }
    
    # Check if gating is enabled
    gating = workflow_config.get('gating', {})
    if not gating.get('enabled', True):
        return {
            'passed': True,
            'message': "Gating disabled for this workflow"
        }
    
    # Run all gate checks
    all_failures = []
    
    # Stage gate
    if gating.get('pre_activation', True):
        all_failures.extend(check_stage_gate(project_name, agent_id, workflow_config))
    
    # Artifact gate
    all_failures.extend(check_artifact_gate(project_name, agent_id, workflow_name))
    
    # Handoff gate
    all_failures.extend(check_handoff_gate(project_name, agent_id))
    
    # Blocker gate
    all_failures.extend(check_blocker_gate(project_name, agent_id))
    
    if all_failures:
        return {
            'passed': False,
            'reasons': all_failures
        }
    
    return {
        'passed': True,
        'message': f"All gates passed for {agent_id}"
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        display_error("Usage: python gate_checker.py <project> <agent_id>")
        sys.exit(1)
    
    result = check_gate(sys.argv[1], sys.argv[2])
    
    if result['passed']:
        display_success(result.get('message', 'Gate check passed'))
    else:
        display_error("Gate check failed:")
        for reason in result.get('reasons', []):
            display_error(f"   - {reason}")
        sys.exit(1)
