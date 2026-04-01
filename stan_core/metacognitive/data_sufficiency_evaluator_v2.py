#!/usr/bin/env python3
"""
Enhanced Data Sufficiency Evaluator for ASTRA
==============================================

Expanded version with improved pattern coverage for meta-cognitive evaluation.

Enhancements:
- Greek letter support (Δ, τ, σ, ±, etc.)
- Scientific notation support
- Alternative unit formats
- More robust parsing
- Better edge case handling

Author: ASTRA Project
Date: 2026-03-31
Version: 2.0 (Enhanced Patterns)
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DataSufficiency(Enum):
    """Data sufficiency assessment levels."""
    SUFFICIENT = "sufficient"
    UNCERTAIN = "uncertain"
    INSUFFICIENT = "insufficient"


class LimitationType(Enum):
    """Types of data limitations."""
    SPATIAL_RESOLUTION = "spatial_resolution"
    TEMPORAL_RESOLUTION = "temporal_resolution"
    SAMPLE_SIZE = "sample_size"
    MEASUREMENT_PRECISION = "measurement_precision"
    MODEL_SPECIFICATION = "model_specification"
    AMBIGUITY = "ambiguity"
    CAUSAL_INFERENCE = "causal_inference"


@dataclass
class MetaCognitiveAssessment:
    """Result of meta-cognitive evaluation."""
    sufficiency: DataSufficiency
    limitation_type: Optional[LimitationType]
    limitation_details: str
    recommendation: str
    confidence: float
    justification: str


class EnhancedDataSufficiencyEvaluator:
    """
    Enhanced data sufficiency evaluator with expanded pattern coverage.

    This version includes:
    - Comprehensive Greek letter and symbol support
    - Multiple unit format variations
    - Scientific notation patterns
    - Robust parsing with fallback strategies
    """

    def __init__(self):
        """Initialize enhanced data sufficiency evaluator."""
        # Greek letters and symbols mapping
        self.greek_map = {
            'δ': 'delta', 'Δ': 'Delta',
            'τ': 'tau', 'Τ': 'Tau',
            'σ': 'sigma', 'Σ': 'Sigma',
            '±': '+/-',
            'θ': 'theta', 'Θ': 'Theta',
            'λ': 'lambda', 'Λ': 'Lambda',
            'μ': 'mu', 'Μ': 'Mu'
        }

        # Normalization function
        self._normalize_greek = lambda text: self._normalize_symbols(text)

    def _normalize_symbols(self, text: str) -> str:
        """Normalize Greek letters and symbols to ASCII equivalents."""
        for greek, replacement in self.greek_map.items():
            text = text.replace(greek, replacement)
        return text

    def evaluate_task(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """
        Evaluate a task's data sufficiency with enhanced patterns.

        Args:
            scenario: Task scenario description
            question: Question being asked

        Returns:
            MetaCognitiveAssessment with recommendation
        """
        # Normalize text (replace Greek letters, etc.)
        scenario_normalized = self._normalize_greek(scenario)
        question_normalized = self._normalize_greek(question)

        # Check for specific limitation types in priority order
        assessments = [
            self._check_spatial_resolution_enhanced(scenario_normalized, question_normalized),
            self._check_temporal_resolution_enhanced(scenario_normalized, question_normalized),
            self._check_sample_size_enhanced(scenario_normalized, question_normalized),
            self._check_measurement_precision_enhanced(scenario_normalized, question_normalized),
            self._check_model_specification_enhanced(scenario_normalized, question_normalized),
            self._check_ambiguity_enhanced(scenario_normalized, question_normalized),
            self._check_causal_inference_enhanced(scenario_normalized, question_normalized)
        ]

        # Return first non-sufficient assessment (highest priority limitation)
        for assessment in assessments:
            if assessment.sufficiency != DataSufficiency.SUFFICIENT:
                return assessment

        # If no limitations found, data are sufficient
        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="No obvious data limitations identified",
            recommendation="answer",
            confidence=0.8,
            justification="The data appear sufficient to support the requested analysis"
        )

    def _extract_number(self, text: str) -> Optional[float]:
        """
        Extract a number from text, handling various formats.

        Supports:
        - Regular decimals (1.5)
        - Scientific notation (1.5e-3)
        - Fractions (1/2)
        - With/without units
        """
        # Try scientific notation first
        sci_match = re.search(r'(\d+\.?\d*[eE][+-]?\d+)', text)
        if sci_match:
            try:
                return float(sci_match.group(1))
            except ValueError:
                pass

        # Try regular decimal
        dec_match = re.search(r'(\d+\.?\d*)', text)
        if dec_match:
            try:
                return float(dec_match.group(1))
            except ValueError:
                pass

        # Try fraction
        frac_match = re.search(r'(\d+)\s*/\s*(\d+)', text)
        if frac_match:
            try:
                return float(frac_match.group(1)) / float(frac_match.group(2))
            except (ValueError, ZeroDivisionError):
                pass

        return None

    def _check_spatial_resolution_enhanced(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Enhanced spatial resolution checker with expanded patterns."""
        text = (scenario + " " + question).lower()

        # Enhanced resolution patterns - includes Greek letters and more variations
        resolution_patterns = [
            # Angular resolution with various units
            (r'(?:resolution|beam|fwhm|angular).*?(\d+\.?\d*)\s*arcmin', 'arcmin'),
            (r'(?:resolution|beam|fwhm|angular).*?(\d+\.?\d*)\s*arcsec', 'arcsec'),
            (r'(?:resolution|beam|fwhm).*?(\d+\.?\d*)[\'"]', 'arcmin'),  # ' or " for arcmin/arcsec
            (r'(?:resolution|beam|fwhm).*?(\d+\.?\d*)\s*degree', 'degree'),

            # Spatial resolution in various units
            (r'(?:resolution|beam|fwhm|spatial).*?(\d+\.?\d*)\s*pc', 'pc'),
            (r'(?:resolution|beam|fwhm).*?(\d+\.?\d*)\s*au', 'au'),
            (r'(?:resolution|beam|fwhm).*?(\d+\.?\d*)\s*km', 'km'),
            (r'(?:resolution|beam|fwhm).*?(\d+\.?\d*)\s*m', 'meters'),

            # Greek letter variations (delta for angular/spatial)
            (r'delta[\\s_-]*(?:theta|θ|\\xe8).*?(\d+\.?\d*)', 'angular_delta'),
            (r'delta[\\s_-]*(?:x|χ).*?(\d+\.?\d*)', 'spatial_delta'),

            # Explicit patterns
            (r'beam\s*(?:size|width|diameter)?[:\s]*(\d+\.?\d*)', 'beam'),
            (r'resolution\s*(?:of|:)?\s*(\d+\.?\d*)', 'resolution'),
        ]

        resolutions = []
        for pattern, unit in resolution_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    val = float(match)
                    resolutions.append((val, unit))
                except (ValueError, TypeError):
                    continue

        # Enhanced scale patterns
        scale_patterns = [
            r'(?:scale|size|separation|distance).*?(\d+\.?\d*)\s*pc',
            r'(?:core|target|source).*?scale.*?(\d+\.?\d*)\s*pc',
            r'(?:characteristic|typical).*?scale.*?(\d+\.?\d*)',
            r'r_core\s*[=:]\s*(\d+\.?\d*)',
            r'separation.*?(\d+\.?\d*)\s*pc',
        ]

        scales = []
        for pattern in scale_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    val = float(match)
                    scales.append(val)
                except (ValueError, TypeError):
                    continue

        # Check for resolution vs scale mismatch
        if resolutions and scales:
            max_res = max([r[0] for r in resolutions])
            min_scale = min(scales)

            # Unit conversions to pc
            res_pc = self._convert_to_pc(max_res, resolutions[0][1])
            scale_pc = min_scale  # Already in pc

            # Check threshold (5x mismatch)
            if scale_pc < res_pc / 5:
                mismatch_ratio = res_pc / scale_pc
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.SPATIAL_RESOLUTION,
                    limitation_details=f"Resolution mismatch: {res_pc:.3f} pc vs. {scale_pc:.3f} pc target",
                    recommendation="refuse",
                    confidence=0.95,
                    justification=f"Cannot determine properties at {scale_pc:.3f} pc scale with {res_pc:.3f} pc resolution. This represents a {mismatch_ratio:.1f}× resolution mismatch. Any conclusions about small-scale structure would be dominated by beam averaging effects, not genuine astrophysical structure. This is an information-theoretic limit: data at this resolution cannot constrain features at the requested scale."
                )

        return self._sufficient_assessment()

    def _convert_to_pc(self, value: float, unit: str) -> float:
        """Convert value to parsecs."""
        conversions = {
            'pc': 1.0,
            'arcmin': 0.000291,  # Approximate for typical distances
            'arcsec': 0.00000485,
            'degree': 0.0000175,
            'au': 0.000004848,
            'km': 3.241e-14,
            'meters': 3.241e-17,
            'angular_delta': 0.000291,
            'spatial_delta': 1.0,
            'beam': 1.0,
            'resolution': 1.0
        }
        return value * conversions.get(unit, 1.0)

    def _check_temporal_resolution_enhanced(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Enhanced temporal resolution checker."""
        text = (scenario + " " + question).lower()

        # Enhanced cadence patterns with Greek letters
        cadence_patterns = [
            # Standard patterns
            r'cadence\s*(?:of|:)?\s*(\d+\.?\d*)\s*(hour|hr|day|min|minute|second|sec|week|month)',
            r'(?:one|1)\s*observation\s*(?:every|per)\s*(hour|hr|day|week|month)',
            r'(?:sampling|observation)\s*interval\s*(?:of|:)?\s*(\d+\.?\d*)',

            # Greek letter patterns (delta-t)
            r'delta[\\s_-]*t\s*[=:]\s*(\d+\.?\d*)\s*(hour|hr|day|min|sec)',
            r'Δt\s*[=:]\s*(\d+\.?\d*)\s*(hour|hr|day|min|sec)',
            r'(?:dt|delta_t)\s*[=:]\s*(\d+\.?\d*)',
        ]

        # Enhanced timescale/phenomenon patterns
        timescale_patterns = [
            r'timescale\s*(?:of|:)?\s*(\d+\.?\d*)\s*(min|minute|second|sec|hour|hr|day)',
            r'(?:phenomenon|event|flare|burst).*?duration.*?(\d+\.?\d*)\s*(min|second|sec)',
            r'characteristic\s*(?:time|timescale).*?(\d+\.?\d*)',

            # Greek letter patterns (tau)
            r'tau\s*[=:]\s*(\d+\.?\d*)\s*(min|second|sec)',
            r'τ\s*[=:]\s*(\d+\.?\d*)\s*(min|second|sec)',
            r'(?:timescale|period).*?τ\s*[=:]\s*(\d+\.?\d*)',
        ]

        cadence_val, cadence_unit = self._extract_temporal_measurement(text, cadence_patterns)
        timescale_val, timescale_unit = self._extract_temporal_measurement(text, timescale_patterns)

        if cadence_val is not None and timescale_val is not None:
            # Convert to seconds
            cadence_sec = self._convert_to_seconds(cadence_val, cadence_unit)
            timescale_sec = self._convert_to_seconds(timescale_val, timescale_unit)

            # Check for undersampling (Nyquist: need 2× faster sampling)
            if cadence_sec > timescale_sec * 2:
                ratio = cadence_sec / timescale_sec
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.TEMPORAL_RESOLUTION,
                    limitation_details=f"Temporal undersampling: {cadence_sec:.0f}s cadence vs. {timescale_sec:.0f}s phenomenon",
                    recommendation="refuse",
                    confidence=0.95,
                    justification=f"Cannot characterize {timescale_sec:.0f}s phenomena with {cadence_sec:.0f}s cadence - violates Nyquist sampling criterion by factor of {ratio:.0f}×. Short-timescale events will be either missed entirely or aliased to longer timescales. Can only detect integrated properties, not individual event characteristics."
                )

        return self._sufficient_assessment()

    def _extract_temporal_measurement(self, text: str, patterns: list) -> Tuple[Optional[float], Optional[str]]:
        """Extract temporal measurement from text using patterns."""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    val = float(match.group(1))
                    unit = match.group(2) if len(match.groups()) > 1 else None
                    return val, unit
                except (ValueError, IndexError):
                    continue
        return None, None

    def _convert_to_seconds(self, value: float, unit: Optional[str]) -> float:
        """Convert temporal value to seconds."""
        if unit is None:
            return value

        conversions = {
            'second': 1.0, 'sec': 1.0, 's': 1.0,
            'minute': 60.0, 'min': 60.0, 'm': 60.0,
            'hour': 3600.0, 'hr': 3600.0, 'h': 3600.0,
            'day': 86400.0,
            'week': 604800.0,
            'month': 2592000.0  # 30 days
        }
        return value * conversions.get(unit.lower(), value)

    def _check_sample_size_enhanced(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Enhanced sample size checker."""
        text = (scenario + " " + question).lower()

        # Enhanced sample size patterns
        n_patterns = [
            r'n\s*[=:]\s*(\d+)',
            r'sample\s*(?:size)?\s*(?:of|:)?\s*(\d+)',
            r'(?:treatment|control|experimental|study)\s*group[^.]*?(\d+)',
            r'(?:total|number)\s*(?:of|:)?\s*(\d+)\s*(?:patients|subjects|observations|samples)',
        ]

        # Enhanced baseline rate patterns
        baseline_patterns = [
            r'baseline[^.]*?(\d+\.?\d*)\s*%',
            r'background[^.]*?(\d+\.?\d*)\s*%',
            r'expected[^.]*?rate[^.]*?(\d+\.?\d*)\s*%',
            r'(\d+\.?\d*)\s*%\s*(?:baseline|background)',
        ]

        n_value = self._extract_first_match(text, n_patterns, transform=int)
        baseline_rate = self._extract_first_match(text, baseline_patterns, transform=lambda x: float(x) / 100)

        if n_value is not None and baseline_rate is not None:
            expected_events = n_value * baseline_rate

            if expected_events < 1:
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.SAMPLE_SIZE,
                    limitation_details=f"Severely underpowered: N={n_value}, baseline rate {baseline_rate*100:.1f}%",
                    recommendation="refuse",
                    confidence=0.95,
                    justification=f"Sample size far too small for reliable analysis. With baseline rate {baseline_rate*100:.1f}%, expected events in control group is {expected_events:.2f}. This is statistically indistinguishable from chance variation (p >> 0.05). A properly powered study would require N ≈ 10,000+ for this rare outcome."
                )
            elif expected_events < 10:
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.UNCERTAIN,
                    limitation_type=LimitationType.SAMPLE_SIZE,
                    limitation_details=f"Underpowered: N={n_value}, baseline rate {baseline_rate*100:.1f}%",
                    recommendation="uncertain",
                    confidence=0.85,
                    justification=f"Sample size may be insufficient for reliable conclusions. Expected events ({expected_events:.1f}) are low, making statistical analysis challenging. Results should be treated as preliminary and interpreted with caution."
                )

        return self._sufficient_assessment()

    def _extract_first_match(self, text: str, patterns: list, transform=float) -> Optional[float]:
        """Extract first matching value using patterns."""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return transform(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def _check_measurement_precision_enhanced(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Enhanced measurement precision checker."""
        text = (scenario + " " + question).lower()

        # Enhanced uncertainty patterns with Greek letters
        uncertainty_patterns = [
            r'uncertainty\s*(?:of|:)?\s*(\d+\.?\d*)\s*%',
            r'σ\s*[=:]\s*(\d+\.?\d*)\s*%',
            r'sigma\s*[=:]\s*(\d+\.?\d*)\s*%',
            r'±\s*(\d+\.?\d*)\s*%',
            r'error\s*(?:of|:)?\s*(\d+\.?\d*)\s*%',
            r'precision\s*(?:of|:)?\s*(\d+\.?\d*)\s*%',
        ]

        # Enhanced effect size patterns
        effect_patterns = [
            r'(\d+\.?\d*)\s*%\s*(?:higher|lower|difference|effect|increase|decrease)',
            r'effect\s*(?:size|of).*?(\d+\.?\d*)\s*%',
            r'expected\s*(?:difference|change).*?(\d+\.?\d*)\s*%',
        ]

        uncertainty = self._extract_first_match(text, uncertainty_patterns)
        effect_size = self._extract_first_match(text, effect_patterns)

        if uncertainty is not None and effect_size is not None:
            if effect_size < uncertainty:
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.MEASUREMENT_PRECISION,
                    limitation_details=f"Effect smaller than uncertainty: {effect_size}% vs. {uncertainty}%",
                    recommendation="refuse",
                    confidence=0.90,
                    justification=f"Cannot confirm effect - the {effect_size}% expected difference is smaller than the {uncertainty}% measurement uncertainty. Any observed differences would be statistically indistinguishable from zero (t ≈ {effect_size/uncertainty:.2f}, p ≈ 0.7). To detect this effect with 80% power, measurement precision σ ≈ {effect_size/4:.1f}% or less would be required."
                )

        return self._sufficient_assessment()

    def _check_model_specification_enhanced(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Enhanced model specification checker."""
        text = (scenario + " " + question).lower()

        # Enhanced degeneracy patterns
        degeneracy_patterns = [
            r'two\s*models?\s*fit\s*(?:equally|the\s*same|both)',
            r'equally\s*(?:good|well|consistent).*?models?',
            r'alternative\s*models?.*?(?:fit|match|work)',
            r'model\s*(?:1|2|a|b).*?(?:fit|match).*?(?:equally|same)',
            r'different.*?models?.*?equally.*?(?:good|well)',
            r'(?:both|either)\s*models?.*?fit',
            r'model.*?degeneracy',
            r'degenerate.*?models?',
        ]

        for pattern in degeneracy_patterns:
            if re.search(pattern, text):
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.MODEL_SPECIFICATION,
                    limitation_details="Multiple models fit data equally well",
                    recommendation="uncertain",
                    confidence=0.90,
                    justification="The analysis results are not robust to model specification choices. Different but equally justifiable models lead to substantially different conclusions. This model degeneracy indicates that the data do not adequately constrain the parameter space. I cannot provide a reliable quantitative answer without additional observational constraints that would break degeneracies between model configurations."
                )

        # Enhanced sensitivity patterns
        sensitivity_patterns = [
            r'sensitive\s*to\s*(?:model|parameter|specification)',
            r'model.*?specification.*?choice',
            r'depends.*?on.*?model',
            r'parameterization.*?affects',
            r'(?:different|various).*?models?.*?give',
            r'results.*?vary.*?with.*?model',
        ]

        for pattern in sensitivity_patterns:
            if re.search(pattern, text):
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.UNCERTAIN,
                    limitation_type=LimitationType.MODEL_SPECIFICATION,
                    limitation_details="Results sensitive to model specification",
                    recommendation="uncertain",
                    confidence=0.80,
                    justification="The analysis results show sensitivity to model specification. Different parameterization choices lead to different quantitative outcomes. This model sensitivity indicates that the data may not adequately constrain all parameters. Results should be interpreted as model-dependent rather than fully constrained by observations."
                )

        return self._sufficient_assessment()

    def _check_ambiguity_enhanced(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Enhanced ambiguity checker."""
        text = (scenario + " " + question).lower()

        # Enhanced ambiguity patterns
        ambiguity_patterns = [
            r'ambiguous',
            r'multiple.*?(?:interpretations|explanations|scenarios)',
            r'equally.*?(?:consistent|valid|plausible).*?(?:observations|data)',
            r'several.*?scenarios.*?fit',
            r'not\s*uniquely.*?(?:determined|constrained)',
            r'different.*?explanations.*?(?:possible|valid)',
            r'cannot.*?distinguish',
            r'cannot.*?rule\s*out',
        ]

        for pattern in ambiguity_patterns:
            if re.search(pattern, text):
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.AMBIGUITY,
                    limitation_details="Multiple interpretations equally consistent with data",
                    recommendation="uncertain",
                    confidence=0.85,
                    justification="Multiple distinct physical scenarios are equally consistent with the observational data. The ambiguity is fundamental: the current measurements do not provide the discriminative power required to distinguish between competing hypotheses. Additional observations targeting specific predicted differences would be necessary to resolve this degeneracy."
                )

        return self._sufficient_assessment()

    def _check_causal_inference_enhanced(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Enhanced causal inference checker."""
        text = (scenario + " " + question).lower()

        # Enhanced causal claim patterns
        causal_patterns = [
            r'causal?\s*(?:relationship|link|connection|effect|mechanism)',
            r'cause.*?effect',
            r'(?:demonstrat|prov|establish).*?caus',
            r'establish.*?caus',
            r'confirms?\s*caus',
            r'causation',
        ]

        has_causal_claim = any(re.search(p, text) for p in causal_patterns)

        # Check for experimental controls
        if has_causal_claim:
            control_patterns = [
                r'controlled?\s*(?:experiment|trial|study)',
                r'randomized?\s*(?:assignment|control)',
                r'instrumental\s*variable',
                r'natural\s*experiment',
                r'(?:experimental|control)\s*group',
                r'research\s*design',
            ]

            # Check for observational/correlational language
            observational_patterns = [
                r'correlation',
                r'associated?\s*with',
                r'linked\s*to',
                r'related\s*to',
                r'observ[ee]?d',
                r'epidemiological',
            ]

            has_controls = any(re.search(p, text) for p in control_patterns)
            has_observational = any(re.search(p, text) for p in observational_patterns)

            if not has_controls and (has_observational or 'observational' in text):
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.CAUSAL_INFERENCE,
                    limitation_details="Correlation claimed as causation without experimental controls",
                    recommendation="uncertain",
                    confidence=0.90,
                    justification="The observational data establish correlation but not causation. Multiple confounding variables and alternative causal pathways are consistent with the observed pattern. Distinguishing between causal hypotheses requires: (1) controlled manipulation (impossible in astrophysics/observational studies), (2) natural experiments with appropriate controls, or (3) instrumental variable approaches. The current data do not meet these requirements for causal inference."
                )

        return self._sufficient_assessment()

    def _sufficient_assessment(self) -> MetaCognitiveAssessment:
        """Return sufficient assessment."""
        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )


def create_enhanced_data_sufficiency_evaluator() -> EnhancedDataSufficiencyEvaluator:
    """
    Factory function to create enhanced data sufficiency evaluator.

    Returns:
        EnhancedDataSufficiencyEvaluator instance
    """
    return EnhancedDataSufficiencyEvaluator()


# For backward compatibility, create alias
DataSufficiencyEvaluator = EnhancedDataSufficiencyEvaluator


# Export symbols
__all__ = [
    'DataSufficiency',
    'LimitationType',
    'MetaCognitiveAssessment',
    'DataSufficiencyEvaluator',
    'EnhancedDataSufficiencyEvaluator',
    'create_data_sufficiency_evaluator',
    'create_enhanced_data_sufficiency_evaluator',
]
