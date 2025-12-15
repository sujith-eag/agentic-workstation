"""
Artifact operations for TUI.

This module contains operation classes that handle artifact/file
browsing and display operations for the TUI.
"""

from pathlib import Path
from typing import List, Tuple, Any
import questionary

from ...utils import display_error, display_info
from rich.console import Console
from ..views import ArtifactListView, ArtifactContentView

console = Console()


class ArtifactOperations:
    """Operations for browsing and displaying project artifacts."""

    def __init__(self, app):
        self.app = app
    """Operations for browsing and displaying project artifacts."""

    def execute(self, *args, **kwargs) -> Any:
        """Execute artifact management operation."""
        if args and isinstance(args[0], Path):
            project_root = args[0]
        else:
            project_root = kwargs.get('project_root', self.app.project_root)
        return self.execute_artifact_management(project_root)

    def get_artifact_list(self, project_root: Path) -> List[Path]:
        """Get list of artifacts in the project."""
        artifacts_dir = project_root / "artifacts"
        if not artifacts_dir.exists():
            return []

        artifacts = []
        for file_path in artifacts_dir.rglob("*"):
            if file_path.is_file():
                artifacts.append(file_path)
        return artifacts

    def get_relative_artifacts(self, project_root: Path) -> List[Tuple[Path, str]]:
        """Get artifacts with relative paths for display."""
        artifacts_dir = project_root / "artifacts"
        artifacts = []

        for file_path in artifacts_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(artifacts_dir)
                artifacts.append((file_path, str(relative_path)))

        return artifacts

    def display_artifact_content(self, file_path: Path, relative_path: str) -> bool:
        """Display the content of an artifact file."""
        try:
            console.clear()

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Use ArtifactContentView for structured display
            view = ArtifactContentView()
            view.render(file_path, relative_path, content)

            return True
        except Exception as e:
            display_error(f"Failed to read artifact: {e}")
            return False

    def has_artifacts(self, project_root: Path) -> bool:
        """Check if project has any artifacts."""
        artifacts = self.get_artifact_list(project_root)
        return len(artifacts) > 0

    def execute_artifact_management(self, project_root: Path) -> None:
        """Execute the full artifact management workflow."""
        from ...utils import display_warning

        if not project_root:
            display_error("Not in a project directory.")
            questionary.press_any_key_to_continue().ask()
            return

        artifacts_dir = project_root / "artifacts"
        if not artifacts_dir.exists():
            display_warning("No artifacts directory found in this project.")
            questionary.press_any_key_to_continue().ask()
            return

        # Get artifacts with relative paths
        artifacts = self.get_relative_artifacts(project_root)
        if not artifacts:
            display_info("No artifacts found in the artifacts directory.")
            questionary.press_any_key_to_continue().ask()
            return

        # Artifact selection
        artifact_choices = [{"name": str(relative), "value": (full_path, relative)}
                           for full_path, relative in artifacts]
        artifact_choices.append({"name": "Cancel", "value": "cancel"})

        selected = questionary.select(
            "Select an artifact to view:",
            choices=artifact_choices
        ).ask()

        if selected and selected != "cancel":
            full_path, relative_path = selected
            self.display_artifact_content(full_path, relative_path)

        questionary.press_any_key_to_continue().ask()