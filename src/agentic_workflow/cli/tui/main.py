"""
Text User Interface for Agentic Workflow OS
Provides interactive menus and guided workflows for better UX.
"""

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from pathlib import Path
import sys
from typing import Optional

from ..utils import is_in_project, get_project_root, display_error, display_success, display_info, display_warning
from ..handlers.project_handlers import ProjectHandlers
from ..handlers.workflow_handlers import WorkflowHandlers
from ..handlers.session_handlers import SessionHandlers
from ..handlers.entry_handlers import EntryHandlers
from agentic_workflow import __version__


console = Console()


class TUIApp:
    """Main TUI Application Class"""

    def __init__(self):
        self.current_context = self._detect_context()
        self.project_root = get_project_root() if self.current_context == "project" else None
        self.project_handlers = ProjectHandlers()
        self.workflow_handlers = WorkflowHandlers()
        self.session_handlers = SessionHandlers()
        self.entry_handlers = EntryHandlers()

    def _detect_context(self) -> str:
        """Detect if we're in global or project context"""
        return "project" if is_in_project() else "global"

    def run(self):
        """Main TUI loop"""
        try:
            while True:
                if self.current_context == "global":
                    self._show_global_menu()
                else:
                    self._show_project_menu()
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            sys.exit(0)
        except Exception as e:
            display_error(f"TUI Error: {e}")
            sys.exit(1)

    def _show_global_menu(self):
        """Display global context menu"""
        console.clear()

        # Header
        header = Panel.fit(
            "[bold blue]Agentic Workflow OS - Global Mode[/bold blue]\n"
            "[dim]Project Management & Creation[/dim]",
            border_style="blue"
        )
        console.print(header)
        console.print()

        # Menu options
        choice = questionary.select(
            "Select an option:",
            choices=[
                {"name": "Create New Project", "value": "create"},
                {"name": "List Existing Projects", "value": "list"},
                {"name": "Manage Existing Project", "value": "manage"},
                {"name": "System Information", "value": "info"},
                {"name": "Exit", "value": "exit"}
            ],
            use_shortcuts=True
        ).ask()

        if choice == "create":
            self._create_project_wizard()
        elif choice == "list":
            self._list_projects()
        elif choice == "manage":
            self._manage_project_menu()
        elif choice == "info":
            self._show_system_info()
        elif choice == "exit":
            sys.exit(0)

    def _show_project_menu(self):
        """Display project context menu"""
        console.clear()

        project_name = self.project_root.name if self.project_root else "Unknown"

        # Header
        header = Panel.fit(
            f"[bold green]Agentic Workflow OS - Project: {project_name}[/bold green]\n"
            "[dim]Workflow Operations & Agent Management[/dim]",
            border_style="green"
        )
        console.print(header)
        console.print()

        # Menu options
        choice = questionary.select(
            "Select an option:",
            choices=[
                {"name": "View Workflow Status", "value": "status"},
                {"name": "Agent Operations", "value": "agents"},
                {"name": "Artifact Management", "value": "artifacts"},
                {"name": "Project Navigation", "value": "navigate"},
                {"name": "Return to Global Mode", "value": "exit"}
            ],
            use_shortcuts=True
        ).ask()

        if choice == "status":
            self._show_workflow_status()
        elif choice == "agents":
            self._agent_operations_menu()
        elif choice == "artifacts":
            self._artifact_management_menu()
        elif choice == "navigate":
            self._project_navigation()
        elif choice == "exit":
            self.current_context = "global"
            self.project_root = None

    def _create_project_wizard(self):
        """Guided project creation wizard"""
        console.print("[bold]Project Creation Wizard[/bold]\n")

        # Project name
        name = questionary.text("Project name:").ask()
        if not name:
            return

        # Workflow type - get real workflow types
        try:
            from ...services import WorkflowService
            workflow_service = WorkflowService()
            workflows = workflow_service.list_workflows()
            workflow_choices = []
            for workflow in workflows:
                info = workflow_service.get_workflow_info(workflow['name'])
                desc = f"{info.get('description', 'No description')[:60]}..."
                workflow_choices.append({
                    "name": f"{workflow['name']} - {desc}",
                    "value": workflow['name']
                })
        except Exception:
            # Fallback to known workflows
            workflow_choices = [
                {"name": "planning - Comprehensive project planning", "value": "planning"},
                {"name": "research - Academic research workflow", "value": "research"},
                {"name": "implementation - Test-driven development", "value": "implementation"},
                {"name": "workflow-creation - Meta-workflow creation", "value": "workflow-creation"}
            ]

        workflow_type = questionary.select(
            "Select workflow type:",
            choices=workflow_choices
        ).ask()

        # Description
        description = questionary.text("Project description:").ask()

        # Confirm
        confirm = questionary.confirm(f"Create project '{name}' with {workflow_type} workflow?").ask()

        if confirm:
            try:
                # Use real project creation handler
                self.project_handlers.handle_init(
                    name=name,
                    workflow=workflow_type,
                    description=description,
                    force=False
                )
                display_success(f"Project '{name}' created successfully!")
                questionary.press_any_key_to_continue().ask()
            except Exception as e:
                display_error(f"Failed to create project: {e}")
                questionary.press_any_key_to_continue().ask()
        else:
            display_error("Project creation cancelled.")

    def _list_projects(self):
        """List existing projects"""
        console.print("[bold]Existing Projects[/bold]\n")

        try:
            # Get project data directly from service
            from ...services import ProjectService
            project_service = ProjectService()
            result = project_service.list_projects()

            if result['count'] > 0:
                # Format projects in a nice table
                table = Table()
                table.add_column("Project Name", style="cyan", no_wrap=True)
                table.add_column("Workflow", style="green")
                table.add_column("Description", style="yellow")

                for project in result['projects']:
                    table.add_row(
                        project['name'],
                        project['workflow'],
                        project['description'] or "(no description)"
                    )

                console.print(table)
            else:
                console.print("[dim]No projects found.[/dim]")

        except Exception as e:
            display_error(f"Failed to list projects: {e}")

        questionary.press_any_key_to_continue().ask()

    def _manage_project_menu(self):
        """Project management submenu"""
        console.print("[bold]Project Management[/bold]\n")

        # Get list of projects for selection
        try:
            from ...services import ProjectService
            project_service = ProjectService()
            
            # This is a simplified approach - in a real implementation we'd parse the project list
            projects_dir = Path("projects")
            if projects_dir.exists():
                projects = [p.name for p in projects_dir.iterdir() if p.is_dir()]
            else:
                projects = []
                
            if not projects:
                display_warning("No projects found to manage.")
                questionary.press_any_key_to_continue().ask()
                return

            # Project selection
            project_name = questionary.select(
                "Select project to manage:",
                choices=projects
            ).ask()

            # Management actions
            action = questionary.select(
                f"Select action for '{project_name}':",
                choices=[
                    {"name": "View Project Status", "value": "status"},
                    {"name": "Remove Project", "value": "remove"},
                    {"name": "Cancel", "value": "cancel"}
                ]
            ).ask()

            if action == "status":
                try:
                    # Change to project directory temporarily
                    import os
                    original_cwd = os.getcwd()
                    os.chdir(f"projects/{project_name}")
                    self.project_handlers.handle_status()
                    os.chdir(original_cwd)
                except Exception as e:
                    display_error(f"Failed to get project status: {e}")
                    
            elif action == "remove":
                confirm = questionary.confirm(
                    f"Are you sure you want to remove project '{project_name}'? This action cannot be undone.",
                    default=False
                ).ask()
                
                if confirm:
                    try:
                        self.project_handlers.handle_remove(name=project_name, force=False)
                        display_success(f"Project '{project_name}' removed successfully!")
                    except Exception as e:
                        display_error(f"Failed to remove project: {e}")
                else:
                    display_info("Project removal cancelled.")
                    
            elif action == "cancel":
                return

        except Exception as e:
            display_error(f"Project management error: {e}")

        questionary.press_any_key_to_continue().ask()

    def _show_system_info(self):
        """Show system information"""
        console.print("[bold]System Information[/bold]\n")

        # Get real system information
        import sys
        from pathlib import Path
        
        # Count projects
        projects_dir = Path("projects")
        project_count = 0
        if projects_dir.exists():
            project_count = len([p for p in projects_dir.iterdir() if p.is_dir()])

        # Count workflows
        try:
            from ...services import WorkflowService
            workflow_service = WorkflowService()
            workflows = workflow_service.list_workflows()
            workflow_count = len(workflows)
        except:
            workflow_count = 4  # fallback

        # System info table
        info_table = Table()
        info_table.add_column("Property", style="cyan", no_wrap=True)
        info_table.add_column("Value", style="yellow")

        info_table.add_row("Version", __version__)
        info_table.add_row("Python Version", f"{sys.version.split()[0]}")
        info_table.add_row("Platform", sys.platform)
        info_table.add_row("Projects", str(project_count))
        info_table.add_row("Workflow Types", str(workflow_count))
        info_table.add_row("Working Directory", str(Path.cwd()))

        console.print(info_table)
        questionary.press_any_key_to_continue().ask()

    def _show_workflow_status(self):
        """Show workflow status for current project"""
        console.print("[bold]Workflow Status[/bold]\n")

        try:
            # Get project status directly from service
            from ...services import ProjectService
            project_service = ProjectService()
            result = project_service.get_project_status()

            if result['status'] == 'not_in_project':
                display_error("Not in a project directory")
                display_info("Use 'Create New Project' to create a new project")
            elif result.get('config'):
                # Format project status in a nice table
                config = result['config']
                table = Table()
                table.add_column("Property", style="cyan", no_wrap=True)
                table.add_column("Value", style="yellow")

                for key, value in config.items():
                    if isinstance(value, dict):
                        table.add_row(key, str(value))
                    else:
                        table.add_row(key, str(value))

                console.print(table)
            else:
                display_warning("Project found but no configuration available")

        except Exception as e:
            display_error(f"Failed to get workflow status: {e}")

        questionary.press_any_key_to_continue().ask()

    def _agent_operations_menu(self):
        """Agent operations submenu"""
        console.print("[bold]Agent Operations[/bold]\n")

        project_name = self.project_root.name if self.project_root else "Unknown"

        # Agent operations menu
        choice = questionary.select(
            "Select agent operation:",
            choices=[
                {"name": "Activate Agent", "value": "activate"},
                {"name": "Record Agent Handoff", "value": "handoff"},
                {"name": "Record Decision", "value": "decision"},
                {"name": "End Workflow", "value": "end"},
                {"name": "Populate Agent Templates", "value": "populate"},
                {"name": "Cancel", "value": "cancel"}
            ]
        ).ask()

        if choice == "activate":
            agent_id = questionary.text("Enter agent ID to activate:").ask()
            if agent_id:
                try:
                    self.session_handlers.handle_activate(
                        project=project_name,
                        agent_id=agent_id
                    )
                    display_success(f"Agent {agent_id} activated successfully!")
                except Exception as e:
                    display_error(f"Failed to activate agent: {e}")

        elif choice == "handoff":
            from_agent = questionary.text("From agent ID:").ask()
            to_agent = questionary.text("To agent ID:").ask()
            artifacts = questionary.text("Artifacts (comma-separated, optional):").ask()
            notes = questionary.text("Handoff notes (optional):").ask()
            
            if from_agent and to_agent:
                try:
                    self.entry_handlers.handle_handoff(
                        project=project_name,
                        from_agent=from_agent,
                        to_agent=to_agent,
                        artifacts=artifacts if artifacts else None,
                        notes=notes if notes else None
                    )
                    display_success("Handoff recorded successfully!")
                except Exception as e:
                    display_error(f"Failed to record handoff: {e}")

        elif choice == "decision":
            title = questionary.text("Decision title:").ask()
            rationale = questionary.text("Decision rationale:").ask()
            agent = questionary.text("Agent ID (optional):").ask()
            
            if title and rationale:
                try:
                    self.entry_handlers.handle_decision(
                        project=project_name,
                        title=title,
                        rationale=rationale,
                        agent=agent if agent else None
                    )
                    display_success("Decision recorded successfully!")
                except Exception as e:
                    display_error(f"Failed to record decision: {e}")

        elif choice == "end":
            confirm = questionary.confirm("Are you sure you want to end the workflow?", default=False).ask()
            if confirm:
                try:
                    self.session_handlers.handle_end(project=project_name)
                    display_success("Workflow ended successfully!")
                except Exception as e:
                    display_error(f"Failed to end workflow: {e}")

        elif choice == "populate":
            try:
                self.session_handlers.handle_populate(project=project_name)
                display_success("Agent frontmatter populated successfully!")
            except Exception as e:
                display_error(f"Failed to populate agents: {e}")

        elif choice == "cancel":
            return

        questionary.press_any_key_to_continue().ask()

    def _artifact_management_menu(self):
        """Artifact management submenu"""
        console.print("[bold]Artifact Management[/bold]\n")

        if not self.project_root:
            display_error("Not in a project directory.")
            questionary.press_any_key_to_continue().ask()
            return

        artifacts_dir = self.project_root / "artifacts"
        if not artifacts_dir.exists():
            display_warning("No artifacts directory found in this project.")
            questionary.press_any_key_to_continue().ask()
            return

        # List available artifacts
        artifacts = []
        for file_path in artifacts_dir.rglob("*"):
            if file_path.is_file():
                artifacts.append(file_path.relative_to(artifacts_dir))

        if not artifacts:
            display_info("No artifacts found in the artifacts directory.")
            questionary.press_any_key_to_continue().ask()
            return

        # Artifact selection
        artifact_choices = [{"name": str(artifact), "value": artifact} for artifact in artifacts]
        artifact_choices.append({"name": "Cancel", "value": "cancel"})
        
        selected = questionary.select(
            "Select an artifact to view:",
            choices=artifact_choices
        ).ask()

        if selected and selected != "cancel":
            try:
                full_path = artifacts_dir / selected
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                console.clear()
                console.print(f"[bold]📄 {selected}[/bold]\n")
                
                # Show content (truncated if too long)
                if len(content) > 2000:
                    console.print(content[:2000] + "\n[dim]... (truncated)[/dim]")
                else:
                    console.print(content)
                    
            except Exception as e:
                display_error(f"Failed to read artifact: {e}")

        questionary.press_any_key_to_continue().ask()

    def _project_navigation(self):
        """Project navigation submenu"""
        console.print("[bold]Project Navigation[/bold]\n")

        if not self.project_root:
            display_error("Not in a project directory.")
            questionary.press_any_key_to_continue().ask()
            return

        # Show project structure
        display_info(f"Project: {self.project_root.name}")
        display_info(f"Location: {self.project_root}")
        console.print()

        # Key directories
        dirs_to_show = ["agent_files", "artifacts", "docs", "input", "package"]
        for dir_name in dirs_to_show:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                file_count = len(list(dir_path.rglob("*")))
                console.print(f"• {dir_name}/ ({file_count} items)")
            else:
                console.print(f"• {dir_name}/ (empty)")

        console.print()
        display_info("Use your file explorer or terminal to navigate the full project structure.")
        display_info("Key directories:")
        display_info("  • agent_files/ - Generated agent prompts and instructions")
        display_info("  • artifacts/ - Agent outputs and deliverables")
        display_info("  • docs/ - Project documentation")
        display_info("  • input/ - User requirements and specifications")
        display_info("  • package/ - Final project deliverables")

        questionary.press_any_key_to_continue().ask()


def main():
    """TUI entry point"""
    app = TUIApp()
    app.run()


if __name__ == "__main__":
    main()