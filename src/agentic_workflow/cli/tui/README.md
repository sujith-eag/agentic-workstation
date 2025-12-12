# Text User Interface (TUI) for Agentic Workflow OS

The TUI provides an interactive, terminal-based interface for managing Agentic Workflow OS projects and operations. It offers guided workflows, menu-driven navigation, and rich terminal formatting for better user experience.

## Overview

The TUI is built using a modular MVC (Model-View-Controller) architecture that separates concerns for maintainability and extensibility. It uses `questionary` for interactive prompts and `rich` for terminal formatting and styling.

## Architecture

### Core Components

#### `main.py` - Main Application
- **Role**: Entry point and orchestrator for the TUI application
- **Function**: Initializes all components, manages application state, and runs the main event loop
- **Description**: The central hub that coordinates controllers, operations, and views

#### Base Classes (Distributed)
- **Role**: Common functionality and abstract base classes
- **Function**: Provides shared utilities for menus, views, wizards, and operations
- **Description**: Base classes are distributed across submodules:
  - `menus/base_menu.py`: `BaseMenu` class with common menu methods
  - `views/base_views.py`: `BaseView` class with common view methods
  - `wizards/base_wizard.py`: `BaseWizard` class with common wizard methods
  - `operations/base_operations.py`: `BaseOperations` class with common operation methods

#### `setup.py` - Configuration Wizard
- **Role**: First-run setup and configuration
- **Function**: Guides users through initial configuration of workspace paths, editor preferences, and system settings
- **Description**: Interactive wizard that creates `~/.config/agentic/config.yaml`

## Component Categories

### Controllers (`controllers/`)
Menu controllers handle navigation and user interaction logic.

- **`base_controller.py`**: Abstract base class for all controllers
- **`global_menu_controller.py`**: Main menu for global operations (project listing, creation)
- **`project_menu_controller.py`**: Project-specific operations menu
- **`agent_operations_controller.py`**: Agent management (activation, handoffs, decisions)
- **`artifact_management_controller.py`**: Artifact operations and management
- **`project_management_controller.py`**: Project creation and management
- **`project_navigation_controller.py`**: Project file and directory navigation
- **`project_wizard_controller.py`**: Guided project creation wizard
- **`system_info_controller.py`**: System information and diagnostics
- **`workflow_status_controller.py`**: Workflow status display and monitoring

### Operations (`operations/`)
Business logic components that handle core functionality.

- **`base_operations.py`**: Abstract base class for operations
- **`agent_ops.py`**: Agent lifecycle operations (activation, handoffs, decisions, workflow management)
- **`artifact_ops.py`**: Artifact management operations (creation, validation, organization)

### Views (`views/`)
Data presentation components that format and display information.

- **`base_views.py`**: Abstract base class for views
- **`project_views.py`**: Project listing and status displays
- **`system_views.py`**: System information and configuration displays
- **`error_view.py`**: Error message and modal displays

### Menus (`menus/`)
Legacy menu components (being phased out in favor of controllers).

- **`base_menu.py`**: Base menu functionality

### Wizards (`wizards/`)
Specialized guided workflows.

- **`base_wizard.py`**: Base wizard functionality

## Key Features

- **Interactive Menus**: Questionary-based selection menus with keyboard navigation
- **Rich Formatting**: Terminal tables, panels, and styled text using Rich library
- **Context Awareness**: Different menus based on global vs. project context
- **Error Handling**: Comprehensive error display with user-friendly modals
- **Guided Workflows**: Step-by-step wizards for complex operations
- **Modular Design**: Easy to extend with new controllers, operations, and views

## Usage

The TUI is launched via the main CLI:

```bash
# From project directory
./workflow tui

# Or via Python module
python3 -m agentic_workflow.cli.tui
```

## Development

When adding new features:

1. **Controllers**: For new menus or navigation flows
2. **Operations**: For new business logic
3. **Views**: For new data display formats
4. **Follow MVC**: Keep presentation, logic, and navigation separate

## Dependencies

- `questionary`: Interactive command-line prompts
- `rich`: Terminal formatting and styling
- `pathlib`: Path operations
- `typing`: Type hints for better code clarity
