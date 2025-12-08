#!/usr/bin/env python3
"""Utility functions for Agentic Workflow CLI."""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import structlog

console = Console()

def setup_logging(verbose: bool = False, log_level: str = "INFO"):
    """Setup structured logging."""
    import logging
    from structlog import WriteLoggerFactory
    from structlog.processors import JSONRenderer

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if verbose:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.processors.KeyValueRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=WriteLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_project_root() -> Optional[Path]:
    """Find the project root directory by looking for project structure."""
    current = Path.cwd()
    
    # Walk up the directory tree
    for path in [current] + list(current.parents):
        # Check for project indicators
        if (path / "agent_files").exists() and (path / "agent_context").exists():
            return path
    
    return None

def is_in_project() -> bool:
    """Check if we're currently in a project directory."""
    return get_project_root() is not None

def format_output(data: Any, format_type: str = "table", title: str = None):
    """Format data for output in various formats."""
    if format_type == "json":
        import json
        console.print_json(json.dumps(data, indent=2, default=str))
    elif format_type == "yaml":
        import yaml
        console.print(yaml.dump(data, default_flow_style=False))
    elif format_type == "table":
        if isinstance(data, list) and data:
            table = Table(title=title)
            # Get headers from first item
            headers = list(data[0].keys()) if isinstance(data[0], dict) else ["Value"]
            for header in headers:
                table.add_column(header, style="cyan")

            for item in data:
                if isinstance(item, dict):
                    row = [str(item.get(h, "")) for h in headers]
                else:
                    row = [str(item)]
                table.add_row(*row)
            console.print(table)
        elif isinstance(data, dict):
            table = Table(title=title)
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            for key, value in data.items():
                table.add_row(key, str(value))
            console.print(table)
        else:
            console.print(data)
    else:
        console.print(data)

def confirm_action(message: str, default: bool = False) -> bool:
    """Get user confirmation for an action."""
    return click.confirm(message, default=default)

def show_progress(message: str):
    """Show a progress indicator."""
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[bold green]{message}"),
        console=console,
    )

def display_error(message: str, exit_code: int = 1):
    """Display an error message and exit."""
    console.print(f"[red]Error:[/red] {message}")
    sys.exit(exit_code)

def display_success(message: str):
    """Display a success message."""
    console.print(f"[green]✓[/green] {message}")

def display_warning(message: str):
    """Display a warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")

def display_info(message: str):
    """Display an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


# Phase 1: Enhanced Display Functions for UI Standardization

def display_status_panel(project_name: str, status_data: Dict[str, Any]):
    """Display project status in a structured table panel."""
    table = Table(title=f"[bold blue]Project Status: {project_name}[/bold blue]")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for key, value in status_data.items():
        formatted_key = key.replace('_', ' ').title()
        table.add_row(formatted_key, str(value))

    console.print(table)


def display_help_panel(title: str, commands: List[Dict[str, str]]):
    """Display help in a rich panel with formatted commands."""
    if not commands:
        return

    # Create table for commands
    table = Table(box=None, pad_edge=False)
    table.add_column("Command", style="green", no_wrap=True)
    table.add_column("Description", style="white", overflow="fold")  # Allow wrapping

    for cmd in commands:
        table.add_row(cmd.get('command', ''), cmd.get('description', ''))

    panel = Panel(
        table,
        title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def display_action_result(action: str, success: bool, details: List[str] = None, icon: str = None):
    """Standardized action completion display with optional details."""
    if icon is None:
        icon = "✓" if success else "✗"
    color = "green" if success else "red"

    console.print(f"[{color}]{icon}[/{color}] {action}")
    if details:
        for detail in details:
            console.print(f"[{color}]  └─[/{color}] {detail}")


def display_project_summary(project_name: str, workflow: str, directories: List[str], next_steps: List[str]):
    """Display project creation summary in a structured panel."""
    # Create directories list
    dir_content = "\n".join(f"  • {d}" for d in directories)

    # Create next steps list
    steps_content = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(next_steps))

    content = f"""[bold white]Workflow:[/bold white] {workflow}
[bold white]Location:[/bold white] projects/{project_name}

[bold white]Created directories:[/bold white]
{dir_content}

[bold white]Next steps:[/bold white]
{steps_content}"""

    panel = Panel(
        content,
        title="[bold green]🎉 Project Created[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)


# Phase 1: Path Handling Utilities

def shorten_path(path: str, max_length: int = 60) -> str:
    """Shorten paths for display readability."""
    path_obj = Path(path)
    path_str = str(path)

    if len(path_str) <= max_length:
        return path_str

    # Try relative to project root
    project_root = get_project_root()
    if project_root:
        try:
            rel_path = path_obj.relative_to(project_root)
            rel_str = str(rel_path)
            if len(rel_str) < len(path_str):
                return rel_str
        except ValueError:
            pass

    # Try relative to current directory
    try:
        rel_path = path_obj.relative_to(Path.cwd())
        rel_str = str(rel_path)
        if len(rel_str) < len(path_str):
            return f"./{rel_str}"
    except ValueError:
        pass

    # Fallback: truncate with ellipsis
    return f"...{path_str[-max_length+3:]}"


def format_file_list(files: List[str], prefix: str = "✓ Generated:", max_line_length: int = 80) -> List[str]:
    """Format a list of files with proper line breaking."""
    formatted_lines = []
    for file_path in files:
        short_path = shorten_path(file_path)
        line = f"{prefix} {short_path}"

        if len(line) <= max_line_length:
            formatted_lines.append(line)
        else:
            # Break long lines
            formatted_lines.append(f"{prefix}")
            formatted_lines.append(f"  {short_path}")

    return formatted_lines


def is_in_project() -> bool:
    """Check if we're currently in a project directory."""
    return get_project_root() is not None

def validate_project_name(name: str) -> bool:
    """Validate a project name."""
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

def create_project_structure(project_path: Path, workflow_type: str):
    """Create the standard project directory structure and generate initial files."""
    # Load workflow configuration to get directory structure
    canonical_data = load_canonical_workflow_data(workflow_type)
    workflow_data = canonical_data.get('workflow', {})
    directories_config = workflow_data.get('directories', {})
    
    # Default directories if not specified in workflow
    default_dirs = [
        "agent_files",
        "agent_context", 
        "agent_log",
        "artifacts",
        "docs",
        "input",
        "package",
    ]
    
    # Use workflow-specific directories or fall back to defaults
    dirs_to_create = []
    for key, path in directories_config.items():
        if key != 'root' and key != 'templates':  # Skip root and templates
            # Remove any {project_name} placeholders and trailing slashes
            clean_path = path.replace('{project_name}', '').strip('/')
            if clean_path:
                dirs_to_create.append(clean_path)
    
    # Fall back to defaults if workflow doesn't specify
    if not dirs_to_create:
        dirs_to_create = default_dirs
    
    # Create the directories
    for dir_name in dirs_to_create:
        (project_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Create agent-specific artifact subdirectories
    artifacts_dir = project_path / directories_config.get('artifacts', 'artifacts')
    agents_list = canonical_data.get('agents', {}).get('agents', [])
    for agent in agents_list:
        agent_slug = agent.get('slug', agent['id'].replace('-', '_'))
        agent_artifacts_dir = artifacts_dir / agent_slug
        agent_artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Create workflow script
    workflow_script = f"""#!/bin/bash
# Agentic Workflow CLI wrapper for {project_path.name}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Try different methods to run the CLI
if command -v agentic >/dev/null 2>&1 && agentic --help >/dev/null 2>&1; then
    # Use installed package
    cd "$PROJECT_DIR" && agentic "$@"
else
    # Try development mode - look for source relative to script location
    WORKFLOW_ROOT="$(cd "$SCRIPT_DIR/../../../agentic_worflow" 2>/dev/null && pwd)"
    if [ -f "$WORKFLOW_ROOT/src/agentic_workflow/cli/main.py" ]; then
        cd "$PROJECT_DIR" && PYTHONPATH="$WORKFLOW_ROOT/src" python3 -c "
from agentic_workflow.cli.main import cli
import sys
sys.argv = ['agentic'] + sys.argv[1:]
cli()
" "$@"
    else
        echo "Error: Could not find agentic workflow installation"
        echo "Please ensure the package is installed or run from source directory"
        exit 1
    fi
fi
"""
    (project_path / "workflow").write_text(workflow_script)
    (project_path / "workflow").chmod(0o755)

    # Generate initial project files using templates
    try:
        generate_project_files(project_path, workflow_type)
    except Exception as e:
        # Log warning but don't fail project creation
        console.print(f"[yellow]Warning: Could not generate project files: {e}[/yellow]")

def generate_project_files(project_path: Path, workflow_type: str):
    """Generate initial project files using templates and canonical data."""
    project_name = project_path.name

    # Load canonical data
    canonical_data = load_canonical_workflow_data(workflow_type)

    # Generate project index
    project_index_context = {
        'project_name': project_name,
        'workflow_name': workflow_type,
        'workflow_display_name': canonical_data.get('workflow', {}).get('display_name', workflow_type),
        'timestamp': str(Path.cwd()),
        'agents': canonical_data.get('agents', {}).get('agents', []),
        'artifacts': canonical_data.get('artifacts', {}).get('artifacts', []),
    }

    project_index_content = render_template('_base/project_index.md.j2', project_index_context, workflow_type)
    (project_path / "docs" / "project_index.md").write_text(project_index_content)

    # Generate agent files
    agents = canonical_data.get('agents', {}).get('agents', [])
    for agent in agents:
        agent_id = agent['id']
        try:
            # Build agent context
            agent_context = build_agent_context(workflow_type, agent_id, project_name)

            # Render agent template
            agent_content = render_template('_base/agent_base.md.j2', agent_context, workflow_type)

            # Save agent file
            agent_filename = f"{agent_id.replace('-', '_')}.md"
            (project_path / "agent_files" / agent_filename).write_text(agent_content)

        except Exception as e:
            console.print(f"[yellow]Warning: Could not generate agent file for {agent_id}: {e}[/yellow]")

    # Session initialization is now handled by runtime.py

    # Generate governance documentation
    try:
        governance_context = {
            'project_name': project_name,
            'workflow_name': workflow_type,
            'workflow_data': canonical_data.get('workflow', {}),
            'timestamp': str(Path.cwd()),
        }

        governance_content = render_template('docs/GOVERNANCE_GUIDE.md.j2', governance_context, workflow_type)
        (project_path / "docs" / "GOVERNANCE_GUIDE.md").write_text(governance_content)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not generate governance guide: {e}[/yellow]")

    # Generate initial artifact stubs for required artifacts
    try:
        generate_initial_artifacts(project_path, canonical_data, workflow_type)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not generate initial artifacts: {e}[/yellow]")

def generate_initial_artifacts(project_path: Path, canonical_data: Dict[str, Any], workflow_type: str):
    """Generate initial artifact stub files for required artifacts."""
    artifacts_data = canonical_data.get('artifacts', {}).get('artifacts', [])
    workflow_data = canonical_data.get('workflow', {})
    directories_config = workflow_data.get('directories', {})
    
    artifacts_dir = project_path / directories_config.get('artifacts', 'artifacts')
    
    for artifact in artifacts_data:
        if artifact.get('required', False):
            filename = artifact['filename']
            owner = artifact.get('owner', 'unknown')
            description = artifact.get('description', 'No description available')
            category = artifact.get('category', 'core')
            
            # Determine the subdirectory based on owner agent
            agent_slug = None
            agents_list = canonical_data.get('agents', {}).get('agents', [])
            for agent in agents_list:
                if agent['id'] == owner:
                    agent_slug = agent.get('slug', agent['id'].replace('-', '_'))
                    break
            
            # Create the full path
            if agent_slug and category != 'core':
                artifact_path = artifacts_dir / agent_slug / filename
            else:
                artifact_path = artifacts_dir / filename
            
            # Create parent directories
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate stub content based on artifact type
            if filename.endswith('.md'):
                stub_content = f"""# {filename.replace('.md', '').replace('_', ' ').title()}

**Owner:** {owner}
**Category:** {category}
**Status:** Stub - Not yet implemented

## Description

{description}

## Purpose

{artifact.get('purpose', 'To be defined by the responsible agent.')}

## Contents

*This is a placeholder file. The actual content will be generated by Agent {owner} during the workflow execution.*

## Metadata

- **Created:** {Path.cwd()}
- **Workflow:** {workflow_type}
- **Required:** {artifact.get('required', False)}
- **Gating:** {artifact.get('is_gating', False)}
- **Shared:** {artifact.get('is_shared', False)}
"""
            else:
                # For non-markdown files, create a simple placeholder
                stub_content = f"""# Placeholder for {filename}

This file will be replaced with actual content by Agent {owner}.

Description: {description}
Category: {category}
Required: {artifact.get('required', False)}
"""

            # Write the stub file
            with open(artifact_path, 'w') as f:
                f.write(stub_content)

def load_workflow_manifest(workflow_type: str) -> Dict[str, Any]:
    """Load workflow manifest using the new config system."""
    from ..core.project_generation import WorkflowLoader
    try:
        loader = WorkflowLoader()
        return loader.load_workflow_manifest(workflow_type)
    except Exception as e:
        raise click.ClickException(f"Failed to load workflow '{workflow_type}': {e}")

def load_canonical_workflow_data(workflow_type: str) -> Dict[str, Any]:
    """Load canonical workflow data using the new config system."""
    from ..core.project_generation import WorkflowLoader
    try:
        loader = WorkflowLoader()
        return loader.load_workflow_manifest(workflow_type)
    except Exception as e:
        raise click.ClickException(f"Failed to load canonical data for workflow '{workflow_type}': {e}")

def render_template(template_name: str, context: Dict[str, Any], workflow_type: str = None) -> str:
    """Render a Jinja2 template with the given context."""
    from ..core.paths import get_package_root
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    import os

    templates_dir = get_package_root() / "templates"

    # Setup Jinja2 environment with custom loader that handles hierarchy
    class HierarchicalLoader(FileSystemLoader):
        def __init__(self, search_paths):
            self.search_paths = search_paths

        def get_source(self, environment, template):
            for search_path in self.search_paths:
                full_path = os.path.join(search_path, template)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        contents = f.read()
                    return contents, full_path, lambda: False
            raise FileNotFoundError(f"Template '{template}' not found in search paths")

    # Build search paths in priority order
    search_paths = []

    # 1. Workflow-specific templates
    if workflow_type:
        workflow_templates = templates_dir / ".." / "manifests" / "workflows" / workflow_type / "templates"
        if workflow_templates.exists():
            search_paths.append(str(workflow_templates))

    # 2. Workflow group templates
    if workflow_type:
        workflow_group = templates_dir / workflow_type
        if workflow_group.exists():
            search_paths.append(str(workflow_group))

    # 3. Role-based templates (would need role detection)
    # search_paths.append(str(templates_dir / "_roles" / role))

    # 4. Base templates
    search_paths.append(str(templates_dir / "_base"))

    # 5. Partials
    search_paths.append(str(templates_dir / "_partials"))

    # 6. Root templates
    search_paths.append(str(templates_dir))

    # Setup Jinja2 environment
    env = Environment(
        loader=HierarchicalLoader(search_paths),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )

    # Add custom filters if needed
    def markdown_filter(text):
        """Basic markdown filter for template variables."""
        return text  # Could add markdown processing here

    env.filters['markdown'] = markdown_filter

    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        raise click.ClickException(f"Template rendering failed for '{template_name}': {e}")

def build_agent_context(workflow_type: str, agent_id: str, project_name: str) -> Dict[str, Any]:
    """Build the complete context for rendering an agent template."""
    # Load canonical data
    canonical_data = load_canonical_workflow_data(workflow_type)

    # Helper function to transform artifact strings to objects
    def transform_artifacts(artifact_list, artifacts_data):
        """Transform list of artifact filenames to objects with filename and description."""
        if not artifact_list:
            return []
        
        transformed = []
        artifacts_lookup = {art['filename']: art for art in artifacts_data.get('artifacts', [])}
        
        for artifact in artifact_list:
            if isinstance(artifact, str):
                # Simple filename string
                filename = artifact
                description = artifacts_lookup.get(filename, {}).get('description', '-')
                transformed.append({'filename': filename, 'description': description})
            elif isinstance(artifact, dict) and 'file' in artifact:
                # Complex artifact with requirements
                filename = artifact['file']
                description = artifacts_lookup.get(filename, {}).get('description', '-')
                transformed.append({'filename': filename, 'description': description, 'required': artifact.get('required', True)})
            else:
                # Already transformed object
                transformed.append(artifact)
        
        return transformed

    # Find the specific agent
    agent_data = None
    agents_list = canonical_data.get('agents', {}).get('agents', [])
    for agent in agents_list:
        if agent['id'] == agent_id:
            agent_data = agent
            break

    if not agent_data:
        raise click.ClickException(f"Agent '{agent_id}' not found in workflow '{workflow_type}'")

    # Find agent instructions
    instructions_data = None
    instructions_list = canonical_data.get('instructions', {}).get('instructions', [])
    for instruction in instructions_list:
        if instruction.get('id') == agent_id:
            instructions_data = instruction
            break

    # Find next agent in pipeline
    workflow_data = canonical_data.get('workflow', {})
    pipeline = workflow_data.get('pipeline', {}).get('order', [])
    next_agent_id = None
    try:
        current_index = pipeline.index(agent_id)
        if current_index + 1 < len(pipeline):
            next_agent_id = pipeline[current_index + 1]
    except ValueError:
        pass

    # Get required artifacts for handoff
    required_artifacts = []
    if next_agent_id:
        # Find what the next agent consumes
        for agent in agents_list:
            if agent['id'] == next_agent_id:
                consumes_core = agent.get('consumes', {}).get('core', [])
                required_artifacts = [item.get('file', '') for item in consumes_core if isinstance(item, dict)]
                break

    # Build comprehensive context
    context = {
        # Project info
        'project_name': project_name,
        'workflow_name': workflow_type,
        'workflow_display_name': workflow_data.get('display_name', workflow_type),
        'timestamp': str(Path.cwd()),  # Should use proper timestamp

        # Agent identity
        'agent_id': agent_data['id'],
        'agent_role': agent_data['role'],
        'agent_type': agent_data['agent_type'],
        'agent_slug': agent_data['slug'],
        'agent_description': agent_data['description'],
        'key_responsibilities': agent_data.get('key_responsibilities', []),

        # Instructions
        'purpose': instructions_data.get('purpose', '') if instructions_data else '',
        'responsibilities': instructions_data.get('responsibilities', []) if instructions_data else [],
        'domain_rules': instructions_data.get('domain_rules', []) if instructions_data else [],
        'guidance': instructions_data.get('guidance', '') if instructions_data else '',
        'examples': instructions_data.get('examples', []) if instructions_data else [],

        # Workflow sections
        'workflow': {
            'entry_conditions': instructions_data.get('workflow', {}).get('entry_conditions', []) if instructions_data else [],
            'steps': instructions_data.get('workflow', {}).get('steps', []) if instructions_data else [],
            'exit_conditions': instructions_data.get('workflow', {}).get('exit_conditions', []) if instructions_data else [],
        },

        # Boundaries
        'boundaries': {
            'in_scope': instructions_data.get('boundaries', {}).get('in_scope', []) if instructions_data else [],
            'out_of_scope': instructions_data.get('boundaries', {}).get('out_of_scope', []) if instructions_data else [],
        },

        # Handoff information
        'handoff': {
            'next': [{'id': next_agent_id}] if next_agent_id else [],
            'required_artifacts': required_artifacts,
            'required_logs': instructions_data.get('handoff', {}).get('required_logs', []) if instructions_data else [],
            'conditions': instructions_data.get('handoff', {}).get('conditions', []) if instructions_data else [],
        },

        # Artifacts (organized by tier) - TRANSFORM TO OBJECTS
        'produces': {
            'core': transform_artifacts(agent_data.get('produces', {}).get('core', []), canonical_data.get('artifacts', {})),
            'domain': transform_artifacts(agent_data.get('produces', {}).get('domain', []), canonical_data.get('artifacts', {})),
            'log': transform_artifacts(agent_data.get('produces', {}).get('log', []), canonical_data.get('artifacts', {})),
        },
        'consumes': {
            'core': transform_artifacts(agent_data.get('consumes', {}).get('core', []), canonical_data.get('artifacts', {})),
            'domain': transform_artifacts(agent_data.get('consumes', {}).get('domain', []), canonical_data.get('artifacts', {})),
            'reference': transform_artifacts(agent_data.get('consumes', {}).get('reference', []), canonical_data.get('artifacts', {})),
            'gating': transform_artifacts(agent_data.get('consumes', {}).get('gating', []), canonical_data.get('artifacts', {})),
        },

        # Next agent info
        'next_agent_id': next_agent_id,
        'required_artifacts': required_artifacts,

        # Workflow metadata
        'workflow_data': workflow_data,
        'artifacts_data': canonical_data.get('artifacts', {}),
        'agents_data': canonical_data.get('agents', {}),

        # Display settings
        'display': workflow_data.get('display', {}),
    }

    return context