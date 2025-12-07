"""Generators module for agentic-workflow-os.

This module provides pure generation functions that produce content
from workflow packages. These are workflow-agnostic and return strings
(no file I/O).

Modules:
- docs: CLI_REFERENCE, AGENT_PIPELINE, ARTIFACT_REGISTRY, etc.
- index: project_index.md generation
- session: active_session.md generation
- agents: Agent file generation (TODO: migrate from generation/)
"""
from .docs import (
    generate_cli_reference,
    generate_agent_pipeline,
    generate_artifact_registry,
    generate_governance,
    generate_copilot_instructions,
    generate_gemini_instructions,
)
from .index import generate_project_index
from .session import (
    generate_active_session_content,
    build_session_substitutions,
    get_orchestrator_context_data,
)

__all__ = [
    # Docs
    'generate_cli_reference',
    'generate_agent_pipeline',
    'generate_artifact_registry',
    'generate_governance',
    'generate_copilot_instructions',
    'generate_gemini_instructions',
    # Index
    'generate_project_index',
    # Session
    'generate_active_session_content',
    'build_session_substitutions',
    'get_orchestrator_context_data',
]
