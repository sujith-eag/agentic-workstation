#!/bin/bash
# Project-local workflow wrapper for {{ workflow_display_name }}
# Description: {{ workflow_description | replace('\n', ' ') | replace('"', '\\"') | replace("'", "\\'") }}
#
# DEPRECATED: This wrapper is no longer needed. Use the context-aware `agentic` CLI instead.
#
# Usage (from within project directory):
#   agentic <command> [args...]
#
# Examples:
#   agentic status
#   agentic handoff --to A02 --artifacts "spec.md"
#   agentic decision --title "Use PostgreSQL" --rationale "ACID compliance"
#
# This script is kept for backward compatibility but redirects to the new CLI.

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
    echo "DEPRECATED: This wrapper is deprecated. Use 'agentic --help' instead."
    echo ""
    echo "Available commands (use 'agentic --help' for full list):"
{% set commands = ['status', 'activate', 'end', 'handoff', 'decision', 'assumption', 'feedback', 'blocker', 'iteration', 'list-pending', 'list-blockers'] %}
{% for command in commands %}
    echo "  {{ command }}"
{% endfor %}
    echo ""
    echo "Workflow: {{ workflow_display_name }}"
    echo "Project: $PROJECT_NAME (auto-detected)"
    exit 1
fi

# Redirect to new context-aware CLI
echo "DEPRECATED: ./workflow is deprecated. Use 'agentic' instead."
exec agentic "$@"
