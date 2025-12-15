"""
Agent operations controller for TUI.

This module contains the controller for agent operations menu.
"""

import questionary
from rich.console import Console

from .base_controller import BaseController
from ...utils import display_info, display_success, display_error, show_progress
from ...handlers import SessionHandlers, EntryHandlers

console = Console()


class AgentOperationsController(BaseController):
    """Controller for agent operations menu."""

    def execute(self, *args, **kwargs) -> None:
        """Execute the agent operations menu."""
        self.run_menu()

    def run_menu(self) -> None:
        """Run the agent operations menu."""
        self.display_context_header("Agent Operations")

        project_name = self.app.project_root.name if self.app.project_root else "Unknown"

        # Agent operations menu
        choice = questionary.select(
            "Select agent operation:",
            choices=[
                {"name": "Activate Agent", "value": "activate"},
                {"name": "Record Agent Handoff", "value": "handoff"},
                {"name": "Record Decision", "value": "decision"},
                {"name": "Record Feedback", "value": "feedback"},
                {"name": "Record Blocker", "value": "blocker"},
                {"name": "Record Iteration", "value": "iteration"},
                {"name": "Record Assumption", "value": "assumption"},
                {"name": "End Workflow", "value": "end"},
                {"name": "Cancel", "value": "cancel"}
            ]
        ).ask()

        if choice == "activate":
            agent_id = questionary.text("Enter agent ID to activate:").ask()
            if agent_id:
                try:
                    with show_progress(f"Activating agent {agent_id}..."):
                        self.app.session_handlers.handle_activate(
                            project=project_name,
                            agent_id=agent_id
                        )
                    display_success(f"Agent {agent_id} activated successfully!")
                    # Note: session_context is now fetched fresh from services, no manual update needed
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "handoff":
            # Prefetch active agent
            active_agent = "Unknown"
            try:
                from agentic_workflow.services import LedgerService
                ledger_service = LedgerService()
                session_data = ledger_service.get_active_session(project_name)
                if session_data and session_data.get('agent_id'):
                    active_agent = session_data['agent_id']
            except Exception:
                pass  # Keep default if fetch fails
            
            # Pre-fill from_agent with active agent
            from_agent = questionary.text(
                "From agent ID:",
                default=active_agent
            ).ask()
            
            to_agent = questionary.text(
                "To agent ID:",
                validate=lambda x: len(x.strip()) > 0 or "To agent ID is required"
            ).ask()
            
            artifacts = questionary.text("Artifacts (comma-separated, optional):").ask()
            notes = questionary.text("Handoff notes (optional):").ask()

            if from_agent and to_agent:
                try:
                    with show_progress("Recording agent handoff..."):
                        self.app.entry_handlers.handle_handoff(
                            project=project_name,
                            from_agent=from_agent,
                            to_agent=to_agent,
                            artifacts=artifacts if artifacts else None,
                            notes=notes if notes else None
                        )
                    display_success("Handoff recorded successfully!")
                    # Note: session_context is now fetched fresh from services, no manual update needed
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "decision":
            title = questionary.text(
                "Decision title:",
                validate=lambda x: len(x.strip()) > 0 or "Decision title is required"
            ).ask()
            rationale = questionary.text(
                "Decision rationale:",
                validate=lambda x: len(x.strip()) > 0 or "Decision rationale is required"
            ).ask()
            agent = questionary.text("Agent ID (optional):").ask()

            if title and rationale:
                try:
                    with show_progress("Recording decision..."):
                        self.app.entry_handlers.handle_decision(
                            project=project_name,
                            title=title,
                            rationale=rationale,
                            agent=agent if agent else None
                        )
                    display_success("Decision recorded successfully!")
                    # Note: session_context is now fetched fresh from services, no manual update needed
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "feedback":
            target = questionary.text("Feedback target (agent or artifact):").ask()
            severity = questionary.select("Severity:", choices=["low", "medium", "high"]).ask()
            summary = questionary.text("Feedback summary:").ask()

            if target and summary:
                try:
                    with show_progress("Recording feedback..."):
                        self.app.entry_handlers.handle_feedback(
                            project=project_name,
                            target=target,
                            severity=severity,
                            summary=summary
                        )
                    display_success("Feedback recorded successfully!")
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "blocker":
            title = questionary.text("Blocker title:").ask()
            description = questionary.text("Blocker description:").ask()
            blocked_agents = questionary.text("Blocked agents (comma-separated, optional):").ask()

            if title and description:
                try:
                    with show_progress("Recording blocker..."):
                        self.app.entry_handlers.handle_blocker(
                            project=project_name,
                            title=title,
                            description=description,
                            blocked_agents=blocked_agents.split(',') if blocked_agents else None
                        )
                    display_success("Blocker recorded successfully!")
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "iteration":
            trigger = questionary.text("What triggered this iteration:").ask()
            impacted_agents = questionary.text("Impacted agents (comma-separated):").ask()
            description = questionary.text("Iteration description:").ask()
            version_bump = questionary.select("Version bump:", choices=["patch", "minor", "major"]).ask()

            if trigger and impacted_agents and description:
                try:
                    with show_progress("Recording iteration..."):
                        self.app.entry_handlers.handle_iteration(
                            project=project_name,
                            trigger=trigger,
                            impacted_agents=impacted_agents.split(','),
                            description=description,
                            version_bump=version_bump
                        )
                    display_success("Iteration recorded successfully!")
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "assumption":
            assumption = questionary.text("Assumption:").ask()
            rationale = questionary.text("Rationale:").ask()

            if assumption and rationale:
                try:
                    with show_progress("Recording assumption..."):
                        self.app.entry_handlers.handle_assumption(
                            project=project_name,
                            assumption=assumption,
                            rationale=rationale
                        )
                    display_success("Assumption recorded successfully!")
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "end":
            confirm = questionary.confirm("Are you sure you want to end the workflow?", default=False).ask()
            if confirm:
                try:
                    with show_progress("Ending workflow session..."):
                        self.app.session_handlers.handle_end(project=project_name)
                    display_success("Workflow ended successfully!")
                    # Note: session_context is now fetched fresh from services, no manual update needed
                except Exception as e:
                    self.app.error_view.display_error_modal(str(e))

        elif choice == "cancel":
            return

        questionary.press_any_key_to_continue().ask()