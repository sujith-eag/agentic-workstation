# Template Placeholder Registry

> **Canonical Variable Reference** for Jinja2 templates  
> Version: 2.0 | Updated: 2025-12-05

---

## 1. Overview

This registry documents all variables available in template contexts. Variables are loaded from canonical JSON files and merged into a unified context by `build_agent_context()`.

---

## 2. Naming Conventions

| Pattern | Example | Source |
|---------|---------|--------|
| `agent_*` | `agent_id`, `agent_role` | agents.json |
| `workflow_*` | `workflow_name`, `workflow_display_name` | workflow.json |
| `project_*` | `project_name` | Function argument |
| Nested dict | `produces.core`, `handoff.next` | Structured data |

---

## 3. Variable Reference

### 3.1 Project Context

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `project_name` | `str` | Argument | Project identifier |
| `workflow_name` | `str` | Argument | Workflow key (e.g., `planning`) |
| `workflow_display_name` | `str` | workflow.json | Human-readable name |
| `timestamp` | `str` | Runtime | ISO timestamp |

### 3.2 Agent Identity

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `agent_id` | `str` | agents.json | Agent identifier (e.g., `A-02`) |
| `agent_role` | `str` | agents.json | Role title |
| `agent_type` | `str` | agents.json | `core`, `support`, `on-demand` |
| `agent_slug` | `str` | agents.json | URL-safe identifier |
| `key_responsibilities` | `list[str]` | agents.json | Brief responsibility list |

### 3.3 Instructions

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `purpose` | `str` | instructions.json | Agent purpose statement |
| `responsibilities` | `list[str]` | instructions.json | Detailed responsibilities |
| `domain_rules` | `list[str]` | instructions.json | Domain-specific rules |

#### Workflow Section

| Variable | Type | Description |
|----------|------|-------------|
| `workflow.entry_conditions` | `list[str]` | Prerequisites before starting |
| `workflow.steps` | `list[str]` | Ordered workflow steps |
| `workflow.exit_conditions` | `list[str]` | Completion criteria |

#### Boundaries Section

| Variable | Type | Description |
|----------|------|-------------|
| `boundaries.in_scope` | `list[str]` | What agent CAN do |
| `boundaries.out_of_scope` | `list[str]` | What agent CANNOT do |

#### Handoff Section

| Variable | Type | Description |
|----------|------|-------------|
| `handoff.next` | `list[dict]` | Next agents `[{id, condition}]` |
| `handoff.required_artifacts` | `list[str]` | Required before handoff |
| `handoff.required_logs` | `list[str]` | Required log entries |
| `handoff.conditions` | `list[str]` | Handoff conditions |

### 3.4 Artifacts (Tiered)

Artifacts are organized by tier for governance control:

| Variable | Type | Description |
|----------|------|-------------|
| `produces.core` | `list[dict]` | Primary outputs (gating) |
| `produces.domain` | `list[dict]` | Domain-specific outputs |
| `produces.log` | `list[dict]` | Log file outputs |
| `consumes.core` | `list[dict]` | Required inputs |
| `consumes.domain` | `list[dict]` | Domain context inputs |
| `consumes.reference` | `list[dict]` | On-demand reference |
| `consumes.gating` | `list[dict]` | Gating inputs from prior stages |

#### Artifact Object Structure

```python
{
    "filename": "requirements_spec.md",
    "description": "Formal requirements",
    "tier": "core",
    "owner": "A-02"
}
```

### 3.5 Workflow Context

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `stage` | `dict` | workflow.json | Current pipeline stage |
| `stage.id` | `str` | | Stage identifier |
| `stage.name` | `str` | | Stage display name |
| `stage.agents` | `list[str]` | | Agents in this stage |

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `checkpoint` | `dict\|None` | workflow.json | Checkpoint after this agent |
| `checkpoint.type` | `str` | | `human`, `automated` |
| `checkpoint.prompt` | `str` | | Checkpoint prompt |
| `checkpoint.gating` | `str` | | `strict`, `warn`, `none` |
| `checkpoint.required_artifacts` | `list[str]` | | Required before checkpoint |

### 3.6 Governance & Policy

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `governance` | `dict` | workflow.json | Governance settings |
| `governance.adr_required` | `bool` | | ADR on major decisions |
| `governance.traceability_required` | `bool` | | Requirement tracing |

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `enforcement` | `dict` | workflow.json | Enforcement settings |
| `enforcement.checkpoint_gating` | `str` | | `strict`, `warn`, `none` |
| `enforcement.handoff_gating` | `str` | | `strict`, `warn`, `none` |

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `logging_policy` | `dict` | workflow.json | Required logging |
| `logging_policy.require_session_log` | `bool` | | Session logging |
| `logging_policy.require_decision_log` | `bool` | | Decision logging |
| `logging_policy.require_handoff_log` | `bool` | | Handoff logging |

### 3.7 Computed Fields

| Variable | Type | Computed From | Description |
|----------|------|---------------|-------------|
| `next_agent_id` | `str\|None` | `handoff.next[0].id` | Primary next agent |
| `required_artifacts` | `list[str]` | `handoff.required_artifacts` | Flat list for checklist |
| `context_file` | `str` | Convention | Context file path |

---

## 4. Data Sources

| File | Path | Contents |
|------|------|----------|
| agents.json | `manifests/_canonical/<workflow>/` | Agent definitions |
| instructions.json | `manifests/_canonical/<workflow>/` | Agent instructions |
| artifacts.json | `manifests/_canonical/<workflow>/` | Artifact registry |
| workflow.json | `manifests/_canonical/<workflow>/` | Workflow config |

---

## 5. Context Builder

The `build_agent_context()` function in `jinja_loader.py` merges all sources:

```python
def build_agent_context(workflow: str, agent_id: str, project_name: str) -> dict:
    # Load canonical JSON files
    agents = load_canonical_json(workflow, 'agents.json')
    instructions = load_canonical_json(workflow, 'instructions.json')
    artifacts = load_canonical_json(workflow, 'artifacts.json')
    workflow_data = load_canonical_json(workflow, 'workflow.json')
    
    # Find and merge agent data
    agent = find_agent(agents, agent_id)
    instr = find_instructions(instructions, agent_id)
    
    # Resolve artifacts to full objects
    produces = resolve_artifacts(agent['produces'], artifacts)
    consumes = resolve_artifacts(agent['consumes'], artifacts)
    
    # Build unified context
    return {
        'project_name': project_name,
        'workflow_name': workflow,
        'agent_id': agent_id,
        'agent_role': agent['role'],
        # ... all variables
    }
```

---

## 6. Template Usage Examples

### Basic Variable Access

```jinja2
# {{ agent_role }}

{{ purpose }}
```

### List Iteration

```jinja2
## Responsibilities

{% for resp in responsibilities %}
- {{ resp }}
{% endfor %}
```

### Tiered Artifacts

```jinja2
## Artifacts You Produce

### Core (Gating)
{% for a in produces.core %}
- `{{ a.filename }}` — {{ a.description }}
{% endfor %}

### Domain
{% for a in produces.domain %}
- `{{ a.filename }}`
{% endfor %}
```

### Conditional Sections

```jinja2
{% if checkpoint %}
> ⚠️ **CHECKPOINT** after this agent: {{ checkpoint.prompt }}
{% endif %}

{% if handoff.next %}
## Next Agent
→ {{ handoff.next[0].id }}
{% endif %}
```

### Using Filters

```jinja2
{{ responsibilities | md_list }}

{{ workflow.steps | md_numbered_list }}

{{ rows | md_table }}
```

---

## 7. Adding New Variables

### Step 1: Add to Schema

Update the relevant JSON schema in `manifests/_canonical_schemas/`:

```json
{
  "properties": {
    "new_field": {
      "type": "string",
      "description": "Description of new field"
    }
  }
}
```

### Step 2: Add to Canonical JSON

Update canonical JSON files in `manifests/_canonical/<workflow>/`.

### Step 3: Update Context Builder

If the field needs special handling, update `build_agent_context()` in `jinja_loader.py`.

### Step 4: Document Here

Add the variable to this registry with type, source, and description.

### Step 5: Use in Templates

```jinja2
{{ new_field }}
```

---

## 8. Variable Categories by Template Type

### Agent Templates

```python
# Required
agent_id, agent_role, purpose, responsibilities

# Artifacts
produces, consumes

# Workflow
workflow, boundaries, handoff

# Optional
checkpoint, stage, governance
```

### Session Templates

```python
# Required
project_name, agent_id, agent_role, workflow_name

# CLI
cli_commands, context_file

# Policy
base_rules, protocol, logging_policy

# Optional
checkpoint
```

### Documentation Templates

```python
# Required
workflow_name, workflow_display_name

# Conditional
agents (list), artifacts (list), cli_commands (list)
```

---

## 9. Deprecation Notes

### Removed Variables (v1.0 → v2.0)

| Old Variable | Replacement | Notes |
|--------------|-------------|-------|
| `produces_list` | `produces.core` | Now tiered dict |
| `consumes_list` | `consumes.core` | Now tiered dict |
| `domain_instructions` | `domain_rules` | Renamed for clarity |
| `{{agent_id}}` (mustache) | `{{ agent_id }}` | Jinja2 syntax |

---

## References

- [TEMPLATES.md](./TEMPLATES.md) — Template system documentation
- [scripts/utils/jinja_loader.py](../scripts/utils/jinja_loader.py) — Context builder
- [manifests/_canonical_schemas/](../manifests/_canonical_schemas/) — JSON schemas

---

*Last updated: 2025-12-05*
