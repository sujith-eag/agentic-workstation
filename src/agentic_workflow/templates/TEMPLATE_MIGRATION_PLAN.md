# Template Migration Plan

**Phase 2 Execution | Status:** In Progress  
**Objective:** Complete migration from `.tpl` to `.j2` Jinja2 templates

> NOTE: Commits and direct repository modifications will be handled by the repository maintainer. Follow the steps to prepare changes, but do not run `git commit` or `git push` from an automated agent.

---

## Overview

This plan migrates all 23 remaining `.tpl` templates to Jinja2 format and removes legacy code paths. The migration is structured in 4 phases with validation gates.

## Current Progress (Summary)


**Notes:**
- Where possible, `jinja2` templates (`.j2`) were migrated for global templates. The primary remaining surface is workflow-specific `.tpl` under `manifests/workflows/` for prompt and artifact templates.
---

## Phase 0: Cleanup (Immediate)

**Duration:** 30 minutes  
**Risk:** LOW  
**Prerequisites:** None

### Tasks

#### 0.1 Delete Deprecated Templates

Remove already-deprecated files:

```bash
rm -rf templates/_deprecated/
```

Files to be deleted:
- `_deprecated/prompts/agent_body.md.tpl`
- `_deprecated/prompts/orchestrator_body.md.tpl`
- `_deprecated/project_index.md.tpl`
- `_deprecated/agent_context_index.md.tpl`
- `_deprecated/workflow_config.yaml.tpl`

#### 0.2 Remove Duplicate Global Templates

Delete `.tpl` files that have `.j2` equivalents:

```bash
# These have .j2 replacements
rm templates/docs/copilot-instructions.md.tpl
rm templates/docs/GEMINI.md.tpl
rm templates/docs/GOVERNANCE_GUIDE.md.tpl
rm templates/logs/exchange_log.md.tpl
rm templates/logs/context_log.md.tpl
```

#### Validation Gate 0

```bash
# Verify .j2 files still exist
ls templates/docs/*.j2
ls templates/logs/*.j2

# Run tests
python -m pytest tests/ -v
```

---

## Phase 1: Core Global Templates

**Duration:** 2 hours  
**Risk:** MEDIUM  
**Prerequisites:** Phase 0 complete

### Tasks

#### 1.1 Convert `active_session.md.tpl`

**Current:** `templates/active_session.md.tpl` (34 lines)
**Target:** `templates/_base/session_base.md.j2` (already exists - verify coverage)

The existing `session_base.md.j2` should replace `active_session.md.tpl`. Need to update:

Steps:
1. Create `templates/docs/CLI_REFERENCE.md.j2` from `.tpl` content
2. Replace `{{command_table}}` with Jinja2 loop:
   ```jinja2
   {% for cmd in commands %}
   | {{ cmd.name }} | {{ cmd.syntax }} | {{ cmd.description }} |
   {% endfor %}
   ```
3. Update `scripts/generators/docs.py` to use Jinja2 loader
4. Delete `.tpl` file

#### 1.3 Convert `GOVERNANCE_BASE.md.tpl`

**Current:** `templates/docs/GOVERNANCE_BASE.md.tpl`
**Target:** Merge into `GOVERNANCE_GUIDE.md.j2` or create separate partial

Review if this is distinct from `GOVERNANCE_GUIDE.md.j2`. If redundant, delete. If needed, convert.

This is a shell script wrapper, not a template engine file. Keep as-is but consider renaming to `workflow.sh.tpl` for clarity.

### Validation Gate 1

```bash
# Run full test suite
# Test project initialization
python -m scripts.cli.workflow init test_phase1 --workflow planning
cd projects/test_phase1
./workflow status
./workflow activate A-01

# Verify active_session.md was generated correctly
head -50 active_session.md
```

---

## Phase 2: Workflow Prompt Templates

**Duration:** 3 hours  
**Risk:** MEDIUM-HIGH  
**Prerequisites:** Phase 1 complete

### Tasks

#### 2.1 Implementation Workflow Prompts — COMPLETED
`manifests/workflows/implementation/templates/prompts/agent_body.md.j2`
`manifests/workflows/implementation/templates/prompts/orchestrator_body.md.j2`
5. Test rendering with `jinja_loader.py` — PASS
6. Mark legacy `.tpl` files as deprecated and remove references; retired `.tpl` files are moved to `_deprecated/`.

**Conversion Pattern:**

1. Copy file with `.j2` extension
2. Convert `{{variable}}` to `{{ variable }}`
3. Convert lists to Jinja2 loops:
   ```jinja2
   {# Old: {{produces_list}} #}
   {% for artifact in produces.core %}
   - `{{ artifact.filename }}` — {{ artifact.description }}
   {% endfor %}
   ```
4. Test rendering with `jinja_loader.py`
5. Delete `.tpl` file

#### 2.2 Research Workflow Prompts — COMPLETED

**Files:**
- `manifests/workflows/research/templates/prompts/agent_header.md.tpl`
- `manifests/workflows/research/templates/prompts/agent_body.md.tpl`

Same conversion pattern as 2.1.

#### 2.3 Workflow-Creation Workflow Prompts — COMPLETED

**Files:**
- `manifests/workflows/workflow-creation/templates/prompts/agent_header.md.tpl`
- `manifests/workflows/workflow-creation/templates/prompts/agent_body.md.tpl`

Same conversion pattern as 2.1.

### Validation Gate 2

```bash
# Test each workflow
for wf in implementation research workflow-creation; do
    python -m scripts.cli.workflow init "test_${wf}" --workflow $wf
    cd projects/test_${wf}
    ./workflow status
    ./workflow activate $(./workflow status | grep "First agent" | awk '{print $NF}')
    cd ../..
done

# Run tests
python -m pytest tests/ -v

> Progress: Workflow prompt templates — `implementation`, `research`, and `workflow-creation` now use Jinja `.j2` templates; legacy `.tpl` files have been deprecated and consolidated under `_deprecated/`.
```

---

## Phase 3: Artifact Templates

**Duration:** 2 hours  
**Risk:** LOW  
**Prerequisites:** Phase 2 complete

### Tasks

#### 3.1 Planning Workflow Artifacts

**Files:**
- `manifests/workflows/planning/templates/artifacts/requirements_spec.md.tpl`
- `manifests/workflows/planning/templates/artifacts/api_specifications.md.tpl`
- `manifests/workflows/planning/templates/artifacts/architecture_overview.md.tpl`

**Note:** These are boilerplate templates, not dynamically rendered. Options:
1. Keep as static `.md` files (remove `.tpl` extension)
2. Convert to `.j2` with variable sections for future use

**Recommendation:** Convert to `.j2` for consistency, even if currently static.

#### 3.2 Implementation Workflow Artifacts

**Files:**
- `manifests/workflows/implementation/templates/artifacts/sprint_backlog.md.tpl`
- `manifests/workflows/implementation/templates/artifacts/test_suite_manifest.md.tpl`
- `manifests/workflows/implementation/templates/artifacts/verification_report.md.tpl`
- `manifests/workflows/implementation/templates/artifacts/observability_manifest.md.tpl`

Same approach as 3.1.

#### 3.3 Log Templates

**File:**
- `manifests/workflows/implementation/templates/logs/tdd_cycle_log.md.tpl`

Convert to `.j2` format.

### Validation Gate 3

```bash
# Verify all .tpl files are gone
find manifests/workflows -name "*.tpl" -type f

# Should return empty

# Run full test suite
python -m pytest tests/ -v

> Progress: Artifact templates — several `.tpl` files remain under `manifests/workflows/*/templates/artifacts`; recommended approach is to convert to `.j2` or, if static, rename to `.md`.
```

---

## Phase 4: Generator Cleanup

**Duration:** 2 hours  
**Risk:** MEDIUM  
**Prerequisites:** Phase 3 complete

### Tasks

#### 4.1 Remove Legacy Generator Code

**File:** `scripts/generation/generate_agents.py`

Remove:
- `generate_agents_for_workflow()` function (legacy regex path)
- Any `--jinja2` flag handling (make Jinja2 the only path)

Keep:
- `generate_agents_jinja2()` → rename to `generate_agents()`

#### 4.2 Update `docs.py`

**File:** `scripts/generators/docs.py`

Refactor:
- `generate_cli_reference()` to use `JinjaTemplateLoader`
- `generate_agent_pipeline()` to use `JinjaTemplateLoader`

Remove:
- Any regex-based template substitution

#### 4.3 Update Imports

Search and replace any calls to old functions:

```bash
grep -r "generate_agents_for_workflow" scripts/
```

Update all callsites.

### Validation Gate 4

```bash
# Full validation
python -m pytest tests/ -v

# Smoke test all workflows
for wf in planning implementation research workflow-creation; do
    python -m scripts.cli.workflow init "final_test_${wf}" --workflow $wf
    cd projects/final_test_${wf}
    ./workflow status
    cd ../..
done

# Verify no .tpl files remain (except workflow.tpl)
find . -name "*.tpl" -type f | grep -v "workflow.tpl"
# Should be empty
```

---

## Rollback Procedures

### Phase 0-1 Rollback

```bash
git checkout HEAD -- templates/
```

### Phase 2-3 Rollback

```bash
git checkout HEAD -- manifests/workflows/*/templates/
```

### Phase 4 Rollback

```bash
git checkout HEAD -- scripts/
```

---

## Migration Checklist

### Phase 0: Cleanup
- [x] Delete `templates/_deprecated/` directory
- [x] Delete duplicate `.tpl` files (docs, logs)
- [x] Verify tests pass

### Phase 1: Core Global Templates
- [x] Convert `active_session.md.tpl` → use `session_base.md.j2`
- [x] Update `session_frontmatter.py`
- [x] Convert `CLI_REFERENCE.md.tpl` → `.j2`
- [x] Update `docs.py`
- [x] Review/remove `GOVERNANCE_BASE.md.tpl`
- [x] Verify tests pass

### Phase 2: Workflow Prompts
- [x] Convert implementation prompts → `.j2`
- [x] Convert research prompts → `.j2`
- [x] Convert workflow-creation prompts → `.j2`

> Progress note: Research and Workflow-creation prompts were already Jinja `.j2` and are marked converted above.
- [ ] Test all workflows
- [ ] Verify tests pass

### Phase 3: Artifact Templates
- [ ] Convert planning artifacts → `.j2`
- [ ] Convert implementation artifacts → `.j2`
- [ ] Convert implementation logs → `.j2`
- [ ] Verify no `.tpl` in workflows
- [ ] Verify tests pass

### Phase 4: Generator Cleanup
- [ ] Remove legacy `generate_agents_for_workflow()`
- [ ] Refactor `docs.py` to Jinja2
- [ ] Update all callsites
- [ ] Final test suite
- [ ] Verify only `workflow.tpl` remains

---

## Success Criteria

1. **Zero `.tpl` files** (except `workflow.tpl` shell wrapper)
2. **All 40+ tests passing**
3. **All 4 workflows initialize correctly**
4. **All agents activate with proper session files**
5. **CLI commands work**: status, activate, handoff, decision, end

---

## Estimated Total Time

| Phase | Duration | Risk |
|-------|----------|------|
| Phase 0 | 30 min | LOW |
| Phase 1 | 2 hours | MEDIUM |
| Phase 2 | 3 hours | MEDIUM-HIGH |
| Phase 3 | 2 hours | LOW |
| Phase 4 | 2 hours | MEDIUM |
| **Total** | **~10 hours** | |

---

## References

- [TEMPLATES_STATUS_REPORT.md](./TEMPLATES_STATUS_REPORT.md) - Current state analysis
- [templates/JINJA2_MIGRATION_REPORT.md](./templates/JINJA2_MIGRATION_REPORT.md) - Original migration
- [scripts/utils/jinja_loader.py](./scripts/utils/jinja_loader.py) - Jinja2 engine
- [templates/PLACEHOLDER_REGISTRY.md](./templates/PLACEHOLDER_REGISTRY.md) - Variable reference
