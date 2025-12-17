"""
Interactive Setup Wizard for Agentic Workflow OS.
Triggers on first run to populate ~/.config/agentic/config.yaml.
"""
import os
import sys
import questionary
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import yaml

# Import the schema to ensure we save valid data
from agentic_workflow.core.schema import SystemConfig
from agentic_workflow.core.exceptions import ConfigError

console = Console()

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "agentic"


def run_setup_wizard() -> None:
    """Launch the first-run configuration wizard."""
    # For testing: auto-setup with defaults
    if os.environ.get('AGENTIC_AUTO_SETUP'):
        config_data = {
            "default_workspace": "~/AgenticProjects",
            "editor_command": "code",
            "tui_enabled": True,
            "check_updates": True,
            "log_level": "INFO"
        }
        _save_config(config_data)
        _ensure_workspace_exists(Path(config_data['default_workspace']).expanduser())
        console.print("[green]✓ Auto-setup complete![/green]")
        return

    console.clear()

    # 1. Welcome UI
    welcome = Text("Welcome to Agentic Workflow OS\n", style="bold blue")
    welcome.append("Let's set up your environment.", style="dim")
    console.print(Panel(welcome, border_style="blue", title="First-Run Setup"))

    try:
        # 2. Workspace Selection
        default_ws = "~/AgenticProjects"
        choices = [
            {"name": f"Default ({default_ws})", "value": default_ws},
            {"name": "Current Directory", "value": str(Path.cwd())},
            {"name": "Custom Path...", "value": "custom"}
        ]
        # Validate default is in choices
        if default_ws not in [choice['value'] for choice in choices]:
            default_ws = None
        ws_choice = questionary.select(
            "Where should we store your projects?",
            choices=choices,
            default=default_ws
        ).ask()

        if ws_choice == "custom":
            workspace_path = questionary.path("Path:", default=default_ws).ask()
        else:
            workspace_path = ws_choice

        # 3. Editor Selection
        editor_choice = questionary.select(
            "Which editor do you use?",
            choices=[
                {"name": "VS Code (code)", "value": "code"},
                {"name": "Vim (vim)", "value": "vim"},
                {"name": "Nano (nano)", "value": "nano"},
                {"name": "Custom...", "value": "custom"}
            ],
            default="code"
        ).ask()

        if editor_choice == "custom":
            editor_cmd = questionary.text("Enter command (e.g., 'subl', 'notepad'):").ask()
        else:
            editor_cmd = editor_choice

        # 4. Save & Exit
        config_data = {
            "default_workspace": workspace_path,
            "editor_command": editor_cmd,
            "tui_enabled": True,
            "check_updates": True,
            "log_level": "INFO"
        }

        console.print()
        console.print("[bold]Configuration Summary:[/bold]")
        console.print(f"  • Projects Location: [cyan]{config_data['default_workspace']}[/cyan]")
        console.print(f"  • Default Editor:    [cyan]{config_data['editor_command']}[/cyan]")
        console.print()

        confirm = questionary.confirm("Save configuration and continue?", default=True).ask()
        if confirm:
            _save_config(config_data)
            _ensure_workspace_exists(Path(workspace_path))

            console.print("[green]✓ Setup complete![/green]")
            console.print("Launching application...\n")
            # Logic flow returns to main.py here to continue execution
        else:
            console.print("[red]Setup cancelled. Exiting.[/red]")
            sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Setup interrupted.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        sys.exit(1)


def _save_config(data: dict) -> None:
    """Serialize config to YAML with validation."""
    try:
        # Validate against schema before saving
        valid_config = SystemConfig(**data)
        
        # Ensure config dir exists
        DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config_file = DEFAULT_CONFIG_DIR / "config.yaml"
        
        # Convert to dict and ensure paths are strings
        config_dict = valid_config.model_dump()
        config_dict['default_workspace'] = str(config_dict['default_workspace'])
        config_dict['log_level'] = config_dict['log_level'].value if hasattr(config_dict['log_level'], 'value') else config_dict['log_level']
        
        with open(config_file, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
            
    except Exception as e:
        console.print(f"[bold red]Error saving configuration:[/bold red] {e}")
        raise ConfigError(f"Failed to save configuration: {e}")
def _ensure_workspace_exists(path: Path) -> None:
    """Create the workspace directory if it doesn't exist"""
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            console.print(f"[dim]Created workspace directory: {path}[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not create workspace directory: {e}[/yellow]")