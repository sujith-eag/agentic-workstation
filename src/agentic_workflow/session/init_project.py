#!/usr/bin/env python3
"""Initialize a new project structure.

This module orchestrates project initialization using modular generators.
The actual content generation is delegated to:
- generators.docs: Document generation
- generators.index: Project index generation
- generators.session: Session file generation
- generation.generate_agents: Agent file generation

Usage:
    python3 -m scripts.session.init_project --project 
    python3 -m scripts.session.init_project --project  --workflow planning
"""
import json
import sys
import datetime
from pathlib import Path

# YAML is still needed for ledger sidecar files
try:
    import yaml
except ImportError:
    display_error("pyyaml required for ledger files")
    sys.exit(1)

# Core imports
from agentic_workflow.core.paths import get_templates_dir, get_projects_dir
from agentic_workflow.core.io import create_directory, write_file, make_executable
from agentic_workflow.core.project import PROJECT_CONFIG_FILE

# Workflow imports
from agentic_workflow.workflow import load_workflow, get_default_workflow, WorkflowError

# Generator imports
from agentic_workflow.generators.docs import (
    generate_cli_reference,
    generate_agent_pipeline,
    generate_artifact_registry,
    generate_governance,
    generate_copilot_instructions,
    generate_gemini_instructions,
)
from agentic_workflow.generators.index import generate_project_index
from agentic_workflow.generators.session import (
    build_session_substitutions,
    get_orchestrator_context_data,
)

# Session imports
from agentic_workflow.session import session_frontmatter as sf

# Agent generation - use Jinja2-based generator
from agentic_workflow.generation.generate_agents import generate_agents


from agentic_workflow.utils.jinja_loader import JinjaTemplateLoader
from agentic_workflow.cli.utils import display_success, display_info, display_warning, display_error


def _create_agent_directories(artifacts_dir: Path, wf) -> None:
    """Create agent artifact directories from workflow package.
    
    Args:
        artifacts_dir: Path to artifacts directory.
        wf: WorkflowPackage instance.
    """
    for agent in wf.agents:
        agent_id = agent['id']
        slug = agent.get('slug', f"agent_{agent_id}")
        
        # Format directory name using workflow's format
        formatted_id = wf.format_agent_id(agent_id)
        dir_name = f"{formatted_id}_{slug}"
        
        create_directory(artifacts_dir / dir_name)


def _create_log_files(logs_dir: Path, project_name: str, workflow_name: str) -> None:
    """Create log files with YAML sidecars.
    
    Args:
        logs_dir: Path to agent_log directory.
        project_name: Project name.
        workflow_name: Workflow name.
    """
    timestamp = datetime.datetime.now().isoformat()
    loader = JinjaTemplateLoader()
    
    log_templates = [
        ("logs/exchange_log.md.j2", "exchange_log.md", {
            'handoffs': [], 'feedback': [], 'iterations': [], 'archives': []
        }),
        ("logs/context_log.md.j2", "context_log.md", {
            'sessions': [], 'decisions': [], 'assumptions': [], 'blockers': [], 'archives': []
        }),
    ]
    
    for tpl_name, dest_name, yaml_sections in log_templates:
        dest_path = logs_dir / dest_name
        yaml_path = dest_path.with_suffix('.yaml')
        
        if dest_path.exists():
            display_info(f"Log file exists (skipping): {dest_path}")
            continue
        
        # Create markdown log
        context = {
            "project_name": project_name,
            "timestamp": timestamp
        }
        content = loader.render(tpl_name, context)
        write_file(dest_path, content)
        display_success(f"Created log file: /{dest_path.relative_to(get_projects_dir())}")
        
        # Create YAML sidecar
        if not yaml_path.exists():
            # Ledger sidecars should be lists of entries (ledger style).
            # Use an empty list for canonical ledger files so writers like
            # `write_log()` can safely `append()` new entries.
            try:
                # For contextual metadata that should be preserved, write
                # a separate metadata file alongside the ledger (e.g., .meta.yaml).
                with open(yaml_path, "w") as f:
                    yaml.safe_dump([], f, sort_keys=False)
                meta_path = yaml_path.with_name(yaml_path.stem + ".meta.yaml")
                meta_data = {
                    'project': project_name,
                    'workflow': workflow_name,
                    'created': timestamp,
                    'last_updated': timestamp,
                    **yaml_sections,
                }
                with open(meta_path, "w") as mf:
                    yaml.safe_dump(meta_data, mf, sort_keys=False)
                display_success(f"Created YAML sidecar (ledger list): /{yaml_path.relative_to(get_projects_dir())}")
                display_success(f"Created YAML metadata sidecar: /{meta_path.relative_to(get_projects_dir())}")
            except Exception:
                # Fallback: write an empty list
                with open(yaml_path, "w") as f:
                    yaml.safe_dump([], f, sort_keys=False)
                display_success(f"Created YAML sidecar (fallback list): /{yaml_path.relative_to(get_projects_dir())}")


def _create_project_metadata(project_dir: Path, project_name: str, wf, timestamp: str, description: str = None) -> None:
    """Create project metadata file with workflow info.
    
    Args:
        project_dir: Path to project directory.
        project_name: Project name.
        wf: WorkflowPackage instance.
        timestamp: ISO format timestamp.
        description: Project description.
    """
    meta_path = project_dir / PROJECT_CONFIG_FILE
    meta_data = {
        'project': project_name,
        'workflow': wf.name,
        'workflow_version': wf.version,
        'created': timestamp,
    }
    
    # Add description if provided
    if description:
        meta_data['description'] = description
    
    # Workflows with stages get stage tracking
    if wf.stages:
        initial_stage = wf.stages[0].get('id', 'INTAKE')
        meta_data['current_stage'] = initial_stage
        meta_data['stage_history'] = [{'stage': initial_stage, 'timestamp': timestamp}]
    
    # Workflows with source_project configuration get linked project tracking
    source_config = wf.metadata.get('source_project', {})
    if source_config:
        meta_data['linked_planning_project'] = None
        create_directory(project_dir / "input" / "planning_artifacts")
    
    # Workflows with TDD configuration get enforcement tracking
    tdd_config = wf.metadata.get('tdd', {})
    if tdd_config:
        meta_data['tdd_enforcement'] = tdd_config.get('enforce', True)
    
    with open(meta_path, "w") as f:
        json.dump(meta_data, f, indent=2)
    display_success(f"Created project metadata: /{meta_path.relative_to(get_projects_dir())}")


def _create_artifact_subdirs(artifacts_dir: Path, wf) -> None:
    """Create workflow-specific artifact subdirectories.
    
    Args:
        artifacts_dir: Path to artifacts directory.
        wf: WorkflowPackage instance.
    """
    artifact_dirs = wf.metadata.get('artifact_directories', [])
    if artifact_dirs:
        for subdir in artifact_dirs:
            create_directory(artifacts_dir / subdir)
    elif wf.focus == 'implementation':
        # Default implementation directories
        for subdir in ['code', 'tests', 'specs', 'observability', 'audits']:
            create_directory(artifacts_dir / subdir)


def _create_code_directories(package_dir: Path, wf) -> None:
    """Create code/output directory structure for workflows.
    
    Args:
        package_dir: Path to package directory (or project root for output_directories).
        wf: WorkflowPackage instance.
    """
    # Check for code_directories (implementation workflow)
    code_config = wf.metadata.get('code_directories', {})
    
    # Also check for output_directories (research workflow)
    output_config = wf.metadata.get('output_directories', {})
    
    if code_config:
        structure = code_config.get('structure', [])
        for subdir in structure:
            subdir = subdir.rstrip('/')
            create_directory(package_dir / subdir)
        if structure:
            display_success(f"Created code structure in /{package_dir.relative_to(get_projects_dir())}/")
    
    if output_config:
        # For output_directories, create under project root (not package)
        root = output_config.get('root', 'output')
        output_root = package_dir.parent / root
        structure = output_config.get('structure', [])
        for subdir in structure:
            subdir = subdir.rstrip('/')
            create_directory(output_root / subdir)
        if structure:
            display_success(f"Created output structure in /{output_root.relative_to(get_projects_dir())}/")
    
    # Default fallback only for implementation focus
    if not code_config and not output_config:
        if wf.focus != 'implementation':
            return
        # Default structure if not specified
        default_structure = ['src/', 'tests/', 'docs/']
        for subdir in default_structure:
            subdir = subdir.rstrip('/')
            create_directory(package_dir / subdir)


def _generate_docs(project_dir: Path, project_name: str, wf) -> None:
    """Generate all documentation files.
    
    Args:
        project_dir: Path to project directory.
        project_name: Project name.
        wf: WorkflowPackage instance.
    """
    docs_dir = project_dir / "docs"
    create_directory(docs_dir)
    
    # Get source workflow for input artifacts (if any)
    source_workflow_name = wf.metadata.get('source_project', {}).get('workflow')
    source_wf = None
    if source_workflow_name:
        try:
            source_wf = load_workflow(source_workflow_name)
        except WorkflowError:
            pass
    
    # Generate docs using generators module
    docs_to_generate = [
        ("GOVERNANCE_GUIDE.md", generate_governance(project_name, wf)),
        ("CLI_REFERENCE.md", generate_cli_reference(project_name, wf)),
        ("AGENT_PIPELINE.md", generate_agent_pipeline(wf)),
        ("ARTIFACT_REGISTRY.md", generate_artifact_registry(wf, source_wf)),
    ]
    
    for filename, content in docs_to_generate:
        if content:
            path = docs_dir / filename
            write_file(path, content)
            display_success(f"Generated: /{path.relative_to(get_projects_dir())}")


def _generate_github_files(project_dir: Path, project_name: str, wf) -> None:
    """Generate .github folder with AI instructions.
    
    Args:
        project_dir: Path to project directory.
        project_name: Project name.
        wf: WorkflowPackage instance.
    """
    github_dir = project_dir / ".github"
    create_directory(github_dir)
    
    # Copilot instructions
    copilot_path = github_dir / "copilot-instructions.md"
    if not copilot_path.exists():
        content = generate_copilot_instructions(project_name, wf)
        if content:
            write_file(copilot_path, content)
            display_success(f"Created: /{copilot_path.relative_to(get_projects_dir())}")
    
    # Gemini instructions
    gemini_path = github_dir / "GEMINI.md"
    if not gemini_path.exists():
        content = generate_gemini_instructions(project_name, wf)
        if content:
            write_file(gemini_path, content)
            display_success(f"Created: /{gemini_path.relative_to(get_projects_dir())}")


def _generate_active_session(context_dir: Path, project_name: str, wf) -> None:
    """Generate initial active_session.md.
    
    Args:
        context_dir: Path to agent_context directory.
        project_name: Project name.
        wf: WorkflowPackage instance.
    """
    # Get first agent from pipeline
    if not wf.pipeline_order:
        raise ValueError(f"Workflow {wf.name} has no pipeline order defined")
    
    first_agent_id = wf.pipeline_order[0]
    first_agent = wf.get_agent(first_agent_id)
    if not first_agent:
        raise ValueError(f"Agent {first_agent_id} not found in workflow {wf.name}")
    
    first_agent_name = first_agent.get('role', first_agent_id)
    
    # Create an uninitialized session instead of activating the orchestrator
    content = f"""---
session_type: uninitialized
project_name: {project_name}
workflow_name: {wf.name}
status: ready_for_activation
timestamp: {datetime.datetime.now().isoformat()}
---

# WORKFLOW READY FOR ACTIVATION

The project has been initialized and is ready for the first agent activation.

## Next Steps

1. **Activate the first agent:**
   ```bash
   ./workflow activate {first_agent_id}
   ```

2. **Review project context** in `project_index.md`

3. **Begin producing artifacts** in the `artifacts/` directory

## Workflow Status

- **Status:** Ready for activation
- **Next Agent:** {first_agent_id} ({first_agent_name})
- **Workflow:** {wf.display_name}
"""
    
    dest_path = context_dir / "active_session.md"
    sf.write_session_file(dest_path, content)
    display_success(f"Generated: /{dest_path.relative_to(get_projects_dir())}")
    
    # Create orchestrator context file (but don't activate the session)
    project_dir = context_dir.parent
    orchestrator_data = get_orchestrator_context_data(wf)
    created = sf.ensure_context_file(
        project_dir, 
        'agent_context/orchestrator_context_index.md', 
        orchestrator_data, 
        get_templates_dir()
    )
    if created:
        display_success(f"Generated: /{project_dir.relative_to(get_projects_dir())}/agent_context/orchestrator_context_index.md")


def _generate_project_index(project_dir: Path, project_name: str, wf) -> None:
    """Generate project_index.md.
    
    Args:
        project_dir: Path to project directory.
        project_name: Project name.
        wf: WorkflowPackage instance.
    """
    content = generate_project_index(project_name, wf)
    dest_path = project_dir / "project_index.md"
    write_file(dest_path, content)
    display_success(f"Generated: /{dest_path.relative_to(get_projects_dir())}")


def _create_workflow_wrapper(project_dir: Path) -> None:
    """Create project-local workflow wrapper script.
    
    Args:
        project_dir: Path to project directory.
    """
    workflow_tpl = get_templates_dir() / "workflow.tpl"
    workflow_dest = project_dir / "workflow"
    
    if workflow_dest.exists():
        display_info(f"Workflow wrapper exists: {workflow_dest}")
        return
        
    if not workflow_tpl.exists():
        display_warning("templates/workflow.tpl not found")
        return
    
    with open(workflow_tpl, "r") as f:
        content = f.read()
    write_file(workflow_dest, content)
    make_executable(workflow_dest)
    display_success(f"Created workflow wrapper: /{workflow_dest.relative_to(get_projects_dir())}")


def init_project(project_name: str, workflow_name: str = None, description: str = None) -> None:
    """Initialize a new project structure.
    
    Args:
        project_name: Name of the project to create.
        workflow_name: Workflow type (default: from registry).
        description: Project description.
    """
    project_dir = get_projects_dir() / project_name
    timestamp = datetime.datetime.now().isoformat()
    
    # Load workflow package
    workflow_name = workflow_name or get_default_workflow()
    try:
        wf = load_workflow(workflow_name)
        display_info(f"Using workflow: {wf.display_name} v{wf.version}")
    except WorkflowError as e:
        display_error(f"Error loading workflow '{workflow_name}': {e}")
        sys.exit(1)
    
    # Define directories
    input_dir = project_dir / "input"
    artifacts_dir = project_dir / "artifacts"
    package_dir = project_dir / "package"
    context_dir = project_dir / "agent_context"
    logs_dir = project_dir / "agent_log"
    
    display_info(f"Initializing project '{project_name}'...")
    
    # 1. Create base directories
    for dir_path in [input_dir, artifacts_dir, package_dir, context_dir, logs_dir]:
        create_directory(dir_path)
    
    # 2. Create agent artifact directories
    try:
        _create_agent_directories(artifacts_dir, wf)
    except Exception as e:
        display_warning(f"Failed to create agent directories: {e}")
    
    # 3. Create workflow-specific artifact subdirectories
    _create_artifact_subdirs(artifacts_dir, wf)
    
    # 4. Create code directories (for implementation workflows)
    _create_code_directories(package_dir, wf)
    
    # 5. Generate core files
    _generate_project_index(project_dir, project_name, wf)
    _generate_active_session(context_dir, project_name, wf)
    
    # 6. Generate documentation
    _generate_docs(project_dir, project_name, wf)
    
    # 7. Create log files
    _create_log_files(logs_dir, project_name, workflow_name)
    
    # 8. Create workflow wrapper
    _create_workflow_wrapper(project_dir)
    
    # 9. Create project metadata
    _create_project_metadata(project_dir, project_name, wf, timestamp, description)
    
    # 10. Generate agent files to project directory using Jinja2 templates
    agent_files_dir = project_dir / "agent_files"
    display_info(f"Generating agent files for workflow '{workflow_name}'...")
    agent_count = generate_agents(workflow_name, agent_files_dir, 
                                   project_name=project_name)
    try:
        shortened_agent_files = f"/{agent_files_dir.relative_to(get_projects_dir())}"
    except Exception:
        shortened_agent_files = str(agent_files_dir)
    display_success(f"Generated {agent_count} agent files in {shortened_agent_files}")
    
    # 11. Generate .github files
    _generate_github_files(project_dir, project_name, wf)
    
    # Summary
    display_success(f"Project '{project_name}' initialized successfully with workflow '{workflow_name}'.")
    display_info("Next steps:")
    display_info(f"  cd projects/{project_name}")
    display_info("  ./workflow status")
    display_info(f"  ./workflow activate {wf.orch_id}")
    display_info("Key paths:")
    try:
        shortened_artifacts = f"/{artifacts_dir.relative_to(get_projects_dir())}"
    except Exception:
        shortened_artifacts = str(artifacts_dir)
    try:
        shortened_index_path = f"/{(project_dir / 'project_index.md').relative_to(get_projects_dir())}"
    except Exception:
        shortened_index_path = str(project_dir / 'project_index.md')
    try:
        shortened_active = f"/{(context_dir / 'active_session.md').relative_to(get_projects_dir())}"
    except Exception:
        shortened_active = str(context_dir / 'active_session.md')
    display_info(f"  Artifacts: {shortened_artifacts}")
    display_info(f"  Index: {shortened_index_path}")
    display_info(f"  Active Session: {shortened_active}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Initialize a new project structure")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--workflow", "-w", default=None, 
                        help="Workflow type (default: from registry, typically 'planning')")
    args = parser.parse_args()
    
    init_project(args.project, args.workflow)
