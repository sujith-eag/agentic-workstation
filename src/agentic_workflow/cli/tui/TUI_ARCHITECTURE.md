# Agentic Workflow OS: TUI Architecture Reference

**Version:** 2.0 (Cockpit Edition)
**Status:** Release Candidate / Stateless Architecture
**Scope:** Text User Interface, Controllers, Views, and State Management.

## 1. Architectural Overview

The TUI is designed as a **Stateless Presentation Layer** that sits on top of the Core Services. It follows a strict "Fetch-Render-Act" cycle to ensure consistency with the underlying Ledger.


```mermaid
graph TD
    User[User Input] --> Controller[Controller]
    Controller --> Service[Service Layer (Read)]
    Service --> Ledger[Ledger I/O]
    Service --> Data[Fresh State Data]
    Data --> View[Rich View Component]
    Controller --> Handler[Request Handler (Write)]
    Handler --> Governance[Governance Gate]
    Governance --> Service
````

### Core Principles

1.  **Stateless Controllers:** The TUI does **not** maintain a long-lived cache of the project state. Every time a menu or dashboard renders, it fetches fresh data from the `LedgerService`.
2.  **Service-Driven Reads:** Controllers query `LedgerService` and `ProjectService` directly to populate views (e.g., getting the Active Agent or Recent Activity).
3.  **Handler-Driven Writes:** Any state-changing operation (Activate, Handoff, Block) must go through `handlers/` to ensure Governance checks and side-effects are applied correctly.
4.  **Views are Pure:** Views accept data dictionaries and render them using `rich`. They perform no I/O operations.

## 2. Directory Structure

| Directory | Role | Key Components |
| :--- | :--- | :--- |
| **`controllers/`** | Navigation & Logic | `GlobalMenu`, `ProjectMenu`, `AgentOperations`, `ProjectNavigation` |
| **`views/`** | Rendering Logic | `DashboardView`, `ArtifactView`, `SystemInfoView`, `ErrorView` |
| **`wizards/`** | Guided Workflows | `ProjectCreationWizard` |
| **`operations/`** | File Operations | `ArtifactOperations` |

## 3. The "Cockpit" State Machine

The `TUIApp` (`main.py`) manages the high-level context switching between Global and Project modes, but it delegates detailed state retrieval to the Services.

### The Dashboard View

The `DashboardView` acts as the "Mission Control" center. It is rendered at the start of the `ProjectMenuController` loop.

  * **Header:** Persistent Context Header (`Agentic OS :: [Project] [Agent]`).
  * **Top Left (Project):** Static metadata (Name, Workflow Type, Description).
  * **Top Right (Session):** Dynamic state (Active Agent, Stage, Blockers).
  * **Bottom (Activity):** Live feed of the last 5 events (Handoffs, Decisions) fetched via `get_recent_activity`.

### Context Switching

  * **Global Mode:** User manages projects (`init`, `list`). Context is `None`.
  * **Project Mode:** User manages a specific workflow. Context is derived from `ProjectService.get_project_status(cwd)`.

## 4\. Interaction Patterns

### The "Fetch-Render-Act" Loop

1.  **Fetch:** Controller calls `LedgerService.get_active_session()` and `ProjectService.get_project_status()`.
2.  **Render:** Controller passes this fresh data to `DashboardView.render()`.
3.  **Act:** User selects an option (e.g., "Record Blocker").
4.  **Write:** Controller calls `EntryHandlers.handle_blocker()`.
5.  **Loop:** Screen clears, and Step 1 repeats (fetching the newly written blocker).

### Error Handling (Modal)

Raw stack traces are suppressed in favor of interactive Modals.

  * **Pattern:**
    ```python
    try:
        handler.do_work()
    except Exception as e:
        self.app.error_view.display_error_modal(str(e))
        # Wait for user acknowledgment
    ```
  * **Benefit:** Prevents errors from flashing on screen and disappearing before the next render cycle.

### Smart Inputs

  * **Prefilling:** When recording a Handoff or Feedback, the Controller prefetches the Active Agent to pre-fill the "From" or "Reporter" fields.
  * **Validation:** Input fields use `questionary` validators to prevent empty or invalid data submissions at the UI level.

## 5. Developer Standards

### Adding a New Screen

1.  **Create the View:** Define `views/my_feature_view.py`. Inherit from `BaseView`.
2.  **Create the Controller:** Define `controllers/my_feature_controller.py`.
3.  **Implement Header:** Always call `self.display_context_header("My Feature")` first.
4.  **Connect Logic:**
      * **Read:** Call `self.app.service_layer...`
      * **Write:** Call `self.app.handlers...`

### Responsiveness

  * **Spinners:** Any operation touching the disk must be wrapped in `show_progress`.
    ```python
    with show_progress("Analyzing..."):
        service.analyze_data()
    ```

### Safety

  * **Imports:** Use absolute imports (`from agentic_workflow.services import ...`) to avoid runtime path errors in the TUI context.

<!-- end list -->

```