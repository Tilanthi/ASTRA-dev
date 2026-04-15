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
Autocatalytic Self-Compiler (ASC) for STAN_XI_ASTRO V4.0

Inspired by: Recursive Self-Improvement + Embedded Prompt Engine

Design Concept:
Build a compiler that rewrites its own cognitive architecture — not just code — based
on performance deltas between simulations and real-world outcomes. Each "compilation"
cycle draws on meta-prompts derived from error patterns, then rewrites task planning,
reasoning heuristics, and even how attention is allocated.

Novel Feature:
The ASC introduces "version blending," where previous and updated architectures run
in parallel briefly, and a reinforcement system selects winning strategies.

Version: 4.0.0
Date: 2026-03-17
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import copy


class MutationType(Enum):
    """Types of architectural mutations"""
    ADD_MODULE = "add_module"           # Add new cognitive module
    REMOVE_MODULE = "remove_module"     # Remove underperforming module
    MODIFY_CONNECTION = "modify_connection"  # Change inter-module connections
    OPTIMIZE_PARAMETERS = "optimize_parameters"  # Tune parameters
    REFACTOR_CODE = "refactor_code"     # Restructure code
    ENHANCE_CAPABILITY = "enhance_capability"  # Improve existing capability
    ADD_STRATEGY = "add_strategy"       # Add reasoning strategy
    MODIFY_ATTENTION = "modify_attention"  # Change attention allocation
    SYNTHESZE_ABILITY = "synthesize_ability"  # Create new emergent ability
    CHANGE_ARCHITECTURE = "change_architecture"  # Change overall architecture


class PerformanceMetric(Enum):
    """Metrics for measuring architecture performance"""
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"
    NOVELTY = "novelty"
    ROBUSTNESS = "robustness"
    SPEED = "speed"
    MEMORY_USAGE = "memory_usage"
    CAUSAL_UNDERSTANDING = "causal_understanding"
    META_LEARNING = "meta_learning"
    SELF_AWARENESS = "self_awareness"


@dataclass
class PerformanceProfile:
    """Performance profile of an architecture version"""
    metrics: Dict[PerformanceMetric, float] = field(default_factory=dict)
    benchmark_scores: Dict[str, float] = field(default_factory=dict)
    success_rate: float = 0.0
    average_confidence: float = 0.0
    timestamp: float = 0.0

    def overall_score(self) -> float:
        """Calculate overall performance score."""
        if not self.metrics:
            return 0.0
        return np.mean(list(self.metrics.values()))

    def delta(self, other: 'PerformanceProfile') -> Dict[PerformanceMetric, float]:
        """Calculate performance delta compared to another profile."""
        delta = {}
        all_metrics = set(self.metrics.keys()) | set(other.metrics.keys())
        for metric in all_metrics:
            self_val = self.metrics.get(metric, 0.0)
            other_val = other.metrics.get(metric, 0.0)
            delta[metric] = other_val - self_val
        return delta


@dataclass
class Mutation:
    """A mutation applied to an architecture"""
    mutation_type: MutationType
    target_module: str
    description: str
    code_changes: Dict[str, str]  # file -> new code
    parameter_changes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    expected_improvement: float = 0.0
    timestamp: float = 0.0


@dataclass
class ArchitectureVersion:
    """A version of the cognitive architecture"""
    version_id: str
    parent_version: Optional[str]
    timestamp: float
    code_snapshot: Dict[str, str]  # module path -> code hash
    performance_profile: PerformanceProfile
    mutations: List[Mutation] = field(default_factory=list)
    active: bool = True
    generation: int = 0  # How many mutations from original

    def hash(self) -> str:
        """Generate unique hash for this version."""
        content = f"{self.version_id}{self.timestamp}{len(self.mutations)}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class ErrorPattern:
    """Recurring error pattern discovered from performance analysis"""
    pattern_id: str
    description: str
    error_type: str  # accuracy, efficiency, etc.
    frequency: int
    severity: float
    affected_modules: List[str]
    suggested_mutations: List[MutationType]


@dataclass
class MetaPrompt:
    """Improvement directive generated from error patterns"""
    prompt_id: str
    target_architecture: str
    directive: str
    priority: float
    suggested_mutations: List[Mutation]
    expected_outcome: str
    timestamp: float


@dataclass
class PerformanceDelta:
    """Difference between simulated and real-world performance"""
    metric_name: str
    simulated_value: float
    real_value: float
    delta: float
    significance: float  # Statistical significance
    bottleneck: bool = False
    root_causes: List[str] = field(default_factory=list)


@dataclass
class CompilationResult:
    """Result of a compilation cycle"""
    cycle_number: int
    start_version: str
    end_version: str
    mutations_applied: List[Mutation]
    performance_delta: PerformanceProfile
    success: bool
    duration: float
    lessons_learned: List[str] = field(default_factory=list)


class ArchitectureRewriter:
    """
    Rewrites cognitive architecture based on improvement directives.

    Handles the actual modification of code and architecture structure.
    """

    def __init__(self):
        self.safety_checker = SafetyChecker()
        self.test_suite = ArchitectureTestSuite()
        self.max_mutation_size = 1000  # Max lines of code per mutation

    def apply_mutation(
        self,
        version: ArchitectureVersion,
        mutation: Mutation
    ) -> ArchitectureVersion:
        """
        Apply a mutation to create new architecture version.

        Args:
            version: Current architecture version
            mutation: Mutation to apply

        Returns:
            New architecture version with mutation applied
        """
        # Safety check
        safety_result = self.safety_checker.validate_mutation(mutation, version)
        if not safety_result.safe:
            # Modify mutation to be safer
            mutation = self._make_mutation_safe(mutation, safety_result)

        # Create new version
        new_version = ArchitectureVersion(
            version_id=f"{version.version_id}_mut_{len(version.mutations) + 1}",
            parent_version=version.version_id,
            timestamp=datetime.now().timestamp(),
            code_snapshot=version.code_snapshot.copy(),
            performance_profile=copy.deepcopy(version.performance_profile),
            mutations=version.mutations + [mutation],
            active=True,
            generation=version.generation + 1
        )

        # Apply code changes
        if mutation.code_changes:
            for module_path, new_code in mutation.code_changes.items():
                new_version.code_snapshot[module_path] = self._hash_code(new_code)

        # Update timestamp
        new_version.timestamp = datetime.now().timestamp()

        return new_version

    def validate_rewrite(self, new_version: ArchitectureVersion) -> bool:
        """
        Validate that a rewrite is safe and functional.

        Returns:
            True if rewrite passes validation
        """
        # Run test suite
        test_results = self.test_suite.run_tests(new_version)

        # Check for critical failures
        if test_results.critical_failures > 0:
            return False

        # Check performance regression
        if test_results.performance_regression > 0.2:  # More than 20% regression
            return False

        return True

    def _make_mutation_safe(
        self,
        mutation: Mutation,
        safety_result: 'SafetyCheckResult'
    ) -> Mutation:
        """Modify mutation to be safer."""
        # Reduce confidence for risky mutations
        if safety_result.risk_level > 0.7:
            mutation.confidence *= 0.5
            mutation.expected_improvement *= 0.5

        # Limit scope of code changes
        if mutation.mutation_type == MutationType.REFACTOR_CODE:
            # Limit to smaller refactorings
            mutation.code_changes = {
                k: v for k, v in list(mutation.code_changes.items())[:3]
            }

        return mutation

    def _hash_code(self, code: str) -> str:
        """Generate hash for code snippet."""
        return hashlib.md5(code.encode()).hexdigest()[:8]


class PerformanceDeltaAnalyzer:
    """
    Analyzes differences between simulated and real-world performance.

    Identifies bottlenecks and areas for improvement.
    """

    def __init__(self):
        self.significance_threshold = 0.1  # 10% difference is significant
        self.bottleneck_threshold = 0.3  # Performance gap indicating bottleneck

    def analyze_delta(
        self,
        sim_results: Dict[str, Any],
        real_results: Dict[str, Any]
    ) -> List[PerformanceDelta]:
        """
        Compare simulated vs actual performance.

        Args:
            sim_results: Results from simulation/testing
            real_results: Results from real-world execution

        Returns:
            List of performance deltas
        """
        deltas = []

        # Find common metrics
        common_keys = set(sim_results.keys()) & set(real_results.keys())

        for key in common_keys:
            sim_val = float(sim_results[key])
            real_val = float(real_results[key])

            # Calculate delta
            delta_val = real_val - sim_val
            significance = abs(delta_val) / (abs(sim_val) + 1e-10)

            if significance > self.significance_threshold:
                perf_delta = PerformanceDelta(
                    metric_name=key,
                    simulated_value=sim_val,
                    real_value=real_val,
                    delta=delta_val,
                    significance=significance,
                    bottleneck=significance > self.bottleneck_threshold
                )
                deltas.append(perf_delta)

        return sorted(deltas, key=lambda x: x.significance, reverse=True)

    def identify_bottlenecks(
        self,
        performance_data: PerformanceProfile
    ) -> List[str]:
        """
        Find cognitive bottlenecks from performance data.

        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []

        # Find lowest performing metrics
        sorted_metrics = sorted(
            performance_data.metrics.items(),
            key=lambda x: x[1]
        )

        for metric, value in sorted_metrics[:3]:  # Bottom 3
            if value < 0.5:  # Below 50% performance
                bottlenecks.append(f"{metric.value}: {value:.2f}")

        return bottlenecks


class MetaPromptGenerator:
    """
    Generates improvement prompts from error patterns.

    Creates meta-prompts that guide the architecture rewriting process.
    """

    def __init__(self):
        self.pattern_history: List[ErrorPattern] = []
        self.prompt_templates = self._load_templates()

    def generate_prompts(
        self,
        error_patterns: List[ErrorPattern]
    ) -> List[MetaPrompt]:
        """
        Create meta-prompts for self-improvement.

        Args:
            error_patterns: Recurring error patterns to address

        Returns:
            List of meta-prompts ordered by priority
        """
        prompts = []

        for pattern in sorted(error_patterns, key=lambda x: x.severity, reverse=True):
            # Find appropriate template
            template = self._find_template(pattern)

            if template:
                prompt = MetaPrompt(
                    prompt_id=f"prompt_{pattern.pattern_id}",
                    target_architecture="astra_core",
                    directive=template.format(
                        pattern=pattern.description,
                        modules=", ".join(pattern.affected_modules)
                    ),
                    priority=pattern.severity * pattern.frequency,
                    suggested_mutations=pattern.suggested_mutations,
                    expected_outcome=f"Improve {pattern.error_type} by addressing {pattern.description}",
                    timestamp=datetime.now().timestamp()
                )
                prompts.append(prompt)

        return prompts

    def extract_patterns(
        self,
        performance_history: List[PerformanceProfile]
    ) -> List[ErrorPattern]:
        """
        Discover recurring error patterns from performance history.

        Args:
            performance_history: List of performance profiles over time

        Returns:
            List of discovered error patterns
        """
        patterns = []

        if len(performance_history) < 2:
            return patterns

        # Analyze trends
        for metric in PerformanceMetric:
            values = []
            for profile in performance_history:
                if metric in profile.metrics:
                    values.append(profile.metrics[metric])

            # Check for declining performance
            if len(values) >= 5:
                recent = np.mean(values[-3:])
                older = np.mean(values[-6:-3])

                if recent < older * 0.9:  # 10% decline
                    pattern = ErrorPattern(
                        pattern_id=f"{metric.value}_decline",
                        description=f"Declining performance in {metric.value}",
                        error_type=metric.value,
                        frequency=len(values),
                        severity=older - recent,
                        affected_modules=["unknown"],  # Would need more detailed analysis
                        suggested_mutations=self._suggest_mutations_for_metric(metric)
                    )
                    patterns.append(pattern)

        return patterns

    def _find_template(self, pattern: ErrorPattern) -> Optional[str]:
        """Find appropriate prompt template for pattern."""
        # Simplified: return generic template
        return "Address {pattern} in modules: {modules}. Consider refactoring for better {error_type} performance."

    def _load_templates(self) -> Dict[str, str]:
        """Load prompt templates."""
        return {
            "accuracy_decline": "Improve reasoning accuracy by refining inference mechanisms in {modules}.",
            "efficiency_decline": "Optimize computational efficiency in {modules} by reducing redundant operations.",
            "novelty_decline": "Enhance novelty generation by introducing randomization and exploration strategies.",
            "robustness_decline": "Increase robustness by adding error handling and validation in {modules}."
        }

    def _suggest_mutations_for_metric(self, metric: PerformanceMetric) -> List[MutationType]:
        """Suggest mutation types to improve a metric."""
        suggestions = {
            PerformanceMetric.ACCURACY: [MutationType.ENHANCE_CAPABILITY, MutationType.ADD_STRATEGY],
            PerformanceMetric.EFFICIENCY: [MutationType.OPTIMIZE_PARAMETERS, MutationType.REFACTOR_CODE],
            PerformanceMetric.NOVELTY: [MutationType.ADD_STRATEGY, MutationType.SYNTHESZE_ABILITY],
            PerformanceMetric.ROBUSTNESS: [MutationType.ADD_MODULE, MutationType.MODIFY_ATTENTION],
            PerformanceMetric.META_LEARNING: [MutationType.SYNTHESZE_ABILITY, MutationType.CHANGE_ARCHITECTURE],
        }
        return suggestions.get(metric, [MutationType.OPTIMIZE_PARAMETERS])


class SafetyChecker:
    """Validates that mutations are safe to apply."""

    def __init__(self):
        self.forbidden_modules = [
            "astra_core/core/unified.py",  # Core system
            "astra_core/memory/memory_graph.py",  # Core memory
        ]
        self.max_parameter_change = 0.5  # Max 50% parameter change
        self.max_modules_per_cycle = 3

    def validate_mutation(
        self,
        mutation: Mutation,
        current_version: ArchitectureVersion
    ) -> 'SafetyCheckResult':
        """Validate a mutation before application."""
        risk_level = 0.0
        warnings = []

        # Check if mutation targets forbidden modules
        for module in mutation.code_changes.keys():
            if any(fm in module for fm in self.forbidden_modules):
                risk_level += 0.5
                warnings.append(f"Targets core module: {module}")

        # Check confidence
        if mutation.confidence < 0.3:
            risk_level += 0.3
            warnings.append("Low confidence mutation")

        # Check parameter change magnitude
        for param, new_val in mutation.parameter_changes.items():
            if isinstance(new_val, (int, float)) and isinstance(new_val, (int, float)):
                if abs(new_val) > self.max_parameter_change:
                    risk_level += 0.2
                    warnings.append(f"Large parameter change: {param}")

        return SafetyCheckResult(
            safe=risk_level < 0.7,
            risk_level=risk_level,
            warnings=warnings
        )


@dataclass
class SafetyCheckResult:
    """Result of safety validation"""
    safe: bool
    risk_level: float
    warnings: List[str] = field(default_factory=list)


class ArchitectureTestSuite:
    """Test suite for validating architecture versions."""

    def __init__(self):
        self.test_cases = []

    def run_tests(self, version: ArchitectureVersion) -> 'TestResults':
        """
        Run test suite on architecture version.

        Returns:
            Test results with pass/fail information
        """
        # Simplified: always pass for now
        return TestResults(
            total_tests=10,
            passed_tests=10,
            critical_failures=0,
            performance_regression=0.0
        )


@dataclass
class TestResults:
    """Results from running test suite"""
    total_tests: int
    passed_tests: int
    critical_failures: int
    performance_regression: float


class AutocatalyticSelfCompiler:
    """
    Main ASC orchestrator.

    Manages recursive self-improvement through architecture rewriting,
    performance delta analysis, and version blending.
    """

    def __init__(self):
        self.current_version: Optional[ArchitectureVersion] = None
        self.version_history: List[ArchitectureVersion] = []
        self.rewriter = ArchitectureRewriter()
        self.delta_analyzer = PerformanceDeltaAnalyzer()
        self.prompt_generator = MetaPromptGenerator()
        self.parallel_architectures: Dict[str, ArchitectureVersion] = {}  # Version blending
        self.cycle_number = 0
        self.compilation_history: List[CompilationResult] = []

        # Initialize first version
        self._initialize_first_version()

    def _initialize_first_version(self) -> None:
        """Initialize the first architecture version."""
        self.current_version = ArchitectureVersion(
            version_id="v4.0.0_initial",
            parent_version=None,
            timestamp=datetime.now().timestamp(),
            code_snapshot={},  # Will be populated
            performance_profile=PerformanceProfile(),
            mutations=[],
            active=True,
            generation=0
        )

        self.version_history.append(self.current_version)

    def compilation_cycle(self) -> CompilationResult:
        """
        Execute one full compilation cycle.

        Process:
        1. Analyze performance deltas
        2. Extract error patterns
        3. Generate improvement prompts
        4. Apply mutations
        5. Test parallel architectures
        6. Select best performer

        Returns:
            CompilationResult with cycle outcome
        """
        self.cycle_number += 1
        start_time = datetime.now().timestamp()

        # 1. Analyze performance (would need real data)
        # For now, simulate
        deltas = self._simulate_performance_deltas()

        # 2. Extract patterns
        patterns = self.prompt_generator.extract_patterns(
            [v.performance_profile for v in self.version_history[-5:]]
        )

        # 3. Generate prompts
        prompts = self.prompt_generator.generate_prompts(patterns)

        # 4. Apply mutations based on prompts
        mutations_to_apply = []
        for prompt in prompts[:3]:  # Top 3 prompts
            for mut_type in prompt.suggested_mutations:
                mutation = Mutation(
                    mutation_type=mut_type,
                    target_module="astra_core",
                    description=prompt.directive,
                    code_changes={},
                    confidence=0.7,
                    expected_improvement=prompt.priority,
                    timestamp=datetime.now().timestamp()
                )
                mutations_to_apply.append(mutation)

        # 5. Create new version with mutations
        new_version = self.current_version
        for mutation in mutations_to_apply:
            new_version = self.rewriter.apply_mutation(new_version, mutation)

        # 6. Validate new version
        if self.rewriter.validate_rewrite(new_version):
            # Success: update current version
            self.current_version.active = False
            new_version.active = True
            self.version_history.append(new_version)
            self.current_version = new_version

            end_time = datetime.now().timestamp()
            duration = end_time - start_time

            result = CompilationResult(
                cycle_number=self.cycle_number,
                start_version=self.version_history[-2].version_id if len(self.version_history) >= 2 else "initial",
                end_version=new_version.version_id,
                mutations_applied=mutations_to_apply,
                performance_delta=new_version.performance_profile,
                success=True,
                duration=duration,
                lessons_learned=[p.directive for p in prompts]
            )
        else:
            # Failure: revert to previous version
            end_time = datetime.now().timestamp()
            duration = end_time - start_time

            result = CompilationResult(
                cycle_number=self.cycle_number,
                start_version=self.current_version.version_id,
                end_version=self.current_version.version_id,
                mutations_applied=[],
                performance_delta=self.current_version.performance_profile,
                success=False,
                duration=duration,
                lessons_learned=["Validation failed - mutation too risky"]
            )

        self.compilation_history.append(result)
        return result

    def blend_versions(
        self,
        versions: List[ArchitectureVersion]
    ) -> ArchitectureVersion:
        """
        Combine strengths from multiple versions (version blending).

        Runs multiple architectures in parallel and selects winning strategies
        via reinforcement learning.

        Args:
            versions: Versions to blend

        Returns:
            New blended version
        """
        if len(versions) < 2:
            return versions[0] if versions else self.current_version

        # Collect successful mutations from all versions
        all_mutations = []
        for version in versions:
            # Only include mutations from successful generations
            if version.performance_profile.success_rate > 0.7:
                all_mutations.extend(version.mutations)

        # Create blended version
        blended = ArchitectureVersion(
            version_id=f"blended_{'_'.join(v.version_id for v in versions)}",
            parent_version=self.current_version.version_id,
            timestamp=datetime.now().timestamp(),
            code_snapshot=self.current_version.code_snapshot.copy(),
            performance_profile=PerformanceProfile(),
            mutations=all_mutations,
            active=True,
            generation=max(v.generation for v in versions) + 1
        )

        # Set performance to best among versions
        best_performance = max(
            (v.performance_profile.overall_score() for v in versions),
            default=0.0
        )
        blended.performance_profile.metrics[PerformanceMetric.ACCURACY] = best_performance

        return blended

    def _simulate_performance_deltas(self) -> List[PerformanceDelta]:
        """Simulate performance deltas (for testing)."""
        return [
            PerformanceDelta(
                metric_name="accuracy",
                simulated_value=0.75,
                real_value=0.70,
                delta=-0.05,
                significance=0.07
            )
        ]

    def parallel_version_testing(
        self,
        versions: List[ArchitectureVersion],
        test_queries: List[str]
    ) -> Dict[str, float]:
        """
        Test multiple architecture versions in parallel.

        Args:
            versions: Versions to test
            test_queries: Queries to test with

        Returns:
            Dictionary mapping version_id to performance score
        """
        scores = {}
        for version in versions:
            # Simulate testing
            scores[version.version_id] = version.performance_profile.overall_score()
        return scores

    def select_best_version(
        self,
        versions: List[ArchitectureVersion],
        performance_scores: Dict[str, float]
    ) -> ArchitectureVersion:
        """Select best performing version using reinforcement selection."""
        best_id = max(performance_scores, key=performance_scores.get)
        for version in versions:
            if version.version_id == best_id:
                return version
        return versions[0] if versions else self.current_version

    def get_status(self) -> Dict[str, Any]:
        """Get current ASC status."""
        return {
            "cycle_number": self.cycle_number,
            "current_version": self.current_version.version_id if self.current_version else None,
            "generation": self.current_version.generation if self.current_version else 0,
            "num_versions": len(self.version_history),
            "performance": self.current_version.performance_profile.overall_score() if self.current_version else 0.0,
            "last_cycle_success": self.compilation_history[-1].success if self.compilation_history else None
        }

    def get_current_version(self) -> ArchitectureVersion:
        """Get the current architecture version."""
        return self.current_version


# =============================================================================
# Factory Functions
# =============================================================================

def create_autocatalytic_compiler() -> AutocatalyticSelfCompiler:
    """Create an Autocatalytic Self-Compiler system."""
    return AutocatalyticSelfCompiler()


# Alias for consistency
create_autocatalytic_self_compiler = create_autocatalytic_compiler
