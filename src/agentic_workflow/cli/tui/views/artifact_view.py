"""
Artifact view for TUI file browsing.

This module contains views for displaying project artifacts
and file contents in a structured format.
"""

from pathlib import Path
from typing import List, Tuple
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax

from .base_views import BaseView


class ArtifactListView(BaseView):
    """View for displaying artifact file lists."""

    def render(self, artifacts: List[Tuple[Path, str]]) -> None:
        """Render the artifact list."""
        if not artifacts:
            self.console.print("[yellow]No artifacts found.[/yellow]")
            return

        table = Table(title="📁 Project Artifacts")
        table.add_column("File", style="cyan", no_wrap=True)
        table.add_column("Size", style="green", justify="right")

        for full_path, relative_path in artifacts:
            try:
                size = full_path.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                table.add_row(relative_path, size_str)
            except OSError:
                table.add_row(relative_path, "N/A")

        self.console.print(table)


class ArtifactContentView(BaseView):
    """View for displaying artifact file contents."""

    def render(self, file_path: Path, relative_path: str, content: str) -> None:
        """Render the artifact content with syntax highlighting."""
        # Determine syntax based on file extension
        suffix = file_path.suffix.lower()
        lexer_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
        }
        lexer = lexer_map.get(suffix, 'text')

        # Create syntax-highlighted content
        syntax = Syntax(content, lexer, theme="monokai", line_numbers=True)

        # Create panel with file info
        panel = Panel(
            syntax,
            title=f"📄 {relative_path}",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(panel)