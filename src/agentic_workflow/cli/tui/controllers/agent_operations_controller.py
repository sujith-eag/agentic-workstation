"""
Agent operations controller for TUI.

This module contains the controller for agent operations menu.
"""

import questionary
from rich.console import Console

from .base_controller import BaseController
from ...utils import display_info

console = Console()


class AgentOperationsController(BaseController):
    """Controller for agent operations menu."""

    def execute(self, *args, **kwargs) -> None:
        """Execute the agent operations menu."""
        self.run_menu()

    def run_menu(self) -> None:
        """Run the agent operations menu."""
        display_info("Agent Operations")
        display_info("")

        project_name = self.app.project_root.name if self.app.project_root else "Unknown"

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
                self.app.agent_ops.execute_agent_activation(agent_id, project_name)

        elif choice == "handoff":
            from_agent = questionary.text("From agent ID:").ask()
            to_agent = questionary.text("To agent ID:").ask()
            artifacts = questionary.text("Artifacts (comma-separated, optional):").ask()
            notes = questionary.text("Handoff notes (optional):").ask()

            if from_agent and to_agent:
                self.app.agent_ops.execute_agent_handoff(from_agent, to_agent, project_name, artifacts, notes)

        elif choice == "decision":
            title = questionary.text("Decision title:").ask()
            rationale = questionary.text("Decision rationale:").ask()
            agent = questionary.text("Agent ID (optional):").ask()

            if title and rationale:
                self.app.agent_ops.execute_decision_recording(title, rationale, project_name, agent)

        elif choice == "end":
            confirm = questionary.confirm("Are you sure you want to end the workflow?", default=False).ask()
            if confirm:
                self.app.agent_ops.execute_workflow_end(project_name)

        elif choice == "populate":
            self.app.agent_ops.execute_agent_population(project_name)

        elif choice == "cancel":
            return

        questionary.press_any_key_to_continue().ask()