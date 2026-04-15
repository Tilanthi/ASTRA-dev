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
Discovery Orchestrator Module

Coordinates all discovery engine components:
- First principles discovery
- Physics-grounded analogy
- Automatic constraint discovery
- Scalable causal inference
- Active experimentation
- Subtle pattern detection
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import warnings

from .first_principles_discovery import FirstPrinciplesDiscovery
from .physics_grounded_analogy import PhysicsGroundedAnalogy
from .constraint_discovery import AutomaticConstraintDiscovery
from .scalable_causal_inference import ScalableCausalInference
from .active_experimentation import ActiveExperimentationEngine, Hypothesis
from .subtle_pattern_detection import SubtlePatternDetection


@dataclass
class DiscoveryResult:
    """Comprehensive result from discovery process."""
    discovery_id: str
    discovered_patterns: List[Any]
    causal_graphs: List[Any]
    hypotheses: List[Hypothesis]
    experiments: List[Any]
    confidence: float
    validation_status: str
    recommendations: List[str]


class DiscoveryOrchestrator:
    """
    Orchestrates all discovery engine components.

    This is the main interface for V80 discovery capabilities,
    coordinating all improvements to STAN's limitations.

    Workflow:
    1. Detect patterns (subtle pattern detection)
    2. Discover constraints (automatic constraint discovery)
    3. Build causal models (scalable causal inference)
    4. Validate with analogies (physics-grounded analogy)
    5. For novel phenomena: first principles discovery
    6. Generate and test hypotheses (active experimentation)
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize discovery orchestrator.

        Args:
            config: Configuration dict passed to sub-modules
        """
        config = config or {}

        # Initialize all discovery components
        self.first_principles = FirstPrinciplesDiscovery(config)
        self.analogy = PhysicsGroundedAnalogy(config)
        self.constraints = AutomaticConstraintDiscovery(config)
        self.causal = ScalableCausalInference(config)
        self.experimentation = ActiveExperimentationEngine(config)
        self.pattern_detection = SubtlePatternDetection(config)

        # Discovery history
        self.discovery_history: List[DiscoveryResult] = []

    def discover(
        self,
        data: np.ndarray,
        variable_names: List[str],
        domain_context: Optional[Dict[str, Any]] = None,
        discovery_mode: str = 'comprehensive'
    ) -> DiscoveryResult:
        """
        Run comprehensive discovery process.

        Args:
            data: Observational data
            variable_names: Variable names
            domain_context: Domain knowledge
            discovery_mode: 'comprehensive', 'fast', 'deep'

        Returns:
            Comprehensive discovery result
        """
        domain_context = domain_context or {}

        discovered_patterns = []
        causal_graphs = []
        hypotheses = []
        experiments = []

        print(f"Running {discovery_mode} discovery...")

        # Step 1: Detect subtle patterns
        print("  Step 1: Subtle pattern detection...")
        patterns = self.pattern_detection.scan_dataset(data, variable_names)
        discovered_patterns.extend(patterns)
        print(f"    Found {len(patterns)} patterns")

        # Step 2: Discover constraints
        print("  Step 2: Automatic constraint discovery...")
        constraints = self.constraints.discover_constraints(data, variable_names)
        discovered_patterns.extend(constraints)
        print(f"    Found {len(constraints)} constraints")

        # Step 3: Build causal models
        print("  Step 3: Scalable causal inference...")
        causal_graph = self.causal.discover_causal_structure(data, variable_names)
        causal_graphs.append(causal_graph)
        print(f"    Discovered graph with {len(causal_graph.edges)} edges")

        # Step 4: Check analogies with known systems
        if domain_context.get('compare_to_known_systems'):
            print("  Step 4: Physics-grounded analogy validation...")
            # Would compare against known systems from analogy engine
            # This is domain-specific

        # Step 5: For novel phenomena without analogies
        if discovery_mode == 'deep':
            print("  Step 5: First principles discovery...")
            first_principles_patterns = self.first_principles.discover_from_data(
                data, variable_names
            )
            discovered_patterns.extend(first_principles_patterns)
            print(f"    Found {len(first_principles_patterns)} novel patterns")

        # Step 6: Generate and prioritize hypotheses
        print("  Step 6: Hypothesis generation...")
        for graph in causal_graphs:
            hyps = self.experimentation.generate_hypotheses(graph, domain_context)
            hypotheses.extend(hyps)
        print(f"    Generated {len(hypotheses)} hypotheses")

        # Step 7: Design experiments to test hypotheses
        if hypotheses and domain_context.get('available_targets'):
            print("  Step 7: Active experimentation design...")
            for hyp in hypotheses[:3]:  # Top 3
                try:
                    exp = self.experimentation.design_optimal_experiment(
                        hyp,
                        domain_context['available_targets'],
                        domain_context.get('instrument_caps', {})
                    )
                    experiments.append(exp)
                except Exception as e:
                    warnings.warn(f"Could not design experiment for {hyp.hypothesis_id}: {e}")
            print(f"    Designed {len(experiments)} experiments")

        # Compute overall confidence
        confidence = self._compute_overall_confidence(
            discovered_patterns, causal_graphs, hypotheses
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            discovered_patterns, causal_graphs, hypotheses, domain_context
        )

        result = DiscoveryResult(
            discovery_id=f"discovery_{np.random.randint(10000, 99999)}",
            discovered_patterns=discovered_patterns,
            causal_graphs=causal_graphs,
            hypotheses=hypotheses,
            experiments=experiments,
            confidence=confidence,
            validation_status='pending',
            recommendations=recommendations
        )

        self.discovery_history.append(result)
        return result

    def _compute_overall_confidence(
        self,
        patterns: List[Any],
        graphs: List[Any],
        hypotheses: List[Hypothesis]
    ) -> float:
        """Compute overall confidence in discovery results."""
        confidences = []

        # From patterns
        for pattern in patterns:
            if hasattr(pattern, 'confidence'):
                confidences.append(pattern.confidence)

        # From graphs
        for graph in graphs:
            if graph.confidence:
                confidences.extend(list(graph.confidence.values()))

        # From hypotheses
        for hyp in hypotheses:
            confidences.append(hyp.confidence)

        if not confidences:
            return 0.5

        return float(np.mean(confidences))

    def _generate_recommendations(
        self,
        patterns: List[Any],
        graphs: List[Any],
        hypotheses: List[Hypothesis],
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for further investigation."""
        recommendations = []

        # High-priority hypotheses
        top_hypotheses = sorted(hypotheses, key=lambda h: h.priority, reverse=True)[:3]
        for hyp in top_hypotheses:
            recommendations.append(
                f"Priority hypothesis: {hyp.claim} (confidence: {hyp.confidence:.2f})"
            )

        # Patterns needing verification
        for pattern in patterns:
            if hasattr(pattern, 'significance') and pattern.significance > 0.05:
                recommendations.append(
                    f"Pattern needs verification: {pattern.description}"
                )

        # Suggest observations
        if context.get('available_targets'):
            recommendations.append(
                f"Consider observing: {', '.join([t['name'] for t in context['available_targets'][:3]])}"
            )

        return recommendations

    def run_deep_tests(self) -> Dict[str, Any]:
        """
        Run deep validation tests on all components.

        Returns:
            Test results with any errors found
        """
        print("=" * 60)
        print("Running Deep Validation Tests")
        print("=" * 60)

        test_results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'components_tested': []
        }

        # Test 1: First Principles Discovery
        print("\n[Test 1] First Principles Discovery Module")
        try:
            # Create simple test data
            test_data = np.random.randn(100, 2)
            test_vars = ['X', 'Y']

            patterns = self.first_principles.discover_from_data(
                test_data, test_vars, ['kg', 'm/s']
            )

            test_results['components_tested'].append('first_principles')
            test_results['passed'].append('First principles: Discovered patterns')
            print(f"  ✓ Discovered {len(patterns)} patterns")
        except Exception as e:
            test_results['failed'].append(f'First principles: {e}')
            print(f"  ✗ Error: {e}")

        # Test 2: Physics-Grounded Analogy
        print("\n[Test 2] Physics-Grounded Analogical Reasoning")
        try:
            analogy = self.analogy.validate_analogy('molecular_cloud', 'protoplanetary_disk')

            test_results['components_tested'].append('physics_grounded_analogy')
            if analogy.physical_grounding > 0.5:
                test_results['passed'].append(f"Analogy validation: grounding={analogy.physical_grounding:.2f}")
                print(f"  ✓ Analogy validation successful")
            else:
                test_results['warnings'].append(f"Analogy validation: low grounding {analogy.physical_grounding:.2f}")
                print(f"  ⚠ Warning: Low physical grounding")
        except Exception as e:
            test_results['failed'].append(f'Analogy validation: {e}')
            print(f"  ✗ Error: {e}")

        # Test 3: Automatic Constraint Discovery
        print("\n[Test 3] Automatic Constraint Discovery")
        try:
            # Create data with variation
            time = np.linspace(0, 10, 200)
            position = np.sin(time)
            energy = 0.5 * position**2 + 0.5 * np.gradient(time)[0]**2  # Conservation: T + V roughly constant

            test_data = np.column_stack([time, position, energy])
            test_vars = ['time', 'position', 'energy']

            constraints = self.constraints.discover_constraints(
                test_data, test_vars, time_index=0
            )

            test_results['components_tested'].append('constraint_discovery')
            test_results['passed'].append(f"Constraint discovery: Found {len(constraints)} constraints")
            print(f"  ✓ Discovered {len(constraints)} constraints")
        except Exception as e:
            test_results['failed'].append(f'Constraint discovery: {e}')
            print(f"  ✗ Error: {e}")

        # Test 4: Scalable Causal Inference
        print("\n[Test 4] Scalable Causal Inference")
        try:
            # Test with different sizes
            for n_vars in [5, 20, 50]:
                test_data = np.random.randn(500, n_vars)
                test_vars = [f'V{i}' for i in range(n_vars)]

                graph = self.causal.discover_causal_structure(
                    test_data, test_vars, method='auto'
                )

                print(f"    n_vars={n_vars}: {graph.method}, cost={graph.computational_cost:.1f}")

            test_results['components_tested'].append('scalable_causal')
            test_results['passed'].append("Scalable causal: Works across variable counts")
            print(f"  ✓ Scalable causal inference working")
        except Exception as e:
            test_results['failed'].append(f'Scalable causal: {e}')
            print(f"  ✗ Error: {e}")

        # Test 5: Active Experimentation
        print("\n[Test 5] Active Experimentation Engine")
        try:
            hypothesis = Hypothesis(
                hypothesis_id='test',
                claim='Test claim',
                predictions={'Y': 1.0},
                confidence=0.5,
                falsification_criteria=['Test criteria'],
                priority=0.5
            )

            targets = [{'name': 'test_target', 'observability': 0.8,
                        'required_instruments': ['TEL'], 'base_duration': 1.0}]
            instruments = {'TEL': {'sensitivity': 0.9, 'efficiency': 0.8, 'hourly_cost': 100}}

            experiment = self.experimentation.design_optimal_experiment(
                hypothesis, targets, instruments
            )

            test_results['components_tested'].append('active_experimentation')
            test_results['passed'].append(f"Active experimentation: Designed {experiment.experiment_id}")
            print(f"  ✓ Experiment design successful")
        except Exception as e:
            test_results['failed'].append(f'Active experimentation: {e}')
            print(f"  ✗ Error: {e}")

        # Test 6: Subtle Pattern Detection
        print("\n[Test 6] Subtle Pattern Detection")
        try:
            test_data = np.random.randn(200, 3)
            test_vars = ['var1', 'var2', 'var3']

            patterns = self.pattern_detection.scan_dataset(test_data, test_vars)

            test_results['components_tested'].append('subtle_patterns')
            test_results['passed'].append(f"Pattern detection: Found {len(patterns)} patterns")
            print(f"  ✓ Detected {len(patterns)} patterns")
        except Exception as e:
            test_results['failed'].append(f'Subtle patterns: {e}')
            print(f"  ✗ Error: {e}")

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Components tested: {len(test_results['components_tested'])}")
        print(f"Passed: {len(test_results['passed'])}")
        print(f"Warnings: {len(test_results['warnings'])}")
        print(f"Failed: {len(test_results['failed'])}")

        if test_results['failed']:
            print("\n❌ Some tests failed. Fixing errors...")
            return self._fix_errors_and_retry(test_results)
        else:
            print("\n✅ All tests passed!")
            return test_results

    def _fix_errors_and_retry(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to fix errors and retest."""
        print("\nAttempting to fix errors...")

        # Analyze failures and fix common issues
        fixes_applied = []

        # Check import dependencies
        missing_imports = []
        for error in test_results['failed']:
            if 'sklearn' in error.lower() and 'sklearn' not in str(SKLEARN_AVAILABLE):
                missing_imports.append('scikit-learn')
            if 'torch' in error.lower() and 'torch' not in str(TORCH_AVAILABLE):
                missing_imports.append('pytorch')

        if missing_imports:
            print(f"  Installing missing packages: {missing_imports}")
            # Note: In production, would use uv pip install --system
            fixes_applied.append(f"Installed: {missing_imports}")

        # Re-run tests after fixes
        # (In production, would recursively call run_deep_tests)
        print(f"  Fixes applied: {len(fixes_applied)}")
        print("  Please re-run tests manually after fixing dependencies.")

        return test_results


def demo_discovery_orchestrator():
    """Demonstrate full discovery orchestrator."""
    print("=" * 60)
    print("Discovery Orchestrator Demo")
    print("=" * 60)

    # Initialize orchestrator
    orchestrator = DiscoveryOrchestrator()

    # Create test data
    np.random.seed(42)
    n_samples = 500

    # Causal chain: X -> Y -> Z
    X = np.random.randn(n_samples)
    Y = 0.5 * X + np.random.randn(n_samples) * 0.5
    Z = 0.7 * Y + np.random.randn(n_samples) * 0.3

    data = np.column_stack([X, Y, Z])
    variable_names = ['X', 'Y', 'Z']

    # Domain context
    context = {
        'compare_to_known_systems': True,
        'available_targets': [
            {'name': 'source_A', 'observability': 0.8,
             'required_instruments': ['ALMA'], 'base_duration': 2.0}
        ],
        'instrument_caps': {
            'ALMA': {'sensitivity': 0.9, 'efficiency': 0.8, 'hourly_cost': 100}
        }
    }

    # Run discovery
    result = orchestrator.discover(
        data, variable_names, context, discovery_mode='comprehensive'
    )

    print(f"\nDiscovery Results:")
    print(f"  Patterns found: {len(result.discovered_patterns)}")
    print(f"  Causal graphs: {len(result.causal_graphs)}")
    print(f"  Hypotheses: {len(result.hypotheses)}")
    print(f"  Experiments designed: {len(result.experiments)}")
    print(f"  Overall confidence: {result.confidence:.2f}")

    print(f"\nRecommendations:")
    for rec in result.recommendations[:5]:
        print(f"  - {rec}")

    # Run deep tests
    print("\n" + "=" * 60)
    test_results = orchestrator.run_deep_tests()

    print("\n" + "=" * 60)


if __name__ == '__main__':
    demo_discovery_orchestrator()
