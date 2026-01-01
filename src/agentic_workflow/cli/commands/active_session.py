"""
Active Session Commands
Focus: The 'Doing' commands (Activate, Handoff, Decision, End).
"""
import click
from typing import Optional
from rich_click import RichCommand
from ..handlers.session_handlers import SessionHandlers
from ..handlers.entry_handlers import EntryHandlers
from ..display import exit_with_error
from agentic_workflow.services import LedgerService

@click.command(cls=RichCommand)
@click.argument('agent_id')
@click.pass_context
def activate(ctx: click.Context, agent_id: str):
    """Activate an agent session to begin work.
    
    Starts a new agent session, advancing the workflow stage if needed.
    Checks gate conditions before activation to ensure prerequisites are met.
    
    \b
    Examples:
      $ agentic activate A-01
      $ agentic activate researcher
    """
    # Context-aware config injection (if available)
    console = ctx.obj.get('console')
    config = ctx.obj.get('config') if ctx.obj else None
    session_handlers = SessionHandlers(console, config)
    
    try:
        session_handlers.handle_activate(agent_id=agent_id)
    except Exception as e:
        exit_with_error(f"Activation failed: {e}", console)

@click.command(cls=RichCommand)
@click.option('--to', required=True, help='Target agent ID')
@click.option('--from', 'from_agent', help='Source agent ID (Auto-detected if active)')
@click.option('--artifacts', help='Comma-separated artifact names')
@click.option('--notes', help='Handoff notes')
@click.pass_context
def handoff(ctx: click.Context, to: str, from_agent: str, artifacts: Optional[str] = None, notes: Optional[str] = None):
    """Record a handoff to transfer work between agents.
    
    Validates the handoff against workflow rules before recording.
    Auto-detects the source agent from the active session if not specified.
    
    \b
    Examples:
      $ agentic handoff --to A-02
      $ agentic handoff --from A-01 --to A-02 --artifacts "spec.md,diagram.png"
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    entry_handlers = EntryHandlers(console)
    
    # Auto-detect 'from_agent' if not supplied
    if not from_agent and project_name:
        ledger_service = LedgerService()
        active_session = ledger_service.get_active_session(project_name)
        if active_session:
            from_agent = active_session.get('agent_id')
        else:
            raise click.UsageError(
                f"No active agent session found for project '{project_name}'. "
                "Please specify --from or activate an agent first."
            )

    try:
        entry_handlers.handle_handoff(
            project=project_name, # Passed explicitly from context
            from_agent=from_agent,
            to_agent=to,
            artifacts=artifacts,
            notes=notes
        )
    except Exception as e:
        exit_with_error(f"Handoff failed: {e}", console)

@click.command(cls=RichCommand)
@click.option('--title', required=True, help='Decision title')
@click.option('--rationale', required=True, help='Reasoning behind the decision')
@click.option('--agent', help='Agent ID making the decision')
@click.pass_context
def decision(ctx: click.Context, title: str, rationale: str, agent: Optional[str] = None):
    """Record a key architectural or design decision.
    
    Documents important project decisions with title and rationale.
    Creates an audit trail for future reference.
    
    \b
    Examples:
      $ agentic decision --title "Use PostgreSQL" --rationale "Need ACID compliance"
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    entry_handlers = EntryHandlers(console)

    try:
        entry_handlers.handle_decision(
            project=project_name,
            title=title,
            rationale=rationale,
            agent=agent
        )
    except Exception as e:
        exit_with_error(f"Decision recording failed: {e}", console)

@click.command(cls=RichCommand, name='end')
@click.pass_context
def end_session(ctx: click.Context):
    """End the current session and archive state.
    
    Closes the active agent session, archives session data,
    and resets the project to an idle state.
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    session_handlers = SessionHandlers(console, config)
    
    try:
        session_handlers.handle_end(project=project_name)
    except Exception as e:
        exit_with_error(f"Failed to end session: {e}", console)

@click.command(cls=RichCommand, name='check-handoff')
@click.argument('agent_id')
@click.pass_context
def check_handoff(ctx: click.Context, agent_id: str):
    """Check if a handoff exists for a specific agent.
    
    Verifies whether there are any pending handoffs directed
    to the specified agent ID.
    
    \b
    Examples:
      $ agentic check-handoff A-02
    """
    from ..handlers.query_handlers import QueryHandlers
    console = ctx.obj.get('console')
    query_handlers = QueryHandlers(console)
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    
    try:
        query_handlers.handle_check_handoff(project=project_name, agent_id=agent_id)
    except Exception as e:
        exit_with_error(f"Handoff check failed: {e}", console)

@click.command(cls=RichCommand)
@click.option('--target', required=True, help='Feedback target')
@click.option('--severity', required=True, type=click.Choice(['low', 'medium', 'high', 'critical']), help='Severity level')
@click.option('--summary', required=True, help='Feedback summary')
@click.pass_context
def feedback(ctx: click.Context, target: str, severity: str, summary: str):
    """Record feedback on an agent, artifact, or process.
    
    Captures structured feedback with severity levels for tracking
    quality issues and improvement opportunities.
    
    \b
    Examples:
      $ agentic feedback --target A-01 --severity high --summary "Missing error handling"
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    entry_handlers = EntryHandlers(console)
    
    try:
        entry_handlers.handle_feedback(
            project=project_name,
            target=target,
            severity=severity,
            summary=summary
        )
    except Exception as e:
        exit_with_error(f"Feedback recording failed: {e}", console)

@click.command(cls=RichCommand)
@click.option('--title', required=True, help='Blocker title')
@click.option('--description', required=True, help='Blocker description')
@click.option('--blocked-agents', help='Comma-separated list of blocked agent IDs')
@click.pass_context
def blocker(ctx: click.Context, title: str, description: str, blocked_agents: Optional[str] = None):
    """Record a blocker that prevents progress.
    
    Documents issues blocking one or more agents from proceeding.
    Tracks which agents are affected for workflow visibility.
    
    \b
    Examples:
      $ agentic blocker --title "API down" --description "Cannot access external API"
      $ agentic blocker --title "Missing spec" --description "Requirements unclear" --blocked-agents "A-02,A-03"
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    entry_handlers = EntryHandlers(console)
    
    # Parse blocked_agents if provided
    blocked_agents_list = None
    if blocked_agents:
        blocked_agents_list = [agent.strip() for agent in blocked_agents.split(',')]
    
    try:
        entry_handlers.handle_blocker(
            project=project_name,
            title=title,
            description=description,
            blocked_agents=blocked_agents_list
        )
    except Exception as e:
        exit_with_error(f"Blocker recording failed: {e}", console)

@click.command(cls=RichCommand)
@click.option('--trigger', required=True, help='What triggered the iteration')
@click.option('--impacted-agents', required=True, help='Comma-separated list of impacted agent IDs')
@click.option('--description', required=True, help='Iteration description')
@click.option('--version-bump', type=click.Choice(['patch', 'minor', 'major']), default='patch', help='Version bump type')
@click.pass_context
def iteration(ctx: click.Context, trigger: str, impacted_agents: str, description: str, version_bump: str):
    """Record a development iteration or major change.
    
    Tracks significant changes that require rework across agents.
    Automatically increments version based on the severity of change.
    
    \b
    Examples:
      $ agentic iteration --trigger "Requirements change" --impacted-agents "A-01,A-02" --description "Added authentication" --version-bump minor
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    entry_handlers = EntryHandlers(console)
    
    # Parse impacted_agents
    impacted_agents_list = [agent.strip() for agent in impacted_agents.split(',')]
    
    try:
        entry_handlers.handle_iteration(
            project=project_name,
            trigger=trigger,
            impacted_agents=impacted_agents_list,
            description=description,
            version_bump=version_bump
        )
    except Exception as e:
        exit_with_error(f"Iteration recording failed: {e}", console)

@click.command(cls=RichCommand)
@click.option('--assumption', required=True, help='The assumption text')
@click.option('--rationale', required=True, help='Rationale for the assumption')
@click.pass_context
def assumption(ctx: click.Context, assumption: str, rationale: str):
    """Record an assumption that may affect the project.
    
    Documents assumptions made during development that could
    impact future work if they prove incorrect.
    
    \b
    Examples:
      $ agentic assumption --assumption "Users have reliable internet" --rationale "Product is cloud-only"
    """
    console = ctx.obj.get('console')
    config = ctx.obj.get('config')
    project_name = config.project.root_path.name if config and config.is_project_context else None
    entry_handlers = EntryHandlers(console)
    
    try:
        entry_handlers.handle_assumption(
            project=project_name,
            assumption=assumption,
            rationale=rationale
        )
    except Exception as e:
        exit_with_error(f"Assumption recording failed: {e}", console)


__all__ = [
    "activate",
    "handoff", 
    "decision",
    "end_session",
    "check_handoff",
    "feedback",
    "blocker",
    "iteration",
    "assumption"
]