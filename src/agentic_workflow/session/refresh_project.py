#!/usr/bin/env python3
"""Refresh regenerable files in an existing project.

This module safely refreshes files that are generated from workflow packages
and templates, while protecting persistent data (artifacts, logs, context).

Regenerable (safe to refresh):
- agent_files/          → Generated from workflow package
- docs/                 → Generated from templates + manifests
- project_index.md      → Generated from workflow artifacts
- .github/              → Generated from templates
- active_session.md     → Can be reset to orchestrator base

Protected (NEVER touched):
- artifacts/            → Agent work products
- agent_log/            → Audit trail, decision history
- agent_context/*_context_index.md → Accumulated context
- input/                → User-provided seed documents
- package/              → Curated outputs
- project_config.json   → Updated with refresh timestamp only

Usage:
    python3 -m scripts.session.refresh_project --project 
    python3 -m scripts.session.refresh_project --project  --agents
    python3 -m scripts.session.refresh_project --project  --docs
    python3 -m scripts.session.refresh_project --project  --dry-run
"""
import json
import sys
import datetime
import shutil
from pathlib import Path

# Use core modules
from agentic_workflow.core.paths import get_projects_dir, get_templates_dir
from agentic_workflow.core.project import load_project_meta, save_project_meta, PROJECT_CONFIG_FILE
from agentic_workflow.core.io import create_directory, write_file

# Workflow and generator imports
from agentic_workflow.workflow import load_workflow, get_default_workflow, WorkflowError
from agentic_workflow.generation.generate_agents import generate_agents_for_workflow
from agentic_workflow.generators.docs import (
    generate_cli_reference,
    generate_agent_pipeline,
    generate_artifact_registry,
    generate_governance,
    generate_copilot_instructions,
    generate_gemini_instructions,
)
from agentic_workflow.generators.index import generate_project_index
from agentic_workflow.generators.session import build_session_substitutions, get_orchestrator_context_data
from agentic_workflow.cli.utils import display_success, display_info, display_warning, display_error


def get_project_workflow(project_dir):
    """Get the workflow name and version for a project."""
    project_name = project_dir.name
    meta = load_project_meta(project_name)
    if meta:
        return meta.get('workflow', get_default_workflow()), meta.get('workflow_version', '0.0.0')
    return get_default_workflow(), '0.0.0'


def refresh_agents(project_dir, wf, dry_run=False):
    """Refresh agent files from workflow package.
    
    Completely regenerates projects//agent_files/ from workflow.
    """
    agent_files_dir = project_dir / 'agent_files'
    
    if dry_run:
        display_info(f"[DRY-RUN] Would regenerate {agent_files_dir}")
        return 0
    
    # Remove existing agent files
    if agent_files_dir.exists():
        shutil.rmtree(agent_files_dir)
        display_info(f"Cleared: {agent_files_dir}")
    
    # Regenerate from workflow
    count = generate_agents_for_workflow(wf.name, agent_files_dir)
    return count


def refresh_docs(project_dir, project_name, wf, dry_run=False):
    """Refresh documentation files from workflow and templates.
    
    Regenerates:
    - docs/CLI_REFERENCE.md
    - docs/AGENT_PIPELINE.md
    - docs/ARTIFACT_REGISTRY.md
    - docs/GOVERNANCE_GUIDE.md
    """
    docs_dir = project_dir / 'docs'
    
    if dry_run:
        display_info(f"[DRY-RUN] Would regenerate {docs_dir}")
        return
    
    # Remove existing docs
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
        display_info(f"Cleared: {docs_dir}")
    
    # Create docs directory
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
    
    display_success(f"Regenerated: /{docs_dir.relative_to(get_projects_dir())}")


def refresh_project_index(project_dir, project_name, wf, dry_run=False):
    """Refresh project_index.md from workflow artifacts."""
    index_path = project_dir / 'project_index.md'
    
    if dry_run:
        display_info(f"[DRY-RUN] Would regenerate {index_path}")
        return
    
    content = generate_project_index(project_name, wf)
    write_file(index_path, content)
    display_success(f"Regenerated: /{index_path.relative_to(get_projects_dir())}")


def refresh_github(project_dir, project_name, wf, dry_run=False):
    """Refresh .github/ AI instruction files."""
    github_dir = project_dir / '.github'
    
    if dry_run:
        display_info(f"[DRY-RUN] Would regenerate {github_dir}")
        return
    
    create_directory(github_dir)
    
    # Regenerate copilot instructions
    copilot_path = github_dir / 'copilot-instructions.md'
    copilot_content = generate_copilot_instructions(project_name, wf)
    if copilot_content:
        write_file(copilot_path, copilot_content)
        display_success(f"Regenerated: /{copilot_path.relative_to(get_projects_dir())}")
    
    # Regenerate Gemini instructions
    gemini_path = github_dir / 'GEMINI.md'
    gemini_content = generate_gemini_instructions(project_name, wf)
    if gemini_content:
        write_file(gemini_path, gemini_content)
        display_success(f"Regenerated: /{gemini_path.relative_to(get_projects_dir())}")


def refresh_active_session(project_dir, project_name, wf, dry_run=False):
    """Refresh active_session.md to orchestrator base state.
    
    Resets to clean orchestrator session from template.
    """
    from . import session_frontmatter as sf
    
    context_dir = project_dir / 'agent_context'
    session_path = context_dir / 'active_session.md'
    
    if dry_run:
        display_info(f"[DRY-RUN] Would reset {session_path}")
        return
    
    # Remove existing session file
    if session_path.exists():
        session_path.unlink()
        display_info(f"Cleared: {session_path}")
    
    # Build substitutions from workflow config
    import datetime
    extra_subs = build_session_substitutions(project_name, wf)

    # Build session using session_frontmatter helper (now uses Jinja loader)
    content = sf.build_orchestrator_session_from_template(
        wf.name,
        project_name,
        wf.orch_id,
        datetime.datetime.now().isoformat(),
        extra_subs=extra_subs,
        fm_extra={'created_at': datetime.datetime.now().isoformat()}
    )

    sf.write_session_file(session_path, content)
    display_success(f"Reset to orchestrator: /{session_path.relative_to(get_projects_dir())}")


def update_metadata(project_dir, wf, scope, dry_run=False):
    """Update project_config.json with refresh timestamp."""
    project_name = project_dir.name
    meta_path = project_dir / PROJECT_CONFIG_FILE
    
    if dry_run:
        display_info(f"[DRY-RUN] Would update {meta_path}")
        return
    
    meta = load_project_meta(project_name)
    if meta is None:
        meta = {}
    
    timestamp = datetime.datetime.now().isoformat()
    
    # Update metadata
    meta['last_refreshed'] = timestamp
    meta['workflow_version'] = wf.version
    
    # Add to refresh history
    if 'refresh_history' not in meta:
        meta['refresh_history'] = []
    
    meta['refresh_history'].append({
        'timestamp': timestamp,
        'scope': scope,
        'workflow_version': wf.version,
    })
    
    # Keep only last 10 refresh entries
    meta['refresh_history'] = meta['refresh_history'][-10:]
    
    save_project_meta(project_name, meta)
    
    display_success(f"Updated metadata: /{meta_path.relative_to(get_projects_dir())}")


def refresh_project(project_name, agents=True, docs=True, index=True, 
                    github=True, session=True, dry_run=False):
    """Refresh regenerable files in a project.
    
    Args:
        project_name: Name of the project to refresh
        agents: Refresh agent_files/
        docs: Refresh docs/
        index: Refresh project_index.md
        github: Refresh .github/
        session: Reset active_session.md
        dry_run: Preview without making changes
    
    Returns:
        True if successful, False otherwise
    """
    project_dir = get_projects_dir() / project_name
    
    if not project_dir.exists():
        display_error(f"Project '{project_name}' does not exist.")
        display_info(f"Use 'workflow init {project_name}' to create a new project.")
        return False
    
    # Get project's workflow
    workflow_name, workflow_version = get_project_workflow(project_dir)
    
    try:
        wf = load_workflow(workflow_name)
    except WorkflowError as e:
        display_error(f"Error loading workflow '{workflow_name}': {e}")
        return False
    
    # Check for version mismatch
    if workflow_version != wf.version:
        display_warning(f"Workflow version changed: {workflow_version} → {wf.version}")
    
    display_info(f"Refreshing project '{project_name}' (workflow: {wf.name} v{wf.version})")
    
    if dry_run:
        display_info("[DRY-RUN MODE - No changes will be made]")
    
    # Track what was refreshed
    scope = []
    
    # Refresh components
    if agents:
        display_info("Agent Files:")
        count = refresh_agents(project_dir, wf, dry_run)
        if not dry_run:
            display_success(f"Generated {count} agent files")
        scope.append('agents')
    
    if docs:
        display_info("Documentation:")
        refresh_docs(project_dir, project_name, wf, dry_run)
        scope.append('docs')
    
    if index:
        display_info("Project Index:")
        refresh_project_index(project_dir, project_name, wf, dry_run)
        scope.append('index')
    
    if github:
        display_info("AI Instructions (.github/):")
        refresh_github(project_dir, project_name, wf, dry_run)
        scope.append('github')
    
    if session:
        display_info("Active Session:")
        refresh_active_session(project_dir, project_name, wf, dry_run)
        scope.append('session')
    
    # Update metadata
    display_info("Metadata:")
    update_metadata(project_dir, wf, scope, dry_run)
    
    if dry_run:
        display_info("DRY-RUN complete. No changes were made.")
    else:
        display_success(f"Refresh complete. Scope: {', '.join(scope)}")
    
    # Remind about protected directories
    display_warning("Protected (not touched):")
    display_info("   - artifacts/     (agent work products)")
    display_info("   - agent_log/     (exchange_log, context_log)")
    display_info("   - agent_context/*_context_index.md (accumulated context)")
    display_info("   - input/         (user seed documents)")
    display_info("   - package/       (curated outputs)")
    
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Refresh regenerable files in an existing project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Protected directories (NEVER touched):
  artifacts/      - Agent work products
  agent_log/      - Exchange log, context log, YAML sidecars
  agent_context/  - Context index files (accumulated data)
  input/          - User-provided seed documents
  package/        - Curated deliverables

Examples:
  # Refresh everything regenerable
  python3 -m scripts.session.refresh_project --project myproject
  
  # Refresh only agent files
  python3 -m scripts.session.refresh_project --project myproject --agents-only
  
  # Refresh only docs
  python3 -m scripts.session.refresh_project --project myproject --docs-only
  
  # Preview changes without applying
  python3 -m scripts.session.refresh_project --project myproject --dry-run
"""
    )
    parser.add_argument('--project', '-p', required=True, help='Project name')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    
    # Scope flags
    parser.add_argument('--agents-only', action='store_true', help='Refresh only agent files')
    parser.add_argument('--docs-only', action='store_true', help='Refresh only documentation')
    parser.add_argument('--no-agents', action='store_true', help='Skip agent files')
    parser.add_argument('--no-docs', action='store_true', help='Skip documentation')
    parser.add_argument('--no-session', action='store_true', help='Skip active_session.md reset')
    
    args = parser.parse_args()
    
    # Determine scope
    if args.agents_only:
        agents, docs, index, github, session = True, False, False, False, False
    elif args.docs_only:
        agents, docs, index, github, session = False, True, True, True, False
    else:
        agents = not args.no_agents
        docs = not args.no_docs
        index = not args.no_docs  # index follows docs
        github = not args.no_docs  # github follows docs
        session = not args.no_session
    
    success = refresh_project(
        args.project,
        agents=agents,
        docs=docs,
        index=index,
        github=github,
        session=session,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
