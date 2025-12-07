#!/usr/bin/env python3
"""End a session and archive its state.

Usage:
    python3 -m scripts.session.end_session 
"""
import sys
import re
import datetime
from pathlib import Path

from agentic_workflow.session import session_frontmatter as sf
from agentic_workflow.core.paths import PROJECTS_DIR
from agentic_workflow.core.project import load_project_meta
from agentic_workflow.cli.utils import display_success, display_warning, display_error, display_info


def archive_session_state(project_dir, content):
    """Extracts Layer 3 and appends it to context_log.md."""
    # Find Layer 3 - support both old and new formats
    # New format: 
    # Old format: ## LAYER 3: SESSION STATE (SCRATCHPAD)
    match = re.search(r"\s*(.*)", content, re.DOTALL)
    if not match:
        # Try old format
        match = re.search(r"## LAYER 3: SESSION STATE \(SCRATCHPAD\)\n(.*)", content, re.DOTALL)
    if not match:
        display_warning("No Layer 3 found to archive.")
        return

    layer3_content = match.group(1).strip()
    
    # Find Active Agent Name for the log
    index_path = project_dir / "project_index.md"
    agent_name = "Unknown Agent"
    if index_path.exists():
        agent_match = re.search(r"\*\*Active Agent:\*\* .*\*\* -\*\* (.*)", index_path.read_text())
        agent_name = agent_match.group(1) if agent_match else "Unknown Agent"
    
    log_entry = f"""
---
**Timestamp:** {datetime.datetime.now().isoformat()}
**Agent:** {agent_name}
**Type:** SESSION_ARCHIVE

{layer3_content}
"""
    
    log_path = project_dir / "agent_log" / "context_log.md"
    with open(log_path, "a") as f:
        f.write(log_entry)
    display_success(f"Archived session state to {log_path}")

    # Also append a structured ledger entry for the session archive
    try:
        from agentic_workflow.ledger.log_write import write_log
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ref = f"ARCHIVE-{timestamp}"
        summary = f"Session archived by {agent_name}"
        write_log(project_dir.name, "context_log.md", "SESSION_ARCHIVE", ref, summary, "ARCHIVED", extra={"agent": agent_name})
    except Exception:
        # Non-fatal; keep original md archive even if ledger write fails
        pass


def reset_active_session(project_dir: Path) -> None:
    """Resets active_session.md to Orchestrator state using Jinja2 template."""
    session_path = project_dir / "agent_context" / "active_session.md"

    # Get workflow name from project metadata
    project_meta = load_project_meta(project_dir.name)
    workflow_name = project_meta.get('workflow', 'planning') # Default to 'planning' if not found
    
    # Determine orchestrator agent_id based on workflow
    orch_id = 'I-00' if workflow_name == 'implementation' else 'A-00'
    
    # Build orchestrator session content using the new Jinja2 flow
    orchestrator_content = sf.build_orchestrator_session_from_template(
        workflow=workflow_name,
        project_name=project_dir.name,
        agent_id=orch_id,
        timestamp=datetime.datetime.now().isoformat()
    )

    sf.write_session_file(session_path, orchestrator_content)
    display_success(f"Reset {session_path} to Orchestrator defaults (from Jinja2 template).")


def update_project_index(project_dir):
    """Updates project_index.md to show Orchestrator is active."""
    index_path = project_dir / "project_index.md"
    if not index_path.exists():
        return
        
    with open(index_path, "r") as f:
        content = f.read()
        
    content = re.sub(r"\*\*Active Agent:\*\* .*", "**Active Agent:** Orchestrator", content)
    content = re.sub(r"\*\*Last Action:\*\* .*", "**Last Action:** Session Ended", content)
    
    with open(index_path, "w") as f:
        f.write(content)
    display_success(f"Updated {index_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="End current session and archive")
    parser.add_argument("--project", required=True, help="Project name")
    args = parser.parse_args()
    
    project_name = args.project
    project_dir = PROJECTS_DIR / project_name
    
    if not project_dir.exists():
        display_error(f"Project {project_name} not found.")
        sys.exit(1)
        
    session_path = project_dir / "agent_context" / "active_session.md"
    if not session_path.exists():
        display_error(f"{session_path} not found.")
        sys.exit(1)
        
    with open(session_path, "r") as f:
        content = f.read()
        
    display_info(f"Ending session for {project_name}...")
    
    archive_session_state(project_dir, content)
    reset_active_session(project_dir)
    update_project_index(project_dir)
    
    display_success("Session ended successfully.")


if __name__ == "__main__":
    main()
