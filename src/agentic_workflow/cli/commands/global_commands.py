#!/usr/bin/env python3
"""
Global commands for Agentic Workflow CLI (available outside projects).
"""
import click
from typing import Optional
from rich_click import RichGroup

from ..handlers.global_handlers import GlobalHandlers
from ..utils import display_error

# Create handler instance
handlers = GlobalHandlers()


@click.group(cls=RichGroup)
def global_commands():
    """Global commands available outside project context."""
    pass


@global_commands.command()
def list_workflows():
    """List available workflow types."""
    try:
        handlers.handle_list_workflows()
    except Exception as e:
        display_error(f"Failed to list workflows: {e}")


@global_commands.command()
@click.option('--edit', '-e', is_flag=True, help='Open config in editor')
def config(edit: bool):
    """Show or edit global configuration."""
    try:
        handlers.handle_config(edit=edit)
    except Exception as e:
        display_error(f"Config operation failed: {e}")