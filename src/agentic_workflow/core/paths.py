import sys
from pathlib import Path
from typing import Optional, List
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
    """Get package root via resources."""
    try:
        # Check if resources are available
        p = resources.files("agentic_workflow")
        return Path(p)
    except Exception:
         # Fallback to dev mode path
         return Path(__file__).resolve().parent.parent

def get_manifests_dir() -> Path:
    """Get manifests directory."""
    return get_package_root() / "manifests"

def get_templates_dir() -> Path:
    """Get templates directory."""
    try:
        return Path(resources.files("agentic_workflow.templates"))
    except Exception:
        return get_package_root() / "templates"

def get_schemas_dir() -> Path:
    """Get schemas directory."""
    return get_package_root() / "schemas"

def get_projects_dir() -> Path:
    """Get projects directory (workspace root - parent of repo root)."""
    from .path_resolution import find_repo_root
    repo_root = find_repo_root()
    return repo_root.parent

def get_agent_files_dir() -> Path:
    """Get global agent files directory."""
    from .path_resolution import find_repo_root
    repo_root = find_repo_root()
    return repo_root / "agent_files"

def get_workflow_search_paths(project_root: Optional[Path] = None) -> List[Path]:
    """
    Get list of paths to search for workflows.
    
    Order:
    1. Project: <project_root>/.agentic/workflows
    2. User: <XDG_DATA_HOME>/agentic/workflows
    3. System: <bundled_manifests>/workflows
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

# For backward compatibility
PROJECTS_DIR = get_projects_dir()
AGENT_FILES_DIR = get_agent_files_dir()
