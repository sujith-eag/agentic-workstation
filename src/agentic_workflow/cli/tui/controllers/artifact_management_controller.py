"""
Artifact management controller for TUI.

This module contains the controller for artifact management menu.
"""

from .base_controller import BaseController
from ...utils import display_info


class ArtifactManagementController(BaseController):
    """Controller for artifact management menu."""

    def execute(self, *args, **kwargs) -> None:
        """Execute the artifact management."""
        self.run_menu()

    def run_menu(self) -> None:
        """Run the artifact management menu."""
        display_info("Artifact Management")
        display_info("")

        self.app.artifact_ops.execute_artifact_management(self.app.project_root)