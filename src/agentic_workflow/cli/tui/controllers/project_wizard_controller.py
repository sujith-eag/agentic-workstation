"""
Wizard controllers for TUI.

This module contains controllers for guided workflows and wizards.
"""

import questionary

from .base_controller import BaseController
from ...utils import display_error, display_info, display_success, show_progress


class ProjectWizardController(BaseController):
    """Controller for project creation wizard."""

    def execute(self, *args, **kwargs) -> None:
        """Execute the project creation wizard."""
        display_info("Project Creation Wizard")
        display_info("")

        # Project name
        name = questionary.text("Project name:").ask()
        if not name:
            return

        # Workflow type - get real workflow types
        try:
            workflow_type = self._select_workflow_type()
        except Exception as e:
            display_error(f"Failed to load workflows: {e}")
            questionary.press_any_key_to_continue().ask()
            return

        # Description
        description = questionary.text("Project description:").ask()

        # Confirm
        confirm = questionary.confirm(f"Create project '{name}' with {workflow_type} workflow?").ask()

        if confirm:
            try:
                # Use session handlers for proper atomic pipeline initialization
                with show_progress(f"Creating project '{name}'..."):
                    self.app.session_handlers.handle_init(
                        project=name,
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

    def _select_workflow_type(self) -> str:
        """Select workflow type with dynamic loading."""
        try:
            from agentic_workflow.services import WorkflowService
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
        except Exception as e:
            # No fallback - rely on WorkflowService as single source of truth
            from agentic_workflow.core.exceptions import AgenticWorkflowError
            raise AgenticWorkflowError("No workflows found. System may be corrupt.") from e

        return questionary.select(
            "Select workflow type:",
            choices=workflow_choices
        ).ask()