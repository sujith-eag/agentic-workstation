"""
CLI Command Modules.

These modules define the user-facing command structure using Click.
They map 1:1 to the domain-specific Handlers.

Modules:
- global_ops: Commands for system config and initialization (init, config).
- project_ops: Commands for project management (list, status, delete).
- active_session: Commands for the active work loop (activate, handoff, decision).
"""

from . import active_session
from . import global_ops
from . import project_ops

__all__ = [
    "active_session",
    "global_ops",
    "project_ops",
]
