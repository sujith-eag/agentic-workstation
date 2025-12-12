"""
Ledger service for Agentic Workflow Platform.

This service handles ledger operations like handoffs, decisions, etc.
"""

from typing import Dict, Any, Optional, List
import logging

from ..ledger.entry_reader import get_project_summary, get_active_session, get_handoffs
from ..ledger.entry_writer import write_handoff, write_decision

logger = logging.getLogger(__name__)

__all__ = ["LedgerService"]


class LedgerService:
    """Service for ledger operations."""

    def __init__(self):
        pass

    def record_handoff(self, project_name: str, from_agent: str, to_agent: str,
                      artifacts: Optional[List[str]] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Record an agent handoff."""
        try:
            entry_id, md_path = write_handoff(
                project_name=project_name,
                from_agent=from_agent,
                to_agent=to_agent,
                artifacts=artifacts,
                notes=notes
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record handoff: {e}")
            raise

    def record_decision(self, project_name: str, title: str, rationale: str,
                       agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Record a decision."""
        try:
            entry_id, md_path = write_decision(
                project_name=project_name,
                title=title,
                rationale=rationale,
                agent_id=agent_id
            )
            return {
                'entry_id': entry_id,
                'md_path': md_path,
                'status': 'recorded'
            }
        except Exception as e:
            logger.error(f"Failed to record decision: {e}")
            raise

    def get_status(self, project_name: str) -> Dict[str, Any]:
        """Get project status."""
        try:
            # Get project summary from logs
            summary = get_project_summary(project_name)
            
            # Check for active session
            active_session = get_active_session(project_name)
            active_agents = 1 if active_session else 0
            
            # Get total handoffs (completed ones)
            all_handoffs = get_handoffs(project_name)
            completed_handoffs = len([h for h in all_handoffs if h.get('status') == 'completed'])
            
            # Determine last activity
            last_activity = "No recent activity"
            if active_session:
                last_activity = f"Agent {active_session.get('agent_id', 'Unknown')} active"
            elif all_handoffs:
                last_handoff = all_handoffs[-1]  # Most recent
                last_activity = f"Last handoff: {last_handoff.get('from_agent', '?')} → {last_handoff.get('to_agent', '?')}"
            
            return {
                "active_agents": active_agents,
                "completed_handoffs": completed_handoffs,
                "open_blockers": summary.get('active_blockers', 0),
                "last_activity": last_activity
            }
        except Exception as e:
            logger.error(f"Failed to get status for project '{project_name}': {e}")
            # Return basic status on error
            return {
                "active_agents": 0,
                "completed_handoffs": 0,
                "open_blockers": 0,
                "last_activity": "Status unavailable"
            }