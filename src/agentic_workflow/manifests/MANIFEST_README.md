# Manifests Directory — Definitive Guide

**Last Updated:** 2025-12-05  
**Status:** Canonical JSON as Source of Truth

---

## Overview

This directory contains the **authoritative data definitions** for the multi-agent workflow system. All workflow configurations, agent definitions, artifact registries, and behavioral instructions are stored here.

### Key Principle

> **Edit canonical JSON only.** YAML files in `workflows/` are generated and should not be edited directly.

---

## Directory Structure

```
manifests/
├── README.md                    # This file
├── SCHEMA_CONSOLIDATION_PLAN.md # Migration plan for schema improvements
├── SCHEMA_MIGRATION_AGENT_PROMPT.md # Agent instructions for executing migrations
│
├── _canonical_schemas/          # JSON Schema definitions (validation rules)
│   ├── agents.schema.json       # Agent identity & I/O contracts
│   ├── artifacts.schema.json    # Artifact registry & ownership
│   ├── instructions.schema.json # Agent behavior & workflow steps
│   └── workflow.schema.json     # Pipeline, stages, globals, checkpoints
│
├── _canonical/                  # Canonical JSON data (EDIT HERE)
│   ├── planning/                # Planning workflow (15 agents)
│   │   ├── agents.json
│   │   ├── artifacts.json
│   │   ├── instructions.json
│   │   └── workflow.json
│   ├── implementation/          # Implementation workflow (10 agents)
│   │   └── ...
│   ├── research/                # Research workflow (12 agents)
│   │   └── ...
│   └── workflow-creation/       # Meta-workflow for creating workflows
│       └── ...
│
└── workflows/                   # Generated YAML (DO NOT EDIT)
    ├── _registry.yaml           # Available workflows
    └── <workflow>/              # Per-workflow generated files
        ├── agents.yaml
        ├── artifacts.yaml
        ├── instructions.yaml
        └── workflow.yaml
```

---

## File Ownership Matrix

| File | What It Owns | What It References |
|------|--------------|-------------------|
| `workflow.json` | Pipeline order, stages, checkpoints, globals, config, display | Agent IDs |
| `agents.json` | Agent identity, type, produces/consumes contracts | Artifact filenames |
| `artifacts.json` | Artifact metadata, ownership, categories | Agent IDs (owner field) |
| `instructions.json` | Behavioral guidance, workflow steps, boundaries, handoffs | Agent IDs, artifact filenames |

### Data Flow

```
workflow.json ──references──► agents.json ──references──► artifacts.json
                                   ▲
                                   │
                            instructions.json
                            (matches by agent ID)
```

---

## Schema Reference

### Agent ID Format

Pattern: `^[A-Z]{1,2}-[A-Z0-9]{2,6}$`

| Example | Workflow | Type |
|---------|----------|------|
| `A-01` | Planning | Core agent (padded) |
| `I-SEC` | Implementation | On-demand agent |
| `R-00` | Research | Orchestrator |

### Agent Types

| Type | Description |
|------|-------------|
| `orchestrator` | Session controller, manages handoffs |
| `core` | Main pipeline agent, sequential execution |
| `on_demand` | Invokable specialist, not in main pipeline |
| `gating` | Validation/audit agent, blocks progression |

### Artifact Categories

| Category | Purpose |
|----------|---------|
| `core` | Essential workflow outputs |
| `domain` | Domain-specific files (code, configs) |
| `reference` | Supporting documentation |
| `gating` | Required for checkpoint progression |
| `log` | Session and decision logs |

### Checkpoint Types

| Type | Description |
|------|-------------|
| `human` | Requires manual approval |
| `gate` | Requires artifact existence |
| `validation` | Requires automated test pass |

---

## Editing Workflow

### 1. Edit Canonical JSON

```bash
# Example: Add a new artifact to planning workflow
vim manifests/_canonical/planning/artifacts.json
```

### 2. Validate Changes

```bash
# Validate single workflow
python3 -m scripts.validation.validate_canonical --workflow planning

# Validate all workflows
python3 -m scripts.validation.validate_canonical --all
```

### 3. Regenerate YAML (if applicable)

```bash
# After validation passes
python3 -m scripts.validation.generate_yaml_from_canonical --workflow planning
```

### 4. Commit Changes

```bash
git add manifests/_canonical/planning/
git commit -m "feat(planning): add new artifact XYZ"
```

---

## Validation Rules

The validator (`scripts/validation/validate_canonical.py`) checks:

### Cross-Reference Integrity

| Rule | Description |
|------|-------------|
| Pipeline → Agents | All IDs in `pipeline.order` must exist in `agents.json` |
| Produces → Artifacts | All produced filenames must exist in `artifacts.json` |
| Consumes → Artifacts | All consumed filenames must exist in `artifacts.json` or `input_from` |
| Owner → Agents | All artifact owners must be valid agent IDs |
| Instructions → Agents | All instruction IDs must match agent IDs |
| Slug Consistency | Slugs must match between `agents.json` and `instructions.json` |

### Format Validation

| Field | Pattern |
|-------|---------|
| Agent ID | `^[A-Z]{1,2}-[A-Z0-9]{2,6}$` |
| Slug | `^[a-z0-9_]+$` |
| Filename | `^[a-z0-9_/]+\.(md\|yaml\|json\|bib)$` |

### Structural Checks

- No duplicate agent IDs or slugs
- No duplicate artifact filenames
- No circular dependencies in produces/consumes
- Cycle references match `workflow.cycles` definitions
 - `workflow.json` may include a new `config` section for enforcement, logging, validation, and bypass controls. Use `config` instead of legacy `globals.logging_policy` or `globals.enforcement`.

---

## Cross-Workflow Dependencies

Workflows can consume artifacts from other workflows via `input_from`:

```json
// implementation/workflow.json
{
  "input_from": {
    "planning": {
      "description": "Planning artifacts consumed by implementation",
      "artifacts": [
        "requirements_spec.md",
        "architecture_overview.md",
        "api_specifications.md"
      ]
    }
  }
}
```

Then agents can reference these:

```json
// implementation/agents.json
{
  "id": "I-02",
  "consumes": {
    "core": [
      {"file": "api_specifications.md", "from_workflow": "planning"}
    ]
  }
}
```

---

## Common Tasks

### Add a New Agent

1. Add to `agents.json`:
```json
{
  "id": "A-15",
  "slug": "new_agent",
  "role": "New Agent Role",
  "agent_type": "core",
  "description": "What this agent does",
  "produces": { "core": ["output.md"] },
  "consumes": { "core": ["input.md"] }
}
```

2. Add to `instructions.json`:
```json
{
  "id": "A-15",
  "slug": "new_agent",
  "role": "New Agent Role",
  "purpose": "...",
  "responsibilities": ["..."],
  "workflow": { "steps": ["..."] },
  "boundaries": { "in_scope": ["..."], "out_of_scope": ["..."] },
  "handoff": { "next": [{"id": "A-16"}] }
}
```

3. Add produced artifacts to `artifacts.json`:
```json
{
  "filename": "output.md",
  "owner": "A-15",
  "description": "...",
  "category": "core",
  "required": true
}
```

4. Add agent ID to `workflow.json` pipeline:
```json
"pipeline": {
  "order": ["A-00", ..., "A-15"]
}
```

5. Validate: `python3 -m scripts.validation.validate_canonical --workflow planning`

### Add a New Artifact

1. Add to `artifacts.json` with valid owner
2. Add to producing agent's `produces` in `agents.json`
3. Add to consuming agents' `consumes` in `agents.json`
4. Validate

### Add a Cross-Workflow Dependency

1. Add artifact to source workflow's `artifacts.json`
2. Add to target workflow's `input_from` in `workflow.json`
3. Add to consuming agent's `consumes` with `from_workflow` key
4. Validate both workflows

---

## CI Integration

Add to your CI pipeline:

```yaml
name: Validate Manifests
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install jsonschema
      - run: python3 -m scripts.validation.validate_canonical --all --strict
```

---

## Troubleshooting

### "Schema validation failed"

Check that your JSON matches the schema. Common issues:
- Missing required fields (`id`, `slug`, `role` for agents)
- Invalid ID format (must match pattern)
- Wrong type (array vs object)

### "Owner not found in agents.json"

The artifact's `owner` field references an agent ID that doesn't exist. Check spelling and ID format.

### "Produces/consumes not in artifacts.json"

The agent references a filename that isn't registered. Either:
- Add the artifact to `artifacts.json`, or
- If it's from another workflow, add to `input_from` and use `from_workflow`

### "Circular dependency detected"

Agent A produces what Agent B consumes, and Agent B produces what Agent A consumes. Review the dependency chain and break the cycle.

---

## Related Documentation

- `DATA_SCHEMA_STATUS_REPORT.md` — Current analysis and issue inventory
- `SCHEMA_CONSOLIDATION_PLAN.md` — Planned improvements
- `scripts/README.md` — CLI documentation
- `manifests/_canonical/CANONICAL_SCHEMA_SPECIFICATION.md` — Design principles

---

## Version History

| Date | Change |
|------|--------|
| 2025-12-05 | Created definitive README |
| 2025-12-04 | Completed canonical migration for all workflows |
| 2025-11-29 | Initial canonical schema implementation |
