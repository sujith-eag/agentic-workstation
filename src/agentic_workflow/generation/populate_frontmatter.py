#!/usr/bin/env python3
"""Populate agent frontmatter for the project.

Reads from canonical JSON manifests and applies frontmatter to agent files.

Usage:
    python3 -m scripts.generation.populate_frontmatter --project 
"""
import argparse
import os
import sys
import re
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    display_error("pyyaml required")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent

from agentic_workflow.generation.canonical_loader import load_canonical_workflow
from agentic_workflow.cli.utils import display_success, display_error, display_warning, display_info


def get_project_workflow(project_name):
    """Get the workflow name for a project from agentic.toml."""
    agentic_toml = ROOT / 'projects' / project_name / 'agentic.toml'
    if not agentic_toml.exists():
        display_error(f"Project config not found: {agentic_toml}")
        return None
    
    try:
        data = yaml.safe_load(agentic_toml.read_text())
        return data.get('workflow')
    except Exception as e:
        display_error(f"Failed to load project config: {e}")
        return None


def load_agents_for_project(project_name):
    """Load agents for the project's workflow from canonical JSON."""
    workflow = get_project_workflow(project_name)
    if not workflow:
        return []
    
    try:
        data = load_canonical_workflow(workflow)
        agents_data = data.get('agents', {})
        return agents_data.get('agents', [])
    except Exception as e:
        display_error(f"Failed to load canonical workflow {workflow}: {e}")
        return []


def parse_frontmatter(content):
    """Parse existing frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    
    body = '---'.join(parts[2:]).lstrip('\n')
    return fm, body


def apply_frontmatter(fm, body):
    """Combine frontmatter dict with body into full markdown."""
    fm_str = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    return f"---\n{fm_str}---\n\n{body}"


def populate_agent_files(project_name):
    """Populate agent files with standardized frontmatter."""
    agents = load_agents_for_project(project_name)
    if not agents:
        display_error("No agents found for project")
        return 1
    
    workflow_name = get_project_workflow(project_name)
    project_dir = ROOT / 'projects' / project_name
    agent_files_dir = project_dir / 'agent_files'
    
    if not project_dir.exists():
        display_error(f"Project directory not found: {project_dir}")
        return 1
    
    updated = 0
    for agent in agents:
        agent_id = agent.get('id')
        role = agent.get('role', agent.get('slug', 'agent'))
        
        agent_file = agent_files_dir / f"{agent_id}_{role}.md"
        if not agent_file.exists():
            display_warning(f"Agent file not found: {agent_file}")
            continue
        
        content = agent_file.read_text()
        existing_fm, body = parse_frontmatter(content)
        
        # Build new frontmatter
        new_fm = {
            'agent_id': agent_id,
            'agent_role': role,
            'agent_type': agent.get('agent_type', 'core'),
            'workflow_name': workflow_name,
            'project_name': project_name,
            'produces': agent.get('produces', {}),
            'consumes': agent.get('consumes', {}),
            'updated': datetime.now().strftime('%Y-%m-%d'),
        }
        
        # Preserve existing fields that shouldn't be overwritten
        for key in ('status', 'notes', 'custom'):
            if key in existing_fm:
                new_fm[key] = existing_fm[key]
        
        # Apply frontmatter
        new_content = apply_frontmatter(new_fm, body)
        agent_file.write_text(new_content)
        updated += 1
        display_success(f"Updated: {agent_file.name}")
    
    display_info(f"Populated {updated} agent files.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Populate agent frontmatter")
    parser.add_argument('--project', required=True, help='Project name')
    args = parser.parse_args()
    
    sys.exit(populate_agent_files(args.project))


if __name__ == '__main__':
    main()
