"""
Project view components for displaying project-related data.

This module contains view classes for rendering project lists,
project status, and other project-related information.
"""

from typing import Dict, Any, List
from rich.table import Table
from rich.console import Console

from .base_views import BaseView

console = Console()


class ProjectListView(BaseView):
    """View for displaying lists of projects."""

    def render(self, data: Dict[str, Any]) -> None:
        """Render project list in a table format."""
        projects = data.get('projects', [])

        if not projects:
            console.print("No projects found.")
            return

        # Format projects in a nice table
        table = Table()
        table.add_column("Project Name", style="cyan", no_wrap=True)
        table.add_column("Workflow", style="green")
        table.add_column("Description", style="yellow")

        for project in projects:
            table.add_row(
                project['name'],
                project['workflow'],
                project['description'] or "(no description)"
            )

        console.print(table)


class ProjectStatusView(BaseView):
    """View for displaying individual project status."""

    def render(self, data: Dict[str, Any]) -> None:
        """Render project status in a table format."""
        config = data.get('config')

        if not config:
            console.print("⚠ Project found but no configuration available")
            location = data.get('path', 'unknown')
            console.print(f"ℹ Location: {location}")
            return

        # Format project status in a nice table
        table = Table()
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow")

        # Add basic project info
        table.add_row("Project Name", config.get('name', data.get('project_name', 'unknown')))
        table.add_row("Workflow", config.get('workflow', 'unknown'))
        table.add_row("Description", config.get('description', ''))
        table.add_row("Location", str(data.get('path', 'unknown')))

        # Add workflow status if available
        if 'workflow_status' in config:
            workflow_status = config['workflow_status']
            table.add_row("Current Stage", workflow_status.get('stage', 'unknown'))
            table.add_row("Active Agent", workflow_status.get('active_agent', 'none'))

        console.print(table)


class ProjectSummaryView(BaseView):
    """View for displaying project creation summaries."""

    def render(self, data: Dict[str, Any]) -> None:
        """Render project summary with directories and next steps."""
        project_name = data.get('project_name', 'unknown')
        workflow_type = data.get('workflow_type', 'unknown')
        directories = data.get('directories', [])
        next_steps = data.get('next_steps', [])

        # Header
        console.print(f"\n[bold green]Project '{project_name}' created successfully![/bold green]")
        console.print(f"[dim]Workflow: {workflow_type}[/dim]\n")

        # Directories section
        if directories:
            console.print("[bold cyan]Project Structure:[/bold cyan]")
            for directory in directories:
                console.print(f"  • {directory}/")
            console.print()

        # Next steps section
        if next_steps:
            console.print("[bold cyan]Next Steps:[/bold cyan]")
            for step in next_steps:
                console.print(f"  {step}")
            console.print()