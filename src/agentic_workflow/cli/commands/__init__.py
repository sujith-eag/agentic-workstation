#!/usr/bin/env python3
"""CLI command groups for Agentic Workflow."""

# Import command groups
from .project import project
from .workflow import workflow

# Placeholder for future commands
# from .agent import agent
# from .dev import dev

__all__ = ['project', 'workflow']