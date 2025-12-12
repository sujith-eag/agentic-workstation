"""Helper utilities for building, merging, and rendering session YAML frontmatter.

Centralizes the logic so multiple scripts don't duplicate YAML handling.
"""
from pathlib import Path
import datetime
import yaml
import re

try:
    from agentic_workflow.utils.templating import TemplateEngine, ContextResolver
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    TemplateEngine = None
    ContextResolver = None

__all__ = [
    "merge_frontmatter",
    "render_frontmatter_yaml", 
    "load_frontmatter_from_text",
    "build_orchestrator_session_from_template",
]


def merge_frontmatter(session_fm: dict, agent_fm: dict, project_name: str = None) -> dict:
    """Merge agent frontmatter into session frontmatter with simplified keys.

    Produces a lean frontmatter with 8 essential fields:
    - project, agent_id, agent_slug, agent_role
    - context_file, consumes, produces, last_activated

    Returns the merged dict (does not write files).
    """
    session = dict(session_fm or {})
    agent = dict(agent_fm or {})

    # Determine project name from session or parameter
    proj = project_name or session.get('project', '')

    id_val = agent.get('agent_id')
    if id_val is None:
        id_str = ""
    else:
        id_str = str(id_val).zfill(2)

    # Agent role can come from multiple fields: agent_role, title, or existing session
    agent_role = agent.get('agent_role') or agent.get('title') or session.get('agent_role')
    slug = agent.get('agent_slug') or agent.get('slug') or (agent_role or '').lower().replace(' ', '_').replace('&', 'and') or f"agent_{id_str}"
    
    consumes = agent.get('consumes', session.get('consumes', []))
    produces = agent.get('produces', session.get('produces', []))
    
    # Compute context_file dynamically from slug
    context_file = agent.get('context_file')
    if not context_file and slug:
        context_file = f"agent_context/{slug}_context_index.md"
    elif not context_file:
        context_file = session.get('context_file', 'agent_context/orchestrator_context_index.md')

    # Simplified frontmatter - 8 essential fields
    return {
        'project': proj,
        'agent_id': id_str or session.get('agent_id', '00'),
        'agent_slug': slug,
        'agent_role': agent_role,
        'context_file': context_file,
        'consumes': consumes,
        'produces': produces,
        'last_activated': datetime.datetime.now().isoformat(),
    }


def render_frontmatter_yaml(fm: dict) -> str:
    """Return a YAML string block with leading/trailing '---' markers."""
    fm_yaml = yaml.dump(fm, sort_keys=False, default_flow_style=False, width=1000)
    return f"---\n{fm_yaml}---\n"


def load_frontmatter_from_text(text: str) -> dict:
    """Parse YAML frontmatter from text if present, else return {}."""
    import re

    fm_match = re.search(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if fm_match:
        try:
            return yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            return {}
    return {}


def write_session_file(path: Path, content: str) -> None:
    """Compose and write the active_session.md file from parts.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# Minimal helper to build a small Layer 3 scratchpad
def build_layer3(agent_role: str, context_file: str) -> str:
    return f"## LAYER 3: SESSION STATE (SCRATCHPAD)\n**Current Task:**\n- [ ] Initialize session for {agent_role}\n- [ ] Read Local Index ({context_file})\n\n**Notes & Reasoning:**\n- Session started at {datetime.datetime.now().isoformat()}\n"


def extract_layers_from_template(template_text: str):
    """Return (layer1, layer2_body) extracted from a full template text.

    - layer1: the string including LAYER 1 markers
    - layer2_body: only the LAYER 2 content (between ## LAYER 2 and ## LAYER 3), 
                   not the full template. This avoids duplication with write_session_file.
    """
    import re
    
    # Extract Layer 1
    match = re.search(r"(.*?)", template_text, re.DOTALL)
    if match:
        layer1 = match.group(1).strip()
    else:
        layer1 = "\n## LAYER 1: ORCHESTRATOR BASE (IMPORTED)\nThis is a minimal orchestrator base.\n"
    
    # Extract Layer 2 body (content between ## LAYER 2 and ## LAYER 3)
    layer2_match = re.search(r"## LAYER 2:.*?\n(.*?)(?=\n---\n\n## LAYER 3|\n## LAYER 3|$)", template_text, re.DOTALL)
    if layer2_match:
        layer2_body = "## LAYER 2: AGENT PERSONA\n" + layer2_match.group(1).strip()
    else:
        # Fallback: try to find just the LAYER 2 section header and what follows
        layer2_body = "## LAYER 2: AGENT PERSONA\n**Role:** (undefined)\n**Objective:** (undefined)"
    
    return layer1, layer2_body


def render_template_body(body_text: str, substitutions: dict) -> str:
    """Replace simple {{key}} placeholders in the body_text using substitutions dict.

    This intentionally implements a minimal, explicit replacement strategy rather
    than a full templating engine to keep dependencies small and predictable.
    """
    out = body_text
    for k, v in (substitutions or {}).items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def orchestrator_frontmatter(project_name: str, extra: dict = None) -> dict:
    """Return a simplified orchestrator frontmatter dict."""
    fm = {
        "project": project_name,
        "agent_id": "orch",
        "agent_slug": "orchestrator",
        "agent_role": "Orchestrator & Project Controller",
        "context_file": "agent_context/orchestrator_context_index.md",
        "consumes": [],
        "produces": [],
        "last_activated": datetime.datetime.now().isoformat()
    }
    if extra:
        fm.update(extra)
    return fm


def default_orchestrator_substitutions(project_name: str = None) -> dict:
    """Return the default substitution map for the orchestrator template."""
    subs = {
        'context_file': 'agent_context/orchestrator_context_index.md',
        'timestamp': datetime.datetime.now().isoformat(),
    }
    if project_name:
        subs['project_name'] = project_name
    return subs


def build_orchestrator_session_from_template(workflow: str, project_name: str, agent_id: str, timestamp: str = "", extra_subs: dict | None = None, fm_extra: dict | None = None) -> str:
    """Build orchestrator session content from Jinja2 templates.
    
    Renders the complete session document including frontmatter and content layers
    for the orchestrator agent using workflow-specific templates.
    
    Args:
        workflow: Workflow name (e.g., 'planning', 'implementation')
        project_name: Name of the project
        agent_id: Agent identifier (e.g., 'A-00', 'I-00')
        timestamp: Session timestamp (ISO format)
        extra_subs: Additional template substitutions
        fm_extra: Extra frontmatter fields
        
    Returns:
        Rendered session content as string with frontmatter and markdown content
    """
    if not JINJA2_AVAILABLE:
        raise ImportError("Jinja2 is required. Please install with: pip install jinja2")

    # If agent_id is not provided, use a default based on the workflow
    if agent_id is None:
        if workflow == 'implementation':
            agent_id = 'I-00'
        else:
            agent_id = 'A-00'

    engine = TemplateEngine(workflow=workflow)
    resolver = ContextResolver()
    context = resolver.get_session_context(
        workflow=workflow,
        agent_id=agent_id,
        project_name=project_name,
        timestamp=timestamp,
        extra_subs=extra_subs
    )
    return engine.render("session_base.md.j2", context)


def ensure_context_file(project_dir: Path, context_file: str, agent_data: dict, templates_dir: Path = None) -> bool:
    """Ensure the agent's context file exists. Creates from template if missing.
    
    IMPORTANT: Does NOT overwrite existing context files to preserve agent state.
    
    Args:
        project_dir: Path to the project directory
        context_file: Relative path like 'agent_context/planning_context_index.md'
        agent_data: Dict with agent_id, agent_role, produces, etc.
        templates_dir: Optional path to templates directory
        
    Returns:
        True if file was created, False if it already existed
    """
    if templates_dir is None:
        templates_dir = Path("templates")
    
    context_path = project_dir / context_file
    
    # CRITICAL: Do not overwrite existing context files
    if context_path.exists():
        return False
    
    # Ensure parent directory exists
    context_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to load template - prefer .j2 over .tpl
    j2_path = templates_dir / "agent_context_index.md.j2"
    tpl_path = templates_dir / "agent_context_index.md.tpl"
    
    if j2_path.exists():
        tpl_content = j2_path.read_text()
    elif tpl_path.exists():
        tpl_content = tpl_path.read_text()
    else:
        # Minimal fallback template
        tpl_content = """# Agent Context: {{agent_role}}

> **Agent ID:** {{agent_id}}  
> **Created:** {{created_at}}

## Session Progress

### Active Tasks
- [ ] Review upstream artifacts
- [ ] Analyze inputs from `consumes`
- [ ] Draft primary outputs

## Artifact Tracker

| Artifact | Status | Notes |
|----------|--------|-------|
{{artifact_rows}}

## Notes & Scratchpad

- Agent activated at {{created_at}}
"""
    
    # Build substitutions
    raw_id = agent_data.get('agent_id', agent_data.get('active_agent_id', '00'))
    
    # Use raw_id directly if it's already in the A-XX or I-XX format.
    # Otherwise, default to A-00 or format numeric IDs.
    if isinstance(raw_id, str) and (raw_id.startswith('A-') or raw_id.startswith('I-')):
        agent_id_str = raw_id
    elif isinstance(raw_id, str) and raw_id.lower() == 'orch': # Orchestrator's internal slug
        # This will depend on the workflow, so we pass orch_id from wf
        agent_id_str = agent_data.get('orch_id_formatted', 'A-00') 
    elif isinstance(raw_id, (int, str)) and str(raw_id).isdigit():
        agent_id_str = f"A-{int(raw_id):02d}" # Default for numeric IDs
    else:
        agent_id_str = str(raw_id) # Fallback for other string IDs
        
    agent_role = agent_data.get('agent_role', agent_data.get('active_agent', 'Unknown'))
    produces = agent_data.get('produces', [])
    now = datetime.datetime.now().isoformat()
    
    # Build artifact rows from produces
    artifact_rows = []
    for artifact in produces:
        if isinstance(artifact, str):
            name = artifact.split('/')[-1]  # Get filename
            artifact_rows.append(f"| `{name}` | Not Started | - |")
    
    if not artifact_rows:
        artifact_rows.append("| (none defined) | - | - |")
    
    # Determine artifact directory
    artifact_prefix = agent_id_str.split('-')[0] if '-' in agent_id_str else agent_id_str
    numeric_part = agent_id_str.split('-')[-1] if '-' in agent_id_str else ''
    artifact_dir = f"artifacts/{artifact_prefix}{numeric_part}_*" # e.g., A00_* or I01_*
    
    if produces:
        for p in produces:
            if p.startswith('artifacts/'):
                parts = p.split('/')
                if len(parts) >= 2:
                    artifact_dir = f"artifacts/{parts[1]}"
                    break
    
    substitutions = {
        'agent_id': agent_id_str,
        'agent_role': agent_role,
        'project_name': agent_data.get('project', project_dir.name),
        'created_at': now,
        'last_updated': now,
        'status': 'Initialized',
        'iteration': '1',
        'artifact_rows': '\n'.join(artifact_rows),
        'context_file': context_file,
        'log_file': agent_data.get('log_file', 'agent_log/exchange_log.md'),
        'artifact_dir': artifact_dir,
    }
    
    content = render_template_body(tpl_content, substitutions)
    context_path.write_text(content)
    
    # Create YAML sidecar for the context file
    yaml_path = context_path.with_suffix('.yaml')
    if not yaml_path.exists():
        yaml_data = {
            'agent_id': agent_id_str,
            'agent_role': agent_role,
            'project': agent_data.get('project', project_dir.name),
            'created': now,
            'last_updated': now,
            'status': 'Initialized',
            'iteration': 1,
            'tasks': {
                'active': [],
                'completed': [],
                'blocked': [],
            },
            'artifacts': [],
            'decisions_local': [],
            'assumptions_local': [],
            'questions': [],
        }
        with open(yaml_path, 'w') as f:
            yaml.safe_dump(yaml_data, f, sort_keys=False)
    
    return True