# Schema Consolidation Plan

**Date:** 2025-12-05  
**Status:** PROPOSED  
**Purpose:** Phased plan to consolidate schemas, fix inconsistencies, and improve data quality

---

## Overview

This document provides a step-by-step plan for an agent (human or AI) to:
1. Consolidate `config.schema.json` into `workflow.schema.json`
2. Eliminate dual-location UI hints
3. Standardize `on_demand` placement
4. Add missing fields (versioning, stages)
5. Update canonical data files
6. Enhance validation script
7. Create definitive documentation

**Execution Order:** Schema → Data → Validation → Documentation

---

## Phase 1: Schema Consolidation

### 1.1 Merge `config.schema.json` into `workflow.schema.json`

**Goal:** All governance and runtime configuration lives in `workflow.json` under a unified `config` section.

**Current State:**
- `config.schema.json` defines: `enforcement`, `logging`, `validation`, `bypass`, `workflow_overrides`
- `workflow.schema.json` has: `globals.logging_policy`, `globals.enforcement` (partial overlap)

**Target State:**
```json
// workflow.schema.json - new unified config section
{
  "properties": {
    "config": {
      "type": "object",
      "description": "Unified runtime configuration for enforcement, logging, and validation",
      "properties": {
        "enforcement": {
          "type": "object",
          "properties": {
            "mode": { "type": "string", "enum": ["strict", "lenient", "none"], "default": "strict" },
            "checkpoint_gating": { "type": "string", "enum": ["strict", "warn", "none"], "default": "strict" },
            "handoff_gating": { "type": "string", "enum": ["strict", "warn", "none"], "default": "strict" }
          }
        },
        "logging": {
          "type": "object",
          "properties": {
            "require_session_log": { "type": "boolean", "default": true },
            "require_decision_log": { "type": "boolean", "default": true },
            "require_assumption_log": { "type": "boolean", "default": true },
            "require_handoff_log": { "type": "boolean", "default": true },
            "require_artifact_tracking": { "type": "boolean", "default": true }
          }
        },
        "validation": {
          "type": "object",
          "properties": {
            "run_validation_commands": { "type": "boolean", "default": true },
            "timeout_seconds": { "type": "integer", "minimum": 1, "default": 30 }
          }
        },
        "bypass": {
          "type": "object",
          "properties": {
            "require_reason": { "type": "boolean", "default": true },
            "log_bypasses": { "type": "boolean", "default": true }
          }
        }
      },
      "additionalProperties": false
    }
  }
}
```

**Steps:**
1. Open `manifests/_canonical_schemas/workflow.schema.json`
2. Add `config` property (as shown above) under `properties`
3. Mark `globals.logging_policy` and `globals.enforcement` as deprecated with description note
4. Optionally delete `config.schema.json` or mark it deprecated with header comment

**Deprecation Comment for globals:**
```json
"globals": {
  "type": "object",
  "description": "Global variables. NOTE: logging_policy and enforcement are DEPRECATED - use config.logging and config.enforcement instead",
  ...
}
```

---

### 1.2 Eliminate Dual-Location UI Hints

**Goal:** UI configuration lives in ONE place only (`display`).

**Current State:**
- `display`: `name`, `stage_order`, `frontmatter_fields`, `agent_prefix`, `orch_id`, `base_rules`, `protocol`, `copilot`
- `globals.ui`: `name`, `stage_order`, `frontmatter_fields` (DUPLICATE)

**Target State:**
- Keep ONLY `display` for all UI hints
- Remove `globals.ui` from schema

**Steps:**
1. Open `manifests/_canonical_schemas/workflow.schema.json`
2. Locate `globals.properties.ui` and REMOVE it entirely
3. Ensure `display` has all needed properties:
```json
"display": {
  "type": "object",
  "description": "Display and UI configuration (SINGLE SOURCE for all UI hints)",
  "properties": {
    "name": { "type": "string", "description": "Short display name for UIs" },
    "agent_prefix": { "type": "string", "description": "ID prefix for agents (e.g., A, I, R)" },
    "orch_id": { "type": "string", "description": "Orchestrator agent ID" },
    "id_format": { "type": "string", "enum": ["padded", "canonical"] },
    "focus": { "type": "string" },
    "stage_order": { "type": "array", "items": { "type": "string" }, "description": "UI ordering of stages" },
    "frontmatter_fields": { "type": "array", "items": { "type": "string" }, "description": "Priority fields for frontmatter" },
    "base_rules": { "type": "array", "items": { "type": "string" } },
    "protocol": { "type": "object" },
    "copilot": { "type": "object" }
  },
  "additionalProperties": false
}
```

---

### 1.3 Standardize `on_demand` Placement

**Goal:** `on_demand` agents are declared ONLY in `pipeline.on_demand`, not in `metadata`.

**Current State (implementation workflow):**
```json
"pipeline": { "order": [...] },
"metadata": { "on_demand": { "agents": ["I-SEC", "I-DOC", ...] } }
```

**Target State:**
```json
"pipeline": {
  "order": [...],
  "on_demand": ["I-SEC", "I-DOC", "I-DS", "I-PERF"]
}
```

**Schema Update (if not already present):**
```json
"pipeline": {
  "properties": {
    "order": { ... },
    "on_demand": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Agent IDs available on-demand (not in main pipeline)"
    },
    ...
  }
}
```

**Validation Rule to Add:**
- If `metadata.on_demand.agents` exists, emit WARNING suggesting move to `pipeline.on_demand`

---

### 1.4 Handle `template` Values in Artifacts

**Goal:** Clarify `template` field semantics.

**Current State:**
- Many artifacts have `"template": null`
- Some have no `template` field at all

**Decision Options:**
1. **REMOVE** `template` field from schema (if not used by any script)
2. **MAKE OPTIONAL** and remove `null` values from data
3. **KEEP** but document when to use

**Recommended: Option 2 - Make Optional**

**Schema Update:**
```json
"template": {
  "type": "string",
  "description": "Template file path relative to templates/ directory. Omit if artifact has no template."
}
```

**Data Cleanup Rule:**
- Remove all `"template": null` entries from artifacts.json files

---

### 1.5 Add Artifact Versioning (Optional Enhancement)

**Goal:** Allow version tracking for gating artifacts.

**Schema Addition:**
```json
"version": {
  "type": "string",
  "pattern": "^[0-9]+\\.[0-9]+(\\.[0-9]+)?$",
  "description": "Semantic version for tracking artifact evolution (optional)"
}
```

**Usage:**
- Only meaningful for `is_gating: true` artifacts
- Scripts can validate version compatibility

---

### 1.6 Add Explicit Stage Assignments

**Goal:** All workflows have explicit `stages` with agent assignments.

**Planning workflow currently lacks stages.** Add:
```json
"stages": [
  {"id": "INCUBATION", "name": "Idea Incubation", "agents": ["A-01"]},
  {"id": "REQUIREMENTS", "name": "Requirements Analysis", "agents": ["A-02"]},
  {"id": "ARCHITECTURE", "name": "Architecture & Design", "agents": ["A-03"]},
  {"id": "SECURITY", "name": "Security Review", "agents": ["A-04"]},
  {"id": "INFRASTRUCTURE", "name": "Infrastructure Planning", "agents": ["A-05"]},
  {"id": "DATA", "name": "Data Architecture", "agents": ["A-06"]},
  {"id": "API", "name": "API Design", "agents": ["A-07"]},
  {"id": "UX", "name": "UX Planning", "agents": ["A-08"]},
  {"id": "DEVWORKFLOW", "name": "Dev Workflow", "agents": ["A-09"]},
  {"id": "QA", "name": "QA Strategy", "agents": ["A-10"]},
  {"id": "PRODUCT", "name": "Product Alignment", "agents": ["A-11"]},
  {"id": "SRE", "name": "SRE Planning", "agents": ["A-12"]},
  {"id": "TRANSITION", "name": "Transition Audit", "agents": ["A-13"]},
  {"id": "AUDIT", "name": "Feasibility Audit", "agents": ["A-14"]}
]
```

---

## Phase 2: Canonical Data Updates

After schema changes, update each workflow's data files.

### 2.1 Planning Workflow (`manifests/_canonical/planning/`)

**workflow.json changes:**
1. Add `config` section (copy from deprecated `globals.logging_policy` + `globals.enforcement`)
2. Remove `globals.logging_policy` and `globals.enforcement` (or mark deprecated)
3. Add `stages` array (as shown in 1.6)
4. Ensure no `globals.ui` exists

**artifacts.json changes:**
1. Remove all `"template": null` entries
2. Verify all `owner` values match agent IDs

**agents.json changes:**
1. No changes expected (already correct)

**instructions.json changes:**
1. No changes expected

---

### 2.2 Implementation Workflow (`manifests/_canonical/implementation/`)

**workflow.json changes:**
1. Add `config` section
2. Move `metadata.on_demand.agents` → `pipeline.on_demand`
3. Remove `metadata.on_demand` after migration
4. Remove `globals.ui` if present

**artifacts.json changes:**
1. Remove all `"template": null` entries

---

### 2.3 Research Workflow (`manifests/_canonical/research/`)

**workflow.json changes:**
1. Add `config` section
2. Verify `pipeline.on_demand` is correct (already has on_demand agents there)
3. Remove `globals.ui` if present

**artifacts.json changes:**
1. Remove all `"template": null` entries

---

## Phase 3: Agent Data Quality Review

### 3.1 Agents.json Review Checklist

For each workflow, verify:

| Check | Description |
|-------|-------------|
| ID format | Matches `^[A-Z]{1,2}-[A-Z0-9]{2,6}$` |
| Slug uniqueness | No duplicate slugs |
| Agent type | One of: `core`, `on_demand`, `orchestrator`, `gating` |
| Description | 1-2 sentences, no jargon |
| Produces | All filenames exist in artifacts.json |
| Consumes | All filenames exist in artifacts.json or input_from |

### 3.2 Instructions.json Review Checklist

| Check | Description |
|-------|-------------|
| ID match | Every `id` exists in agents.json |
| Slug match | Slug matches agents.json slug |
| Purpose | Clear, actionable, boundary-aware |
| Responsibilities | 5-10 specific duties |
| Workflow steps | Ordered execution steps |
| Entry/Exit conditions | Clear prerequisites and completion criteria |
| Handoff structure | Uses structured format, not free text |
| Boundaries | In-scope and out-of-scope defined |

### 3.3 Artifacts.json Review Checklist

| Check | Description |
|-------|-------------|
| Filename format | `^[a-z0-9_/]+\.(md\|yaml\|json\|bib)$` |
| Owner | Valid agent ID |
| Category | One of: `core`, `domain`, `reference`, `gating`, `log` |
| Required | Boolean, true for essential artifacts |
| is_gating | Boolean, true for checkpoint blockers |
| is_shared | Boolean, true if multiple agents modify |

---

## Phase 4: Validation Script Enhancement

### 4.1 New Validation Rules to Add

Add these checks to `scripts/validation/validate_canonical.py`:

```python
# 1. Check for deprecated globals usage
def validate_deprecated_globals(workflow_data: Dict, result: ValidationResult):
    """Warn about deprecated globals.logging_policy and globals.enforcement."""
    globals_section = workflow_data.get("globals", {})
    if "logging_policy" in globals_section:
        result.add_warning("workflow.json: globals.logging_policy is deprecated - use config.logging")
    if "enforcement" in globals_section:
        result.add_warning("workflow.json: globals.enforcement is deprecated - use config.enforcement")
    if "ui" in globals_section:
        result.add_warning("workflow.json: globals.ui is deprecated - use display section")

# 2. Check for metadata.on_demand (should be in pipeline)
def validate_on_demand_placement(workflow_data: Dict, result: ValidationResult):
    """Warn if on_demand agents are in metadata instead of pipeline."""
    metadata = workflow_data.get("metadata", {})
    if "on_demand" in metadata:
        result.add_warning("workflow.json: metadata.on_demand should be moved to pipeline.on_demand")

# 3. Check for null template values
def validate_artifact_templates(artifacts_data: Dict, result: ValidationResult):
    """Warn about null template values that should be removed."""
    for artifact in artifacts_data.get("artifacts", []):
        if artifact.get("template") is None and "template" in artifact:
            filename = artifact.get("filename", "?")
            result.add_warning(f"artifacts.json: '{filename}' has template: null - remove field instead")

# 4. Check for missing config section
def validate_config_section(workflow_data: Dict, result: ValidationResult):
    """Check that config section exists with required sub-sections."""
    config = workflow_data.get("config")
    if not config:
        result.add_warning("workflow.json: Missing 'config' section - add enforcement and logging config")
    else:
        if "enforcement" not in config:
            result.add_warning("workflow.json: config.enforcement missing")
        if "logging" not in config:
            result.add_warning("workflow.json: config.logging missing")

# 5. Check stages have agent assignments
def validate_stage_completeness(workflow_data: Dict, agent_ids: Set[str], result: ValidationResult):
    """Ensure all agents are assigned to a stage."""
    stages = workflow_data.get("stages", [])
    if not stages:
        result.add_warning("workflow.json: No stages defined - consider adding explicit stage assignments")
        return
    
    assigned_agents = set()
    for stage in stages:
        assigned_agents.update(stage.get("agents", []))
    
    pipeline_order = set(workflow_data.get("pipeline", {}).get("order", []))
    unassigned = pipeline_order - assigned_agents
    if unassigned:
        result.add_warning(f"workflow.json: Agents not assigned to any stage: {', '.join(sorted(unassigned))}")
```

### 4.2 Enhanced CLI Options

Add to `validate_canonical.py`:

```python
parser.add_argument('--strict', action='store_true', 
                    help='Treat warnings as errors')
parser.add_argument('--fix-suggestions', action='store_true',
                    help='Show suggested fixes for common issues')
parser.add_argument('--output', '-o', choices=['text', 'json'],
                    default='text', help='Output format')
```

### 4.3 JSON Output for CI Integration

```python
def output_json(results: List[ValidationResult]):
    """Output results as JSON for CI/CD integration."""
    output = {
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed)
        },
        "workflows": {}
    }
    for r in results:
        output["workflows"][r.workflow] = {
            "passed": r.passed,
            "errors": r.errors,
            "warnings": r.warnings,
            "info": r.info
        }
    print(json.dumps(output, indent=2))
```

---

## Phase 5: Documentation

### 5.1 Create `manifests/README.md` (Definitive Version)

Replace existing README with comprehensive documentation covering:
- File structure and ownership
- Schema overview
- Data editing workflow
- Validation commands
- CI integration example

See separate file: `MANIFEST_README_TEMPLATE.md`

### 5.2 Create `manifests/_canonical/README.md`

Focus on:
- Canonical JSON as source of truth
- Data relationships diagram
- Cross-reference rules
- Common edit patterns

---

## Execution Checklist

Use this checklist to track progress:

### Phase 1: Schema
- [ ] 1.1 Add `config` section to workflow.schema.json
- [ ] 1.1 Mark `globals.logging_policy` and `globals.enforcement` as deprecated
- [ ] 1.2 Remove `globals.ui` from workflow.schema.json
- [ ] 1.2 Ensure `display` has all UI properties
- [ ] 1.3 Verify `pipeline.on_demand` exists in schema
- [ ] 1.4 Update `template` field description (make optional, no null)
- [ ] 1.5 Add `version` field to artifacts.schema.json (optional)
- [ ] 1.6 Update stages schema to require agent assignments

### Phase 2: Data
- [ ] 2.1 Update planning/workflow.json
- [ ] 2.1 Update planning/artifacts.json (remove template: null)
- [ ] 2.2 Update implementation/workflow.json (move on_demand)
- [ ] 2.2 Update implementation/artifacts.json
- [ ] 2.3 Update research/workflow.json
- [ ] 2.3 Update research/artifacts.json

### Phase 3: Quality
- [ ] 3.1 Review all agents.json files
- [ ] 3.2 Review all instructions.json files
- [ ] 3.3 Review all artifacts.json files

### Phase 4: Validation
- [ ] 4.1 Add deprecated globals check
- [ ] 4.1 Add on_demand placement check
- [ ] 4.1 Add null template check
- [ ] 4.1 Add config section check
- [ ] 4.1 Add stage completeness check
- [ ] 4.2 Add CLI options (--strict, --fix-suggestions, --output)
- [ ] 4.3 Add JSON output format

### Phase 5: Documentation
- [ ] 5.1 Update manifests/README.md
- [ ] 5.2 Create manifests/_canonical/README.md
- [ ] Archive this plan as completed ADR

---

## Risk Mitigation

1. **Backup before changes:** Copy `manifests/_canonical/` before editing
2. **Validate after each file:** Run `python3 -m scripts.validation.validate_canonical --workflow <name>` after each change
3. **Incremental commits:** Commit after each phase
4. **Test generation:** After data changes, test that agent file generation still works

---

## Next Document

See `SCHEMA_MIGRATION_AGENT_PROMPT.md` for the agent execution instructions.
