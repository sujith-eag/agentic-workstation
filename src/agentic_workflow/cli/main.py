#!/usr/bin/env python3
"""Main CLI entry point for Agentic Workflow."""
import click
from pathlib import Path
from rich.console import Console
from rich_click import RichGroup

from agentic_workflow import __version__
from agentic_workflow.core.config_service import ConfigurationService
from agentic_workflow.core.schema import RuntimeConfig
from agentic_workflow.core.exceptions import AgenticWorkflowError
from agentic_workflow.cli.utils import display_error, display_info, display_warning

# Initialize console
console = Console()


class ContextAwareGroup(RichGroup):
    """RichGroup that shows context-aware help."""

    def get_command(self, ctx: click.Context, cmd_name: str):
        """Get command with context awareness."""
        # Load config if not already loaded
        if not ctx.obj or 'config' not in ctx.obj:
            from ..core.config_service import ConfigurationService
            config_service = ConfigurationService()
            config = config_service.load_config()
            if not ctx.obj:
                ctx.obj = {}
            ctx.obj['config'] = config

        config = ctx.obj['config']

        # Check if command should be available in current context
        if config.is_project_context:
            # In project context, only allow project commands
            project_commands = ['activate', 'handoff', 'status', 'end-session', 'decision']
            if cmd_name not in project_commands:
                return None
        else:
            # In global context, only allow global commands
            global_commands = ['init', 'list-workflows', 'config']
            if cmd_name not in global_commands:
                return None

        # First try to get the command normally
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd

        # If command not found, try to load it dynamically
        if config.is_project_context:
            # In project context, try project commands
            from .commands.workflow import activate, handoff, status, end_session, decision
            project_commands = {
                'activate': activate,
                'handoff': handoff,
                'status': status,
                'end-session': end_session,
                'decision': decision
            }
            return project_commands.get(cmd_name)
        else:
            # In global context, try global commands
            from .commands.workflow import init, list_workflows
            from .commands.global_commands import config
            global_commands = {
                'init': init,
                'list-workflows': list_workflows,
                'config': config
            }
            return global_commands.get(cmd_name)

        return None

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List commands based on current context."""
        # Load config if not already loaded
        if not ctx.obj or 'config' not in ctx.obj:
            from ..core.config_service import ConfigurationService
            config_service = ConfigurationService()
            config = config_service.load_config()
            if not ctx.obj:
                ctx.obj = {}
            ctx.obj['config'] = config

        config = ctx.obj['config']

        if config.is_project_context:
            # Project context commands
            return ['activate', 'handoff', 'status', 'end-session', 'decision']
        else:
            # Global context commands
            return ['init', 'list-workflows', 'config']


def show_version(ctx, param, value):
    """Callback to display styled version information."""
    if value:
        from rich.panel import Panel
        from rich.text import Text

        version_text = Text(f"Agentic Workflow v{__version__}", style="bold cyan")
        panel = Panel(version_text, title="[bold blue]Version[/bold blue]", border_style="blue")
        console.print(panel)
        ctx.exit()


@click.group(cls=ContextAwareGroup, invoke_without_command=True)
@click.option('--version', is_flag=True, callback=show_version, expose_value=False, help='Show version and exit')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--force', '-f', is_flag=True, help='Force operations')
@click.pass_context
def cli(ctx: click.Context, verbose: bool, force: bool):
    """Agentic Workflow — Multi-agent planning system.

    A comprehensive platform for managing complex software projects through
    orchestrated agent workflows.
    """
    # Initialize context object
    ctx.ensure_object(dict)

    # Load configuration with context awareness
    config_service = ConfigurationService()
    runtime_config = config_service.load_config(verbose=verbose, force=force)

    # Setup logging after config is loaded
    from .utils import setup_logging
    setup_logging(verbose=verbose, log_level=runtime_config.system.log_level if hasattr(runtime_config, 'system') else "INFO")

    # Store in context
    ctx.obj['config'] = runtime_config
    ctx.obj['console'] = console

    # Add context-aware commands dynamically
    add_context_commands(cli, runtime_config)

    # If no subcommand provided, launch TUI
    if ctx.invoked_subcommand is None:
        run_tui_mode(runtime_config)


def run_tui_mode(config: RuntimeConfig):
    """Entry point for TUI with error boundary."""
    try:
        from .tui.main import TUIApp
        app = TUIApp(config)
        app.run()
    except AgenticWorkflowError as e:
        # Business Logic Errors (Governance, Config, etc.)
        _display_error_modal(str(e), title="Operation Failed")
        # Restarting the loop or exiting depends on severity,
        # usually we return to main menu or exit gracefully.
    except Exception as e:
        # Unexpected crashes - show stack trace in TUI
        console.clear()
        from rich.panel import Panel
        from rich.text import Text
        error_text = Text(f"An unexpected error occurred:\n{str(e)}", style="red")
        panel = Panel(error_text, title="[bold red]Critical Error[/bold red]", border_style="red")
        console.print(panel)
        console.print_exception()
        input("\nPress Enter to exit...")
        raise


def _display_error_modal(message: str, title: str = "Error"):
    """Display an error modal in the TUI."""
    console.clear()
    from rich.panel import Panel
    error_panel = Panel(
        f"[bold white]{message}[/bold white]",
        title=f"[bold red]{title}[/bold red]",
        border_style="red",
        padding=(1, 2)
    )
    console.print(error_panel)
    input("\nPress Enter to exit...")


# Dynamic command registration based on context
def add_context_commands(cli_group: click.Group, config: RuntimeConfig):
    """Add commands based on current context."""
    if config.is_project_context:
        # Project mode commands - direct commands for context-aware usage
        from .commands.workflow import activate, handoff, status, end_session
        cli_group.add_command(activate)
        cli_group.add_command(handoff)
        cli_group.add_command(status)
        cli_group.add_command(end_session)
    else:
        # Global mode commands
        from .commands.workflow import init, list_workflows
        from .commands.global_commands import config
        cli_group.add_command(init)
        cli_group.add_command(list_workflows)
        cli_group.add_command(config)


# Add all commands statically for help to work
from .commands.workflow import init, list_workflows, activate, handoff, status, end_session
from .commands.global_commands import config

cli.add_command(init)
cli.add_command(list_workflows)
cli.add_command(config)
cli.add_command(activate)
cli.add_command(handoff)
cli.add_command(status)
cli.add_command(end_session)


if __name__ == "__main__":
    import sys
    from agentic_workflow.core.exceptions import AgenticWorkflowError

    try:
        cli()
    except AgenticWorkflowError as e:
        display_error(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        display_error(f"[red]Unexpected Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)