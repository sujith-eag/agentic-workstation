# Agentic Workflow OS: CLI Architecture Reference

**Version:** 3.0 (Current Implementation)
**Last Updated:** 31 December 2025
**Scope:** Command Line Interface Architecture and Implementation

## 1. Architectural Overview

The CLI implements a **context-aware routing system** that dynamically exposes different command sets based on execution location (global vs project context). It follows a strict **layered architecture** with clear separation of concerns between interface, orchestration, and business logic.

### Core Architecture

```
┌─────────────┐
│   main.py   │  Entry Point & Context Router
└──────┬──────┘
       │
       ├─────────────────┬─────────────────┐
       │                 │                 │
┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│ global_ops  │  │ project_ops │  │active_session│  Command Modules
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       └─────────┬───────┴─────────┬───────┘
                 │                 │
         ┌───────▼─────────────────▼────────┐
         │         Handler Layer            │
         │  ┌────────────────────────────┐  │
         │  │ SessionHandlers            │  │  Lifecycle Management
         │  │ EntryHandlers              │  │  Ledger Writes
         │  │ QueryHandlers              │  │  Read Operations
         │  │ ProjectHandlers            │  │  Project CRUD
         │  │ GlobalHandlers             │  │  System Config
         │  │ WorkflowHandlers           │  │  Workflow Operations
         │  │ ArtifactHandlers           │  │  Artifact Operations
         │  └────────────┬───────────────┘  │
         └───────────────┼──────────────────┘
                         │
         ┌───────────────▼──────────────────┐
         │      Service Layer               │
         │  ProjectService | LedgerService  │
         │  WorkflowService                 │
         └──────────────────────────────────┘
```

### Architectural Principles

1. **Context-Aware Routing**: Commands dynamically shown/hidden based on directory location
2. **Handler-Based Orchestration**: All commands delegate to handler classes for business logic
3. **Zero Logic in Commands**: Click command functions only parse arguments and call handlers
4. **Unified Theming**: Consistent visual presentation via centralized Theme system
5. **TUI Integration**: Commands share handlers with TUI for consistent behavior

-----

## 2. Context-Aware Routing (`main.py`)

The `ContextAwareGroup` class extends Rich Click's `RichGroup` to provide dynamic command discovery based on execution context.

### Context Detection

| Context | Detection Logic | Available Commands |
|---------|----------------|-------------------|
| **Global** | No `.agentic` directory in current path | System initialization, project management, configuration |
| **Project** | `.agentic` directory present in current or parent directory | Workflow operations, session management, ledger entries |

### Command Routing Implementation

**Dynamic Command List** (`list_commands`):
- Inspects `config.is_project_context` to determine context
- Returns filtered command list appropriate for current location
- Project context: `status`, `activate`, `handoff`, `decision`, `end`, `feedback`, `blocker`, `iteration`, `assumption`, `list-pending`, `list-blockers`
- Global context: `init`, `list`, `delete`, `config`, `workflows`

**Command Resolution** (`get_command`):
- Maps command names to actual Click command functions
- Maintains separate mappings for project and global contexts
- Supports command aliasing (e.g., `end` → `end_session`, `list` → `list_projects`)

### Theme Integration

Rich Click configuration applies application theme colors to help output:
```
Theme.get_color_map() → RichHelpConfiguration
- style_option: help.command.color
- style_command: help.command.color  
- style_metavar: help.description.color
```

### TUI Fallback

When invoked without subcommands, CLI launches the interactive TUI (`TUIApp`) for guided navigation.

-----

## 3. Command Modules

Command modules define the Click interface layer. They are organized by functional domain and contain zero business logic.

### Module Organization

| Module | Context | Purpose | Commands |
|--------|---------|---------|----------|
| `global_ops.py` | Global | System setup and configuration | `init`, `workflows`, `config` |
| `project_ops.py` | Both | Project management and queries | `list`, `delete`, `status`, `list-pending`, `list-blockers` |
| `active_session.py` | Project | Workflow session operations | `activate`, `handoff`, `decision`, `end`, `feedback`, `blocker`, `iteration`, `assumption`, `check-handoff` |

### Command Patterns

All command functions follow consistent patterns:

1. **Argument Parsing**: Use Click decorators for options and arguments
2. **Rich Help Formatting**: All commands use `cls=RichCommand` for consistent help styling
3. **Context Extraction**: Retrieve `config` from Click context when needed
4. **Handler Delegation**: Pass parsed arguments directly to handler methods
5. **Error Handling**: Catch exceptions and display via `display_error()`
6. **Standardized Help**: Google-style docstrings with extended descriptions and examples

### Global Operations

**`init`** - Initialize new project
- Arguments: `project` (name), `--workflow`, `--description`, `--force`
- Handler: `SessionHandlers.handle_init()`
- Creates project structure and initializes workflow

**`workflows`** - List available workflows
- Handler: `GlobalHandlers.handle_list_workflows()`
- Displays workflow templates with metadata

**`config`** - View/edit global configuration
- Options: `--edit` to open in editor
- Handler: `GlobalHandlers.handle_config()`

### Project Operations

**`list`** - List all projects or show project details
- Arguments: `name` (optional)
- Options: `--format` (table|json|yaml)
- Handler: `ProjectHandlers.handle_list()`

**`delete`** - Remove project
- Arguments: `project`
- Options: `--force` to skip confirmation
- Handler: `ProjectHandlers.handle_delete()`

**`status`** - Show project/system status (context-aware)
- Handler: `QueryHandlers.handle_status()`
- Displays active session, recent activity, blockers

**`list-pending`** - Show pending handoffs
- Handler: `QueryHandlers.handle_list_pending()`

**`list-blockers`** - Show active blockers
- Handler: `QueryHandlers.handle_list_blockers()`

### Active Session Operations

**`activate`** - Activate agent session
- Arguments: `agent_id`
- Handler: `SessionHandlers.handle_activate()`
- Enforces governance gates before activation

**`handoff`** - Record agent handoff
- Options: `--to` (required), `--from`, `--artifacts`, `--notes`
- Handler: `EntryHandlers.handle_handoff()`
- Auto-detects source agent from active session

**`decision`** - Record decision
- Options: `--title`, `--rationale`, `--agent`
- Handler: `EntryHandlers.handle_decision()`

**`end`** - End active session
- Handler: `SessionHandlers.handle_end()`
- Archives session and clears active state

**`feedback`** - Record feedback
- Options: `--target`, `--severity`, `--summary`
- Handler: `EntryHandlers.handle_feedback()`

**`blocker`** - Record blocker
- Options: `--title`, `--description`, `--blocked-agents`
- Handler: `EntryHandlers.handle_blocker()`

**`iteration`** - Record iteration
- Options: `--trigger`, `--impacted-agents`, `--description`, `--version-bump`
- Handler: `EntryHandlers.handle_iteration()`

**`assumption`** - Record assumption
- Options: `--assumption`, `--rationale`
- Handler: `EntryHandlers.handle_assumption()`

**`check-handoff`** - Check if handoff exists
- Arguments: `agent_id`
- Handler: `QueryHandlers.handle_check_handoff()`

-----

## 4. Handler Architecture

Handlers bridge the CLI/TUI interface with the service layer. They orchestrate service calls, perform validation, and format output.

### Handler Classes

| Handler | Responsibility | Key Dependencies | Methods |
|---------|---------------|------------------|---------|
| **SessionHandlers** | Lifecycle management (init, activate, end) | ProjectService, WorkflowService, GateChecker | `handle_init`, `handle_activate`, `handle_end` |
| **EntryHandlers** | Ledger write operations | LedgerService | `handle_handoff`, `handle_decision`, `handle_feedback`, `handle_blocker`, `handle_iteration`, `handle_assumption` |
| **QueryHandlers** | Read-only queries and status | LedgerService, ProjectService | `handle_status`, `handle_check_handoff`, `handle_list_pending`, `handle_list_blockers` |
| **ProjectHandlers** | Project CRUD operations | ProjectService | `handle_list`, `handle_delete` |
| **GlobalHandlers** | System configuration | ConfigurationService, WorkflowService | `handle_list_workflows`, `handle_config` |
| **WorkflowHandlers** | Advanced workflow operations | WorkflowService, GateChecker | `handle_set_stage`, `handle_gate_check` |
| **ArtifactHandlers** | Artifact management | (varies) | Artifact-specific operations |

### Handler Design Patterns

**Constructor Pattern**:
```python
def __init__(self, console: Console, config=None):
    self.console = console
    self.config = config
    self.service = ServiceClass(config)
```

**Method Signature Pattern**:
- Accept keyword arguments directly (no `argparse.Namespace`)
- Use `Optional[str]` for nullable parameters
- Project name auto-detection from context when not provided

**Error Handling Pattern**:
- Try-except blocks wrapping service calls
- `validate_required()` for mandatory parameters
- `handle_error()` for consistent error display and logging

**TUI Integration Pattern**:
Handlers provide data-only methods for TUI consumption:
- `get_active_session()` - returns dict, no display
- `list_projects_data()` - returns data structure
- `get_dashboard_data()` - aggregates multiple data sources

### SessionHandlers Details

**Lifecycle Management**:
- `handle_init()`: Orchestrates project creation via `ProjectService.init_project()`
- `handle_activate()`: Enforces governance gates via `GateChecker` before activation
- `handle_end()`: Archives session and clears active state

**Governance Integration**:
Activation flow includes mandatory gate checking:
1. Validate agent ID and project existence
2. Invoke `GateChecker.check_gate(project, agent_id)`
3. If violations exist and mode is Strict, raise `CLIExecutionError`
4. Otherwise, proceed with activation via service layer

### EntryHandlers Details

**Ledger Operations**:
All methods write immutable entries to ledger files:
- `handle_handoff()`: Validates workflow rules, writes to `exchange_log.md`
- `handle_decision()`: Records ADR entries to `context_log.md`
- `handle_feedback/blocker/iteration/assumption()`: Structured ledger writes

**Validation Integration**:
Handoff operations validate against workflow manifest:
- Check valid agent transitions
- Verify required artifacts exist
- Enforce workflow stage rules

### QueryHandlers Details

**Read-Only Operations**:
- No state mutations
- Aggregates data from multiple services
- Formats output for CLI display or TUI consumption

**Smart Status**:
`handle_status()` provides comprehensive project overview:
- Active session information
- Recent activity summary
- Pending handoffs count
- Active blockers count
- Current workflow stage

-----

## 5. Supporting Modules

### Theme System (`theme.py`)

Centralized theme constants for consistent UI styling across CLI and TUI.

**Theme Categories**:
- **Status Colors**: SUCCESS, ERROR, WARNING, INFO
- **UI Elements**: BORDER, PANEL_BORDER, TABLE_HEADER, TABLE_BORDER
- **Text Styles**: HEADER, SUBHEADER, BODY, DIM, BOLD
- **Semantic Tokens**: DASHBOARD, FEEDBACK dictionaries for context-specific styling

**Integration**:
- `Theme.get_color_map()` returns dict of semantic color mappings
- Used by Rich Click configuration for help styling
- Referenced in display functions for consistent panels/tables

### Display Module (`display.py`)

Presentation functions for formatted output using Rich. All functions exported via `__all__`.

**Core Functions**:
- `display_table()`: Render data in Rich tables
- `display_list()`: Formatted lists with themes
- `display_text_panel()`: Text content in themed panels
- `display_action_result()`: Formatted operation results
- `display_error()`: Error panels with themed borders
- `display_info()`: Informational messages
- `display_warning()`: Warning messages with icons
- `display_project_summary()`: Structured project creation summary
- `display_help_panel()`: Help content in panels
- `display_status_panel()`: Multi-section status panels
- `exit_with_error()`: Exit with error message

**Design Principles**: 
- All functions accept `Console` parameter for testability and consistency
- Google-style docstrings with comprehensive documentation
- Console type validation for robustness
- Consistent imports: stdlib → third-party → local

### Formatting Module (`formatting.py`)

Utility functions for text formatting and layout.

**Key Functions**:
- `get_terminal_widthDelegates to `display_table()` for consistency
- `show_progress_bar()`: Progress indicators
- `shorten_path()`: Intelligent path shortening with relative path support
- `format_file_list()`: File list formatting with line wrapping

### UI Utils (`ui_utils.py`)

Additional UI helpers:
- `setup_logging()`: Configure logging system
- `format_output()`: Generic output formatting (table/json/yaml)

-----

## 6. Data Flow

### Command Execution Flow

```
User Input
    ↓
main.py: ContextAwareGroup
    ↓ (context detection)
Command Module (Click)
    ↓ (argument parsing)
Handler Method
    ↓ (validation)
Service Layer
    ↓ (business logic)
Ledger/Filesystem I/O
    ↓
Handler
    ↓ (format output)
Display Module
    ↓
Console Output
```

### Example: Handoff Flow

1. **User**: `agentic handoff --to A-02 --artifacts plan.md`
2. **Routing**: `ContextAwareGroup` routes to `active_session.handoff`
3. **Command**: Click parses arguments, extracts project from context
4. **Handler**: `EntryHandlers.handle_handoff()` validates inputs
5. **Validation**: Checks workflow rules via `validate_workflow_handoff()`
6. **Service**: `LedgerService.record_handoff()` writes to ledger
7. **Display**: `display_action_result()` shows confirmation
8. **Output**: Success message with artifact list

### Context Injection Pattern

Handlers receive project context via Click's context object:
```python
@click.pass_context
def command(ctx: click.Context, ...):
    config = ctx.obj.get('config')
    project = config.project.root_path.name if config.is_project_context else None
    handler.method(project=project, ...)
```

Auto-detection fallbacks when context unavailable:
- Use `Path.cwd().name` for project name
- Query `LedgerService.get_active_session()` for active agent

-----

## 7. Extending the CLI

### Adding a New Command

Follow this three-step process to maintain architectural consistency:

**Step 1: Implement Handler Logic**

Add method to appropriate handler class:
```python
# handlers/entry_handlers.py
def handle_new_operation(self, project: str, param: str) -> None:
    validate_required(project, "project", "new_operation")
    result = self.service.perform_operation(project, param)
    display_action_result("Operation complete", True, self.console)
```

**Step 2: Create Command Function**

Define Click command in appropriate module:
```python
# commands/active_session.py
@click.command(cls=RichCommand)
@click.option('--param', required=True)
@click.pass_context
def new_operation(ctx: click.Context, param: str):
    config = ctx.obj.get('config')
    project = config.project.root_path.name if config.is_project_context else None
    entry_handlers.handle_new_operation(project=project, param=param)
```

**Step 3: Register Command**

Update routing in `main.py`:
```python
# main.py - get_command() method
if config.is_project_context:
    mapping = {
        # ... existing ...
        'new-operation': active_session.new_operation,
    }
```

Also add to `list_commands()` return list for appropriate context.

### Design Guidelines

- **Zero Logic in Commands**: Command functions only parse and route
- **Keyword Arguments**: Handlers use kwargs, not positional args
- **Error Handling**: Use `try/except` with `display_error()`
- **Validation**: Use `validate_required()` for mandatory params
- **Display**: Use theme-aware display functions
- **TUI Compatibility**: Consider adding data-only method for TUI

-----