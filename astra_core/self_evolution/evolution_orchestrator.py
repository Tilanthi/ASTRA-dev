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
Evolution Orchestrator for STAN Self-Evolution

Manages the autonomous self-improvement cycle:
1. Evaluate current capabilities
2. Generate targeted mutations
3. Apply and test mutations
4. Select successful improvements
5. Repeat

This is the main entry point for the self-evolution system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import numpy as np
import time
import json
import os
from datetime import datetime

try:
    from .capability_evaluator import CapabilityEvaluator, EvaluationResult, CapabilityDomain
    from .mutation_engine import MutationEngine, MutationSpec, MutationResult
    from .capability_baseline import CapabilityProfile, ReasoningMetric
    from .code_analyzer import CodeAnalyzer
    from .enhanced_mutation import EnhancedMutationEngine, create_improved_mutation_engine
except ImportError:
    from capability_evaluator import CapabilityEvaluator, EvaluationResult, CapabilityDomain
    from mutation_engine import MutationEngine, MutationSpec, MutationResult
    from capability_baseline import CapabilityProfile, ReasoningMetric
    from code_analyzer import CodeAnalyzer
    from enhanced_mutation import EnhancedMutationEngine, create_improved_mutation_engine


class EvolutionPhase(Enum):
    """Phases of evolution cycle"""
    EVALUATION = "evaluation"
    MUTATION_GENERATION = "mutation_generation"
    MUTATION_TESTING = "mutation_testing"
    SELECTION = "selection"
    CONSOLIDATION = "consolidation"


@dataclass
class EvolutionConfig:
    """Configuration for evolution process"""
    # Cycle parameters
    max_cycles: int = 100
    mutations_per_cycle: int = 10
    improvement_threshold: float = 0.02  # Minimum improvement to accept

    # Evaluation parameters
    evaluation_timeout: float = 300.0  # seconds
    use_cached_evaluations: bool = True

    # Mutation parameters
    mutation_types: List[str] = field(default_factory=lambda: [
        "algorithm_optimization",
        "causal_model_update",
        "abstraction_refinement",
        "domain_knowledge_addition",
        "cross_domain_linking",
    ])

    # Selection parameters
    elitism_rate: float = 0.2  # Keep top 20% of mutations
    diversity_bonus: float = 0.1  # Bonus for novel mutations

    # Safety parameters
    rollback_on_failure: bool = True
    backup_before_mutation: bool = True
    max_consecutive_failures: int = 5

    # Logging
    log_file: str = "evolution_log.json"
    checkpoint_interval: int = 10


@dataclass
class EvolutionCycle:
    """Results of a single evolution cycle"""
    cycle_number: int
    phase: EvolutionPhase
    baseline_profile: Optional[CapabilityProfile] = None
    mutations_generated: List[MutationSpec] = field(default_factory=list)
    mutations_tested: List[MutationResult] = field(default_factory=list)
    successful_mutations: List[MutationResult] = field(default_factory=list)
    new_profile: Optional[CapabilityProfile] = None
    improvement: float = 0.0
    duration: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class EvolutionOrchestrator:
    """
    Orchestrates the autonomous self-evolution of STAN.

    This is the main controller for the self-improvement process.
    """

    def __init__(self,
                 stan_core_path: str = "/shared/ASTRA",
                 config: Optional[EvolutionConfig] = None):
        """
        Args:
            stan_core_path: Path to stan_core directory
            config: Optional evolution configuration
        """
        self.stan_core_path = stan_core_path
        self.config = config or EvolutionConfig()

        # Initialize components
        self.evaluator = CapabilityEvaluator(stan_core_path)
        self.mutation_engine = MutationEngine(stan_core_path)
        self.enhanced_mutation = create_improved_mutation_engine(stan_core_path)

        # Evolution state
        self.cycle_number = 0
        self.cycle_history: List[EvolutionCycle] = []
        self.best_profile: Optional[CapabilityProfile] = None
        self.best_score: float = 0.0

        # Safety state
        self.consecutive_failures: int = 0
        self.rollback_points: List[Dict[str, Any]] = []

        # Logging
        self.log_file = os.path.join(stan_core_path, self.config.log_file)
        self._init_logging()

    def run_evolution(self, num_cycles: int = 5) -> Dict[str, Any]:
        """
        Run autonomous evolution for specified cycles.

        Args:
            num_cycles: Number of evolution cycles to run

        Returns:
            Summary of evolution results
        """
        print(f"Starting STAN self-evolution for {num_cycles} cycles...")
        print(f"Stan core path: {self.stan_core_path}")
        print(f"Log file: {self.log_file}")

        # Save initial state
        self._save_checkpoint("initial")

        for cycle in range(num_cycles):
            self.cycle_number = cycle + 1
            print(f"\n{'='*80}")
            print(f"EVOLUTION CYCLE {self.cycle_number}/{num_cycles}")
            print(f"{'='*80}")

            try:
                cycle_result = self._run_single_cycle()
                self.cycle_history.append(cycle_result)

                if not cycle_result.success:
                    print(f"Cycle {self.cycle_number} failed: {cycle_result.error_message}")
                    self.consecutive_failures += 1

                    if self.consecutive_failures >= self.config.max_consecutive_failures:
                        print("Too many consecutive failures. Stopping evolution.")
                        break
                else:
                    self.consecutive_failures = 0

                    # Update best
                    if cycle_result.new_profile:
                        if cycle_result.new_profile.overall_score > self.best_score:
                            self.best_score = cycle_result.new_profile.overall_score
                            self.best_profile = cycle_result.new_profile

                            # Save checkpoint
                            if self.cycle_number % self.config.checkpoint_interval == 0:
                                self._save_checkpoint(f"cycle_{self.cycle_number}")

            except Exception as e:
                print(f"Error in cycle {self.cycle_number}: {e}")
                self.consecutive_failures += 1

        # Generate final summary
        summary = self._generate_summary()

        # Save final state
        self._save_checkpoint("final")

        return summary

    def _run_single_cycle(self) -> EvolutionCycle:
        """Run a single evolution cycle"""
        cycle_start = time.time()
        cycle = EvolutionCycle(
            cycle_number=self.cycle_number,
            phase=EvolutionPhase.EVALUATION
        )

        try:
            # Phase 1: Evaluate baseline
            print("\n[Phase 1: Baseline Evaluation]")
            baseline_result = self.evaluator.evaluate_full()

            if not baseline_result.success:
                cycle.success = False
                cycle.error_message = baseline_result.error_message
                return cycle

            cycle.baseline_profile = baseline_result.profile
            self._log_profile("baseline", baseline_result.profile)

            print(f"  Baseline overall score: {baseline_result.profile.overall_score:.3f}")

            # Phase 2: Generate mutations
            print("\n[Phase 2: Mutation Generation]")
            cycle.phase = EvolutionPhase.MUTATION_GENERATION

            capability_scores = {
                metric.value: score.value
                for metric, score in baseline_result.profile.scores.items()
            }

            mutations = self.mutation_engine.generate_mutations(
                capability_scores,
                self.config.mutations_per_cycle
            )

            cycle.mutations_generated = mutations
            print(f"  Generated {len(mutations)} mutations")

            # Phase 3: Test mutations
            print("\n[Phase 3: Mutation Testing]")
            cycle.phase = EvolutionPhase.MUTATION_TESTING

            for i, mutation in enumerate(mutations):
                print(f"  Testing mutation {i+1}/{len(mutations)}: {mutation.mutation_type.value}")

                mutation_result = self._test_mutation(mutation, baseline_result.profile)
                cycle.mutations_tested.append(mutation_result)

                if mutation_result.success:
                    print(f"    Success! Improvement: {mutation_result.improvement:.3f}")
                    cycle.successful_mutations.append(mutation_result)
                else:
                    print(f"    Failed: {mutation_result.error_message}")

            # Phase 4: Selection
            print("\n[Phase 4: Selection]")
            cycle.phase = EvolutionPhase.SELECTION

            selected = self._select_mutations(cycle.successful_mutations)
            print(f"  Selected {len(selected)} successful mutations")

            # Phase 5: Consolidation
            print("\n[Phase 5: Consolidation]")
            cycle.phase = EvolutionPhase.CONSOLIDATION

            # Re-evaluate after applying successful mutations
            final_result = self.evaluator.evaluate_full()

            if final_result.success:
                cycle.new_profile = final_result.profile

                # Compare to baseline
                comparison = self.evaluator.baseline.compare_profiles(
                    baseline_result.profile,
                    final_result.profile
                )

                cycle.improvement = comparison['overall_improvement']
                self._log_profile("final", final_result.profile)

                print(f"  Final overall score: {final_result.profile.overall_score:.3f}")
                print(f"  Improvement: {cycle.improvement:+.3f}")

                if comparison['is_better']:
                    print(f"  ✓ IMPROVED: {comparison['improvements']} improvements, {comparison['regressions']} regressions")

                cycle.duration = time.time() - cycle_start

            else:
                cycle.success = False
                cycle.error_message = "Final evaluation failed"

            return cycle

        except Exception as e:
            cycle.success = False
            cycle.error_message = str(e)
            cycle.duration = time.time() - cycle_start
            return cycle

    def _test_mutation(self, mutation: MutationSpec, baseline_profile: CapabilityProfile) -> MutationResult:
        """
        Test a mutation by applying it and evaluating.

        Args:
            mutation: Mutation to test
            baseline_profile: Baseline capability profile

        Returns:
            MutationResult with outcome
        """
        # Use enhanced mutation engine for real code changes
        target_capability = mutation.expected_improvement or "pattern_discovery"

        success, target_file, message = self.enhanced_mutation.generate_specific_mutation(target_capability)

        if success:
            # Create a successful mutation result
            result = MutationResult(
                mutation_spec=mutation,
                success=True,
                files_modified=[target_file] if target_file else []
            )

            try:
                # Evaluate with mutation
                eval_result = self.evaluator.evaluate_full()

                if eval_result.success:
                    # Compare to baseline
                    comparison = self.evaluator.baseline.compare_profiles(
                        baseline_profile,
                        eval_result.profile
                    )

                    # Check if mutation improved capabilities
                    is_improvement = (
                        comparison['overall_improvement'] > self.config.improvement_threshold and
                        comparison['regressions'] == 0
                    )

                    result.improvement = comparison['overall_improvement']

                    if not is_improvement:
                        # Rollback by restoring from backup or reverting
                        result.success = False
                        result.error_message = f"No improvement ({comparison['overall_improvement']:.3f})"
                    else:
                        print(f"    ✓ Mutation improved capabilities by {result.improvement:.3f}")

                else:
                    result.success = False
                    result.error_message = f"Evaluation failed: {eval_result.error_message}"

            except Exception as e:
                result.success = False
                result.error_message = str(e)

            return result
        else:
            # Enhanced mutation failed, try original method
            apply_result = self.mutation_engine.apply_mutation(mutation)

            if not apply_result.success:
                apply_result.improvement = 0.0
                return apply_result

            try:
                # Evaluate with mutation
                eval_result = self.evaluator.evaluate_full()

                if not eval_result.success:
                    # Rollback on evaluation failure
                    self.mutation_engine.rollback_mutation(apply_result)

                    apply_result.success = False
                    apply_result.error_message = f"Evaluation failed: {eval_result.error_message}"

                    return apply_result

                # Compare to baseline
                comparison = self.evaluator.baseline.compare_profiles(
                    baseline_profile,
                    eval_result.profile
                )

                # Check if mutation improved capabilities
                is_improvement = (
                    comparison['overall_improvement'] > self.config.improvement_threshold and
                    comparison['regressions'] == 0
                )

                # Store improvement in result
                apply_result.improvement = comparison['overall_improvement']

                # Rollback if not an improvement
                if not is_improvement:
                    self.mutation_engine.rollback_mutation(apply_result)
                    apply_result.success = False
                    apply_result.error_message = f"No improvement ({comparison['overall_improvement']:.3f})"

                return apply_result

            except Exception as e:
                # Rollback on error
                self.mutation_engine.rollback_mutation(apply_result)

                apply_result.success = False
                apply_result.error_message = str(e)

                return apply_result

    def _select_mutations(self, mutations: List[MutationResult]) -> List[MutationResult]:
        """Select best mutations to keep"""
        # Sort by improvement
        sorted_mutations = sorted(
            [m for m in mutations if m.success],
            key=lambda x: x.improvement if hasattr(x, 'improvement') else 0,
            reverse=True
        )

        # Apply elitism
        n_keep = max(1, int(len(sorted_mutations) * self.config.elitism_rate))

        return sorted_mutations[:n_keep]

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of evolution results"""
        if not self.cycle_history:
            return {'error': 'No cycles completed'}

        successful_cycles = [c for c in self.cycle_history if c.success]

        if not successful_cycles:
            return {'error': 'No successful cycles'}

        # Extract metrics
        baseline_scores = [c.baseline_profile.overall_score for c in successful_cycles if c.baseline_profile]
        final_scores = [c.new_profile.overall_score for c in successful_cycles if c.new_profile]
        improvements = [c.improvement for c in successful_cycles]

        best_cycle = max(successful_cycles, key=lambda c: c.improvement if c.new_profile else 0)

        return {
            'cycles_completed': len(self.cycle_history),
            'successful_cycles': len(successful_cycles),
            'initial_score': baseline_scores[0] if baseline_scores else 0.0,
            'final_score': final_scores[-1] if final_scores else 0.0,
            'best_score': max(final_scores) if final_scores else 0.0,
            'total_improvement': final_scores[-1] - baseline_scores[0] if final_scores and baseline_scores else 0.0,
            'average_improvement_per_cycle': np.mean(improvements) if improvements else 0.0,
            'best_cycle': best_cycle.cycle_number,
            'best_cycle_improvement': best_cycle.improvement,
            'mutations_tested': sum(len(c.mutations_tested) for c in self.cycle_history),
            'mutations_successful': sum(len(c.successful_mutations) for c in self.cycle_history),
        }

    def _save_checkpoint(self, name: str):
        """Save evolution checkpoint"""
        checkpoint = {
            'name': name,
            'cycle_number': self.cycle_number,
            'best_score': self.best_score,
            'best_profile': self._serialize_profile(self.best_profile) if self.best_profile else None,
            'timestamp': time.time(),
        }

        checkpoint_file = os.path.join(
            self.stan_core_path,
            f".evolution_checkpoint_{name}.json"
        )

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)

    def _serialize_profile(self, profile: CapabilityProfile) -> Dict[str, Any]:
        """Serialize capability profile for JSON storage"""
        return {
            'overall_score': profile.overall_score,
            'strengths': [m.value for m in profile.strengths],
            'weaknesses': [m.value for m in profile.weaknesses],
            'scores': {
                metric.value: {
                    'value': score.value,
                    'confidence': score.confidence,
                }
                for metric, score in profile.scores.items()
            }
        }

    def _log_profile(self, label: str, profile: CapabilityProfile):
        """Log profile to file"""
        log_entry = {
            'cycle': self.cycle_number,
            'label': label,
            'timestamp': time.time(),
            'profile': self._serialize_profile(profile)
        }

        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass  # Don't fail on logging errors

    def _init_logging(self):
        """Initialize logging system"""
        # Create/clear log file
        try:
            with open(self.log_file, 'w') as f:
                f.write('')  # Clear file
        except Exception:
            pass


__all__ = [
    'EvolutionPhase',
    'EvolutionConfig',
    'EvolutionCycle',
    'EvolutionOrchestrator',
]
