"""
Global command handlers for Agentic Workflow CLI.

Handlers for commands available outside project context.
"""

from pathlib import Path
from typing import Optional
import logging

from ...core.schema import RuntimeConfig
from ...core.exceptions import AgenticWorkflowError
from ...generators.pipeline import InitPipeline
from ..utils import display_info, display_error

logger = logging.getLogger(__name__)


class GlobalHandlers:
    """Handlers for global CLI commands."""

    def handle_init(
        self,
        name: str,
        workflow: str = 'planning',
        description: Optional[str] = None,
        force: bool = False,
        config: RuntimeConfig = None
    ) -> None:
        """Handle project initialization."""
        if not config:
            raise AgenticWorkflowError("Configuration required for initialization")

        # Resolve project path using config
        target_path = self._resolve_project_path(name, config)

        # Initialize pipeline
        pipeline = InitPipeline(config)
        pipeline.run(name, str(target_path), workflow, force)

        # Display success with rich UI
        self._display_creation_success(name, target_path)

    def _resolve_project_path(self, name: str, config: RuntimeConfig) -> Path:
        """Resolve project path based on config and name."""
        path = Path(name)
        # If explicit path ("./app", "/tmp/app") -> Use it
        if path.is_absolute() or path.parts[0] in ['.', '..']:
            return path.resolve()

        # If name only ("my-app") -> Use Default Workspace
        return config.system.default_workspace / name

    def _display_creation_success(self, name: str, target_path: Path) -> None:
        """Display rich success message with created files/directories."""
        from rich.panel import Panel
        from rich.table import Table
        from rich.console import Console

        console = Console()

        # Create table of created items
        table = Table(title="Created Project Structure", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Path", style="green")

        # List created directories and files
        created_items = [
            ("Directory", ".agentic"),
            ("File", ".agentic/config.yaml"),
            ("File", ".agentic/active_session.md"),
            ("Directory", "agent_files"),
            ("Directory", "agent_context"),
            ("Directory", "agent_log"),
            ("Directory", "artifacts"),
            ("Directory", "docs"),
            ("Directory", "input"),
            ("Directory", "package"),
            ("File", "project_index.md"),
        ]

        for item_type, rel_path in created_items:
            full_path = target_path / rel_path
            if full_path.exists():
                table.add_row(item_type, rel_path)

        # Success panel
        success_panel = Panel.fit(
            f"[bold green]✓[/bold green] Project '{name}' initialized successfully!\n"
            f"[dim]Location: {target_path}[/dim]\n\n"
            f"Next steps:\n"
            f"• cd {target_path}\n"
            f"• agentic status\n"
            f"• agentic activate <agent_id>",
            title="[bold green]Success![/bold green]",
            border_style="green"
        )

        console.print(success_panel)
        console.print(table)

    def handle_list_workflows(self) -> None:
        """List available workflow types."""
        # For now, hardcode the known workflows
        workflows = ['planning', 'research', 'implementation']
        display_info("Available workflows:")
        for wf in workflows:
            display_info(f"  - {wf}")

    def handle_config(self, edit: bool = False) -> None:
        """Show or edit global configuration."""
        from ...core.config_service import ConfigurationService
        config_service = ConfigurationService()
        config_path = config_service._get_global_config_path()

        if edit:
            import subprocess
            from ...core.schema import SystemConfig
            config = SystemConfig()
            editor = config.editor_command
            try:
                subprocess.run([editor, str(config_path)])
            except Exception as e:
                display_error(f"Failed to open editor: {e}")
        else:
            if config_path.exists():
                with open(config_path) as f:
                    content = f.read()
                display_info(f"Global config at: {config_path}")
                display_info(content)
            else:
                display_info("No global config found. Run 'agentic' to set it up.")