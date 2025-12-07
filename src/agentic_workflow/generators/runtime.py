"""
Runtime generator for project creation.

This module handles the generation of runtime files including:
- Initial artifacts based on templates
- Log and context initialization
- Agent markdown files
- Executable workflow scripts
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import jinja2
import os

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import jinja2
import os

from agentic_workflow.core.io import write_file
from agentic_workflow.core.paths import get_templates_dir, get_workflow_search_paths
from agentic_workflow.utils.jinja_loader import JinjaTemplateLoader
from agentic_workflow.cli.utils import display_success, display_info

logger = logging.getLogger(__name__)

def find_workflow_dir(workflow_type: str) -> Optional[Path]:
    """Find the directory for a given workflow type."""
    for search_path in get_workflow_search_paths():
        candidate = search_path / workflow_type
        if candidate.is_dir():
            return candidate
    return None

def generate_workflow_script(target_path: Path, config: Dict[str, Any], workflow_data: Dict[str, Any]) -> None:
    """
    Generate the workflow executable script from template.

    Args:
        target_path: Project root directory
        config: Project configuration
        workflow_data: Loaded workflow data
    """
    # Load workflow script template
    template_path = get_templates_dir() / 'workflow.tpl'

    if not template_path.exists():
        logger.warning(f"Workflow template not found at {template_path}, skipping script generation")
        return

    # Initialize Jinja2 environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(get_templates_dir()),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Load and render template with workflow data
    template = env.get_template('workflow.tpl')
    
    # Extract workflow metadata for template
    workflow_metadata = workflow_data.get('workflow', {})
    agents = workflow_data.get('agents', [])
    
    # Prepare template context
    context = {
        'workflow_name': workflow_metadata.get('name', config.get('workflow_type', 'unknown')),
        'workflow_display_name': workflow_metadata.get('display_name', workflow_metadata.get('name', 'Unknown Workflow')),
        'workflow_description': workflow_metadata.get('description', ''),
        'project_name': config.get('project_name', 'unknown'),
        'agents': agents,
        'pipeline_order': workflow_metadata.get('pipeline', {}).get('order', []),
        'checkpoints': workflow_metadata.get('pipeline', {}).get('checkpoints', []),
        'repo_root': config.get('repo_root', '/path/to/repo'),
        'config': config
    }

    # Render template
    script_content = template.render(**context)

    # Write script
    script_path = target_path / 'workflow'
    # Write script
    script_path = target_path / 'workflow'
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

    # Make executable
    os.chmod(script_path, 0o755)

    display_success(f"Generated workflow script: {script_path}")


def generate_artifact_files(target_path: Path, config: Dict[str, Any], workflow_data: Dict[str, Any]) -> None:
    """
    Generate initial artifact files for agents based on workflow definition.
    
    Args:
        target_path: Project root directory
        config: Project configuration
        workflow_data: Loaded workflow data
    """
    workflow_type = config.get('workflow_type')
    
    # Initialize Template Loader with workflow context
    # This automatically handles hierarchy: Workflow -> Role -> Base
    try:
        loader = JinjaTemplateLoader(workflow=workflow_type)
    except Exception as e:
        logger.error(f"Failed to initialize JinjaTemplateLoader: {e}")
        return

    # Extract agents
    agents_data = workflow_data.get('agents', {})
    if isinstance(agents_data, list):
        agents = agents_data
    else:
        agents = agents_data.get('agents', [])

    count = 0
    artifacts_dir = target_path / 'artifacts'
    
    for agent in agents:
        agent_id = agent.get('id')
        agent_slug = agent.get('slug')
        agent_type = agent.get('agent_type', 'core')
        agent_role = agent.get('role', '')
        
        # Skip orchestrator (artifacts managed separately)
        if agent_type == 'orchestrator':
            continue
        
        if not (agent_id and agent_slug):
            continue
            
        agent_dir = artifacts_dir / f"{agent_id}_{agent_slug}"
        if not agent_dir.exists():
            continue
            
        # Get produced artifacts
        produces = agent.get('produces', [])
        artifact_list = []
        
        # Normalize produces (handle list vs dict of lists)
        if isinstance(produces, list):
            artifact_list = produces
        elif isinstance(produces, dict):
            for category, items in produces.items():
                if isinstance(items, list):
                    artifact_list.extend(items)
        
        for artifact in artifact_list:
            if not isinstance(artifact, dict):
                continue
                
            filename = artifact.get('filename')
            description = artifact.get('description', 'No description provided.')
            
            if not filename:
                continue
                
            file_path = agent_dir / filename
            
            if file_path.exists():
                continue
            
            # Enforce extension for text content if missing
            if not file_path.suffix and '.' not in file_path.name:
                 file_path = file_path.with_suffix('.md')
                 filename = file_path.name
                
            content = ""
            template_found = False
            
            # Try to render using the loader
            # Implicitly looks in artifacts/ folders via loader paths if configured, 
            # OR we pass relative path if we know where they are.
            # Usually artifact templates are in `artifacts/` or `workflow/templates/artifacts/`.
            # We try passing just the filename (if path includes it) or search common subdirs.
            
            # Helper to try rendering
            def try_render(tpl_name):
                try:
                    # Provide rich context for artifacts
                    context = {
                        'project_name': config.get('name'),
                        'agent_id': agent_id,
                        'agent_role': agent_role,
                        'description': description,
                        'artifact': artifact,
                        # Pass workflow data just in case
                        'workflow': workflow_type 
                    }
                    # render() handles .j2 vs .tpl lookup internally
                    return loader.render(tpl_name, context, role=agent_role if agent_role else None)
                except jinja2.TemplateNotFound:
                    return None
                except Exception as e:
                    logger.warning(f"Error rendering {tpl_name}: {e}")
                    return None

            # Search candidates
            # 1. artifacts/<filename> (common pattern)
            # 2. <filename> (direct match in search path)
            candidates = [
                f"artifacts/{filename}.j2", 
                f"artifacts/{filename}",
                f"{filename}.j2", 
                f"{filename}"
            ]
            
            for candidate in candidates:
                rendered = try_render(candidate)
                if rendered is not None:
                    content = rendered
                    template_found = True
                    break
            
            # Fallback content
            if not template_found:
                content = f"""# {filename}

**Owner**: {agent_role} ({agent_id})
**Description**: {description}

<!-- Initial scaffold generated by agentic-workflow -->
"""
            
            try:
                write_file(file_path, content)
                count += 1
                logger.debug(f"Generated artifact: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to write artifact {file_path}: {e}")

    display_info(f"Generated {count} initial artifact files")


def generate_agent_files(target_path: Path, config: Dict[str, Any]) -> None:
    """
    Generate agent files for the project from workflow templates.

    Args:
        target_path: Project root directory
        config: Project configuration
    """
    from agentic_workflow.generation.generate_agents import generate_agents

    workflow_type = config.get('workflow_type', 'planning')
    project_name = config.get('name', target_path.name)
    output_dir = target_path / 'agent_files'

    try:
        # Generate agent files
        generated_count = generate_agents(workflow_type, output_dir, None, project_name, False)
        display_info(f"Generated {generated_count} agent files for project {project_name}")
    except Exception as e:
        logger.warning(f"Failed to generate agent files: {e}")


def initialize_runtime_state(target_path: Path, config: Dict[str, Any], workflow_data: Dict[str, Any]) -> None:
    """
    Initialize runtime state (logs, contexts, docs) from templates.
    """
    workflow_type = config.get('workflow_type')
    
    # Initialize loader
    try:
        loader = JinjaTemplateLoader(workflow=workflow_type)
    except Exception as e:
        logger.error(f"Failed to initialize JinjaTemplateLoader: {e}")
        return

    # Helper to render all files in a source subdir
    def render_subdir(subdir: str, target_subdir: str):
        # We still need to list files to know WHAT to render.
        # Loader doesn't list, so we use filesystem for discovery.
        source_dir = get_templates_dir() / subdir
        
        if not source_dir.exists():
            logger.debug(f"Source dir not found: {source_dir}")
            return

        target_dir = target_path / target_subdir
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        # Iterate file system to find templates
        for template_file in source_dir.glob('*'):
            if template_file.is_dir() or template_file.name.startswith('_'):
                continue
            
            template_name = template_file.name
            
            # Target filename: strip .j2 suffix
            target_filename = template_name
            if target_filename.endswith('.j2'):
                target_filename = target_filename[:-3]
            
            # Construct relative path for loader (e.g., "logs/exchange_log.md.j2")
            loader_path = f"{subdir}/{template_name}"
            
            try:
                # Render using loader (gets all filters/inheritance)
                content = loader.render(
                    loader_path, 
                    {'project_name': config.get('name'), 'workflow_type': workflow_type}
                )
                
                write_file(target_dir / target_filename, content)
                logger.debug(f"Initialized runtime file: {target_subdir}/{target_filename}")
            except Exception as e:
                logger.warning(f"Failed to render runtime template {loader_path}: {e}")

    # 1. Initialize Logs
    render_subdir("logs", "agent_log")

    # 2. Initialize Docs
    render_subdir("docs", "docs")

    # 3. Initialize Session and Index from _base templates
    # We maintain the robust context building here but use the loader to render
    
    from datetime import datetime
    
    # Get first agent from workflow data
    pipeline_order = workflow_data.get('workflow', {}).get('pipeline', {}).get('order', [])
    if not pipeline_order:
        raise ValueError("Workflow data must contain a valid pipeline order")
    
    first_agent_id = pipeline_order[0]
    
    agents = workflow_data.get('agents', [])
    if isinstance(agents, dict): agents = agents.get('agents', [])
    first_agent = next((a for a in agents if a.get('id') == first_agent_id), None)
    if not first_agent:
        raise ValueError(f"Agent {first_agent_id} not found in workflow agents")
    
    first_agent_role = first_agent.get('role', 'Unknown')
    
    workflow_meta = workflow_data.get('workflow', {})
    workflow_display_name = workflow_meta.get('display_name', workflow_type.capitalize())
    workflow_version = workflow_meta.get('version', '1.0')
    
    context = {
        'project_name': config.get('name'),
        'workflow_name': workflow_type,
        'workflow_display_name': workflow_display_name,
        'workflow_version': workflow_version,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'agent_id': first_agent_id,
        'agent_role': first_agent_role,
        'current_phase': 'Ready for Activation',
        'active_agent': first_agent_id,
        'last_action': 'Project Created',
        'session_status': 'ready_for_activation'
    }

    # Build registry entries from workflow data
    registry_entries = []
    agents = workflow_data.get('agents', [])
    if isinstance(agents, dict): agents = agents.get('agents', [])
    
    for agent in agents:
        owner = agent.get('role', agent.get('id', 'Unknown'))
        produces = agent.get('produces', [])
        
        # Normalize produces
        items = []
        if isinstance(produces, list):
            items = produces
        elif isinstance(produces, dict):
            for cat_items in produces.values():
                if isinstance(cat_items, list):
                    items.extend(cat_items)
        
        for item in items:
            if isinstance(item, dict) and item.get('filename'):
                registry_entries.append({
                    'name': item.get('filename'),
                    'owner': owner,
                    'description': item.get('description', '')
                })
    
    context['registry_entries'] = registry_entries

    # Generate active_session.md
    try:
        # Check if we have an active agent
        if context.get('agent_id') is None:
            # Create a simple uninitialized session file
            session_content = f"""---
session_type: uninitialized
project_name: {context['project_name']}
workflow_name: {context['workflow_name']}
status: ready_for_activation
timestamp: {context['timestamp']}
---

# WORKFLOW READY FOR ACTIVATION

The project has been initialized and is ready for the first agent activation.

## Next Steps

1. **Activate the first agent:**
   ```bash
   ./workflow activate A-01  # For planning workflow
   # OR
   ./workflow activate I-01  # For implementation workflow
   ```

2. **Review project context** in `project_index.md`

3. **Begin producing artifacts** in the `artifacts/` directory

## Workflow Status

- **Status:** {context['current_phase']}
- **Next Agent:** A-01 (Project Guide & Idea Incubation)
- **Workflow:** {context['workflow_display_name']}
"""
        else:
            # Use loader to render _base/session_base.md.j2 for active sessions
            session_content = loader.render('_base/session_base.md.j2', context)
        
        context_dir = target_path / "agent_context"
        context_dir.mkdir(parents=True, exist_ok=True)
        write_file(context_dir / "active_session.md", session_content)
        display_success("Initialized agents_context/active_session.md")
    except Exception as e:
        logger.warning(f"Failed to generate active_session.md: {e}")

    # Generate project_index.md
    try:
        index_content = loader.render('_base/project_index.md.j2', context)
        write_file(target_path / "project_index.md", index_content)
        display_success("Initialized project_index.md")
    except Exception as e:
        logger.warning(f"Failed to generate project_index.md: {e}")
