"""
Ablation Study Test Runner

Main script to run ablation studies on ASTRA system.
"""

import sys
import os
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import stan_core
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configurations import (
    AblationConfig,
    get_all_ablations,
    get_critical_ablations,
    get_ablation_by_name
)
from metrics import (
    QueryResult,
    MetricScore,
    AblationEvaluation,
    get_all_metrics,
    evaluate_result,
    compute_overall_score
)


# Test queries for ablation studies
TEST_QUERIES = [
    # Hypothesis Generation
    "Generate a novel hypothesis about the cause of filament width variations in the ISM",
    "Propose a testable explanation for unusual exoplanet atmospheric compositions",

    # Cross-Domain Reasoning
    "How do stellar feedback mechanisms influence galaxy-scale processes?",
    "Analyze the connection between high-energy transients and gravitational wave events",

    # Scientific Accuracy
    "Calculate the expected gravitational wave frequency from a binary neutron star merger",
    "Explain the physical constraints on dark matter detection methods",

    # Domain-Specific Knowledge
    "What are the main formation mechanisms for massive stars in dense clusters?",
    "How do pulsar timing arrays detect nanohertz gravitational waves?",

    # Causal Reasoning
    "What causal mechanisms link supernova rates to star formation history?",
    "Analyze the causal relationship between AGN activity and galaxy quenching",

    # Physics Reasoning
    "Derive the expected temperature profile of a radiative shock in the ISM",
    "Apply Jeans instability criteria to molecular cloud collapse",
]


@dataclass
class AblationComparison:
    """Comparison between ablated system and full system"""
    ablation_name: str
    full_system_score: float
    ablated_system_score: float
    performance_delta: float
    percent_degradation: float
    metric_comparisons: Dict[str, Dict[str, float]] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AblationTestRunner:
    """Runner for ablation studies"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or "stan_core/tests/ablation/results"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        self.metrics = get_all_metrics()
        self.results: Dict[str, AblationEvaluation] = {}

    def create_system_with_ablation(self, ablation_config: AblationConfig):
        """Create ASTRA system with ablated components"""
        try:
            from stan_core import create_stan_system

            # Create system configuration with ablations
            system_config = self._apply_ablation_config({}, ablation_config)

            # Create system with modified config
            system = create_stan_system(config=system_config)

            return system

        except Exception as e:
            print(f"Error creating system with ablation {ablation_config.name}: {e}")
            return None

    def _apply_ablation_config(self, base_config: Dict, ablation: AblationConfig) -> Dict:
        """Apply ablation configuration to system config"""
        config = base_config.copy()

        # Disable specified components
        if "disabled_components" in config:
            config["disabled_components"].update(ablation.disabled_components)
        else:
            config["disabled_components"] = set(ablation.disabled_components)

        # Apply component-specific settings
        config.update(ablation.settings)

        return config

    def process_query(self, system, query: str) -> QueryResult:
        """Process a query with the system"""
        start_time = time.time()

        try:
            # Process query
            result = system.answer(query)

            processing_time = time.time() - start_time

            # Extract answer and metadata
            answer = result.get('answer', '')
            reasoning_trace = result.get('reasoning_trace', [])
            confidence = result.get('confidence', 0.5)
            sources = result.get('sources', [])

            return QueryResult(
                query=query,
                answer=answer,
                reasoning_trace=reasoning_trace,
                confidence=confidence,
                sources=sources,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return QueryResult(
                query=query,
                answer=f"Error: {str(e)}",
                processing_time=processing_time,
                error=str(e)
            )

    def run_ablation(self, ablation_config: AblationConfig,
                     queries: Optional[List[str]] = None) -> AblationEvaluation:
        """Run a single ablation study"""
        print(f"\n{'='*60}")
        print(f"Running ablation: {ablation_config.name}")
        print(f"Description: {ablation_config.description}")
        print(f"{'='*60}")

        if queries is None:
            queries = TEST_QUERIES

        # Create system with ablation
        system = self.create_system_with_ablation(ablation_config)

        if system is None:
            print(f"Failed to create system for ablation {ablation_config.name}")
            return AblationEvaluation(ablation_name=ablation_config.name)

        # Process queries
        query_results = []
        all_metric_scores = []

        for i, query in enumerate(queries):
            print(f"\n[{i+1}/{len(queries)}] Processing: {query[:60]}...")

            result = self.process_query(system, query)
            query_results.append(result)

            # Evaluate result
            metric_scores = evaluate_result(result, self.metrics)
            all_metric_scores.extend(metric_scores)

            # Print summary
            overall = compute_overall_score(metric_scores, self.metrics)
            print(f"  Score: {overall:.3f} | Time: {result.processing_time:.2f}s")

        # Aggregate metric scores
        aggregated_scores = self._aggregate_metric_scores(all_metric_scores)
        overall_score = compute_overall_score(aggregated_scores, self.metrics)

        evaluation = AblationEvaluation(
            ablation_name=ablation_config.name,
            query_results=query_results,
            metric_scores=aggregated_scores,
            overall_score=overall_score
        )

        self.results[ablation_config.name] = evaluation

        print(f"\n{'='*60}")
        print(f"Ablation {ablation_config.name} complete")
        print(f"Overall Score: {overall_score:.3f}")
        print(f"{'='*60}")

        return evaluation

    def _aggregate_metric_scores(self, metric_scores: List[MetricScore]) -> List[MetricScore]:
        """Aggregate metric scores across multiple queries"""
        # Group by metric name
        grouped: Dict[str, List[MetricScore]] = {}
        for score in metric_scores:
            if score.metric_name not in grouped:
                grouped[score.metric_name] = []
            grouped[score.metric_name].append(score)

        # Average scores for each metric
        aggregated = []
        for metric_name, scores in grouped.items():
            avg_value = sum(s.value for s in scores) / len(scores)
            aggregated.append(MetricScore(
                metric_name=metric_name,
                value=avg_value,
                normalized_value=avg_value
            ))

        return aggregated

    def run_full_system_baseline(self, queries: Optional[List[str]] = None) -> AblationEvaluation:
        """Run full system (no ablations) to establish baseline"""
        print(f"\n{'='*60}")
        print("Running FULL SYSTEM BASELINE")
        print(f"{'='*60}")

        # Create empty ablation config (no disabled components)
        baseline_config = AblationConfig(
            name="full_system",
            description="Full ASTRA system with all components enabled",
            ablation_type=None
        )

        return self.run_ablation(baseline_config, queries)

    def compare_ablation_to_baseline(self, ablation_name: str) -> AblationComparison:
        """Compare ablated system to full system baseline"""
        if "full_system" not in self.results:
            raise ValueError("Must run full system baseline first")

        if ablation_name not in self.results:
            raise ValueError(f"Ablation {ablation_name} not found in results")

        baseline = self.results["full_system"]
        ablated = self.results[ablation_name]

        # Compute comparison
        delta = baseline.overall_score - ablated.overall_score
        percent_degradation = (delta / baseline.overall_score) * 100 if baseline.overall_score > 0 else 0

        # Compare individual metrics
        metric_comparisons = {}
        for base_score in baseline.metric_scores:
            ablated_score = next(
                (s for s in ablated.metric_scores if s.metric_name == base_score.metric_name),
                None
            )

            if ablated_score:
                metric_delta = base_score.value - ablated_score.value
                metric_comparisons[base_score.metric_name] = {
                    "baseline": base_score.value,
                    "ablated": ablated_score.value,
                    "delta": metric_delta,
                    "percent_delta": (metric_delta / base_score.value * 100) if base_score.value > 0 else 0
                }

        comparison = AblationComparison(
            ablation_name=ablation_name,
            full_system_score=baseline.overall_score,
            ablated_system_score=ablated.overall_score,
            performance_delta=delta,
            percent_degradation=percent_degradation,
            metric_comparisons=metric_comparisons
        )

        return comparison

    def run_all_ablations(self, ablations: Optional[List[AblationConfig]] = None,
                         queries: Optional[List[str]] = None) -> Dict[str, AblationComparison]:
        """Run all ablation studies and compare to baseline"""
        if ablations is None:
            ablations = get_all_ablations()

        # Run baseline first
        print("\n" + "="*80)
        print("STARTING ABLATION STUDIES")
        print("="*80)

        self.run_full_system_baseline(queries)

        # Run all ablations
        comparisons = {}

        for ablation in ablations:
            evaluation = self.run_ablation(ablation, queries)
            comparison = self.compare_ablation_to_baseline(ablation.name)
            comparisons[ablation.name] = comparison

        # Save results
        self._save_results(comparisons)

        # Print summary
        self._print_summary(comparisons)

        return comparisons

    def run_critical_ablations_only(self, queries: Optional[List[str]] = None) -> Dict[str, AblationComparison]:
        """Run only critical ablations (high expected impact)"""
        critical_ablations = get_critical_ablations()
        return self.run_all_ablations(critical_ablations, queries)

    def _save_results(self, comparisons: Dict[str, AblationComparison]):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ablation_results_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        # Convert to serializable format
        results_dict = {
            name: {
                "ablation_name": comp.ablation_name,
                "full_system_score": comp.full_system_score,
                "ablated_system_score": comp.ablated_system_score,
                "performance_delta": comp.performance_delta,
                "percent_degradation": comp.percent_degradation,
                "metric_comparisons": comp.metric_comparisons,
                "timestamp": comp.timestamp
            }
            for name, comp in comparisons.items()
        }

        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"\nResults saved to: {filepath}")

    def _print_summary(self, comparisons: Dict[str, AblationComparison]):
        """Print summary of ablation results"""
        print("\n" + "="*80)
        print("ABLATION STUDY SUMMARY")
        print("="*80)

        # Sort by degradation
        sorted_comparisons = sorted(
            comparisons.items(),
            key=lambda x: x[1].percent_degradation,
            reverse=True
        )

        print(f"\n{'Ablation':<30} {'Baseline':<10} {'Ablated':<10} {'Delta':<10} {'Degradation':<12}")
        print("-"*80)

        for name, comp in sorted_comparisons:
            print(f"{name:<30} {comp.full_system_score:<10.3f} {comp.ablated_system_score:<10.3f} "
                  f"{comp.performance_delta:<10.3f} {comp.percent_degradation:>6.1f}%")

        print("\n" + "="*80)
        print("KEY FINDINGS:")
        print("="*80)

        # Most critical component
        most_critical = max(comparisons.items(), key=lambda x: x[1].percent_degradation)
        print(f"\nMost Critical Component:")
        print(f"  {most_critical[0]}: {most_critical[1].percent_degradation:.1f}% degradation")

        # Least critical component
        least_critical = min(comparisons.items(), key=lambda x: x[1].percent_degradation)
        print(f"\nLeast Critical Component:")
        print(f"  {least_critical[0]}: {least_critical[1].percent_degradation:.1f}% degradation")

        # Average degradation
        avg_degradation = sum(c.percent_degradation for c in comparisons.values()) / len(comparisons)
        print(f"\nAverage Degradation: {avg_degradation:.1f}%")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run ASTRA ablation studies")
    parser.add_argument("--critical-only", action="store_true",
                       help="Run only critical ablations")
    parser.add_argument("--ablation", type=str,
                       help="Run specific ablation by name")
    parser.add_argument("--queries", type=str,
                       help="JSON file containing custom queries")
    parser.add_argument("--output", type=str,
                       help="Output directory for results")

    args = parser.parse_args()

    # Load queries
    queries = TEST_QUERIES
    if args.queries:
        with open(args.queries, 'r') as f:
            queries = json.load(f)

    # Create runner
    runner = AblationTestRunner(output_dir=args.output)

    # Run ablations
    if args.ablation:
        # Run specific ablation
        ablation_config = get_ablation_by_name(args.ablation)
        if ablation_config is None:
            print(f"Error: Ablation '{args.ablation}' not found")
            return

        runner.run_full_system_baseline(queries)
        runner.run_ablation(ablation_config, queries)
        comparison = runner.compare_ablation_to_baseline(args.ablation)

        print(f"\nResults for {args.ablation}:")
        print(f"  Performance Delta: {comparison.performance_delta:.3f}")
        print(f"  Percent Degradation: {comparison.percent_degradation:.1f}%")

    elif args.critical_only:
        # Run critical ablations only
        runner.run_critical_ablations_only(queries)

    else:
        # Run all ablations
        runner.run_all_ablations(queries)


if __name__ == "__main__":
    main()
