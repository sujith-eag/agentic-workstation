#!/usr/bin/env python3
"""Canonical JSON loader for workflow manifests.

This module provides small helpers to read canonical JSON files from
`manifests/_canonical//` so runtime scripts can use the
source-of-truth JSON files instead of the generated YAML files.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_ROOT = SCRIPT_DIR.parent
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from agentic_workflow.core.paths import get_manifests_dir


def _load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    if not file_path.exists():
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_workflow_json(workflow: str) -> Dict[str, Any]:
    return _load_json(get_manifests_dir() / workflow / 'workflow.json') or {}


def load_agents_json(workflow: str) -> Dict[str, Any]:
    return _load_json(get_manifests_dir() / workflow / 'agents.json') or {}


def load_artifacts_json(workflow: str) -> Dict[str, Any]:
    return _load_json(get_manifests_dir() / workflow / 'artifacts.json') or {}


def load_instructions_json(workflow: str) -> Dict[str, Any]:
    return _load_json(get_manifests_dir() / workflow / 'instructions.json') or {}


def list_canonical_workflows() -> list[str]:
    manifests_dir = get_manifests_dir()
    if not manifests_dir.exists():
        return []
    return [d.name for d in manifests_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]
