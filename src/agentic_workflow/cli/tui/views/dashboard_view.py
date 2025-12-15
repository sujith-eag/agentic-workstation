"""
Dashboard view for TUI project cockpit.

This module contains the dashboard view that displays project status
and session context in a cockpit-style interface.
"""

from typing import Dict, Any, List
from datetime import datetime
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.style import Style

from .base_views import BaseView

class DashboardView(BaseView):
    """Dashboard view for project cockpit interface."""

    # SEMANTIC STYLES (Centralized Theming)
    THEME = {
        "project.border": "blue",
        "project.title": "bold blue",
        "project.key": "cyan",
        "session.border": "green",
        "session.title": "bold green",
        "session.key": "green",
        "activity.border": "magenta",
        "activity.title": "bold magenta",
        "activity.header": "bold magenta",
        "text.value": "yellow",
        "text.dim": "dim",
    }

    def render(self, 
               project_name: str, 
               session_context: Dict[str, Any], 
               status: Dict[str, Any], 
               recent_activity: List[Dict[str, Any]] = None) -> None:
        """Render the dashboard with project info, session context, status, and recent activity."""
        
        # 1. Main Layout Structure
        layout = Layout()
        layout.split_column(
            Layout(name="top", ratio=1),
            Layout(name="bottom", ratio=1)
        )
        layout["top"].split_row(
            Layout(name="left_panel", ratio=1),
            Layout(name="right_panel", ratio=1)
        )

        # 2. Data Preparation (Normalization)
        project_data = {
            "Project": project_name,
            "Workflow": status.get('workflow') or 'Not set',
            "Description": status.get('description') or 'No description available'
        }

        session_data = {
            "Active Agent": session_context.get('active_agent') or 'No active agent',
            "Current Stage": status.get('stage') or 'Not started',
            "Last Action": session_context.get('last_action') or 'No recent activity'
        }

        # 3. Component Rendering (Using Helper)
        layout["top"]["left_panel"].update(
            self._create_info_panel("Project Information", project_data, "project")
        )

        layout["top"]["right_panel"].update(
            self._create_info_panel("Session Status", session_data, "session")
        )

        layout["bottom"].update(
            self._create_activity_panel(recent_activity or [])
        )

        self.console.print(layout)

    def _create_info_panel(self, title: str, data: Dict[str, str], theme_prefix: str) -> Panel:
        """
        Generic helper to create Key-Value information panels.
        
        Args:
            title: Panel title text
            data: Dictionary of Label->Value pairs
            theme_prefix: Key prefix to look up in self.THEME (e.g., 'project')
        """
        content = Text()
        
        for key, value in data.items():
            # Apply semantic styling
            key_style = self.THEME.get(f"{theme_prefix}.key", "bold")
            val_style = self.THEME.get("text.value", "default")
            
            # Special handling for description/long text to be dim
            if key in ["Description", "Last Action"]:
                val_style = self.THEME.get("text.dim", "dim")

            content.append(f"{key}: ", style=key_style)
            content.append(f"{value}\n", style=val_style)

        return Panel(
            content,
            title=f"[{self.THEME[f'{theme_prefix}.title']}]{title}[/]",
            border_style=self.THEME[f'{theme_prefix}.border'],
            padding=(1, 2)
        )

    def _create_activity_panel(self, activity: List[Dict[str, Any]]) -> Panel:
        """Create the recent activity panel with robust formatting."""
        table = Table(
            show_header=True, 
            header_style=self.THEME["activity.header"],
            expand=True  # Ensure table fills the panel
        )
        
        # Define columns with explicit ratios/widths for responsiveness
        table.add_column("Time", style="dim", width=16, no_wrap=True)
        table.add_column("Type", width=10)
        table.add_column("Summary", style="white", ratio=1, overflow="fold") # Fold long text

        if not activity:
            # Handle empty state gracefully
            table.add_row("No recent activity", "-", "-")
        else:
            for item in activity:
                table.add_row(
                    self._format_timestamp(item.get('timestamp')),
                    item.get('type', 'unknown').title(),
                    item.get('summary', 'No summary')
                )

        return Panel(
            table,
            title=f"[{self.THEME['activity.title']}]Recent Activity[/]",
            border_style=self.THEME["activity.border"],
            padding=(1, 2)
        )

    def _format_timestamp(self, ts_str: str) -> str:
        """Robustly parse and format timestamps."""
        if not ts_str:
            return ""
        try:
            # Parse ISO format (e.g., 2025-12-15T14:30:00.123456)
            dt = datetime.fromisoformat(ts_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            # Fallback for unexpected formats
            return ts_str[:16]