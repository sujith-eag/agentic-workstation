# Agentic Workstation (Beta Release)

> **Structured Architectural Scaffolding for AI Development**

[![Version](https://img.shields.io/badge/version-1.0.3-blue.svg)](https://github.com/sujith-eag/agentic-workstation)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Agentic Workstation** is a development platform that orchestrates Multi-Agent Systems to plan, architect, and implement complex software projects. Unlike "Chat with Code" tools that rely on messy, unstructured conversation history, this system enforces a **Context-First** philosophy. It treats Agent Context as a file-system state machine, ensuring that your AI Engineer knows exactly what your AI Architect decided.

---

## ⚡ Why Use This?

Most AI coding tools suffer from **Context Drift**. After 20 messages, the AI forgets the architectural constraints you set in message #1.

AI for projects and work is like a rocket: it gives a quick boost of velocity if you have direction, but soon everyone realizes it's only a first-stage booster that stops midway once context is off. The velocity drops, and to carry forward and build production-grade applications needs a 2nd and 3rd stage booster with precision guidance to reach and stay in orbit. **This project is that 2nd and 3rd stage.**

**Agentic Workstation solves this by:**
1.  **Strict Role Separation:** Agents have clearly defined roles with explicit boundaries - architects handle specifications, engineers handle implementation, with enforced separation to prevent scope creep.
2.  **Artifact-Driven Handoffs:** Agents cannot proceed until they receive specific, validated artifacts from predecessors, ensuring dependencies are met before progression.
3.  **Programmatic Agent Interaction:** Agents operate in environments with terminal access, using CLI tools to search project state, log decisions, record handoffs, and progress through workflow stages - enabling structured, auditable AI collaboration without conversational drift.

The system operates on a **Stateless Core / Stateful Edge** model.

---

## 🚀 Quick Start

### Environment Setup
Create and activate a Python virtual environment:
```bash
# Create virtual environment
python3 -m venv myproject-env

# Activate the environment
source myproject-env/bin/activate  

# On Windows: 
source myproject-env\Scripts\activate
```

### Installation

**Option A: Pip (Recommended)**
```bash
pip install agentic-workstation

# Verify installation
agentic --version
agentic workflow list
agentic tui --help
```

**Option B: From Source (Development)**
```bash
git clone https://github.com/sujith-eag/agentic-workstation.git
cd agentic-workstation
pip install -e .
```

### Uninstallation

**Option A: Pip**
```bash
pip uninstall agentic-workstation
```

**Option B: Docker**
```bash
# Remove the Docker image
docker rmi agentic-workstation

# Remove any running containers (if any)
docker rm $(docker ps -aq --filter ancestor=agentic-workstation)
```

## CLI & TUI Usage

For detailed CLI documentation, see [CLI_REFERENCE.md](CLI_REFERENCE.md). For interactive usage, use the Text User Interface (TUI) with `agentic tui`.


### Available Commands

- `agentic project` - Project management (init, list, remove, status)
- `agentic workflow` - Workflow orchestration (init, activate, handoff, status)
- `agentic tui` - Interactive Text User Interface for guided workflow management
- `agentic --help` - Show all available options

---

## 🏗️ Creating & Running a Project

### 1. Initialize a Project
Navigate to your empty folder and initialize a project.

```bash
mkdir my-new-saas && cd my-new-saas
agentic project init MySaaS
```

*This creates a project with the default "planning" workflow. Use `--workflow` to specify another workflow.*

### 2. Agent Workflow Orchestration

Agents operate in environments with terminal access, using CLI commands to orchestrate structured workflows:

1.  **Session Activation:** User or Agents run `agentic workflow activate A-01` to start their session and receive context.

2.  **Context Processing:** Agents access the generated `active_session.md` file containing their role, instructions, and project state.

3.  **Artifact Generation:** Agents produce required deliverables and save them to specified artifact paths.

4.  **Handoff Execution:** Agents execute handoff commands to progress the workflow:
    ```bash
    agentic workflow handoff --from A01 --to A02 --artifacts artifacts/A-01/project_brief.md
    ```
    *The system validates artifact existence and workflow rules before allowing progression.*

5.  **State Management:** Agents can log decisions, record blockers, and query project status using CLI commands throughout the process.

### 3. Review Status

View the decision tree and current state.

```bash
agentic workflow status
```

---

## 📦 Workflows (NOT ENTIRLY COVERED YET)

The system supports pluggable **Workflow Manifests**.

### 1. Planning (Canonical)
*   **Goal:** Turn a 1-sentence idea into a full Tech Spec.
*   **Agents:**
    *   `A-01 Incubation`: Refines the idea.
    *   `A-02 Requirements`: Lists functional/non-functional reqs.
    *   `A-03 Architect`: Designs the system topology.
    *   `A-04 Security`: Threat modeling.
    *   (And 10 more specialized roles).

### 2. Implementation (Canonical)
*   **Goal:** Turn specs into code.
*   **Agents:**
    *   `E-01 Frontend`: React/Vue/Svelte implementation.
    *   `E-02 Backend`: API & Logic.
    *   `E-03 Database`: Schema & Migrations.

### 3. Custom Workflows
You can create your own workflows by placing a manifest in:
- Project: `./.agentic/workflows/my-custom-flow/workflow.json`
- User global: `~/.config/agentic/workflows/my-custom-flow/workflow.json`
- System: Bundled in package (not recommended for custom)

Workflow manifests include `workflow.json`, `agents.json`, `artifacts.json`, etc.

---

## 🛠️ CLI Commands

### Global Commands
```bash
# List available workflows
agentic workflow list-workflows

# Show CLI help
agentic --help
```

### TUI Commands
```bash
# Launch Text User Interface for interactive workflow management
agentic tui

# From source/development:
python3 -m agentic_workflow.cli.main tui
```
*The TUI provides an interactive, menu-driven interface for project management and workflow operations, with context-aware menus that automatically detect whether you're working globally or within a project.*

### Project Commands
```bash
# Create new project
agentic project init MyProject --workflow planning --description "My project description"

# List all projects
agentic project list

# Show project details
agentic project list MyProject

# Remove a project
agentic project remove MyProject --force

# Show current project status
agentic project status
```

### Workflow Commands
```bash
# Initialize workflow in project
agentic workflow init MyProject --workflow planning --description "My planning project"

# Activate an agent session
agentic workflow activate MyProject A-01

# Show project workflow status
agentic workflow status MyProject

# Record handoff between agents
agentic workflow handoff MyProject --from A01 --to A02 --artifacts "file.md"

# Record project decision
agentic workflow decision MyProject --title "Decision title" --rationale "Reasoning"

# Check if handoff exists for agent
agentic workflow check-handoff MyProject A-02

# List pending handoffs
agentic workflow list-pending MyProject

# List active blockers
agentic workflow list-blockers MyProject

# End workflow session
agentic workflow end MyProject

# Delete project (workflow command)
agentic workflow delete MyProject --force
```

## ⚙️ Configuration & Governance

### `agentic.toml`
Every project handles its own configuration.
```toml
[project]
name = "MySaaS"
version = "0.1.0"

[governance]
require_reviews = true
git_commit_on_handoff = true
```

### Global Config (`~/.config/agentic/config.toml`)
Set your preferences for all projects.
```toml
[directories]
projects = "projects"

[governance]
level = "moderate"

[workflows]
default = "planning"
```

---

## 🛠️ Development

This project is built with Python 3.10+.

*   **Core:** `src/agentic_workflow`
*   **Manifests:** `src/agentic_workflow/manifests` (Canonical Definitions)
*   **Templates:** `src/agentic_workflow/templates` (Jinja2 templates)
*   **Build:** `pyproject.toml` (Hatchling)
*   **Tests:** Not included in deployment

**License:** MIT
