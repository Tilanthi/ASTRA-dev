"""
Benchmark Suite for STAR-Learn

Comprehensive testing framework to validate self-teaching improvements:

Tier 1: Foundational Capabilities
- Causal Discovery: Synthetic datasets with known structures
- Scientific Reasoning: GPQA-style questions
- Pattern Recognition: ARC-AGI tasks
- Mathematical Proof: IMO-ProofBench problems

Tier 2: Scientific Discovery
- Law Discovery: Rediscover physical laws from data
- Hypothesis Generation: Generate testable hypotheses
- Experiment Design: Create falsifiable experiments
- Theory Construction: Build explanatory frameworks

Tier 3: Self-Teaching Metrics
- Learning Rate: Improvement per iteration
- Transfer Efficiency: Cross-domain application
- Curriculum Quality: Difficulty appropriateness
- Knowledge Retention: Prevent forgetting
- Novelty Generation: Generate new insights

Tier 4: Autonomous Integration
- Swarm Coordination: Multi-agent collaboration
- Stigmergic Emergence: Collective intelligence
- Biological Fields: TAU/ETA/C_K dynamics
- MORK Integration: Ontology evolution
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import time


class BenchmarkTier(Enum):
    """Benchmark difficulty tiers"""
    FOUNDATIONAL = "tier_1"  # Basic capabilities
    DISCOVERY = "tier_2"  # Scientific discovery
    SELF_TEACHING = "tier_3"  # Learning metrics
    INTEGRATION = "tier_4"  # System integration


@dataclass
class BenchmarkTest:
    """A single benchmark test"""
    name: str
    tier: BenchmarkTier
    domain: str

    # Test function
    test_func: Optional[Callable] = None
    test_data: Optional[Dict] = None

    # Evaluation criteria
    success_criteria: Dict[str, float] = field(default_factory=dict)
    timeout_seconds: float = 60.0

    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class BenchmarkResult:
    """Result of running a benchmark test"""
    test_name: str
    tier: BenchmarkTier
    passed: bool
    score: float  # 0-1

    # Detailed metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0

    # Output
    output: str = ""
    error: Optional[str] = None

    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SelfTeachingMetrics:
    """Metrics for evaluating self-teaching capability"""
    # Learning metrics
    learning_rate: float = 0.0  # Improvement per iteration
    asymptotic_performance: float = 0.0  # Final performance level
    convergence_speed: float = 0.0  # Iterations to 90% of asymptotic

    # Transfer metrics
    transfer_efficiency: float = 0.0  # Performance on new domains
    zero_shot_transfer: float = 0.0  # Performance without domain-specific training
    few_shot_adaptation: float = 0.0  # Adaptation speed with few examples

    # Retention metrics
    retention_rate: float = 0.0  # Knowledge kept over time
    catastrophic_forgetting: float = 0.0  # Performance drop on old tasks
    memory_efficiency: float = 0.0  # Info retained per memory unit

    # Novelty metrics
    novelty_generation: float = 0.0  # Generate truly new insights
    creativity_score: float = 0.0  # Originality of solutions
    innovation_rate: float = 0.0  # New discoveries per time

    # Autonomy metrics
    autonomy_level: float = 0.0  # Independence from human intervention
    self_modification_success: float = 0.0  # Safe self-improvement
    curriculum_quality: float = 0.0  # Problem generation quality

    # Integration metrics
    stigmergic_coordination: float = 0.0  # Swarm coordination
    biological_field_dynamics: float = 0.0  # TAU/ETA/C_K evolution
    mork_integration: float = 0.0  # Ontology growth quality
    leapcore_evolution: float = 0.0  # Strategy evolution

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'learning_rate': self.learning_rate,
            'asymptotic_performance': self.asymptotic_performance,
            'convergence_speed': self.convergence_speed,
            'transfer_efficiency': self.transfer_efficiency,
            'zero_shot_transfer': self.zero_shot_transfer,
            'few_shot_adaptation': self.few_shot_adaptation,
            'retention_rate': self.retention_rate,
            'catastrophic_forgetting': self.catastrophic_forgetting,
            'memory_efficiency': self.memory_efficiency,
            'novelty_generation': self.novelty_generation,
            'creativity_score': self.creativity_score,
            'innovation_rate': self.innovation_rate,
            'autonomy_level': self.autonomy_level,
            'self_modification_success': self.self_modification_success,
            'curriculum_quality': self.curriculum_quality,
            'stigmergic_coordination': self.stigmergic_coordination,
            'biological_field_dynamics': self.biological_field_dynamics,
            'mork_integration': self.mork_integration,
            'leapcore_evolution': self.leapcore_evolution,
        }


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark suite"""
    # Test selection
    run_tier_1: bool = True
    run_tier_2: bool = True
    run_tier_3: bool = True
    run_tier_4: bool = True

    # Performance parameters
    n_iterations_per_test: int = 10
    timeout_per_test: float = 60.0
    parallel_execution: bool = False

    # Reporting
    generate_report: bool = True
    save_detailed_results: bool = True

    # Comparison
    baseline_comparison: bool = True
    baseline_path: str = "baseline_results.json"


class BenchmarkSuite:
    """
    Benchmark Suite for evaluating self-teaching systems.

    Provides comprehensive testing across all capability dimensions.
    """

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """
        Initialize the benchmark suite.

        Args:
            config: Benchmark configuration
        """
        self.config = config or BenchmarkConfig()

        # Load test definitions
        self.tests = self._load_tests()

        # Results storage
        self.results: List[BenchmarkResult] = []
        self.metrics_history: List[SelfTeachingMetrics] = []

        # Baseline data
        self.baseline: Optional[Dict] = None

    def _load_tests(self) -> Dict[str, BenchmarkTest]:
        """Load all benchmark tests."""
        tests = {}

        # Tier 1: Foundational Capabilities
        tests.update(TIER_1_TESTS)

        # Tier 2: Scientific Discovery
        tests.update(TIER_2_TESTS)

        # Tier 3: Self-Teaching Metrics
        tests.update(TIER_3_TESTS)

        # Tier 4: Autonomous Integration
        tests.update(TIER_4_TESTS)

        return tests

    def run_full_suite(self, system) -> Dict[str, Any]:
        """
        Run the full benchmark suite.

        Args:
            system: STAR-Learn system to test

        Returns:
            Summary of results
        """
        start_time = time.time()

        # Clear previous results
        self.results = []
        self.metrics_history = []

        # Run tests by tier
        tier_results = {}

        if self.config.run_tier_1:
            print("Running Tier 1: Foundational Capabilities...")
            tier_results['tier_1'] = self._run_tier(BenchmarkTier.FOUNDATIONAL, system)

        if self.config.run_tier_2:
            print("Running Tier 2: Scientific Discovery...")
            tier_results['tier_2'] = self._run_tier(BenchmarkTier.DISCOVERY, system)

        if self.config.run_tier_3:
            print("Running Tier 3: Self-Teaching Metrics...")
            tier_results['tier_3'] = self._run_tier(BenchmarkTier.SELF_TEACHING, system)

        if self.config.run_tier_4:
            print("Running Tier 4: Autonomous Integration...")
            tier_results['tier_4'] = self._run_tier(BenchmarkTier.INTEGRATION, system)

        # Calculate overall metrics
        metrics = self._calculate_metrics(tier_results, system)

        total_time = time.time() - start_time

        summary = {
            'tier_results': tier_results,
            'overall_metrics': metrics.to_dict(),
            'total_time': total_time,
            'tests_passed': sum(1 for r in self.results if r.passed),
            'tests_failed': sum(1 for r in self.results if not r.passed),
            'average_score': np.mean([r.score for r in self.results]) if self.results else 0.0
        }

        # Generate report if requested
        if self.config.generate_report:
            self._generate_report(summary)

        return summary

    def _run_tier(
        self,
        tier: BenchmarkTier,
        system
    ) -> Dict[str, BenchmarkResult]:
        """Run all tests in a tier."""
        tier_tests = {
            name: test
            for name, test in self.tests.items()
            if test.tier == tier
        }

        results = {}

        for name, test in tier_tests.items():
            print(f"  Running test: {name}...")
            result = self._run_test(test, system)
            results[name] = result
            self.results.append(result)

        return results

    def _run_test(
        self,
        test: BenchmarkTest,
        system
    ) -> BenchmarkResult:
        """Run a single benchmark test."""
        start_time = time.time()

        try:
            # Run test
            if test.test_func:
                test_result = test.test_func(system, test.test_data or {})
                score = test_result.get("score", 0.0)
                passed = score >= test.success_criteria.get("min_score", 0.5)
                metrics = test_result.get("metrics", {})
            else:
                score = 0.0
                passed = False
                metrics = {}

            execution_time = time.time() - start_time

            return BenchmarkResult(
                test_name=test.name,
                tier=test.tier,
                passed=passed,
                score=score,
                metrics=metrics,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return BenchmarkResult(
                test_name=test.name,
                tier=test.tier,
                passed=False,
                score=0.0,
                metrics={"error": str(e)},
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )

    def _generate_report(self, summary: Dict[str, Any]) -> None:
        """Generate benchmark report."""
        report = {
            "summary": summary,
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "tier": r.tier.value,
                    "passed": r.passed,
                    "score": r.score,
                    "execution_time": r.execution_time
                }
                for r in self.results
            ],
            "timestamp": datetime.now().isoformat()
        }

        # Save report
        if self.config.report_path:
            with open(self.config.report_path, 'w') as f:
                json.dump(report, f, indent=2)

    def add_test(self, test: BenchmarkTest) -> None:
        """Add a test to the benchmark suite."""
        self.tests[test.name] = test

    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary of all results."""
        return {
            "total_tests": len(self.results),
            "tests_passed": sum(1 for r in self.results if r.passed),
            "tests_failed": sum(1 for r in self.results if not r.passed),
            "average_score": np.mean([r.score for r in self.results]) if self.results else 0.0,
            "total_time": sum(r.execution_time for r in self.results)
        }


# Factory functions
def create_benchmark_suite(config: Optional[BenchmarkConfig] = None) -> BenchmarkSuite:
    """Create a benchmark suite."""
    return BenchmarkSuite(config or BenchmarkConfig())


# Tier test definitions
TIER_1_TESTS: Dict[str, BenchmarkTest] = {
    "causal_discovery_synthetic": BenchmarkTest(
        name="Causal Discovery - Synthetic Data",
        tier=BenchmarkTier.FOUNDATIONAL,
        domain="causal",
        description="Discover causal structure from synthetic datasets",
        success_criteria={"min_score": 0.7},
        timeout_seconds=60.0
    ),
    "scientific_reasoning_gpqa": BenchmarkTest(
        name="Scientific Reasoning - GPQA",
        tier=BenchmarkTier.FOUNDATIONAL,
        domain="reasoning",
        description="Answer GPQA-style scientific questions",
        success_criteria={"min_score": 0.6},
        timeout_seconds=60.0
    ),
    "pattern_recognition_arc": BenchmarkTest(
        name="Pattern Recognition - ARC-AGI",
        tier=BenchmarkTier.FOUNDATIONAL,
        domain="patterns",
        description="Solve ARC-AGI pattern tasks",
        success_criteria={"min_score": 0.5},
        timeout_seconds=60.0
    ),
}

TIER_2_TESTS: Dict[str, BenchmarkTest] = {
    "law_discovery": BenchmarkTest(
        name="Law Discovery",
        tier=BenchmarkTier.DISCOVERY,
        domain="physics",
        description="Rediscover physical laws from data",
        success_criteria={"min_score": 0.6},
        timeout_seconds=90.0
    ),
    "hypothesis_generation": BenchmarkTest(
        name="Hypothesis Generation",
        tier=BenchmarkTier.DISCOVERY,
        domain="discovery",
        description="Generate testable hypotheses",
        success_criteria={"min_score": 0.5},
        timeout_seconds=60.0
    ),
    "experiment_design": BenchmarkTest(
        name="Experiment Design",
        tier=BenchmarkTier.DISCOVERY,
        domain="scientific",
        description="Create falsifiable experiments",
        success_criteria={"min_score": 0.5},
        timeout_seconds=60.0
    ),
}

TIER_3_TESTS: Dict[str, BenchmarkTest] = {
    "learning_rate": BenchmarkTest(
        name="Learning Rate",
        tier=BenchmarkTier.SELF_TEACHING,
        domain="learning",
        description="Measure improvement per iteration",
        success_criteria={"min_score": 0.3},
        timeout_seconds=120.0
    ),
    "transfer_efficiency": BenchmarkTest(
        name="Transfer Efficiency",
        tier=BenchmarkTier.SELF_TEACHING,
        domain="learning",
        description="Measure cross-domain application",
        success_criteria={"min_score": 0.4},
        timeout_seconds=120.0
    ),
    "knowledge_retention": BenchmarkTest(
        name="Knowledge Retention",
        tier=BenchmarkTier.SELF_TEACHING,
        domain="memory",
        description="Measure retention and prevent forgetting",
        success_criteria={"min_score": 0.5},
        timeout_seconds=90.0
    ),
}

TIER_4_TESTS: Dict[str, BenchmarkTest] = {
    "swarm_coordination": BenchmarkTest(
        name="Swarm Coordination",
        tier=BenchmarkTier.INTEGRATION,
        domain="swarm",
        description="Multi-agent collaboration",
        success_criteria={"min_score": 0.4},
        timeout_seconds=120.0
    ),
    "stigmergic_emergence": BenchmarkTest(
        name="Stigmergic Emergence",
        tier=BenchmarkTier.INTEGRATION,
        domain="collective",
        description="Collective intelligence emergence",
        success_criteria={"min_score": 0.3},
        timeout_seconds=120.0
    ),
    "mork_integration": BenchmarkTest(
        name="MORK Integration",
        tier=BenchmarkTier.INTEGRATION,
        domain="ontology",
        description="Ontology evolution",
        success_criteria={"min_score": 0.5},
        timeout_seconds=90.0
    ),
}
