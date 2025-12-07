"""
Governance Rule Extraction Logic.

This module handles the extraction of governance rules from workflow manifests.
It translates manifest definitions into the internal governance configuration format.
"""

import logging
from typing import Dict, Any, List

from agentic_workflow.core.governance import (
    GOVERNANCE_LEVEL_STRICT,
    GOVERNANCE_LEVEL_MODERATE,
    GOVERNANCE_LEVEL_LENIENT
)

logger = logging.getLogger(__name__)


def extract_governance_from_workflow(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract governance rules from raw workflow manifest data.

    This maps workflow-specific governance settings (from YAML/JSON) into the
    internal configuration format used by the GovernanceEngine.

    Args:
        workflow_data: Raw dictionary loaded from workflow manifest.

    Returns:
        Dictionary compatible with GovernanceEngine config structure.
    """
    governance_config = {}
    workflow_info = workflow_data.get('workflow', {})
    workflow_governance = workflow_info.get('governance', {})

    # If no governance in manifest, return empty config but don't error
    if not workflow_governance:
        # Note: We might still want to extract implicit rules from enforcement settings if they exist
        pass

    # 1. Extract strictness level
    enforcement_config = workflow_info.get('config', {}).get('enforcement', {})
    mode = enforcement_config.get('mode', 'moderate')

    level_mapping = {
        'strict': GOVERNANCE_LEVEL_STRICT,
        'moderate': GOVERNANCE_LEVEL_MODERATE,
        'lenient': GOVERNANCE_LEVEL_MODERATE
    }
    governance_config['strictness'] = {
        'level': level_mapping.get(mode, GOVERNANCE_LEVEL_MODERATE)
    }

    # 2. Extract specific rule overrides
    rules = {}
    
    # Checkpoint gating rule
    checkpoint_gating = enforcement_config.get('checkpoint_gating', 'moderate')
    if checkpoint_gating == 'strict':
        rules['strict_checkpoint_gating'] = {
            'name': 'Strict Checkpoint Gating',
            'description': 'All checkpoints must be completed before proceeding',
            'context': 'handoff',
            'level': 'strict',
            'error_message': 'Cannot proceed without completing required checkpoints',
            'fix_suggestion': 'Complete all upstream checkpoints before handoff'
        }

    # Handoff gating rule
    handoff_gating = enforcement_config.get('handoff_gating', 'moderate')
    if handoff_gating == 'strict':
        rules['strict_handoff_gating'] = {
            'name': 'Strict Handoff Gating',
            'description': 'All handoffs must be properly logged',
            'context': 'handoff',
            'level': 'strict',
            'error_message': 'Handoff must be properly logged before proceeding',
            'fix_suggestion': 'Ensure handoff is logged in agent_log/exchange_log.md'
        }

    # Required artifacts rule (Derived from artifacts section)
    _extract_artifact_rules(workflow_data, rules)

    # Decision logging rule
    logging_config = workflow_info.get('config', {}).get('logging', {})
    if logging_config.get('require_decision_log', False):
        rules['decision_logging_required'] = {
            'name': 'Decision Logging Required',
            'description': 'All decisions must be logged',
            'context': 'decision',
            'level': 'moderate',
            'error_message': 'Decision must be logged',
            'fix_suggestion': 'Log decision in agent_log/decision_log.md'
        }

    # Naming convention rule
    artifact_naming = workflow_governance.get('artifact_naming', {})
    if artifact_naming.get('enforce_snake_case', False):
        rules['snake_case_artifacts'] = {
            'name': 'Snake Case Artifacts',
            'description': 'All artifacts must follow snake_case naming',
            'context': 'init',
            'level': 'lenient',
            'error_message': 'Artifact names must be in snake_case',
            'fix_suggestion': 'Rename artifacts to follow snake_case convention'
        }

    governance_config['rules'] = rules
    return governance_config


def _extract_artifact_rules(workflow_data: Dict[str, Any], rules: Dict[str, Any]) -> None:
    """
    Helper to extract artifact-related governance rules.

    Args:
        workflow_data: Source workflow data.
        rules: Target rules dictionary to update.
    """
    artifacts_data = workflow_data.get('artifacts', {})
    if isinstance(artifacts_data, list):
        artifacts = artifacts_data
    else:
        artifacts = artifacts_data.get('artifacts', [])
        
    required_artifacts = [art for art in artifacts if art.get('required', False)]
    
    if required_artifacts:
        rules['required_artifacts_check'] = {
            'name': 'Required Artifacts Check',
            'description': 'All required artifacts must be present',
            'context': 'end',
            'level': 'moderate',
            'error_message': 'Required artifacts are missing',
            'fix_suggestion': 'Ensure all required artifacts are created before session end'
        }
