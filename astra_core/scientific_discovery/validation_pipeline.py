"""
ASTRA Multi-Stage Validation Pipeline

This module implements a comprehensive validation pipeline that goes beyond
basic novelty checking to include:
- Citation validation (detect hallucinated references)
- Formula validation (physics/math consistency checking)
- Statistical validation (sample size, statistical significance)
- Multi-stage confidence progression
- Parallel processing for speed

Version: 1.0.0
Date: 2026-07-01
"""

import asyncio
import re
import math
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import json

try:
    import numpy as np
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from .literature_validator import (
    LiteratureValidator,
    NoveltyReport,
    ConfidenceLevel,
    ValidationStatus,
    SimilarPaper,
    CitationReport,
    FormulaReport
)

logger = logging.getLogger(__name__)


class ValidationStage(Enum):
    """Validation stages in the pipeline"""
    LITERATURE_SEARCH = "literature_search"
    SEMANTIC_NOVELTY = "semantic_novelty"
    CITATION_VALIDATION = "citation_validation"
    FORMULA_VALIDATION = "formula_validation"
    STATISTICAL_VALIDATION = "statistical_validation"
    FINAL_ASSESSMENT = "final_assessment"


@dataclass
class ValidationResult:
    """Result from a single validation stage"""
    stage: ValidationStage
    passed: bool
    score: float  # 0.0 to 1.0
    details: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PipelineReport:
    """Comprehensive report from validation pipeline"""
    discovery_claim: str
    discovery_type: str
    domains: List[str]
    overall_status: ValidationStatus
    confidence_level: ConfidenceLevel
    stage_results: List[ValidationResult] = field(default_factory=list)
    novelty_report: Optional[NoveltyReport] = None
    citation_report: Optional[CitationReport] = None
    formula_report: Optional[FormulaReport] = None
    statistical_report: Optional[Dict[str, Any]] = None
    total_validation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            "discovery_claim": self.discovery_claim,
            "discovery_type": self.discovery_type,
            "domains": self.domains,
            "overall_status": self.overall_status.value,
            "confidence_level": self.confidence_level.value,
            "stage_results": [
                {
                    "stage": sr.stage.value,
                    "passed": sr.passed,
                    "score": sr.score,
                    "details": sr.details,
                    "errors": sr.errors,
                    "warnings": sr.warnings
                }
                for sr in self.stage_results
            ],
            "novelty_report": {
                "novelty_score": self.novelty_report.novelty_score if self.novelty_report else 0,
                "similar_papers": [
                    {
                        "title": p.title,
                        "similarity_score": p.similarity_score,
                        "authors": p.authors,
                        "year": p.year
                    }
                    for p in (self.novelty_report.similar_papers if self.novelty_report else [])
                ]
            } if self.novelty_report else None,
            "citation_report": {
                "total_citations": self.citation_report.total_citations if self.citation_report else 0,
                "verified_citations": self.citation_report.verified_citations if self.citation_report else 0,
                "hallucinated_citations": self.citation_report.hallucinated_citations if self.citation_report else 0,
            } if self.citation_report else None,
            "formula_report": {
                "total_formulas": self.formula_report.total_formulas if self.formula_report else 0,
                "verified_formulas": self.formula_report.verified_formulas if self.formula_report else 0,
                "inconsistent_formulas": self.formula_report.inconsistent_formulas if self.formula_report else 0,
            } if self.formula_report else None,
            "statistical_report": self.statistical_report,
            "total_validation_time": self.total_validation_time,
            "timestamp": self.timestamp.isoformat(),
            "limitations": self.limitations
        }


class CitationValidator:
    """Validate citations in discovery claims"""

    def __init__(self, literature_validator: LiteratureValidator):
        self.literature_validator = literature_validator
        # Common citation patterns
        self.citation_patterns = [
            r'\((\w+\s+et\s+al\.?,\s*\d{4})\)',  # (Smith et al., 2020)
            r'(\w+\s+et\s+al\.\s+\[\d+\])',     # Smith et al. [15]
            r'\[(\w+\s+et\s+al\.,\s*\d{4})\]',  # [Smith et al., 2020]
            r'(\w+\s+\(\d{4}\))',                # Smith (2020)
        ]

    def extract_citations(self, text: str) -> List[str]:
        """Extract potential citations from text"""
        citations = []
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        return list(set(citations))  # Remove duplicates

    async def validate_citations(self, discovery_claim: str) -> CitationReport:
        """
        Validate that citations in discovery claim refer to real papers

        Returns:
            CitationReport with validation results
        """
        citations = self.extract_citations(discovery_claim)

        if not citations:
            return CitationReport(
                total_citations=0,
                verified_citations=0,
                hallucinated_citations=0,
                unverifiable_citations=0,
                citation_details=[]
            )

        verified = 0
        hallucinated = 0
        unverifiable = 0
        details = []

        for citation in citations:
            # Try to find the paper in literature
            try:
                # Search for first author name + year
                author_match = re.search(r'(\w+)', citation)
                year_match = re.search(r'(\d{4})', citation)

                if author_match and year_match:
                    author = author_match.group(1)
                    year = year_match.group(1)

                    # Search literature for this paper
                    search_query = f"author:{author} year:{year}"
                    result = await self.literature_validator.arxiv_client.search(
                        query=search_query,
                        max_results=5
                    )

                    if result.papers:
                        verified += 1
                        details.append({
                            "citation": citation,
                            "status": "verified",
                            "matched_paper": result.papers[0].title
                        })
                    else:
                        unverifiable += 1
                        details.append({
                            "citation": citation,
                            "status": "unverifiable",
                            "reason": "No matching papers found"
                        })
                else:
                    unverifiable += 1

            except Exception as e:
                logger.warning(f"Failed to validate citation {citation}: {e}")
                unverifiable += 1

        # If citation rate is too high or unverifiable rate is high, flag as potential hallucination
        if unverifiable > len(citations) * 0.5:
            hallucinated = unverifiable

        return CitationReport(
            total_citations=len(citations),
            verified_citations=verified,
            hallucinated_citations=hallucinated,
            unverifiable_citations=unverifiable,
            citation_details=details
        )


class FormulaValidator:
    """Validate mathematical and physical formulas in discovery claims"""

    # Physical constants and their values (for consistency checking)
    PHYSICAL_CONSTANTS = {
        'c': 2.998e8,        # Speed of light (m/s)
        'G': 6.674e-11,      # Gravitational constant
        'h': 6.626e-34,      # Planck constant
        'k_B': 1.381e-23,    # Boltzmann constant
        'm_p': 1.673e-27,    # Proton mass
        'sigma_SB': 5.670e-8 # Stefan-Boltzmann constant
    }

    def __init__(self):
        """Initialize formula validator"""
        # Formula patterns
        self.formula_patterns = [
            r'[\w\s]+\s*[=]\s*[\w\d\.\+\-\*\/\^\(\)]+',  # Simple equations
            r'\$[^$]+\$',                                  # LaTeX formulas
            r'\\[[^\]]+\]',                                # LaTeX formulas
        ]

    def extract_formulas(self, text: str) -> List[str]:
        """Extract mathematical formulas from text"""
        formulas = []
        for pattern in self.formula_patterns:
            matches = re.findall(pattern, text)
            formulas.extend(matches)
        return formulas

    def check_formula_consistency(self, formula: str) -> Tuple[bool, str]:
        """
        Check if a formula is physically/mathematically consistent

        Returns:
            (is_consistent, reasoning)
        """
        # Basic checks
        if '=' in formula:
            lhs, rhs = formula.split('=', 1)

            # Check for dimensional consistency (very basic)
            # This is a simplified check - real dimensional analysis is much more complex

            # Check for obviously wrong things like dividing by constants
            for const_name, const_value in self.PHYSICAL_CONSTANTS.items():
                if f'/{const_name}' in formula or f'/ {const_name}' in formula:
                    # Dividing by a fundamental constant is suspicious
                    return False, f"Suspicious: dividing by fundamental constant {const_name}"

            # Check if formula contains only valid characters
            valid_chars = set('0123456789.+-*/^()= abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
            formula_chars = set(formula)
            if not formula_chars.issubset(valid_chars):
                return False, "Formula contains invalid characters"

        return True, "Formula appears consistent"

    def validate_formulas(self, discovery_claim: str) -> FormulaReport:
        """
        Validate formulas in discovery claim

        Returns:
            FormulaReport with validation results
        """
        formulas = self.extract_formulas(discovery_claim)

        if not formulas:
            return FormulaReport(
                total_formulas=0,
                verified_formulas=0,
                derivable_formulas=0,
                inconsistent_formulas=0,
                unverifiable_formulas=0,
                formula_details=[]
            )

        verified = 0
        inconsistent = 0
        derivable = 0
        unverifiable = 0
        details = []

        for formula in formulas:
            is_consistent, reasoning = self.check_formula_consistency(formula)

            if is_consistent:
                verified += 1
                details.append({
                    "formula": formula,
                    "status": "consistent",
                    "reasoning": reasoning
                })
            else:
                inconsistent += 1
                details.append({
                    "formula": formula,
                    "status": "inconsistent",
                    "reasoning": reasoning
                })

        return FormulaReport(
            total_formulas=len(formulas),
            verified_formulas=verified,
            derivable_formulas=derivable,
            inconsistent_formulas=inconsistent,
            unverifiable_formulas=unverifiable,
            formula_details=details
        )


class StatisticalValidator:
    """Validate statistical claims in discoveries"""

    def __init__(self):
        """Initialize statistical validator"""
        self.statistical_patterns = [
            (r'significant.*?p\s*[<]\s*([\d.]+)', 'p_value'),
            (r'correlation.*?r\s*=\s*([\-\d.]+)', 'correlation'),
            (r'sample.*?size\s*[=]\s*(\d+)', 'sample_size'),
            (r'sigma\s*[=]\s*([\d.]+)', 'sigma'),
            (r'confidence.*?interval\s*(\d+)%', 'confidence_interval'),
            (r'n\s*=\s*(\d+)', 'n_samples'),
        ]

    def extract_statistical_claims(self, text: str) -> Dict[str, List[float]]:
        """Extract statistical claims from text"""
        claims = {}
        for pattern, claim_type in self.statistical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                claims[claim_type] = [float(m) for m in matches]
        return claims

    def validate_statistical_claims(self, discovery_claim: str) -> ValidationResult:
        """
        Validate statistical claims in discovery

        Returns:
            ValidationResult with statistical validation details
        """
        claims = self.extract_statistical_claims(discovery_claim)

        if not claims:
            return ValidationResult(
                stage=ValidationStage.STATISTICAL_VALIDATION,
                passed=True,
                score=1.0,
                details={"message": "No statistical claims to validate"},
                warnings=[]
            )

        errors = []
        warnings = []
        score = 1.0

        # Check p-values
        if 'p_value' in claims:
            for p_val in claims['p_value']:
                if p_val > 0.1:
                    warnings.append(f"High p-value {p_val} suggests weak statistical significance")
                    score *= 0.8
                elif p_val < 0.001:
                    # Very low p-values are suspicious
                    if p_val < 1e-10:
                        errors.append(f"Extremely low p-value {p_val} is suspicious")
                        score *= 0.5

        # Check correlations
        if 'correlation' in claims:
            for corr in claims['correlation']:
                if abs(corr) > 1.0:
                    errors.append(f"Invalid correlation coefficient {corr} (must be between -1 and 1)")
                    score *= 0.0
                elif abs(corr) > 0.99:
                    warnings.append(f"Near-perfect correlation {corr} is suspicious")
                    score *= 0.7

        # Check sample sizes
        if 'sample_size' in claims:
            for n in claims['sample_size']:
                if n < 10:
                    warnings.append(f"Very small sample size {n}")
                    score *= 0.6
                elif n > 1e9:
                    warnings.append(f"Implausibly large sample size {n}")
                    score *= 0.7

        return ValidationResult(
            stage=ValidationStage.STATISTICAL_VALIDATION,
            passed=len(errors) == 0,
            score=max(0.0, min(1.0, score)),
            details={
                "statistical_claims": claims,
                "claims_checked": len(claims)
            },
            errors=errors,
            warnings=warnings
        )


class ValidationPipeline:
    """
    Multi-stage validation pipeline for scientific discoveries

    Pipeline stages:
    1. Literature Search - Search arXiv/ADS for similar work
    2. Semantic Novelty - Compute semantic similarity to existing papers
    3. Citation Validation - Check citations are real papers
    4. Formula Validation - Check mathematical/physical consistency
    5. Statistical Validation - Check statistical claims
    6. Final Assessment - Combine all evidence into confidence level
    """

    def __init__(
        self,
        literature_validator: LiteratureValidator,
        enable_citation_validation: bool = True,
        enable_formula_validation: bool = True,
        enable_statistical_validation: bool = True,
        parallel_stages: bool = True
    ):
        """
        Initialize validation pipeline

        Args:
            literature_validator: LiteratureValidator instance
            enable_citation_validation: Enable citation validation stage
            enable_formula_validation: Enable formula validation stage
            enable_statistical_validation: Enable statistical validation stage
            parallel_stages: Run independent stages in parallel
        """
        self.literature_validator = literature_validator
        self.enable_citation_validation = enable_citation_validation
        self.enable_formula_validation = enable_formula_validation
        self.enable_statistical_validation = enable_statistical_validation
        self.parallel_stages = parallel_stages

        # Initialize sub-validators
        self.citation_validator = CitationValidator(literature_validator) if enable_citation_validation else None
        self.formula_validator = FormulaValidator() if enable_formula_validation else None
        self.statistical_validator = StatisticalValidator() if enable_statistical_validation else None

        logger.info(
            f"ValidationPipeline initialized with "
            f"citation={enable_citation_validation}, "
            f"formula={enable_formula_validation}, "
            f"statistical={enable_statistical_validation}, "
            f"parallel={parallel_stages}"
        )

    async def run_stage(
        self,
        stage: ValidationStage,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str
    ) -> ValidationResult:
        """Run a single validation stage"""

        if stage == ValidationStage.LITERATURE_SEARCH:
            # This is integrated into semantic novelty stage
            return ValidationResult(
                stage=stage,
                passed=True,
                score=1.0,
                details={"message": "Literature search completed"}
            )

        elif stage == ValidationStage.SEMANTIC_NOVELTY:
            # This is the main literature validation
            novelty_report = await self.literature_validator.validate_novelty(
                discovery_claim=discovery_claim,
                domains=domains,
                discovery_type=discovery_type
            )
            passed = novelty_report.novelty_score > 0.3
            return ValidationResult(
                stage=stage,
                passed=passed,
                score=novelty_report.novelty_score,
                details={
                    "novelty_score": novelty_report.novelty_score,
                    "similar_papers_found": len(novelty_report.similar_papers),
                    "max_similarity": max([p.similarity_score for p in novelty_report.similar_papers]) if novelty_report.similar_papers else 0
                },
                errors=[] if passed else ["Low novelty score"],
                warnings=[]
            )

        elif stage == ValidationStage.CITATION_VALIDATION:
            if not self.citation_validator:
                return ValidationResult(
                    stage=stage,
                    passed=True,
                    score=1.0,
                    details={"message": "Citation validation disabled"}
                )

            citation_report = await self.citation_validator.validate_citations(discovery_claim)
            passed = citation_report.hallucinated_citations == 0
            score = 1.0 - (citation_report.hallucinated_citations / max(1, citation_report.total_citations))
            return ValidationResult(
                stage=stage,
                passed=passed,
                score=score,
                details={
                    "total_citations": citation_report.total_citations,
                    "verified": citation_report.verified_citations,
                    "hallucinated": citation_report.hallucinated_citations
                },
                errors=["Hallucinated citations detected"] if citation_report.hallucinated_citations > 0 else [],
                warnings=[]
            )

        elif stage == ValidationStage.FORMULA_VALIDATION:
            if not self.formula_validator:
                return ValidationResult(
                    stage=stage,
                    passed=True,
                    score=1.0,
                    details={"message": "Formula validation disabled"}
                )

            formula_report = self.formula_validator.validate_formulas(discovery_claim)
            passed = formula_report.inconsistent_formulas == 0
            score = formula_report.verified_formulas / max(1, formula_report.total_formulas)
            return ValidationResult(
                stage=stage,
                passed=passed,
                score=score,
                details={
                    "total_formulas": formula_report.total_formulas,
                    "verified": formula_report.verified_formulas,
                    "inconsistent": formula_report.inconsistent_formulas
                },
                errors=["Inconsistent formulas detected"] if formula_report.inconsistent_formulas > 0 else [],
                warnings=[]
            )

        elif stage == ValidationStage.STATISTICAL_VALIDATION:
            if not self.statistical_validator:
                return ValidationResult(
                    stage=stage,
                    passed=True,
                    score=1.0,
                    details={"message": "Statistical validation disabled"}
                )

            return self.statistical_validator.validate_statistical_claims(discovery_claim)

        elif stage == ValidationStage.FINAL_ASSESSMENT:
            # This is computed after all other stages
            return ValidationResult(
                stage=stage,
                passed=True,
                score=1.0,
                details={"message": "Final assessment"}
            )

        else:
            raise ValueError(f"Unknown validation stage: {stage}")

    async def validate(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str = "general"
    ) -> PipelineReport:
        """
        Run full validation pipeline on a discovery

        Args:
            discovery_claim: The discovery text to validate
            domains: List of astronomical domains
            discovery_type: Type of discovery

        Returns:
            PipelineReport with comprehensive validation results
        """
        start_time = asyncio.get_event_loop().time()
        logger.info(f"Starting validation pipeline for: {discovery_claim[:100]}...")

        # Define stages to run
        stages = [
            ValidationStage.SEMANTIC_NOVELTY,
        ]

        if self.enable_citation_validation:
            stages.append(ValidationStage.CITATION_VALIDATION)
        if self.enable_formula_validation:
            stages.append(ValidationStage.FORMULA_VALIDATION)
        if self.enable_statistical_validation:
            stages.append(ValidationStage.STATISTICAL_VALIDATION)

        stage_results = []

        if self.parallel_stages:
            # Run independent stages in parallel
            # Semantic novelty must run first
            semantic_result = await self.run_stage(
                ValidationStage.SEMANTIC_NOVELTY,
                discovery_claim,
                domains,
                discovery_type
            )
            stage_results.append(semantic_result)

            # Run other stages in parallel
            other_stages = [s for s in stages if s != ValidationStage.SEMANTIC_NOVELTY]
            if other_stages:
                tasks = [
                    self.run_stage(stage, discovery_claim, domains, discovery_type)
                    for stage in other_stages
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Stage failed with exception: {result}")
                    elif isinstance(result, ValidationResult):
                        stage_results.append(result)
        else:
            # Run stages sequentially
            for stage in stages:
                try:
                    result = await self.run_stage(
                        stage,
                        discovery_claim,
                        domains,
                        discovery_type
                    )
                    stage_results.append(result)
                except Exception as e:
                    logger.error(f"Stage {stage} failed: {e}")

        # Compute final assessment
        # Overall score is weighted average of stage scores
        weights = {
            ValidationStage.SEMANTIC_NOVELTY: 0.5,
            ValidationStage.CITATION_VALIDATION: 0.2,
            ValidationStage.FORMULA_VALIDATION: 0.15,
            ValidationStage.STATISTICAL_VALIDATION: 0.15,
        }

        weighted_score = 0.0
        total_weight = 0.0
        for result in stage_results:
            weight = weights.get(result.stage, 0.1)
            weighted_score += result.score * weight
            total_weight += weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine overall status and confidence level
        all_passed = all(r.passed for r in stage_results)
        critical_errors = any(len(r.errors) > 0 for r in stage_results)

        if all_passed and final_score >= 0.7:
            overall_status = ValidationStatus.VALIDATED
            confidence_level = ConfidenceLevel.VALIDATED
        elif all_passed and final_score >= 0.5:
            overall_status = ValidationStatus.CANDIDATE
            confidence_level = ConfidenceLevel.CANDIDATE
        elif critical_errors:
            # Determine type of error
            if any(r.stage == ValidationStage.CITATION_VALIDATION and not r.passed for r in stage_results):
                overall_status = ValidationStatus.CITATION_ERRORS
            elif any(r.stage == ValidationStage.FORMULA_VALIDATION and not r.passed for r in stage_results):
                overall_status = ValidationStatus.FORMULA_ERRORS
            elif any(r.stage == ValidationStage.STATISTICAL_VALIDATION and not r.passed for r in stage_results):
                overall_status = ValidationStatus.STATISTICAL_ERRORS
            else:
                overall_status = ValidationStatus.CANDIDATE
            confidence_level = ConfidenceLevel.CANDIDATE
        else:
            overall_status = ValidationStatus.CANDIDATE
            confidence_level = ConfidenceLevel.CANDIDATE

        # Get detailed reports from stages
        novelty_report = None
        citation_report = None
        formula_report = None
        statistical_report = None

        for result in stage_results:
            if result.stage == ValidationStage.SEMANTIC_NOVELTY:
                # Re-run to get full report (could optimize this)
                novelty_report = await self.literature_validator.validate_novelty(
                    discovery_claim=discovery_claim,
                    domains=domains,
                    discovery_type=discovery_type
                )

        if self.citation_validator:
            citation_report = await self.citation_validator.validate_citations(discovery_claim)
        if self.formula_validator:
            formula_report = self.formula_validator.validate_formulas(discovery_claim)
        if self.statistical_validator:
            statistical_report = self.statistical_validator.validate_statistical_claims(discovery_claim).details

        # Gather limitations
        limitations = []
        if not self.enable_citation_validation:
            limitations.append("Citation validation disabled")
        if not self.enable_formula_validation:
            limitations.append("Formula validation disabled")
        if not self.enable_statistical_validation:
            limitations.append("Statistical validation disabled")

        total_time = asyncio.get_event_loop().time() - start_time

        report = PipelineReport(
            discovery_claim=discovery_claim,
            discovery_type=discovery_type,
            domains=domains,
            overall_status=overall_status,
            confidence_level=confidence_level,
            stage_results=stage_results,
            novelty_report=novelty_report,
            citation_report=citation_report,
            formula_report=formula_report,
            statistical_report=statistical_report,
            total_validation_time=total_time,
            limitations=limitations
        )

        logger.info(
            f"Validation pipeline complete: status={overall_status.value}, "
            f"confidence={confidence_level.value}, "
            f"score={final_score:.3f}, "
            f"time={total_time:.2f}s"
        )

        return report


def create_validation_pipeline(
    literature_validator: LiteratureValidator,
    enable_citation_validation: bool = True,
    enable_formula_validation: bool = True,
    enable_statistical_validation: bool = True,
    parallel_stages: bool = True
) -> ValidationPipeline:
    """
    Create a ValidationPipeline instance

    Args:
        literature_validator: LiteratureValidator instance
        enable_citation_validation: Enable citation validation stage
        enable_formula_validation: Enable formula validation stage
        enable_statistical_validation: Enable statistical validation stage
        parallel_stages: Run independent stages in parallel

    Returns:
        Configured ValidationPipeline instance
    """
    return ValidationPipeline(
        literature_validator=literature_validator,
        enable_citation_validation=enable_citation_validation,
        enable_formula_validation=enable_formula_validation,
        enable_statistical_validation=enable_statistical_validation,
        parallel_stages=parallel_stages
    )


# Test function
async def test_validation_pipeline():
    """Test the validation pipeline"""
    from .literature_validator import create_literature_validator

    # Create validators
    lit_validator = create_literature_validator()
    pipeline = create_validation_pipeline(lit_validator)

    # Test discovery
    test_discovery = (
        "Molecular clouds exhibit a characteristic filament width of approximately 0.1 parsecs, "
        "as observed in Herschel surveys (Arzoumanian et al., 2011). This width is consistent "
        "across diverse environments with p < 0.001, suggesting a fundamental physical process "
        "regulating filament structure. The relationship between filament width and Jeans length "
        "suggests a connection to turbulent fragmentation (n = 150 clouds)."
    )

    report = await pipeline.validate(
        discovery_claim=test_discovery,
        domains=["ism", "molecular_clouds"],
        discovery_type="pattern_discovery"
    )

    print("\n=== Validation Pipeline Test ===")
    print(f"Discovery: {test_discovery[:100]}...")
    print(f"Overall Status: {report.overall_status.value}")
    print(f"Confidence Level: {report.confidence_level.value}")
    print(f"\nStage Results:")
    for result in report.stage_results:
        print(f"  {result.stage.value}: passed={result.passed}, score={result.score:.3f}")

    print(f"\nDetailed Reports:")
    if report.novelty_report:
        print(f"  Novelty Score: {report.novelty_report.novelty_score:.3f}")
    if report.citation_report:
        print(f"  Citations: {report.citation_report.verified_citations}/{report.citation_report.total_citations} verified")
    if report.formula_report:
        print(f"  Formulas: {report.formula_report.verified_formulas}/{report.formula_report.total_formulas} verified")

    print(f"\nTotal Time: {report.total_validation_time:.2f}s")
    print(f"Limitations: {report.limitations}")


if __name__ == "__main__":
    asyncio.run(test_validation_pipeline())