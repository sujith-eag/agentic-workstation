# Validation Script Enhancement Guide

**Target File:** `scripts/validation/validate_canonical.py`  
**Purpose:** Add new validation rules aligned with schema consolidation

---

## Overview

This document provides the exact code additions needed to enhance the validation script with new checks for:
1. Deprecated globals usage detection
2. On-demand placement validation
3. Null template value detection
4. Config section completeness
5. Stage-agent assignment completeness
6. Enhanced CLI options

---

## New Validation Functions

Add these functions **after line 350** (after `validate_slug_consistency`) and **before** `validate_pipeline_order`:

### Function 1: Deprecated Globals Detection

```python
def validate_deprecated_globals(workflow_data: Dict, result: ValidationResult):
    """Warn about deprecated globals.logging_policy, globals.enforcement, and globals.ui."""
    if not workflow_data:
        return
    
    globals_section = workflow_data.get("globals", {})
    
    if "logging_policy" in globals_section:
        result.add_warning(
            "workflow.json: globals.logging_policy is DEPRECATED - "
            "migrate to config.logging section"
        )
    
    if "enforcement" in globals_section:
        result.add_warning(
            "workflow.json: globals.enforcement is DEPRECATED - "
            "migrate to config.enforcement section"
        )
    
    if "ui" in globals_section:
        result.add_warning(
            "workflow.json: globals.ui is DEPRECATED - "
            "use display section for all UI configuration"
        )
```

### Function 2: On-Demand Placement Check

```python
def validate_on_demand_placement(workflow_data: Dict, result: ValidationResult):
    """Warn if on_demand agents are defined in metadata instead of pipeline."""
    if not workflow_data:
        return
    
    metadata = workflow_data.get("metadata", {})
    
    # Check for on_demand in metadata (deprecated location)
    if "on_demand" in metadata:
        on_demand_agents = metadata.get("on_demand", {}).get("agents", [])
        if on_demand_agents:
            result.add_warning(
                f"workflow.json: metadata.on_demand.agents contains {len(on_demand_agents)} agent(s) - "
                "move to pipeline.on_demand for consistency"
            )
    
    # Verify pipeline.on_demand exists if there are on-demand agents in agents.json
    pipeline = workflow_data.get("pipeline", {})
    pipeline_on_demand = set(pipeline.get("on_demand", []))
    
    # This check works with agents data passed separately - see integration below
```

### Function 3: Null Template Detection

```python
def validate_artifact_templates(artifacts_data: Dict, result: ValidationResult):
    """Warn about null template values that should be removed."""
    if not artifacts_data:
        return
    
    null_template_count = 0
    for artifact in artifacts_data.get("artifacts", []):
        # Check if template key exists AND is explicitly null
        if "template" in artifact and artifact.get("template") is None:
            filename = artifact.get("filename", "unknown")
            null_template_count += 1
            if null_template_count <= 5:  # Limit spam
                result.add_warning(
                    f"artifacts.json: '{filename}' has template: null - "
                    "remove field entirely instead of setting to null"
                )
    
    if null_template_count > 5:
        result.add_warning(
            f"artifacts.json: {null_template_count - 5} more artifact(s) with template: null"
        )
```

### Function 4: Config Section Validation

```python
def validate_config_section(workflow_data: Dict, result: ValidationResult):
    """
    Check that the unified config section exists with required sub-sections.
    This is the new consolidated location for enforcement/logging/validation/bypass.
    """
    if not workflow_data:
        return
    
    config = workflow_data.get("config")
    
    if not config:
        # Check if using deprecated globals - if so, guide migration
        globals_section = workflow_data.get("globals", {})
        has_deprecated = (
            "logging_policy" in globals_section or 
            "enforcement" in globals_section
        )
        
        if has_deprecated:
            result.add_warning(
                "workflow.json: Missing 'config' section - "
                "migrate globals.logging_policy and globals.enforcement to config"
            )
        else:
            result.add_info(
                "workflow.json: No 'config' section - "
                "consider adding config.enforcement and config.logging"
            )
        return
    
    # Validate config sub-sections
    required_sections = ["enforcement", "logging"]
    optional_sections = ["validation", "bypass"]
    
    for section in required_sections:
        if section not in config:
            result.add_warning(f"workflow.json: config.{section} is missing")
    
    # Validate enforcement sub-fields if present
    enforcement = config.get("enforcement", {})
    if enforcement:
        valid_modes = ["strict", "lenient", "none"]
        for field in ["mode", "checkpoint_gating", "handoff_gating"]:
            value = enforcement.get(field)
            if value and value not in valid_modes:
                result.add_error(
                    f"workflow.json: config.enforcement.{field} has invalid value '{value}' - "
                    f"must be one of {valid_modes}"
                )
    
    result.add_info(f"workflow.json: config section has {len(config)} sub-section(s)")
```

### Function 5: Stage Completeness Check

```python
def validate_stage_completeness(workflow_data: Dict, agent_ids: Set[str], result: ValidationResult):
    """
    Validate that stages are defined and all pipeline agents are assigned.
    """
    if not workflow_data:
        return
    
    stages = workflow_data.get("stages", [])
    pipeline = workflow_data.get("pipeline", {})
    pipeline_order = set(pipeline.get("order", []))
    on_demand = set(pipeline.get("on_demand", []))
    
    # If no stages defined but pipeline exists, warn
    if not stages and pipeline_order:
        result.add_warning(
            "workflow.json: No 'stages' array defined - "
            "consider adding explicit stage assignments for clarity"
        )
        return
    
    if not stages:
        return
    
    # Collect all agents assigned to stages
    assigned_agents = set()
    for stage in stages:
        stage_id = stage.get("id", "UNKNOWN")
        stage_agents = stage.get("agents", [])
        
        # Validate stage agents exist
        for agent_id in stage_agents:
            if agent_id not in agent_ids:
                result.add_error(
                    f"workflow.json: Stage '{stage_id}' references unknown agent '{agent_id}'"
                )
            else:
                assigned_agents.add(agent_id)
    
    # Check for unassigned pipeline agents (excluding orchestrator A-00/I-00/R-00)
    orchestrator_ids = {aid for aid in pipeline_order if aid.endswith("-00")}
    core_agents = pipeline_order - orchestrator_ids
    unassigned = core_agents - assigned_agents
    
    if unassigned:
        result.add_warning(
            f"workflow.json: {len(unassigned)} agent(s) not assigned to any stage: "
            f"{', '.join(sorted(unassigned))}"
        )
    
    # Info about on-demand agents (not expected in stages)
    if on_demand:
        result.add_info(
            f"workflow.json: {len(on_demand)} on-demand agent(s) (not in stages): "
            f"{', '.join(sorted(on_demand))}"
        )
```

---

## Integration into validate_workflow()

Locate the `validate_workflow()` function (around line 480) and add calls to the new functions.

**Add AFTER the existing validations and BEFORE `detect_circular_dependencies`:**

```python
def validate_workflow(workflow_name: str) -> ValidationResult:
    """Run all validations for a workflow."""
    result = ValidationResult(workflow=workflow_name)
    workflow_dir = CANONICAL_DIR / workflow_name
    
    # ... existing code ...
    
    # Existing validations
    agent_ids = validate_agent_ids(agents_data, result)
    
    artifact_filenames = set()
    if artifacts_data:
        artifact_filenames = validate_artifact_filenames(artifacts_data, agent_ids, result)
    
    if instructions_data:
        validate_instructions(instructions_data, agent_ids, result)
    
    if artifact_filenames:
        validate_produces_consumes(agents_data, artifact_filenames, workflow_data, result)
    
    if workflow_data:
        validate_pipeline_order(workflow_data, agent_ids, result)
        validate_stage_agents(workflow_data, agent_ids, result)
        validate_input_from_artifacts(workflow_data, result)
    
    if instructions_data and workflow_data:
        validate_cycle_references(instructions_data, workflow_data, result)
    
    if instructions_data:
        validate_slug_consistency(agents_data, instructions_data, result)
    
    # =========================================
    # NEW VALIDATIONS - Add these lines
    # =========================================
    
    # Schema consolidation checks
    if workflow_data:
        validate_deprecated_globals(workflow_data, result)
        validate_on_demand_placement(workflow_data, result)
        validate_config_section(workflow_data, result)
        validate_stage_completeness(workflow_data, agent_ids, result)
    
    # Artifact template checks
    if artifacts_data:
        validate_artifact_templates(artifacts_data, result)
    
    # =========================================
    # END NEW VALIDATIONS
    # =========================================
    
    # Dependency cycle detection (keep last)
    detect_circular_dependencies(agents_data, result)
    
    return result
```

---

## Enhanced CLI Options

Update the `main()` function to add new CLI options:

```python
def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate canonical JSON manifests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 -m scripts.validation.validate_canonical --all
  python3 -m scripts.validation.validate_canonical --workflow planning --strict
  python3 -m scripts.validation.validate_canonical --all --output json
        """
    )
    parser.add_argument('--workflow', '-w', help='Specific workflow to validate')
    parser.add_argument('--all', '-a', action='store_true', help='Validate all workflows')
    parser.add_argument('--check-cross-refs', action='store_true', 
                        help='Only check cross-references')
    parser.add_argument('--quiet', '-q', action='store_true', 
                        help='Only show errors')
    
    # NEW OPTIONS
    parser.add_argument('--strict', action='store_true',
                        help='Treat warnings as errors (exit 1 if any warnings)')
    parser.add_argument('--output', '-o', choices=['text', 'json'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--fix-suggestions', action='store_true',
                        help='Show suggested fixes for common issues')
    
    args = parser.parse_args()
    
    # ... existing workflow discovery code ...
    
    all_passed = True
    results = []
    
    for wf in workflows:
        result = validate_workflow(wf)
        results.append(result)
        if not result.passed:
            all_passed = False
        # NEW: strict mode treats warnings as failures
        if args.strict and result.warnings:
            all_passed = False
    
    # NEW: JSON output option
    if args.output == 'json':
        output_json(results)
    else:
        # Print results (existing code)
        for result in results:
            if args.quiet and result.passed:
                continue
            result.print_summary()
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY: {len(results)} workflow(s) checked")
        print(f"{'='*60}")
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        warnings = sum(len(r.warnings) for r in results)
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Warnings: {warnings}")
        
        if args.strict and warnings:
            print(f"\n⚠️  --strict mode: {warnings} warning(s) treated as errors")
    
    sys.exit(0 if all_passed else 1)
```

---

## JSON Output Function

Add this function before `main()`:

```python
def output_json(results: List[ValidationResult]):
    """Output results as JSON for CI/CD integration."""
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "total_errors": sum(len(r.errors) for r in results),
            "total_warnings": sum(len(r.warnings) for r in results)
        },
        "workflows": {}
    }
    
    for r in results:
        output["workflows"][r.workflow] = {
            "passed": r.passed,
            "error_count": len(r.errors),
            "warning_count": len(r.warnings),
            "info_count": len(r.info),
            "errors": r.errors,
            "warnings": r.warnings,
            "info": r.info
        }
    
    print(json.dumps(output, indent=2))
```

Add this import at the top of the file:

```python
from datetime import datetime
```

---

## Testing the Enhanced Validator

After making changes, test with:

```bash
# Basic validation
python3 -m scripts.validation.validate_canonical --all

# Strict mode (warnings = errors)
python3 -m scripts.validation.validate_canonical --all --strict

# JSON output for CI
python3 -m scripts.validation.validate_canonical --all --output json

# Quiet mode
python3 -m scripts.validation.validate_canonical --all --quiet
```

---

## Expected Output After Schema Migration

After completing all migrations, running validation should show:

```
============================================================
Workflow: planning - ✅ PASSED
============================================================

ℹ️  Info (5):
  - agents.json: Schema validation passed
  - artifacts.json: Schema validation passed
  - workflow.json: config section has 4 sub-section(s)
  - workflow.json: 14 agent(s) in pipeline order
  - workflow.json: 3 checkpoint(s) defined

============================================================
VALIDATION SUMMARY: 3 workflow(s) checked
============================================================
  ✅ Passed: 3
  ❌ Failed: 0
  ⚠️  Warnings: 0
```

If deprecated patterns are still present:

```
⚠️  Warnings (2):
  - workflow.json: globals.logging_policy is DEPRECATED - migrate to config.logging
  - workflow.json: Missing 'config' section - add enforcement and logging config
```
