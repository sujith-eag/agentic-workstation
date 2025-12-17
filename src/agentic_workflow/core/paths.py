import sys
from pathlib import Path
from typing import Optional, List, Callable
from importlib import resources

__all__ = [
    # Package Paths (where code lives)
    "get_package_root",
    "get_manifests_dir",
    "get_templates_dir", 
    "get_schemas_dir",
    
    # Project Paths (where user data lives)
    "get_projects_dir",
    "get_agent_files_dir",
    "get_workflow_search_paths",
    
    # Backward Compatibility
    "PROJECTS_DIR",
    "AGENT_FILES_DIR",
]


def get_package_root() -> Path:
    """Resolve the package root Path using importlib.resources or a fallback.

    The function prefers `importlib.resources.files` but falls back to a
    repository-relative package path when resources are unavailable.
    """
    try:
        # Check if resources are available
        p = resources.files("agentic_workflow")
        return Path(p)
    except Exception:
         # Fallback to dev mode path
         return Path(__file__).resolve().parent.parent

def get_manifests_dir() -> Path:
    """Return the package `manifests` directory Path inside the package root."""
    return get_package_root() / "manifests"

def get_templates_dir() -> Path:
    """Return the package `templates` directory Path from package resources or fallback."""
    try:
        return Path(resources.files("agentic_workflow.templates"))
    except Exception:
        return get_package_root() / "templates"

def get_schemas_dir() -> Path:
    """Return the package `schemas` directory Path inside the package root."""
    return get_package_root() / "schemas"

def get_projects_dir() -> Path:
    """Resolve the projects directory as the parent of the repository root Path."""
    from .path_resolution import find_repo_root
    repo_root = find_repo_root()
    return repo_root.parent

def get_agent_files_dir() -> Path:
    """Resolve the global `agent_files` directory Path for the current repo."""
    from .path_resolution import find_repo_root
    repo_root = find_repo_root()
    return repo_root / "agent_files"

def get_workflow_search_paths(project_root: Optional[Path] = None) -> List[Path]:
    """Build an ordered list of Paths to search for workflows (project, user, system).

    Order of returned paths:
    1. Project-local workflows (``<project_root>/.agentic/workflows``)
    2. User workflows under XDG or platformdirs
    3. Bundled system workflows inside package manifests
    """
    paths = []
    
    # 1. Project
    if project_root is None:
        try:
             from .path_resolution import find_project_root
             project_root = find_project_root()
        except (ImportError, Exception):
             pass
             
    if project_root:
        paths.append(project_root / ".agentic" / "workflows")
        
    # 2. User
    # Use ConfigurationService logic or platformdirs
    # We can try to import the config service helper or replicate
    import os
    try:
        import platformdirs
        user_data = Path(platformdirs.user_data_dir("agentic-workflow", "agentic")) / "workflows"
        paths.append(user_data)
    except ImportError:
        # Fallback
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
             paths.append(Path(xdg_data) / "agentic" / "workflows")
        else:
             paths.append(Path.home() / ".local" / "share" / "agentic" / "workflows")

    # 3. System (Bundled)
    try:
        # We need the 'workflows' dir inside manifests
        # get_manifests_dir returns manifests/ or manifests/_canonical
        # Our bundled workflows are in manifests/workflows
        # Let's use resources again to be safe
        p = resources.files("agentic_workflow.manifests")
        paths.append(Path(p) / "workflows")
    except Exception:
         # Fallback
         paths.append(get_package_root() / "manifests" / "workflows")
         
    return paths


# Lazy-evaluated Path wrapper to avoid executing filesystem resolution at import time
class _LazyPath:
    """Lazily compute and proxy a `pathlib.Path` value on first access.

    This preserves backward-compatible module level symbols like
    `PROJECTS_DIR` while preventing filesystem/path-resolution from
    running at import time (which breaks the "No Ghost Logic" rule).
    """

    def __init__(self, factory: Callable[[], Path]):
        """Store a zero-argument `factory` that returns a `Path` when invoked."""
        self._factory = factory
        self._value: Optional[Path] = None

    def _ensure(self) -> None:
        """Compute and cache the backed `Path` value on first access."""
        if self._value is None:
            self._value = self._factory()

    def __getattr__(self, name):
        """Proxy attribute access to the resolved `Path` after ensuring it exists."""
        self._ensure()
        return getattr(self._value, name)

    def __fspath__(self) -> str:
        """Return the filesystem path string of the resolved Path."""
        self._ensure()
        return self._value.__fspath__()

    def __str__(self) -> str:
        """Return the string form of the resolved Path for display/logging."""
        self._ensure()
        return str(self._value)

    def __repr__(self) -> str:
        """Return a compact representation helpful for debugging the lazy wrapper."""
        return f"_LazyPath({self._factory.__name__}) -> {repr(self._value)}"

    def __truediv__(self, key):
        """Support division operator to compose paths (delegates to resolved Path)."""
        self._ensure()
        return self._value / key


# For backward compatibility: expose lazy-evaluated module symbols that act like Paths
PROJECTS_DIR = _LazyPath(get_projects_dir)
AGENT_FILES_DIR = _LazyPath(get_agent_files_dir)
