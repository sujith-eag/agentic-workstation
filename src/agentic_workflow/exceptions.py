class AgenticError(Exception):
    """Base class for all Agentic exceptions."""
    exit_code = 1

class ConfigError(AgenticError):
    """Configuration related errors."""
    exit_code = 10

class WorkflowNotFoundError(AgenticError):
    """Workflow not found errors."""
    exit_code = 11

class AgentNotFoundError(AgenticError):
    """Agent not found errors."""
    exit_code = 12

class ProjectNotFoundError(AgenticError):
    """Project not found errors."""
    exit_code = 13

class ManifestError(AgenticError):
    """Manifest parsing or validation errors."""
    exit_code = 14
