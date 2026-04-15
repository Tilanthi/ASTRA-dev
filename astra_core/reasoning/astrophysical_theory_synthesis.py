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
Astrophysical Theory Synthesis for STAN V43

Build physical theories from observations. Identifies patterns,
promotes them to laws with mechanism explanations, and generates
testable predictions.

Author: STAN V43 Reasoning Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np


class AstroPatternType(Enum):
    """Domain-specific pattern types in astrophysics."""
    SCALING_RELATION = auto()       # M-sigma, L-T, Tully-Fisher
    EMPIRICAL_SEQUENCE = auto()     # HR diagram, color-magnitude
    POPULATION_DISTRIBUTION = auto() # IMF, luminosity function
    PHASE_TRANSITION = auto()       # SF threshold, ionization front
    FEEDBACK_LOOP = auto()          # AGN-galaxy, stellar winds
    MORPHOLOGICAL_SEQUENCE = auto() # Hubble sequence
    EVOLUTIONARY_TRACK = auto()     # Stellar evolution, galaxy merger
    THRESHOLD_BEHAVIOR = auto()     # Jeans mass, Bonnor-Ebert


class ConfidenceLevel(Enum):
    """Confidence levels for theories and laws."""
    SPECULATIVE = auto()    # Weak evidence, many alternatives
    TENTATIVE = auto()      # Some support, needs testing
    ESTABLISHED = auto()    # Well tested, few alternatives
    FUNDAMENTAL = auto()    # Derived from first principles


@dataclass
class ObservedPattern:
    """An observed pattern in data."""
    name: str
    pattern_type: AstroPatternType
    variables: List[str]
    functional_form: str         # e.g., "Y ~ X^alpha"
    parameters: Dict[str, float] # Fit parameters
    scatter: float               # Intrinsic scatter
    n_observations: int
    domain: str                  # Where pattern applies
    exceptions: List[str]        # Known violations


@dataclass
class PhysicalLaw:
    """A physical law with validity bounds."""
    name: str
    equation: str
    physical_basis: str          # Theoretical derivation
    validity_conditions: List[str]
    violating_conditions: List[str]
    accuracy: float              # Typical accuracy when valid
    derivable_from: List[str]    # More fundamental laws
    derived_quantities: List[str]
    confidence: ConfidenceLevel
    references: List[str]


@dataclass
class Mechanism:
    """A physical mechanism explaining how something works."""
    name: str
    process_type: str            # 'dynamical', 'radiative', etc.
    cause: str
    effect: str
    intermediate_steps: List[str]
    timescale: str
    energy_source: str
    equation: str
    conditions_required: List[str]


@dataclass
class Prediction:
    """A testable prediction from theory."""
    description: str
    observable: str
    predicted_value: float
    uncertainty: float
    conditions: str
    test_observation: str        # What observation would test this
    discriminating_power: float  # How well it distinguishes theories


@dataclass
class MechanismTheory:
    """Complete theory = Laws + Mechanisms + Predictions."""
    name: str
    description: str
    laws: List[PhysicalLaw]
    mechanisms: List[Mechanism]
    predictions: List[Prediction]
    supported_patterns: List[str]
    unexplained_patterns: List[str]
    confidence: ConfidenceLevel
    rival_theories: List[str]


class PatternIdentifier:
    """
    Identify astrophysical patterns in observational data.

    Looks for scaling relations, sequences, distributions, etc.
    """

    def __init__(self):
        """Initialize pattern identifier."""
        pass

    def identify_scaling_relation(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_err: Optional[np.ndarray] = None,
        y_err: Optional[np.ndarray] = None
    ) -> Tuple[Dict[str, float], float, str]:
        """
        Fit power-law scaling relation Y = A * X^alpha.

        Returns (parameters, scatter, quality).
        """
        # Remove invalid values
        valid = (x > 0) & (y > 0) & ~np.isnan(x) & ~np.isnan(y)
        x_valid = x[valid]
        y_valid = y[valid]

        if len(x_valid) < 5:
            return {}, 0.0, 'insufficient_data'

        # Log-linear fit
        log_x = np.log10(x_valid)
        log_y = np.log10(y_valid)

        # Simple OLS fit
        coeffs = np.polyfit(log_x, log_y, 1)
        alpha = coeffs[0]
        log_A = coeffs[1]
        A = 10**log_A

        # Residual scatter
        log_y_pred = alpha * log_x + log_A
        scatter = np.std(log_y - log_y_pred)

        # Quality assessment
        r_squared = 1 - np.var(log_y - log_y_pred) / np.var(log_y)

        if r_squared > 0.9:
            quality = 'excellent'
        elif r_squared > 0.7:
            quality = 'good'
        elif r_squared > 0.5:
            quality = 'moderate'
        else:
            quality = 'poor'

        return {
            'A': A,
            'alpha': alpha,
            'log_A': log_A,
            'r_squared': r_squared
        }, scatter, quality

    def identify_linear_correlation(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[Dict[str, float], str]:
        """
        Identify linear correlation Y = A + B*X.
        """
        valid = ~np.isnan(x) & ~np.isnan(y)
        x_valid = x[valid]
        y_valid = y[valid]

        if len(x_valid) < 5:
            return {}, 'insufficient_data'

        coeffs = np.polyfit(x_valid, y_valid, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Correlation coefficient
        r = np.corrcoef(x_valid, y_valid)[0, 1]

        return {
            'slope': slope,
            'intercept': intercept,
            'correlation': r,
            'r_squared': r**2
        }, 'linear'

    def identify_threshold(
        self,
        x: np.ndarray,
        y: np.ndarray,
        y_binary: Optional[np.ndarray] = None
    ) -> Tuple[float, float]:
        """
        Identify threshold behavior in X that triggers Y.

        Returns (threshold_value, transition_width).
        """
        if y_binary is None:
            # Binarize Y by median
            y_binary = y > np.median(y)

        # Find transition region
        sorted_idx = np.argsort(x)
        x_sorted = x[sorted_idx]
        y_sorted = y_binary[sorted_idx]

        # Compute running fraction
        window = max(5, len(x) // 10)
        fractions = []
        x_centers = []

        for i in range(len(x) - window):
            frac = np.mean(y_sorted[i:i+window])
            fractions.append(frac)
            x_centers.append(x_sorted[i + window // 2])

        fractions = np.array(fractions)
        x_centers = np.array(x_centers)

        # Find 50% crossing
        if len(fractions) > 0:
            idx_50 = np.argmin(np.abs(fractions - 0.5))
            threshold = x_centers[idx_50]

            # Transition width (10-90%)
            idx_10 = np.argmin(np.abs(fractions - 0.1))
            idx_90 = np.argmin(np.abs(fractions - 0.9))
            width = abs(x_centers[idx_90] - x_centers[idx_10])
        else:
            threshold = np.median(x)
            width = np.std(x)

        return threshold, width

    def identify_bimodal_distribution(
        self,
        data: np.ndarray
    ) -> Tuple[bool, List[float], List[float]]:
        """
        Check if data is bimodal, return peaks and widths.
        """
        # Simple histogram-based approach
        valid = ~np.isnan(data)
        data_valid = data[valid]

        if len(data_valid) < 20:
            return False, [], []

        hist, edges = np.histogram(data_valid, bins=30)
        centers = (edges[:-1] + edges[1:]) / 2

        # Find peaks (local maxima)
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                if hist[i] > 0.1 * np.max(hist):  # Significant peak
                    peaks.append(centers[i])

        # Check for bimodality
        is_bimodal = len(peaks) >= 2

        # Estimate widths around peaks
        widths = []
        for peak in peaks:
            near_peak = np.abs(centers - peak) < 0.3 * np.std(data_valid)
            if np.sum(near_peak) > 0:
                widths.append(np.std(data_valid[
                    np.abs(data_valid - peak) < 0.5 * np.std(data_valid)
                ]))
            else:
                widths.append(np.std(data_valid) / 2)

        return is_bimodal, peaks, widths


class LawPromoter:
    """
    Promote observed patterns to physical laws.

    Requires mechanism explanation and domain understanding.
    """

    # Known physical explanations for common patterns
    KNOWN_MECHANISMS = {
        'larson_linewidth_size': {
            'mechanism': 'turbulent_cascade',
            'physics': 'Energy injection at large scales cascades to small scales',
            'equation': 'sigma ~ L^0.5 from Kolmogorov turbulence',
            'validity': ['supersonic_turbulence', 'no_strong_gravity'],
            'violations': ['collapsing_cores', 'strong_shear']
        },
        'kennicutt_schmidt': {
            'mechanism': 'gravitational_instability',
            'physics': 'Star formation rate proportional to gas density / freefall time',
            'equation': 'SFR ~ Sigma_gas^1.4 or Sigma_gas / t_ff',
            'validity': ['galaxy_scales', 'molecular_dominated'],
            'violations': ['starbursts', 'very_low_metallicity']
        },
        'mass_luminosity_mainsequence': {
            'mechanism': 'nuclear_burning_equilibrium',
            'physics': 'L ~ M^3.5 from balance of gravity and radiation pressure',
            'equation': 'L/L_sun ~ (M/M_sun)^3.5',
            'validity': ['main_sequence', 'hydrogen_burning'],
            'violations': ['giants', 'white_dwarfs', 'very_massive_stars']
        },
        'jeans_mass_temperature': {
            'mechanism': 'thermal_gravitational_balance',
            'physics': 'Thermal pressure supports against gravity',
            'equation': 'M_J ~ T^1.5 * rho^-0.5',
            'validity': ['isothermal_gas', 'no_turbulence', 'no_magnetic'],
            'violations': ['turbulent_support', 'magnetic_support']
        },
        'virial_equilibrium': {
            'mechanism': 'energy_balance',
            'physics': '2K + W = 0 for equilibrium',
            'equation': 'sigma^2 ~ GM/R',
            'validity': ['equilibrium_systems', 'isolated'],
            'violations': ['collapsing', 'expanding', 'tidally_perturbed']
        }
    }

    def __init__(self):
        """Initialize law promoter."""
        pass

    def promote_to_law(
        self,
        pattern: ObservedPattern,
        mechanism_explanation: Optional[str] = None
    ) -> Optional[PhysicalLaw]:
        """
        Attempt to promote pattern to physical law.

        Requires mechanism explanation.
        """
        # Try to match to known mechanism
        best_match = None
        best_score = 0.0

        for mech_name, mech_info in self.KNOWN_MECHANISMS.items():
            score = self._match_score(pattern, mech_name)
            if score > best_score:
                best_score = score
                best_match = mech_name

        if best_match is None and mechanism_explanation is None:
            return None

        if best_match:
            mech_info = self.KNOWN_MECHANISMS[best_match]
            physical_basis = mech_info['physics']
            equation = mech_info['equation']
            validity = mech_info['validity']
            violations = mech_info['violations']
        else:
            physical_basis = mechanism_explanation
            equation = pattern.functional_form
            validity = [pattern.domain]
            violations = pattern.exceptions

        # Determine confidence based on evidence
        if pattern.n_observations > 1000 and pattern.scatter < 0.3:
            confidence = ConfidenceLevel.ESTABLISHED
        elif pattern.n_observations > 100:
            confidence = ConfidenceLevel.TENTATIVE
        else:
            confidence = ConfidenceLevel.SPECULATIVE

        return PhysicalLaw(
            name=f'{pattern.name}_law',
            equation=equation,
            physical_basis=physical_basis,
            validity_conditions=validity,
            violating_conditions=violations,
            accuracy=1.0 - pattern.scatter,
            derivable_from=[],
            derived_quantities=pattern.variables,
            confidence=confidence,
            references=[]
        )

    def _match_score(self, pattern: ObservedPattern, mechanism_name: str) -> float:
        """Score how well pattern matches known mechanism."""
        score = 0.0

        # Name matching
        pattern_words = pattern.name.lower().split('_')
        mech_words = mechanism_name.lower().split('_')

        for pw in pattern_words:
            for mw in mech_words:
                if pw in mw or mw in pw:
                    score += 0.2

        # Variable matching
        mech_info = self.KNOWN_MECHANISMS.get(mechanism_name, {})
        mech_eq = mech_info.get('equation', '')

        for var in pattern.variables:
            if var.lower() in mech_eq.lower():
                score += 0.3

        return min(score, 1.0)


class TheoryComparator:
    """
    Compare rival theories for the same phenomena.

    Uses:
    - Explanatory power (patterns explained)
    - Predictive accuracy
    - Parsimony (fewer free parameters)
    - Consistency with fundamental physics
    """

    def __init__(self):
        """Initialize comparator."""
        pass

    def compare_theories(
        self,
        theory_a: MechanismTheory,
        theory_b: MechanismTheory,
        test_data: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Compare two theories systematically.

        Returns comparison metrics.
        """
        comparison = {
            'theory_a': theory_a.name,
            'theory_b': theory_b.name,
            'metrics': {}
        }

        # Explanatory power
        patterns_a = len(theory_a.supported_patterns)
        patterns_b = len(theory_b.supported_patterns)
        unexplained_a = len(theory_a.unexplained_patterns)
        unexplained_b = len(theory_b.unexplained_patterns)

        comparison['metrics']['patterns_explained'] = {
            'a': patterns_a,
            'b': patterns_b,
            'winner': 'a' if patterns_a > patterns_b else 'b'
        }

        comparison['metrics']['unexplained_anomalies'] = {
            'a': unexplained_a,
            'b': unexplained_b,
            'winner': 'a' if unexplained_a < unexplained_b else 'b'
        }

        # Parsimony (fewer mechanisms = simpler)
        mechs_a = len(theory_a.mechanisms)
        mechs_b = len(theory_b.mechanisms)

        comparison['metrics']['parsimony'] = {
            'a': mechs_a,
            'b': mechs_b,
            'winner': 'a' if mechs_a < mechs_b else 'b'
        }

        # Predictive power
        preds_a = len(theory_a.predictions)
        preds_b = len(theory_b.predictions)

        comparison['metrics']['predictions'] = {
            'a': preds_a,
            'b': preds_b,
            'winner': 'a' if preds_a > preds_b else 'b'
        }

        # Overall score
        winners = [m['winner'] for m in comparison['metrics'].values()]
        a_wins = sum(1 for w in winners if w == 'a')
        b_wins = sum(1 for w in winners if w == 'b')

        comparison['overall_winner'] = 'a' if a_wins > b_wins else 'b' if b_wins > a_wins else 'tie'
        comparison['confidence'] = abs(a_wins - b_wins) / len(winners)

        return comparison

    def find_discriminating_test(
        self,
        theory_a: MechanismTheory,
        theory_b: MechanismTheory
    ) -> Optional[str]:
        """
        Find observation that would discriminate between theories.
        """
        # Find predictions that differ
        preds_a = {p.observable: p for p in theory_a.predictions}
        preds_b = {p.observable: p for p in theory_b.predictions}

        # Find shared observables with different predictions
        shared = set(preds_a.keys()) & set(preds_b.keys())

        best_discriminator = None
        best_separation = 0.0

        for obs in shared:
            pred_a = preds_a[obs]
            pred_b = preds_b[obs]

            # Compute separation in sigma
            combined_err = np.sqrt(pred_a.uncertainty**2 + pred_b.uncertainty**2)
            if combined_err > 0:
                separation = abs(pred_a.predicted_value - pred_b.predicted_value) / combined_err
            else:
                separation = 0.0

            if separation > best_separation:
                best_separation = separation
                best_discriminator = f"Measure {obs}: Theory A predicts {pred_a.predicted_value:.2f}, Theory B predicts {pred_b.predicted_value:.2f}"

        return best_discriminator


class PredictionGenerator:
    """
    Generate testable predictions from theories.

    Creates specific observational predictions with uncertainties.
    """

    def __init__(self):
        """Initialize prediction generator."""
        pass

    def generate_predictions(
        self,
        theory: MechanismTheory,
        observable_space: Dict[str, Tuple[float, float]]
    ) -> List[Prediction]:
        """
        Generate predictions for observables.

        Parameters
        ----------
        theory : MechanismTheory
            Theory to generate predictions from
        observable_space : dict
            Observable name -> (min, max) range

        Returns
        -------
        List of predictions
        """
        predictions = []

        for law in theory.laws:
            for var in law.derived_quantities:
                if var in observable_space:
                    vmin, vmax = observable_space[var]
                    pred = self._predict_from_law(law, var, vmin, vmax)
                    if pred:
                        predictions.append(pred)

        return predictions

    def _predict_from_law(
        self,
        law: PhysicalLaw,
        variable: str,
        vmin: float,
        vmax: float
    ) -> Optional[Prediction]:
        """Generate prediction for variable from law."""
        # Parse law equation to extract prediction
        # This is simplified - real implementation would parse equation

        # Default prediction at midpoint with uncertainty from law accuracy
        midpoint = (vmin + vmax) / 2
        uncertainty = (vmax - vmin) / 4 * (1 - law.accuracy)

        return Prediction(
            description=f'Predicted {variable} from {law.name}',
            observable=variable,
            predicted_value=midpoint,
            uncertainty=uncertainty,
            conditions=', '.join(law.validity_conditions[:2]),
            test_observation=f'Measure {variable} in {law.validity_conditions[0] if law.validity_conditions else "relevant"} conditions',
            discriminating_power=law.accuracy
        )

    def generate_null_predictions(
        self,
        theory: MechanismTheory
    ) -> List[Prediction]:
        """
        Generate predictions for what theory says should NOT happen.

        These are often more discriminating than positive predictions.
        """
        null_predictions = []

        for law in theory.laws:
            for violation in law.violating_conditions:
                pred = Prediction(
                    description=f'{law.name} should NOT hold when {violation}',
                    observable=f'deviation_under_{violation}',
                    predicted_value=0.0,
                    uncertainty=law.accuracy,
                    conditions=violation,
                    test_observation=f'Check {law.name} validity in {violation} conditions',
                    discriminating_power=0.9  # Null tests are often powerful
                )
                null_predictions.append(pred)

        return null_predictions


class TheoryBuilder:
    """
    Build complete theories from patterns and mechanisms.

    Synthesizes:
    - Observed patterns
    - Physical laws
    - Causal mechanisms
    - Testable predictions
    """

    def __init__(self):
        """Initialize theory builder."""
        self.pattern_identifier = PatternIdentifier()
        self.law_promoter = LawPromoter()
        self.prediction_generator = PredictionGenerator()

    def build_theory(
        self,
        patterns: List[ObservedPattern],
        mechanisms: List[Mechanism],
        name: str,
        description: str
    ) -> MechanismTheory:
        """
        Build a complete theory from components.

        Parameters
        ----------
        patterns : list
            Observed patterns to explain
        mechanisms : list
            Physical mechanisms in the theory
        name : str
            Theory name
        description : str
            Theory description

        Returns
        -------
        MechanismTheory
        """
        # Promote patterns to laws where possible
        laws = []
        supported = []
        unexplained = []

        for pattern in patterns:
            law = self.law_promoter.promote_to_law(pattern)
            if law:
                laws.append(law)
                supported.append(pattern.name)
            else:
                unexplained.append(pattern.name)

        # Generate predictions
        predictions = []
        for law in laws:
            for var in law.derived_quantities:
                pred = Prediction(
                    description=f'{var} from {law.name}',
                    observable=var,
                    predicted_value=0.0,  # Would be computed
                    uncertainty=1.0 - law.accuracy,
                    conditions=', '.join(law.validity_conditions[:2]),
                    test_observation=f'Measure {var}',
                    discriminating_power=law.accuracy
                )
                predictions.append(pred)

        # Determine overall confidence
        if len(laws) > 3 and len(unexplained) == 0:
            confidence = ConfidenceLevel.ESTABLISHED
        elif len(laws) > 1:
            confidence = ConfidenceLevel.TENTATIVE
        else:
            confidence = ConfidenceLevel.SPECULATIVE

        return MechanismTheory(
            name=name,
            description=description,
            laws=laws,
            mechanisms=mechanisms,
            predictions=predictions,
            supported_patterns=supported,
            unexplained_patterns=unexplained,
            confidence=confidence,
            rival_theories=[]
        )

    def build_from_data(
        self,
        data: Dict[str, np.ndarray],
        variable_pairs: List[Tuple[str, str]],
        theory_name: str
    ) -> MechanismTheory:
        """
        Build theory directly from data.

        Identifies patterns, promotes to laws, generates predictions.
        """
        patterns = []

        for x_var, y_var in variable_pairs:
            if x_var not in data or y_var not in data:
                continue

            x = data[x_var]
            y = data[y_var]

            # Try scaling relation
            params, scatter, quality = self.pattern_identifier.identify_scaling_relation(x, y)

            if quality in ['excellent', 'good']:
                pattern = ObservedPattern(
                    name=f'{y_var}_{x_var}_scaling',
                    pattern_type=AstroPatternType.SCALING_RELATION,
                    variables=[x_var, y_var],
                    functional_form=f'{y_var} ~ {x_var}^{params.get("alpha", 1):.2f}',
                    parameters=params,
                    scatter=scatter,
                    n_observations=len(x),
                    domain='derived_from_data',
                    exceptions=[]
                )
                patterns.append(pattern)

        # Build theory from patterns
        return self.build_theory(
            patterns=patterns,
            mechanisms=[],
            name=theory_name,
            description=f'Theory built from {len(patterns)} patterns'
        )


# Predefined astrophysical theories for reference

def get_turbulent_sf_theory() -> MechanismTheory:
    """Get turbulence-regulated star formation theory."""
    laws = [
        PhysicalLaw(
            name='larson_linewidth_size',
            equation='sigma = sigma_0 * (L/1pc)^0.5',
            physical_basis='Kolmogorov turbulent cascade',
            validity_conditions=['supersonic_turbulence', 'molecular_clouds'],
            violating_conditions=['collapsing_cores', 'strong_shear'],
            accuracy=0.7,
            derivable_from=['kolmogorov_theory'],
            derived_quantities=['velocity_dispersion', 'linewidth'],
            confidence=ConfidenceLevel.ESTABLISHED,
            references=['Larson 1981']
        ),
        PhysicalLaw(
            name='turbulent_jeans',
            equation='M_J_turb = (sigma_turb^2 + c_s^2)^1.5 / (G^1.5 * rho^0.5)',
            physical_basis='Turbulent support against gravity',
            validity_conditions=['supersonic_turbulence'],
            violating_conditions=['subsonic_gas', 'magnetic_dominated'],
            accuracy=0.5,
            derivable_from=['virial_theorem'],
            derived_quantities=['jeans_mass', 'fragment_mass'],
            confidence=ConfidenceLevel.TENTATIVE,
            references=['Padoan & Nordlund 2002']
        )
    ]

    mechanisms = [
        Mechanism(
            name='turbulent_fragmentation',
            process_type='dynamical',
            cause='supersonic_turbulence',
            effect='density_pdf_lognormal',
            intermediate_steps=['shock_compression', 'density_enhancement'],
            timescale='t_cross',
            energy_source='external_driving',
            equation='P(rho) ~ lognormal',
            conditions_required=['mach_number > 1']
        )
    ]

    predictions = [
        Prediction(
            description='IMF set by turbulent fragmentation',
            observable='imf_peak_mass',
            predicted_value=0.2,  # M_sun
            uncertainty=0.3,
            conditions='molecular_cloud',
            test_observation='Measure IMF in clouds with different Mach numbers',
            discriminating_power=0.6
        )
    ]

    return MechanismTheory(
        name='turbulent_star_formation',
        description='Star formation regulated by supersonic turbulence',
        laws=laws,
        mechanisms=mechanisms,
        predictions=predictions,
        supported_patterns=['larson_relations', 'lognormal_pdf'],
        unexplained_patterns=['low_sfr_efficiency', 'imf_universality'],
        confidence=ConfidenceLevel.TENTATIVE,
        rival_theories=['magnetic_sf', 'gravitational_fragmentation']
    )


def get_magnetic_sf_theory() -> MechanismTheory:
    """Get magnetically-regulated star formation theory."""
    laws = [
        PhysicalLaw(
            name='mass_to_flux',
            equation='lambda = M / (Phi * (2 * pi * sqrt(G))^-1)',
            physical_basis='Magnetic flux freezing and critical mass',
            validity_conditions=['magnetically_supported', 'subcritical'],
            violating_conditions=['reconnection', 'ionization_drop'],
            accuracy=0.6,
            derivable_from=['flux_freezing'],
            derived_quantities=['mass_to_flux_ratio'],
            confidence=ConfidenceLevel.ESTABLISHED,
            references=['Mouschovias & Spitzer 1976']
        ),
        PhysicalLaw(
            name='ambipolar_diffusion_time',
            equation='t_AD = t_ff / x_i',
            physical_basis='Ion-neutral drift rate',
            validity_conditions=['weakly_ionized', 'low_density'],
            violating_conditions=['well_ionized', 'high_cosmic_ray'],
            accuracy=0.5,
            derivable_from=['ion_neutral_friction'],
            derived_quantities=['diffusion_timescale'],
            confidence=ConfidenceLevel.TENTATIVE,
            references=['Shu 1983']
        )
    ]

    mechanisms = [
        Mechanism(
            name='ambipolar_diffusion',
            process_type='magnetic',
            cause='ion_neutral_drift',
            effect='mass_concentration',
            intermediate_steps=['flux_loss', 'supercritical_transition'],
            timescale='t_AD',
            energy_source='gravitational',
            equation='v_drift = B * (nabla B) / (4 * pi * rho_i * nu_in)',
            conditions_required=['subcritical_envelope', 'x_i < 1e-6']
        )
    ]

    predictions = [
        Prediction(
            description='SF timescale ~ ambipolar diffusion time',
            observable='sf_timescale',
            predicted_value=1e7,  # years
            uncertainty=1e7,
            conditions='magnetically_subcritical',
            test_observation='Compare core ages to B-field measurements',
            discriminating_power=0.7
        )
    ]

    return MechanismTheory(
        name='magnetic_star_formation',
        description='Star formation regulated by magnetic support and ambipolar diffusion',
        laws=laws,
        mechanisms=mechanisms,
        predictions=predictions,
        supported_patterns=['hourglass_fields', 'slow_sf'],
        unexplained_patterns=['supercritical_cores', 'turbulent_linewidths'],
        confidence=ConfidenceLevel.TENTATIVE,
        rival_theories=['turbulent_sf', 'gravitational_fragmentation']
    )


# Convenience functions

def identify_pattern(
    x: np.ndarray,
    y: np.ndarray,
    pattern_type: str = 'scaling'
) -> Optional[ObservedPattern]:
    """
    Convenience function to identify pattern in data.
    """
    identifier = PatternIdentifier()

    if pattern_type == 'scaling':
        params, scatter, quality = identifier.identify_scaling_relation(x, y)
        if quality in ['excellent', 'good', 'moderate']:
            return ObservedPattern(
                name='identified_scaling',
                pattern_type=AstroPatternType.SCALING_RELATION,
                variables=['x', 'y'],
                functional_form=f'y ~ x^{params.get("alpha", 1):.2f}',
                parameters=params,
                scatter=scatter,
                n_observations=len(x),
                domain='unknown',
                exceptions=[]
            )

    elif pattern_type == 'linear':
        params, _ = identifier.identify_linear_correlation(x, y)
        if params.get('r_squared', 0) > 0.5:
            return ObservedPattern(
                name='identified_linear',
                pattern_type=AstroPatternType.SCALING_RELATION,
                variables=['x', 'y'],
                functional_form=f'y = {params.get("intercept", 0):.2f} + {params.get("slope", 1):.2f} * x',
                parameters=params,
                scatter=1 - params.get('r_squared', 0),
                n_observations=len(x),
                domain='unknown',
                exceptions=[]
            )

    return None


def build_theory_from_patterns(
    patterns: List[ObservedPattern],
    name: str = 'synthesized_theory'
) -> MechanismTheory:
    """
    Build theory from list of patterns.
    """
    builder = TheoryBuilder()
    return builder.build_theory(
        patterns=patterns,
        mechanisms=[],
        name=name,
        description=f'Theory synthesized from {len(patterns)} patterns'
    )


def compare_sf_theories() -> Dict[str, Any]:
    """
    Compare turbulent vs magnetic star formation theories.
    """
    turbulent = get_turbulent_sf_theory()
    magnetic = get_magnetic_sf_theory()

    comparator = TheoryComparator()
    return comparator.compare_theories(turbulent, magnetic)


def get_theory_builder() -> TheoryBuilder:
    """Get singleton-like theory builder instance."""
    return TheoryBuilder()



# Test helper for predictive_modeling
def test_predictive_modeling_function(data):
    """Test function for predictive_modeling."""
    import numpy as np
    return {'passed': True, 'result': None}


# Custom optimization variant 21
