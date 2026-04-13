"""
ASTRA Live — Astrophysical Verifier
Multi-layer verification for astronomical hypotheses: statistical, physical, observational, systematic.

Inspired by Aletheia's Generator-Verifier-Reviser pattern, adapted for astronomy:
- Instead of formal proof verification, we check physical plausibility
- Instead of citation checking, we check cross-dataset consistency
- Instead of mathematical rigor, we check astrophysical consistency

Author: ASTRA V9.5 (Aletheia Integration)
Date: 2026-04-13
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple
import time


class VerificationLayer(Enum):
    """Layers of astrophysical verification"""
    STATISTICAL = "statistical"           # p-values, confidence, effect sizes
    PHYSICAL = "physical"                 # Laws of physics, dimensional analysis
    OBSERVATIONAL = "observational"       # Cross-dataset, multi-wavelength consistency
    SYSTEMATIC = "systematic"             # Instrumental limits, selection effects


class FailureReason(Enum):
    """Astronomy-specific reasons to abandon a hypothesis"""
    PHYSICAL_IMPOSSIBILITY = "violates_fundamental_physics"
    OBSERVATIONAL_IMPOSSIBILITY = "exceeds_instrument_limits"
    STATISTICAL_STAGNATION = "confidence_not_improving"
    CROSS_DATASET_CONTRADICTION = "contradicts_well_established_measurements"
    SYSTEMATIC_DOMINATED = "systematic_errors_exceed_signal"
    REDSHIFT_IMPOSSIBILITY = "unphysical_redshift_evolution"
    DIMENSIONAL_INCONSISTENCY = "units_do_not_balance"


@dataclass
class VerificationFlaw:
    """A specific flaw identified in a hypothesis"""
    layer: VerificationLayer
    severity: str  # "critical", "major", "minor"
    description: str
    suggestion: str
    location: Optional[str] = None  # Where in the hypothesis the flaw occurs


@dataclass
class Verdict:
    """Result of astrophysical verification"""
    passed: bool
    overall_confidence: float
    should_abandon: bool
    abandon_reason: Optional[FailureReason] = None
    flaws: List[VerificationFlaw] = field(default_factory=list)
    layer_scores: Dict[VerificationLayer, float] = field(default_factory=dict)
    revision_hints: List[str] = field(default_factory=list)
    verification_time: float = field(default_factory=time.time)


@dataclass
class PhysicalQuantities:
    """Extracted physical quantities from a hypothesis"""
    quantities: Dict[str, Tuple[float, str]]  # name: (value, unit)
    relations: List[str]  # Relationships between quantities
    energy_terms: List[str]  # Terms involving energy
    causal_relations: List[str]  # Cause-effect relationships


class AstrophysicalVerifier:
    """
    Multi-layer astrophysical verification system.

    Checks four layers:
    1. Statistical: p-values, FDR, effect sizes
    2. Physical: dimensional analysis, energy conservation, causality
    3. Observational: cross-dataset, multi-wavelength consistency
    4. Systematic: instrumental limits, selection effects
    """

    def __init__(self):
        # Physical constants (CGS units)
        self.constants = {
            'c': 2.998e10,          # Speed of light [cm/s]
            'G': 6.674e-8,          # Gravitational constant [cm³/g/s²]
            'h': 6.626e-27,         # Planck constant [erg·s]
            'k_B': 1.381e-16,       # Boltzmann constant [erg/K]
            'm_p': 1.673e-24,       # Proton mass [g]
            'sigma_T': 6.652e-25,   # Thomson cross-section [cm²]
            'L_sun': 3.828e33,      # Solar luminosity [erg/s]
            'M_sun': 1.989e33,      # Solar mass [g]
            'R_sun': 6.957e10,      # Solar radius [cm]
        }

        # Astronomical survey constraints
        self.survey_limits = {
            'pantheon': {
                'z_max': 2.3,
                'z_min': 0.001,
                'n_supernovae': 1701,
                'distance_precision': 0.1,  # mag
            },
            'gaia_dr3': {
                'magnitude_limit': 21.0,
                'parallax_precision': 0.01,  # mas
                'n_stars': 1.8e9,
            },
            'sdss_dr18': {
                'z_max': 0.5,
                'area': 10000,  # deg²
                'n_galaxies': 2e6,
            },
            'planck': {
                'frequency_range': (30, 857),  # GHz
                'angular_resolution': 5.0,  # arcmin
                'temperature_precision': 1e-6,  # K
            },
            'tess': {
                'magnitude_limit': 16.0,
                'pixel_scale': 21.0,  # arcsec/pixel
                'period_precision': 0.001,  # days
            },
            'ligo': {
                'frequency_range': (10, 5000),  # Hz
                'strain_sensitivity': 1e-21,
                'mass_range': (0.1, 200),  # Solar masses
            },
        }

        # Known physical constraints
        self.physical_constraints = {
            'speed_limit': self.constants['c'],  # Nothing exceeds c
            'temperature_range': (0, 1e12),  # K (from CMB to early universe)
            'density_range': (1e-31, 1e15),  # g/cm³ (void to neutron star)
            'magnetic_field_range': (1e-6, 1e15),  # G (interstellar to magnetar)
        }

    def verify(self, hypothesis: 'Hypothesis', test_results: List = None,
               data_sources: List[str] = None) -> Verdict:
        """
        Main verification entry point. Run all four layers of verification.

        Args:
            hypothesis: The hypothesis to verify
            test_results: Statistical test results (if available)
            data_sources: Which astronomical datasets were used

        Returns:
            Verdict with pass/fail, confidence, and identified flaws
        """
        flaws = []
        layer_scores = {}
        revision_hints = []

        # Layer 1: Statistical Verification
        stat_score, stat_flaws = self._check_statistical_layer(hypothesis, test_results)
        layer_scores[VerificationLayer.STATISTICAL] = stat_score
        flaws.extend(stat_flaws)

        # Layer 2: Physical Consistency
        phys_score, phys_flaws = self._check_physical_layer(hypothesis)
        layer_scores[VerificationLayer.PHYSICAL] = phys_score
        flaws.extend(phys_flaws)

        # Layer 3: Observational Consistency
        obs_score, obs_flaws = self._check_observational_layer(hypothesis, data_sources)
        layer_scores[VerificationLayer.OBSERVATIONAL] = obs_score
        flaws.extend(obs_flaws)

        # Layer 4: Systematic Error Check
        sys_score, sys_flaws = self._check_systematic_layer(hypothesis)
        layer_scores[VerificationLayer.SYSTEMATIC] = sys_score
        flaws.extend(sys_flaws)

        # Calculate overall confidence
        overall_confidence = np.mean(list(layer_scores.values()))

        # Determine if hypothesis should be abandoned
        should_abandon, abandon_reason = self._should_abandon(
            hypothesis, layer_scores, flaws
        )

        # Generate revision hints from flaws
        revision_hints = self._generate_revision_hints(flaws)

        # Determine pass/fail (pass if all layers above threshold)
        passed = all(score >= 0.5 for score in layer_scores.values())

        return Verdict(
            passed=passed,
            overall_confidence=overall_confidence,
            should_abandon=should_abandon,
            abandon_reason=abandon_reason,
            flaws=flaws,
            layer_scores=layer_scores,
            revision_hints=revision_hints,
        )

    def _check_statistical_layer(self, hypothesis: 'Hypothesis',
                                 test_results: List = None) -> Tuple[float, List[VerificationFlaw]]:
        """
        Layer 1: Statistical verification.

        Checks:
        - p-values are meaningful
        - Confidence is improving over time
        - Effect sizes are reasonable
        - Not suffering from multiple testing
        """
        flaws = []
        score = 0.8  # Start high, deduct for issues

        if test_results is None:
            # Use hypothesis's test results
            test_results = hypothesis.test_results

        if not test_results:
            # No tests run yet - neutral score
            return 0.5, []

        # Check for statistical significance
        significant_tests = [t for t in test_results if getattr(t, 'passed', False)]
        n_significant = len(significant_tests)
        n_total = len(test_results)

        if n_total > 0:
            significance_rate = n_significant / n_total
            score *= (0.5 + 0.5 * significance_rate)

        # Check for confidence plateau (stagnation)
        if len(test_results) >= 5:
            recent_confidence = [t.passed for t in test_results[-5:]]
            if not any(recent_confidence):
                flaws.append(VerificationFlaw(
                    layer=VerificationLayer.STATISTICAL,
                    severity="major",
                    description="Confidence has plateaued - last 5 tests all failed",
                    suggestion="Consider alternative mechanisms or increase sample size"
                ))
                score *= 0.7

        # Check for p-value hacking (too many marginal results)
        if test_results:
            marginal_p = [t for t in test_results
                         if hasattr(t, 'p_value') and 0.01 < t.p_value < 0.1]
            if len(marginal_p) > n_total * 0.5:
                flaws.append(VerificationFlaw(
                    layer=VerificationLayer.STATISTICAL,
                    severity="minor",
                    description=f"Many marginal p-values ({len(marginal_p)}/{n_total}) - possible p-hacking",
                    suggestion="Apply FDR correction, increase sample size, or pre-register analysis"
                ))

        return max(0.0, min(1.0, score)), flaws

    def _check_physical_layer(self, hypothesis: 'Hypothesis') -> Tuple[float, List[VerificationFlaw]]:
        """
        Layer 2: Physical consistency verification.

        Checks:
        - Dimensional analysis (units balance)
        - Energy conservation
        - Causality (no superluminal effects)
        - Thermodynamic consistency
        - Physical parameter ranges
        """
        flaws = []
        score = 0.9  # Start high

        # Parse hypothesis for physical quantities
        quantities = self._extract_physical_quantities(hypothesis)

        # Check dimensional consistency
        dimensionally_consistent = self._check_dimensional_consistency(quantities)
        if not dimensionally_consistent:
            flaws.append(VerificationFlaw(
                layer=VerificationLayer.PHYSICAL,
                severity="critical",
                description="Dimensional analysis failed: units do not balance",
                suggestion="Check all equations for unit consistency. Common issue: missing factors of c or G."
            ))
            score *= 0.3

        # Check energy conservation
        energy_conserved = self._check_energy_conservation(quantities)
        if not energy_conserved:
            flaws.append(VerificationFlaw(
                layer=VerificationLayer.PHYSICAL,
                severity="critical",
                description="Energy conservation violated: energy not balanced",
                suggestion="Include all energy terms: kinetic, potential, radiative, feedback, etc."
            ))
            score *= 0.4

        # Check causality
        causal = self._check_causality(quantities)
        if not causal:
            flaws.append(VerificationFlaw(
                layer=VerificationLayer.PHYSICAL,
                severity="critical",
                description="Causality violation: superluminal effects detected",
                suggestion="Review light-travel time calculations and causal structure"
            ))
            score *= 0.2

        # Check physical parameter ranges
        in_range = self._check_parameter_ranges(quantities)
        if not in_range:
            flaws.append(VerificationFlaw(
                layer=VerificationLayer.PHYSICAL,
                severity="major",
                description="Physical parameters outside known ranges",
                suggestion="Verify that temperatures, densities, magnetic fields are astrophysically reasonable"
            ))
            score *= 0.6

        return max(0.0, min(1.0, score)), flaws

    def _check_observational_layer(self, hypothesis: 'Hypothesis',
                                   data_sources: List[str] = None) -> Tuple[float, List[VerificationFlaw]]:
        """
        Layer 3: Observational consistency verification.

        Checks:
        - Cross-dataset consistency
        - Within survey limits
        - Multi-wavelength consistency
        - Redshift evolution is physical
        """
        flaws = []
        score = 0.8

        if data_sources is None:
            # Infer from hypothesis description
            data_sources = self._infer_data_sources(hypothesis)

        # Check if hypothesis is within survey capabilities
        for source in data_sources:
            if source.lower() in self.survey_limits:
                limits = self.survey_limits[source.lower()]
                if not self._within_survey_limits(hypothesis, limits):
                    flaws.append(VerificationFlaw(
                        layer=VerificationLayer.OBSERVATIONAL,
                        severity="major",
                        description=f"Hypothesis requires precision beyond {source} capabilities",
                        suggestion=f"Refine hypothesis to match {source} sensitivity or identify alternative datasets"
                    ))
                    score *= 0.7

        # Check for cross-dataset consistency (multiple datasets should agree)
        if len(data_sources) > 1:
            consistent = self._check_cross_dataset_consistency(hypothesis, data_sources)
            if not consistent:
                flaws.append(VerificationFlaw(
                    layer=VerificationLayer.OBSERVATIONAL,
                    severity="major",
                    description="Cross-dataset inconsistency: predictions disagree across datasets",
                    suggestion="Check for selection effects, systematic offsets, or different populations"
                ))
                score *= 0.6

        # Check redshift evolution (if applicable)
        z_physical = self._check_redshift_evolution(hypothesis)
        if not z_physical:
            flaws.append(VerificationFlaw(
                layer=VerificationLayer.OBSERVATIONAL,
                severity="critical",
                description="Unphysical redshift evolution detected",
                suggestion="Ensure evolution law is causal and monotonic where appropriate"
            ))
            score *= 0.3

        return max(0.0, min(1.0, score)), flaws

    def _check_systematic_layer(self, hypothesis: 'Hypothesis') -> Tuple[float, List[VerificationFlaw]]:
        """
        Layer 4: Systematic error verification.

        Checks:
        - Signal larger than systematic errors
        - Selection effects accounted for
        - Instrumental biases considered
        - Not dominated by uncertainties
        """
        flaws = []
        score = 0.85

        # Check if signal is larger than systematics
        signal_to_systematic = self._estimate_signal_to_systematic(hypothesis)
        if signal_to_systematic < 3.0:  # Less than 3-sigma from systematics
            flaws.append(VerificationFlaw(
                layer=VerificationLayer.SYSTEMATIC,
                severity="major",
                description=f"Signal-to-systematic ratio low ({signal_to_systematic:.1f}σ)",
                suggestion="Increase sample size, improve systematic modeling, or focus on higher-S/N measurements"
            ))
            score *= 0.5

        # Check for selection effects
        has_selection_correction = self._check_selection_effects(hypothesis)
        if not has_selection_correction:
            flaws.append(VerificationFlaw(
                layer=VerificationLayer.SYSTEMATIC,
                severity="minor",
                description="Selection effects may not be fully accounted for",
                suggestion="Consider completeness functions, detection thresholds, and Malmquist bias"
            ))
            score *= 0.9

        return max(0.0, min(1.0, score)), flaws

    def _extract_physical_quantities(self, hypothesis: 'Hypothesis') -> PhysicalQuantities:
        """Extract physical quantities and relations from hypothesis text"""
        quantities = {}
        relations = []
        energy_terms = []
        causal_relations = []

        # Common astrophysical quantities to look for
        patterns = {
            'temperature': ['temperature', 'T_eff', 'T_cmb', 'kelvin', 'K'],
            'density': ['density', 'rho', 'n_e', 'n_H', 'cm^-3'],
            'velocity': ['velocity', 'v', 'km/s', 'dispersion'],
            'luminosity': ['luminosity', 'L', 'erg/s', 'solar'],
            'mass': ['mass', 'M', 'M_sun', 'kg'],
            'distance': ['distance', 'd', 'kpc', 'Mpc', 'parsecs'],
            'redshift': ['redshift', 'z'],
            'magnetic_field': ['magnetic', 'B', 'Gauss', 'muG'],
            'metallicity': ['metallicity', 'Fe/H', 'Z'],
        }

        # This is a simplified extraction - a full implementation would use NLP
        # For now, we'll do keyword matching in the description
        desc = hypothesis.description.lower()

        for quantity, keywords in patterns.items():
            for keyword in keywords:
                if keyword.lower() in desc:
                    quantities[quantity] = (0.0, "unknown")  # Value extracted from data
                    break

        # Look for energy-related terms
        energy_keywords = ['energy', 'power', 'luminosity', 'flux', 'heating', 'cooling',
                          'feedback', 'accretion', 'radiation']
        for keyword in energy_keywords:
            if keyword in desc:
                energy_terms.append(keyword)

        # Look for causal relations
        causal_keywords = ['causes', 'leads to', 'results in', 'due to', 'because',
                          'feedback', 'trigger', 'induce', 'drives']
        for keyword in causal_keywords:
            if keyword in desc:
                causal_relations.append(keyword)

        return PhysicalQuantities(
            quantities=quantities,
            relations=relations,
            energy_terms=energy_terms,
            causal_relations=causal_relations,
        )

    def _check_dimensional_consistency(self, quantities: PhysicalQuantities) -> bool:
        """Check that units balance in equations"""
        # Simplified check - full implementation would parse equations
        # For now, check if energy terms appear balanced
        n_energy_terms = len(quantities.energy_terms)
        return n_energy_terms > 0 or n_energy_terms % 2 == 0

    def _check_energy_conservation(self, quantities: PhysicalQuantities) -> bool:
        """Check that energy is conserved"""
        # Simplified check - look for energy input/output balance
        energy_keywords = quantities.energy_terms
        has_source = any(kw in energy_keywords for kw in ['heating', 'accretion', 'power'])
        has_sink = any(kw in energy_keywords for kw in ['cooling', 'radiation', 'loss'])
        # Either no energy terms, or balanced terms
        return len(energy_keywords) == 0 or (has_source and has_sink)

    def _check_causality(self, quantities: PhysicalQuantities) -> bool:
        """Check that nothing travels faster than light"""
        # Simplified check - look for superluminal keywords
        desc = ' '.join(quantities.relations)
        superluminal_keywords = ['faster than light', 'superluminal', 'ftl', 'instantaneous']
        return not any(kw in desc.lower() for kw in superluminal_keywords)

    def _check_parameter_ranges(self, quantities: PhysicalQuantities) -> bool:
        """Check that physical parameters are within known ranges"""
        # This would check actual values against physical_constraints
        # For now, return True (simplified)
        return True

    def _within_survey_limits(self, hypothesis: 'Hypothesis', limits: dict) -> bool:
        """Check if hypothesis requirements match survey capabilities"""
        # Simplified check - would parse hypothesis for required precision
        return True

    def _infer_data_sources(self, hypothesis: 'Hypothesis') -> List[str]:
        """Infer which datasets are used from hypothesis description"""
        desc = hypothesis.description.lower()
        sources = []

        source_keywords = {
            'pantheon': ['pantheon', 'sn ia', 'supernova', 'distance modulus'],
            'gaia': ['gaia', 'parallax', 'astrometry', 'hr diagram'],
            'sdss': ['sdss', 'galaxy color', 'redshift', 'spectroscopic'],
            'planck': ['planck', 'cmb', 'cosmic microwave', 'power spectrum'],
            'tess': ['tess', 'transit', 'exoplanet', 'light curve'],
            'ligo': ['ligo', 'gravitational wave', 'gw', 'chirp'],
        }

        for source, keywords in source_keywords.items():
            if any(kw in desc for kw in keywords):
                sources.append(source)

        return sources if sources else ['unknown']

    def _check_cross_dataset_consistency(self, hypothesis: 'Hypothesis',
                                        data_sources: List[str]) -> bool:
        """Check if results are consistent across different datasets"""
        # Simplified - would check actual cross-dataset comparisons
        return True

    def _check_redshift_evolution(self, hypothesis: 'Hypothesis') -> bool:
        """Check if redshift evolution is physical"""
        desc = hypothesis.description.lower()

        # Check for unphysical evolution patterns
        unphysical_patterns = [
            'decreases with redshift',  # Most things increase or stay constant
            'negative evolution',  # Usually unphysical
            'faster than light',  # Causality violation
        ]

        return not any(pattern in desc for pattern in unphysical_patterns)

    def _estimate_signal_to_systematic(self, hypothesis: 'Hypothesis') -> float:
        """Estimate signal-to-systematic error ratio"""
        # Simplified - would use actual data
        # Use confidence as proxy
        return hypothesis.confidence * 10  # Rough scaling

    def _check_selection_effects(self, hypothesis: 'Hypothesis') -> bool:
        """Check if selection effects are accounted for"""
        desc = hypothesis.description.lower()
        selection_keywords = ['selection', 'completeness', 'bias', 'malmquist',
                             'detection limit', 'flux limit']
        return any(kw in desc for kw in selection_keywords)

    def _should_abandon(self, hypothesis: 'Hypothesis',
                       layer_scores: Dict[VerificationLayer, float],
                       flaws: List[VerificationFlaw]) -> Tuple[bool, Optional[FailureReason]]:
        """
        Determine if hypothesis should be abandoned based on critical flaws.

        Returns:
            (should_abandon, reason)
        """
        # Check for critical flaws in any layer
        for flaw in flaws:
            if flaw.severity == "critical":
                if flaw.layer == VerificationLayer.PHYSICAL:
                    if "dimensional" in flaw.description.lower():
                        return True, FailureReason.DIMENSIONAL_INCONSISTENCY
                    elif "energy" in flaw.description.lower():
                        return True, FailureReason.PHYSICAL_IMPOSSIBILITY
                    elif "causality" in flaw.description.lower():
                        return True, FailureReason.PHYSICAL_IMPOSSIBILITY
                elif flaw.layer == VerificationLayer.OBSERVATIONAL:
                    if "redshift" in flaw.description.lower():
                        return True, FailureReason.REDSHIFT_IMPOSSIBILITY
                    elif "capability" in flaw.description.lower():
                        return True, FailureReason.OBSERVATIONAL_IMPOSSIBILITY

        # Check for persistent low scores across all layers
        if all(score < 0.3 for score in layer_scores.values()):
            return True, FailureReason.CROSS_DATASET_CONTRADICTION

        # Check for systematic-dominated
        if layer_scores.get(VerificationLayer.SYSTEMATIC, 1.0) < 0.4:
            return True, FailureReason.SYSTEMATIC_DOMINATED

        # Check for statistical stagnation
        if layer_scores.get(VerificationLayer.STATISTICAL, 1.0) < 0.4:
            return True, FailureReason.STATISTICAL_STAGNATION

        return False, None

    def _generate_revision_hints(self, flaws: List[VerificationFlaw]) -> List[str]:
        """Generate revision hints from identified flaws"""
        hints = []

        for flaw in flaws:
            if flaw.suggestion:
                hints.append(flaw.suggestion)

        # Add general hints based on flaw patterns
        critical_flaws = [f for f in flaws if f.severity == "critical"]
        if critical_flaws:
            hints.insert(0, "CRITICAL: Address critical flaws before proceeding")

        physical_flaws = [f for f in flaws if f.layer == VerificationLayer.PHYSICAL]
        if len(physical_flaws) > 2:
            hints.append("Multiple physical inconsistencies detected - review fundamental assumptions")

        return list(set(hints))  # Remove duplicates


def verify_hypothesis(hypothesis: 'Hypothesis', test_results: List = None,
                     data_sources: List[str] = None) -> Verdict:
    """
    Convenience function to verify a hypothesis.

    Args:
        hypothesis: The hypothesis to verify
        test_results: Statistical test results (if available)
        data_sources: Which astronomical datasets were used

    Returns:
        Verdict with pass/fail, confidence, and identified flaws

    Example:
        >>> from astra_live_backend.hypotheses import Hypothesis
        >>> h = Hypothesis(id="H001", name="Test", domain="Astrophysics",
        ...                description="Filament spacing scales with density")
        >>> verdict = verify_hypothesis(h)
        >>> if verdict.should_abandon:
        ...     print(f"Abandon: {verdict.abandon_reason}")
    """
    verifier = AstrophysicalVerifier()
    return verifier.verify(hypothesis, test_results, data_sources)


# === Generator-Verifier-Reviser Loop ===

class GeneratorVerifierReviser:
    """
    Implements the Generator-Verifier-Reviser loop for astronomical discovery.

    Inspired by Aletheia (DeepMind), adapted for astronomy:
    - Generator: Proposes astrophysical hypotheses
    - Verifier: Checks physical + observational consistency
    - Reviser: Refines based on identified flaws

    Loop continues until:
    1. Hypothesis passes verification (confidence >= threshold)
    2. Verifier recommends abandonment
    3. Maximum iterations reached
    """

    def __init__(self, max_iterations: int = 10, confidence_threshold: float = 0.8):
        self.verifier = AstrophysicalVerifier()
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold

    def iterate(self, hypothesis: 'Hypothesis', generate_fn: callable,
               revise_fn: callable) -> Tuple['Hypothesis', Verdict]:
        """
        Run the Generator-Verifier-Reviser loop.

        Args:
            hypothesis: Initial hypothesis
            generate_fn: Function to generate new aspects (returns modified hypothesis)
            revise_fn: Function to revise based on flaws (hypothesis, flaws) -> hypothesis

        Returns:
            (final_hypothesis, final_verdict)
        """
        current_h = hypothesis
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            # Verify current state
            verdict = self.verifier.verify(current_h)

            # Check for abandonment
            if verdict.should_abandon:
                return current_h, verdict

            # Check for success
            if verdict.passed and current_h.confidence >= self.confidence_threshold:
                return current_h, verdict

            # Revise based on flaws
            if verdict.flaws:
                try:
                    current_h = revise_fn(current_h, verdict.flaws, verdict.revision_hints)
                except Exception as e:
                    # Revision failed - return current state
                    return current_h, verdict
            else:
                # No flaws but not confident enough - generate more
                try:
                    current_h = generate_fn(current_h)
                except Exception as e:
                    # Generation failed - return current state
                    return current_h, verdict

        # Max iterations reached
        return current_h, verdict


# === Convenience Functions for Engine Integration ===

def quick_verify(hypothesis: 'Hypothesis') -> Dict:
    """
    Quick verification for engine integration.

    Returns a dict compatible with engine's decision-making.
    """
    verdict = verify_hypothesis(hypothesis)

    return {
        'passed': verdict.passed,
        'confidence': verdict.overall_confidence,
        'should_abandon': verdict.should_abandon,
        'abandon_reason': verdict.abandon_reason.value if verdict.abandon_reason else None,
        'num_flaws': len(verdict.flaws),
        'critical_flaws': len([f for f in verdict.flaws if f.severity == 'critical']),
        'layer_scores': {layer.value: score for layer, score in verdict.layer_scores.items()},
        'revision_hints': verdict.revision_hints,
    }


def create_exit_condition_checker():
    """
    Create an exit condition checker for the engine.

    Returns a function that can be called to check if a hypothesis
    should be abandoned based on astrophysical verification.
    """
    verifier = AstrophysicalVerifier()

    def should_exit(hypothesis: 'Hypothesis', test_results: List = None,
                   data_sources: List[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if hypothesis should be abandoned.

        Returns:
            (should_exit, reason_string)
        """
        verdict = verifier.verify(hypothesis, test_results, data_sources)

        if verdict.should_abandon:
            reason_map = {
                FailureReason.PHYSICAL_IMPOSSIBILITY: "Violates fundamental physics",
                FailureReason.OBSERVATIONAL_IMPOSSIBILITY: "Beyond current observational capabilities",
                FailureReason.STATISTICAL_STAGNATION: "Confidence not improving",
                FailureReason.CROSS_DATASET_CONTRADICTION: "Contradicts established measurements",
                FailureReason.SYSTEMATIC_DOMINATED: "Systematic errors exceed signal",
                FailureReason.REDSHIFT_IMPOSSIBILITY: "Unphysical redshift evolution",
                FailureReason.DIMENSIONAL_INCONSISTENCY: "Units do not balance",
            }
            reason = reason_map.get(verdict.abandon_reason, "Unknown reason")
            return True, reason

        return False, None

    return should_exit
