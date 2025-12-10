#!/usr/bin/env python3
"""Main CLI entry point for Agentic Workflow."""
import click
from pathlib import Path
from rich.console import Console
from rich_click import RichGroup

from agentic_workflow import __version__
from agentic_workflow.cli.config import load_config
from agentic_workflow.cli.commands import project, workflow
from agentic_workflow.cli.utils import display_error, display_info, display_warning

# Initialize console
console = Console()


def show_version(ctx, param, value):
    """Callback to display styled version information."""
    if value:
        from rich.panel import Panel
        from rich.text import Text
        
        version_text = Text(f"Agentic Workflow v{__version__}", style="bold cyan")
        panel = Panel(version_text, title="[bold blue]Version[/bold blue]", border_style="blue")
        console.print(panel)
        ctx.exit()


def check_for_updates(console: Console) -> None:
    """Check for updates (stub implementation)."""
    # TODO: Implement update checking logic
    display_info("Update checking not yet implemented")


def launch_web_ui() -> None:
    """Launch the web UI (stub implementation).
    
    TODO: Implement web UI server using FastAPI or similar.
    This should start a local server and open the browser.
    """
    display_warning("Web UI not yet implemented")
    display_info("This feature is planned for a future release.")


@click.group(cls=RichGroup)
@click.option('--version', is_flag=True, callback=show_version, expose_value=False, help='Show version and exit')
@click.option('--config', '-c', type=click.Path(exists=True), help='Config file path')
@click.option('--output', '-o', type=click.Choice(['table', 'json', 'yaml', 'csv']), default='table', help='Output format')
@click.option('--api', is_flag=True, help='API mode (structured output)')
@click.option('--web', is_flag=True, help='Launch web UI')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--verbose', '-v', count=True, help='Verbosity level (repeat for more)')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default='INFO', help='Log level')
@click.option('--auth-token', help='Authentication token for multi-user support')
@click.option('--cache', is_flag=True, help='Enable caching for performance')
@click.option('--retry', type=int, default=0, help='Retry count for failed operations')
@click.option('--check-updates', is_flag=True, help='Check for updates on startup')
@click.pass_context
def cli(ctx: click.Context, config, output, api, web, interactive, verbose, log_level, auth_token, cache, retry, check_updates):
    """Agentic Workflow — Multi-agent planning system.

    A comprehensive platform for managing complex software projects through
    orchestrated agent workflows. Supports CLI, API, web, and programmatic interfaces.
    """
    # Initialize context object
    ctx.ensure_object(dict)

    # Load configuration
    config_obj = load_config(Path(config) if config else None)

    # Setup comprehensive context
    ctx.obj.update({
        "config": config_obj,
        "output_format": output,
        "api_mode": api,
        "interactive": interactive,
        "verbosity": verbose,
        "log_level": log_level,
        "auth_token": auth_token,
        "cache_enabled": cache,
        "retry_count": retry,
        "console": console,
        "start_time": __import__('time').time()
    })

    # Handle special flags
    if check_updates:
        check_for_updates(console)

    if web:
        display_info("Launching web UI...")
        launch_web_ui()
        ctx.exit()

    # Setup logging based on verbosity
    from .utils import setup_logging
    setup_logging(verbose > 0, log_level)

# Register command groups
cli.add_command(project)
cli.add_command(workflow)


@cli.command()
@click.option('--global-mode', is_flag=True, help='Force global mode (ignore project context)')
@click.option('--project-mode', is_flag=True, help='Force project mode (require project context)')
@click.pass_context
def tui(ctx, global_mode, project_mode):
    """Launch Text User Interface for interactive workflow management.
    
    Provides guided menus and wizards for project creation and workflow operations.
    Automatically detects context (global vs project) unless overridden.
    """
    try:
        from .tui.main import main as tui_main
        tui_main()
    except ImportError as e:
        display_error(f"TUI dependencies not available: {e}")
        display_info("Install with: pip install questionary")
        ctx.exit(1)
    except Exception as e:
        display_error(f"TUI failed to start: {e}")
        ctx.exit(1)
    """Launch Text User Interface for interactive workflow management.
    
    Provides guided menus and wizards for project creation and workflow operations.
    Automatically detects context (global vs project) unless overridden.
    """
    try:
        from .tui.main import main as tui_main
        tui_main()
    except ImportError as e:
        display_error(f"TUI dependencies not available: {e}")
        display_info("Install with: pip install questionary")
        ctx.exit(1)
    except Exception as e:
        display_error(f"TUI failed to start: {e}")
        ctx.exit(1)

if __name__ == "__main__":
    import sys
    from agentic_workflow.exceptions import AgenticError
    
    try:
        cli()
    except AgenticError as e:
        display_error(f"[red]Error:[/red] {e}")
        if hasattr(e, 'exit_code'):
             sys.exit(e.exit_code)
        sys.exit(1)
    except Exception as e:
        display_error(f"[red]Unexpected Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)