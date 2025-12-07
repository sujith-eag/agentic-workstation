# Consolidated Change Summary — Canonical Schemas (v2.x)

**Date:** 2025-12-04
**Scope:** Consolidation of key changes applied across `workflow.json`, `agents.json`, `artifacts.json`, and `instructions.json` as part of the recent schema refactor.

---

## Purpose

This document captures the essential reasons for the refactor, what changed, and the expected impacts and migration guidance — condensed from the detailed reports in `_canonical`.

## Why the refactor was done

- Reduce redundancy and schema drift by establishing a single source of truth: the JSON canonical manifests in `manifests/_canonical/<workflow>/`.
- Make programmatic validation and CI enforcement reliable by moving to schema-first JSON (draft-07) with cross-file referential checks.
- Simplify human workflows by deriving YAML and agent-facing files from validated JSON rather than editing many divergent sources.
- Improve interoperability across workflows (planning, implementation, research, workflow-creation) with consistent ID, slug, and filename patterns.

## High-level design decisions (short)

- JSON-first canonical store (authoritative). YAML and agent files are derived/generated.
- Each canonical JSON file owns a single responsibility:
  - `workflow.json`: orchestration, pipeline, stages, cycles, global rules
  - `agents.json`: agent identity and I/O contracts (produces/consumes)
  - `artifacts.json`: artifact registry and authoritative ownership
  - `instructions.json`: agent behavioral guidance (advisory, not authoritative for ownership)
- Minimal required fields: schemas require only what is necessary for programmatic correctness.
- Cross-reference validation rules enforce integrity between files (IDs, filenames, owners).

## Key concrete schema changes

1. Agent ID and slug normalization
   - Enforced pattern: `^[A-Z]{1,2}-[A-Z0-9]{2,6}$` (e.g., `A-00`, `I-SEC`) for `agents[].id` and authoritative `owner` fields.
   - Slugs standardized to `^[a-z][a-z0-9_]*$` (underscore_separated lower-case).

2. Flattened produces/consumes
   - `agents.json` uses flat `produces: []` and `consumes: []` arrays for simple cases (schemata allow categorized arrays where helpful), removing nested redundant ownership fields previously embedded across files.

3. Centralized artifact ownership
   - `artifacts.json` is authoritative for `filename` → `owner` mapping. `instructions.json` ownership fields are advisory only and will be removed during migration.
   - `artifacts` entries now require a `category` enum: `core`, `domain`, `reference`, `gating`, `log`.

4. Consumes item extended shape
   - Consume entries allow either a string (local required) or an object `{ file, required, from_workflow }`, enabling optional or cross-workflow references in a normalized way.

5. Pipeline and stage consolidation
   - `workflow.json.pipeline` is an object containing `order`, `on_demand`, `parallel_groups`, `allow_skip`, and `allow_parallel` — keeping orchestration centralized.
   - `stages` include `agents` arrays to record stage assignments (not held in agents.json).

6. Checkpoints standardized
   - Checkpoint types normalized to `human`, `gate`, `validation`.

7. Schema improvements and stricter validation
   - JSON Schemas updated for required fields, patterns, and additionalProperties=false in places where drift must be prevented.
   - Cross-file validators implemented (see `validate_canonical.py`) for: pipeline order, artifact owners, produces/consumes existence, slug consistency, cycle references, and circular dependency detection.

8. Structured handoff in `instructions.json`
   - Added an optional structured `handoff` object to `instructions.json` to make handoffs machine-readable for CLI enforcement and template rendering.
   - Shape: `next` (array of `{id, role, stage}`) or `null`, plus `required_artifacts`, `required_logs`, and `notes`.
   - Reasoning: enables automated gating, clearer handoff prerequisites, and reduces brittle free-text parsing in generators and the CLI.

9. Workflow-level logging, enforcement, and checkpoint expansion
   - Purpose: Provide machine-enforceable logging and gating policy at the workflow level so the CLI/runner can make deterministic decisions about handoffs and checkpoints.
   - Changes:
      - Added `globals.logging_policy` with booleans controlling required logs and artifact tracking.
      - Added `globals.enforcement` with global `checkpoint_gating` and `handoff_gating` settings and `globals.enforcement_mode` for rollout compatibility.
      - Expanded `checkpoints[]` to include `gating`, `required_artifacts`, `required_logs`, `bypass_policy`, `owner`, `validation_command`, and `timeout_seconds`.
      - Added schema `definitions`: `logEntry`, `bypassPolicy`, and `artifactMatch` to support structured validation and migration.
   - Impact: Enables CLI gating, bypass auditing, and automated checkpoint validation scripts; reduces ambiguity in handoff/approval semantics.

9. Return-to-caller conditional in `instructions.schema.json`
   - Purpose: Prevent contradictory handoff records where `return_to_caller: true` is paired with a non-null `next` list.
   - Change: Added an `if`/`then` JSON Schema conditional so `return_to_caller: true` requires `next: null` for `handoff` objects.
   - Impact: Makes the caller-return semantic machine-enforceable, preventing generator/CLI logic errors and simplifying migration of legacy "return to caller" free-text markers.

10. UI/display hints in `workflow.schema.json`
   - Purpose: Provide optional UI hints so frontends and templates can prioritize fields and stage ordering without changing functional schema behavior.
   - Change: Added `globals.ui` (optional) with `name`, `stage_order`, and `frontmatter_fields`, and extended top-level `display` with the same fields.
   - Impact: Enables UIs and template renderers to consume standardized display preferences (Layer 1 frontmatter guidance) while keeping them optional to preserve backward compatibility.

## Immediate fixes applied (summary)

- Added missing orchestrator (`A-00`) instructions where absent.
- Fixed slug/id mismatches (several instructions entries updated to match agents.json).
- Resolved duplicate `A-06` entries in instructions and corrected adjacent IDs.
- Added `category` to artifacts schema and flagged missing categories in manifests.

(For detailed file-level diffs and the complete chronology, see `PHASE_1_COMPLETION.md` and `DATA_STANDARDIZATION_REPORT.md`.)

## Post-migration updates

- `research` and `workflow-creation` canonical workflows were migrated and brought into compliance with the v2.x schema.
- Checkpoint fields standardized across all workflows: `owner` now references agent IDs, `validation_command` uses CLI-style invocations (or empty string), and `timeout_seconds` added.
- `bypassPolicy.retention_days` was removed and `bypassPolicy.allowed_roles` now follows the canonical agent ID pattern aligned with `agents.schema.json`.
- All four canonical workflows validate successfully against `workflow.schema.json` after these changes.

## Expected impacts

- Tools and scripts (`validate_canonical.py`, `generate_yaml.py`) can reliably validate and generate derived outputs; CI can fail fast on schema violations.
- Migration reduces maintenance cost: only canonical JSON needs authoritative edits; generated YAML keeps editors happy.
- Consumers of manifests (scaffolding, generators, agent-runner) must rely on the canonical JSON shapes rather than ad-hoc YAML conventions.

## Migration highlights / developer notes

- If you edit manifests, edit `manifests/_canonical/<workflow>/*.json` and run validation. Use the generator to refresh YAML and agent files.
- To convert older artifacts with `consumes_optional` or nested `produces: { core: [...] }`, run the migration tool (`migrate_to_canonical.py`) or follow these manual steps:
  - Convert `consumes_optional` entries into `consumes` objects with `required: false`.
  - Flatten nested `produces` to a single array or to categorized arrays that match the schema's `produceCategory` definition.
  - Ensure every artifact has a `category` and a valid `owner` that matches an `agents.json` id.

## Quick action checklist (top priorities)

- Ensure all agents use canonical ID format (A-00 style) and unique slugs. (High)
- Ensure `artifacts.json` entries include `category` (High)
- Remove or mark deprecated `ownership` and `inputs/outputs` in `instructions.json` (Medium)
- Run full validation across workflows and fix reported issues before committing (High)

---

## Where to look next

- `PHASE_1_COMPLETION.md` — what was implemented and validation summary.
- `DATA_STANDARDIZATION_REPORT.md` — rationale, divergence analysis, and recommended architecture.
- `_canonical_schemas/*` — authoritative schema definitions.

