#!/usr/bin/env python3
"""Update project_index.yaml with new artifact entries.

Appends or updates artifact metadata in the project index file.

Usage:
    python3 -m scripts.generation.update_index --project  --artifact  [--type ] [--status ]
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    display_error("pyyaml required")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent

from agentic_workflow.cli.utils import display_error, display_success


def load_index(index_path):
    """Load project_index.yaml or return empty structure."""
    if index_path.exists():
        try:
            data = yaml.safe_load(index_path.read_text()) or {}
        except yaml.YAMLError:
            data = {}
    else:
        data = {}
    
    if 'artifacts' not in data:
        data['artifacts'] = []
    if 'metadata' not in data:
        data['metadata'] = {}
    
    return data


def save_index(index_path, data):
    """Save project_index.yaml."""
    index_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


def update_artifact(data, artifact_path, artifact_type, status):
    """Add or update an artifact entry in the index."""
    artifacts = data.get('artifacts', [])
    
    # Normalize path
    artifact_rel = str(artifact_path)
    
    # Find existing entry
    existing = None
    for i, entry in enumerate(artifacts):
        if entry.get('path') == artifact_rel:
            existing = i
            break
    
    new_entry = {
        'path': artifact_rel,
        'type': artifact_type,
        'status': status,
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    
    if existing is not None:
        # Preserve fields that shouldn't be overwritten
        old = artifacts[existing]
        for key in ('created', 'owner', 'notes'):
            if key in old:
                new_entry[key] = old[key]
        artifacts[existing] = new_entry
        action = 'Updated'
    else:
        new_entry['created'] = new_entry['updated']
        artifacts.append(new_entry)
        action = 'Added'
    
    data['artifacts'] = artifacts
    data['metadata']['last_modified'] = datetime.now().isoformat()
    
    return action


def main():
    parser = argparse.ArgumentParser(description="Update project index with artifact")
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--artifact', required=True, help='Artifact path (relative to project)')
    parser.add_argument('--type', default='artifact', help='Artifact type')
    parser.add_argument('--status', default='active', help='Artifact status')
    args = parser.parse_args()
    
    project_dir = ROOT / 'projects' / args.project
    if not project_dir.exists():
        display_error(f"Project not found: {project_dir}")
        sys.exit(1)
    
    index_path = project_dir / 'project_index.yaml'
    data = load_index(index_path)
    
    action = update_artifact(data, args.artifact, args.type, args.status)
    save_index(index_path, data)
    
    display_success(f"{action}: {args.artifact} in {index_path}")


if __name__ == '__main__':
    main()
