"""
Cross-Survey Knowledge Fusion for STAN V42

Combines information from heterogeneous astronomical surveys:
- Multi-wavelength data fusion (radio, IR, optical, UV, X-ray)
- Cross-catalog matching with uncertainty
- Joint posterior inference from multiple sources
- Tension detection between surveys
- Optimal weighting for combined constraints

This enables stronger constraints than any single survey alone,
while properly accounting for systematics and correlations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple, Set
from enum import Enum
import math
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class WavelengthBand(Enum):
    """Electromagnetic wavelength bands."""
    RADIO = "radio"           # > 1 mm
    MILLIMETER = "millimeter" # 1mm - 0.3mm
    SUBMILLIMETER = "submm"   # 300 - 100 μm
    FAR_INFRARED = "fir"      # 100 - 30 μm
    MID_INFRARED = "mir"      # 30 - 3 μm
    NEAR_INFRARED = "nir"     # 3 - 0.7 μm
    OPTICAL = "optical"       # 700 - 400 nm
    ULTRAVIOLET = "uv"        # 400 - 10 nm
    X_RAY = "xray"            # 10nm - 0.01nm
    GAMMA_RAY = "gamma"       # < 0.01 nm
    GRAVITATIONAL = "gw"      # Gravitational waves
    NEUTRINO = "neutrino"     # Neutrino observations


class SurveyType(Enum):
    """Types of astronomical surveys."""
    PHOTOMETRIC = "photometric"     # Imaging
    SPECTROSCOPIC = "spectroscopic" # Spectra
    ASTROMETRIC = "astrometric"     # Positions/motions
    POLARIMETRIC = "polarimetric"   # Polarization
    TIME_DOMAIN = "time_domain"     # Time series
    INTERFEROMETRIC = "interferometric"  # High resolution


class MatchQuality(Enum):
    """Quality of cross-match."""
    CERTAIN = "certain"      # Unambiguous match
    PROBABLE = "probable"    # High probability match
    POSSIBLE = "possible"    # Uncertain match
    AMBIGUOUS = "ambiguous"  # Multiple possible matches
    NO_MATCH = "no_match"    # No counterpart found


@dataclass
class Survey:
    """Metadata for an astronomical survey."""
    name: str
    wavelength_band: WavelengthBand
    survey_type: SurveyType
    angular_resolution: float  # arcsec
    positional_accuracy: float  # arcsec (1σ)
    depth: float  # Limiting magnitude or flux
    coverage_area: float  # square degrees
    systematic_uncertainty: float  # fractional
    calibration_quality: float  # 0-1 scale
    catalog_size: int
    epoch: float  # MJD of typical observation


@dataclass
class Source:
    """A single astronomical source from a survey."""
    source_id: str
    survey_name: str
    ra: float  # degrees
    dec: float  # degrees
    ra_error: float  # arcsec
    dec_error: float  # arcsec
    measurements: Dict[str, float]  # parameter_name -> value
    uncertainties: Dict[str, float]  # parameter_name -> 1σ error
    flags: Dict[str, Any] = field(default_factory=dict)
    epoch: Optional[float] = None


@dataclass
class CrossMatch:
    """Cross-match between sources from different surveys."""
    match_id: str
    sources: List[Source]
    surveys: List[str]
    match_quality: MatchQuality
    separation: float  # arcsec
    match_probability: float
    false_positive_probability: float


@dataclass
class FusedSource:
    """Combined source from multiple surveys."""
    fused_id: str
    cross_match: CrossMatch
    combined_position: Tuple[float, float, float, float]  # ra, dec, ra_err, dec_err
    combined_measurements: Dict[str, float]
    combined_uncertainties: Dict[str, float]
    measurement_sources: Dict[str, List[str]]  # parameter -> contributing surveys
    tension_flags: Dict[str, float]  # parameter -> tension significance
    reliability: float


@dataclass
class JointPosterior:
    """Joint posterior from multiple surveys."""
    parameters: List[str]
    means: Dict[str, float]
    covariance: Dict[str, Dict[str, float]]
    contributing_surveys: List[str]
    individual_posteriors: Dict[str, Dict[str, Tuple[float, float]]]  # survey -> param -> (mean, std)
    tension_statistics: Dict[str, float]
    effective_sample_size: float


# ============================================================================
# Cross-Matcher
# ============================================================================

class CrossMatcher:
    """
    Matches sources across different surveys.
    """

    def __init__(self,
                 base_matching_radius: float = 3.0,
                 probability_threshold: float = 0.5):
        """
        Args:
            base_matching_radius: Base matching radius in arcsec
            probability_threshold: Minimum probability for match
        """
        self.base_matching_radius = base_matching_radius
        self.probability_threshold = probability_threshold
        self._match_counter = 0

    def compute_matching_radius(self,
                               source1: Source,
                               source2: Source,
                               n_sigma: float = 3.0) -> float:
        """
        Compute position-uncertainty-aware matching radius.
        """
        # Combined positional uncertainty
        combined_error = math.sqrt(
            source1.ra_error ** 2 + source1.dec_error ** 2 +
            source2.ra_error ** 2 + source2.dec_error ** 2
        )

        return max(self.base_matching_radius, n_sigma * combined_error)

    def compute_separation(self,
                          source1: Source,
                          source2: Source) -> float:
        """
        Compute angular separation in arcsec.
        """
        # Convert to radians
        ra1 = math.radians(source1.ra)
        dec1 = math.radians(source1.dec)
        ra2 = math.radians(source2.ra)
        dec2 = math.radians(source2.dec)

        # Haversine formula
        dlat = dec2 - dec1
        dlon = ra2 - ra1

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(dec1) * math.cos(dec2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Convert to arcsec
        return math.degrees(c) * 3600

    def compute_match_probability(self,
                                  separation: float,
                                  positional_error: float,
                                  source_density: float) -> float:
        """
        Compute probability that match is correct (Bayesian matching).

        Uses likelihood ratio between true association and chance alignment.
        """
        if positional_error <= 0:
            positional_error = 1.0

        # Likelihood of true match (Rayleigh distribution)
        true_likelihood = (separation / positional_error ** 2 *
                          math.exp(-separation ** 2 / (2 * positional_error ** 2)))

        # Likelihood of chance alignment (uniform within search area)
        # source_density is per square arcsec
        chance_likelihood = source_density

        # Prior: assume 50/50 before data
        prior_true = 0.5

        # Posterior probability of true match
        posterior = (true_likelihood * prior_true /
                    (true_likelihood * prior_true + chance_likelihood * (1 - prior_true)))

        return min(1.0, max(0.0, posterior))

    def match_catalogs(self,
                      catalog1: List[Source],
                      catalog2: List[Source],
                      survey1_density: float = 0.01,
                      survey2_density: float = 0.01) -> List[CrossMatch]:
        """
        Cross-match two catalogs.

        Args:
            catalog1, catalog2: Lists of Source objects
            survey1_density, survey2_density: Source density per square arcsec
        """
        matches = []

        for source1 in catalog1:
            candidates = []

            for source2 in catalog2:
                separation = self.compute_separation(source1, source2)
                matching_radius = self.compute_matching_radius(source1, source2)

                if separation <= matching_radius:
                    positional_error = math.sqrt(
                        source1.ra_error ** 2 + source1.dec_error ** 2 +
                        source2.ra_error ** 2 + source2.dec_error ** 2
                    )

                    probability = self.compute_match_probability(
                        separation, positional_error, survey2_density
                    )

                    candidates.append((source2, separation, probability))

            # Select best match
            if candidates:
                candidates.sort(key=lambda x: x[2], reverse=True)
                best_source, best_sep, best_prob = candidates[0]

                if best_prob >= self.probability_threshold:
                    # Determine match quality
                    if best_prob > 0.95 and len(candidates) == 1:
                        quality = MatchQuality.CERTAIN
                    elif best_prob > 0.8:
                        quality = MatchQuality.PROBABLE
                    elif len(candidates) > 1 and candidates[1][2] > 0.3:
                        quality = MatchQuality.AMBIGUOUS
                    else:
                        quality = MatchQuality.POSSIBLE

                    match = CrossMatch(
                        match_id=self._generate_match_id(),
                        sources=[source1, best_source],
                        surveys=[source1.survey_name, best_source.survey_name],
                        match_quality=quality,
                        separation=best_sep,
                        match_probability=best_prob,
                        false_positive_probability=1 - best_prob
                    )
                    matches.append(match)

        return matches

    def multi_catalog_match(self,
                           catalogs: Dict[str, List[Source]],
                           densities: Dict[str, float]) -> List[CrossMatch]:
        """
        Match across multiple catalogs.
        """
        all_matches = []
        survey_names = list(catalogs.keys())

        # Pairwise matching
        for i in range(len(survey_names)):
            for j in range(i + 1, len(survey_names)):
                survey1 = survey_names[i]
                survey2 = survey_names[j]

                matches = self.match_catalogs(
                    catalogs[survey1],
                    catalogs[survey2],
                    densities.get(survey1, 0.01),
                    densities.get(survey2, 0.01)
                )
                all_matches.extend(matches)

        # Merge matches that share sources
        merged = self._merge_matches(all_matches)

        return merged

    def _merge_matches(self, matches: List[CrossMatch]) -> List[CrossMatch]:
        """Merge matches that share sources into multi-survey matches."""
        # Build graph of connected sources
        source_to_matches = defaultdict(list)

        for match in matches:
            for source in match.sources:
                source_to_matches[source.source_id].append(match)

        # Find connected components
        visited = set()
        merged_matches = []

        for match in matches:
            if match.match_id in visited:
                continue

            # BFS to find all connected matches
            component_matches = []
            queue = [match]

            while queue:
                current = queue.pop(0)
                if current.match_id in visited:
                    continue

                visited.add(current.match_id)
                component_matches.append(current)

                # Find connected matches
                for source in current.sources:
                    for connected in source_to_matches[source.source_id]:
                        if connected.match_id not in visited:
                            queue.append(connected)

            # Merge component into single match
            if component_matches:
                all_sources = []
                all_surveys = set()
                max_sep = 0.0
                min_prob = 1.0

                for cm in component_matches:
                    for source in cm.sources:
                        if source.source_id not in [s.source_id for s in all_sources]:
                            all_sources.append(source)
                            all_surveys.add(source.survey_name)
                    max_sep = max(max_sep, cm.separation)
                    min_prob = min(min_prob, cm.match_probability)

                merged = CrossMatch(
                    match_id=self._generate_match_id(),
                    sources=all_sources,
                    surveys=list(all_surveys),
                    match_quality=min(cm.match_quality for cm in component_matches),
                    separation=max_sep,
                    match_probability=min_prob,
                    false_positive_probability=1 - min_prob
                )
                merged_matches.append(merged)

        return merged_matches

    def _generate_match_id(self) -> str:
        """Generate unique match ID."""
        self._match_counter += 1
        return f"XMATCH_{self._match_counter:08d}"


# ============================================================================
# Measurement Combiner
# ============================================================================

class MeasurementCombiner:
    """
    Combines measurements from different surveys.
    """

    def __init__(self,
                 tension_threshold: float = 3.0,
                 correlation_threshold: float = 0.1):
        self.tension_threshold = tension_threshold
        self.correlation_threshold = correlation_threshold
        self._fusion_counter = 0

    def combine_positions(self,
                         sources: List[Source]) -> Tuple[float, float, float, float]:
        """
        Combine positions using inverse variance weighting.

        Returns (ra, dec, ra_error, dec_error)
        """
        if not sources:
            return (0.0, 0.0, 999.0, 999.0)

        if len(sources) == 1:
            s = sources[0]
            return (s.ra, s.dec, s.ra_error, s.dec_error)

        # Inverse variance weights
        ra_weights = []
        dec_weights = []
        ra_values = []
        dec_values = []

        for s in sources:
            if s.ra_error > 0:
                ra_weights.append(1.0 / s.ra_error ** 2)
                ra_values.append(s.ra)
            if s.dec_error > 0:
                dec_weights.append(1.0 / s.dec_error ** 2)
                dec_values.append(s.dec)

        # Weighted means
        total_ra_weight = sum(ra_weights)
        total_dec_weight = sum(dec_weights)

        if total_ra_weight > 0:
            combined_ra = sum(w * v for w, v in zip(ra_weights, ra_values)) / total_ra_weight
            combined_ra_err = 1.0 / math.sqrt(total_ra_weight)
        else:
            combined_ra = sources[0].ra
            combined_ra_err = sources[0].ra_error

        if total_dec_weight > 0:
            combined_dec = sum(w * v for w, v in zip(dec_weights, dec_values)) / total_dec_weight
            combined_dec_err = 1.0 / math.sqrt(total_dec_weight)
        else:
            combined_dec = sources[0].dec
            combined_dec_err = sources[0].dec_error

        return (combined_ra, combined_dec, combined_ra_err, combined_dec_err)

    def combine_measurements(self,
                            sources: List[Source],
                            surveys: Optional[Dict[str, Survey]] = None) -> Tuple[Dict[str, float],
                                                                                   Dict[str, float],
                                                                                   Dict[str, List[str]],
                                                                                   Dict[str, float]]:
        """
        Combine measurements using optimal weighting.

        Returns:
            - combined_measurements: parameter -> combined value
            - combined_uncertainties: parameter -> combined uncertainty
            - measurement_sources: parameter -> list of contributing surveys
            - tensions: parameter -> tension significance (sigma)
        """
        combined = {}
        uncertainties = {}
        sources_dict = {}
        tensions = {}

        # Collect all measurements
        all_measurements = defaultdict(list)  # param -> [(value, error, survey)]

        for source in sources:
            for param, value in source.measurements.items():
                error = source.uncertainties.get(param, float('inf'))
                if error < float('inf'):
                    all_measurements[param].append((value, error, source.survey_name))

        # Combine each parameter
        for param, measurements in all_measurements.items():
            if not measurements:
                continue

            values = [m[0] for m in measurements]
            errors = [m[1] for m in measurements]
            survey_names = [m[2] for m in measurements]

            # Add systematic uncertainties from surveys if available
            if surveys:
                for i, survey_name in enumerate(survey_names):
                    if survey_name in surveys:
                        sys = surveys[survey_name].systematic_uncertainty
                        errors[i] = math.sqrt(errors[i] ** 2 + (values[i] * sys) ** 2)

            # Inverse variance weighting
            weights = [1.0 / e ** 2 if e > 0 else 0.0 for e in errors]
            total_weight = sum(weights)

            if total_weight > 0:
                combined[param] = sum(w * v for w, v in zip(weights, values)) / total_weight
                uncertainties[param] = 1.0 / math.sqrt(total_weight)
            else:
                combined[param] = values[0]
                uncertainties[param] = errors[0]

            sources_dict[param] = survey_names

            # Check for tension
            if len(measurements) > 1:
                tension = self._compute_tension(values, errors)
                tensions[param] = tension

        return combined, uncertainties, sources_dict, tensions

    def _compute_tension(self, values: List[float], errors: List[float]) -> float:
        """
        Compute tension between measurements.

        Returns chi-squared per degree of freedom equivalent.
        """
        n = len(values)
        if n < 2:
            return 0.0

        # Weighted mean
        weights = [1.0 / e ** 2 if e > 0 else 0.0 for e in errors]
        total_weight = sum(weights)

        if total_weight == 0:
            return 0.0

        weighted_mean = sum(w * v for w, v in zip(weights, values)) / total_weight

        # Chi-squared
        chi_sq = sum(((v - weighted_mean) / e) ** 2
                    for v, e in zip(values, errors) if e > 0)

        # Convert to sigma equivalent
        dof = n - 1
        if dof > 0:
            # Approximate sigma from chi-squared
            return math.sqrt(max(0, chi_sq - dof)) if chi_sq > dof else 0.0

        return 0.0

    def fuse_sources(self,
                    cross_match: CrossMatch,
                    surveys: Optional[Dict[str, Survey]] = None) -> FusedSource:
        """
        Create fused source from cross-match.
        """
        sources = cross_match.sources

        # Combine position
        combined_pos = self.combine_positions(sources)

        # Combine measurements
        combined, uncertainties, sources_dict, tensions = self.combine_measurements(
            sources, surveys
        )

        # Compute reliability
        reliability = self._compute_reliability(cross_match, tensions)

        return FusedSource(
            fused_id=self._generate_fused_id(),
            cross_match=cross_match,
            combined_position=combined_pos,
            combined_measurements=combined,
            combined_uncertainties=uncertainties,
            measurement_sources=sources_dict,
            tension_flags=tensions,
            reliability=reliability
        )

    def _compute_reliability(self,
                            cross_match: CrossMatch,
                            tensions: Dict[str, float]) -> float:
        """Compute overall reliability score."""
        # Start with match probability
        reliability = cross_match.match_probability

        # Penalize high tensions
        if tensions:
            max_tension = max(tensions.values())
            if max_tension > self.tension_threshold:
                reliability *= math.exp(-(max_tension - self.tension_threshold) / 2)

        # Penalize ambiguous matches
        if cross_match.match_quality == MatchQuality.AMBIGUOUS:
            reliability *= 0.7
        elif cross_match.match_quality == MatchQuality.POSSIBLE:
            reliability *= 0.85

        return reliability

    def _generate_fused_id(self) -> str:
        """Generate unique fused source ID."""
        self._fusion_counter += 1
        return f"FUSED_{self._fusion_counter:08d}"


# ============================================================================
# Joint Posterior Calculator
# ============================================================================

class JointPosteriorCalculator:
    """
    Computes joint posteriors from multiple surveys.
    """

    def __init__(self,
                 correlation_model: str = "independent"):
        """
        Args:
            correlation_model: How to model survey correlations
                - "independent": Assume surveys are independent
                - "conservative": Add extra correlation term
        """
        self.correlation_model = correlation_model

    def compute_joint_posterior(self,
                               sources: List[Source],
                               parameters: List[str],
                               surveys: Optional[Dict[str, Survey]] = None) -> JointPosterior:
        """
        Compute joint posterior distribution.
        """
        # Collect individual posteriors
        individual = {}  # survey -> param -> (mean, std)

        for source in sources:
            survey_posteriors = {}
            for param in parameters:
                if param in source.measurements:
                    mean = source.measurements[param]
                    std = source.uncertainties.get(param, float('inf'))

                    # Add systematic if available
                    if surveys and source.survey_name in surveys:
                        sys = surveys[source.survey_name].systematic_uncertainty
                        std = math.sqrt(std ** 2 + (mean * sys) ** 2)

                    survey_posteriors[param] = (mean, std)

            if survey_posteriors:
                individual[source.survey_name] = survey_posteriors

        # Compute joint means and covariance
        means = {}
        covariance = {p1: {p2: 0.0 for p2 in parameters} for p1 in parameters}
        contributing_surveys = list(individual.keys())

        for param in parameters:
            # Collect measurements for this parameter
            values = []
            variances = []

            for survey, posteriors in individual.items():
                if param in posteriors:
                    mean, std = posteriors[param]
                    values.append(mean)
                    variances.append(std ** 2)

            if values:
                # Inverse variance weighting
                weights = [1.0 / v if v > 0 else 0.0 for v in variances]
                total_weight = sum(weights)

                if total_weight > 0:
                    means[param] = sum(w * v for w, v in zip(weights, values)) / total_weight
                    covariance[param][param] = 1.0 / total_weight
                else:
                    means[param] = values[0]
                    covariance[param][param] = variances[0]
            else:
                means[param] = 0.0
                covariance[param][param] = float('inf')

        # Compute tension statistics
        tension_stats = self._compute_tension_statistics(individual, means, parameters)

        # Effective sample size
        ess = self._compute_effective_sample_size(individual, parameters)

        return JointPosterior(
            parameters=parameters,
            means=means,
            covariance=covariance,
            contributing_surveys=contributing_surveys,
            individual_posteriors=individual,
            tension_statistics=tension_stats,
            effective_sample_size=ess
        )

    def _compute_tension_statistics(self,
                                   individual: Dict[str, Dict[str, Tuple[float, float]]],
                                   joint_means: Dict[str, float],
                                   parameters: List[str]) -> Dict[str, float]:
        """Compute tension between surveys for each parameter."""
        tensions = {}

        for param in parameters:
            chi_sq = 0.0
            n_surveys = 0

            for survey, posteriors in individual.items():
                if param in posteriors:
                    mean, std = posteriors[param]
                    if std > 0 and std < float('inf'):
                        chi_sq += ((mean - joint_means[param]) / std) ** 2
                        n_surveys += 1

            if n_surveys > 1:
                dof = n_surveys - 1
                # Convert to sigma equivalent
                tensions[param] = math.sqrt(max(0, chi_sq - dof)) if chi_sq > dof else 0.0
            else:
                tensions[param] = 0.0

        return tensions

    def _compute_effective_sample_size(self,
                                       individual: Dict,
                                       parameters: List[str]) -> float:
        """Compute effective sample size."""
        # Simplified: count number of independent constraints
        ess = 0.0

        for survey, posteriors in individual.items():
            n_params = sum(1 for p in parameters if p in posteriors)
            ess += n_params

        return ess

    def detect_tension(self,
                      joint: JointPosterior,
                      threshold: float = 3.0) -> List[Dict[str, Any]]:
        """
        Detect significant tensions between surveys.
        """
        tensions = []

        for param, tension in joint.tension_statistics.items():
            if tension > threshold:
                # Find disagreeing surveys
                disagreeing = []
                joint_mean = joint.means[param]

                for survey, posteriors in joint.individual_posteriors.items():
                    if param in posteriors:
                        mean, std = posteriors[param]
                        if std > 0:
                            deviation = abs(mean - joint_mean) / std
                            if deviation > threshold / 2:
                                disagreeing.append({
                                    "survey": survey,
                                    "value": mean,
                                    "error": std,
                                    "deviation": deviation
                                })

                tensions.append({
                    "parameter": param,
                    "tension_sigma": tension,
                    "joint_value": joint_mean,
                    "disagreeing_surveys": disagreeing
                })

        return tensions


# ============================================================================
# Survey Calibrator
# ============================================================================

class SurveyCalibrator:
    """
    Cross-calibrates surveys using overlapping observations.
    """

    def __init__(self):
        self._calibration_offsets: Dict[Tuple[str, str, str], float] = {}

    def estimate_calibration_offset(self,
                                   survey1: str,
                                   survey2: str,
                                   parameter: str,
                                   matched_sources: List[CrossMatch]) -> Tuple[float, float]:
        """
        Estimate systematic offset between two surveys.

        Returns (offset, uncertainty)
        """
        differences = []
        weights = []

        for match in matched_sources:
            source1 = next((s for s in match.sources if s.survey_name == survey1), None)
            source2 = next((s for s in match.sources if s.survey_name == survey2), None)

            if source1 and source2:
                if parameter in source1.measurements and parameter in source2.measurements:
                    diff = source1.measurements[parameter] - source2.measurements[parameter]

                    err1 = source1.uncertainties.get(parameter, 1.0)
                    err2 = source2.uncertainties.get(parameter, 1.0)
                    weight = 1.0 / (err1 ** 2 + err2 ** 2)

                    differences.append(diff)
                    weights.append(weight)

        if not differences:
            return 0.0, float('inf')

        # Weighted mean of differences
        total_weight = sum(weights)
        offset = sum(w * d for w, d in zip(weights, differences)) / total_weight
        uncertainty = 1.0 / math.sqrt(total_weight)

        # Store
        self._calibration_offsets[(survey1, survey2, parameter)] = offset

        return offset, uncertainty

    def apply_calibration(self,
                         source: Source,
                         reference_survey: str) -> Source:
        """
        Apply calibration offset to bring source to reference frame.
        """
        calibrated = Source(
            source_id=source.source_id,
            survey_name=source.survey_name,
            ra=source.ra,
            dec=source.dec,
            ra_error=source.ra_error,
            dec_error=source.dec_error,
            measurements=source.measurements.copy(),
            uncertainties=source.uncertainties.copy(),
            flags=source.flags.copy(),
            epoch=source.epoch
        )

        for param in calibrated.measurements:
            key = (source.survey_name, reference_survey, param)
            if key in self._calibration_offsets:
                offset = self._calibration_offsets[key]
                calibrated.measurements[param] -= offset

        return calibrated


# ============================================================================
# Main Fusion Engine
# ============================================================================

class CrossSurveyFusionEngine:
    """
    Main engine for cross-survey knowledge fusion.
    """

    def __init__(self):
        self.cross_matcher = CrossMatcher()
        self.combiner = MeasurementCombiner()
        self.posterior_calculator = JointPosteriorCalculator()
        self.calibrator = SurveyCalibrator()

        self._surveys: Dict[str, Survey] = {}
        self._catalogs: Dict[str, List[Source]] = {}
        self._fused_sources: List[FusedSource] = []
        self._event_bus = None

    def set_event_bus(self, event_bus):
        """Set event bus for integration."""
        self._event_bus = event_bus

    def register_survey(self, survey: Survey):
        """Register a survey."""
        self._surveys[survey.name] = survey

    def add_catalog(self, survey_name: str, sources: List[Source]):
        """Add catalog for a survey."""
        if survey_name not in self._catalogs:
            self._catalogs[survey_name] = []
        self._catalogs[survey_name].extend(sources)

    def perform_fusion(self,
                      calibrate: bool = True,
                      reference_survey: Optional[str] = None) -> List[FusedSource]:
        """
        Perform full cross-survey fusion.
        """
        if len(self._catalogs) < 2:
            logger.warning("Need at least 2 catalogs for fusion")
            return []

        # Estimate source densities
        densities = {}
        for name, catalog in self._catalogs.items():
            if name in self._surveys:
                area = self._surveys[name].coverage_area
                densities[name] = len(catalog) / (area * 3600 ** 2) if area > 0 else 0.01
            else:
                densities[name] = 0.01

        # Cross-match
        matches = self.cross_matcher.multi_catalog_match(self._catalogs, densities)

        logger.info(f"Found {len(matches)} cross-matches")

        # Calibrate if requested
        if calibrate and reference_survey:
            # Estimate calibration offsets
            survey_names = list(self._catalogs.keys())
            for survey in survey_names:
                if survey != reference_survey:
                    for param in self._get_common_parameters(survey, reference_survey):
                        self.calibrator.estimate_calibration_offset(
                            survey, reference_survey, param, matches
                        )

        # Fuse sources
        fused_sources = []
        for match in matches:
            fused = self.combiner.fuse_sources(match, self._surveys)
            fused_sources.append(fused)

        self._fused_sources = fused_sources

        # Emit event
        if self._event_bus:
            self._event_bus.publish(
                "fusion_complete",
                "cross_survey_fusion",
                {
                    "n_matches": len(matches),
                    "n_fused": len(fused_sources),
                    "n_surveys": len(self._catalogs)
                }
            )

        return fused_sources

    def compute_joint_constraints(self,
                                  parameters: List[str]) -> JointPosterior:
        """
        Compute joint constraints on parameters from all surveys.
        """
        all_sources = []
        for catalog in self._catalogs.values():
            all_sources.extend(catalog)

        return self.posterior_calculator.compute_joint_posterior(
            all_sources, parameters, self._surveys
        )

    def detect_tensions(self, threshold: float = 3.0) -> List[Dict]:
        """
        Detect tensions between surveys.
        """
        # Get common parameters
        all_params = set()
        for catalog in self._catalogs.values():
            for source in catalog:
                all_params.update(source.measurements.keys())

        joint = self.compute_joint_constraints(list(all_params))

        return self.posterior_calculator.detect_tension(joint, threshold)

    def get_fusion_statistics(self) -> Dict[str, Any]:
        """Get fusion statistics."""
        stats = {
            "n_surveys": len(self._catalogs),
            "total_sources": sum(len(c) for c in self._catalogs.values()),
            "n_fused": len(self._fused_sources),
            "surveys": {}
        }

        for name, catalog in self._catalogs.items():
            survey_info = {"n_sources": len(catalog)}
            if name in self._surveys:
                survey_info.update({
                    "band": self._surveys[name].wavelength_band.value,
                    "type": self._surveys[name].survey_type.value,
                    "resolution": self._surveys[name].angular_resolution
                })
            stats["surveys"][name] = survey_info

        # Tension summary
        if self._fused_sources:
            tension_counts = defaultdict(int)
            for fused in self._fused_sources:
                for param, tension in fused.tension_flags.items():
                    if tension > 3.0:
                        tension_counts[param] += 1
            stats["high_tension_parameters"] = dict(tension_counts)

        return stats

    def _get_common_parameters(self, survey1: str, survey2: str) -> List[str]:
        """Get parameters measured by both surveys."""
        params1 = set()
        params2 = set()

        for source in self._catalogs.get(survey1, []):
            params1.update(source.measurements.keys())

        for source in self._catalogs.get(survey2, []):
            params2.update(source.measurements.keys())

        return list(params1.intersection(params2))


# ============================================================================
# Singleton Access
# ============================================================================

_fusion_engine: Optional[CrossSurveyFusionEngine] = None


def get_cross_survey_fusion_engine() -> CrossSurveyFusionEngine:
    """Get singleton fusion engine instance."""
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = CrossSurveyFusionEngine()
    return _fusion_engine


# ============================================================================
# Integration with STAN Event Bus
# ============================================================================

def setup_cross_survey_fusion_integration(event_bus) -> None:
    """Set up cross-survey fusion integration with STAN event bus."""
    engine = get_cross_survey_fusion_engine()
    engine.set_event_bus(event_bus)

    def on_catalog_received(event):
        """Handle incoming catalog data."""
        payload = event.get("payload", {})
        survey_name = payload.get("survey_name")
        sources_data = payload.get("sources", [])

        if survey_name and sources_data:
            sources = []
            for sd in sources_data:
                source = Source(
                    source_id=sd.get("id", "unknown"),
                    survey_name=survey_name,
                    ra=sd.get("ra", 0.0),
                    dec=sd.get("dec", 0.0),
                    ra_error=sd.get("ra_error", 1.0),
                    dec_error=sd.get("dec_error", 1.0),
                    measurements=sd.get("measurements", {}),
                    uncertainties=sd.get("uncertainties", {})
                )
                sources.append(source)

            engine.add_catalog(survey_name, sources)

    def on_fusion_request(event):
        """Handle fusion request."""
        payload = event.get("payload", {})
        fused = engine.perform_fusion(
            calibrate=payload.get("calibrate", True),
            reference_survey=payload.get("reference_survey")
        )

        event_bus.publish(
            "fusion_result",
            "cross_survey_fusion",
            {
                "n_fused": len(fused),
                "fused_sources": [
                    {
                        "id": f.fused_id,
                        "ra": f.combined_position[0],
                        "dec": f.combined_position[1],
                        "measurements": f.combined_measurements,
                        "reliability": f.reliability
                    }
                    for f in fused[:100]  # Limit size
                ]
            }
        )

    event_bus.subscribe("catalog_data", on_catalog_received)
    event_bus.subscribe("fusion_request", on_fusion_request)
    logger.info("Cross-survey fusion integration configured")
