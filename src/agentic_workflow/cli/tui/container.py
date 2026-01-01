"""
Dependency Injection Container for TUI Application.

This module provides a lightweight DI container with:
- Singleton and transient service lifetimes
- Lazy initialization
- Clear dependency resolution
- Type-safe service registration

Part of Phase 1: God Object Refactoring
"""

from typing import Callable, Dict, Any, Optional, Literal, TypeVar
from pathlib import Path
from rich.console import Console

from agentic_workflow.cli.theme import Theme
from .ui import LayoutManager, InputHandler, FeedbackPresenter, ProgressPresenter
from .views.error_view import ErrorView
from ..handlers import (
    ProjectHandlers,
    WorkflowHandlers,
    SessionHandlers,
    EntryHandlers,
    QueryHandlers,
    ArtifactHandlers,
)

T = TypeVar('T')
ServiceLifetime = Literal['singleton', 'transient']


class DependencyContainer:
    """
    Dependency injection container with lazy loading and lifetime management.
    
    Supports:
    - Singleton services (created once, cached)
    - Transient services (new instance each time)
    - Lazy initialization (only create when needed)
    - Clear error messages for missing services
    
    Usage:
        container = DependencyContainer(config)
        console = container.resolve('console')  # Gets singleton instance
        controller = container.resolve('global_menu')  # Gets new instance
    """
    
    def __init__(self, config: Optional[Any] = None, console: Optional[Any] = None):
        """
        Initialize the dependency container.
        
        Args:
            config: Runtime configuration object
            console: Optional pre-created console instance (for testing)
        """
        self.config = config
        self._injected_console = console  # Store injected console for testing
        self._singletons: Dict[str, Any] = {}  # Cache for singleton instances
        self._factories: Dict[str, tuple[ServiceLifetime, Callable[[], Any]]] = {}
        
        # Register all services
        self._register_services()
    
    def _register_services(self):
        """Register all services with their factories and lifetimes."""
        # ================================================================
        # UI Components (All Singletons - shared across app)
        # ================================================================
        
        # Use injected console or create new one
        self.register_singleton('console', lambda: self._injected_console if self._injected_console else Console())
        
        self.register_singleton('theme', lambda: Theme)
        
        self.register_singleton('layout', lambda: LayoutManager(
            console=self.resolve('console'),
            theme_map=self.resolve('theme').get_color_map()
        ))
        
        self.register_singleton('input_handler', lambda: InputHandler(
            console=self.resolve('console')
        ))
        
        self.register_singleton('feedback', lambda: FeedbackPresenter(
            console=self.resolve('console'),
            layout=self.resolve('layout'),
            theme_map=self.resolve('theme').feedback_theme()
        ))
        
        self.register_singleton('progress', lambda: ProgressPresenter(
            console=self.resolve('console'),
            layout=self.resolve('layout'),
            theme_map=self.resolve('theme').progress_theme()
        ))
        
        self.register_singleton('error_view', lambda: ErrorView(
            console=self.resolve('console'),
            input_handler=self.resolve('input_handler'),
            theme_map=self.resolve('theme').get_color_map()
        ))
        
        # ================================================================
        # Handlers (All Singletons - maintain state across operations)
        # ================================================================
        
        self.register_singleton('project_handlers', lambda: ProjectHandlers(
            console=self.resolve('console')
        ))
        
        self.register_singleton('workflow_handlers', lambda: WorkflowHandlers(
            console=self.resolve('console'),
            config=self.config
        ))
        
        self.register_singleton('session_handlers', lambda: SessionHandlers(
            console=self.resolve('console'),
            config=self.config
        ))
        
        self.register_singleton('entry_handlers', lambda: EntryHandlers(
            console=self.resolve('console')
        ))
        
        self.register_singleton('query_handlers', lambda: QueryHandlers(
            console=self.resolve('console')
        ))
        
        self.register_singleton('artifact_handlers', lambda: ArtifactHandlers())
        
        # ================================================================
        # Controllers (Transient - new instance per request)
        # ================================================================
        # Note: Controllers will be registered in Phase 4 after they're
        # updated to accept explicit dependencies
    
    def register_singleton(self, name: str, factory: Callable[[], T]) -> None:
        """
        Register a service as singleton (created once, cached).
        
        Args:
            name: Service identifier
            factory: Function that creates the service instance
        """
        self._factories[name] = ('singleton', factory)
    
    def register_transient(self, name: str, factory: Callable[[], T]) -> None:
        """
        Register a service as transient (new instance each time).
        
        Args:
            name: Service identifier
            factory: Function that creates the service instance
        """
        self._factories[name] = ('transient', factory)
    
    def resolve(self, service_name: str) -> Any:
        """
        Resolve a service by name.
        
        Args:
            service_name: The name of the service to resolve
            
        Returns:
            The service instance (cached singleton or new transient)
            
        Raises:
            KeyError: If service is not registered
        """
        if service_name not in self._factories:
            available = ', '.join(sorted(self._factories.keys()))
            raise KeyError(
                f"Service '{service_name}' not registered in container. "
                f"Available services: {available}"
            )
        
        lifetime, factory = self._factories[service_name]
        
        if lifetime == 'singleton':
            # Return cached instance or create and cache
            if service_name not in self._singletons:
                self._singletons[service_name] = factory()
            return self._singletons[service_name]
        else:  # transient
            # Always create new instance
            return factory()
    
    def is_registered(self, service_name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_name: The name of the service
            
        Returns:
            True if service is registered, False otherwise
        """
        return service_name in self._factories
    
    def get_registered_services(self) -> list[str]:
        """
        Get list of all registered service names.
        
        Returns:
            List of service names sorted alphabetically
        """
        return sorted(self._factories.keys())
    
    def clear_singletons(self) -> None:
        """
        Clear all cached singleton instances.
        
        Useful for testing or when you need fresh instances.
        """
        self._singletons.clear()
    
    def get_service_lifetime(self, service_name: str) -> Optional[ServiceLifetime]:
        """
        Get the lifetime of a registered service.
        
        Args:
            service_name: The name of the service
            
        Returns:
            'singleton' or 'transient', or None if not registered
        """
        if service_name not in self._factories:
            return None
        return self._factories[service_name][0]


__all__ = ['DependencyContainer', 'ServiceLifetime']
