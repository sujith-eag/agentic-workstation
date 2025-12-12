#!/usr/bin/env python3
"""
Project management commands for Agentic Workflow CLI.

Design Decision: Commands pass arguments directly to handlers as keyword arguments.
No argparse.Namespace conversion - handlers are designed to accept kwargs.
"""
import click
from typing import Optional
from rich_click import RichGroup

from ..handlers.project_handlers import ProjectHandlers
from ..utils import display_error

# Create handler instance
handlers = ProjectHandlers()


@click.group(cls=RichGroup)
def project():
    """Manage agentic workflow projects."""
    pass


@project.command()
@click.argument('name', required=False)
@click.pass_context
def list(ctx: click.Context, name: Optional[str]):
    """List projects or show project details."""
    try:
        handlers.handle_list(
            name=name,
            output_format=ctx.obj.get('output_format', 'table') if ctx.obj else 'table'
        )
    except Exception as e:
        display_error(f"Project listing failed: {e}")


@project.command()
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Force removal without confirmation')
def remove(name: str, force: bool):
    """Remove a project."""
    try:
        handlers.handle_remove(
            name=name,
            force=force
        )
    except Exception as e:
        display_error(f"Project removal failed: {e}")


@project.command()
@click.argument('agent_id')
def activate(agent_id: str):
    """Activate an agent session."""
    try:
        handlers.handle_activate(agent_id=agent_id)
    except Exception as e:
        display_error(f"Agent activation failed: {e}")


@project.command()
@click.option('--to', required=True, help='Target agent ID')
@click.option('--artifacts', help='Comma-separated artifact names')
def handoff(to: str, artifacts: str):
    """Handoff to next agent."""
    try:
        artifact_list = artifacts.split(',') if artifacts else []
        handlers.handle_handoff(to=to, artifacts=artifact_list)
    except Exception as e:
        display_error(f"Handoff failed: {e}")


@project.command()
def end():
    """End the current session."""
    try:
        handlers.handle_end_session()
    except Exception as e:
        display_error(f"Session end failed: {e}")