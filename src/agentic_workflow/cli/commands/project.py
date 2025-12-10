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
@click.argument('name')
@click.option('--workflow', '-w', default=None,
              help='Workflow type to use (planning, research, implementation, etc.)')
@click.option('--description', '-d', help='Project description')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing project')
def init(name: str, workflow: Optional[str], description: str, force: bool):
    """Initialize a new project."""
    try:
        handlers.handle_init(
            name=name,
            workflow=workflow,
            description=description,
            force=force
        )
    except Exception as e:
        display_error(f"Project initialization failed: {e}")


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
def status():
    """Show current project status."""
    try:
        handlers.handle_status()
    except Exception as e:
        display_error(f"Project status check failed: {e}")