"""Session lifecycle management module.

This module contains scripts for managing agent sessions:
- init_project: Create new project structure
- activate_agent: Switch to a specific agent
- end_session: Archive and reset session
- session_frontmatter: YAML frontmatter utilities
"""

from .session_frontmatter import (
    merge_frontmatter,
    render_frontmatter_yaml,
    load_frontmatter_from_text,
    write_session_file,
    build_layer3,
    extract_layers_from_template,
    render_template_body,
    orchestrator_frontmatter,
    default_orchestrator_substitutions,
    build_orchestrator_session_from_template,
)

__all__ = [
    'merge_frontmatter',
    'render_frontmatter_yaml',
    'load_frontmatter_from_text',
    'write_session_file',
    'build_layer3',
    'extract_layers_from_template',
    'render_template_body',
    'orchestrator_frontmatter',
    'default_orchestrator_substitutions',
    'build_orchestrator_session_from_template',
]
