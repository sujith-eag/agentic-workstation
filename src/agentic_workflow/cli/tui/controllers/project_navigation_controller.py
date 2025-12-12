"""
Navigation controllers for TUI.

This module contains controllers for navigation operations.
"""

from pathlib import Path
import questionary

from .base_controller import BaseController
from ...utils import display_error, display_info


class ProjectNavigationController(BaseController):
    """Controller for project navigation display."""

    def execute(self, *args, **kwargs) -> None:
        """Execute project navigation display."""
        display_info("Project Navigation")
        display_info("")

        if not self.app.project_root:
            display_error("Not in a project directory.")
            questionary.press_any_key_to_continue().ask()
            return

        self._display_project_info()
        self._display_directory_structure()
        self._display_help_info()

        questionary.press_any_key_to_continue().ask()

    def _display_project_info(self) -> None:
        """Display basic project information."""
        display_info(f"Project: {self.app.project_root.name}")
        display_info(f"Location: {self.app.project_root}")
        display_info("")

    def _display_directory_structure(self) -> None:
        """Display the key project directories with file counts."""
        dirs_to_show = ["agent_files", "artifacts", "docs", "input", "package"]
        for dir_name in dirs_to_show:
            dir_path = self.app.project_root / dir_name
            if dir_path.exists():
                file_count = self._count_files(dir_path)
                display_info(f"• {dir_name}/ ({file_count} items)")
            else:
                display_info(f"• {dir_name}/ (empty)")

    def _display_help_info(self) -> None:
        """Display helpful information about project directories."""
        display_info("")
        display_info("Use your file explorer or terminal to navigate the full project structure.")
        display_info("Key directories:")
        display_info("  • agent_files/ - Generated agent prompts and instructions")
        display_info("  • artifacts/ - Agent outputs and deliverables")
        display_info("  • docs/ - Project documentation")
        display_info("  • input/ - User requirements and specifications")
        display_info("  • package/ - Final project deliverables")

    def _count_files(self, dir_path: Path) -> int:
        """Count total files in a directory recursively."""
        return len(list(dir_path.rglob("*")))