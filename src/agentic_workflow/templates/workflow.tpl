#!/bin/bash
# Project-local workflow wrapper for {{ workflow_display_name }}
# Description: {{ workflow_description | replace('\n', ' ') | replace('"', '\\"') | replace("'", "\\'") }}
# Auto-resolves repo root and forwards commands to the main CLI.
#
# Usage (from within project directory):
#   ./workflow <command> [args...]
#
# Examples:
#   ./workflow status
#   ./workflow handoff --from A01 --to A02 --artifacts "spec.md"
#   ./workflow decision --title "Use PostgreSQL" --rationale "ACID compliance"
#
# This wrapper automatically injects the project name, so you don't need to specify it.

set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="$(basename "$SCRIPT_DIR")"

# Find repo root by walking up until we find src/agentic_workflow/cli/main.py
find_repo_root() {
    local dir="$SCRIPT_DIR"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/src/agentic_workflow/cli/main.py" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "Error: Could not find repo root (src/agentic_workflow/cli/main.py not found)" >&2
    exit 1
}

REPO_ROOT="$(find_repo_root)"

# Check for command
if [[ $# -lt 1 ]]; then
    echo "Usage: ./workflow <command> [args...]"
    echo ""
    echo "Available commands:"
{% set commands = ['init', 'activate', 'end', 'populate', 'delete', 'handoff', 'decision', 'status', 'check-handoff', 'list-pending', 'list-blockers', 'list-workflows'] %}
{% for command in commands %}
    echo "  {{ command }}"
{% endfor %}
    echo ""
    echo "Workflow: {{ workflow_display_name }}"
    echo "Project: $PROJECT_NAME (auto-detected)"
    exit 1
fi

COMMAND="$1"
shift

# Commands that don't need project name injected
case "$COMMAND" in
    help|--help|-h)
        PYTHONPATH="$REPO_ROOT/src" exec python3 -m agentic_workflow.cli.main workflow --help
        ;;
esac

# Forward to main CLI with project name auto-injected
PYTHONPATH="$REPO_ROOT/src" exec python3 -m agentic_workflow.cli.main workflow "$COMMAND" "$PROJECT_NAME" "$@"
