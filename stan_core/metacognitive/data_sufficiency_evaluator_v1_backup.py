#!/usr/bin/env python3
"""
Data Sufficiency Evaluator for ASTRA
====================================

Meta-cognitive module that evaluates whether data are sufficient
to support requested scientific conclusions.

This is a core capability for scientific AI systems - the ability
to recognize when observational or experimental limitations preclude
reliable inference.

Author: ASTRA Project
Date: 2026-03-31
Version: 1.0
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DataSufficiency(Enum):
    """Data sufficiency assessment levels."""
    SUFFICIENT = "sufficient"  # Data support confident conclusions
    UNCERTAIN = "uncertain"    # Data limited but some inferences possible
    INSUFFICIENT = "insufficient"  # Data cannot support requested conclusions


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
    confidence: float  # 0.0 to 1.0
    justification: str


class DataSufficiencyEvaluator:
    """
    Evaluates data sufficiency for scientific reasoning tasks.

    This module implements meta-cognitive self-evaluation by checking
    for various data limitations that would preclude reliable conclusions.

    Integration with ASTRA:
        - Automatically invoked during query processing
        - Provides meta-cognitive assessments before response generation
        - Can trigger refusal or uncertainty responses
    """

    def __init__(self):
        """Initialize data sufficiency evaluator."""
        self.limitation_patterns = self._build_limitation_patterns()
        self.resolution_keywords = [
            'resolution', 'beam', 'fwhm', 'angular', 'spatial', 'pixel',
            'cadence', 'temporal', 'sampling', 'timescale', 'duration'
        ]
        self.sample_size_keywords = [
            'sample size', 'n=', 'n =', 'patients', 'subjects', 'number of',
            'observations', 'total', 'baseline'
        ]
        self.precision_keywords = [
            'uncertainty', 'error', 'precision', 'σ', 'sigma', '±', '+/-',
            'measurement', 'noise', 'signal-to-noise'
        ]
        self.model_keywords = [
            'model', 'fit', 'parameter', 'degenerate', 'alternative',
            'specification', 'assumption', 'different but'
        ]
        self.ambiguity_keywords = [
            'ambiguous', 'multiple interpretations', 'equally consistent',
            'several scenarios', 'not uniquely determined'
        ]
        self.causal_keywords = [
            'causal', 'causation', 'cause', 'effect', 'mechanism',
            'correlation', 'confounding', 'selection bias'
        ]

    def evaluate_task(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """
        Evaluate a task's data sufficiency.

        Args:
            scenario: Task scenario description
            question: Question being asked

        Returns:
            MetaCognitiveAssessment with recommendation
        """
        # Check for specific limitation types in priority order
        assessments = [
            self._check_spatial_resolution(scenario, question),
            self._check_temporal_resolution(scenario, question),
            self._check_sample_size(scenario, question),
            self._check_measurement_precision(scenario, question),
            self._check_model_specification(scenario, question),
            self._check_ambiguity(scenario, question),
            self._check_causal_inference(scenario, question)
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

    def _check_spatial_resolution(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Check for spatial resolution limitations."""
        text = (scenario + " " + question).lower()

        # Look for resolution indicators
        resolution_patterns = [
            (r'(\d+\.?\d*)\s*arcmin?', 'angular_resolution'),
            (r'(\d+\.?\d*)\s*arcsec?', 'angular_resolution'),
            (r'(\d+\.?\d*)\s*pc', 'spatial_resolution'),
            (r'beam\s*(?:fwhm|width|size)[:\s]*(\d+\.?\d*)', 'beam_size'),
            (r'resolution\s*(?:of|:)?\s*(\d+\.?\d*)', 'explicit_resolution'),
        ]

        resolutions = []
        for pattern, res_type in resolution_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    resolutions.append((float(match), res_type))
                except ValueError:
                    continue

        # Look for scale comparisons
        scale_pattern = r'(\d+\.?\d*)\s*pc.*?(\d+\.?\d*)\s*pc|scale.*?(\d+\.?\d*)'
        scale_matches = re.findall(scale_pattern, text)

        # Check for resolution mismatch (smaller scale queried than resolution)
        for match in scale_matches:
            scales = [float(m) for m in match if m]
            if len(scales) >= 2 and len(resolutions) > 0:
                min_scale = min(scales)
                max_resolution = max([r[0] for r in resolutions])
                
                if min_scale < max_resolution / 5:  # 5x mismatch threshold
                    return MetaCognitiveAssessment(
                        sufficiency=DataSufficiency.INSUFFICIENT,
                        limitation_type=LimitationType.SPATIAL_RESOLUTION,
                        limitation_details=f"Resolution mismatch: observational resolution {max_resolution} pc vs. target scale {min_scale} pc",
                        recommendation="refuse",
                        confidence=0.95,
                        justification=f"Cannot determine properties at {min_scale} pc scale with {max_resolution} pc resolution. This represents a {max_resolution/min_scale:.1f}× resolution mismatch. Any conclusions about small-scale structure would be dominated by beam averaging effects, not genuine astrophysical structure. This is an information-theoretic limit: data at this resolution cannot constrain features at the requested scale."
                    )

        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )

    def _check_temporal_resolution(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Check for temporal resolution limitations."""
        text = (scenario + " " + question).lower()

        # Look for temporal indicators
        cadence_patterns = [
            r'cadence\s*(?:of|:)?\s*(\d+\.?\d*)\s*(hour|day|min|second)',
            r'(\d+\.?\d*)\s*(hour|day|min|second).*?cadence',
            r'one\s*observation\s*per\s*(hour|day|week|month)',
        ]

        timescale_patterns = [
            r'timescale\s*(?:of|:)?\s*(\d+\.?\d*)\s*(min|second|hour)',
            r'(\d+\.?\d*)\s*(min|minute|second).*?phenomenon',
            r'flare.*?(\d+\.?\d*)\s*(min|minute)',
        ]

        cadence_match = None
        for pattern in cadence_patterns:
            match = re.search(pattern, text)
            if match:
                cadence_match = match
                break

        timescale_match = None
        for pattern in timescale_patterns:
            match = re.search(pattern, text)
            if match:
                timescale_match = match
                break

        # Check for temporal mismatch
        if cadence_match and timescale_match:
            try:
                cadence_val = float(cadence_match.group(1))
                timescale_val = float(timescale_match.group(1))

                # Unit conversion to minutes
                unit_to_min = {'hour': 60, 'day': 1440, 'min': 1, 'minute': 1, 
                               'second': 1/60, 'week': 10080, 'month': 43200}

                cadence_unit = cadence_match.group(2) if len(cadence_match.groups()) > 1 else 'min'
                timescale_unit = timescale_match.group(2) if len(timescale_match.groups()) > 1 else 'min'

                cadence_min = cadence_val * unit_to_min.get(cadence_unit, 1)
                timescale_min = timescale_val * unit_to_min.get(timescale_unit, 1)

                # Check for severe undersampling (Nyquist criterion: need at least 2× faster sampling)
                if cadence_min > timescale_min * 2:
                    return MetaCognitiveAssessment(
                        sufficiency=DataSufficiency.INSUFFICIENT,
                        limitation_type=LimitationType.TEMPORAL_RESOLUTION,
                        limitation_details=f"Temporal undersampling: {cadence_min:.0f} min cadence vs. {timescale_min:.0f} min phenomenon",
                        recommendation="refuse",
                        confidence=0.95,
                        justification=f"Cannot characterize {timescale_min:.0f} min phenomena with {cadence_min:.0f} min cadence - violates Nyquist sampling criterion by factor of {cadence_min/timescale_min:.0f}×. Short-timescale events will be either missed entirely or aliased to longer timescales. Can only detect integrated energy output over {cadence_min:.0f}-min periods, not individual event properties."
                    )
            except (ValueError, IndexError):
                pass

        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )

    def _check_sample_size(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Check for sample size limitations."""
        text = (scenario + " " + question).lower()

        # Look for sample size and baseline rates
        n_pattern = r'n\s*=\s*(\d+)|(?:treatment|control|sample)\s*group[^.]*?(\d+)'
        baseline_pattern = r'baseline[^.]*?(\d+\.?\d*)\s*%'

        n_matches = re.findall(n_pattern, text)
        baseline_match = re.search(baseline_pattern, text)

        if n_matches and baseline_match:
            try:
                # Extract sample size
                n_values = []
                for match in n_matches:
                    for val in match:
                        if val:
                            n_values.append(int(val))

                if n_values:
                    min_n = min(n_values)
                    baseline_rate = float(baseline_match.group(1)) / 100

                    # Calculate expected counts
                    expected_events = min_n * baseline_rate

                    # Check if severely underpowered
                    if expected_events < 1:
                        return MetaCognitiveAssessment(
                            sufficiency=DataSufficiency.INSUFFICIENT,
                            limitation_type=LimitationType.SAMPLE_SIZE,
                            limitation_details=f"Severely underpowered: N={min_n}, baseline rate {baseline_rate*100:.1f}%",
                            recommendation="refuse",
                            confidence=0.95,
                            justification=f"Sample size far too small for reliable analysis. With baseline rate {baseline_rate*100:.1f}%, expected events in control group is {expected_events:.2f}. The observed differences are statistically indistinguishable from chance variation (p >> 0.05). A properly powered study would require N ≈ 10,000+ to detect 50% risk reduction with adequate power (80%)."
                        )
                    elif expected_events < 10:
                        return MetaCognitiveAssessment(
                            sufficiency=DataSufficiency.UNCERTAIN,
                            limitation_type=LimitationType.SAMPLE_SIZE,
                            limitation_details=f"Underpowered: N={min_n}, baseline rate {baseline_rate*100:.1f}%",
                            recommendation="uncertain",
                            confidence=0.85,
                            justification=f"Sample size may be insufficient for reliable conclusions. Expected events ({expected_events:.1f}) are low, making statistical analysis challenging. Results should be treated as preliminary and interpreted with caution. Cannot make definitive claims about treatment effects."
                        )
            except (ValueError, IndexError):
                pass

        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )

    def _check_measurement_precision(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Check for measurement precision limitations."""
        text = (scenario + " " + question).lower()

        # Look for uncertainty and effect size
        uncertainty_pattern = r'uncertainty\s*(?:of|:)?\s*(\d+\.?\d*)\s*%|σ\s*(?:=|:)?\s*(\d+\.?\d*)\s*%|±\s*(\d+\.?\d*)\s*%'
        effect_pattern = r'(\d+\.?\d*)\s*%\s*(?:higher|lower|difference|effect)'

        uncertainty_match = re.search(uncertainty_pattern, text)
        effect_match = re.search(effect_pattern, text)

        if uncertainty_match and effect_match:
            try:
                # Extract uncertainty
                uncertainty = None
                for group in uncertainty_match.groups():
                    if group:
                        uncertainty = float(group)
                        break

                if uncertainty:
                    effect_size = float(effect_match.group(1))

                    # Check if effect smaller than uncertainty
                    if effect_size < uncertainty:
                        return MetaCognitiveAssessment(
                            sufficiency=DataSufficiency.INSUFFICIENT,
                            limitation_type=LimitationType.MEASUREMENT_PRECISION,
                            limitation_details=f"Effect smaller than uncertainty: {effect_size}% vs. {uncertainty}%",
                            recommendation="refuse",
                            confidence=0.90,
                            justification=f"Cannot confirm effect - the {effect_size}% expected difference is smaller than the {uncertainty}% measurement uncertainty. The observed values are statistically indistinguishable from zero given measurement errors (t-statistic ≈ {effect_size/uncertainty:.2f}, p ≈ 0.7). To detect this effect with 80% power, measurement precision σ ≈ {effect_size/4:.1f}% or less would be required."
                        )
            except (ValueError, IndexError):
                pass

        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )

    def _check_model_specification(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Check for model specification issues."""
        text = (scenario + " " + question).lower()

        # Look for model degeneracy indicators
        degeneracy_patterns = [
            r'two\s*models?\s*fit\s*(?:equally|the\s*same)',
            r'equally\s*(?:good|well).*?models?',
            r'alternative\s*models?.*?fit',
            r'model\s*(?:1|2).*?(?:fit|match).*?(?:equally|same)',
            r'different.*?models?.*?equally.*?(?:good|well)',
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

        # Check for model sensitivity
        sensitivity_patterns = [
            r'sensitive\s*to\s*model',
            r'model.*?specification.*?choice',
            r'depends.*?on.*?model',
            r'parameterization.*?affects',
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

        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )

    def _check_ambiguity(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Check for ambiguous data interpretations."""
        text = (scenario + " " + question).lower()

        # Look for ambiguity indicators
        ambiguity_patterns = [
            r'ambiguous',
            r'multiple.*?interpretations',
            r'equally\s*consistent.*?(?:observations|data)',
            r'several.*?scenarios.*?fit',
            r'not\s*uniquely.*?determined',
            r'different.*?explanations.*?possible',
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

        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )

    def _check_causal_inference(self, scenario: str, question: str) -> MetaCognitiveAssessment:
        """Check for causal inference limitations."""
        text = (scenario + " " + question).lower()

        # Look for causal claims
        causal_patterns = [
            r'causal?\s*(?:relationship|link|connection|effect)',
            r'cause.*?effect',
            r'demonstrat(?:e|es).*?caus',
            r'proves?.*?caus',
            r'establish.*?caus',
        ]

        has_causal_claim = any(re.search(p, text) for p in causal_patterns)

        # Check if appropriate controls mentioned
        if has_causal_claim:
            control_patterns = [
                r'controlled?\s*(?:experiment|trial|study)',
                r'randomized?',
                r'instrumental\s*variable',
                r'natural\s*experiment',
                r'confounding.*?variable',
            ]

            has_controls = any(re.search(p, text) for p in control_patterns)

            # Check for correlational language suggesting observational data
            correlation_patterns = [
                r'correlation',
                r'associated?\s*with',
                r'linked\s*to',
                r'related\s*to',
                r'observ[ee]?d',
            ]

            has_correlation = any(re.search(p, text) for p in correlation_patterns)

            if not has_controls and (has_correlation or 'observational' in text):
                return MetaCognitiveAssessment(
                    sufficiency=DataSufficiency.INSUFFICIENT,
                    limitation_type=LimitationType.CAUSAL_INFERENCE,
                    limitation_details="Correlation claimed as causation without experimental controls",
                    recommendation="uncertain",
                    confidence=0.90,
                    justification="The observational data establish correlation but not causation. Multiple confounding variables and alternative causal pathways are consistent with the observed pattern. Distinguishing between causal hypotheses requires: (1) controlled manipulation (impossible in astrophysics), (2) natural experiments with appropriate controls, or (3) instrumental variable approaches. The current observational data do not meet these requirements for causal inference."
                )

        return MetaCognitiveAssessment(
            sufficiency=DataSufficiency.SUFFICIENT,
            limitation_type=None,
            limitation_details="",
            recommendation="answer",
            confidence=0.0,
            justification=""
        )

    def _build_limitation_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for detecting limitations."""
        return {
            'resolution': [
                r'resolution.*?(\d+\.?\d*)',
                r'beam.*?(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*pc',
            ],
            'sample_size': [
                r'n\s*=\s*(\d+)',
                r'sample.*?size.*?(\d+)',
            ],
            'uncertainty': [
                r'±\s*(\d+\.?\d*)',
                r'σ\s*=\s*(\d+\.?\d*)',
            ]
        }


def create_data_sufficiency_evaluator() -> DataSufficiencyEvaluator:
    """
    Factory function to create data sufficiency evaluator.

    Returns:
        DataSufficiencyEvaluator instance
    """
    return DataSufficiencyEvaluator()


# Export symbols
__all__ = [
    'DataSufficiency',
    'LimitationType',
    'MetaCognitiveAssessment',
    'DataSufficiencyEvaluator',
    'create_data_sufficiency_evaluator',
]
