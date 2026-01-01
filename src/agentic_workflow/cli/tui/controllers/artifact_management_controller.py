"""
Artifact management controller for TUI.

This module contains the controller for artifact management menu.
"""

import logging
from pathlib import Path
from questionary import Choice

from .base_controller import BaseController
from ..ui import InputResult
from ..views import ArtifactContentView
from agentic_workflow.core.exceptions import FileSystemError

logger = logging.getLogger(__name__)


class ArtifactManagementController(BaseController):
    """Controller for artifact management menu."""

    def __init__(self, artifact_handlers, progress, **kwargs):
        """Initialize with required dependencies."""
        super().__init__(**kwargs)
        self.artifact_handlers = artifact_handlers
        self.progress = progress
        # project_root is already set by BaseController

    def execute(self, *args, **kwargs) -> None:
        """Execute the artifact management."""
        self.run_menu()

    def run_menu(self) -> None:
        """Run the artifact management menu."""
        self.feedback.info("Artifact Management")

        project_root = self.project_root
        if not project_root:
            self.error_view.display_error_modal("Not in a project directory.", title="Project Required")
            return

        artifacts_dir = Path(project_root) / "artifacts"
        if not artifacts_dir.exists():
            self.feedback.warning("No artifacts directory found in this project.")
            self.input_handler.wait_for_user()
            return

        artifacts = self.artifact_handlers.list_artifacts(artifacts_dir)
        if not artifacts:
            self.feedback.info("No artifacts found in the artifacts directory.")
            self.input_handler.wait_for_user()
            return

        artifact_choices = [
            Choice(title=str(relative_path), value=(full_path, relative_path))
            for full_path, relative_path in artifacts
        ]

        selected = self.input_handler.get_selection(
            choices=artifact_choices,
            message="Select an artifact to view:"
        )

        if selected == InputResult.EXIT or selected is None:
            return

        full_path, relative_path = selected
        try:
            with self.progress.spinner(f"Opening {relative_path}"):
                content = self.artifact_handlers.read_artifact(full_path)

            view = ArtifactContentView(console=self.console, theme_map=self.theme.get_color_map())
            view.render(full_path, relative_path, content)
            self.input_handler.wait_for_user("Press Enter to return to artifacts...")
        except FileSystemError as e:
            self.error_view.display_error_modal(f"Failed to read artifact: {e}", title="Read Error")
        except Exception as e:
            logger.exception(f"Unexpected error reading artifact {relative_path}: {e}")
            self.error_view.display_error_modal(f"Unexpected error: {e}", title="Critical Error")
            raise


__all__ = ["ArtifactManagementController"]