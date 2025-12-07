#!/usr/bin/env python3
"""Project management commands."""
import click
from pathlib import Path
from typing import Optional
import argparse

from ..handlers.project_handlers import ProjectHandlers
from ..utils import display_error

# Create handler instance
handlers = ProjectHandlers()

@click.group()
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
    # Convert click args to argparse namespace for handler compatibility
    args = argparse.Namespace(
        name=name,
        workflow=workflow,
        description=description,
        force=force
    )

    try:
        handlers.handle_init(args)
    except Exception as e:
        display_error(f"Project initialization failed: {e}")

@project.command()
@click.argument('name', required=False)
@click.pass_context
def list(ctx: click.Context, name: Optional[str]):
    """List projects or show project details."""
    # Convert click args to argparse namespace for handler compatibility
    args = argparse.Namespace(
        name=name,
        output_format=ctx.obj.get('output_format', 'table')
    )

    try:
        handlers.handle_list(args)
    except Exception as e:
        display_error(f"Project listing failed: {e}")

@project.command()
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Force removal without confirmation')
def remove(name: str, force: bool):
    """Remove a project."""
    # Convert click args to argparse namespace for handler compatibility
    args = argparse.Namespace(
        name=name,
        force=force
    )

    try:
        handlers.handle_remove(args)
    except Exception as e:
        display_error(f"Project removal failed: {e}")


@project.command()
def status():
    """Show current project status."""
    # Convert click args to argparse namespace for handler compatibility
    args = argparse.Namespace()

    try:
        handlers.handle_status(args)
    except Exception as e:
        display_error(f"Project status check failed: {e}")