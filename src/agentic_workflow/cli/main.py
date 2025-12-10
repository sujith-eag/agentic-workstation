#!/usr/bin/env python3
"""Main CLI entry point for Agentic Workflow."""
import click
from pathlib import Path
from rich.console import Console

from agentic_workflow import __version__
from agentic_workflow.cli.config import load_config
from agentic_workflow.cli.commands import project, workflow

# Initialize console
console = Console()


def check_for_updates(console: Console) -> None:
    """Check for updates (stub implementation)."""
    # TODO: Implement update checking logic
    console.print("[dim]Update checking not yet implemented[/dim]")


def launch_web_ui() -> None:
    """Launch the web UI (stub implementation).
    
    TODO: Implement web UI server using FastAPI or similar.
    This should start a local server and open the browser.
    """
    console.print("[yellow]Web UI not yet implemented[/yellow]")
    console.print("[dim]This feature is planned for a future release.[/dim]")


@click.group()
@click.version_option(version=__version__)
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
        console.print("[blue]Launching web UI...[/blue]")
        launch_web_ui()
        ctx.exit()

    # Setup logging based on verbosity
    from .utils import setup_logging
    setup_logging(verbose > 0, log_level)

# Register command groups
cli.add_command(project)
cli.add_command(workflow)

if __name__ == "__main__":
    import sys
    from agentic_workflow.exceptions import AgenticError
    
    try:
        cli()
    except AgenticError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if hasattr(e, 'exit_code'):
             sys.exit(e.exit_code)
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)