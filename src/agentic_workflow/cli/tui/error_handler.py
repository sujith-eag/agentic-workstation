"""Centralized error handling for TUI operations.

This module provides decorators and utilities for consistent error handling
across the TUI, using the existing exception hierarchy and logging infrastructure.
"""

import logging
from functools import wraps
from typing import Callable, Optional, TypeVar, Any

from agentic_workflow.core.exceptions import (
    AgenticWorkflowError,
    ProjectError,
    WorkflowError,
    AgentError,
    CLIError,
    ValidationError,
    FileSystemError,
    LedgerError,
    ConfigError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


def handle_tui_errors(
    operation_name: str,
    show_error_modal: bool = True,
    fallback_value: Any = False,
):
    """Decorator to handle TUI operation errors consistently.
    
    This decorator catches expected business logic exceptions and displays them
    to the user, while logging and re-raising unexpected errors for debugging.
    
    Args:
        operation_name: Name of the operation for logging
        show_error_modal: Whether to display error modal to user (default True)
        fallback_value: Value to return on error (default False for actions)
    
    Expected Exceptions (caught and shown to user):
        - ProjectError, WorkflowError, AgentError: Business logic errors
        - CLIError, ValidationError: User input/validation errors
        - LedgerError: Ledger operations
        - FileSystemError, OSError, IOError: File operations
    
    Unexpected Exceptions (logged and re-raised):
        - TypeError, AttributeError, KeyError: Programming errors
        - Any other Exception: Unknown errors
    
    Usage:
        @handle_tui_errors("activate_agent", fallback_value=False)
        def execute(self, context):
            # ... operation code
            return True
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
                
            # Expected business logic errors - show to user
            except (ProjectError, WorkflowError, AgentError, CLIError, 
                    ValidationError, LedgerError, ConfigError) as e:
                # These are expected errors, log at info level
                logger.info(
                    f"{operation_name} failed with expected error: {e}",
                    extra=e.to_dict() if isinstance(e, AgenticWorkflowError) else {
                        "operation": operation_name,
                        "error_type": type(e).__name__
                    }
                )
                
                if show_error_modal and hasattr(self, 'error_view'):
                    self.error_view.display_error_modal(
                        str(e),
                        title=f"{operation_name.replace('_', ' ').title()} Failed"
                    )
                elif hasattr(self, 'feedback'):
                    self.feedback.error(str(e))
                    
                return fallback_value
                
            # File system errors - show to user
            except (OSError, IOError, FileSystemError) as e:
                logger.warning(
                    f"{operation_name} failed due to filesystem error: {e}",
                    exc_info=True,
                    extra={
                        "operation": operation_name,
                        "error_type": type(e).__name__
                    }
                )
                
                if show_error_modal and hasattr(self, 'error_view'):
                    self.error_view.display_error_modal(
                        f"File system error: {e}",
                        title="Operation Failed"
                    )
                elif hasattr(self, 'feedback'):
                    self.feedback.error(f"File system error: {e}")
                    
                return fallback_value
                
            # Unexpected errors - log full traceback and re-raise
            except Exception as e:
                logger.exception(
                    f"Unexpected error in {operation_name}: {e}",
                    extra={
                        "operation": operation_name,
                        "error_type": type(e).__name__,
                        "function": func.__name__,
                        "call_args": str(args)[:200],
                        "call_kwargs": str(kwargs)[:200]
                    }
                )
                
                # Show error modal if available, then re-raise for debugging
                if show_error_modal and hasattr(self, 'error_view'):
                    self.error_view.display_error_modal(
                        f"Unexpected error: {e}\n\nThis is a bug - please report it.",
                        title="Critical Error"
                    )
                
                # Re-raise to prevent silent failures
                raise
                
        return wrapper
    return decorator


def safe_fetch(
    fetch_func: Callable[[], T],
    operation_name: str,
    fallback_value: T,
    expected_exceptions: tuple = (ProjectError, WorkflowError, AgentError, KeyError, AttributeError)
) -> T:
    """Safely fetch data with expected exception handling.
    
    Use for data fetching operations where missing data is acceptable
    and should return a fallback value. Unexpected exceptions are logged
    and re-raised to prevent silent failures.
    
    Args:
        fetch_func: Function to execute that returns data
        operation_name: Operation name for logging
        fallback_value: Value to return if fetch fails with expected exception
        expected_exceptions: Tuple of exceptions to catch (others will propagate)
    
    Returns:
        Result of fetch_func or fallback_value on expected exceptions
        
    Raises:
        Any exception not in expected_exceptions
        
    Example:
        active_agent = safe_fetch(
            lambda: query_handlers.get_active_session(project)['agent_id'],
            operation_name="fetch_active_agent",
            fallback_value="No Active Agent",
            expected_exceptions=(KeyError, ProjectError, AgentError)
        )
    """
    try:
        return fetch_func()
    except expected_exceptions as e:
        logger.debug(
            f"{operation_name} returned fallback due to expected exception: {e}",
            extra={
                "operation": operation_name,
                "error_type": type(e).__name__,
                "fallback_value": str(fallback_value)[:100]
            }
        )
        return fallback_value
    except Exception as e:
        # Unexpected error - log with full traceback and re-raise
        logger.exception(
            f"Unexpected error in {operation_name}: {e}",
            extra={
                "operation": operation_name,
                "error_type": type(e).__name__,
                "expected_exceptions": str(expected_exceptions)
            }
        )
        raise


__all__ = [
    "handle_tui_errors",
    "safe_fetch",
]
