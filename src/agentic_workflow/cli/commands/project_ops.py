"""
Project Operations Commands
Focus: Management and Status (List, Delete, Status).
"""
import click
from rich_click import RichCommand

from ..handlers.project_handlers import ProjectHandlers
from ..handlers.query_handlers import QueryHandlers
from ..display import exit_with_error

@click.command(name='list', cls=RichCommand)
@click.argument('name', required=False)
@click.option('--format', '-f', 'output_format', default='table', type=click.Choice(['table', 'json', 'yaml']))
@click.pass_context
def list_projects(ctx: click.Context, name: str, output_format: str):
    """List all projects or show details for a specific project.
    
    Without arguments, displays a table of all projects.
    With a project name, shows detailed configuration.
    
    \b
    Examples:
      $ agentic list
      $ agentic list my-project
      $ agentic list --format json
    """
    console = ctx.obj.get('console')
    project_handlers = ProjectHandlers(console)
    
    try:
        project_handlers.handle_list(name=name, output_format=output_format)
    except Exception as e:
        exit_with_error(f"List failed: {e}", console)

@click.command(name='delete', cls=RichCommand)
@click.argument('project')
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
@click.pass_context
def delete_project(ctx: click.Context, project: str, force: bool):
    """Delete a project and all its data.
    
    Removes the project directory and all associated files.
    Prompts for confirmation unless --force is specified.
    
    \b
    Examples:
      $ agentic delete my-project
      $ agentic delete my-project --force
    """
    console = ctx.obj.get('console')
    project_handlers = ProjectHandlers(console)
    
    if not force:
        if not click.confirm(f"Are you sure you want to delete '{project}'?"):
            return
            
    try:
        project_handlers.handle_delete(project=project, force=force)
    except Exception as e:
        exit_with_error(f"Deletion failed: {e}", console)

@click.command(name='list-pending', cls=RichCommand)
@click.pass_context
def list_pending(ctx: click.Context):
    """List all pending handoffs in the current project.
    
    Shows handoffs that have been initiated but not yet accepted
    by the target agent. Must be run from within a project directory.
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    query_handlers = QueryHandlers(console)
    
    try:
        query_handlers.handle_list_pending(project=project_name)
    except Exception as e:
        exit_with_error(f"List pending failed: {e}", console)

@click.command(name='list-blockers', cls=RichCommand)
@click.pass_context
def list_blockers(ctx: click.Context):
    """List all active blockers in the current project.
    
    Shows blockers that are currently preventing progress,
    including which agents are affected. Must be run from
    within a project directory.
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    query_handlers = QueryHandlers(console)
    
    try:
        query_handlers.handle_list_blockers(project=project_name)
    except Exception as e:
        exit_with_error(f"List blockers failed: {e}", console)

@click.command(cls=RichCommand)
@click.pass_context
def status(ctx: click.Context):
    """Show current project or system status.
    
    Context-aware command that displays:
    - Inside a project: workflow state, active agent, recent activity
    - Outside a project: error message with guidance
    """
    # If inside a project, shows workflow state.
    # If outside, could show system health or error.
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    query_handlers = QueryHandlers(console)
    
    try:
        query_handlers.handle_status(project=project_name)
    except Exception as e:
        exit_with_error(f"Status check failed: {e}", console)


__all__ = ["list_projects", "delete_project", "list_pending", "list_blockers", "status"]