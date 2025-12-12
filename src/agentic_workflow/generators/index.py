"""Project index generator.

This module generates project_index.md content from workflow packages.

Usage:
    from generators.index import generate_project_index
    
    content = generate_project_index('myproject', wf)
"""
import datetime
from typing import Optional

from agentic_workflow.workflow import WorkflowPackage
from agentic_workflow.utils.templating import TemplateEngine


def generate_project_index(project_name: str, wf: WorkflowPackage) -> str:
    """Generate project_index.md content from workflow package.
    
    Uses Jinja2 templates for rendering.
    
    Args:
        project_name: Project name.
        wf: WorkflowPackage instance.
        
    Returns:
        Generated project index markdown content.
    """
    artifacts = wf.artifacts
    
    # Build File Registry entries
    registry_entries = []
    for artifact in artifacts:
        name = artifact.get('filename', 'unknown')
        owner = artifact.get('owner', 'Unknown')
        if isinstance(owner, int):
            owner_str = wf.format_agent_id(owner)
        elif owner == 'orch':
            owner_str = wf.orch_id
        else:
            owner_str = str(owner)
        desc = artifact.get('description', '')
        registry_entries.append({
            'name': name,
            'owner': owner_str,
            'description': desc
        })
    
    # Render with Jinja2
    loader = TemplateEngine(workflow=wf.name)
    context = {
        'project_name': project_name,
        'workflow_name': wf.name,
        'workflow_display_name': wf.display_name,
        'workflow_version': wf.version,
        'timestamp': datetime.datetime.now().isoformat(),
        'registry_entries': registry_entries,
        'current_phase': 'Initialization',
        'active_agent': 'Orchestrator',
        'last_action': 'Project Initialized',
    }
    return loader.render('project_index.md.j2', context)
