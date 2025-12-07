#!/usr/bin/env python3
"""
Workflow package loader.

Discovers and loads workflow packages from manifests/workflows//.
Provides unified access to agents, artifacts, instructions, and metadata.

Usage:
    from agentic_workflow.workflow import load_workflow, list_workflows

    # List available workflows
    workflows = list_workflows()

    # Load a specific workflow
    wf = load_workflow("planning")
    agents = wf.agents
    artifacts = wf.artifacts
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from agentic_workflow.cli.utils import display_info, display_error, display_success

# from agentic_workflow.generation.canonical_loader import (
#     load_canonical_workflow,
#     list_canonical_workflows,
#     CanonicalLoadError
# )


class WorkflowError(Exception):
    """Raised when workflow loading fails."""
    pass


@dataclass
class WorkflowPackage:
    """
    Represents a loaded workflow package.
    
    Attributes:
        name: Workflow identifier (e.g., "planning")
        version: Semantic version string
        path: Absolute path to workflow package directory
        metadata: Full workflow.yaml contents
        agents: List of agent definitions from agents.yaml
        artifacts: List of artifact definitions from artifacts.yaml
        instructions: Dict of per-agent instructions from instructions.yaml
        governance: Governance markdown content (if exists)
    """
    name: str
    version: str
    path: Path
    metadata: Dict[str, Any] = field(default_factory=dict)
    agents: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    instructions: Dict[str, Any] = field(default_factory=dict)
    governance: str = ""

    @property
    def display_name(self) -> str:
        """Human-readable workflow name."""
        return self.metadata.get("display_name", self.name.title())

    @property
    def description(self) -> str:
        """Workflow description."""
        return self.metadata.get("description", "")

    @property
    def pipeline_order(self) -> List[str]:
        """Agent execution order."""
        return self.metadata.get("pipeline", {}).get("order", [])

    @property
    def checkpoints(self) -> List[Dict[str, Any]]:
        """Workflow checkpoints requiring human approval."""
        return self.metadata.get("pipeline", {}).get("checkpoints", [])

    @property
    def globals(self) -> Dict[str, Any]:
        """Global workflow settings."""
        return self.metadata.get("globals", {})

    # =========================================================================
    # DISPLAY CONFIGURATION PROPERTIES
    # These drive template generation and replace hardcoded values
    # =========================================================================

    @property
    def display(self) -> Dict[str, Any]:
        """Display configuration for templates."""
        return self.metadata.get("display", {})

    @property
    def agent_prefix(self) -> str:
        """Agent ID prefix (e.g., 'A' for planning, 'I' for implementation)."""
        # Prefer display.agent_prefix
        prefix = self.display.get("agent_prefix")
        if prefix:
            return prefix

        # Fall back to canonical workflow.json display.agent_prefix if available
        try:
            repo_root = Path(__file__).resolve().parent.parent
            canonical = repo_root / "manifests" / "_canonical" / self.name / "workflow.json"
            if canonical.exists():
                import json
                with open(canonical, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    canonical_prefix = data.get("display", {}).get("agent_prefix")
                    if canonical_prefix:
                        return canonical_prefix
        except Exception:
            pass

        # Fall back to legacy top-level 'prefix', then default 'A'
        return self.metadata.get("prefix", "A")

    @property
    def orch_id(self) -> str:
        """Orchestrator display ID (e.g., 'A00', 'I0')."""
        default = f"{self.agent_prefix}00" if self.id_format == "padded" else f"{self.agent_prefix}0"
        # Normalize using format_agent_id to match stored agent ID style
        return self.format_agent_id(self.display.get("orch_id", default))

    @property
    def id_format(self) -> str:
        """ID format: 'padded' (A01) or 'simple' (I1)."""
        # Prefer display.id_format, fall back to legacy top-level 'agent_id_format', then default
        return self.display.get("id_format", self.metadata.get("agent_id_format", "padded"))

    @property
    def focus(self) -> str:
        """Workflow focus description (e.g., 'planning-only', 'implementation')."""
        return self.display.get("focus", "planning")

    @property
    def base_rules(self) -> List[str]:
        """Base rules for active_session template."""
        return self.display.get("base_rules", [])

    @property
    def protocol(self) -> Dict[str, Any]:
        """Workflow-specific protocol configuration."""
        return self.display.get("protocol", {})

    @property
    def cycle(self) -> Dict[str, Any]:
        """Workflow-specific cycle (e.g., TDD cycle)."""
        return self.display.get("cycle", {})

    @property
    def cli_config(self) -> Dict[str, Any]:
        """CLI configuration for reference generation."""
        return self.metadata.get("cli", {})

    @property
    def extra_commands(self) -> List[Dict[str, Any]]:
        """Workflow-specific CLI commands."""
        return self.cli_config.get("extra_commands", [])

    @property
    def cli_examples(self) -> List[Dict[str, Any]]:
        """CLI example commands for quick reference."""
        return self.cli_config.get("examples", [])

    @property
    def stages(self) -> List[Dict[str, Any]]:
        """Workflow stages (for implementation-style workflows)."""
        return self.metadata.get("stages", [])

    @property
    def on_demand_config(self) -> Dict[str, Any]:
        """On-demand agent configuration."""
        return self.metadata.get("on_demand", {})

    def format_agent_id(self, agent_id) -> str:
        """Format an agent ID according to workflow display rules.
        
        Args:
            agent_id: Raw agent ID (e.g., 1, '1', 'orch', 'I1', 'sec')
            
        Returns:
            Formatted ID string (e.g., 'A01', 'I1', 'A00', 'I-SEC')
        """
        aid = str(agent_id)

        # Detect whether canonical agent IDs in this workflow use a hyphen
        hyphen_preferred = any('-' in str(a.get('id', '')) for a in self.agents)
        sep = '-' if hyphen_preferred else ''
        
        # Handle orchestrator (use explicit orch_id to avoid recursion issues)
        if aid in ('orch', 'orchestrator', '0', '00'):
            # Use display orch_id if present, normalized to preferred separator
            raw_orch = self.display.get('orch_id', f"{self.agent_prefix}00" if self.id_format == 'padded' else f"{self.agent_prefix}0")
            # If raw_orch already contains the prefix, normalize below; fall through
            aid = raw_orch
        
        # Handle on-demand agents (e.g., 'sec' -> 'I-SEC')
        if aid in ('sec', 'doc', 'ds', 'perf'):
            return f"{self.agent_prefix}-{aid.upper()}"
        
        # Already formatted with correct prefix - normalize separator if necessary
        if aid.startswith(self.agent_prefix):
            # If it already contains hyphen and hyphen_preferred is False, remove it
            if '-' in aid and not hyphen_preferred:
                return aid.replace('-', '')
            # If it lacks hyphen but hyphen_preferred is True, insert it after prefix
            if '-' not in aid and hyphen_preferred:
                rest = aid[len(self.agent_prefix):]
                return f"{self.agent_prefix}{sep}{rest}"
            return aid
        
        # Handle X- prefixed on-demand agents (normalize prefix)
        if aid.startswith('I-') or aid.startswith('A-'):
            return f"{self.agent_prefix}-{aid[2:]}"
        
        # Numeric ID - format according to id_format
        try:
            num = int(aid.lstrip('AI'))
            num_str = str(num).zfill(2) if self.id_format == "padded" else str(num)
            return f"{self.agent_prefix}{sep}{num_str}" if sep else f"{self.agent_prefix}{num_str}"
        except ValueError:
            # Unknown format, return with prefix
            # If we can't parse, attach prefix and preferred separator
            return f"{self.agent_prefix}{sep}{aid}" if sep else f"{self.agent_prefix}{aid}"

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent definition by ID (e.g., 'A1' or 'orch')."""
        # Normalize requested id according to workflow formatting rules
        try:
            formatted = self.format_agent_id(agent_id)
        except Exception:
            formatted = str(agent_id)

        for agent in self.agents:
            # Normalize stored id for resilient comparison
            stored = str(agent.get("id", "")).upper()
            if stored == str(formatted).upper():
                return agent
        return None

    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get artifact definition by ID."""
        for artifact in self.artifacts:
            if artifact.get("id") == artifact_id:
                return artifact
        return None

    def get_agent_instructions(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get instructions for a specific agent."""
        agents_instructions = self.instructions.get("agents", [])
        for agent_instr in agents_instructions:
            if agent_instr.get("agent") == agent_id:
                return agent_instr
        return None


def _get_workflows_dir() -> Path:
    """Get the manifests/workflows directory path."""
    # Try to find repo root by looking for manifests/ directory
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        workflows_path = parent / "manifests" / "workflows"
        if workflows_path.is_dir():
            return workflows_path
    
    # Fallback: assume standard repo structure
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "manifests" / "workflows"


def _load_text(file_path: Path) -> str:
    """Load text file, returning empty string if not found."""
    if not file_path.exists():
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def list_workflows() -> List[Dict[str, str]]:
    """
    List available workflow packages from canonical JSON.
    
    Returns:
        List of dicts with 'name', 'version', 'path', 'description' keys.
    
    Example:
        >>> workflows = list_workflows()
        >>> for wf in workflows:
        ...     print(f"{wf['name']} v{wf['version']}")
    """
    workflows_dir = _get_workflows_dir()
    result = []
    
    from agentic_workflow.generation.canonical_loader import list_canonical_workflows, load_canonical_workflow

    # Get workflows from canonical directory
    for wf_name in list_canonical_workflows():
        manifests = load_canonical_workflow(wf_name)
        workflow_data = manifests.get("workflow", {})
        if workflow_data:
            wf_path = workflows_dir / wf_name
            result.append({
                "name": wf_name,
                "version": workflow_data.get("version", "0.0.0"),
                "path": str(wf_path),
                "description": workflow_data.get("description", ""),
                "enabled": True,
                "status": "stable",
            })
    
    return result


def get_default_workflow() -> str:
    """
    Get the default workflow name.
    
    Returns:
        Workflow name string (e.g., "planning").
    """
    # Default to 'planning' - could be made configurable via global config
    return "planning"


def load_workflow(name: str) -> WorkflowPackage:
    """
    Load a complete workflow package from canonical JSON.
    
    Args:
        name: Workflow identifier (e.g., "planning").
    
    Returns:
        WorkflowPackage with all loaded data.
    
    Raises:
        WorkflowError: If workflow not found or invalid.
    
    Example:
        >>> wf = load_workflow("planning")
        >>> print(f"Loaded {wf.name} v{wf.version} with {len(wf.agents)} agents")
    """
    workflows_dir = _get_workflows_dir()
    wf_path = workflows_dir / name
    
    # Load all canonical data (supports JSON/YAML)
    from agentic_workflow.generation.canonical_loader import (
        load_canonical_workflow,
        get_agents_list, 
        get_artifacts_list, 
        get_instructions_list,
        CanonicalLoadError
    )

    try:
        manifests = load_canonical_workflow(name)
    except CanonicalLoadError as e:
        raise WorkflowError(f"Failed to load workflow '{name}': {e}")
    
    workflow_data = manifests.get("workflow", {})
    
    agents = get_agents_list(manifests)
    artifacts = get_artifacts_list(manifests)
    instructions = get_instructions_list(manifests)
    
    # Load governance from workflow metadata (no longer from separate file)
    governance = workflow_data.get("governance", {})
    if isinstance(governance, dict):
        # Convert governance dict to string representation for backward compatibility
        import json
        governance = json.dumps(governance, indent=2)
    
    return WorkflowPackage(
        name=workflow_data.get("name", name),
        version=workflow_data.get("version", "0.0.0"),
        path=wf_path,
        metadata=workflow_data,
        agents=agents,
        artifacts=artifacts,
        instructions=instructions,
        governance=governance,
    )


def get_workflow_agents(name: str) -> List[Dict[str, Any]]:
    """
    Get agent definitions for a workflow.
    
    Shortcut for load_workflow(name).agents.
    
    Args:
        name: Workflow identifier.
    
    Returns:
        List of agent definition dicts.
    """
    return load_workflow(name).agents


def get_workflow_artifacts(name: str) -> List[Dict[str, Any]]:
    """
    Get artifact definitions for a workflow.
    
    Shortcut for load_workflow(name).artifacts.
    
    Args:
        name: Workflow identifier.
    
    Returns:
        List of artifact definition dicts.
    """
    return load_workflow(name).artifacts


def get_workflow_instructions(name: str) -> Dict[str, Any]:
    """
    Get instructions for a workflow.
    
    Shortcut for load_workflow(name).instructions.
    
    Args:
        name: Workflow identifier.
    
    Returns:
        Instructions dict with 'agents' key.
    """
    return load_workflow(name).instructions


# --- CLI interface for testing ---

def main():
    """CLI for testing workflow loader."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Workflow package loader")
    parser.add_argument("command", choices=["list", "load", "agents", "artifacts"])
    parser.add_argument("--workflow", "-w", default=None, help="Workflow name")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        if args.command == "list":
            workflows = list_workflows()
            if args.json:
                display_info(json.dumps(workflows, indent=2))
            else:
                display_info("Available workflows:")
                for wf in workflows:
                    status = "✓" if wf["enabled"] else "○"
                    display_info(f"  {status} {wf['name']} v{wf['version']} - {wf['description']}")
                display_info(f"\nDefault: {get_default_workflow()}")

        elif args.command == "load":
            wf_name = args.workflow or get_default_workflow()
            wf = load_workflow(wf_name)
            if args.json:
                display_info(json.dumps({
                    "name": wf.name,
                    "version": wf.version,
                    "path": str(wf.path),
                    "agents_count": len(wf.agents),
                    "artifacts_count": len(wf.artifacts),
                    "pipeline_order": wf.pipeline_order,
                }, indent=2))
            else:
                display_info(f"Workflow: {wf.display_name} v{wf.version}")
                display_info(f"Path: {wf.path}")
                display_info(f"Agents: {len(wf.agents)}")
                display_info(f"Artifacts: {len(wf.artifacts)}")
                pipeline_str = ' → '.join(str(x) for x in wf.pipeline_order)
                display_info(f"Pipeline: {pipeline_str}")

        elif args.command == "agents":
            wf_name = args.workflow or get_default_workflow()
            agents = get_workflow_agents(wf_name)
            if args.json:
                display_info(json.dumps(agents, indent=2))
            else:
                display_info(f"Agents in '{wf_name}' workflow:")
                for agent in agents:
                    display_info(f"  {agent['id']}: {agent['role']}")

        elif args.command == "artifacts":
            wf_name = args.workflow or get_default_workflow()
            artifacts = get_workflow_artifacts(wf_name)
            if args.json:
                display_info(json.dumps(artifacts, indent=2))
            else:
                display_info(f"Artifacts in '{wf_name}' workflow ({len(artifacts)} total):")
                for artifact in artifacts[:10]:  # Show first 10
                    display_info(f"  {artifact['id']}: {artifact.get('name', 'unnamed')}")
                if len(artifacts) > 10:
                    display_info(f"  ... and {len(artifacts) - 10} more")

    except WorkflowError as e:
        display_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
