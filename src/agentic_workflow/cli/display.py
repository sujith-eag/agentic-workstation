#!/usr/bin/env python3
"""Display utility functions for Agentic Workflow CLI."""
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .formatting import get_terminal_width
from .theme import Theme


__all__ = [
    "display_error",
    "exit_with_error",
    "display_table",
    "display_list",
    "display_text_panel",
    "display_warning",
    "display_info",
    "display_project_summary",
    "display_action_result",
    "display_help_panel",
    "display_status_panel",
]


def display_error(message: str, console: Console) -> None:
    """Display an error message in a themed panel.
    
    Args:
        message: The error message to display.
        console: Rich Console instance for rendering.
    """
    if not message or not isinstance(message, str):
        message = "An unknown error occurred"
    color_map = Theme.get_color_map()
    panel = Panel(
        f"[{color_map['error.color']}]{message}[/{color_map['error.color']}]",
        title=f"[{color_map['error.color']}]Error[/{color_map['error.color']}]",
        border_style=color_map['panel.error.border'],
        padding=(0, 1),
        width=min(get_terminal_width() - 4, 100)
    )
    console.print(panel)


def exit_with_error(message: str, console: Console, exit_code: int = 1) -> None:
    """Display an error message and exit the program.
    
    Args:
        message: The error message to display before exiting.
        console: Rich Console instance for rendering.
        exit_code: The exit code to use (default: 1).
    """
    display_error(message, console)
    sys.exit(exit_code)


def display_table(
    data: List[Dict[str, Any]],
    console: Console,
    title: Optional[str] = None,
    columns: Optional[List[str]] = None,
    format_type: str = 'table'
) -> None:
    """Display data as a Rich table or json/yaml.
    
    Args:
        data: List of dictionaries to display
        console: Rich Console instance
        title: Optional table title
        columns: Optional column order/filter (defaults to all keys from first item)
        format_type: 'table', 'json', or 'yaml'
    """
    if not data or not isinstance(data, list):
        display_info("No data to display", console)
        return
    
    if not isinstance(console, Console):
        raise TypeError("console must be a Rich Console instance")
    
    if format_type == 'json':
        import json
        console.print(json.dumps(data, indent=2, default=str))
        return
    
    if format_type == 'yaml':
        import yaml
        console.print(yaml.dump(data, default_flow_style=False))
        return
    
    # Table format
    color_map = Theme.get_color_map()
    
    # Determine columns
    if columns is None:
        if isinstance(data[0], dict):
            columns = list(data[0].keys())
        else:
            columns = ['Value']
    
    # Create table
    table = Table(
        title=f"[bold {color_map['table.title.color']}]{title}[/bold {color_map['table.title.color']}]" if title else None,
        border_style=color_map['table.border'],
        width=min(get_terminal_width() - 4, 120)
    )
    
    # Add columns
    for col in columns:
        table.add_column(
            col.replace('_', ' ').title(),
            style=color_map['table.header'],
            overflow='fold'
        )
    
    # Add rows
    for item in data:
        if isinstance(item, dict):
            row = [str(item.get(col, '')) for col in columns]
        else:
            row = [str(item)]
        table.add_row(*row)
    
    console.print(table)


def display_list(
    items: List[str],
    console: Console,
    title: Optional[str] = None,
    style: str = 'bullet'
) -> None:
    """Display a list of items with consistent formatting.
    
    Args:
        items: List of strings to display.
        console: Rich Console instance for rendering.
        title: Optional section title.
        style: List style - 'bullet', 'numbered', or 'plain'.
    """
    if not items or not isinstance(items, list):
        return
    
    if not isinstance(console, Console):
        raise TypeError("console must be a Rich Console instance")
    
    color_map = Theme.get_color_map()
    
    if title:
        console.print(f"\n[bold {color_map['info.color']}]{title}[/bold {color_map['info.color']}]")
    
    for i, item in enumerate(items, 1):
        if style == 'numbered':
            console.print(f"  [{color_map['info.color']}]{i}.[/{color_map['info.color']}] {item}")
        elif style == 'bullet':
            console.print(f"  [{color_map['info.color']}]•[/{color_map['info.color']}] {item}")
        else:  # plain
            console.print(f"  {item}")


def display_text_panel(
    content: str,
    console: Console,
    title: Optional[str] = None,
    syntax: Optional[str] = None
) -> None:
    """Display text content in a Rich panel with optional syntax highlighting.
    
    Args:
        content: Text content to display.
        console: Rich Console instance for rendering.
        title: Panel title.
        syntax: Optional syntax highlighting (e.g., 'yaml', 'json', 'python').
    """
    if not content or not isinstance(content, str):
        return
    
    if not isinstance(console, Console):
        raise TypeError("console must be a Rich Console instance")
    
    color_map = Theme.get_color_map()
    
    # Apply syntax highlighting if requested
    if syntax:
        from rich.syntax import Syntax
        highlighted = Syntax(
            content,
            syntax,
            theme='monokai',
            line_numbers=False,
            word_wrap=True
        )
        panel_content = highlighted
    else:
        panel_content = content
    
    panel = Panel(
        panel_content,
        title=f"[bold {color_map['panel.title.color']}]{title}[/bold {color_map['panel.title.color']}]" if title else None,
        border_style=color_map['panel.border'],
        padding=(1, 2),
        width=min(get_terminal_width() - 4, 120)
    )
    console.print(panel)


def display_warning(message: str, console: Console) -> None:
    """Display a warning message.
    
    Args:
        message: The warning message to display.
        console: Rich Console instance for rendering.
    """
    if not message or not isinstance(message, str):
        message = "Warning"
    color_map = Theme.get_color_map()
    console.print(f"[{color_map['warning.color']}]⚠[/{color_map['warning.color']}] {message}")


def display_info(message: str, console: Console) -> None:
    """Display an informational message.
    
    Args:
        message: The info message to display.
        console: Rich Console instance for rendering.
    """
    if not message or not isinstance(message, str):
        return  # Don't display empty info messages
    color_map = Theme.get_color_map()
    console.print(f"[{color_map['info.color']}]ℹ[/{color_map['info.color']}] {message}")


def display_project_summary(project_name: str, workflow: str, directories: List[str], next_steps: List[str], console: Console) -> None:
    """Display project creation summary in a structured panel.
    
    Uses display_list() internally for clean, consistent list rendering.
    
    Args:
        project_name: The name of the created project.
        workflow: The workflow type used for the project.
        directories: List of created directory paths.
        next_steps: List of suggested next steps.
        console: Rich Console instance for rendering.
    """
    if not isinstance(console, Console):
        raise TypeError("console must be a Rich Console instance")
    color_map = Theme.get_color_map()
    
    # Input validation and defaults
    project_name = project_name or "Unknown Project"
    workflow = workflow or "Default Workflow"
    directories = directories or ["No directories created"]
    next_steps = next_steps or ["No next steps defined"]
    
    # Build panel content with metadata
    from io import StringIO
    content_buffer = StringIO()
    
    # Write metadata
    content_buffer.write(f"[bold {color_map['summary.workflow.color']}]Workflow:[/bold {color_map['summary.workflow.color']}] {workflow}\n")
    content_buffer.write(f"[bold {color_map['summary.location.color']}]Location:[/bold {color_map['summary.location.color']}] projects/{project_name}\n\n")
    
    # Render directories section
    content_buffer.write(f"[bold {color_map['summary.directories.color']}]Created directories:[/bold {color_map['summary.directories.color']}]\n")
    for directory in directories:
        content_buffer.write(f"  [{color_map['info.color']}]•[/{color_map['info.color']}] {directory}\n")
    
    # Render next steps section
    content_buffer.write(f"\n[bold {color_map['summary.steps.color']}]Next steps:[/bold {color_map['summary.steps.color']}]\n")
    for i, step in enumerate(next_steps, 1):
        content_buffer.write(f"  [{color_map['info.color']}]{i}.[/{color_map['info.color']}] {step}\n")
    
    panel = Panel(
        content_buffer.getvalue().rstrip(),
        title=f"[bold {color_map['summary.title.color']}]🎉 Project Created[/bold {color_map['summary.title.color']}]",
        border_style=color_map['summary.panel.border'],
        padding=(1, 2),
        width=min(get_terminal_width() - 4, 120)
    )
    console.print(panel)


def display_action_result(action: str, success: bool, console: Console, details: Optional[List[str]] = None, icon: Optional[str] = None) -> None:
    """Display standardized action completion with optional details.
    
    Args:
        action: Description of the action performed.
        success: Whether the action succeeded.
        console: Rich Console instance for rendering.
        details: Optional list of detail strings to display.
        icon: Optional custom icon (defaults to ✓ or ✗).
    """
    if not isinstance(console, Console):
        raise TypeError("console must be a Rich Console instance")
    if not action or not isinstance(action, str):
        action = "Unknown action"
    
    color_map = Theme.get_color_map()
    if icon is None:
        icon = "✓" if success else "✗"
    color = color_map['success.color'] if success else color_map['error.color']

    console.print(f"[{color}]{icon}[/{color}] {action}")
    if details and isinstance(details, list):
        for detail in details:
            if detail and isinstance(detail, str):
                console.print(f"[{color}]  └─[/{color}] {detail}")


def display_help_panel(title: str, commands: List[Dict[str, str]], console: Console) -> None:
    """Display help information in a rich panel with formatted commands.
    
    Args:
        title: The title for the help panel.
        commands: List of command dictionaries with 'command' and 'description' keys.
        console: Rich Console instance for rendering.
    """
    if not isinstance(console, Console):
        raise TypeError("console must be a Rich Console instance")
    if not commands:
        return

    color_map = Theme.get_color_map()
    # Create table for commands
    table = Table(box=None, pad_edge=False)
    table.add_column("Command", style=color_map['help.command.color'], no_wrap=True, max_width=get_terminal_width() // 4)
    table.add_column("Description", style=color_map['help.description.color'], overflow="fold", max_width=get_terminal_width() // 2)

    for cmd in commands:
        table.add_row(cmd.get('command', ''), cmd.get('description', ''))

    panel = Panel(
        table,
        title=f"[bold {color_map['panel.title.color']}] {title} [/bold {color_map['panel.title.color']}]",
        border_style=color_map['panel.border'],
        padding=(1, 2),
        width=min(get_terminal_width() - 4, 100)  # Responsive width with max
    )
    console.print(panel)

def display_status_panel(project_name: str, status_data: Dict[str, Any], console: Console) -> None:
    """Display project status in a structured table panel.
    
    Args:
        project_name: The name of the project.
        status_data: Dictionary of status properties and their values.
        console: Rich Console instance for rendering.
    """
    if not isinstance(console, Console):
        raise TypeError("console must be a Rich Console instance")
    color_map = Theme.get_color_map()
    table = Table(
        title=f"[bold {color_map['panel.title.color']}]Project Status: {project_name}[/bold {color_map['panel.title.color']}]",
        border_style=color_map['table.border'],
        width=min(get_terminal_width() - 4, 120)
    )
    table.add_column("Property", style=color_map['table.header'], no_wrap=True)
    table.add_column("Value", style=color_map['table.body'], max_width=get_terminal_width() // 2)

    for key, value in status_data.items():
        formatted_key = key.replace('_', ' ').title()
        table.add_row(formatted_key, str(value))

    console.print(table)


