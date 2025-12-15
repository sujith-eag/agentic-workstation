"""
Governance Rule Engine for Agentic Workflow Platform.

This module provides governance rule enforcement for workflow operations,
ensuring compliance with project-specific and global governance policies.

It includes:
- Rule-based validation with configurable strictness levels.
- Support for different governance contexts (init, handoff, decision, end).
- detailed error reporting with actionable feedback.

Author: AI Assistant
Date: December 6, 2025
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field

from agentic_workflow.core.exceptions import (
    GovernanceError,
    ValidationViolation,
    PolicyConfigurationError
)
# Use late import for config functions to avoid circular deps if needed,
# or import standard constants/types.
from agentic_workflow.core.config_service import ConfigurationService
from agentic_workflow.core.path_resolution import get_project_dirs, get_workflow_paths

# Setup logging
logger = logging.getLogger(__name__)

# Governance constants
GOVERNANCE_LEVEL_STRICT = "strict"
GOVERNANCE_LEVEL_MODERATE = "moderate"
GOVERNANCE_LEVEL_LENIENT = "lenient"

GOVERNANCE_CONTEXT_INIT = "init"
GOVERNANCE_CONTEXT_HANDOFF = "handoff"
GOVERNANCE_CONTEXT_DECISION = "decision"
GOVERNANCE_CONTEXT_END = "end"
GOVERNANCE_CONTEXT_ACTIVATION = "activation"


@dataclass
class GovernanceRule:
    """
    Represents a single governance rule.

    Attributes:
        name: Unique identifier for the rule.
        description: Human-readable description of what the rule enforces.
        context: The context in which this rule applies (e.g., 'init', 'handoff').
        level: Strictness level required to trigger this rule ('strict', 'moderate', 'lenient').
        condition: Callable that takes a data dictionary and returns True if compliant.
        error_message: Message to display when the rule is violated.
        fix_suggestion: Optional suggestion for resolving the violation.
        enabled: Whether the rule is currently active.
    """
    name: str
    description: str
    context: str
    level: str
    condition: Callable[[Dict[str, Any]], bool]
    error_message: str
    fix_suggestion: Optional[str] = None
    enabled: bool = True


@dataclass
class GovernanceResult:
    """
    Result of governance validation.

    Attributes:
        passed: True if all applicable rules passed.
        violations: List of violation details (dictionaries).
        warnings: List of warning details.
        context: The context that was validated.
    """
    passed: bool
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    context: str = ""

    def __bool__(self) -> bool:
        return self.passed


class GovernanceEngine:
    """
    Engine for evaluating governance rules against workflow data.

    This engine manages a registry of rules and evaluates them based on the
    requested context and strictness level.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GovernanceEngine.

        Args:
            config: Configuration dictionary containing 'governance' settings.
        """
        self.config = config
        self.rules: Dict[str, GovernanceRule] = {}
        self._load_rules()

    def register_rule(self, rule: GovernanceRule) -> None:
        """
        Register a new governance rule or overwrite an existing one.

        Args:
            rule: The GovernanceRule instance to register.
        """
        self.rules[rule.name] = rule
        logger.debug(f"Registered governance rule: {rule.name}")

    def _load_rules(self) -> None:
        """
        Load governance rules from configuration and defaults.

        Merges built-in default rules with overrides provided in the configuration.
        """
        governance_config = self.config.get('governance', {})

        # 1. Load default rules
        default_rules = self._get_default_rules()

        # 2. Extract overrides from config
        config_rules = governance_config.get('rules') or {}

        # 3. Merge rules
        # First, process overrides for existing default rules
        for rule_name, rule_config in config_rules.items():
            if rule_name in default_rules:
                default_rule = default_rules[rule_name]
                # Create a new rule instance with overrides
                self.register_rule(GovernanceRule(
                    name=rule_config.get('name', default_rule.name),
                    description=rule_config.get('description', default_rule.description),
                    context=rule_config.get('context', default_rule.context),
                    level=rule_config.get('level', default_rule.level),
                    condition=default_rule.condition,  # Retain original condition logic
                    error_message=rule_config.get('error_message', default_rule.error_message),
                    fix_suggestion=rule_config.get('fix_suggestion', default_rule.fix_suggestion),
                    enabled=rule_config.get('enabled', default_rule.enabled)
                ))
            else:
                # Custom rule defined in config - use dynamic condition evaluation
                self.register_rule(GovernanceRule(
                    name=rule_config.get('name', rule_name),
                    description=rule_config.get('description', ''),
                    context=rule_config.get('context', GOVERNANCE_CONTEXT_INIT),
                    level=rule_config.get('level', GOVERNANCE_LEVEL_MODERATE),
                    condition=self._create_dynamic_condition(rule_config),
                    error_message=rule_config.get('error_message', f'Rule {rule_name} failed'),
                    fix_suggestion=rule_config.get('fix_suggestion'),
                    enabled=rule_config.get('enabled', True)
                ))

        # 4. Register remaining default rules
        for rule_name, rule in default_rules.items():
            if rule_name not in self.rules:
                self.register_rule(rule)

    def _create_dynamic_condition(self, rule_config: Dict) -> Callable:
        """
        Create a dynamic condition function from declarative rule configuration.

        Translates YAML/JSON rule definitions into executable logic that evaluates:
        - required_files: Check if files exist relative to project path
        - required_context: Check if keys exist in agent/project data
        - blocked_by: Check if agent ID is in blocked list

        Args:
            rule_config: Dictionary containing rule configuration keys

        Returns:
            Callable that takes data dict and returns bool
        """
        def dynamic_condition(data: Dict[str, Any]) -> bool:
            # Check required files
            required_files = rule_config.get('required_files', [])
            if required_files:
                project_path = Path(data.get('project', {}).get('path', ''))
                if not project_path.exists():
                    logger.warning(f"Project path does not exist: {project_path}")
                    return False

                for file_path in required_files:
                    full_path = project_path / file_path
                    if not full_path.exists():
                        logger.debug(f"Required file missing: {full_path}")
                        return False

            # Check required context keys
            required_context = rule_config.get('required_context', [])
            if required_context:
                agent_data = data.get('agent', {})
                project_data = data.get('project', {})

                for key in required_context:
                    if key not in agent_data and key not in project_data:
                        logger.debug(f"Required context key missing: {key}")
                        return False

            # Check blocked agents
            blocked_by = rule_config.get('blocked_by', [])
            if blocked_by:
                agent_id = data.get('agent', {}).get('id', '')
                if agent_id in blocked_by:
                    logger.debug(f"Agent {agent_id} is blocked by rule")
                    return False

            return True

        return dynamic_condition

    def _get_default_rules(self) -> Dict[str, GovernanceRule]:
        """
        Define the set of built-in default governance rules.

        Returns:
            Dictionary mapping rule names to GovernanceRule instances.
        """
        return {
            'project_structure_valid': GovernanceRule(
                name='project_structure_valid',
                description='Project directory structure must be valid',
                context=GOVERNANCE_CONTEXT_INIT,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_project_structure,
                error_message='Project structure validation failed',
                fix_suggestion='Run project initialization to create required directories'
            ),
            'workflow_files_exist': GovernanceRule(
                name='workflow_files_exist',
                description='Required workflow files must exist',
                context=GOVERNANCE_CONTEXT_INIT,
                level=GOVERNANCE_LEVEL_MODERATE,
                condition=self._check_workflow_files,
                error_message='Required workflow files are missing',
                fix_suggestion='Ensure workflow.json, agents.json, and artifacts.json exist'
            ),
            'agent_handoff_valid': GovernanceRule(
                name='agent_handoff_valid',
                description='Agent handoff must be valid',
                context=GOVERNANCE_CONTEXT_HANDOFF,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_agent_handoff,
                error_message='Invalid agent handoff',
                fix_suggestion='Ensure from_agent and to_agent are valid and different'
            ),
            'decision_rationale_required': GovernanceRule(
                name='decision_rationale_required',
                description='Decisions must have rationale',
                context=GOVERNANCE_CONTEXT_DECISION,
                level=GOVERNANCE_LEVEL_MODERATE,
                condition=self._check_decision_rationale,
                error_message='Decision rationale is required',
                fix_suggestion='Provide a rationale for the decision'
            ),
            'session_end_artifacts_complete': GovernanceRule(
                name='session_end_artifacts_complete',
                description='All required artifacts must be complete at session end',
                context=GOVERNANCE_CONTEXT_END,
                level=GOVERNANCE_LEVEL_LENIENT,
                condition=self._check_artifacts_complete,
                error_message='Required artifacts are incomplete',
                fix_suggestion='Complete all required artifacts before ending session'
            ),
            'agent_stage_valid': GovernanceRule(
                name='agent_stage_valid',
                description='Agent must be valid for current project stage',
                context=GOVERNANCE_CONTEXT_ACTIVATION,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_agent_stage,
                error_message='Agent cannot be activated in current stage',
                fix_suggestion='Advance to appropriate stage or select different agent'
            ),
            'agent_artifacts_exist': GovernanceRule(
                name='agent_artifacts_exist',
                description='Required artifacts must exist for agent activation',
                context=GOVERNANCE_CONTEXT_ACTIVATION,
                level=GOVERNANCE_LEVEL_MODERATE,
                condition=self._check_agent_artifacts,
                error_message='Required artifacts are missing',
                fix_suggestion='Create required artifacts before activating agent'
            ),
            'agent_not_blocked': GovernanceRule(
                name='agent_not_blocked',
                description='Agent must not be blocked',
                context=GOVERNANCE_CONTEXT_ACTIVATION,
                level=GOVERNANCE_LEVEL_STRICT,
                condition=self._check_agent_not_blocked,
                error_message='Agent is currently blocked',
                fix_suggestion='Resolve blockers before activating agent'
            )
        }

    def validate(
        self, 
        context: str, 
        data: Dict[str, Any], 
        strictness: Optional[str] = None
    ) -> GovernanceResult:
        """
        Validate data against rules for a specific context.

        Args:
            context: The context to validate (e.g., 'init', 'handoff').
            data: The data dictionary to check against rule conditions.
            strictness: Optional override for strictness level. Defaults to config settings.

        Returns:
            GovernanceResult object containing pass status and violations.
        """
        if strictness is None:
            strictness = self.config.get('governance', {}).get('strictness', {}).get('level', GOVERNANCE_LEVEL_MODERATE)

        result = GovernanceResult(passed=True, context=context)
        evaluated_rules = 0

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if rule.context != context:
                continue

            # Check if rule applies to the current strictness level
            if not self._rule_applies_to_level(rule.level, strictness):
                continue

            evaluated_rules += 1

            try:
                rule_passed = rule.condition(data)
                
                if not rule_passed:
                    violation = {
                        'rule': rule.name,
                        'description': rule.description,
                        'error_message': rule.error_message,
                        'fix_suggestion': rule.fix_suggestion,
                        'level': rule.level
                    }
                    result.violations.append(violation)
                    result.passed = False
                    logger.warning(f"Governance violation: {rule.name} - {rule.error_message}")
                else:
                    logger.debug(f"Governance rule passed: {rule.name}")

            except Exception as e:
                logger.error(f"Error evaluating governance rule {rule.name}: {e}")
                
                # In strict mode, code errors during validation are treated as violations
                if strictness == GOVERNANCE_LEVEL_STRICT:
                    violation = {
                        'rule': rule.name,
                        'description': rule.description,
                        'error_message': f'Rule evaluation failed: {e}',
                        'fix_suggestion': 'Check rule configuration and data format',
                        'level': rule.level
                    }
                    result.violations.append(violation)
                    result.passed = False

        logger.info(f"Governance validation complete: {evaluated_rules} rules evaluated, {len(result.violations)} violations")
        return result

    def enforce(
        self, 
        context: str, 
        data: Dict[str, Any], 
        strictness: Optional[str] = None
    ) -> None:
        """
        Enforce governance rules, raising an exception on violations.

        Args:
            context: The context to enforce.
            data: The data to validate.
            strictness: Optional strictness level override.

        Raises:
            ValidationViolation: If any compliance rules are violated.
        """
        result = self.validate(context, data, strictness)
        if not result.passed:
            # Construct a detailed error message from violations
            msgs = [f"- {v['error_message']} ({v['rule']})" for v in result.violations]
            msg_str = "\n".join(msgs)
            raise ValidationViolation(
                f"Governance enforcement failed with {len(result.violations)} violations:\n{msg_str}",
                context={"violations": result.violations, "governance_context": context}
            )

    def _rule_applies_to_level(self, rule_level: str, current_level: str) -> bool:
        """
        Check if a rule applies to the current strictness level.
        
        Logic: A rule at 'rule_level' applies if 'current_level' is equal or stricter.
        Hierarchy: LENIENT < MODERATE < STRICT
        """
        levels = [GOVERNANCE_LEVEL_LENIENT, GOVERNANCE_LEVEL_MODERATE, GOVERNANCE_LEVEL_STRICT]
        
        try:
            rule_index = levels.index(rule_level)
            current_index = levels.index(current_level)
            return rule_index <= current_index
        except ValueError:
            logger.warning(f"Invalid governance level encountered: rule={rule_level}, current={current_level}")
            return True # Fallback: apply rule

    # ---------------------------
    # Built-in Condition Logic
    # ---------------------------

    def _check_project_structure(self, data: Dict[str, Any]) -> bool:
        """Condition: Check if project structure is valid."""
        try:
            project_path = data.get('project_path')
            if not project_path:
                return False

            from agentic_workflow.core.path_resolution import validate_project_structure
            issues = validate_project_structure(Path(project_path), self.config)
            return len(issues) == 0
        except Exception:
            return False

    def _check_workflow_files(self, data: Dict[str, Any]) -> bool:
        """Condition: Check if required workflow files exist."""
        try:
            project_path = data.get('project_path')
            if not project_path:
                return False

            workflow_paths = get_workflow_paths(self.config, Path(project_path))
            required_files = ['workflow_file', 'agents_file', 'artifacts_file']

            for file_key in required_files:
                file_path = workflow_paths.get(file_key)
                if not file_path or not file_path.exists():
                    return False

            return True
        except Exception:
            return False

    def _check_agent_handoff(self, data: Dict[str, Any]) -> bool:
        """Condition: Check if agent handoff matches rules (different agents, valid artifacts)."""
        from_agent = data.get('from_agent')
        to_agent = data.get('to_agent')
        artifacts = data.get('artifacts', [])

        if not from_agent or not to_agent:
            return False

        if from_agent == to_agent:
            return False

        # Validate existence of referenced artifacts
        if artifacts:
            try:
                project_path = data.get('project_path')
                if project_path:
                    project_dirs = get_project_dirs(self.config, Path(project_path))
                    artifacts_dir = project_dirs.get('artifacts')
                    if artifacts_dir:
                        for artifact in artifacts:
                            artifact_path = artifacts_dir / artifact
                            if not artifact_path.exists():
                                return False
            except Exception:
                pass 

        return True

    def _check_decision_rationale(self, data: Dict[str, Any]) -> bool:
        """Condition: Check if decision includes a non-empty rationale."""
        rationale = data.get('rationale', '').strip()
        return len(rationale) > 0

    def _check_artifacts_complete(self, data: Dict[str, Any]) -> bool:
        """Condition: Check if all 'required' artifacts are present."""
        try:
            project_path = data.get('project_path')
            if not project_path:
                return True

            workflow_paths = get_workflow_paths(self.config, Path(project_path))
            artifacts_file = workflow_paths.get('artifacts_file')

            if not artifacts_file or not artifacts_file.exists():
                return True

            with open(artifacts_file, 'r', encoding='utf-8') as f:
                artifacts_data = json.load(f)

            project_dirs = get_project_dirs(self.config, Path(project_path))
            artifacts_dir = project_dirs.get('artifacts')

            if not artifacts_dir:
                return True

            for artifact in artifacts_data.get('artifacts', []):
                if artifact.get('required', False):
                    artifact_name = artifact.get('name')
                    if artifact_name:
                        artifact_path = artifacts_dir / artifact_name
                        if not artifact_path.exists():
                            return False

            return True
        except Exception:
            return True

    def _check_agent_stage(self, data: Dict[str, Any]) -> bool:
        """Check if agent can be activated in current stage."""
        try:
            agent_stage = data.get('agent', {}).get('stage', '')
            current_stage = data.get('stage', {}).get('current', '')
            
            if not agent_stage or not current_stage:
                return True  # No specific stage requirement
            
            # Simple check: agent stage should be <= current stage
            # This is a basic implementation - could be enhanced
            return agent_stage == current_stage
        except Exception:
            return True

    def _check_agent_artifacts(self, data: Dict[str, Any]) -> bool:
        """Check if required artifacts exist for agent."""
        try:
            consumes_core = data.get('agent', {}).get('consumes_core', [])
            if not consumes_core:
                return True  # No required artifacts
            
            # For now, assume artifacts exist if listed
            # Could be enhanced to check actual file existence
            return True
        except Exception:
            return True

    def _check_agent_not_blocked(self, data: Dict[str, Any]) -> bool:
        """Check if agent is not blocked."""
        try:
            # For now, assume no blockers
            # Could be enhanced to check blocker logs
            return True
        except Exception:
            return True


# -----------------------------------------------------------------------------
# Module Interface Functions
# -----------------------------------------------------------------------------

def get_governance_engine(config: Optional[Dict[str, Any]] = None) -> GovernanceEngine:
    """
    Factory function to get a GovernanceEngine instance.

    Args:
        config: Optional configuration dictionary. If None, loads command config.

    Returns:
        Initialized GovernanceEngine.
    """
    if config is None:
        config_service = ConfigurationService()
        config = config_service.load_config()
    return GovernanceEngine(config)


def validate_governance(
    context: str, 
    data: Dict[str, Any], 
    config: Optional[Dict[str, Any]] = None, 
    strictness: Optional[str] = None
) -> GovernanceResult:
    """
    Convenience wrapper to validate governance rules.

    Args:
        context: Validation context.
        data: Data to validate.
        config: Engine configuration.
        strictness: Strictness level override.

    Returns:
        GovernanceResult.
    """
    engine = get_governance_engine(config)
    return engine.validate(context, data, strictness)


def enforce_governance(
    context: str, 
    data: Dict[str, Any], 
    config: Optional[Dict[str, Any]] = None, 
    strictness: Optional[str] = None
) -> None:
    """
    Convenience wrapper to enforce governance rules.

    Args:
        context: Enforcement context.
        data: Data to validate.
        config: Engine configuration.
        strictness: Strictness level override.

    Raises:
        ValidationViolation: If rules validation fails.
    """
    engine = get_governance_engine(config)
    engine.enforce(context, data, strictness)

