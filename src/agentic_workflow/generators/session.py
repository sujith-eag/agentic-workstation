"""Active session generator.

This module generates active_session.md content from workflow packages.

Usage:
    from generators.session import generate_active_session_content
    
    content = generate_active_session_content('myproject', wf)
"""
import datetime
from typing import Dict, Any, Optional, Tuple

from agentic_workflow.workflow import WorkflowPackage
from agentic_workflow.core.paths import get_templates_dir


def build_session_substitutions(project_name: str, wf: Optional[WorkflowPackage] = None) -> Dict[str, str]:
    """Build substitution dict for active_session template.
    
    Args:
        project_name: Project name.
        wf: Optional WorkflowPackage for workflow-specific config.
        
    Returns:
        Dict of template substitutions.
    """
    subs = {}
    
    if wf:
        display = wf.display
        
        # Format base_rules as numbered list
        base_rules = display.get('base_rules', [
            "**Source of Truth:** `project_index.md` is your file registry",
            "**Inputs:** Read from paths listed in `consumes` (frontmatter)",
            "**Outputs:** Write to paths listed in `produces` (frontmatter)",
            "**Logging:** See `docs/CLI_REFERENCE.md` for workflow commands"
        ])
        subs['base_rules'] = '\n'.join(f"{i}. {rule}" for i, rule in enumerate(base_rules, 1))
        
        # Format protocol
        protocol = display.get('protocol', {})
        subs['protocol_name'] = protocol.get('name', 'Context Protocol')
        protocol_steps = protocol.get('steps', [
            "**On Startup:** Read `project_index.md` → Read `context_file` → Check `agent_log/exchange_log.md`",
            "**Gating:** Do NOT proceed if upstream HANDOFF is missing",
            "**Checkpointing:** Update `context_file` after every significant step"
        ])
        subs['protocol_steps'] = '\n'.join(f"{i}. {step}" for i, step in enumerate(protocol_steps, 1))
    else:
        # Defaults for no workflow
        subs['base_rules'] = """1. **Source of Truth:** `project_index.md` is your file registry
2. **Inputs:** Read from paths listed in `consumes` (frontmatter)
3. **Outputs:** Write to paths listed in `produces` (frontmatter)
4. **Logging:** See `docs/CLI_REFERENCE.md` for workflow commands"""
        subs['protocol_name'] = 'Context Protocol'
        subs['protocol_steps'] = """1. **On Startup:** Read `project_index.md` → Read `context_file` → Check `agent_log/exchange_log.md`
2. **Gating:** Do NOT proceed if upstream HANDOFF is missing
3. **Checkpointing:** Update `context_file` after every significant step"""
    
    return subs


def generate_active_session_content(project_name: str, wf: Optional[WorkflowPackage] = None) -> Tuple[str, Dict[str, str]]:
    """Generate active_session.md content with orchestrator defaults.
    
    This function prepares the content and substitutions needed to create
    an active_session.md file. The actual file writing is handled by
    session_frontmatter.py functions.
    
    Args:
        project_name: Project name.
        wf: Optional WorkflowPackage for workflow-specific config.
        
    Returns:
        Tuple of (template_path, extra_substitutions).
    """
    # Get template path (Jinja2-based)
    tpl_path = get_templates_dir() / "_base" / "session_base.md.j2"
    
    # Build substitutions from workflow config
    extra_subs = build_session_substitutions(project_name, wf)
    
    # Return template name (relative) and substitutions for backward compatibility
    return str(tpl_path), extra_subs


def get_orchestrator_context_data(wf: Optional[WorkflowPackage] = None) -> Dict[str, Any]:
    """Get orchestrator context file data.
    
    Args:
        wf: Optional WorkflowPackage for workflow-specific config.
        
    Returns:
        Dict for orchestrator context file.
    """
    orch_id = wf.orch_id if wf else '00'
    
    return {
        'agent_id': orch_id,
        'agent_role': 'Orchestrator & Project Controller',
        'produces': [],
        'log_file': 'agent_log/exchange_log.md',
        'context_file': 'agent_context/orchestrator_context_index.md',
    }
