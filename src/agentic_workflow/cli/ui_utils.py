#!/usr/bin/env python3
"""UI utility functions for Agentic Workflow CLI."""
import sys
from typing import Any, Dict, List, NoReturn, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import structlog
from contextlib import contextmanager
import json
import yaml
from .display import display_error, display_info


__all__ = [
    "setup_logging",
    "format_output",
    "show_progress",
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


def format_output(data: Any, format_type: str = "table", title: Optional[str] = None, console: Optional[Console] = None) -> None:
    """Format data for output in various formats.
    
    Delegates to display_table() for consistency with display layer.
    
    Args:
        data: The data to format and display.
        format_type: Output format - 'table', 'json', or 'yaml'.
        title: Optional title for the output.
        console: Rich Console instance (creates new if None).
    """
    if console is None:
        console = Console()
    
    try:
        # Delegate to display layer for consistency
        from .display import display_table
        
        if isinstance(data, list):
            display_table(data, console, title=title, format_type=format_type)
        elif isinstance(data, dict):
            # Convert dict to list of key-value pairs for table display
            dict_list = [{"Key": k, "Value": str(v)} for k, v in data.items()]
            display_table(dict_list, console, title=title, format_type=format_type)
        else:
            # Fallback for non-structured data
            console.print(data)
    except Exception as e:
        display_error(f"Failed to format output: {e}", console)
        console.print(data)  # Fallback to raw output


@contextmanager
def show_progress(message: str, console: Optional[Console] = None):
    """Show a progress indicator as a context manager."""
    if console is None:
        console = Console()
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

