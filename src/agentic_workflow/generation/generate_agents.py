#!/usr/bin/env python3
"""Generate agent files from workflow packages using Jinja2 templates.

This script generates agent prompt files from workflow packages using
Jinja2 templates and canonical JSON data.

Output locations:
- Global: agent_files// (when --workflow specified without --project)
- Project: projects//agent_files/ (when --project specified)

Usage:
    # Generate for a workflow (global)
    python3 -m scripts.generation.generate_agents --workflow planning
    
    # Generate for a project (uses project's workflow)
    python3 -m scripts.generation.generate_agents --project myproject
    
    # Generate specific agent
    python3 -m scripts.generation.generate_agents --workflow planning --agent A01
"""
import argparse
import json
import sys
from pathlib import Path

from agentic_workflow.workflow.loader import load_workflow, WorkflowError
from agentic_workflow.workflow.resolver import get_default_workflow
from agentic_workflow.utils.jinja_loader import render_agent
from agentic_workflow.cli.utils import display_error, display_warning, display_info, display_success
from agentic_workflow.core.paths import get_projects_dir
from pathlib import Path as _Path


def get_agent_filename(agent: dict, wf) -> str:
    """Generate filename for an agent.
    
    Uses workflow.format_agent_id() to get consistent ID formatting.
    
    Args:
        agent: Agent definition dict
        wf: WorkflowPackage instance
        
    Returns:
        Filename string (e.g., "A01_Requirements Analyst.md")
    """
    agent_id = agent.get('id')
    role = agent.get('role', agent.get('slug', 'agent'))
    
    # Use workflow's ID formatter for consistent naming
    formatted_id = wf.format_agent_id(agent_id)
    
    return f"{formatted_id}_{role}.md"


def generate_agents(
    workflow_name: str,
    output_dir: Path = None,
    agent_filter: str = None,
    project_name: str = "project",
    dry_run: bool = False
) -> int:
    """Generate agent files using Jinja2 template engine.
    
    Uses the global agent_base.md.j2 template with context from canonical JSON.
    
    Args:
        workflow_name: Name of workflow package (e.g., 'planning')
        output_dir: Output directory (default: agent_files//)
        agent_filter: Optional agent ID to filter to single agent
        project_name: Project name for context
        dry_run: If True, print content without writing
        
    Returns:
        Number of files generated
    """
    try:
        wf = load_workflow(workflow_name)
    except WorkflowError as e:
        display_error(str(e))
        return 0
    
    # Set default output directory
    if output_dir is None:
        output_dir = ROOT / 'agent_files' / workflow_name
    
    # Get agent list
    agents = wf.agents
    
    # Filter agents if requested
    if agent_filter:
        target = str(agent_filter).upper()
        # Use workflow's formatting helper to normalize the requested agent id
        try:
            target_id = wf.format_agent_id(target)
        except Exception:
            target_id = target

        # Compare normalized ids case-insensitively
        agents = [a for a in agents if str(wf.format_agent_id(a.get('id', ''))).upper() == target_id.upper()]
        if not agents:
            display_error(f"Agent {agent_filter} not found in workflow {workflow_name}")
            return 0
    
    generated = 0
    for agent in agents:
        agent_id = agent.get('id')
        
        try:
            # Render using Jinja2 with global agent_base.md.j2 template
            content = render_agent(workflow_name, agent_id, project_name)
            
            # Generate filename
            filename = get_agent_filename(agent, wf)
            
            if dry_run:
                display_info(f"=== {filename} ===")
                display_info(content[:500] + "..." if len(content) > 500 else content)
            else:
                full_path = Path(output_dir) / filename
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                try:
                    shortened = f"/{full_path.relative_to(get_projects_dir())}"
                except Exception:
                    try:
                        shortened = f"/{full_path.relative_to(_Path.cwd())}"
                    except Exception:
                        shortened = str(full_path)
                display_success(f"Generated: {shortened}")
                generated += 1
                
        except Exception as e:
            display_error(f"Error generating {agent_id}: {e}")
            continue
    
    return generated


def generate_agents_for_project(
    project_name: str,
    agent_filter: str = None,
    dry_run: bool = False
) -> int:
    """Generate agent files for a project using its workflow.
    
    Reads workflow from project's project_config.json metadata file.
    Outputs to projects//agent_files/
    
    Args:
        project_name: Project name
        agent_filter: Optional agent ID to filter
        dry_run: If True, print without writing
        
    Returns:
        Number of files generated
    """
    project_dir = ROOT / 'projects' / project_name
    
    if not project_dir.exists():
        display_error(f"Project {project_name} not found")
        return 0
    
    # Read project workflow from project_config.json
    meta_path = project_dir / 'project_config.json'
    if meta_path.exists():
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        workflow_name = meta.get('workflow', get_default_workflow())
    else:
        workflow_name = get_default_workflow()
        display_warning(f"No project_config.json found, using default: {workflow_name}")
    
    output_dir = project_dir / 'agent_files'
    
    display_info(f"Generating agents for project '{project_name}' using workflow '{workflow_name}'")
    return generate_agents(workflow_name, output_dir, agent_filter, project_name, dry_run)


def main():
    parser = argparse.ArgumentParser(
        description="Generate agent files from workflow packages using Jinja2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate for default workflow (global agent_files/)
    python3 -m scripts.generation.generate_agents
    
    # Generate for specific workflow
    python3 -m scripts.generation.generate_agents --workflow planning
    
    # Generate for a project (uses project's workflow)
    python3 -m scripts.generation.generate_agents --project myproject
    
    # Generate specific agent
    python3 -m scripts.generation.generate_agents --workflow planning --agent A01
"""
    )
    parser.add_argument('--workflow', '-w', type=str, help='Workflow name (e.g., planning)')
    parser.add_argument('--project', '-p', type=str, help='Project name (uses project workflow)')
    parser.add_argument('--agent', type=str, help='Specific agent ID to regenerate (e.g., 1, 01, A01)')
    parser.add_argument('--dry-run', action='store_true', help='Print output without writing files')
    args = parser.parse_args()
    
    if args.project:
        # Project mode: generate to project's agent_files/
        generated = generate_agents_for_project(args.project, args.agent, args.dry_run)
    else:
        # Workflow mode: generate to agent_files//
        workflow_name = args.workflow or get_default_workflow()
        project_name = "project"
        generated = generate_agents(workflow_name, None, args.agent, project_name, args.dry_run)
    
    if not args.dry_run:
        display_success(f"Generated {generated} agent files.")


if __name__ == '__main__':
    main()
