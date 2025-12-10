# Agentic Workstation CLI & TUI Reference

**Version:** 1.0.3
**Generated:** December 10, 2025
**Source:** Code Review Analysis

## Overview

The Agentic Workstation provides both command-line (CLI) and text user interface (TUI) access to multi-agent workflow orchestration. The CLI offers scripting and automation capabilities, while the TUI provides interactive, menu-driven workflow management with guided wizards and context-aware operations.

## Global Options

All commands support these global options:

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | ` -c` | Custom configuration file path |
| `--output` | ` -o` | Output format (table, json, yaml, csv) |
| `--api` | `` | Enable API mode for structured output |
| `--web` | `` | Launch web UI interface |
| `--interactive` | ` -i` | Enable interactive mode |
| `--verbose` | ` -v` | Increase verbosity (repeatable) |
| `--log-level` | `` | Set logging level (DEBUG, INFO, WARNING, ERROR) |
| `--auth-token` | `` | Authentication token for multi-user support |
| `--cache` | `` | Enable caching for performance |
| `--retry` | `` | Number of retry attempts for failed operations |
| `--check-updates` | `` | Check for updates on startup |

## Command Groups

### Project Commands

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `project` | None | None | Project |
| `init` | `name` | `--workflow` | Init |
| `list` | `name` | None | List |
| `remove` | `name` | `--force (Force removal without confirmation)` | Remove |

### Workflow Commands

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `workflow` | None | None | Workflow |
| `init` | `project` | `--workflow (Workflow type)`, `--force (Overwrite existing project)` | Init |
| `activate` | `project`, `agent_id` | None | Activate |
| `end` | `project` | None | End |
| `populate` | `project` | None | Populate |
| `delete` | `project` | `--force (Force deletion without confirmation)` | Delete |
| `handoff` | `project` | `--from (Source agent ID)`, `--to (Target agent ID)`, `--artifacts (Comma-separated artifact list)`, `--notes (Handoff notes)` | Handoff |
| `decision` | `project` | `--title (Decision title)`, `--rationale (Decision rationale)`, `--agent (Agent ID)` | Decision |
| `status` | `project` | None | Status |
| `check_handoff` | `project`, `agent_id` | None | Check Handoff |
| `list_pending` | `project` | None | List Pending |
| `list_blockers` | `project` | None | List Blockers |

### TUI Commands

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `tui` | None | `--global-mode (Force global mode)`, `--project-mode (Force project mode)` | Launch Text User Interface for interactive workflow management |

## Usage Examples

### CLI Usage

### Project Management

```bash
# Initialize a new project
agentic project init my_project --workflow planning --description "My new project"

# List all projects
agentic project list

# Show project status
agentic project status

# Remove a project
agentic project remove my_project --force
```

### Workflow Management

```bash
# Initialize workflow in project
agentic workflow init my_project --workflow planning

# Activate an agent
agentic workflow activate my_project A01

# Record handoff between agents
agentic workflow handoff my_project --from A01 --to A02 --artifacts "requirements.md"

# Check workflow status
agentic workflow status my_project

# End workflow
agentic workflow end my_project
```

### TUI Usage

```bash
# Launch interactive Text User Interface (auto-detects context)
agentic tui

# Force global mode (project management)
agentic tui --global-mode

# Force project mode (workflow operations)
agentic tui --project-mode

# From source/development
python3 -m agentic_workflow.cli.main tui
```

### Advanced Usage

```bash
# Use JSON output for scripting
agentic --output json project list

# Enable verbose logging
agentic --verbose workflow status my_project

# Use API mode for automation
agentic --api workflow list
```

## CLI vs TUI

### Command Line Interface (CLI)
- **Best for**: Scripting, automation, CI/CD pipelines
- **Features**: Structured output formats (JSON, YAML, CSV), API mode, scripting integration
- **Usage**: Direct commands with options and arguments
- **Context**: Manual context management

### Text User Interface (TUI)
- **Best for**: Interactive workflow management, learning the system, guided operations
- **Features**: Menu-driven interface, context-aware menus, guided wizards, real-time data display
- **Usage**: Interactive prompts and selections
- **Context**: Automatic detection (global vs project mode)

### When to Use Each

| Use Case | Recommended Interface | Reason |
|----------|----------------------|---------|
| **Scripting/Automation** | CLI | Structured output, API mode |
| **First-time setup** | TUI | Guided wizards, help text |
| **CI/CD pipelines** | CLI | Non-interactive, predictable |
| **Interactive exploration** | TUI | Menus, real-time feedback |
| **Batch operations** | CLI | Command composition, loops |
| **Learning the system** | TUI | Context-aware guidance |

## Error Handling

The CLI provides comprehensive error handling with user-friendly messages:

- **Validation Errors**: Clear messages for invalid inputs
- **File System Errors**: Helpful guidance for permission/path issues
- **Network Errors**: Retry logic with informative messages
- **Configuration Errors**: Suggestions for fixing config issues

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Command not found
- `3`: Validation error
- `4`: File system error

## Configuration

The CLI uses TOML configuration files. Default locations:

1. Project-specific: `./agentic.toml`
2. User-specific: `~/.config/agentic/config.toml`
3. System-wide: `/etc/agentic/config.toml`

Example configuration:

```toml
[core]
workspace_root = "~/projects"
default_workflow = "planning"

[ui]
theme = "dark"
show_progress = true

[logging]
level = "INFO"
file = "~/.agentic/logs/agentic.log"
```

## Troubleshooting

### Common Issues

1. **Command not found**: Ensure `agentic` is in your PATH
2. **Permission denied**: Check file permissions in project directory
3. **Workflow not found**: Verify workflow name and installation
4. **Handler errors**: Check project configuration and artifacts

### Getting Help

```bash
# Show general help
agentic --help

# Show command group help
agentic project --help
agentic workflow --help
agentic tui --help

# Show specific command help
agentic project init --help
agentic workflow status --help
agentic tui --help
```

---

*This documentation covers both CLI and TUI interfaces for the Agentic Workstation. Last updated: December 10, 2025*
