"""
ASTRA Pipeline Validation Module
Implements rigorous validation gates to prevent false discoveries and ensure scientific integrity.

Based on peer review feedback identifying systemic architectural flaws:
- Citation resolution failures
- Non-traceable computation
- Trivial validation targets
- Ungoverned agreement criteria
- Unfalsifiable self-generated metrics
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation failures."""
    CRITICAL = "CRITICAL"  # Blocks output completely
    MAJOR = "MAJOR"  # Should block but can be overridden
    MINOR = "MINOR"  # Warning only


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    severity: ValidationSeverity
    message: str
    details: Optional[Dict[str, Any]] = None


class CitationValidator:
    """Validates that all citations resolve to bibliography entries."""

    def __init__(self, tex_content: str, bib_content: str):
        self.tex_content = tex_content
        self.bib_content = bib_content
        self.cite_pattern = re.compile(r'\\cite\{([^}]+)\}')
        self.bib_pattern = re.compile(r'@[^{]+\{([^,]+),')

    def validate(self) -> ValidationResult:
        """
        CRITICAL GATE: All citations must resolve to bibliography entries.

        This is a hard validation gate - output cannot be considered "complete"
        if any citations are unresolved.
        """
        cite_keys = self._extract_cite_keys()
        bib_keys = self._extract_bib_keys()

        unresolved = cite_keys - set(bib_keys)

        if unresolved:
            return ValidationResult(
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Unresolved citations found: {unresolved}",
                details={
                    "unresolved_keys": list(unresolved),
                    "total_citations": len(cite_keys),
                    "resolved_citations": len(cite_keys) - len(unresolved)
                }
            )

        return ValidationResult(
            passed=True,
            severity=ValidationSeverity.CRITICAL,
            message=f"All {len(cite_keys)} citations resolved successfully",
            details={"resolved_citations": len(cite_keys)}
        )

    def _extract_cite_keys(self) -> set:
        """Extract all citation keys from LaTeX content."""
        matches = self.cite_pattern.findall(self.tex_content)
        # Split multiple citations like \cite{key1,key2}
        keys = set()
        for match in matches:
            keys.update([k.strip() for k in match.split(',')])
        return keys

    def _extract_bib_keys(self) -> List[str]:
        """Extract all bibliography keys from .bib file."""
        return self.bib_pattern.findall(self.bib_content)


class DerivationValidator:
    """Validates that numeric results have shown derivations."""

    def __init__(self, results_section: str):
        self.results_section = results_section
        self.number_pattern = re.compile(r'\b\d+\.?\d*\s*(?:Gyr|Myr|K|M_\odot|Z_\odot|%)\b')

    def validate(self) -> ValidationResult:
        """
        CRITICAL GATE: Every numeric result must have derivation shown.

        Required format for each result:
        1. Formula/equation used
        2. Values substituted into formula
        3. Final result
        """
        numeric_results = self._extract_numeric_results()

        missing_derivations = []
        for result in numeric_results:
            if not self._has_derivation(result):
                missing_derivations.append(result)

        if missing_derivations:
            return ValidationResult(
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"{len(missing_derivations)} numeric results lack derivation",
                details={"missing_derivations": missing_derivations}
            )

        return ValidationResult(
            passed=True,
            severity=ValidationSeverity.CRITICAL,
            message=f"All {len(numeric_results)} numeric results have derivations shown",
            details={"validated_results": len(numeric_results)}
        )

    def _extract_numeric_results(self) -> List[str]:
        """Extract numeric results from text."""
        return self.number_pattern.findall(self.results_section)

    def _has_derivation(self, result: str) -> bool:
        """Check if result has derivation shown nearby."""
        # Look for formula patterns, substitution markers, calculation indicators
        derivation_indicators = [
            r'formula',
            r'equation',
            r'=.*=',  # Substitution pattern like "t = 10 Gyr × (1.0)^-2.5"
            r'substitut',
            r'calculat',
            r'deriv'
        ]

        context = self._get_result_context(result)
        for indicator in derivation_indicators:
            if re.search(indicator, context, re.IGNORECASE):
                return True

        return False

    def _get_result_context(self, result: str) -> str:
        """Get text context around a result."""
        # Find result in text and extract surrounding paragraph
        lines = self.results_section.split('\n')
        for i, line in enumerate(lines):
            if result in line:
                # Get surrounding lines (before and after)
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                return '\n'.join(lines[start:end])
        return ""


class AgreementValidator:
    """Validates agreement against explicit tolerance thresholds."""

    # Default tolerance thresholds (can be overridden)
    DEFAULT_TOLERANCES = {
        "mass": 0.01,  # 1%
        "metallicity": 0.05,  # 5%
        "lifetime": 0.10,  # 10%
        "temperature": 0.05,  # 5%
        "pre_ms_fraction": 0.50,  # 50% (factor of 2)
    }

    def __init__(self, predicted_values: Dict[str, float],
                 expected_values: Dict[str, float],
                 tolerances: Optional[Dict[str, float]] = None):
        self.predicted = predicted_values
        self.expected = expected_values
        self.tolerances = tolerances or self.DEFAULT_TOLERANCES

    def validate(self) -> ValidationResult:
        """
        MAJOR GATE: Agreement must be assessed against explicit tolerances.

        All "match"/"error" assignments must use quantitative criteria,
        not qualitative judgment.
        """
        results = []
        failed = []

        for parameter in self.expected.keys():
            if parameter not in self.predicted:
                logger.warning(f"Parameter {parameter} not in predicted values")
                continue

            relative_error = self._calculate_relative_error(
                self.predicted[parameter],
                self.expected[parameter]
            )

            tolerance = self.tolerances.get(parameter, 0.10)
            assessment = self._assess_agreement(relative_error, tolerance)

            results.append({
                "parameter": parameter,
                "predicted": self.predicted[parameter],
                "expected": self.expected[parameter],
                "relative_error": relative_error,
                "tolerance": tolerance,
                "assessment": assessment
            })

            if assessment == "× Error":
                failed.append(parameter)

        if failed:
            return ValidationResult(
                passed=False,
                severity=ValidationSeverity.MAJOR,
                message=f"Parameters failed agreement test: {failed}",
                details={
                    "failed_parameters": failed,
                    "all_results": results
                }
            )

        return ValidationResult(
            passed=True,
            severity=ValidationSeverity.MAJOR,
            message=f"All parameters passed agreement test",
            details={"all_results": results}
        )

    def _calculate_relative_error(self, predicted: float, expected: float) -> float:
        """Calculate relative error as percentage."""
        if expected == 0:
            return abs(predicted)  # Absolute error for zero expected
        return abs(predicted - expected) / abs(expected)

    def _assess_agreement(self, relative_error: float, tolerance: float) -> str:
        """Assess agreement against tolerance thresholds."""
        if relative_error < tolerance * 0.5:
            return "✓ Excellent Match"
        elif relative_error < tolerance:
            return "✓ Acceptable Match"
        elif relative_error < tolerance * 2:
            return "~ Loose Match"
        else:
            return "× Error"


class NonTrivialValidationValidator:
    """Validates that non-trivial test cases are included."""

    def __init__(self, validation_cases: List[Dict[str, Any]]):
        self.validation_cases = validation_cases

    def validate(self) -> ValidationResult:
        """
        MAJOR GATE: Validation must include non-trivial cases.

        Testing against calibration points (M = 1.0 M☉) is insufficient.
        At least one held-out case is required.
        """
        non_trivial_cases = [
            case for case in self.validation_cases
            if self._is_non_trivial(case)
        ]

        if not non_trivial_cases:
            return ValidationResult(
                passed=False,
                severity=ValidationSeverity.MAJOR,
                message="No non-trivial validation cases found - only calibration cases",
                details={
                    "total_cases": len(self.validation_cases),
                    "calibration_cases": len(self.validation_cases)
                }
            )

        return ValidationResult(
            passed=True,
            severity=ValidationSeverity.MAJOR,
            message=f"Found {len(non_trivial_cases)} non-trivial validation cases",
            details={
                "total_cases": len(self.validation_cases),
                "non_trivial_cases": len(non_trivial_cases)
            }
        )

    def _is_non_trivial(self, case: Dict[str, Any]) -> bool:
        """Determine if case is non-trivial (not a calibration point)."""
        # A case is trivial if it matches exact calibration values
        mass = case.get("M", 0)
        metallicity = case.get("Z", 0)

        # Solar calibration point
        if abs(mass - 1.0) < 0.01 and abs(metallicity - 1.0) < 0.01:
            return False

        return True


class MetricSpecificationValidator:
    """Validates that meta-metrics are either retired or fully specified."""

    def __init__(self, content: str):
        self.content = content

    def validate(self) -> ValidationResult:
        """
        MAJOR GATE: Self-generated metrics must be specified or retired.

        Options:
        A) No self-generated similarity/confidence/novelty scores
        B) Full methodology specified and independently checkable
        """
        # Check for self-generated metric claims
        metric_claims = self._find_metric_claims()

        if not metric_claims:
            # Option A: No metrics - this is fine
            return ValidationResult(
                passed=True,
                severity=ValidationSeverity.MAJOR,
                message="No self-generated metrics found (Option A - retired)"
            )

        # Option B: Check if methodology is specified
        methodology_specified = self._check_methodology_specified()

        if not methodology_specified:
            return ValidationResult(
                passed=False,
                severity=ValidationSeverity.MAJOR,
                message="Self-generated metrics found without methodology specification",
                details={
                    "metric_claims": metric_claims,
                    "required": "Either retire metrics or specify methodology"
                }
            )

        return ValidationResult(
            passed=True,
            severity=ValidationSeverity.MAJOR,
            message=f"Self-generated metrics have methodology specified (Option B)",
            details={"metric_claims": metric_claims}
        )

    def _find_metric_claims(self) -> List[str]:
        """Find claims about similarity, confidence, novelty, etc."""
        metric_patterns = [
            r'(\d+%\s+similarity)',
            r'(similarity\s+of\s+~?\d+%)',
            r'(confidence\s+score)',
            r'(novelty\s+score)',
            r'(rejection\s+threshold)',
            r'(EUREKA\s+score)',
        ]

        claims = []
        for pattern in metric_patterns:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            claims.extend(matches)

        return claims

    def _check_methodology_specified(self) -> bool:
        """Check if methodology for metrics is specified."""
        methodology_indicators = [
            r'methodology\s+(?:specified|described|explained)',
            r'similarity\s+calculation',
            r'algorithm',
            r'feature\s+extraction',
            r'distance\s+metric',
            r'normalization',
        ]

        for indicator in methodology_indicators:
            if re.search(indicator, self.content, re.IGNORECASE):
                return True

        return False


class PipelineValidator:
    """Main validator that runs all validation gates."""

    def __init__(self, tex_content: str, bib_content: str,
                 results_section: str, validation_cases: List[Dict]):
        self.tex_content = tex_content
        self.bib_content = bib_content
        self.results_section = results_section
        self.validation_cases = validation_cases

        self.validators = [
            CitationValidator(tex_content, bib_content),
            DerivationValidator(results_section),
            NonTrivialValidationValidator(validation_cases),
            MetricSpecificationValidator(tex_content)
        ]

    def validate_all(self) -> Tuple[bool, List[ValidationResult]]:
        """
        Run all validation gates.

        CRITICAL failures block output completely.
        MAJOR failures should block but can be overridden.
        MINOR failures are warnings only.
        """
        results = []
        all_passed = True

        logger.info("Starting ASTRA pipeline validation...")

        for validator in self.validators:
            result = validator.validate()
            results.append(result)

            if not result.passed:
                logger.error(f"Validation failed: {result.message}")
                if result.severity == ValidationSeverity.CRITICAL:
                    all_passed = False
            else:
                logger.info(f"Validation passed: {result.message}")

        return all_passed, results

    def get_validation_report(self) -> str:
        """Generate human-readable validation report."""
        passed, results = self.validate_all()

        report = ["=" * 80]
        report.append("ASTRA Pipeline Validation Report")
        report.append("=" * 80)

        if passed:
            report.append("✅ ALL VALIDATIONS PASSED")
        else:
            report.append("❌ VALIDATION FAILED - Output blocked")

        report.append("\nDetailed Results:")
        report.append("-" * 80)

        for i, result in enumerate(results, 1):
            status = "✅ PASS" if result.passed else "❌ FAIL"
            severity = f"[{result.severity.value}]"
            report.append(f"{i}. {status} {severity}: {result.message}")

            if result.details:
                for key, value in result.details.items():
                    report.append(f"   - {key}: {value}")

        report.append("=" * 80)

        return "\n".join(report)


def validate_discovery_pipeline(
    tex_content: str,
    bib_content: str,
    results_section: str,
    validation_cases: List[Dict],
    predicted_values: Optional[Dict[str, float]] = None,
    expected_values: Optional[Dict[str, float]] = None
) -> Tuple[bool, str]:
    """
    Main entry point for pipeline validation.

    Args:
        tex_content: Full LaTeX document content
        bib_content: Bibliography .bib file content
        results_section: Results section of paper
        validation_cases: List of validation test cases
        predicted_values: System's predicted values (for agreement validation)
        expected_values: Expected literature values (for agreement validation)

    Returns:
        Tuple of (passed: bool, report: str)
    """
    validator = PipelineValidator(tex_content, bib_content, results_section, validation_cases)

    # Run standard validations
    passed, results = validator.validate_all()

    # Optional: Run agreement validation if values provided
    if predicted_values and expected_values:
        agreement_validator = AgreementValidator(predicted_values, expected_values)
        agreement_result = agreement_validator.validate()
        results.append(agreement_result)

        if not agreement_result.passed:
            passed = False

    # Generate report
    report = validator.get_validation_report()

    return passed, report


# Example usage
if __name__ == "__main__":
    # Example validation (would be called by pipeline)
    tex = r"\cite{test1} and \cite{test2}"
    bib = r"@article{test1, title={Test}} @article{test2, title={Test}}"
    results = "The lifetime is 10 Gyr"
    cases = [{"M": 1.0, "Z": 1.0}]

    passed, report = validate_discovery_pipeline(tex, bib, results, cases)
    print(report)
