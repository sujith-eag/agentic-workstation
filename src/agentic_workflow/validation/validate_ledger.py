#!/usr/bin/env python3
"""Simple validator for `extra` YAML produced by the dispatcher.

Reads YAML from stdin and validates required keys for the given --type.

Usage:
    echo "source: A01\ntarget: A02" | python3 -m scripts.validation.validate_ledger --type HANDOFF
"""
import sys
import argparse
from pathlib import Path
import yaml
from agentic_workflow.cli.utils import display_error


def validate_handoff(data):
    errors = []
    if not data.get('source'):
        errors.append('missing source')
    if not data.get('target'):
        errors.append('missing target')
    if not data.get('artifacts'):
        errors.append('missing artifacts')
    
    # Check workflow-aware validation if project info is available
    source = data.get('source')
    target = data.get('target')
    project = data.get('project')
    
    if source and target and project:
        workflow_errors = validate_workflow_handoff(project, source, target)
        errors.extend(workflow_errors)
    
    return errors


def validate_workflow_handoff(project_name: str, from_agent: str, to_agent: str) -> list:
    """
    Validate that a handoff is allowed according to the workflow definition.
    
    Args:
        project_name: Name of the project
        from_agent: Agent initiating the handoff
        to_agent: Agent receiving the handoff
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    try:
        # Load project config to get workflow type
        from agentic_workflow.core.paths import PROJECTS_DIR
        project_dir = PROJECTS_DIR / project_name
        config_file = project_dir / "project_config.json"
        
        if not config_file.exists():
            return ["project config not found"]
            
        import json
        with open(config_file, 'r') as f:
            project_config = json.load(f)
            
        workflow_name = project_config.get('workflow')
        if not workflow_name:
            return ["workflow not specified in project config"]
            
        # Load workflow agents from the generated JSON file
        from agentic_workflow.core.paths import get_manifests_dir
        manifests_dir = get_manifests_dir()
        workflow_json_path = manifests_dir / workflow_name / "agents.json"
        if not workflow_json_path.exists():
            return [f"workflow manifest not found: {workflow_json_path}"]
            
        import json
        with open(workflow_json_path, 'r') as f:
            workflow_data = json.load(f)
            
        agents = workflow_data.get('agents', [])
        
        # Find the source agent
        source_agent = None
        for agent in agents:
            if agent.get('id') == from_agent or agent.get('slug') == from_agent:
                source_agent = agent
                break
                
        if not source_agent:
            errors.append(f"source agent '{from_agent}' not found in workflow '{workflow_name}'")
            return errors
            
        # Check if target is in the handoff.next list
        handoff_next = source_agent.get('handoff', {}).get('next', [])
        
        # If no explicit handoff rules, allow sequential pipeline progression
        if not handoff_next:
            # Get pipeline order from workflow
            workflow_json_path = manifests_dir / workflow_name / "workflow.json"
            if workflow_json_path.exists():
                with open(workflow_json_path, 'r') as f:
                    workflow_data = json.load(f)
                    pipeline_order = workflow_data.get('pipeline', {}).get('order', [])
                    
                # Find current agent position and allow next agent
                try:
                    current_index = pipeline_order.index(from_agent)
                    if current_index < len(pipeline_order) - 1:
                        next_agent = pipeline_order[current_index + 1]
                        if next_agent == to_agent:
                            target_allowed = True
                except (ValueError, IndexError):
                    pass
        else:
            # Check explicit handoff rules
            for next_agent in handoff_next:
                if isinstance(next_agent, dict):
                    agent_id = next_agent.get('id')
                else:
                    agent_id = next_agent
                    
                if agent_id == to_agent:
                    target_allowed = True
                    break
                
        if not target_allowed:
            allowed_targets = [str(agent.get('id', agent)) for agent in handoff_next]
            errors.append(f"handoff from '{from_agent}' to '{to_agent}' not allowed. Allowed targets: {', '.join(allowed_targets)}")
            
    except Exception as e:
        errors.append(f"workflow validation error: {e}")
        
    return errors


def validate_feedback(data):
    errors = []
    if not data.get('source'):
        errors.append('missing source')
    if not data.get('target'):
        errors.append('missing target')
    return errors


def validate_iteration(data):
    # iteration has loose requirements
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', required=True, help='Event type to validate')
    args = parser.parse_args()

    try:
        raw = sys.stdin.read()
        extra = yaml.safe_load(raw) or {}
    except Exception as e:
        display_error(f'Failed to parse YAML from stdin: {e}')
        sys.exit(2)

    etype = args.type.upper()
    errs = []
    if etype == 'HANDOFF':
        errs = validate_handoff(extra)
    elif etype == 'FEEDBACK':
        errs = validate_feedback(extra)
    elif etype == 'ITERATION':
        errs = validate_iteration(extra)
    elif etype == 'SESSION_ARCHIVE':
        errs = []
    else:
        display_error(f'Unknown type: {etype}')
        sys.exit(2)

    if errs:
        for e in errs:
            display_error(str(e))
        sys.exit(3)

    sys.exit(0)


if __name__ == '__main__':
    main()
