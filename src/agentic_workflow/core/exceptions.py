"""
Core exceptions and error handling for Agentic Workflow Platform.

This module provides a comprehensive exception hierarchy and error handling
utilities for consistent error management across the application.
"""

from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

__all__ = [
    # Base Exception
    "AgenticWorkflowError",
    
    # Configuration Errors
    "ConfigError",
    "ConfigNotFoundError", 
    "ConfigValidationError",
    "ConfigMergeError",
    
    # Project Errors
    "ProjectError",
    "ProjectNotFoundError",
    "ProjectAlreadyExistsError",
    "ProjectValidationError",
    
    # Workflow Errors
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    
    # Agent Errors
    "AgentError",
    "AgentNotFoundError",
    "AgentValidationError",
    
    # CLI Errors
    "CLIError",
    "CLIValidationError",
    "CLIExecutionError",
    
    # Validation Errors
    "ValidationError",
    "SchemaValidationError",
    
    # File System Errors
    "FileSystemError",
    "FileNotFoundError",
    "FilePermissionError",
    "DirectoryError",
    
    # Ledger Errors
    "LedgerError",
    "LedgerValidationError",
    "LedgerCorruptionError",
    
    # Generation Errors
    "GenerationError",
    "TemplateError",
    "TemplateNotFoundError",
    
    # Service Errors
    "ServiceError",
    "ServiceUnavailableError",
    "ServiceTimeoutError",
    
    # Handler Errors
    "HandlerError",
    "SessionError",
    "ArtifactError",
    
    # Governance Errors
    "GovernanceError",
    "ValidationViolation",
    "PolicyConfigurationError",
    
    # Utility Functions
    "handle_error",
    "validate_required",
    "validate_path_exists",
    "validate_file_readable",
    "safe_operation",
]


class AgenticWorkflowError(Exception):
    """Base exception for all agentic workflow errors.
    
    This exception provides structured error handling with error codes,
    context information, and cause chaining for better debugging and logging.
    All custom exceptions in the agentic workflow system inherit from this base class.
    
    Args:
        message: Human-readable error message
        error_code: Machine-readable error code (defaults to class name)
        context: Additional context dictionary for debugging
        cause: Original exception that caused this error (for chaining)
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause

    def __str__(self) -> str:
        parts = [f"[{self.error_code}] {self.message}"]
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.cause:
            parts.append(f"Cause: {self.cause}")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
            "exception_type": self.__class__.__name__
        }


# Configuration Errors
class ConfigError(AgenticWorkflowError):
    """Configuration-related errors."""
    pass


class ConfigNotFoundError(ConfigError):
    """Configuration file not found."""
    pass


class ConfigValidationError(ConfigError):
    """Configuration validation failed."""
    pass


class ConfigMergeError(ConfigError):
    """Configuration merging failed."""
    pass


# Project Errors
class ProjectError(AgenticWorkflowError):
    """Project-related errors."""
    pass


class ProjectNotFoundError(ProjectError):
    """Project not found."""
    pass


class ProjectAlreadyExistsError(ProjectError):
    """Project already exists."""
    pass


class ProjectValidationError(ProjectError):
    """Project validation failed."""
    pass


# Workflow Errors
class WorkflowError(AgenticWorkflowError):
    """Workflow-related errors."""
    pass


class WorkflowNotFoundError(WorkflowError):
    """Workflow not found."""
    pass


class WorkflowValidationError(WorkflowError):
    """Workflow validation failed."""
    pass


class WorkflowExecutionError(WorkflowError):
    """Workflow execution failed."""
    pass


# Agent Errors
class AgentError(AgenticWorkflowError):
    """Agent-related errors."""
    pass


class AgentNotFoundError(AgentError):
    """Agent not found."""
    pass


class AgentValidationError(AgentError):
    """Agent validation failed."""
    pass


# CLI Errors
class CLIError(AgenticWorkflowError):
    """CLI-related errors."""
    pass


class CLIValidationError(CLIError):
    """CLI validation failed."""
    pass


class CLIExecutionError(CLIError):
    """CLI execution failed."""
    pass


# Validation Errors
class ValidationError(AgenticWorkflowError):
    """Validation-related errors."""
    pass


class SchemaValidationError(ValidationError):
    """Schema validation failed."""
    pass


# File System Errors
class FileSystemError(AgenticWorkflowError):
    """File system related errors."""
    pass


class FileNotFoundError(FileSystemError):
    """File not found."""
    pass


class FilePermissionError(FileSystemError):
    """File permission error."""
    pass


class DirectoryError(FileSystemError):
    """Directory operation error."""
    pass


# Ledger Errors
class LedgerError(AgenticWorkflowError):
    """Ledger-related errors."""
    pass


class LedgerValidationError(LedgerError):
    """Ledger validation failed."""
    pass


class LedgerCorruptionError(LedgerError):
    """Ledger corruption detected."""
    pass


# Generation Errors
class GenerationError(AgenticWorkflowError):
    """Generation-related errors."""
    pass


class TemplateError(GenerationError):
    """Template processing error."""
    pass


class TemplateNotFoundError(TemplateError):
    """Template not found."""
    pass


# Service Errors
class ServiceError(AgenticWorkflowError):
    """Service layer errors."""
    pass


class ServiceUnavailableError(ServiceError):
    """Service unavailable."""
    pass


class ServiceTimeoutError(ServiceError):
    """Service timeout."""
    pass


class HandlerError(AgenticWorkflowError):
    """CLI handler error."""
    pass


class SessionError(AgenticWorkflowError):
    """Session management error."""
    pass


class ArtifactError(AgenticWorkflowError):
    """Artifact processing error."""
    pass


class GovernanceError(AgenticWorkflowError):
    """Base exception for governance-related errors."""
    pass


class ValidationViolation(GovernanceError):
    """Raised when a specific governance validation rule is violated."""
    pass


class PolicyConfigurationError(GovernanceError):
    """Raised when governance policy definition is invalid or malformed."""
    pass


def handle_error(
    error: Exception,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    log_level: str = "error",
    reraise: bool = True
) -> None:
    """
    Centralized error handling function.

    Args:
        error: The exception that occurred
        operation: Description of the operation being performed
        context: Additional context information
        log_level: Logging level ("debug", "info", "warning", "error", "critical")
        reraise: Whether to re-raise the exception after logging
    """
    full_context = {
        "operation": operation,
        "error_type": type(error).__name__,
        **(context or {})
    }

    if isinstance(error, AgenticWorkflowError):
        # Already structured error
        log_data = error.to_dict()
        log_data.update(full_context)
    else:
        # Wrap generic exceptions
        log_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": full_context
        }

    # Log the error
    log_func = getattr(logger, log_level.lower(), logger.error)
    log_func(f"Error in {operation}: {error}", extra=log_data)

    if reraise:
        raise error


def validate_required(
    value: Any,
    name: str,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Validate that a required value is not None/empty.

    Args:
        value: Value to check
        name: Name of the value for error messages
        operation: Current operation context
        context: Additional context

    Raises:
        ValidationError: If value is None or empty
    """
    if value is None:
        raise ValidationError(
            f"Required value '{name}' is None",
            error_code="REQUIRED_VALUE_MISSING",
            context={"operation": operation, "value_name": name, **(context or {})}
        )

    if isinstance(value, str) and not value.strip():
        raise ValidationError(
            f"Required value '{name}' is empty",
            error_code="REQUIRED_VALUE_EMPTY",
            context={"operation": operation, "value_name": name, **(context or {})}
        )

    if isinstance(value, (list, dict)) and len(value) == 0:
        raise ValidationError(
            f"Required value '{name}' is empty",
            error_code="REQUIRED_VALUE_EMPTY",
            context={"operation": operation, "value_name": name, **(context or {})}
        )


def validate_path_exists(
    path: Path,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Validate that a path exists.

    Args:
        path: Path to check
        operation: Current operation context
        context: Additional context

    Raises:
        FileNotFoundError: If path doesn't exist
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Path does not exist: {path}",
            error_code="PATH_NOT_FOUND",
            context={"operation": operation, "path": str(path), **(context or {})}
        )


def validate_file_readable(
    path: Path,
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Validate that a file is readable.

    Args:
        path: File path to check
        operation: Current operation context
        context: Additional context

    Raises:
        FilePermissionError: If file is not readable
    """
    validate_path_exists(path, operation, context)

    if not path.is_file():
        raise FileSystemError(
            f"Path is not a file: {path}",
            error_code="NOT_A_FILE",
            context={"operation": operation, "path": str(path), **(context or {})}
        )

    try:
        with open(path, 'r', encoding='utf-8') as f:
            f.read(1)  # Try to read one character
    except (PermissionError, OSError) as e:
        raise FilePermissionError(
            f"File is not readable: {path}",
            error_code="FILE_NOT_READABLE",
            context={"operation": operation, "path": str(path), **(context or {})},
            cause=e
        )


def safe_operation(
    operation_func: Callable,
    operation_name: str,
    context: Optional[Dict[str, Any]] = None,
    fallback_value: Any = None,
    log_level: str = "error"
) -> Any:
    """
    Execute an operation safely with error handling.

    Args:
        operation_func: Function to execute
        operation_name: Name of the operation for logging
        context: Additional context
        fallback_value: Value to return on error
        log_level: Logging level for errors

    Returns:
        Result of operation_func or fallback_value on error
    """
    try:
        return operation_func()
    except Exception as e:
        handle_error(
            e,
            operation_name,
            context=context,
            log_level=log_level,
            reraise=False
        )
        return fallback_value
