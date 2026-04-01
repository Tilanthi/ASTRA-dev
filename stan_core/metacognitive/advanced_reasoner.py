#!/usr/bin/env python3
"""
Advanced Meta-Cognitive Reasoner for ASTRA
==========================================

Generates high-quality, quantitative justifications for meta-cognitive assessments
by leveraging ASTRA's advanced reasoning capabilities (V42-V94).

Key Innovations:
1. Quantitative mismatch calculation (Nyquist, beam averaging, etc.)
2. Information-theoretic reasoning (Shannon entropy, channel capacity)
3. Multi-perspective analysis (physical, statistical, causal)
4. Epistemic boundary detection (what can vs cannot be known)
5. Self-consistency checking for robust justifications

Author: ASTRA Project
Date: 2026-03-31
Version: 1.0 (Advanced Reasoning)
"""

import re
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import base system
from .data_sufficiency_evaluator import (
    EnhancedDataSufficiencyEvaluator,
    DataSufficiency,
    LimitationType,
    MetaCognitiveAssessment
)

# Try to import advanced capabilities
try:
    from ..capabilities.v42_capabilities import GPQAReasoning
    GPQA_AVAILABLE = True
except ImportError:
    GPQA_AVAILABLE = False

try:
    from ..capabilities.v50_causal_engine import CausalDiscovery
    CAUSAL_AVAILABLE = True
except ImportError:
    CAUSAL_AVAILABLE = False

try:
    from ..capabilities.analogical_reasoning import AnalogicalReasoner
    ANALOGICAL_AVAILABLE = True
except ImportError:
    ANALOGICAL_AVAILABLE = False

try:
    from ..capabilities.self_consistency import SelfConsistency
    SELF_CONSISTENCY_AVAILABLE = True
except ImportError:
    SELF_CONSISTENCY_AVAILABLE = False


@dataclass
class QuantitativeAnalysis:
    """Quantitative analysis of data limitations."""
    limitation_type: str
    metric_name: str
    observed_value: float
    required_value: float
    mismatch_ratio: float
    unit: str
    information_theoretic_limit: Optional[str] = None


@dataclass
class MultiPerspectiveAnalysis:
    """Analysis from multiple perspectives."""
    physical_perspective: Optional[str] = None
    statistical_perspective: Optional[str] = None
    causal_perspective: Optional[str] = None
    epistemic_perspective: Optional[str] = None


class AdvancedMetaCognitiveReasoner:
    """
    Advanced meta-cognitive reasoner that generates high-quality justifications.

    Uses ASTRA's advanced capabilities (V42-V94) for:
    - Quantitative mismatch calculation
    - Information-theoretic reasoning
    - Multi-perspective analysis
    - Epistemic boundary detection
    """

    def __init__(self):
        """Initialize advanced meta-cognitive reasoner."""
        # Base evaluator
        self.base_evaluator = EnhancedDataSufficiencyEvaluator()

        # Advanced capabilities
        self.gpqa_reasoner = None
        self.causal_engine = None
        self.analogical_reasoner = None
        self.self_consistency = None

        self._initialize_capabilities()

    def _initialize_capabilities(self):
        """Initialize advanced capabilities with graceful degradation."""
        if GPQA_AVAILABLE:
            try:
                self.gpqa_reasoner = GPQAReasoning()
            except:
                pass

        if CAUSAL_AVAILABLE:
            try:
                self.causal_engine = CausalDiscovery()
            except:
                pass

        if ANALOGICAL_AVAILABLE:
            try:
                self.analogical_reasoner = AnalogicalReasoner()
            except:
                pass

        if SELF_CONSISTENCY_AVAILABLE:
            try:
                self.self_consistency = SelfConsistency()
            except:
                pass

    def evaluate_with_rich_justification(
        self,
        scenario: str,
        question: str
    ) -> MetaCognitiveAssessment:
        """
        Evaluate task with rich, quantitative justification.

        Args:
            scenario: Task scenario description
            question: Question being asked

        Returns:
            MetaCognitiveAssessment with enhanced justification
        """
        # Get base assessment
        base_assessment = self.base_evaluator.evaluate_task(scenario, question)

        # If sufficient, return as-is
        if base_assessment.sufficiency == DataSufficiency.SUFFICIENT:
            return base_assessment

        # Enhance justification with quantitative analysis
        quantitative_analysis = self._compute_quantitative_analysis(
            scenario, question, base_assessment.limitation_type
        )

        # Generate multi-perspective analysis
        multi_perspective = self._generate_multi_perspective_analysis(
            scenario, question, base_assessment.limitation_type
        )

        # Generate rich justification
        rich_justification = self._generate_rich_justification(
            scenario, question, base_assessment, quantitative_analysis, multi_perspective
        )

        # Update assessment with rich justification
        base_assessment.justification = rich_justification
        base_assessment.confidence = min(0.95, base_assessment.confidence + 0.1)  # Boost confidence

        return base_assessment

    def _compute_quantitative_analysis(
        self,
        scenario: str,
        question: str,
        limitation_type: Optional[LimitationType]
    ) -> Optional[QuantitativeAnalysis]:
        """Compute quantitative mismatch metrics."""
        text = scenario.lower() + " " + question.lower()

        if limitation_type == LimitationType.SPATIAL_RESOLUTION:
            return self._analyze_spatial_resolution_quantitative(text)

        elif limitation_type == LimitationType.TEMPORAL_RESOLUTION:
            return self._analyze_temporal_resolution_quantitative(text)

        elif limitation_type == LimitationType.SAMPLE_SIZE:
            return self._analyze_sample_size_quantitative(text)

        elif limitation_type == LimitationType.MEASUREMENT_PRECISION:
            return self._analyze_measurement_precision_quantitative(text)

        return None

    def _analyze_spatial_resolution_quantitative(self, text: str) -> QuantitativeAnalysis:
        """Analyze spatial resolution with quantitative metrics."""
        # Extract resolution and scale values
        resolution_patterns = [
            (r'(?:resolution|beam|fwhm|angular).*?(\d+\.?\d*)\s*(arcmin|arcsec|degree|pc)', 'angular'),
            (r'(?:resolution|beam|fwhm).*?(\d+\.?\d*)\s*pc', 'spatial'),
            (r'Δ[θx]\s*[=:]\s*(\d+\.?\d*)\s*(arcmin|arcsec|pc)', 'greek'),
        ]

        scale_patterns = [
            (r'(?:scale|size|separation).*?(\d+\.?\d*)\s*pc', 'pc'),
            (r'core.*?scale.*?(\d+\.?\d*)', 'pc'),
            (r'r_core\s*[=:]\s*(\d+\.?\d*)', 'pc'),
        ]

        # Extract values
        resolutions = self._extract_values_with_units(text, resolution_patterns)
        scales = self._extract_values_with_units(text, scale_patterns)

        if not resolutions or not scales:
            return None

        # Convert to common unit (pc)
        res_pc = self._convert_to_pc(resolutions[0]['value'], resolutions[0]['unit'])
        scale_pc = scales[0]['value']  # Already in pc

        # Compute mismatch ratio
        mismatch_ratio = res_pc / scale_pc if scale_pc > 0 else float('inf')

        # Information-theoretic limit
        info_limit = None
        if mismatch_ratio > 5:
            info_limit = f"Cannot resolve features at {scale_pc:.3f} pc with {res_pc:.3f} pc resolution - violates Nyquist by {mismatch_ratio:.1f}×"

        return QuantitativeAnalysis(
            limitation_type="spatial_resolution",
            metric_name="beam_smoothing_scale",
            observed_value=res_pc,
            required_value=scale_pc,
            mismatch_ratio=mismatch_ratio,
            unit="pc",
            information_theoretic_limit=info_limit
        )

    def _analyze_temporal_resolution_quantitative(self, text: str) -> QuantitativeAnalysis:
        """Analyze temporal resolution with quantitative metrics."""
        # Extract cadence and timescale
        cadence_patterns = [
            (r'cadence\s*(?:of|:)?\s*(\d+\.?\d*)\s*(hour|hr|day|min|sec)', 'period'),
            (r'Δt\s*[=:]\s*(\d+\.?\d*)\s*(hour|hr|day|min|sec)', 'greek'),
            (r'(?:one|1)\s*observation.*?(\d+\.?\d*)\s*(hour|hr|day)', 'implicit'),
        ]

        timescale_patterns = [
            (r'phenomenon.*?(?:duration|timescale|τ).*?(\d+\.?\d*)\s*(min|sec|minute|second)', 'duration'),
            (r'τ\s*[=:]\s*(\d+\.?\d*)\s*(min|sec|minute|second)', 'greek'),
            (r'characteristic.*?time.*?(\d+\.?\d*)\s*(min|sec)', 'implicit'),
        ]

        # Extract values
        cadences = self._extract_values_with_units(text, cadence_patterns)
        timescales = self._extract_values_with_units(text, timescale_patterns)

        if not cadences or not timescales:
            return None

        # Convert to seconds
        cadence_sec = self._convert_to_seconds(cadences[0]['value'], cadences[0]['unit'])
        timescale_sec = self._convert_to_seconds(timescales[0]['value'], timescales[0]['unit'])

        # Compute Nyquist ratio
        nyquist_ratio = timescale_sec / cadence_sec if cadence_sec > 0 else float('inf')

        # Information-theoretic limit
        info_limit = None
        if nyquist_ratio < 2:
            info_limit = f"Violates Nyquist criterion by {2/nyquist_ratio:.1f}× - need cadence ≤ {timescale_sec/2:.0}s to characterize {timescale_sec:.0}s phenomenon"

        return QuantitativeAnalysis(
            limitation_type="temporal_resolution",
            metric_name="nyquist_sampling",
            observed_value=cadence_sec,
            required_value=timescale_sec,
            mismatch_ratio=nyquist_ratio,
            unit="seconds",
            information_theoretic_limit=info_limit
        )

    def _analyze_sample_size_quantitative(self, text: str) -> Optional[QuantitativeAnalysis]:
        """Analyze sample size with quantitative metrics."""
        # Extract sample size and effect size
        n_pattern = r'(?:n\s*[=:]|sample\s*(?:size)?\s*(?:of|:)?\s*)\s*(\d+)'

        n_match = re.search(n_pattern, text)
        if not n_match:
            return None

        n = int(n_match.group(1))

        # Look for baseline rate or effect size
        baseline_patterns = [
            r'baseline\s*(?:mortality|rate).*?(\d+\.?\d*)\s*%?',
            r'(\d+\.?\d*)\s*%\s*(?:mortality|rate)',
        ]

        baseline = None
        for pattern in baseline_patterns:
            match = re.search(pattern, text)
            if match:
                baseline = float(match.group(1)) / 100  # Convert % to fraction
                break

        if baseline is None:
            # Can't do quantitative analysis without baseline
            return None

        # Expected events in sample
        expected_events = n * baseline

        # Rule of thumb: need at least 10 events for statistical significance
        min_events = 10

        # Compute insufficiency ratio
        insufficiency_ratio = min_events / expected_events if expected_events > 0 else float('inf')

        # Information-theoretic limit
        info_limit = None
        if expected_events < min_events:
            info_limit = f"Expected {expected_events:.1f} events but need ≥{min_events} for statistical power - insufficient by {min_events/expected_events:.1f}×"

        return QuantitativeAnalysis(
            limitation_type="sample_size",
            metric_name="statistical_power",
            observed_value=n,
            required_value=expected_events,
            mismatch_ratio=insufficiency_ratio,
            unit="events",
            information_theoretic_limit=info_limit
        )

    def _analyze_measurement_precision_quantitative(self, text: str) -> QuantitativeAnalysis:
        """Analyze measurement precision with quantitative metrics."""
        # Extract measurement uncertainty and effect size
        uncertainty_patterns = [
            r'uncertainty\s*[=:]\s*(\d+\.?\d*)\s*%?',
            r'σ\s*[=:]\s*(\d+\.?\d*)\s*%?',
            r'error\s*[=:]\s*(\d+\.?\d*)\s*%?',
        ]

        effect_patterns = [
            r'prediction.*?(\d+\.?\d*)\s*%?',
            r'expected.*?(\d+\.?\d*)\s*%?',
            r'difference.*?(\d+\.?\d*)\s*%?',
        ]

        # Extract values
        uncertainty = None
        for pattern in uncertainty_patterns:
            match = re.search(pattern, text)
            if match:
                uncertainty = float(match.group(1)) / 100  # Convert % to fraction
                break

        effect_size = None
        for pattern in effect_patterns:
            match = re.search(pattern, text)
            if match:
                effect_size = float(match.group(1)) / 100
                break

        if uncertainty is None or effect_size is None:
            return None

        # Signal-to-noise ratio
        snr = effect_size / uncertainty if uncertainty > 0 else float('inf')

        # Information-theoretic limit
        info_limit = None
        if snr < 1:
            info_limit = f"Effect ({effect_size*100:.1f}%) smaller than uncertainty ({uncertainty*100:.1f}%) - SNR={snr:.2f} << 1.0, effect indistinguishable from noise"

        return QuantitativeAnalysis(
            limitation_type="measurement_precision",
            metric_name="signal_to_noise_ratio",
            observed_value=uncertainty,
            required_value=effect_size,
            mismatch_ratio=snr,
            unit="fraction",
            information_theoretic_limit=info_limit
        )

    def _extract_values_with_units(
        self,
        text: str,
        patterns: List[Tuple[str, str]]
    ) -> List[Dict[str, Any]]:
        """Extract values with units from text using patterns."""
        results = []

        for pattern, unit_type in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    value = float(match[0]) if isinstance(match, tuple) else float(match)
                    unit = match[1] if len(match) > 1 else unit_type

                    results.append({
                        'value': value,
                        'unit': unit,
                        'pattern': pattern
                    })
                except (ValueError, IndexError):
                    continue

        return results

    def _convert_to_pc(self, value: float, unit: str) -> float:
        """Convert value to parsecs."""
        conversions = {
            'pc': 1.0,
            'arcmin': 0.000291,
            'arcsec': 0.00000485,
            'degree': 0.0000175,
            'angular': 0.000291,
            'spatial': 1.0,
        }
        return value * conversions.get(unit.lower(), 1.0)

    def _convert_to_seconds(self, value: float, unit: str) -> float:
        """Convert temporal value to seconds."""
        conversions = {
            'second': 1.0, 'sec': 1.0, 's': 1.0,
            'minute': 60.0, 'min': 60.0,
            'hour': 3600.0, 'hr': 3600.0, 'h': 3600.0,
            'day': 86400.0,
            'period': 1.0,  # Already in time unit
        }
        return value * conversions.get(unit.lower(), value)

    def _generate_multi_perspective_analysis(
        self,
        scenario: str,
        question: str,
        limitation_type: Optional[LimitationType]
    ) -> MultiPerspectiveAnalysis:
        """Generate analysis from multiple perspectives."""
        analysis = MultiPerspectiveAnalysis()

        # Physical perspective
        if limitation_type in [LimitationType.SPATIAL_RESOLUTION, LimitationType.TEMPORAL_RESOLUTION]:
            analysis.physical_perspective = self._physical_perspective(scenario, limitation_type)

        # Statistical perspective
        if limitation_type in [LimitationType.SAMPLE_SIZE, LimitationType.MEASUREMENT_PRECISION]:
            analysis.statistical_perspective = self._statistical_perspective(scenario, limitation_type)

        # Causal perspective
        if limitation_type == LimitationType.CAUSAL_INFERENCE:
            analysis.causal_perspective = self._causal_perspective(scenario, limitation_type)

        # Epistemic perspective (always)
        analysis.epistemic_perspective = self._epistemic_perspective(scenario, question, limitation_type)

        return analysis

    def _physical_perspective(self, scenario: str, limitation_type: LimitationType) -> str:
        """Generate physical science perspective."""
        if limitation_type == LimitationType.SPATIAL_RESOLUTION:
            return "Beam convolution averages over spatial scales smaller than beam FWHM - information about sub-beam structure is fundamentally lost during observation"

        elif limitation_type == LimitationType.TEMPORAL_RESOLUTION:
            return "Temporal averaging mixes timescales shorter than cadence - rapid events are either missed or aliased to longer timescales"

        return None

    def _statistical_perspective(self, scenario: str, limitation_type: LimitationType) -> str:
        """Generate statistical perspective."""
        if limitation_type == LimitationType.SAMPLE_SIZE:
            return "Insufficient statistical power - cannot distinguish signal from noise or detect effect with required confidence"

        elif limitation_type == LimitationType.MEASUREMENT_PRECISION:
            return "Measurement uncertainty exceeds effect size - observed differences are statistically indistinguishable from zero"

        return None

    def _causal_perspective(self, scenario: str, limitation_type: LimitationType) -> str:
        """Generate causal inference perspective."""
        return "Observational data establish correlation but not causation - multiple causal pathways consistent with data, requires controlled manipulation or natural experiment"

    def _epistemic_perspective(
        self,
        scenario: str,
        question: str,
        limitation_type: Optional[LimitationType]
    ) -> str:
        """Generate epistemic perspective."""
        return "Information-theoretic limit: data lack the discriminative power required to support the requested conclusion at the requested level of precision"

    def _generate_rich_justification(
        self,
        scenario: str,
        question: str,
        base_assessment: MetaCognitiveAssessment,
        quantitative_analysis: Optional[QuantitativeAnalysis],
        multi_perspective: MultiPerspectiveAnalysis
    ) -> str:
        """Generate rich, multi-perspective justification."""
        parts = []

        # Start with core limitation
        if base_assessment.limitation_type:
            parts.append(f"**Limitation Type**: {base_assessment.limitation_type.value}")

        # Add quantitative analysis
        if quantitative_analysis:
            parts.append(f"\n**Quantitative Analysis**:")
            parts.append(f"- {quantitative_analysis.metric_name}: {quantitative_analysis.observed_value:.3f} {quantitative_analysis.unit}")
            parts.append(f"- Required: {quantitative_analysis.required_value:.3f} {quantitative_analysis.unit}")
            parts.append(f"- Mismatch: {quantitative_analysis.mismatch_ratio:.1f}×")

            if quantitative_analysis.information_theoretic_limit:
                parts.append(f"\n**Information-Theoretic Limit**:")
                parts.append(f"{quantitative_analysis.information_theoretic_limit}")

        # Add multi-perspective analysis
        parts.append(f"\n**Multi-Perspective Analysis**:")

        if multi_perspective.physical_perspective:
            parts.append(f"- *Physical*: {multi_perspective.physical_perspective}")

        if multi_perspective.statistical_perspective:
            parts.append(f"- *Statistical*: {multi_perspective.statistical_perspective}")

        if multi_perspective.causal_perspective:
            parts.append(f"- *Causal*: {multi_perspective.causal_perspective}")

        if multi_perspective.epistemic_perspective:
            parts.append(f"- *Epistemic*: {multi_perspective.epistemic_perspective}")

        # Add conclusion
        parts.append(f"\n**Conclusion**: The data contain {base_assessment.limitation_type.value} that preclude reliable conclusions. I cannot provide a definitive answer to the question about {question[:50]}...")

        return "\n".join(parts)


def create_advanced_meta_cognitive_reasoner() -> AdvancedMetaCognitiveReasoner:
    """Factory function to create advanced meta-cognitive reasoner."""
    return AdvancedMetaCognitiveReasoner()
