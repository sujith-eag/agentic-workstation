#!/usr/bin/env python3
"""On-demand agent invocation for workflows.

This is the canonical and cleaned implementation for on-demand agent invocation.
It provides `invoke_on_demand()` and related helper functions used by the
CLI and internal scripts.
"""
from __future__ import annotations
import yaml
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from agentic_workflow.workflow.canonical import load_agents_json, load_instructions_json
from agentic_workflow.core.project import load_project_meta
from agentic_workflow.core.paths import WORKFLOWS_DIR, PROJECTS_DIR
from agentic_workflow.cli.utils import display_success, display_error, display_info


def load_workflow_agents(workflow_name: str) -> Optional[Dict]:
    agents_json = load_agents_json(workflow_name)
    if agents_json:
        return agents_json
    agents_file = WORKFLOWS_DIR / workflow_name / "agents.yaml"
    if not agents_file.exists():
        return None
    with open(agents_file, "r") as f:
        return yaml.safe_load(f)


def get_on_demand_agent(workflow_name: str, agent_id: str) -> Optional[Dict]:
    agents = load_workflow_agents(workflow_name)
    if not agents:
        return None
    on_demand = agents.get("on_demand", []) or agents.get("on_demand_agents", [])
    for agent in on_demand:
        if agent.get("id") == agent_id:
            return agent
    return None


def load_workflow_instructions(workflow_name: str) -> Optional[Dict]:
    instr_json = load_instructions_json(workflow_name)
    if instr_json:
        return instr_json
    instr_file = WORKFLOWS_DIR / workflow_name / "instructions.yaml"
    if not instr_file.exists():
        return None
    with open(instr_file, "r") as f:
        return yaml.safe_load(f)


def get_agent_instructions(workflow_name: str, agent_id: str) -> str:
    instr = load_workflow_instructions(workflow_name)
    if not instr:
        return ""
    lean = instr.get("lean", {})
    if isinstance(lean, dict) and agent_id in lean:
        return lean[agent_id]
    per_agent = instr.get("per_agent", []) or instr.get("instructions", [])
    for a in per_agent:
        if isinstance(a, dict) and a.get("id") == agent_id:
            return a.get("instructions", "") or a.get("content", "")
    return ""


def generate_on_demand_session(agent_config: Dict, instructions: str, reason: Optional[str] = None) -> str:
    now = datetime.now().isoformat()
    fm = {
        "agent_id": agent_config.get("id"),
        "agent_role": agent_config.get("role"),
        "mode": "on-demand",
        "invoked_at": now,
        "invocation_reason": reason or "Manual invocation",
        "produces": agent_config.get("produces", []),
    }
    fm_yaml = yaml.safe_dump(fm, sort_keys=False).strip()
    produces = "\n".join(f"- {p}" for p in fm.get("produces", [])) or "- (none)"
    lines = [
        "---",
        fm_yaml,
        "---",
        "",
        f"# On-Demand Agent Session: {agent_config.get('id')}",
        "",
        f"Role: {agent_config.get('role')}",
        f"Focus: {agent_config.get('focus', '')}",
        f"Invoked: {now}",
        f"Reason: {reason or 'Manual invocation'}",
        "",
        "## Agent Instructions",
        "",
        instructions,
        "",
        "## Trigger Conditions",
        "",
        f"{agent_config.get('trigger', 'Manually invoked')}",
        "",
        "## Outputs",
        "",
        "This agent produces:",
        produces,
        "",
        "## Session Notes",
    ]
    return "\n".join(lines)


def log_invocation(project_name: str, agent_id: str, reason: Optional[str] = None) -> None:
    project_dir = PROJECTS_DIR / project_name
    exchange_log = project_dir / "agent_log" / "exchange_log.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n---\n\n"
        f"### INVOKE: {agent_id}\n\n"
        f"- timestamp: {now}\n"
        f"- type: on-demand-invocation\n"
        f"- agent: {agent_id}\n"
        f"- reason: {reason or 'Manual invocation'}\n\n"
    )
    exchange_log.parent.mkdir(parents=True, exist_ok=True)
    with open(exchange_log, "a") as f:
        f.write(entry)


def invoke_on_demand(project_name: str, agent_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    project_dir = PROJECTS_DIR / project_name
    if not project_dir.exists():
        return {"success": False, "error": f"Project '{project_name}' not found"}
    project_wf = load_project_meta(project_name)
    if not project_wf:
        return {"success": False, "error": "Project workflow metadata not found (project_config.json)"}
    workflow_name = project_wf.get("workflow", "planning")
    agent_config = get_on_demand_agent(workflow_name, agent_id)
    if not agent_config:
        return {"success": False, "error": f"On-demand agent '{agent_id}' not found in workflow '{workflow_name}'"}
    instructions = get_agent_instructions(workflow_name, agent_id)
    session_content = generate_on_demand_session(agent_config, instructions, reason)
    session_file = project_dir / "agent_context" / "active_session.md"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    with open(session_file, "w") as f:
        f.write(session_content)
    try:
        log_invocation(project_name, agent_id, reason)
    except Exception:
        pass
    return {"success": True, "session_file": str(session_file), "agent_id": agent_id, "agent_role": agent_config.get("role")}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        display_error("Usage: python invoke_agent.py <project> <agent_id> [reason]")
        sys.exit(1)
    reason = sys.argv[3] if len(sys.argv) > 3 else None
    res = invoke_on_demand(sys.argv[1], sys.argv[2], reason)
    if res.get("success"):
        display_success(f"Invoked: {res['agent_id']} ({res.get('agent_role')})")
        display_info(f"Session: {res['session_file']}")
    else:
        display_error(f"Failed: {res.get('error')}")
        sys.exit(1)
