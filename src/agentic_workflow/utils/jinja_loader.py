#!/usr/bin/env python3
"""Jinja2 Template Loader for the agent workflow system.

This module provides Jinja2-based template loading with:
- Hierarchical template resolution (workflow → role → base → partials)
- Custom filters for markdown formatting
- Template inheritance support
- Integration with canonical JSON data

Template Loading Hierarchy:
1. manifests/workflows//templates/  (workflow package override)
2. templates//                      (workflow group)
3. templates/_roles//                   (role-based)
4. templates/_base/                           (base templates)
5. templates/_partials/                       (shared partials)

Usage:
    from agentic_workflow.utils.jinja_loader import JinjaTemplateLoader
    
    loader = JinjaTemplateLoader()
    
    # Render an agent template
    output = loader.render_agent('planning', 'A-02', project_name='my_project')
    
    # Render with custom context
    output = loader.render('agent_body.md.j2', context, workflow='planning')
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import warnings

try:
    from jinja2 import (
        Environment,
        FileSystemLoader,
        ChoiceLoader,
        PrefixLoader,
        TemplateNotFound,
        select_autoescape,
        pass_context,
    )
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = None

# Directories relative to repo root
from agentic_workflow.core.paths import get_package_root, get_templates_dir, get_manifests_dir
from agentic_workflow.cli.utils import display_error, display_success, display_info

ROOT_DIR = get_package_root()
TEMPLATES_DIR = get_templates_dir()
WORKFLOWS_DIR = ROOT_DIR / "manifests" / "workflows"
CANONICAL_DIR = get_manifests_dir()


class JinjaTemplateLoader:
    """Jinja2-based template loader with hierarchical resolution."""
    
    def __init__(self, workflow: Optional[str] = None, role: Optional[str] = None, workflow_root: Optional[Path] = None):
        """Initialize the loader.
        
        Args:
            workflow: Default workflow name for template resolution
            role: Default role for role-based template resolution
            workflow_root: Custom workflow root path for template overrides
        """
        if not JINJA2_AVAILABLE:
            raise ImportError(
                "Jinja2 is required for template rendering. "
                "Install with: pip install jinja2"
            )
        
        self.workflow = workflow
        self.role = role
        self.workflow_root = workflow_root
        self._env = self._create_environment(workflow, role, workflow_root)
    
    def _create_environment(
        self, 
        workflow: Optional[str] = None, 
        role: Optional[str] = None,
        workflow_root: Optional[Path] = None
    ) -> Environment:
        """Create Jinja2 environment with hierarchical loaders.
        
        Search order:
        1. User Project Overrides ($PROJECT_ROOT/.agentic/templates)
        2. Workflow Root Override (if provided)
        3. Workflow package templates (manifests/workflows)
        ...
        """
        loaders = []
        
        # 0. User Project Override (Highest Priority)
        # Try to find project root using path_resolution
        try:
            from agentic_workflow.core.path_resolution import find_project_root
            project_root = find_project_root()
            user_templates = project_root / ".agentic" / "templates"
            if user_templates.exists():
                loaders.append(FileSystemLoader(str(user_templates)))
        except ImportError:
            pass # path_resolution might not be importable if circular, or just skip

        # 0.5. Workflow Root Override
        if workflow_root and workflow_root.exists():
            loaders.append(FileSystemLoader(str(workflow_root)))

        # 1. Workflow package override (highest priority) -> Now third highest
        if workflow:
            wf_pkg_path = WORKFLOWS_DIR / workflow / "templates"
            if wf_pkg_path.exists():
                loaders.append(FileSystemLoader(str(wf_pkg_path)))
        
        # 2. Workflow group templates
        if workflow:
            wf_group_path = TEMPLATES_DIR / workflow
            if wf_group_path.exists():
                loaders.append(FileSystemLoader(str(wf_group_path)))
        
        # 3. Role templates
        if role:
            role_path = TEMPLATES_DIR / "_roles" / role
            if role_path.exists():
                loaders.append(FileSystemLoader(str(role_path)))
        
        # 4. Base templates
        base_path = TEMPLATES_DIR / "_base"
        if base_path.exists():
             loaders.append(FileSystemLoader(str(base_path)))

        # 5. Partials (with prefix for explicit includes)
        partials_path = TEMPLATES_DIR / "_partials"
        if partials_path.exists():
            loaders.append(FileSystemLoader(str(partials_path)))
        
        # 6. Root templates (fallback/resources)
        # Check if TEMPLATES_DIR is a resource object (from our paths.py update it might be)
        if isinstance(TEMPLATES_DIR, Path):
             loaders.append(FileSystemLoader(str(TEMPLATES_DIR)))
        
        # If we updated paths.py to return a resource traversable, we might need PackageLoader logic?
        # But for now, our paths.py returns a Path object (either extracted resource or fs path).
        # So FileSystemLoader works if it points to a real path. 
        # CAUTION: if importlib.resources returns a MultiplexedPath or something not compatible with FileSystemLoader...
        # Standard Jinja PackageLoader is better for resources.
        
        try:
            from jinja2 import PackageLoader
            loaders.append(PackageLoader('agentic_workflow', 'templates'))
        except Exception:
            pass # Fallback to whatever TEMPLATES_DIR was if it exists

        # Create environment with choice loader
        env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        
        # Register custom filters
        self._register_filters(env)
        
        return env
    
    def _register_filters(self, env: Environment) -> None:
        """Register custom Jinja2 filters for markdown formatting."""
        
        def md_list(items: List[str], prefix: str = "- ") -> str:
            """Format list as markdown bullet points."""
            if not items:
                return ""
            return "\n".join(f"{prefix}{item}" for item in items)
        
        def md_numbered_list(items: List[str]) -> str:
            """Format list as markdown numbered list."""
            if not items:
                return ""
            return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))
        
        def md_table(rows: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
            """Format list of dicts as markdown table."""
            if not rows:
                return ""
            
            # Get headers from first row if not provided
            if headers is None:
                headers = list(rows[0].keys())
            
            # Build table
            lines = []
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")
            
            for row in rows:
                values = [str(row.get(h, "")) for h in headers]
                lines.append("| " + " | ".join(values) + " |")
            
            return "\n".join(lines)
        
        def quote(text: str) -> str:
            """Wrap text in markdown quote."""
            if not text:
                return ""
            return "\n".join(f"> {line}" for line in text.split("\n"))
        
        def code(text: str, lang: str = "") -> str:
            """Wrap text in markdown code block."""
            return f"```{lang}\n{text}\n```"
        
        def slugify(text: str) -> str:
            """Convert text to URL-friendly slug."""
            text = text.lower()
            text = re.sub(r'[^\w\s-]', '', text)
            text = re.sub(r'[\s_]+', '-', text)
            return text.strip('-')
        
        def capitalize_first(text: str) -> str:
            """Capitalize first letter only."""
            if not text:
                return ""
            return text[0].upper() + text[1:]
        
        # Register all filters
        env.filters['md_list'] = md_list
        env.filters['md_numbered_list'] = md_numbered_list
        env.filters['md_table'] = md_table
        env.filters['quote'] = quote
        env.filters['code'] = code
        env.filters['slugify'] = slugify
        env.filters['capitalize_first'] = capitalize_first
    
    def render(
        self, 
        template_name: str, 
        context: Dict[str, Any],
        workflow: Optional[str] = None,
        role: Optional[str] = None
    ) -> str:
        """Render a template with context.
        
        Args:
            template_name: Template filename (e.g., 'agent_body.md.j2')
            context: Dictionary of template variables
            workflow: Override workflow for this render
            role: Override role for this render
            
        Returns:
            Rendered template string
        """
        # Recreate environment if workflow/role changed
        effective_workflow = workflow or self.workflow
        effective_role = role or self.role
        
        if effective_workflow != self.workflow or effective_role != self.role:
            env = self._create_environment(effective_workflow, effective_role)
        else:
            env = self._env
        
        # Prefer Jinja `.j2` templates. If a legacy `.tpl` is requested, try
        # to resolve a `.j2` variant first and emit a deprecation warning.
        resolved_name = template_name
        if template_name.endswith('.tpl'):
            j2_candidate = template_name.rsplit('.tpl', 1)[0] + '.j2'
            try:
                # If a .j2 template exists in the environment, use it instead
                env.get_template(j2_candidate)
                warnings.warn(
                    f"Using legacy template '{template_name}'. Prefer '{j2_candidate}' (.j2).",
                    DeprecationWarning,
                )
                resolved_name = j2_candidate
            except TemplateNotFound:
                # No .j2 exists; continue to use the .tpl file but warn
                warnings.warn(
                    f"Using legacy template '{template_name}' (.tpl). This format is deprecated; consider converting to .j2",
                    DeprecationWarning,
                )

        # Finally, attempt to render the resolved template name (j2 or tpl)
        template = env.get_template(resolved_name)
        return template.render(**context)
    
    def render_string(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a template string with context.
        
        Args:
            template_str: Template content as string
            context: Dictionary of template variables
            
        Returns:
            Rendered template string
        """
        template = self._env.from_string(template_str)
        return template.render(**context)
    
    def get_template_path(self, template_name: str) -> Optional[Path]:
        """Get the resolved path of a template.
        
        Args:
            template_name: Template filename
            
        Returns:
            Path to the resolved template, or None if not found
        """
        try:
            source, filename, _ = self._env.loader.get_source(self._env, template_name)
            return Path(filename) if filename else None
        except TemplateNotFound:
            return None


def load_canonical_json(workflow: str, filename: str) -> Dict[str, Any]:
    """Load a canonical JSON file for a workflow.
    
    Args:
        workflow: Workflow name (e.g., 'planning')
        filename: JSON filename (e.g., 'agents.json')
        
    Returns:
        Parsed JSON data
    """
    from agentic_workflow.generation.canonical_loader import load_canonical_file, CanonicalLoadError
    
    data = load_canonical_file(workflow, filename)
    if data is None:
        raise FileNotFoundError(f"Canonical file not found for {workflow}/{filename}")
    return data


def build_agent_context(
    workflow: str, 
    agent_id: str, 
    project_name: str = "project"
) -> Dict[str, Any]:
    """Build complete context for an agent template.
    
    Loads and merges data from:
    - agents.json
    - instructions.json
    - artifacts.json
    - workflow.json
    
    Args:
        workflow: Workflow name
        agent_id: Agent identifier
        project_name: Project name for context
        
    Returns:
        Complete context dictionary for template rendering
    """
    from agentic_workflow.generation.canonical_loader import load_canonical_workflow, CanonicalLoadError

    # Load all canonical data (supports JSON/YAML auto-detection)
    try:
        manifests = load_canonical_workflow(workflow)
    except CanonicalLoadError as e:
        # If loading fails (e.g. missing files), try to load what we can or raise
        # For templates, we usually need at least agents and artifacts
        raise ValueError(f"Failed to load canonical data for '{workflow}': {e}")

    agents = manifests.get('agents', {})
    instructions = manifests.get('instructions', {})
    artifacts = manifests.get('artifacts', {})
    workflow_data = manifests.get('workflow', {})
    
    # Normalize the requested agent id using workflow formatting rules
    formatted_agent_id = agent_id
    try:
        from agentic_workflow.workflow.loader import load_workflow, WorkflowError
        wf = load_workflow(workflow)
        formatted_agent_id = wf.format_agent_id(agent_id)
    except Exception:
        # Fallback to the raw agent_id if workflow loader is unavailable
        formatted_agent_id = agent_id

    # Find agent data
    agent = next((a for a in agents['agents'] if str(a.get('id', '')).upper() == str(formatted_agent_id).upper()), None)
    if not agent:
        raise ValueError(f"Agent {agent_id} (normalized: {formatted_agent_id}) not found in {workflow}")
    
    # Find instructions for agent (instructions is a list)
    instructions_list = instructions.get('instructions', [])
    agent_instr = next(
        (i for i in instructions_list if str(i.get('id', '')).upper() == str(formatted_agent_id).upper()),
        {}
    )
    
    # Build artifacts lookup
    artifact_lookup = {a['filename']: a for a in artifacts.get('artifacts', [])}
    
    # Resolve produces/consumes to full artifact data
    def resolve_artifacts(artifact_refs: Dict[str, List]) -> Dict[str, List[Dict]]:
        """Resolve artifact filenames to full artifact data."""
        result = {}
        for category, items in artifact_refs.items():
            resolved = []
            for item in items:
                # Handle both string filenames and dict objects
                if isinstance(item, str):
                    fn = item
                elif isinstance(item, dict):
                    fn = item.get('file') or item.get('filename', '')
                else:
                    continue
                
                artifact = artifact_lookup.get(fn, {'filename': fn, 'description': ''})
                resolved.append(artifact)
            result[category] = resolved
        return result
    
    produces = resolve_artifacts(agent.get('produces', {}))
    consumes = resolve_artifacts(agent.get('consumes', {}))
    
    # Find checkpoint after this agent (if any)
    checkpoint = None
    for cp in workflow_data.get('checkpoints', []):
        if str(cp.get('after_agent', '')).upper() == str(formatted_agent_id).upper():
            checkpoint = cp
            break
    
    # Find stage for this agent
    stage = None
    for s in workflow_data.get('stages', []):
        agents_list = [str(x).upper() for x in s.get('agents', [])]
        if str(formatted_agent_id).upper() in agents_list:
            stage = s
            break
    
    # Build context
    context = {
        # Project info
        'project_name': project_name,
        'workflow_name': workflow,
        'workflow_display_name': workflow_data.get('display_name', workflow.title()),
        
        # Agent info (from agents.json)
        'agent_id': formatted_agent_id,
        'agent_role': agent.get('role', ''),
        'agent_type': agent.get('type', 'core'),
        'agent_slug': agent.get('slug', ''),
        'key_responsibilities': agent.get('key_responsibilities', []),
        
        # Instructions (from instructions.json)
        'purpose': agent_instr.get('purpose', ''),
        'responsibilities': agent_instr.get('responsibilities', []),
        'workflow': agent_instr.get('workflow', {}),
        'boundaries': agent_instr.get('boundaries', {}),
        'handoff': agent_instr.get('handoff', {}),
        'domain_rules': agent_instr.get('domain_rules', []),
        
        # Artifacts (resolved)
        'produces': produces,
        'consumes': consumes,
        
        # Workflow context
        'stage': stage,
        'checkpoint': checkpoint,
        
        # Governance
        'governance': workflow_data.get('globals', {}).get('governance', {}),
        'enforcement': workflow_data.get('globals', {}).get('enforcement', {}),
        'logging_policy': workflow_data.get('globals', {}).get('logging_policy', {}),
        
        # Computed fields
        'next_agent_id': (
            agent_instr.get('handoff', {}).get('next', [{}])[0].get('id')
            if agent_instr.get('handoff', {}).get('next')
            else None
        ),
        'required_artifacts': agent_instr.get('handoff', {}).get('required_artifacts', []),
    }
    
    return context


def render_agent(
    workflow: str, 
    agent_id: str, 
    project_name: str = "project",
    template_name: str = "agent_base.md.j2"
) -> str:
    """Convenience function to render an agent template.
    
    Args:
        workflow: Workflow name
        agent_id: Agent identifier
        project_name: Project name
        template_name: Template to use
        
    Returns:
        Rendered agent template
    """
    context = build_agent_context(workflow, agent_id, project_name)
    
    # Determine role from agent type for template resolution
    role = None
    agent_type = context.get('agent_type', '')
    if agent_type == 'orchestrator':
        role = 'orchestrator'
    elif 'analyst' in context.get('agent_role', '').lower():
        role = 'analyst'
    elif 'engineer' in context.get('agent_role', '').lower():
        role = 'engineer'
    elif 'auditor' in context.get('agent_role', '').lower():
        role = 'auditor'
    
    loader = JinjaTemplateLoader(workflow=workflow, role=role)
    return loader.render(template_name, context)


def render_session(
    workflow: str,
    agent_id: str,
    project_name: str = "project",
    template_name: str = "session_base.md.j2",
    timestamp: str = "",
    extra_subs: Optional[Dict[str, Any]] = None,
) -> str:
    """Render a session template for an agent.
    
    Args:
        workflow: Workflow name
        agent_id: Agent identifier
        project_name: Project name
        template_name: Template to use
        timestamp: Session start timestamp
        
    Returns:
        Rendered session template
    """
    context = build_agent_context(workflow, agent_id, project_name)
    
    # Add session-specific fields
    context['timestamp'] = timestamp or ""
    context['context_file'] = f"agent_context/{workflow}_context_index.md"
    # Merge any extra substitutions into Jinja context
    if extra_subs:
        context.update(extra_subs)
    
    loader = JinjaTemplateLoader(workflow=workflow)
    return loader.render(template_name, context)


if __name__ == '__main__':
    # Quick test
    import sys
    
    if not JINJA2_AVAILABLE:
        display_error("Jinja2 not installed. Run: pip install jinja2")
        sys.exit(1)
    
    display_success("Jinja2 template loader initialized successfully.")
    display_info(f"Templates dir: {TEMPLATES_DIR}")
    display_info(f"Workflows dir: {WORKFLOWS_DIR}")
    display_info(f"Canonical dir: {CANONICAL_DIR}")
    
    # List available base templates
    base_path = TEMPLATES_DIR / "_base"
    if base_path.exists():
        display_info(f"\nBase templates: {list(base_path.glob('*.j2'))}")
    
    partials_path = TEMPLATES_DIR / "_partials"
    if partials_path.exists():
        display_info(f"Partials: {list(partials_path.glob('*.j2'))}")
