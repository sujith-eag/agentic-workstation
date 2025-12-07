# Current Schema & Implementation Status — Canonical Schemas

**Date:** 2025-12-04
**Context:** Snapshot describing the current shape and validation status of the canonical JSON schemas and the manifest files migrated so far.

---

## Overall validation status

- Phase 1 completed: canonical JSON schemas implemented and planning + implementation workflows migrated to canonical format (see `PHASE_1_COMPLETION.md`).
- Validator `validate_canonical.py` has been extended to run cross-file checks (IDs, filenames, owners, cycles).
- Migration work for `research` and `workflow-creation` completed; all four canonical workflows now validate against the updated schemas.

## Schema files (location: `manifests/_canonical_schemas/`)

- `agents.schema.json` — CURRENT
  - Enforces: `agents` array with required `id`, `slug`, `role`.
  - Pattern: `id` matches `^[A-Z]{1,2}-[A-Z0-9]{2,6}$`.
  - Allows `produces`/`consumes` arrays; consumption items can be strings or objects with `file`, `required`, `from_workflow`.
  - `agent_type` enum present: [`core`, `on_demand`, `orchestrator`, `gating`].
  - Status: Implemented and applied to migrated workflows.

- `artifacts.schema.json` — CURRENT
  - Enforces `filename` (primary key), `owner` (agent ID), and required `category` enum: `core`, `domain`, `reference`, `gating`, `log`.
  - Supports `type` (`file` | `directory`), `is_shared`, `is_gating`, `required`, `template`, `sections`.
  - Status: Implemented; some artifacts in non-migrated workflows still missing `category` values (validation failures expected until migration finishes).

- `instructions.schema.json` — CURRENT
  - Enforces `instructions` array; `id` must match agent ID and `slug` is required.
  - Behavioral fields (`purpose`, `responsibilities`, `workflow`, `boundaries`, `handoff`) present.
  - Deprecated ownership/explicit I/O removed or marked advisory; `explicit_io`/`derived` flags allowed for migration signals.
  - Status: Implemented; historical files may contain advisory/duplicated ownership fields that should be removed or ignored.
  - Note: `handoff` was recently extended to a structured form to support automation: `next` (array of `{id,role,stage}`) or `null`, optional `required_artifacts`, `required_logs`, and `notes`. This allows CLI gating and template rendering to avoid fragile free-text parsing.

- `workflow.schema.json` — CURRENT
  - Enforces `name`, `display_name`, and `pipeline` object with required `order`.
  - Supports `stages` (with `agents` arrays), `cycles`, `input_from`, `directories`, `checkpoints`, `globals`, `display`, and `cli`.
  - Checkpoint types normalized to `human`, `gate`, `validation`.
  - Status: Implemented and used by migrated workflows.

  - Recent additions (v2.x):
    - `globals.logging_policy`: controls which logs/artifact tracking are required (session, decision, assumption, handoff, artifact tracking).
    - `globals.enforcement` and `globals.enforcement_mode`: global gating defaults (`strict|warn|none`) and rollout/compatibility mode (`enforce|compat_warn|report_only`).
    - `globals.feature_flags`: optional flags for gradual rollouts.
    - Expanded `checkpoints[]` schema: `gating`, `required_artifacts`, `required_logs`, `bypass_policy`, `owner`, `validation_command`, `timeout_seconds`.
    - New `definitions`: `logEntry`, `bypassPolicy`, and `artifactMatch` to support structured validation of logs, bypass audits, and artifact matching rules.

  - Validation: After these updates all four canonical `workflow.json` files validate successfully against the updated schema.

## Migration & manifest status (per workflow)

- Planning (manifests/_canonical/planning/)
  - `agents.json`: migrated, IDs hyphenated, slugs normalized.
  - `artifacts.json`: migrated; artifacts categorized; owners validated.
  - `instructions.json`: migrated; missing orchestrator added; slug mismatches corrected.
  - `workflow.json`: migrated to `pipeline` object form with `order` and `stages`.
  - Validation: PASS (planning)

- Implementation (manifests/_canonical/implementation/)
  - `agents.json`, `artifacts.json`, `instructions.json`, `workflow.json` migrated.
  - Validation: PASS (implementation)

- Research (manifests/_canonical/research/)
  - Migrated to canonical shape; checkpoint `owner` and `validation_command` fields standardized.
  - Validation: PASS (research)

- Workflow-creation (manifests/_canonical/workflow-creation/)
  - Migrated to canonical shape; final verification checkpoint uses the CLI-style `validation_command`.
  - Validation: PASS (workflow-creation)

## Tooling & validators (present)

- `scripts/validation/validate_canonical.py` (enhanced)
  - Schema validation for all files against the JSON Schemas.
  - Cross-file checks:
    - `workflow.pipeline.order` items exist in `agents.json`.
    - `artifacts[].owner` exists in `agents.json`.
    - All `produces`/`consumes` artifact filenames exist in `artifacts.json` or `input_from`.
    - `instructions[].id` and `slug` consistency with agents.
    - `workflow.cycles` references validity.
  - Circular dependency detection for agent dependency graphs.

- Generation scripts (planned/partial):
  - `generate_yaml.py` — generate human-readable YAML from canonical JSON with comments.
  - `generate_agent_files.py` — produce agent markdowns from canonical data + templates.

## Known gaps and remaining work

- (Completed) All canonical workflows migrated. If you add or change canonical JSON, run validation and regenerate derived YAML.
- Remove redundant ownership and explicit I/O fields from `instructions.json` in non-migrated files.
- Add `category` to orphan artifacts in the remaining workflows.
- Add CI step to run `validate_canonical.py` and fail on ERRORs.
- Add `migrate_to_canonical.py` (or run the migration script) to convert legacy YAML automatically and produce a diff report.

## Recommended next steps (short)

1. Run validator for all workflows and capture failures:
   ```bash
   python3 -m scripts.validation.validate_canonical --all
   ```
2. Migrate `research` and `workflow-creation` using `migrate_to_canonical.py` or the step checklist in `STANDARDIZATION_PLAN.md`.
3. Fix any remaining slug/id mismatches and ensure every artifact has `category` and valid `owner`.
4. Add the validator as a CI gate and require validation success before merging canonical JSON changes.
5. Use `generate_yaml.py` to produce the derived human-readable YAML for editors after validation completes.

---

## Quick reference (where things live)

- Schemas: `manifests/_canonical_schemas/*.json`
- Canonical manifests: `manifests/_canonical/<workflow>/*.json`
- Derived YAML (generated): `manifests/workflows/<workflow>/*.yaml`
- Validation script: `scripts/validation/validate_canonical.py`

