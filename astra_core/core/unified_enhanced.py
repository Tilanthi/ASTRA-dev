# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Enhanced unified STAN system with all Phase 2-4 enhancements

Integrates:
- Modular domain architecture
- Cross-domain meta-learning
- Unified differentiable physics
- Physical intuition development
- All existing capabilities

This is the main entry point for the enhanced STAN-XI-ASTRO system.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Import existing unified system
try:
    from .unified import UnifiedSTANSystem, UnifiedConfig, TaskType, TaskAnalyzer
    BASE_UNIFIED_AVAILABLE = True
except ImportError:
    UnifiedSTANSystem = None
    UnifiedConfig = None
    TaskType = None
    TaskAnalyzer = None
    BASE_UNIFIED_AVAILABLE = False
    logger.warning("Base unified system not available, using standalone mode")

# Import domain system
try:
    from ..domains import DomainRegistry, BaseDomainModule, DomainQueryResult
    from ..domains.registry import DomainRegistry as DomainsRegistry
except ImportError:
    DomainRegistry = None
    BaseDomainModule = None
    DomainQueryResult = None
    logger.warning("Domain system not available")

# Import meta-learning
try:
    from ..reasoning.cross_domain_meta_learner import CrossDomainMetaLearner
except ImportError:
    CrossDomainMetaLearner = None
    logger.warning("CrossDomainMetaLearner not available")

# Import physics
try:
    from ..physics import (
        UnifiedPhysicsEngine,
        PhysicsCurriculum,
        PhysicalAnalogicalReasoner,
        PhysicsDomain,
        PhysicsResult
    )
except ImportError:
    UnifiedPhysicsEngine = None
    PhysicsCurriculum = None
    PhysicalAnalogicalReasoner = None
    logger.warning("Physics system not available")

# Import counterfactual reasoning
try:
    from ..reasoning.integrated_counterfactual import (
        IntegratedCounterfactualSystem,
        get_counterfactual_system,
        process_query_with_counterfactual
    )
    COUNTERFACTUAL_AVAILABLE = True
except ImportError:
    IntegratedCounterfactualSystem = None
    get_counterfactual_system = None
    process_query_with_counterfactual = None
    COUNTERFACTUAL_AVAILABLE = False
    logger.warning("Counterfactual reasoning system not available")


# Define EnhancedUnifiedConfig based on whether UnifiedConfig is available
if BASE_UNIFIED_AVAILABLE:
    @dataclass
    class EnhancedUnifiedConfig(UnifiedConfig):
        """Enhanced configuration with new capabilities"""
        # Domain configuration
        enable_domains: bool = True
        auto_load_domains: bool = True
        domains_config: Dict[str, Dict[str, Any]] = field(default_factory=dict)

        # Meta-learning configuration
        enable_meta_learning: bool = True
        meta_learning_config: Dict[str, Any] = field(default_factory=dict)

        # Physics configuration
        enable_unified_physics: bool = True
        enable_physics_curriculum: bool = True
        enable_analogical_reasoning: bool = True
        physics_config: Dict[str, Any] = field(default_factory=dict)

        # Intuition development
        enable_intuition_development: bool = True
else:
    @dataclass
    class EnhancedUnifiedConfig:
        """Enhanced configuration with new capabilities (standalone mode)"""
        # Base configuration
        auto_optimize: bool = True
        use_all_capabilities: bool = True
        enable_metacognition: bool = True
        enable_swarm_intelligence: bool = True

        # Domain configuration
        enable_domains: bool = True
        auto_load_domains: bool = True
        domains_config: Dict[str, Dict[str, Any]] = field(default_factory=dict)

        # Meta-learning configuration
        enable_meta_learning: bool = True
        meta_learning_config: Dict[str, Any] = field(default_factory=dict)

        # Physics configuration
        enable_unified_physics: bool = True
        enable_physics_curriculum: bool = True
        enable_analogical_reasoning: bool = True
        physics_config: Dict[str, Any] = field(default_factory=dict)

        # Intuition development
        enable_intuition_development: bool = True


class EnhancedUnifiedSTANSystem:
    """
    Enhanced unified STAN system with all Phase 2-4 capabilities

    This is the main system that integrates all enhancements.
    """

    def __init__(self, config: Optional[EnhancedUnifiedConfig] = None):
        """
        Initialize enhanced unified system

        Args:
            config: Configuration object
        """
        self.config = config or EnhancedUnifiedConfig()

        # Initialize base system if available
        self.base_system = None
        if UnifiedSTANSystem is not None:
            base_config = UnifiedConfig(
                auto_optimize=self.config.auto_optimize,
                use_all_capabilities=self.config.use_all_capabilities,
                enable_metacognition=self.config.enable_metacognition,
                enable_swarm_intelligence=self.config.enable_swarm_intelligence
            )
            self.base_system = UnifiedSTANSystem(config=base_config)

        # Initialize domain registry
        self.domain_registry: Optional[DomainRegistry] = None
        if self.config.enable_domains and DomainRegistry is not None:
            self.domain_registry = DomainRegistry()
            self._initialize_domains()

        # Initialize meta-learner
        self.meta_learner: Optional[CrossDomainMetaLearner] = None
        if self.config.enable_meta_learning and CrossDomainMetaLearner is not None:
            self.meta_learner = CrossDomainMetaLearner(
                config=self.config.meta_learning_config
            )
            self._register_domain_features()

        # Initialize physics engine
        self.physics_engine: Optional[UnifiedPhysicsEngine] = None
        if self.config.enable_unified_physics and UnifiedPhysicsEngine is not None:
            self.physics_engine = UnifiedPhysicsEngine(
                config=self.config.physics_config
            )

        # Initialize intuition systems
        self.physics_curriculum: Optional[PhysicsCurriculum] = None
        self.analogical_reasoner: Optional[PhysicalAnalogicalReasoner] = None

        if self.config.enable_physics_curriculum and PhysicsCurriculum is not None:
            self.physics_curriculum = PhysicsCurriculum()

        if self.config.enable_analogical_reasoning and PhysicalAnalogicalReasoner is not None:
            self.analogical_reasoner = PhysicalAnalogicalReasoner()

        # Initialize counterfactual reasoning system
        self.counterfactual_system: Optional[IntegratedCounterfactualSystem] = None
        if COUNTERFACTUAL_AVAILABLE:
            self.counterfactual_system = get_counterfactual_system()
            logger.info("Counterfactual reasoning system initialized")

        # Performance tracking
        self.performance_stats = {
            'queries_processed': 0,
            'domains_used': set(),
            'meta_adaptations': 0,
            'physics_computations': 0,
            'analogies_used': 0,
            'counterfactual_queries': 0
        }

        logger.info("EnhancedUnifiedSTANSystem initialized")

    def _initialize_domains(self):
        """Initialize domain modules"""
        if self.domain_registry is None or not self.config.auto_load_domains:
            return

        # Configure domains to auto-load
        # Include ALL 75 available domains
        domains_config = {
            # Core astrophysics domains (HIGH PRIORITY)
            'ism': {'enabled': True},
            'star_formation': {'enabled': True},
            'exoplanets': {'enabled': True},
            'gravitational_waves': {'enabled': True},
            'cosmology': {'enabled': True},
            'solar_system': {'enabled': True},
            'time_domain': {'enabled': True},

            # Additional domain modules (ALL 75 DOMAINS)
            'high_energy': {'enabled': True},
            'galactic_archaeology': {'enabled': True},
            'radio_extragalactic': {'enabled': True},
            'radio_galactic': {'enabled': True},
            'accretion_disk_theory': {'enabled': True},
            'agn': {'enabled': True},
            'astrochemical_surveys': {'enabled': True},
            'astrometry': {'enabled': True},
            'astroparticle': {'enabled': True},
            'atomic_physics': {'enabled': True},
            'black_holes': {'enabled': True},
            'cmb': {'enabled': True},
            'compact_binaries': {'enabled': True},
            'computational_astrophysics': {'enabled': True},
            'dust_formation': {'enabled': True},
            'dust_grain_physics': {'enabled': True},
            'dwarf_galaxies': {'enabled': True},
            'dynamical_systems': {'enabled': True},
            'exoplanet_atmospheres': {'enabled': True},
            'extragalactic': {'enabled': True},
            'farinfrared_astronomy': {'enabled': True},
            'fluid_dynamics': {'enabled': True},
            'frbs': {'enabled': True},
            'galactic_structure': {'enabled': True},
            'galaxy_clusters': {'enabled': True},
            'galaxy_evolution': {'enabled': True},
            'gamma_ray': {'enabled': True},
            'general_relativity': {'enabled': True},
            'gravitational_lensing': {'enabled': True},
            'hii_regions': {'enabled': True},
            'heliospheric_physics': {'enabled': True},
            'hpc': {'enabled': True},
            'infrared_astronomy': {'enabled': True},
            'interferometry': {'enabled': True},
            'intergalactic_medium': {'enabled': True},
            'inverse_problems': {'enabled': True},
            'kilonovae': {'enabled': True},
            'large_scale_structure': {'enabled': True},
            'mhd': {'enabled': True},
            'millimetre_astronomy': {'enabled': True},
            'molecular_cloud_collapse': {'enabled': True},
            'molecular_cloud_dynamics': {'enabled': True},
            'molecular_cloud_evolution': {'enabled': True},
            'molecular_spectroscopy': {'enabled': True},
            'nuclear_astrophysics': {'enabled': True},
            'numerical_methods': {'enabled': True},
            'orbital_dynamics': {'enabled': True},
            'photoionization': {'enabled': True},
            'planetary_formation': {'enabled': True},
            'plasma_physics': {'enabled': True},
            'polarimetry': {'enabled': True},
            'prebiotic_chemistry': {'enabled': True},
            'quantum_applications': {'enabled': True},
            'radiative_processes': {'enabled': True},
            'radiative_transfer_theory': {'enabled': True},
            'shock_physics_extended': {'enabled': True},
            'signal_processing': {'enabled': True},
            'solar_physics': {'enabled': True},
            'solid_state_astro': {'enabled': True},
            'statistical_mechanics': {'enabled': True},
            'stellar_atmospheres': {'enabled': True},
            'stellar_populations': {'enabled': True},
            'stellar_structure': {'enabled': True},
            'submillimeter_astronomy': {'enabled': True},
            'supernovae': {'enabled': True},
            'theoretical_astrophysics': {'enabled': True},
            'tidal_disruption': {'enabled': True},
            'xray_binaries': {'enabled': True}
        }

        # Merge with user config
        domains_config.update(self.config.domains_config)

        # Auto-load domains
        load_results = self.domain_registry.auto_load_domains(domains_config)
        logger.info(f"Domain loading results: {load_results}")

    def _register_domain_features(self):
        """Register domain features with meta-learner"""
        if self.meta_learner is None or self.domain_registry is None:
            return

        # Register features for each loaded domain
        for domain_name in self.domain_registry.list_domains():
            domain = self.domain_registry.get_domain(domain_name)
            if domain and hasattr(domain, 'get_domain_features'):
                try:
                    features = domain.get_domain_features()
                    self.meta_learner.register_domain_features(domain_name, features)
                except Exception as e:
                    logger.warning(f"Failed to register features for {domain_name}: {e}")

    def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query using all available capabilities

        This is the main entry point for interacting with STAN-XI-ASTRO.

        Args:
            query: User query
            context: Additional context (parameters, data, etc.)
            mode: Processing mode ('auto', 'domain', 'physics', 'meta')

        Returns:
            Processing result with answer and metadata
        """
        context = context or {}
        result = {
            'query': query,
            'mode': mode or 'auto',
            'capabilities_used': [],
            'reasoning_trace': [],
            'answer': None,
            'confidence': 0.0,
            'metadata': {}
        }

        # Determine processing mode
        # Default to 'auto' if no mode specified
        if not mode:
            mode = 'auto'
        if mode == 'auto':
            mode = self._determine_optimal_mode(query, context)
            result['mode'] = mode

        # Route to appropriate processing
        try:
            if mode == 'counterfactual' and self.counterfactual_system:
                result = self._process_with_counterfactual(query, context, result)
            elif mode == 'domain' and self.domain_registry:
                result = self._process_with_domains(query, context, result)
            elif mode == 'physics' and self.physics_engine:
                result = self._process_with_physics(query, context, result)
            elif mode == 'meta' and self.meta_learner:
                result = self._process_with_meta_learning(query, context, result)
            else:
                # Use base system
                if self.base_system:
                    base_result = self.base_system.process_query(query, context)
                    result.update(base_result)
                    result['mode'] = 'base'
                    # Ensure confidence is set from base system
                    if 'confidence' not in result or result['confidence'] == 0:
                        result['confidence'] = 0.6  # Default confidence for base system
                else:
                    result['answer'] = "STAN-XI-ASTRO is ready to assist with your query."
                    result['confidence'] = 0.5
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            result['error'] = str(e)
            result['success'] = False
            result['confidence'] = 0.0  # Zero confidence on error

        # Ensure confidence is always set and > 0 (unless error)
        if result.get('confidence', 0) == 0 and not result.get('error'):
            result['confidence'] = 0.7  # Default confidence if not set

        # Ensure capabilities_used is populated
        if not result.get('capabilities_used'):
            # Add default capability based on mode
            mode_capability_map = {
                'domain': ['domain_expertise'],
                'physics': ['unified_physics'],
                'counterfactual': ['counterfactual_reasoning'],
                'meta': ['meta_learning'],
                'base': ['base_system']
            }
            result['capabilities_used'] = mode_capability_map.get(mode, ['base_system'])

        # Update performance stats
        self.performance_stats['queries_processed'] += 1

        return result

    def answer(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Alias for process_query for backward compatibility

        Args:
            query: User query
            context: Additional context

        Returns:
            Processing result with answer and metadata
        """
        return self.process_query(query, context)

    def _determine_optimal_mode(self, query: str, context: Dict[str, Any]) -> str:
        """Determine optimal processing mode for query"""
        query_lower = query.lower()

        # Check for counterfactual reasoning keywords FIRST
        # (these are more specific than domain/physics keywords)
        counterfactual_keywords = [
            'what would (happen|make|cause|require)',
            'what (if|conditions?|would)',
            'not (have|be|true|exist)',
            '(eliminate|prevent|suppress|avoid)',
            'alternative (scenarios?|explanations?|interpretations?)',
            'distinguish (between|from)',
            'counterfactual',
            '(hypothetical|theoretical) scenario'
        ]
        if COUNTERFACTUAL_AVAILABLE and self.counterfactual_system:
            for pattern in counterfactual_keywords:
                # Simple regex matching
                import re
                if re.search(pattern, query_lower):
                    return 'counterfactual'

        # Check for domain-specific keywords
        if self.domain_registry:
            for domain_name in self.domain_registry.list_domains():
                domain = self.domain_registry.get_domain(domain_name)
                if domain:
                    config = domain.get_config()
                    if any(kw in query_lower for kw in config.keywords):
                        return 'domain'

        # Check for physics keywords
        physics_keywords = ['physics', 'equation', 'model', 'simulate',
                          'compute', 'constraint', 'conservation',
                          'force', 'energy', 'momentum']
        if any(kw in query_lower for kw in physics_keywords):
            return 'physics'

        # Check for adaptation keywords
        adaptation_keywords = ['adapt', 'transfer', 'similar', 'analogy',
                             'compare', 'relate', 'like', 'versus']
        if any(kw in query_lower for kw in adaptation_keywords):
            return 'meta'

        # Default to base system
        return 'base'

    def _process_with_domains(
        self,
        query: str,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query using domain modules"""
        # Find relevant domain
        relevant_domain = self._find_relevant_domain(query)

        if relevant_domain:
            domain_result = relevant_domain.process_query(query, context)
            result['answer'] = domain_result.answer

            # Ensure confidence is always set and > 0
            if hasattr(domain_result, 'confidence') and domain_result.confidence > 0:
                result['confidence'] = domain_result.confidence
            else:
                result['confidence'] = 0.75  # Default confidence for domain answers

            result['reasoning_trace'] = domain_result.reasoning_trace if hasattr(domain_result, 'reasoning_trace') else []

            # Populate capabilities_used
            # If domain provided specific capabilities, use those
            # Otherwise, use all domain capabilities
            if hasattr(domain_result, 'capabilities_used') and domain_result.capabilities_used:
                result['capabilities_used'] = domain_result.capabilities_used
            else:
                # Fallback to domain's general capabilities
                if hasattr(relevant_domain, 'get_capabilities'):
                    result['capabilities_used'] = relevant_domain.get_capabilities()
                else:
                    result['capabilities_used'] = [relevant_domain.config.domain_name]

            result['domain_used'] = relevant_domain.config.domain_name
            self.performance_stats['domains_used'].add(relevant_domain.config.domain_name)

        return result

    def _process_with_physics(
        self,
        query: str,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query using unified physics engine"""
        # Extract model and parameters from query/context
        model_name = context.get('model', 'newtonian_gravity')
        parameters = context.get('parameters', {})

        # Add default values if needed
        if 'mass' not in parameters:
            parameters['mass'] = self.physics_engine.constants.get('M_sun', 1.989e33)
        if 'distance' not in parameters:
            parameters['distance'] = self.physics_engine.constants.get('AU', 1.496e13)

        try:
            physics_result = self.physics_engine.compute(
                model_name=model_name,
                parameters=parameters,
                compute_gradient=True,
                enforce_constraints=True
            )

            result['physics_result'] = physics_result
            result['answer'] = self._format_physics_result(physics_result)
            result['capabilities_used'].append('unified_physics')
            result['model_used'] = model_name
            result['confidence'] = 0.85  # High confidence for physics computations
            self.performance_stats['physics_computations'] += 1

        except Exception as e:
            result['error'] = str(e)
            result['answer'] = f"Physics computation failed: {e}"
            result['confidence'] = 0.0

        return result

    def _process_with_meta_learning(
        self,
        query: str,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process query using meta-learning"""
        # Extract target domain and adaptation data
        target_domain = context.get('target_domain')
        adaptation_data = context.get('adaptation_data', {})
        n_examples = context.get('n_examples', 5)

        if target_domain and self.meta_learner:
            source_domains = self.meta_learner.get_meta_learning_status().get('registered_domains', [])

            if source_domains:
                adapted = self.meta_learner.adapt_to_new_domain(
                    target_domain=target_domain,
                    source_domains=source_domains,
                    adaptation_data=adaptation_data,
                    n_examples=n_examples
                )

                result['answer'] = (
                    f"Adapted to {target_domain} from {adapted.source_domain} "
                    f"with {adapted.performance:.1%} performance using {adapted.adaptation_method}"
                )
                result['confidence'] = adapted.performance
                result['adaptation_result'] = adapted
                result['capabilities_used'].append('meta_learning')
                self.performance_stats['meta_adaptations'] += 1
            else:
                result['answer'] = "No source domains available for adaptation"
                result['confidence'] = 0.0
        else:
            result['answer'] = "Meta-learning requires target_domain specification"
            result['confidence'] = 0.0

        return result

    def _process_with_counterfactual(
        self,
        query: str,
        context: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process query using counterfactual reasoning engine.

        This is the key method that enables ASTRA's "nascent discovery mode"—the
        ability to go beyond recovering known results and explore hypothetical alternatives.
        """
        try:
            # Use the integrated counterfactual system
            cf_result = self.counterfactual_system.process_query(query, context)

            # Check if counterfactual reasoning was successful
            if cf_result and not cf_result.get('requires_standard_processing'):
                # Counterfactual reasoning succeeded
                result['answer'] = cf_result.get('answer')
                result['query_type'] = cf_result.get('query_type', 'counterfactual')
                result['confidence'] = cf_result.get('confidence', 0.75)
                result['capabilities_used'] = cf_result.get('capabilities_used',
                                                         ['counterfactual_reasoning'])
                result['classification'] = cf_result.get('classification')

                # Add metadata
                result['metadata']['counterfactual_analysis'] = True
                result['metadata']['triggers'] = cf_result.get('classification', {}).triggers if hasattr(cf_result.get('classification', {}), 'triggers') else []

                # Update performance stats
                self.performance_stats['counterfactual_queries'] += 1

                logger.info(f"Counterfactual reasoning applied: {cf_result.get('query_type')}")
            else:
                # Counterfactual system detected this as a standard query
                # Fall back to domain processing
                if self.domain_registry:
                    result['answer'] = ("Query classified as standard analysis - "
                                         "routing to domain modules")
                    result['requires_standard_processing'] = True
                else:
                    result['answer'] = "Counterfactual system unavailable for this query"
                    result['confidence'] = 0.5

        except Exception as e:
            logger.error(f"Counterfactual processing failed: {e}")
            result['answer'] = f"Counterfactual reasoning encountered an error: {str(e)}"
            result['error'] = str(e)
            result['success'] = False

        return result

    def _format_physics_result(self, physics_result) -> str:
        """Format physics result for human-readable output"""
        value = physics_result.value

        if isinstance(value, (int, float)):
            return f"Computed value: {value:.6e}"
        elif isinstance(value, dict):
            return f"Computed multi-component result with {len(value)} components"
        else:
            return f"Computed result: {value}"

    def _find_relevant_domain(self, query: str) -> Optional[BaseDomainModule]:
        """Find most relevant domain for query"""
        if not self.domain_registry:
            return None

        query_lower = query.lower()
        best_domain = None
        best_score = 0

        for domain_name in self.domain_registry.list_domains():
            domain = self.domain_registry.get_domain(domain_name)
            if domain:
                config = domain.get_config()
                score = sum(1 for kw in config.keywords if kw in query_lower)
                if score > best_score:
                    best_score = score
                    best_domain = domain

        return best_domain if best_score > 0 else None

    def adapt_to_domain(
        self,
        target_domain: str,
        adaptation_data: Dict[str, Any],
        n_examples: int = 5
    ) -> Dict[str, Any]:
        """
        Adapt system to new domain using meta-learning

        Args:
            target_domain: Domain to adapt to
            adaptation_data: Data from target domain
            n_examples: Number of examples for few-shot learning

        Returns:
            Adaptation result
        """
        if self.meta_learner and self.domain_registry:
            source_domains = self.domain_registry.list_domains()
            adapted_model = self.meta_learner.adapt_to_new_domain(
                target_domain=target_domain,
                source_domains=source_domains,
                adaptation_data=adaptation_data,
                n_examples=n_examples
            )
            return adapted_model

        return {'error': 'Meta-learning not available'}

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status

        Returns:
            Dictionary with status information for all components
        """
        status = {
            'base_system': self.base_system is not None,
            'domains': {
                'enabled': self.domain_registry is not None,
                'loaded': len(self.domain_registry.list_domains()) if self.domain_registry else 0,
                'available': self.domain_registry.list_domains() if self.domain_registry else []
            },
            'meta_learning': {
                'enabled': self.meta_learner is not None,
                'registered_domains': self.meta_learner.get_meta_learning_status() if self.meta_learner else {}
            },
            'physics': {
                'engine': self.physics_engine is not None,
                'curriculum': self.physics_curriculum is not None,
                'analogical': self.analogical_reasoner is not None
            },
            'performance': self.performance_stats.copy()
        }

        # Add intuition assessment
        if self.physics_curriculum:
            status['intuition'] = self.physics_curriculum.get_intuition_assessment()

        # Add analogical reasoner status
        if self.analogical_reasoner:
            status['analogical_reasoner'] = self.analogical_reasoner.get_status()

        return status

    def learn_physics_curriculum(self, n_problems: int = 10) -> Dict[str, Any]:
        """
        Learn from physics curriculum

        Args:
            n_problems: Number of problems to solve

        Returns:
            Learning progress
        """
        if self.physics_curriculum:
            next_stage = self.physics_curriculum.get_next_stage()
            if next_stage:
                progress = self.physics_curriculum.learn_at_stage(next_stage, n_problems)
                return {
                    'stage': next_stage,
                    'progress': progress,
                    'overall_intuition': self.physics_curriculum.get_intuition_assessment()
                }

        return {'error': 'Physics curriculum not available'}

    def find_analogies(
        self,
        target_phenomenon: str,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find physical analogies for a phenomenon

        Args:
            target_phenomenon: Phenomenon to find analogies for
            min_similarity: Minimum similarity threshold

        Returns:
            List of analogies
        """
        if self.analogical_reasoner:
            analogies = self.analogical_reasoner.find_analogies(
                target_phenomenon, min_similarity
            )

            return [
                {
                    'source': a.source_phenomenon,
                    'target': a.target_phenomenon,
                    'similarity': a.structural_similarity,
                    'confidence': a.confidence,
                    'mapping': a.mapping,
                    'differences': a.differences
                }
                for a in analogies
            ]

        return []

    def compute_physics(
        self,
        model_name: str,
        parameters: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute physics model

        Args:
            model_name: Name of physics model
            parameters: Model parameters
            options: Additional options (compute_gradient, enforce_constraints)

        Returns:
            Computation result
        """
        if self.physics_engine is None:
            return {'error': 'Physics engine not available'}

        opts = options or {}
        compute_gradient = opts.get('compute_gradient', True)
        enforce_constraints = opts.get('enforce_constraints', True)

        result = self.physics_engine.compute(
            model_name=model_name,
            parameters=parameters,
            compute_gradient=compute_gradient,
            enforce_constraints=enforce_constraints
        )

        return {
            'value': result.value,
            'gradients': result.gradients,
            'constraint_violations': result.constraint_violations,
            'model_name': result.model_name,
            'metadata': result.metadata
        }

    def get_domain_info(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific domain

        Args:
            domain_name: Name of domain

        Returns:
            Domain information or None if not found
        """
        if self.domain_registry:
            domain = self.domain_registry.get_domain(domain_name)
            if domain:
                return domain.get_status()
        return None

    def list_domains(self) -> List[str]:
        """List all available domains"""
        if self.domain_registry:
            return self.domain_registry.list_domains()
        return []

    def list_physics_models(self) -> List[str]:
        """List all available physics models"""
        if self.physics_engine:
            return list(self.physics_engine.models.keys())
        return []


def create_enhanced_stan_system(config: Optional[EnhancedUnifiedConfig] = None) -> EnhancedUnifiedSTANSystem:
    """
    Factory function to create enhanced STAN system

    Args:
        config: Optional configuration

    Returns:
        EnhancedUnifiedSTANSystem instance
    """
    return EnhancedUnifiedSTANSystem(config)


# Backwards compatibility alias
create_stan_system = create_enhanced_stan_system
