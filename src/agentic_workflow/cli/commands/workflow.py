#!/usr/bin/env python3
"""
Modular workflow commands for Agentic Workflow CLI.

This module provides workflow-related commands using the new handler architecture
for better maintainability and error handling.
"""

import click
from pathlib import Path
from typing import Optional
import argparse

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


# Session Commands
@workflow.command()
@click.argument('project')
@click.option('--workflow', '-w', default='planning', help='Workflow type')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing project')
def init(project: str, workflow: str, force: bool):
    """Initialize a workflow in a new project."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(
            project=project,
            workflow=workflow,
            force=force
        )
        _session_handlers.handle_init(args)

    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
@click.argument('agent_id')
def activate(project: str, agent_id: str):
    """Activate an agent session."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(
            project=project,
            agent_id=agent_id
        )
        _session_handlers.handle_activate(args)

    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def end(project: str):
    """End the current project session."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(project=project)
        _session_handlers.handle_end(args)

    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def populate(project: str):
    """Populate agent frontmatter from manifest."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(project=project)
        _session_handlers.handle_populate(args)

    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
@click.option('--force', '-f', is_flag=True, help='Force deletion without confirmation')
def delete(project: str, force: bool):
    """Delete a project."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(
            project=project,
            force=force
        )
        _session_handlers.handle_delete(args)

    except Exception as e:
        display_error(str(e))


# Entry Commands
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
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(
            project=project,
            from_agent=from_agent,
            to_agent=to_agent,
            artifacts=artifacts,
            notes=notes
        )
        _entry_handlers.handle_handoff(args)

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
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(
            project=project,
            title=title,
            rationale=rationale,
            agent=agent
        )
        _entry_handlers.handle_decision(args)

    except Exception as e:
        display_error(str(e))


# Query Commands
@workflow.command()
@click.argument('project')
def status(project: str):
    """Show project status summary."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(project=project)
        _query_handlers.handle_status(args)

    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
@click.argument('agent_id')
def check_handoff(project: str, agent_id: str):
    """Check if a handoff exists for an agent."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(
            project=project,
            agent_id=agent_id
        )
        _query_handlers.handle_check_handoff(args)

    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def list_pending(project: str):
    """List pending handoffs."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(project=project)
        _query_handlers.handle_list_pending(args)

    except Exception as e:
        display_error(str(e))


@workflow.command()
@click.argument('project')
def list_blockers(project: str):
    """List active blockers."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace(project=project)
        _query_handlers.handle_list_blockers(args)

    except Exception as e:
        display_error(str(e))


# Workflow Commands
@workflow.command()
def list_workflows():
    """List available workflows."""
    try:
        # Convert click args to argparse namespace for handler compatibility
        args = argparse.Namespace()
        _workflow_handlers.handle_list_workflows(args)

    except Exception as e:
        display_error(str(e))


# Export the workflow group as cli for backward compatibility
cli = workflow
