# Agentic Workflow CLI Usage Guide

**Version:** 1.0.0
**Date:** December 6, 2025
**Status:** Phase 2 Week 1 Complete - Core CLI Foundation

## Overview

The Agentic Workflow CLI is a modern, comprehensive command-line interface for managing complex software projects through orchestrated multi-agent workflows. It provides professional-grade tooling with rich output, structured logging, and extensible architecture.

## Installation

```bash
# Install from source (development)
pip install -e .

# Or install specific optional features
pip install -e ".[web,auth,performance]"
```

## Global Options

All commands support these global options:

```bash
agentic --help                    # Show help
agentic --version                 # Show version

# Output formatting
agentic --output table project list    # Table format (default)
agentic --output json project list     # JSON format
agentic --output yaml project list     # YAML format

# Logging and verbosity
agentic --verbose project list         # Enable verbose logging
agentic --log-level DEBUG project list # Set log level

# Configuration
agentic --config ~/.myconfig.toml     # Custom config file

# Advanced features (Phase 2+)
agentic --web                        # Launch web UI
agentic --api                        # API mode
agentic --interactive                # Interactive mode
agentic --auth-token TOKEN           # Authentication
agentic --cache                      # Enable caching
agentic --retry 3                    # Retry count
```

## Project Management

### Creating Projects

```bash
# Create a new project with planning workflow
agentic project init my_project --workflow planning --description "My software project"

# Create with custom workflow
agentic project init research_proj --workflow research --description "Research project"

# Available workflows: planning, research, implementation, workflow-creation
```

**What gets created:**
- `projects/my_project/` directory
- Standard folder structure: `agent_files/`, `agent_context/`, `agent_log/`, `artifacts/`, `docs/`, `input/`, `package/`
- `agentic.toml` configuration file
- `workflow` executable script for project-specific commands

### Listing Projects

```bash
# List all projects
agentic project list

# Show in different formats
agentic --output json project list
agentic --output yaml project list

# Show specific project details
agentic project list my_project
```

### Project Status

```bash
# From anywhere: shows warning if not in project
agentic project status

# From within project directory: shows full status
cd projects/my_project
agentic project status
```

### Removing Projects

```bash
# Remove with confirmation prompt
agentic project remove my_project

# Force remove without confirmation
agentic project remove my_project --force
```

## Workflow Management

### Listing Workflows

```bash
# List all available workflows
agentic workflow list

# Workflows include:
# - planning: Comprehensive software project planning (15 agents)
# - research: Evidence-based academic research pipeline
# - implementation: Test-driven development workflow (6 agents)
# - workflow-creation: Guided workflow package creation
```

### Workflow Operations

```bash
# Initialize workflow in current project
cd projects/my_project
agentic workflow init planning

# Check workflow status
agentic workflow status

# Activate specific agent (when workflow is running)
agentic workflow activate A01

# Record handoffs between agents
agentic workflow handoff --from A01 --to A02 --artifacts "requirements.md,design.pdf" --message "Requirements analysis complete"

# Record workflow decisions
agentic workflow decision "Use microservices architecture" --rationale "Scalability requirements" --options "monolith,microservices" --outcome "Approved"

# End workflow
agentic workflow end
```

## Project-Specific Usage

Each project includes a `workflow` script for convenient access:

```bash
cd projects/my_project

# Use local workflow script (recommended)
./workflow status
./workflow workflow list
./workflow project list

# Or use global CLI with project context
agentic --project-dir . workflow status
```

## Configuration

### Configuration Hierarchy

1. **Command-line options** (highest priority)
2. **User config:** `~/.agentic.toml`
3. **Project config:** `projects/my_project/agentic.toml`
4. **Defaults** (lowest priority)

### Configuration File Format

```toml
# ~/.agentic.toml or agentic.toml
default_workflow = "planning"
projects_dir = "./projects"
theme = "dark"
verbose = false
log_level = "INFO"
cache_enabled = false
retry_count = 0
api_port = 8000
web_host = "127.0.0.1"
web_port = 8000
update_check_interval = 86400
```

## Output Formats

### Table Format (Default)
Rich-formatted tables with colors and styling:
```
                     Available Projects
┏━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ name         ┃ workflow ┃ description                     ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ my_project   │ planning │ My software project             │
└──────────────┴──────────┴─────────────────────────────────┘
```

### JSON Format
Machine-readable structured output:
```json
[
  {
    "name": "my_project",
    "workflow": "planning",
    "description": "My software project"
  }
]
```

### YAML Format
Human-readable structured output:
```yaml
- name: my_project
  workflow: planning
  description: My software project
```

## Logging

### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages

### Structured Logging
Uses structlog for machine-readable logs with context:
```bash
agentic --verbose --log-level DEBUG project list
```

## Error Handling

The CLI provides clear error messages and appropriate exit codes:

```bash
# Project not found
agentic project list nonexistent
# Error: Project 'nonexistent' not found

# Workflow not found
agentic project init myproj --workflow nonexistent
# Error: Workflow type 'nonexistent' not found

# Not in project directory
agentic workflow status
# ⚠ Project configuration not found
```

## Examples

### Complete Project Lifecycle

```bash
# 1. Create project
agentic project init my_app --workflow planning --description "Web application project"

# 2. Navigate to project
cd projects/my_app

# 3. Check status
./workflow status

# 4. Initialize workflow
./workflow workflow init planning

# 5. Check available workflows
./workflow workflow list

# 6. Monitor progress (in different formats)
./workflow --output json project list
./workflow --output yaml workflow status

# 7. Clean up when done
cd ../..
agentic project remove my_app --force
```

### Research Project Setup

```bash
# Create research project
agentic project init research2025 --workflow research --description "2025 Research Initiative"

cd projects/research2025

# Initialize research workflow
./workflow workflow init research

# The research workflow includes specialized agents for:
# - Literature review (R-00)
# - Methodology design (R-01)
# - Data collection (R-02)
# - Analysis (R-03)
# - Publication prep (R-04)
# - Peer review (R-05)
# - Final submission (R-06)
# - On-demand: LaTeX (R-TEX), Visualization (R-VIZ), Editing (R-EDIT), Statistics (R-STAT)
```

## Troubleshooting

### Common Issues

**"Workflow type not found"**
- Check available workflows: `agentic workflow list`
- Ensure correct spelling and case

**"Project configuration not found"**
- Run from project directory or use `--project-dir` option
- Check that `agentic.toml` exists in project root

**Import errors**
- Ensure proper Python path: `PYTHONPATH=/path/to/src`
- Check virtual environment activation

### Getting Help

```bash
# General help
agentic --help

# Command-specific help
agentic project --help
agentic workflow --help
agentic project init --help

# Verbose output for debugging
agentic --verbose --log-level DEBUG <command>
```

## Architecture Notes

### Phase 2 Status
- ✅ **Week 1 Complete:** Core CLI foundation with Click framework
- 🔄 **Week 2 Planned:** Interactive mode, auto-completion, web UI foundations
- 🔄 **Future:** Full web interface, advanced authentication, performance optimizations

### Key Features Implemented
- Modern Click-based command structure
- Rich console output with tables and colors
- Hierarchical configuration system
- Structured logging with structlog
- Multi-format output (table/json/yaml)
- Comprehensive error handling
- Extensible plugin architecture

### File Structure
```
projects/
└── my_project/
    ├── agentic.toml      # Project configuration
    ├── workflow          # Local CLI wrapper script
    ├── agent_files/      # Generated agent prompts
    ├── agent_context/    # Runtime context
    ├── agent_log/        # Handoffs and decisions
    ├── artifacts/        # Agent outputs
    ├── docs/             # Documentation
    ├── input/            # User requirements
    └── package/          # Final deliverables
```

## Next Steps

After Phase 2 completion, the CLI will support:
- Interactive mode with guided workflows
- Web-based interface for complex operations
- Auto-completion and command suggestions
- Multi-user authentication and isolation
- Performance caching and optimization
- Real-time progress monitoring

---

**Validation Status:** ✅ All core functionalities tested and working
- Project creation/deletion ✅
- Workflow listing ✅
- Multi-format output ✅
- Configuration system ✅
- Error handling ✅
- File/folder generation ✅