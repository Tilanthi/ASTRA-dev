"""
Domain registry for managing domain modules

Provides hot-swappable domain modules with automatic loading,
dependency resolution, and lifecycle management.
"""

import importlib
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from . import (
    BaseDomainModule,
    DomainConfig,
    DomainQueryResult,
    CrossDomainConnection
)

logger = logging.getLogger(__name__)


class DomainLoadError(Exception):
    """Exception raised when domain module fails to load"""
    pass


class DomainDependencyError(Exception):
    """Exception raised when domain dependencies cannot be resolved"""
    pass


class DomainRegistry:
    """
    Registry for managing domain modules

    Features:
    - Hot-swappable domain modules
    - Automatic dependency resolution
    - Domain lifecycle management
    - Cross-domain connection discovery
    """

    def __init__(self):
        """Initialize domain registry"""
        self._domains: Dict[str, BaseDomainModule] = {}
        self._domain_configs: Dict[str, DomainConfig] = {}
        self._load_order: List[str] = []
        self._global_config: Dict[str, Any] = {}

    def register_domain(self, domain: BaseDomainModule) -> None:
        """
        Register a domain module

        Args:
            domain: Domain module instance to register

        Raises:
            ValueError: If domain configuration is invalid
        """
        config = domain.get_config()

        # Validate configuration
        if not config.domain_name:
            raise ValueError("Domain name cannot be empty")

        # Check for name conflicts
        if config.domain_name in self._domains:
            logger.warning(f"Domain {config.domain_name} already registered, replacing")

        self._domains[config.domain_name] = domain
        self._domain_configs[config.domain_name] = config

        logger.info(f"Registered domain: {config.domain_name} v{config.version}")

    def unregister_domain(self, domain_name: str) -> None:
        """
        Unregister a domain module

        Args:
            domain_name: Name of domain to unregister
        """
        if domain_name in self._domains:
            del self._domains[domain_name]
            del self._domain_configs[domain_name]

            if domain_name in self._load_order:
                self._load_order.remove(domain_name)

            logger.info(f"Unregistered domain: {domain_name}")
        else:
            logger.warning(f"Domain {domain_name} not registered")

    def get_domain(self, domain_name: str) -> Optional[BaseDomainModule]:
        """
        Get domain module by name

        Args:
            domain_name: Name of domain to retrieve

        Returns:
            Domain module or None if not found
        """
        return self._domains.get(domain_name)

    def list_domains(self) -> List[str]:
        """
        List all registered domain names

        Returns:
            List of domain names in load order
        """
        return self._load_order.copy()

    def get_all_domains(self) -> Dict[str, BaseDomainModule]:
        """
        Get all registered domain modules

        Returns:
            Dictionary mapping domain names to modules
        """
        return self._domains.copy()

    def set_global_config(self, config: Dict[str, Any]) -> None:
        """
        Set global configuration for domain initialization

        Args:
            config: Global configuration dictionary
        """
        self._global_config = config

        # Reinitialize all domains with new config
        for domain_name, domain in self._domains.items():
            try:
                domain.initialize(self._global_config)
            except Exception as e:
                logger.error(f"Failed to reinitialize {domain_name}: {e}")

    def auto_load_domains(
        self,
        domains_config: Dict[str, Dict[str, Any]],
        base_path: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Automatically load domains from configuration

        Args:
            domains_config: Dictionary mapping domain names to their configs
            base_path: Base path for domain modules (defaults to stan_core.domains)

        Returns:
            Dictionary mapping domain names to load success status
        """
        if base_path is None:
            base_path = "stan_core.domains"

        load_results = {}

        # Resolve dependencies and determine load order
        load_order = self._resolve_load_order(domains_config)

        # Load domains in dependency order
        for domain_name in load_order:
            config = domains_config.get(domain_name, {})

            if not config.get('enabled', True):
                logger.info(f"Domain {domain_name} disabled, skipping")
                load_results[domain_name] = False
                continue

            try:
                success = self._load_domain_module(domain_name, base_path, config)
                load_results[domain_name] = success
            except Exception as e:
                logger.error(f"Failed to load domain {domain_name}: {e}")
                load_results[domain_name] = False

        return load_results

    def _resolve_load_order(
        self,
        domains_config: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Resolve domain load order based on dependencies

        Uses topological sort to determine load order.

        Args:
            domains_config: Domain configurations

        Returns:
            List of domain names in dependency order

        Raises:
            DomainDependencyError: If circular dependencies detected
        """
        # Build dependency graph
        graph = {name: set(config.get('dependencies', []))
                for name, config in domains_config.items()}

        # Topological sort (Kahn's algorithm)
        in_degree = {name: len(deps) for name, deps in graph.items()}
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for neighbors
            for name, deps in graph.items():
                if node in deps:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        # Check for circular dependencies
        if len(result) != len(graph):
            raise DomainDependencyError(
                f"Circular dependencies detected in domains: "
                f"{set(graph.keys()) - set(result)}"
            )

        return result

    def _load_domain_module(
        self,
        domain_name: str,
        base_path: str,
        config: Dict[str, Any]
    ) -> bool:
        """
        Load a single domain module

        Args:
            domain_name: Name of domain to load
            base_path: Base path for domain modules
            config: Domain configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import module
            module_path = f"{base_path}.{domain_name}"
            module = importlib.import_module(module_path)

            # Get domain class (convention: DomainNameDomain)
            # Try multiple naming conventions to handle plural/singular variations
            possible_class_names = []

            # 1. Standard: words capitalized + 'Domain' (e.g., 'black_holes' -> 'BlackHolesDomain')
            class_name = ''.join(word.capitalize() for word in domain_name.split('_')) + 'Domain'
            possible_class_names.append(class_name)

            # 2. Simple capitalization + 'Domain' (e.g., 'cmb' -> 'CmbDomain')
            possible_class_names.append(domain_name.capitalize() + 'Domain')

            # 3. Common plural-to-singular mappings
            # Remove trailing 's' from last word if plural
            words = domain_name.split('_')
            if words[-1].endswith('s') and len(words[-1]) > 1:
                # Try singular form (e.g., 'exoplanets' -> 'exoplanet')
                singular_words = words[:-1] + [words[-1][:-1]]
                singular_name = ''.join(word.capitalize() for word in singular_words) + 'Domain'
                possible_class_names.append(singular_name)

            # 4. Check for domain classes already imported in the module's namespace
            # Scan module for any class ending in 'Domain'
            for attr_name in dir(module):
                if attr_name.endswith('Domain') and attr_name != 'BaseDomainModule':
                    possible_class_names.append(attr_name)

            # Try each possible class name
            domain_class = None
            for class_name in possible_class_names:
                if hasattr(module, class_name):
                    domain_class = getattr(module, class_name)
                    break

            if domain_class is None:
                raise AttributeError(f"No domain class found in {module_path}. Tried: {possible_class_names[:3]}")

            domain_class = getattr(module, class_name)

            # Create domain instance
            domain_instance = domain_class(**config.get('params', {}))

            # Initialize domain
            domain_instance.initialize(self._global_config)

            # Register domain
            self.register_domain(domain_instance)
            self._load_order.append(domain_name)

            logger.info(f"Successfully loaded domain: {domain_name}")
            return True

        except ImportError as e:
            raise DomainLoadError(f"Failed to import {domain_name}: {e}")
        except AttributeError as e:
            raise DomainLoadError(f"Domain class not found in {domain_name}: {e}")
        except Exception as e:
            raise DomainLoadError(f"Failed to load {domain_name}: {e}")

    def find_best_domain_for_query(
        self,
        query: str,
        min_confidence: float = 0.1
    ) -> Optional[BaseDomainModule]:
        """
        Find the best domain to handle a query

        Args:
            query: User query
            min_confidence: Minimum confidence threshold

        Returns:
            Best matching domain or None if no domain meets threshold
        """
        best_domain = None
        best_score = min_confidence

        for domain_name, domain in self._domains.items():
            if not domain.config.enabled:
                continue

            score = domain.can_handle_query(query)
            if score > best_score:
                best_score = score
                best_domain = domain

        return best_domain

    def discover_all_connections(self) -> Dict[str, List[CrossDomainConnection]]:
        """
        Discover cross-domain connections between all registered domains

        Returns:
            Dictionary mapping domain names to their connections
        """
        connections = {}

        for domain_name, domain in self._domains.items():
            other_domains = [d for name, d in self._domains.items()
                           if name != domain_name]

            domain_connections = domain.discover_cross_domain_connections(other_domains)
            connections[domain_name] = domain_connections

        return connections

    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get comprehensive registry status

        Returns:
            Dictionary with registry status information
        """
        # Get status of all domains
        domain_statuses = {}
        for name, domain in self._domains.items():
            domain_statuses[name] = domain.get_status()

        # Discover connections
        connections = self.discover_all_connections()

        return {
            'total_domains': len(self._domains),
            'enabled_domains': sum(1 for d in self._domains.values() if d.config.enabled),
            'load_order': self._load_order,
            'domain_statuses': domain_statuses,
            'cross_domain_connections': {
                name: len(conns) for name, conns in connections.items()
            },
            'total_connections': sum(len(conns) for conns in connections.values())
        }

    def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query using appropriate domain

        Args:
            query: User query
            context: Additional context

        Returns:
            Processing result
        """
        context = context or {}

        # Find best domain
        domain = self.find_best_domain_for_query(query)

        if domain is None:
            return {
                'success': False,
                'error': 'No suitable domain found for query',
                'query': query
            }

        # Process with domain
        try:
            result = domain.process_query(query, context)

            return {
                'success': True,
                'domain': domain.config.domain_name,
                'answer': result.answer,
                'confidence': result.confidence,
                'reasoning_trace': result.reasoning_trace,
                'capabilities_used': result.capabilities_used,
                'metadata': result.metadata
            }

        except Exception as e:
            logger.error(f"Domain {domain.config.domain_name} failed to process query: {e}")
            return {
                'success': False,
                'error': str(e),
                'domain': domain.config.domain_name,
                'query': query
            }

    def enable_domain(self, domain_name: str) -> bool:
        """
        Enable a domain

        Args:
            domain_name: Name of domain to enable

        Returns:
            True if successful, False otherwise
        """
        domain = self.get_domain(domain_name)
        if domain:
            domain.config.enabled = True
            logger.info(f"Enabled domain: {domain_name}")
            return True
        return False

    def disable_domain(self, domain_name: str) -> bool:
        """
        Disable a domain

        Args:
            domain_name: Name of domain to disable

        Returns:
            True if successful, False otherwise
        """
        domain = self.get_domain(domain_name)
        if domain:
            domain.config.enabled = False
            logger.info(f"Disabled domain: {domain_name}")
            return True
        return False

    def reload_domain(self, domain_name: str) -> bool:
        """
        Reload a domain module

        Args:
            domain_name: Name of domain to reload

        Returns:
            True if successful, False otherwise
        """
        domain = self.get_domain(domain_name)
        if not domain:
            logger.warning(f"Cannot reload unknown domain: {domain_name}")
            return False

        try:
            # Reinitialize domain
            domain.initialize(self._global_config)
            logger.info(f"Reloaded domain: {domain_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload domain {domain_name}: {e}")
            return False
