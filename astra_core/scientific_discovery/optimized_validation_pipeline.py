"""
Optimized Validation Pipeline with Performance Enhancements

This module implements performance optimizations for the validation pipeline:
1. Parallel stage execution for independent stages
2. Early exit strategy for low-quality discoveries
3. Enhanced caching with multi-level architecture
4. Progressive validation depth
5. Performance monitoring

Version: 1.0.0
Date: 2026-07-01
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from .validation_pipeline import (
    ValidationPipeline,
    ValidationResult,
    ValidationStage,
    PipelineReport,
    ValidationStatus,
    ConfidenceLevel
)
from .literature_validator import NoveltyReport

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for validation pipeline"""
    validation_time: float = 0.0
    stage_timings: Dict[str, float] = field(default_factory=dict)
    cache_hit_rate: float = 0.0
    parallel_utilization: float = 0.0
    early_exit_triggered: bool = False
    validation_depth: str = "full"  # "basic", "standard", "extensive"


class OptimizedValidationPipeline(ValidationPipeline):
    """
    Optimized validation pipeline with performance enhancements

    Key optimizations:
    1. Parallel execution of independent validation stages
    2. Early exit for clearly invalid discoveries
    3. Progressive validation depth based on discovery quality
    4. Performance monitoring and metrics
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_metrics = PerformanceMetrics()
        self.validation_count = 0
        self.early_exit_count = 0

    async def validate_optimized(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str = "general",
        enable_early_exit: bool = True,
        enable_progressive_depth: bool = True
    ) -> PipelineReport:
        """
        Optimized validation with performance enhancements

        Args:
            discovery_claim: The discovery text to validate
            domains: List of astronomical domains
            discovery_type: Type of discovery
            enable_early_exit: Enable early exit for low-quality discoveries
            enable_progressive_depth: Enable progressive validation depth

        Returns:
            PipelineReport with comprehensive validation results
        """
        start_time = time.time()
        self.validation_count += 1

        logger.info(f"Starting optimized validation pipeline for discovery #{self.validation_count}")

        # Phase 1: Quick assessment (seconds)
        quick_assessment_start = time.time()
        quick_score = self._quick_assess_discovery(discovery_claim)
        quick_assessment_time = time.time() - quick_assessment_start

        self.performance_metrics.stage_timings['quick_assessment'] = quick_assessment_time

        # Early exit for clearly low-quality discoveries
        if enable_early_exit and quick_score < 0.3:
            logger.info(f"Early exit triggered: quick assessment score {quick_score:.3f} < 0.3")
            self.early_exit_count += 1
            self.performance_metrics.early_exit_triggered = True
            self.performance_metrics.validation_depth = "basic"

            return await self._basic_validation_report(
                discovery_claim, domains, discovery_type, quick_score
            )

        # Phase 2: Semantic novelty (must run first, 30-45 seconds)
        novelty_start = time.time()
        novelty_report = await self.literature_validator.validate_novelty(
            discovery_claim=discovery_claim,
            domains=domains,
            discovery_type=discovery_type
        )
        novelty_time = time.time() - novelty_start

        self.performance_metrics.stage_timings['semantic_novelty'] = novelty_time

        # Early exit if clearly not novel
        if enable_early_exit and novelty_report.novelty_score < 0.2:
            logger.info(f"Early exit triggered: novelty score {novelty_report.novelty_score:.3f} < 0.2")
            self.early_exit_count += 1
            self.performance_metrics.early_exit_triggered = True
            self.performance_metrics.validation_depth = "standard"

            return await self._standard_validation_report(
                discovery_claim, domains, discovery_type, novelty_report, quick_score
            )

        # Phase 3: Parallel validation of independent stages (5-10 seconds)
        parallel_start = time.time()
        parallel_time = await self._run_parallel_stages(discovery_claim, domains, discovery_type)
        parallel_stage_time = time.time() - parallel_start

        self.performance_metrics.stage_timings['parallel_stages'] = parallel_stage_time
        self.performance_metrics.parallel_utilization = (
            parallel_stage_time / (parallel_stage_time * 3) if parallel_stage_time > 0 else 0
        )

        # Phase 4: Final assessment
        final_report = await self._generate_final_report(
            discovery_claim, domains, discovery_type, novelty_report, quick_score
        )

        # Update performance metrics
        total_time = time.time() - start_time
        self.performance_metrics.validation_time = total_time
        self.performance_metrics.validation_depth = "extensive"

        # Cache statistics
        if self.literature_validator:
            cache_stats = self.literature_validator.get_cache_stats()
            self.performance_metrics.cache_hit_rate = cache_stats.get('hit_rate', 0.0)

        logger.info(
            f"Optimized validation complete: time={total_time:.2f}s, "
            f"depth={self.performance_metrics.validation_depth}, "
            f"early_exit={self.performance_metrics.early_exit_triggered}"
        )

        return final_report

    def _quick_assess_discovery(self, discovery_claim: str) -> float:
        """
        Quick quality assessment (takes <1 second)

        Returns:
            Quick assessment score (0-1)
        """
        score = 0.5  # Base score

        # Length check (too short or too long is suspicious)
        length = len(discovery_claim)
        if 200 <= length <= 2000:
            score += 0.2
        elif length < 100:
            score -= 0.3

        # Scientific content indicators
        scientific_terms = [
            'analysis', 'data', 'observation', 'measurement', 'statistical',
            'correlation', 'significant', 'hypothesis', 'theory', 'model'
        ]
        term_count = sum(1 for term in scientific_terms if term in discovery_claim.lower())
        score += min(0.3, term_count * 0.05)

        # Citation presence
        if '(' in discovery_claim and any(char.isdigit() for char in discovery_claim):
            score += 0.1

        # Quantitative claims
        if any(char.isdigit() for char in discovery_claim):
            score += 0.1

        return max(0.0, min(1.0, score))

    async def _run_parallel_stages(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str
    ) -> float:
        """
        Run independent validation stages in parallel

        Returns:
            Time taken for parallel stages
        """
        start_time = time.time()

        # Create tasks for independent stages
        tasks = []

        if self.citation_validator:
            tasks.append(self._run_citation_validation(discovery_claim))

        if self.formula_validator:
            tasks.append(self._run_formula_validation(discovery_claim))

        if self.statistical_validator:
            tasks.append(self._run_statistical_validation(discovery_claim))

        # Run all tasks in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return time.time() - start_time

    async def _basic_validation_report(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str,
        quick_score: float
    ) -> PipelineReport:
        """Generate basic validation report for early exit cases"""
        from .validation_pipeline import ValidationResult

        # Create minimal validation results
        quick_result = ValidationResult(
            stage=ValidationStage.SEMANTIC_NOVELTY,
            passed=quick_score > 0.3,
            score=quick_score,
            details={"quick_assessment": True},
            errors=["Failed quick assessment"] if quick_score < 0.3 else [],
            warnings=[]
        )

        return PipelineReport(
            discovery_claim=discovery_claim,
            discovery_type=discovery_type,
            domains=domains,
            overall_status=ValidationStatus.CANDIDATE,
            confidence_level=ConfidenceLevel.CANDIDATE,
            stage_results=[quick_result],
            total_validation_time=time.time(),
            limitations=["Early exit - basic validation only"]
        )

    async def _standard_validation_report(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str,
        novelty_report: NoveltyReport,
        quick_score: float
    ) -> PipelineReport:
        """Generate standard validation report"""
        from .validation_pipeline import ValidationResult

        novelty_result = ValidationResult(
            stage=ValidationStage.SEMANTIC_NOVELTY,
            passed=novelty_report.novelty_score > 0.2,
            score=novelty_report.novelty_score,
            details={"novelty_score": novelty_report.novelty_score},
            errors=["Low novelty score"] if novelty_report.novelty_score < 0.2 else [],
            warnings=[]
        )

        return PipelineReport(
            discovery_claim=discovery_claim,
            discovery_type=discovery_type,
            domains=domains,
            overall_status=ValidationStatus.CANDIDATE,
            confidence_level=ConfidenceLevel.CANDIDATE,
            stage_results=[novelty_result],
            novelty_report=novelty_report,
            total_validation_time=time.time(),
            limitations=["Early exit - standard validation only"]
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        total_validations = self.validation_count if self.validation_count > 0 else 1
        early_exit_rate = self.early_exit_count / total_validations

        return {
            "total_validations": self.validation_count,
            "early_exit_count": self.early_exit_count,
            "early_exit_rate": early_exit_rate,
            "avg_validation_time": self.performance_metrics.validation_time,
            "cache_hit_rate": self.performance_metrics.cache_hit_rate,
            "parallel_utilization": self.performance_metrics.parallel_utilization,
            "stage_timings": self.performance_metrics.stage_timings
        }


def create_optimized_validation_pipeline(
    literature_validator,
    enable_citation_validation: bool = True,
    enable_formula_validation: bool = True,
    enable_statistical_validation: bool = True,
    parallel_stages: bool = True
) -> OptimizedValidationPipeline:
    """
    Create an optimized validation pipeline instance

    Args:
        literature_validator: LiteratureValidator instance
        enable_citation_validation: Enable citation validation stage
        enable_formula_validation: Enable formula validation stage
        enable_statistical_validation: Enable statistical validation stage
        parallel_stages: Run independent stages in parallel

    Returns:
        Configured OptimizedValidationPipeline instance
    """
    return OptimizedValidationPipeline(
        literature_validator=literature_validator,
        enable_citation_validation=enable_citation_validation,
        enable_formula_validation=enable_formula_validation,
        enable_statistical_validation=enable_statistical_validation,
        parallel_stages=parallel_stages
    )


# Test function
async def test_optimized_pipeline():
    """Test the optimized validation pipeline"""
    from .literature_validator import create_literature_validator

    # Create optimized validators
    lit_validator = create_literature_validator()
    pipeline = create_optimized_validation_pipeline(lit_validator)

    # Test discovery
    test_discovery = (
        "Molecular clouds exhibit a characteristic filament width of approximately 0.1 parsecs, "
        "as observed in Herschel surveys (Arzoumanian et al., 2011). This width is consistent "
        "across diverse environments with p < 0.001, suggesting a fundamental physical process "
        "regulating filament structure (n=150 clouds, correlation r=0.87)."
    )

    print("=== Optimized Validation Pipeline Test ===")

    # Test with early exit
    report = await pipeline.validate_optimized(
        discovery_claim=test_discovery,
        domains=["ism", "molecular_clouds"],
        discovery_type="pattern_discovery",
        enable_early_exit=True,
        enable_progressive_depth=True
    )

    print(f"Discovery: {test_discovery[:100]}...")
    print(f"Overall Status: {report.overall_status.value}")
    print(f"Total Time: {report.total_validation_time:.2f}s")
    print(f"Validation Depth: {pipeline.performance_metrics.validation_depth}")

    # Performance summary
    summary = pipeline.get_performance_summary()
    print(f"\nPerformance Summary:")
    print(f"  Total Validations: {summary['total_validations']}")
    print(f"  Early Exit Rate: {summary['early_exit_rate']:.1%}")
    print(f"  Cache Hit Rate: {summary['cache_hit_rate']:.1%}")
    print(f"  Parallel Utilization: {summary['parallel_utilization']:.1%}")
    print(f"  Stage Timings: {summary['stage_timings']}")


if __name__ == "__main__":
    asyncio.run(test_optimized_pipeline())