#!/usr/bin/env python3
"""UI utility functions for Agentic Workflow CLI."""
import sys
from typing import Any, Dict, List, NoReturn
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import structlog
from contextlib import contextmanager

console = Console()

__all__ = [
    "setup_logging",
    "format_output",
    "confirm_action",
    "show_progress",
    "display_error",
    "exit_with_error",
    "display_success",
    "display_warning",
    "display_info",
    "display_status_panel",
    "display_help_panel",
    "display_action_result",
    "display_project_summary",
    "shorten_path",
    "format_file_list",
]


def setup_logging(verbose: bool = False, log_level: str = "INFO") -> None:
    """Setup structured logging."""
    import logging
    from structlog import WriteLoggerFactory
    from structlog.processors import JSONRenderer

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if verbose:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.processors.KeyValueRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=WriteLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def format_output(data: Any, format_type: str = "table", title: str = None) -> None:
    """Format data for output in various formats."""
    if format_type == "json":
        import json
        console.print_json(json.dumps(data, indent=2, default=str))
    elif format_type == "yaml":
        import yaml
        console.print(yaml.dump(data, default_flow_style=False))
    elif format_type == "table":
        if isinstance(data, list) and data:
            table = Table(title=title)
            # Get headers from first item
            headers = list(data[0].keys()) if isinstance(data[0], dict) else ["Value"]
            for header in headers:
                table.add_column(header, style="cyan")

            for item in data:
                if isinstance(item, dict):
                    row = [str(item.get(h, "")) for h in headers]
                else:
                    row = [str(item)]
                table.add_row(*row)
            console.print(table)
        elif isinstance(data, dict):
            table = Table(title=title)
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            for key, value in data.items():
                table.add_row(key, str(value))
            console.print(table)
        else:
            console.print(data)
    else:
        console.print(data)


def confirm_action(message: str, default: bool = False) -> bool:
    """Get user confirmation for an action."""
    return click.confirm(message, default=default)


@contextmanager
def show_progress(message: str):
    """Show a progress indicator as a context manager."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[bold green]{message}"),
        console=console,
    )
    with progress:
        task = progress.add_task("", total=None)
        try:
            yield
        finally:
            progress.update(task, completed=100)


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[red]Error:[/red] {message}")


def exit_with_error(message: str, exit_code: int = 1) -> NoReturn:
    """Display an error message and exit the program."""
    display_error(message)
    sys.exit(exit_code)


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[green]✓[/green] {message}")


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def display_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def display_status_panel(project_name: str, status_data: Dict[str, Any]) -> None:
    """Display project status in a structured table panel."""
    table = Table(title=f"[bold blue]Project Status: {project_name}[/bold blue]")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for key, value in status_data.items():
        formatted_key = key.replace('_', ' ').title()
        table.add_row(formatted_key, str(value))

    console.print(table)


def display_help_panel(title: str, commands: List[Dict[str, str]]) -> None:
    """Display help in a rich panel with formatted commands."""
    if not commands:
        return

    # Create table for commands
    table = Table(box=None, pad_edge=False)
    table.add_column("Command", style="green", no_wrap=True)
    table.add_column("Description", style="white", overflow="fold")  # Allow wrapping

    for cmd in commands:
        table.add_row(cmd.get('command', ''), cmd.get('description', ''))

    panel = Panel(
        table,
        title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def display_action_result(action: str, success: bool, details: List[str] = None, icon: str = None) -> None:
    """Standardized action completion display with optional details."""
    if icon is None:
        icon = "✓" if success else "✗"
    color = "green" if success else "red"

    console.print(f"[{color}]{icon}[/{color}] {action}")
    if details:
        for detail in details:
            console.print(f"[{color}]  └─[/{color}] {detail}")


def display_project_summary(project_name: str, workflow: str, directories: List[str], next_steps: List[str]) -> None:
    """Display project creation summary in a structured panel."""
    # Create directories list
    dir_content = "\n".join(f"  • {d}" for d in directories)

    # Create next steps list
    steps_content = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(next_steps))

    content = f"""[bold white]Workflow:[/bold white] {workflow}
[bold white]Location:[/bold white] projects/{project_name}

[bold white]Created directories:[/bold white]
{dir_content}

[bold white]Next steps:[/bold white]
{steps_content}"""

    panel = Panel(
        content,
        title="[bold green]🎉 Project Created[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)


def shorten_path(path: str, max_length: int = 60) -> str:
    """Shorten paths for display readability."""
    from pathlib import Path
    path_obj = Path(path)
    path_str = str(path)

    if len(path_str) <= max_length:
        return path_str

    # Try relative to project root
    from ..core.config_service import ConfigurationService
    config_service = ConfigurationService()
    project_root = config_service.find_project_root()
    if project_root:
        try:
            rel_path = path_obj.relative_to(project_root)
            rel_str = str(rel_path)
            if len(rel_str) < len(path_str):
                return rel_str
        except ValueError:
            pass

    # Try relative to current directory
    try:
        rel_path = path_obj.relative_to(Path.cwd())
        rel_str = str(rel_path)
        if len(rel_str) < len(path_str):
            return f"./{rel_str}"
    except ValueError:
        pass

    # Fallback: truncate with ellipsis
    return f"...{path_str[-max_length+3:]}"


def format_file_list(files: List[str], prefix: str = "✓ Generated:", max_line_length: int = 80) -> List[str]:
    """Format a list of files with proper line breaking."""
    formatted_lines = []
    for file_path in files:
        short_path = shorten_path(file_path)
        line = f"{prefix} {short_path}"

        if len(line) <= max_line_length:
            formatted_lines.append(line)
        else:
            # Break long lines
            formatted_lines.append(f"{prefix}")
            formatted_lines.append(f"  {short_path}")

    return formatted_lines