#!/usr/bin/env python3
"""
Modular workflow commands for Agentic Workflow CLI.

This module provides workflow-related commands using the new handler architecture
for better maintainability and error handling.

Design Decision: Commands pass arguments directly to handlers as keyword arguments.
No argparse.Namespace conversion - handlers are designed to accept kwargs.
"""

import click
from typing import Optional

from ..handlers import SessionHandlers, EntryHandlers, QueryHandlers, WorkflowHandlers
from ..utils import display_error, display_success


# Initialize handlers
_session_handlers = SessionHandlers()
_entry_handlers = EntryHandlers()
_query_handlers = QueryHandlers()
_workflow_handlers = WorkflowHandlers()


@click.group()
def workflow():
    """Manage agentic workflows."""
    pass


# ============================================================================
# Session Commands
# ============================================================================

@workflow.command()
@click.argument('project')
@click.option('--workflow', '-w', 'workflow_type', default='planning', help='Workflow type')
@click.option('--description', '-d', help='Project description')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing project')
def init(project: str, workflow_type: str, description: str, force: bool):
    """Initialize a workflow in a new project."""
    try:
        _session_handlers.handle_init(
            project=project,
            workflow=workflow_type,
            description=description,
            force=force
        )
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
@click.argument('agent_id')
def activate(project: str, agent_id: str):
    """Activate an agent session."""
    try:
        _session_handlers.handle_activate(
            project=project,
            agent_id=agent_id
        )
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def end(project: str):
    """End the current project session."""
    try:
        _session_handlers.handle_end(project=project)
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def populate(project: str):
    """Populate agent frontmatter from manifest."""
    try:
        _session_handlers.handle_populate(project=project)
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
@click.option('--force', '-f', is_flag=True, help='Force deletion without confirmation')
def delete(project: str, force: bool):
    """Delete a project."""
    try:
        _session_handlers.handle_delete(
            project=project,
            force=force
        )
    except Exception as e:
        display_error(str(e))


# ============================================================================
# Entry Commands
# ============================================================================

@workflow.command()
@click.argument('project')
@click.option('--from', 'from_agent', required=True, help='Source agent ID')
@click.option('--to', 'to_agent', required=True, help='Target agent ID')
@click.option('--artifacts', help='Comma-separated artifact list')
@click.option('--notes', help='Handoff notes')
def handoff(project: str, from_agent: str, to_agent: str,
           artifacts: Optional[str], notes: Optional[str]):
    """Record an agent handoff."""
    try:
        _entry_handlers.handle_handoff(
            project=project,
            from_agent=from_agent,
            to_agent=to_agent,
            artifacts=artifacts,
            notes=notes
        )
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
@click.option('--title', required=True, help='Decision title')
@click.option('--rationale', required=True, help='Decision rationale')
@click.option('--agent', help='Agent ID')
def decision(project: str, title: str, rationale: str, agent: Optional[str]):
    """Record a project decision."""
    try:
        _entry_handlers.handle_decision(
            project=project,
            title=title,
            rationale=rationale,
            agent=agent
        )
    except Exception as e:
        display_error(str(e))


# ============================================================================
# Query Commands
# ============================================================================

@workflow.command()
@click.argument('project')
def status(project: str):
    """Show project status summary."""
    try:
        _query_handlers.handle_status(project=project)
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
@click.argument('agent_id')
def check_handoff(project: str, agent_id: str):
    """Check if a handoff exists for an agent."""
    try:
        _query_handlers.handle_check_handoff(
            project=project,
            agent_id=agent_id
        )
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def list_pending(project: str):
    """List pending handoffs."""
    try:
        _query_handlers.handle_list_pending(project=project)
    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def list_blockers(project: str):
    """List active blockers."""
    try:
        _query_handlers.handle_list_blockers(project=project)
    except Exception as e:
        display_error(str(e))


# ============================================================================
# Workflow Commands
# ============================================================================

@workflow.command()
def list_workflows():
    """List available workflows."""
    try:
        _workflow_handlers.handle_list_workflows()
    except Exception as e:
        display_error(str(e))


# Export the workflow group as cli for backward compatibility
cli = workflow
