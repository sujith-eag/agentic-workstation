"""Generation module.

This module contains scripts for generating content:
- populate_frontmatter: Generate agent files from manifest
- update_index: Update project index with artifacts
- canonical_loader: Load canonical JSON workflow files
- denormalizer: Denormalize canonical data for YAML generation
- yaml_writer: Write formatted YAML with comments
- generate_workflow_yaml: Main orchestrator for YAML generation
"""
from agentic_workflow.generation.populate_frontmatter import populate_agent_files
from agentic_workflow.generation.update_index import update_artifact, load_index, save_index
from agentic_workflow.generation.canonical_loader import (
    load_canonical_workflow,
    list_canonical_workflows,
    get_agents_list,
    get_artifacts_list,
    get_instructions_list,
    get_workflow_metadata,
    CanonicalLoadError,
)
from agentic_workflow.generation.denormalizer import (
    Denormalizer,
    denormalize_canonical,
)
from agentic_workflow.generation.yaml_writer import (
    YamlWriter,
    write_all_yaml,
)

__all__ = [
    # Legacy
    'populate_agent_files',
    'update_artifact',
    'load_index',
    'save_index',
    # Canonical loader
    'load_canonical_workflow',
    'list_canonical_workflows',
    'get_agents_list',
    'get_artifacts_list',
    'get_instructions_list',
    'get_workflow_metadata',
    'CanonicalLoadError',
    # Denormalizer
    'Denormalizer',
    'denormalize_canonical',
    # YAML writer
    'YamlWriter',
    'write_all_yaml',
]
