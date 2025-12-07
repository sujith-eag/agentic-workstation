#!/usr/bin/env python3
"""Canonical JSON loader for workflow manifests.

Loads and validates canonical JSON files from manifests/_canonical/.
Provides unified access to workflow data with schema validation.

Usage:
    from agentic_workflow.generation.canonical_loader import load_canonical_workflow
    
    data = load_canonical_workflow("planning")
    agents = data["agents"]
    artifacts = data["artifacts"]
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from importlib import resources

from ..core.exceptions import CLIExecutionError
from agentic_workflow.cli.utils import display_info, display_error

# Custom exception for our loader
class CanonicalLoadError(Exception):
    """Raised when canonical loading fails."""
    pass

def get_canonical_dir() -> Path:
    """Get the canonical manifests directory via resources."""
    try:
        # Use importlib.resources logic
        # Assuming the package structure: agentic_workflow.manifests._canonical
        # Note: Users might need to ensure __init__.py exists in manifests/_canonical if it's a subpackage
        # But simpler is to access 'manifests' resource and joinpath.
        return resources.files("agentic_workflow.manifests").joinpath("_canonical")
    except Exception:
        # Fallback for dev mode if package not fully installed
        return Path(__file__).resolve().parent.parent.parent / "manifests" / "_canonical"

def get_schema_dir() -> Path:
    """Get the JSON schemas directory via resources."""
    try:
        return resources.files("agentic_workflow.manifests").joinpath("_canonical_schemas")
    except Exception:
        return Path(__file__).resolve().parent.parent.parent / "manifests" / "_canonical_schemas"

def list_canonical_workflows() -> List[str]:
    """List available workflows from all search paths.
    
    Returns:
        List of workflow names (unique).
    """
    from ..core.paths import get_workflow_search_paths
    
    workflows = set()
    for search_path in get_workflow_search_paths():
        if not search_path.exists():
            continue
            
        for d in search_path.iterdir():
            if d.is_dir() and not d.name.startswith("_") and not d.name.startswith("."):
                workflows.add(d.name)
                
    return sorted(list(workflows))

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file."""
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise CanonicalLoadError(f"Invalid JSON in {file_path}: {e}")

def load_canonical_file(workflow: str, filename: str) -> Optional[Dict[str, Any]]:
    """Load a specific canonical JSON file from search paths."""
    from ..core.paths import get_workflow_search_paths
    
    for search_path in get_workflow_search_paths():
        # Check standard path structure: <search_path>/<workflow>/<filename>
        file_path = search_path / workflow / filename
        if file_path.exists():
            return load_json_file(file_path)
    
    return None

import yaml

def load_manifest_file(workflow: str, filename_base: str) -> Optional[Dict[str, Any]]:
    """Load a canonical file with json/yaml auto-detection."""
    canonical_dir = get_canonical_dir()
    base_path = canonical_dir / workflow / filename_base
    
    extensions = [".json", ".yaml", ".yml"]
    
    for ext in extensions:
        file_path = base_path.with_suffix(ext)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    if ext == ".json":
                        return json.load(f)
                    else:
                        return yaml.safe_load(f)
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                raise CanonicalLoadError(f"Invalid format in {file_path}: {e}")
                
    return None

def load_canonical_workflow(workflow: str) -> Dict[str, Any]:
    """Load all canonical files for a workflow (JSON or YAML)."""
    # Check simple existence first (optional optimization omitted for simplicity)
    
    # Load required files
    manifests = {
        "workflow": load_manifest_file(workflow, "workflow"),
        "agents": load_manifest_file(workflow, "agents"),
        "artifacts": load_manifest_file(workflow, "artifacts"),
        "instructions": load_manifest_file(workflow, "instructions"),
    }
    
    # Validate required
    required = ["workflow", "agents", "artifacts"]
    for key in required:
        if manifests[key] is None:
            raise CanonicalLoadError(f"Missing required manifest: {workflow}/{key}[.json|.yaml]")
            
    # Default optional
    if manifests["instructions"] is None:
        manifests["instructions"] = {"instructions": []}
        
    return manifests


def get_agents_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract agents list from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        List of agent definitions.
    """
    agents_data = data.get("agents", {})
    return agents_data.get("agents", [])


def get_artifacts_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract artifacts list from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        List of artifact definitions.
    """
    artifacts_data = data.get("artifacts", {})
    return artifacts_data.get("artifacts", [])


def get_instructions_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract instructions list from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        List of instruction definitions.
    """
    instructions_data = data.get("instructions", {})
    return instructions_data.get("instructions", [])


def get_workflow_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract workflow metadata from canonical data.
    
    Args:
        data: Loaded canonical workflow data.
        
    Returns:
        Workflow configuration dict.
    """
    return data.get("workflow", {})


def build_agent_lookup(agents: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dict from agent ID to agent definition.
    
    Args:
        agents: List of agent definitions.
        
    Returns:
        Dict mapping agent ID to agent dict.
    """
    return {agent["id"]: agent for agent in agents if "id" in agent}


def build_artifact_lookup(artifacts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dict from filename to artifact definition.
    
    Args:
        artifacts: List of artifact definitions.
        
    Returns:
        Dict mapping filename to artifact dict.
    """
    return {art["filename"]: art for art in artifacts if "filename" in art}


def build_instruction_lookup(instructions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a lookup dict from agent ID to instruction definition.
    
    Args:
        instructions: List of instruction definitions.
        
    Returns:
        Dict mapping agent ID to instruction dict.
    """
    return {instr["id"]: instr for instr in instructions if "id" in instr}


def extract_files_from_produces_consumes(items: Any) -> List[str]:
    """Extract file names from produces/consumes structure.
    
    Handles both formats:
    - Simple list: ["file1.md", "file2.md"]
    - Categorized dict: {"core": ["file1.md"], "log": ["file2.md"]}
    - Items can be strings or dicts with "filename" (canonical) or "file" (legacy) keys
    
    Args:
        items: Produces or consumes data.
        
    Returns:
        Flat list of filenames.
    """
    files = []
    
    # Note: canonical schema uses the key `filename` for artifact entries.
    # This function prefers `filename` (canonical) and falls back to
    # legacy `file` for backward compatibility.
    if isinstance(items, dict):
        # Categorized format
        for category_items in items.values():
            if isinstance(category_items, list):
                for item in category_items:
                    if isinstance(item, dict):
                        # Prefer 'filename' (canonical schema) then 'file' (legacy)
                        files.append(item.get("filename") or item.get("file", ""))
                    elif isinstance(item, str):
                        files.append(item)
    elif isinstance(items, list):
        # Simple list format
        for item in items:
            if isinstance(item, dict):
                files.append(item.get("filename") or item.get("file", ""))
            elif isinstance(item, str):
                files.append(item)
    
    return [f for f in files if f]  # Filter empty strings


# --- CLI for testing ---

def main():
    """CLI for testing canonical loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Canonical JSON loader")
    parser.add_argument("command", choices=["list", "load", "agents", "artifacts"])
    parser.add_argument("--workflow", "-w", default="planning", help="Workflow name")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    try:
        if args.command == "list":
            workflows = list_canonical_workflows()
            display_info("Available canonical workflows:")
            for wf in workflows:
                display_info(f"  - {wf}")
        
        elif args.command == "load":
            data = load_canonical_workflow(args.workflow)
            display_info(f"Loaded {args.workflow}:")
            display_info(f"  Agents: {len(get_agents_list(data))}")
            display_info(f"  Artifacts: {len(get_artifacts_list(data))}")
            display_info(f"  Instructions: {len(get_instructions_list(data))}")
        
        elif args.command == "agents":
            data = load_canonical_workflow(args.workflow)
            agents = get_agents_list(data)
            if args.json:
                display_info(json.dumps(agents, indent=2))
            else:
                display_info(f"Agents in {args.workflow}:")
                for agent in agents:
                    display_info(f"  {agent['id']}: {agent.get('role', agent.get('slug', 'unknown'))}")
        
        elif args.command == "artifacts":
            data = load_canonical_workflow(args.workflow)
            artifacts = get_artifacts_list(data)
            if args.json:
                display_info(json.dumps(artifacts, indent=2))
            else:
                display_info(f"Artifacts in {args.workflow} ({len(artifacts)} total):")
                for art in artifacts[:10]:
                    display_info(f"  {art['filename']}: {art.get('description', '')[:50]}")
                if len(artifacts) > 10:
                    display_info(f"  ... and {len(artifacts) - 10} more")
    
    except CanonicalLoadError as e:
        display_error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
