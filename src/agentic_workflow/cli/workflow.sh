#!/bin/bash
# Unified workflow CLI wrapper
#
# Usage:
#   ./scripts/cli/workflow.sh <command> <project> [args...]
#
# Commands:
#   init <project>                    Initialize project structure
#   activate <project> <agent_id>     Activate agent session
#   end <project>                     End session
#   populate <project>                Populate agent frontmatter from manifest
#   handoff <project> [args]          Write handoff entry
#   feedback <project> [args]         Write feedback entry
#   decision <project> [args]         Write decision entry
#   assumption <project> [args]       Write assumption entry
#   blocker <project> [args]          Write blocker entry
#   status <project>                  Show project status
#   check-handoff <project> <id>      Check if handoff exists
#   list-pending <project>            List pending handoffs
#   list-blockers <project>           List active blockers
#
# Examples:
#   ./scripts/cli/workflow.sh init myproject
#   ./scripts/cli/workflow.sh activate myproject A01
#   ./scripts/cli/workflow.sh populate myproject
#   ./scripts/cli/workflow.sh handoff myproject --from A01 --to A02 --artifacts "spec.md"
#   ./scripts/cli/workflow.sh decision myproject --title "Use PostgreSQL" --rationale "ACID"
#   ./scripts/cli/workflow.sh status myproject

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Run the Python CLI with all arguments
python3 -m scripts.cli.workflow "$@"
