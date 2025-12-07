# Integrated Canonical Schema Report — v2.x

**Date:** 2025-12-05
**Status:** Consolidated (canonical + migration + validation)

Overview

- Purpose: consolidate the trimmed specification, consolidated change summary, and current schema status into a single authoritative reference for the canonical JSON manifests and migration results. This report also captures the most recent validation outputs, gaps, and recommended next actions (regeneration, CI, cross-file checks).
- Scope: schemas under `manifests/_canonical_schemas/` and canonical manifests under `manifests/_canonical/<workflow>/` (planning, implementation, research, workflow-creation).

1. Executive Summary

- Canonical-first approach adopted: JSON manifests in `manifests/_canonical/` are authoritative; YAML and agent-facing files are derived by generation scripts.
- Key schema improvements (v2.x): structured `handoff` in `instructions.schema.json`, `return_to_caller` conditional, expanded `workflow.schema.json` with `globals.logging_policy`, `globals.enforcement`, checkpoint expansions (`owner`, `validation_command`, `bypass_policy`, `required_artifacts`, `required_logs`, `timeout_seconds`), UI/display hints, and definitions (`logEntry`, `bypassPolicy`, `artifactMatch`).
- Migration status: planning, implementation, research, and workflow-creation canonical workflows migrated and validated successfully against `workflow.schema.json` (validator returned empty error lists for all four workflows).
- Immediate next steps: regenerate derived YAML/agent files from canonical JSON, add a CI gate running `scripts/validation/validate_canonical.py`, and optionally add cross-file existence checks in CI.

2. Current Schema & Manifest Status (detailed)

- Schemas (location: `manifests/_canonical_schemas/`)
  - `agents.schema.json` — CURRENT
    - Enforces `id`, `slug`, `role`, `agent_type` and `produces`/`consumes` shapes. Agent ID pattern: `^[A-Z]{1,2}-[A-Z0-9]{2,6}$`.
  - `artifacts.schema.json` — CURRENT
    - Enforces `filename` (primary), `owner` (agent ID), and `category` (`core`, `domain`, `reference`, `gating`, `log`).
  - `instructions.schema.json` — CURRENT
    - `instructions[].id` must match an agent ID; `slug` required. `handoff` is structured with `next` (array or null), `required_artifacts`, `required_logs`, `notes`; `return_to_caller: true` requires `next: null` (schema `if`/`then` enforced).
  - `workflow.schema.json` — CURRENT
    - Provides `pipeline` with `order`, `stages`, `cycles`, `checkpoints[]`, `globals`, and `cli` guidance. Checkpoints now include `gating`, `required_artifacts`, `required_logs`, `bypass_policy`, `owner`, `validation_command`, and `timeout_seconds`.

- Canonical manifests migrated and validation status (per workflow)
  - `planning`: all canonical files migrated; validation PASS.
  - `implementation`: migrated; validation PASS.
  - `research`: migrated; validation PASS.
  - `workflow-creation`: migrated; validation PASS.

- Key changes applied across manifests
  - Structured `handoff` objects replaced free-text handoffs where helpful; `return_to_caller` semantics enforced.
  - Checkpoint `owner` fields normalized to agent IDs (e.g., `A-00`, `I-03`).
  - `validation_command` standardized to CLI invocations (e.g., `./workflow validate-checkpoint --after-agent I-03 --check unit_tests_pass`) or empty string when no command is used.
  - `bypassPolicy.retention_days` removed; `bypassPolicy.allowed_roles` constrained to canonical agent ID format.
  - `globals.logging_policy` and `globals.enforcement` added to `workflow.json` to support deterministic gating and logging.

3. Validation Summary & Evidence

- Validation tooling: `scripts/validation/validate_canonical.py` using Python + `jsonschema` (Draft-07). The validator performs schema validation and cross-file referential checks (pipeline order, artifact owners, produces/consumes existence, instruction IDs vs agents, cycles).

- Recent validator run (aggregated result):

```
{
  "_canonical/planning/workflow.json": [],
  "_canonical/implementation/workflow.json": [],
  "_canonical/research/workflow.json": [],
  "_canonical/workflow-creation/workflow.json": []
}
```

- Interpretation: no schema errors were reported for any of the four canonical workflow JSON files after the v2.x schema changes and manifest normalization.

4. Files Changed & Migration Actions (concise)

- Schemas updated:
  - `manifests/_canonical_schemas/instructions.schema.json` — added structured `handoff` and `return_to_caller` conditional.
  - `manifests/_canonical_schemas/workflow.schema.json` — added `globals.logging_policy`, `globals.enforcement`, checkpoint expansions, UI hints, and definitions (`logEntry`, `bypassPolicy`, `artifactMatch`).

- Canonical manifests normalized (not exhaustive list):
  - `manifests/_canonical/planning/workflow.json` — added checkpoint gating fields, owners to agent IDs, CLI `validation_command`s, removed `retention_days`.
  - `manifests/_canonical/implementation/workflow.json` — checkpoint owners added, validation commands and timeouts added.
  - `manifests/_canonical/research/workflow.json` — owners and validation commands standardized.
  - `manifests/_canonical/workflow-creation/workflow.json` — owner and final verification CLI `validation_command` added.

- Documentation trimmed and consolidated:
  - `manifests/_canonical/CANONICAL_SCHEMA_SPECIFICATION.md` — trimmed to actionable guidance.
  - `manifests/_canonical/CONSOLIDATED_CHANGE_SUMMARY.md` — records the key schema changes and migration notes.
  - `manifests/_canonical/CURRENT_SCHEMA_STATUS.md` — snapshot of validation and migration state.

5. Architecture & Pipeline (diagrams)

- Canonical → Validate → Generate flow (ASCII diagram):

```
CANONICAL JSON (manifests/_canonical/<workflow>/)
  ├─ workflow.json
  ├─ agents.json
  ├─ artifacts.json
  └─ instructions.json
         │
         ▼
  VALIDATE (jsonschema + cross-file checks)
         │
         ▼
  GENERATE (scripts/generation/*.py)
  ├─ manifests/workflows/<workflow>/*.yaml
  └─ agent_files/<workflow>/*.md
```

- Checkpoint lifecycle (simplified):

```
[Agent X finishes step] → [Checkpoint defined in workflow.json triggers]
  Checkpoint fields:
    - after_agent: Agent X
    - gating: strict|warn|none
    - required_artifacts: [file1, file2]
    - required_logs: [session, decision]
    - bypass_policy: {allowed_roles: [A-03], audit_required: true}
    - owner: Agent Y (agent ID)
    - validation_command: ./workflow validate-checkpoint --after-agent X --check ...
    - timeout_seconds: 86400
  → If gating == strict, CLI runs validation_command and blocks progress on failure.
```

6. Cross-file Referential Rules (enforced)

- `workflow.pipeline.order` items must exist in `agents.json` for that workflow.
- All `artifacts[].owner` values must be valid `agents.json` IDs.
- `agents[].produces` and `agents[].consumes` entries must reference filenames in `artifacts.json` or be declared as cross-workflow `input_from` entries.
- `instructions[].id` must match an agent ID from `agents.json` and `slug` must exist.
- Uniqueness constraints: agent IDs, slugs, artifact filenames, instruction IDs.

7. Known Gaps, Residual Work & New Updates (beyond attached docs)

- Regeneration of Derived Files (pending):
  - The canonical -> YAML/agent generation has not been executed after the final canonical edits. Derived files under `manifests/workflows/<workflow>/` should be regenerated.
  - Recommended command (run after validation):

```bash
python3 scripts/generation/generate_workflow_files.py --all
# or, for a single workflow:
python3 scripts/generation/generate_workflow_files.py --workflow planning
```

- CI Integration (recommended, not yet present):
  - Add a CI job that runs `scripts/validation/validate_canonical.py` (fail on schema or cross-file errors). Example GitHub Actions snippet:

```yaml
name: Validate Canonical Manifests
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install deps
        run: python -m pip install --upgrade pip && pip install jsonschema
      - name: Run validator
        run: python3 scripts/validation/validate_canonical.py --all
```

- Cross-file existence CI step (optional enhancement):
  - Enforce that `owner` and `allowed_roles` refer to IDs present in `agents.json` across workflows. If your validator already checks this, include it in CI.

- Standardize `validation_command` (optional):
  - Right now `validation_command` is a string CLI invocation. Consider formalizing it into an object to capture structured outputs, e.g.:

```json
"validation_command": {
  "cmd": "./workflow validate-checkpoint --after-agent I-03 --check unit_tests_pass",
  "report_path": "reports/I-03-validation.json",
  "success_codes": [0]
}
```

This would make automated report collection easier for the generator and runner.

- Backstop cross-workflow checks (recommended):
  - Add a global check ensuring `input_from` references point to existing workflows and exported artifact names.

8. Migration Notes & Developer Checklist

- If editing canonical manifests, follow this sequence:
  1. Edit JSON in `manifests/_canonical/<workflow>/` (not YAML).
  2. Run validator locally: `python3 scripts/validation/validate_canonical.py --workflow <workflow>` or `--all`.
  3. Fix issues until validator reports no errors.
  4. Run generator: `python3 scripts/generation/generate_workflow_files.py --workflow <workflow>`.
  5. Review generated YAML/agent files and commit.

- Common migration fixes (already applied in v2.x):
  - Replace free-text `owner` values with canonical agent IDs.
  - Convert `handoff.next` free-text entries to structured objects or `null` when `return_to_caller: true`.
  - Ensure every artifact has a `category` and a valid `owner`.
  - Remove `retention_days` from `bypassPolicy`.

9. Action Plan & Priorities (recommended ordering)

- High (immediate):
  - Regenerate derived YAML and agent files for all migrated workflows and commit the results.
  - Add the validator to CI to prevent further schema drift.

- Medium:
  - Add cross-workflow existence checks to the validator (if not already present), ensuring `owner`/`allowed_roles` reference live agent IDs across workflows.
  - Formalize `validation_command` into a structured object for better reporting.

- Low:
  - Provide a small library or CLI `workflow` binary that implements `validate-checkpoint` and returns structured JSON reports for the generator to consume.

10. Quick Commands & Examples

- Validate all canonical manifests (local):

```bash
python3 scripts/validation/validate_canonical.py --all
```

- Validate a single workflow:

```bash
python3 scripts/validation/validate_canonical.py --workflow planning
```

- Regenerate derived YAML for all workflows:

```bash
python3 scripts/generation/generate_workflow_files.py --all
```

11. Annex: Change Log Highlights (human-friendly bullet list)

- Added structured `handoff` and schema conditional preventing `return_to_caller` contradictions.
- Expanded `workflow.schema.json` with checkpoint gating and logging policy fields.
- Normalized `owner` and `bypassPolicy.allowed_roles` to canonical agent ID format.
- Replaced ad-hoc validation scripts in manifests with CLI-style `validation_command` entries.
- Trimmed the canonical schema specification doc to essential guidance.
- Completed migration and validation for planning, implementation, research, and workflow-creation workflows.

12. Contact & Ownership

- Canonical files are the source-of-truth. For edits, coordinate with the schema owners (see `agents.json` orchestrator entries). The `A-00` orchestrator and owner agents should be used as primary reviewers for pipeline and checkpoint gating changes.

---
