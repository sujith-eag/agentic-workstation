import datetime
import re
import yaml
from pathlib import Path
from typing import Optional, Tuple, Any, Dict

from agentic_workflow.core.paths import AGENT_FILES_DIR
from agentic_workflow.core.project import load_project_meta
from agentic_workflow.session import session_frontmatter as sf
from agentic_workflow.exceptions import AgentNotFoundError, ProjectNotFoundError
from agentic_workflow.cli.utils import display_info, display_success

try:
    from agentic_workflow.utils.jinja_loader import render_session
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    render_session = None


class SessionManager:
    """Manages agent sessions and context switching."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        if not self.project_dir.exists():
            raise ProjectNotFoundError(f"Project directory not found: {self.project_dir}")
        self.project_name = self.project_dir.name

    def get_workflow_name(self) -> str:
        """Get the workflow name for a project from its metadata."""
        project_name = self.project_dir.name
        meta = load_project_meta(project_name)
        if meta and 'workflow' in meta:
            return meta['workflow']
        return 'planning' # Default fallback

    def activate_agent(self, agent_id: str) -> None:
        """Activates an agent session."""
        display_info(f"Activating Agent {agent_id} in {self.project_name}...")

        # Normalize ID
        agent_id_formatted = self._normalize_agent_id(agent_id)

        # Load Content
        content, filename, source_dir = self._load_agent_content(agent_id)
        display_info(f"Loaded agent from {source_dir / filename}")

        # Parse Frontmatter
        frontmatter, body = self._parse_agent_content(content)

        # Update Session File
        self._update_active_session_file(agent_id_formatted)

        # Update Project Index
        agent_title = frontmatter.get('title', frontmatter.get('agent_role', f"Agent {agent_id_formatted}"))
        self._update_project_index(agent_title)
        
        display_success("Activation complete.")

    def _normalize_agent_id(self, agent_id_raw: str) -> str:
        if agent_id_raw.lower() == 'a00' or agent_id_raw.lower() == 'orch':
            return 'A-00'
        elif agent_id_raw.startswith('A') and len(agent_id_raw) == 3 and agent_id_raw[1:].isdigit():
            return f"A-{agent_id_raw[1:]}"
        elif agent_id_raw.isdigit():
            return f"A-{int(agent_id_raw):02d}"
        else:
            return agent_id_raw

    def _load_agent_content(self, agent_id: str) -> Tuple[str, str, Path]:
        """Finds and loads the agent file by ID."""
        raw_id = str(agent_id).upper().lstrip('A').lstrip('0') or '0'
        
        patterns = []
        if raw_id == '0' or raw_id.lower() == 'orch':
            patterns = ['Orchestrator_prompt.md', 'A00_', 'A-00_']
        else:
            patterns = [
                f"A{raw_id}_",           # A1_
                f"A{raw_id.zfill(2)}_",  # A01_
                f"A-{raw_id}_",          # A-1_
                f"A-{raw_id.zfill(2)}_", # A-01_
            ]

        search_dirs = []
        
        # 1. Project-local agent_files
        project_agents_dir = self.project_dir / 'agent_files'
        if project_agents_dir.exists():
            search_dirs.append(project_agents_dir)
        
        # 2. Global workflow-specific agent_files
        workflow_name = self.get_workflow_name()
        # Note: In Phase 1 we will rely on canonical_loader, but for now reuse AGENT_FILES_DIR
        # Use AGENT_FILES_DIR from paths (which points to root/agent_files currently)
        # Ideally we should look into manifests, but keeping compat with existing structure for Phase 0
        workflow_agents_dir = AGENT_FILES_DIR / workflow_name
        if workflow_agents_dir.exists():
            search_dirs.append(workflow_agents_dir)
            
        # Search
        for search_dir in search_dirs:
            for f in search_dir.glob("*.md"):
                for pattern in patterns:
                    if f.name.startswith(pattern) or f.name == pattern:
                        with open(f, "r") as file:
                            return file.read(), f.name, search_dir
        
        # Fallback regex search
        for search_dir in search_dirs:
            for f in search_dir.glob("*.md"):
                with open(f, "r") as file:
                    content = file.read()
                    if re.search(f"agent_id: ['\"]?{raw_id}['\"]?", content) or \
                       re.search(f"agent_id: {agent_id}", content):
                        return content, f.name, search_dir

        raise AgentNotFoundError(f"Agent {agent_id} not found in project or workflow '{workflow_name}'")

    def _parse_agent_content(self, content: str) -> Tuple[Dict, str]:
        fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        frontmatter = yaml.safe_load(fm_match.group(1)) if fm_match else {}
        body_match = re.search(r"\n---\n(.*)", content, re.DOTALL)
        body = body_match.group(1).strip() if body_match else content
        return frontmatter, body

    def _update_active_session_file(self, agent_id: str) -> None:
        session_path = self.project_dir / "agent_context" / "active_session.md"
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        workflow_name = self.get_workflow_name()
        
        if not JINJA2_AVAILABLE:
             raise ImportError("Jinja2 is required")
             
        content = render_session(
            workflow=workflow_name,
            agent_id=agent_id,
            project_name=self.project_name,
            timestamp=datetime.datetime.now().isoformat()
        )
        sf.write_session_file(session_path, content)

    def _update_project_index(self, agent_role: str) -> None:
        index_path = self.project_dir / "project_index.md"
        if not index_path.exists():
            return
            
        with open(index_path, "r") as f:
            content = f.read()
            
        content = re.sub(r"\*\*Active Agent:\*\* .*", f"**Active Agent:** {agent_role}", content)
        content = re.sub(r"\*\*Last Action:\*\* .*", f"**Last Action:** Session started for {agent_role}", content)
        
        with open(index_path, "w") as f:
            f.write(content)
