"""Document generators for project docs.

This module generates documentation files from workflow packages.
Functions return content strings - file I/O is handled by callers.

Usage:
    from generators.docs import generate_cli_reference, generate_agent_pipeline
    
    cli_content = generate_cli_reference('myproject', wf)
    pipeline_content = generate_agent_pipeline(wf)
"""
from typing import Optional

from agentic_workflow.workflow import WorkflowPackage, load_workflow, WorkflowError
from agentic_workflow.core.paths import get_templates_dir
from agentic_workflow.utils.templating import TemplateEngine
from agentic_workflow.generation.denormalizer import Denormalizer


def generate_cli_reference(project_name: str, wf: WorkflowPackage) -> str:
    """Generate CLI_REFERENCE.md content dynamically from workflow config.
    
    Args:
        project_name: Project name
        wf: WorkflowPackage instance (source of truth)
        
    Returns:
        Generated CLI reference markdown content
    """
    # Build context for Jinja template rendering so we can switch to .j2
    context = {
        'project_name': project_name,
        'wf_display_name': wf.display_name,
        'wf_name': wf.name,
        'cli_examples': wf.cli_examples,
        'extra_commands': wf.extra_commands,
        'stages': wf.stages,
    }

    # Render using Jinja2 template (no fallback)
    loader = TemplateEngine(workflow=wf.name)
    return loader.render('docs/CLI_REFERENCE.md.j2', context)
    # Quick Start
    lines.append("## Quick Start (Recommended)")
    lines.append("")
    lines.append("From within this project folder, use the **local workflow wrapper**:")
    lines.append("")
    lines.append("```bash")
    lines.append("./workflow  [args...]")
    lines.append("```")
    lines.append("")
    lines.append("The project name is auto-detected — no need to specify it.")
    lines.append("")
    
    # Examples from workflow config
    lines.append("### Examples")
    lines.append("")
    lines.append("```bash")
    for example in wf.cli_examples:
        cmd = example.get('command', '')
        desc = example.get('description', '')
        lines.append(f"{cmd:<45} # {desc}")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Alternative root CLI
    lines.append("## Alternative: Root CLI")
    lines.append("")
    lines.append("You can also run commands from the **repo root**:")
    lines.append("")
    lines.append("```bash")
    lines.append("cd /path/to/agentic-workflow-os")
    lines.append(f"python3 -m scripts.cli.workflow  {project_name} [args]")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Workflow-specific commands (if any)
    if wf.extra_commands:
        lines.append(f"## {wf.display_name}-Specific Commands")
        lines.append("")
        lines.append("| Command | Syntax | Description |")
        lines.append("|---------|--------|-------------|")
        for cmd in wf.extra_commands:
            # Handle both string format and dict format
            if isinstance(cmd, str):
                name = cmd
                syntax = f"./workflow {cmd} [args]"
                desc = f"Run {cmd} command"
            else:
                name = cmd.get('name', '')
                syntax = cmd.get('syntax', '')
                desc = cmd.get('description', '')
            lines.append(f"| **{name}** | `{syntax}` | {desc} |")
        lines.append("")
    
    # Standard session commands
    lines.append("## Session Commands")
    lines.append("")
    lines.append("| Command | Syntax | Description |")
    lines.append("|---------|--------|-------------|")
    
    # Format agent ID examples
    ex1 = wf.format_agent_id(1)
    ex2 = wf.format_agent_id(2)
    
    lines.append("| **init** | `init` | Initialize project directory structure |")
    lines.append(f"| **activate** | `activate ` | Activate agent session ({wf.orch_id}, {ex1}, {ex2}, ...) |")
    lines.append("| **end** | `end` | Archive session and reset to Orchestrator |")
    lines.append("")
    
    # Entry commands
    lines.append("## Entry Commands (exchange_log)")
    lines.append("")
    lines.append("| Command | Syntax | Description |")
    lines.append("|---------|--------|-------------|")
    lines.append("| **handoff** | `handoff --from  --to  [--artifacts ] [--notes ]` | Write handoff with auto-generated ID |")
    lines.append("| **feedback** | `feedback --target  --severity  --summary ` | Write feedback ticket |")
    lines.append("| **iteration** | `iteration --trigger  --agents ` | Write iteration cycle |")
    lines.append("")
    
    lines.append("## Entry Commands (context_log)")
    lines.append("")
    lines.append("| Command | Syntax | Description |")
    lines.append("|---------|--------|-------------|")
    lines.append("| **session** | `session --agent  --role ` | Write session entry |")
    lines.append("| **decision** | `decision --title  --rationale  [--agent ]` | Write decision entry |")
    lines.append("| **assumption** | `assumption --text  [--rationale ]` | Write assumption entry |")
    lines.append("| **blocker** | `blocker --title  --description ` | Write blocker entry |")
    lines.append("")
    
    # Query commands
    lines.append("## Query Commands")
    lines.append("")
    lines.append("| Command | Syntax | Description |")
    lines.append("|---------|--------|-------------|")
    lines.append("| **status** | `status` | Show project status summary |")
    lines.append("| **check-handoff** | `check-handoff ` | Check if handoff exists |")
    lines.append("| **list-pending** | `list-pending` | List pending handoffs |")
    lines.append("| **list-blockers** | `list-blockers` | List active blockers |")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Stages reference (if workflow has stages)
    if wf.stages:
        lines.append("## Stages Reference")
        lines.append("")
        lines.append("| Stage | Description |")
        lines.append("|-------|-------------|")
        for stage in wf.stages:
            stage_id = stage.get('id', '')
            stage_desc = stage.get('description', '')
            lines.append(f"| `{stage_id}` | {stage_desc} |")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # On-demand agents (if any)
    on_demand = wf.on_demand_config.get('agents', [])
    if on_demand:
        lines.append("## On-Demand Agents")
        lines.append("")
        lines.append("These agents are invoked as needed, not part of the core pipeline:")
        lines.append("")
        lines.append("| Agent | Command | Purpose |")
        lines.append("|-------|---------|---------|")
        for agent in on_demand:
            if isinstance(agent, dict):
                aid = agent.get('id', '')
                desc = agent.get('description', '')
                lines.append(f"| `{aid}` | `./workflow invoke {aid}` | {desc} |")
            elif isinstance(agent, str):
                formatted_id = wf.format_agent_id(agent)
                lines.append(f"| `{formatted_id}` | `./workflow invoke {formatted_id}` | Specialist agent |")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Auto-generated IDs
    lines.append("## Auto-Generated Entry IDs")
    lines.append("")
    lines.append("Entry IDs are auto-generated based on existing entries:")
    lines.append("")
    lines.append("- Handoffs: `HO-001`, `HO-002`, ...")
    lines.append("- Feedback: `FB-001`, `FB-002`, ...")
    lines.append("- Iterations: `ITER-001`, `ITER-002`, ...")
    lines.append("- Sessions: `SESS-001`, `SESS-002`, ...")
    lines.append("- Decisions: `DEC-001`, `DEC-002`, ...")
    lines.append("- Assumptions: `ASSUMP-001`, `ASSUMP-002`, ...")
    lines.append("- Blockers: `BLK-001`, `BLK-002`, ...")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Copy-paste commands
    lines.append("## Copy-Paste Ready Commands")
    lines.append("")
    
    lines.append("### Write a Decision")
    lines.append("```bash")
    lines.append(f'./workflow decision --title "Decision title" --rationale "Why this decision" --agent {ex1}')
    lines.append("```")
    lines.append("")
    
    lines.append("### Signal Handoff to Next Agent")
    lines.append("```bash")
    lines.append(f'./workflow handoff --from {ex1} --to {ex2} --artifacts "file1.md,file2.md" --notes "Ready for next phase"')
    lines.append("```")
    lines.append("")
    
    lines.append("### Check Project Status")
    lines.append("```bash")
    lines.append("./workflow status")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Python API
    lines.append("## Python API")
    lines.append("")
    lines.append("For programmatic access:")
    lines.append("")
    lines.append("```python")
    lines.append("from agentic_workflow.ledger.entry_writer import write_handoff, write_decision")
    lines.append("from agentic_workflow.ledger.entry_reader import get_project_summary")
    lines.append("")
    lines.append("# Write entries")
    lines.append(f'entry_id, path = write_handoff("{project_name}", "{ex1}", "{ex2}", artifacts=["spec.md"])')
    lines.append(f'entry_id, path = write_decision("{project_name}", "{ex1}", "Title", "Rationale")')
    lines.append("")
    lines.append("# Query")
    lines.append(f'summary = get_project_summary("{project_name}")')
    lines.append("```")
    lines.append("")
    
    # (All rendering now done through Jinja template.)
    # This return is kept to satisfy function signature if template rendering
    # does not raise. The template is authoritative for content.
    return loader.render('docs/CLI_REFERENCE.md.j2', context)


def generate_agent_pipeline(wf: WorkflowPackage) -> str:
    """Generate AGENT_PIPELINE.md content from workflow agents.
    
    Args:
        wf: WorkflowPackage instance.
        
    Returns:
        Generated pipeline markdown content.
    """
    agents = wf.agents
    pipeline_order = wf.pipeline_order
    
    lines = ["# Agent Pipeline", "", "> Agent order, roles, and I/O for this project.", ""]
    lines.append(f"**Workflow:** {wf.display_name} v{wf.version}")
    lines.append("")
    lines.append("## Pipeline Order")
    lines.append("")
    lines.append("```")
    
    # Build pipeline string using workflow's format_agent_id method
    pipeline_items = [wf.format_agent_id(x) for x in pipeline_order]
    pipeline_str = ' → '.join(pipeline_items)
    
    lines.append(pipeline_str)
    lines.append("```")
    lines.append("")
    lines.append("## Agent Registry")
    lines.append("")
    lines.append("| ID | Role | Description |")
    lines.append("|----|------|-------------|")
    
    for agent in agents:
        aid = agent.get('id', '?')
        aid_str = wf.format_agent_id(aid)
        
        role = agent.get('role', 'Unknown')
        desc = agent.get('description', '')[:60] + ('...' if len(agent.get('description', '')) > 60 else '')
        lines.append(f"| {aid_str} | {role} | {desc} |")
    
    lines.append("")
    lines.append("## Agent I/O Summary")
    lines.append("")
    
    for agent in agents:
        aid = agent.get('id', '?')
        aid_str = wf.format_agent_id(aid)
        
        role = agent.get('role', 'Unknown')
        
        # Handle both flat lists and nested dicts for consumes/produces
        consumes_raw = agent.get('consumes', {})
        produces_raw = agent.get('produces', {})
        
        # Extract filenames from nested structure
        def flatten_artifacts(artifacts):
            """Flatten nested artifact structure to list of filenames."""
            if isinstance(artifacts, list):
                # Already a flat list
                result = []
                for item in artifacts:
                    if isinstance(item, dict):
                        result.append(item.get('filename', item.get('file', str(item))))
                    else:
                        result.append(str(item))
                return result
            elif isinstance(artifacts, dict):
                # Nested structure with core/domain/etc categories
                result = []
                for category, items in artifacts.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                result.append(item.get('filename', item.get('file', str(item))))
                            else:
                                result.append(str(item))
                return result
            return []
        
        consumes = flatten_artifacts(consumes_raw)
        produces = flatten_artifacts(produces_raw)
        
        # Legacy flat fields (for backward compatibility)
        consumes_core = agent.get('consumes_core', [])
        consumes_domain = agent.get('consumes_domain', [])
        consumes_opt = agent.get('consumes_optional', [])
        
        lines.append(f"### {aid_str}: {role}")
        lines.append("")
        
        # Handle tiered artifacts (shown if present)
        if consumes_core:
            lines.append(f"**Core (Required):** {', '.join(consumes_core)}")
        if consumes_domain:
            lines.append(f"**Domain (Context):** {', '.join(consumes_domain)}")
        if consumes:
            lines.append(f"**Consumes:** {', '.join(consumes)}")
        if consumes_opt:
            lines.append(f"**Optional:** {', '.join(consumes_opt)}")
        if produces:
            lines.append(f"**Produces:** {', '.join(produces)}")
        lines.append("")
    
    return "\n".join(lines)


def generate_artifact_registry(wf: WorkflowPackage, source_wf: Optional[WorkflowPackage] = None) -> str:
    """Generate ARTIFACT_REGISTRY.md content from workflow artifacts.
    
    Args:
        wf: WorkflowPackage instance.
        source_wf: Optional source workflow for input artifacts (e.g., planning workflow).
        
    Returns:
        Generated artifact registry markdown content.
    """
    # Reconstruct canonical data for denormalization
    canonical_data = {
        "workflow": wf.metadata,
        "agents": {"agents": wf.agents},
        "artifacts": {"artifacts": wf.artifacts},
        "instructions": {"instructions": wf.instructions}
    }
    
    # Use denormalizer for proper artifact metadata extraction
    denormalizer = Denormalizer(canonical_data)
    artifacts = denormalizer.denormalize_artifacts()
    
    lines = ["# Artifact Registry", "", "> All artifacts, their owners, and consumers for this project.", ""]
    lines.append(f"**Workflow:** {wf.display_name} v{wf.version}")
    lines.append(f"**Total artifacts:** {len(artifacts)}")
    lines.append("")
    
    # Group artifacts by section
    current_section = None
    
    lines.append("| Artifact | Owner | Consumed By | Description |")
    lines.append("|----------|-------|-------------|-------------|")
    
    for artifact in artifacts:
        # Check for section change
        section = artifact.get('_section', None)
        if section and section != current_section:
            section_name = section.replace('_', ' ').title()
            lines.append(f"| **{section_name}** | | | |")
            current_section = section
        
        name = artifact.get('filename', artifact.get('id', artifact.get('file', 'Unknown')))
        
        # Determine owner format based on whether it's a source_owner or owner
        if 'source_owner' in artifact and source_wf:
            # Input artifact from planning - use source workflow's format
            owner = artifact.get('source_owner', '?')
            owner_str = source_wf.format_agent_id(owner)
        else:
            # Implementation artifact - use current workflow's format
            owner = artifact.get('owner', artifact.get('source_owner', '?'))
            owner_str = wf.format_agent_id(owner)
        
        desc = artifact.get('description', '')[:50] + ('...' if len(artifact.get('description', '')) > 50 else '')
        
        # Format consumed_by agents
        consumed_by = artifact.get('consumed_by', [])
        if consumed_by:
            consumed_str = ', '.join(wf.format_agent_id(agent_id) for agent_id in consumed_by[:3])  # Limit to 3
            if len(consumed_by) > 3:
                consumed_str += f" +{len(consumed_by) - 3} more"
        else:
            consumed_str = "-"
        
        lines.append(f"| `{name}` | {owner_str} | {consumed_str} | {desc} |")
    
    lines.append("")
    
    return "\n".join(lines)


def generate_governance(project_name: str, wf: WorkflowPackage) -> str:
    """Generate GOVERNANCE_GUIDE.md content from template and workflow governance.
    
    Args:
        project_name: Project name.
        wf: WorkflowPackage instance.
        
    Returns:
        Generated governance markdown content, or empty string if template not found.
    """
    loader = TemplateEngine(workflow=wf.name)
    
    # Get workflow-specific governance content
    workflow_governance = wf.governance if wf.governance else ""
    
    # Strip the header from workflow governance since template has structure
    if workflow_governance:
        lines = workflow_governance.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('## ') or line.startswith('---'):
                start_idx = i
                break
        workflow_governance = '\n'.join(lines[start_idx:])

    context = {
        "project_name": project_name,
        "workflow_name": wf.display_name,
        "workflow_version": wf.version,
        "workflow_governance": workflow_governance
    }
    

def generate_copilot_instructions(project_name: str, wf: WorkflowPackage) -> str:
    """Generate .github/copilot-instructions.md from template and workflow config.
    
    Args:
        project_name: Project name.
        wf: WorkflowPackage instance.
        
    Returns:
        Generated copilot instructions content, or empty string if template not found.
    """
    copilot_config = wf.display.get('copilot', {})
    context = {
        'project_name': project_name,
        'workflow_type': copilot_config.get('workflow_type', wf.name.title()),
        'workflow_display_name': wf.display_name,
        'workflow_tagline': copilot_config.get('tagline', 'project workspace'),
        'governance_purpose': copilot_config.get('governance_purpose', 'Decision IDs, logging rules'),
        'startup_extras': copilot_config.get('startup_extras', ''),
        'extra_resources': copilot_config.get('extra_resources', ''),
        'core_rules': copilot_config.get('core_rules', ''),
        'cycle_section': copilot_config.get('cycle_section', ''),
        'cli_examples': ("\n".join([e.get('command', '') + "  # " + e.get('description', '') for e in copilot_config.get('cli_examples', [])]) if isinstance(copilot_config.get('cli_examples', []), list) else copilot_config.get('cli_examples', '')),
        'on_demand_section': copilot_config.get('on_demand_section', ''),
    }

    loader = TemplateEngine(workflow=wf.name)
    return loader.render('docs/copilot-instructions.md.j2', context)


def generate_gemini_instructions(project_name: str, wf: WorkflowPackage) -> str:
    """Generate .github/GEMINI.md from template and workflow config.
    
    Args:
        project_name: Project name.
        wf: WorkflowPackage instance.
        
    Returns:
        Generated gemini instructions content, or empty string if template not found.
    """
    copilot_config = wf.display.get('copilot', {})
    context = {
        'project_name': project_name,
        'workflow_type': copilot_config.get('workflow_type', wf.name.title()),
        'workflow_display_name': wf.display_name,
        'workflow_tagline': copilot_config.get('tagline', 'project workspace'),
        'governance_purpose': copilot_config.get('governance_purpose', 'Decision IDs, logging rules'),
        'startup_extras': copilot_config.get('startup_extras', ''),
        'extra_resources': copilot_config.get('extra_resources', ''),
        'core_rules': copilot_config.get('core_rules', ''),
        'cycle_section': copilot_config.get('cycle_section', ''),
        'cli_examples': ("\n".join([e.get('command', '') + "  # " + e.get('description', '') for e in copilot_config.get('cli_examples', [])]) if isinstance(copilot_config.get('cli_examples', []), list) else copilot_config.get('cli_examples', '')),
        'on_demand_section': copilot_config.get('on_demand_section', ''),
    }

    loader = TemplateEngine(workflow=wf.name)
    return loader.render('docs/GEMINI.md.j2', context)
