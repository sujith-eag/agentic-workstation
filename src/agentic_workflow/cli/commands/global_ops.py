"""
Global Operations Commands
Focus: Bootstrap and System Config (Init, Config, Workflows).
"""
import click
from rich_click import RichCommand

from ..handlers.session_handlers import SessionHandlers
from ..handlers.global_handlers import GlobalHandlers
from ..display import exit_with_error

@click.command(cls=RichCommand)
@click.argument('project')
@click.option('--workflow', '-w', default='planning', help='Workflow type (default: planning)')
@click.option('--description', '-d', help='Short description of the project')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing project')
@click.pass_context
def init(ctx: click.Context, project: str, workflow: str, description: str, force: bool):
    """Initialize a new Agentic Workflow project.
    
    Creates a new project directory with the specified workflow type,
    generates configuration files, and sets up the initial structure.
    
    \b
    Examples:
      $ agentic init my-project
      $ agentic init my-project --workflow research --description "Research phase"
    """
    console = ctx.obj.get('console')
    session_handlers = SessionHandlers(console)
    
    try:
        # Init belongs to SessionHandlers because it starts the lifecycle
        session_handlers.handle_init(
            project=project,
            workflow=workflow,
            description=description,
            force=force
        )
    except Exception as e:
        exit_with_error(f"Initialization failed: {e}", console)

@click.command(name='workflows', cls=RichCommand)
@click.pass_context
def list_workflows(ctx: click.Context):
    """List all available workflow definitions.
    
    Shows workflow templates that can be used with 'agentic init'.
    Displays workflow name, description, agent count, and version.
    """
    console = ctx.obj.get('console')
    global_handlers = GlobalHandlers(console)
    
    try:
        global_handlers.handle_list_workflows()
    except Exception as e:
        exit_with_error(f"Failed to list workflows: {e}", console)

@click.command(cls=RichCommand)
@click.option('--edit', '-e', is_flag=True, help='Open config in default editor')
@click.pass_context
def config(ctx: click.Context, edit: bool):
    """View or edit global configuration.
    
    Displays the global configuration file in YAML format.
    Use --edit to open the configuration in your default editor.
    """
    console = ctx.obj.get('console')
    global_handlers = GlobalHandlers(console)
    
    try:
        global_handlers.handle_config(edit=edit)
    except Exception as e:
        exit_with_error(f"Config operation failed: {e}", console)


__all__ = ["init", "list_workflows", "config"]