"""
Prior/Expectation Model (Formal Knowledge Base)

Implements machine-readable knowledge base encoding established scientific
relations with uncertainties. This prevents ASTRA from reporting agreement
with known relations as "discoveries."

This module addresses the critical issue where ASTRA treats expected
replications (e.g., filament width ≈ 0.1 pc) as novel discoveries.

Version: 1.0.0
Date: 2026-07-04
"""

import yaml
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class PriorClassification(Enum):
    """Classification of result relative to prior knowledge"""
    CONFIRMATORY = "confirmatory"  # Consistent with prior (within uncertainty)
    UNDERPOWERED = "underpowered"  # Effect size below minimum detectable effect
    CANDIDATE_NOVEL = "candidate_novel"  # Potentially novel, needs validation
    NOVEL_DISCOVERY = "novel_discovery"  # Genuinely novel, passes validation


class RelationType(Enum):
    """Types of scientific relations"""
    SCALING_LAW = "scaling_law"  # Power-law scaling relation
    CONSTANT_VALUE = "constant_value"  # Universal constant value
    DISTRIBUTION = "distribution"  # Statistical distribution
    CORRELATION = "correlation"  # Correlation between variables


@dataclass
class ScientificRelation:
    """
    A known scientific relation with quantified uncertainty.

    Each relation has a central value, uncertainty, and a machine-checkable
    predicate for determining consistency.
    """
    # Identification
    relation_id: str  # Unique identifier (e.g., "larson_law_velocity_size")
    name: str  # Human-readable name
    relation_type: RelationType

    # Quantitative specification
    expected_value: float  # Central expected value
    uncertainty: float  # 1-sigma uncertainty (can be asymmetric with upper_uncertainty)
    upper_uncertainty: Optional[float] = None  # For asymmetric uncertainties
    lower_uncertainty: Optional[float] = None  # For asymmetric uncertainties

    # Relation-specific parameters
    variables: List[str] = field(default_factory=list)  # Variables in relation
    units: str = ""  # Physical units
    power_law_index: Optional[float] = None  # For scaling laws

    # Metadata
    citation: str = ""  # Primary literature citation
    confidence_level: float = 0.95  # Confidence level (default 95%)
    domain: str = ""  # Astrophysical domain (e.g., "molecular_clouds")

    # Machine-checkable predicate
    def is_consistent_with(self, observed_value: float, observed_uncertainty: float = 0.0) -> Tuple[bool, float]:
        """
        Check if observed value is consistent with prior.

        Args:
            observed_value: Observed/measured value
            observed_uncertainty: Uncertainty in observed value

        Returns:
            (is_consistent, deviation_sigma) where:
            - is_consistent: True if within confidence interval
            - deviation_sigma: Deviation in units of combined uncertainty
        """
        # Combined uncertainty (prior + observation, quadrature sum)
        if self.upper_uncertainty is not None and self.lower_uncertainty is not None:
            # Asymmetric case - use average
            prior_unc = (self.upper_uncertainty + self.lower_uncertainty) / 2.0
        else:
            prior_unc = self.uncertainty

        combined_unc = np.sqrt(prior_unc**2 + observed_uncertainty**2)

        # Deviation from expected value
        deviation = observed_value - self.expected_value

        # Convert to sigma
        if combined_unc > 0:
            deviation_sigma = deviation / combined_unc
        else:
            deviation_sigma = 0.0

        # Check consistency (within confidence interval)
        is_consistent = abs(deviation_sigma) < self._get_sigma_threshold()

        return is_consistent, deviation_sigma

    def _get_sigma_threshold(self) -> float:
        """Get sigma threshold for confidence level"""
        # Approximate sigma for common confidence levels
        confidence_to_sigma = {
            0.68: 1.0,
            0.95: 2.0,
            0.99: 2.58,
            0.997: 3.0
        }
        return confidence_to_sigma.get(self.confidence_level, 2.0)

    def get_confidence_interval(self) -> Tuple[float, float]:
        """Get confidence interval (lower, upper)"""
        if self.upper_uncertainty is not None and self.lower_uncertainty is not None:
            lower = self.expected_value - self.lower_uncertainty
            upper = self.expected_value + self.upper_uncertainty
        else:
            lower = self.expected_value - self.uncertainty
            upper = self.expected_value + self.uncertainty
        return lower, upper


@dataclass
class PowerAnalysisResult:
    """Result of statistical power analysis"""
    is_underpowered: bool
    minimum_detectable_effect: float  # Minimum effect size detectable
    achieved_power: float  # Statistical power achieved
    required_sample_size: int  # Required sample size for desired power
    current_sample_size: int
    effect_size_of_interest: float  # Effect size we want to detect
    recommendation: str  # Human-readable recommendation


class PriorKnowledgeBase:
    """
    Formal knowledge base of established scientific relations.

    This enables ASTRA to:
    - Automatically classify results as confirmatory/novel
    - Check consistency with known physics
    - Avoid reporting expected replications as discoveries
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize prior knowledge base.

        Args:
            config_path: Path to YAML config file (default: astra_priors.yaml)
        """
        if config_path is None:
            # Default to project root config
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'astra_priors.yaml'

        self.config_path = config_path
        self.relations: Dict[str, ScientificRelation] = {}
        self.domain_relations: Dict[str, List[str]] = {}  # domain -> relation IDs

        # Load relations from config
        if config_path.exists():
            self._load_from_config(config_path)
        else:
            logger.warning(f"[PriorKB] Config file not found at {config_path}, using defaults")
            self._load_default_relations()

        logger.info(f"[PriorKB] ✅ Initialized with {len(self.relations)} scientific relations")

    def _load_from_config(self, config_path: Path):
        """Load relations from YAML config file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Parse relations
            for relation_data in config.get('relations', []):
                relation = self._parse_relation(relation_data)
                self.add_relation(relation)

            logger.info(f"[PriorKB] Loaded {len(self.relations)} relations from {config_path}")

        except Exception as e:
            logger.error(f"[PriorKB] Failed to load config: {e}")
            self._load_default_relations()

    def _parse_relation(self, data: Dict[str, Any]) -> ScientificRelation:
        """Parse relation from config data"""
        relation_type = RelationType(data.get('relation_type', 'constant_value'))

        # Handle asymmetric uncertainties
        upper_unc = data.get('upper_uncertainty')
        lower_unc = data.get('lower_uncertainty')

        return ScientificRelation(
            relation_id=data['relation_id'],
            name=data['name'],
            relation_type=relation_type,
            expected_value=float(data['expected_value']),
            uncertainty=float(data.get('uncertainty', 0.0)),
            upper_uncertainty=upper_unc and float(upper_unc),
            lower_uncertainty=lower_unc and float(lower_unc),
            variables=data.get('variables', []),
            units=data.get('units', ''),
            power_law_index=data.get('power_law_index'),
            citation=data.get('citation', ''),
            confidence_level=float(data.get('confidence_level', 0.95)),
            domain=data.get('domain', '')
        )

    def _load_default_relations(self):
        """Load default set of established relations"""
        # Larson's Law 1: Velocity-size relation
        larson1 = ScientificRelation(
            relation_id="larson_law_velocity_size",
            name="Larson's Law 1: Velocity-size relation",
            relation_type=RelationType.SCALING_LAW,
            expected_value=0.38,  # Power-law index
            uncertainty=0.05,
            variables=["velocity_dispersion", "cloud_size"],
            units="dimensionless",
            power_law_index=0.38,
            citation="Larson 1981, MNRAS, 74, 19",
            confidence_level=0.95,
            domain="molecular_clouds"
        )

        # Universal filament width
        filament_width = ScientificRelation(
            relation_id="universal_filament_width",
            name="Universal filament width in molecular clouds",
            relation_type=RelationType.CONSTANT_VALUE,
            expected_value=0.1,  # parsecs
            uncertainty=0.03,
            variables=["filament_width"],
            units="pc",
            citation="Arzoumanian et al. 2011, A&A, 529, L6",
            confidence_level=0.95,
            domain="molecular_clouds"
        )

        # Salpeter IMF slope
        salpeter_imf = ScientificRelation(
            relation_id="salpeter_imf_slope",
            name="Salpeter IMF slope",
            relation_type=RelationType.CONSTANT_VALUE,
            expected_value=2.35,  # Power-law index
            uncertainty=0.1,
            variables=["mass_function_slope"],
            units="dimensionless",
            citation="Salpeter 1955, ApJ, 121, 161",
            confidence_level=0.95,
            domain="stellar_formation"
        )

        # Larson's Law 2: Mass-size relation
        larson2 = ScientificRelation(
            relation_id="larson_law_mass_size",
            name="Larson's Law 2: Mass-size relation",
            relation_type=RelationType.SCALING_LAW,
            expected_value=2.0,  # Power-law index
            uncertainty=0.2,
            variables=["cloud_mass", "cloud_size"],
            units="dimensionless",
            power_law_index=2.0,
            citation="Larson 1981, MNRAS, 74, 19",
            confidence_level=0.95,
            domain="molecular_clouds"
        )

        # Virial parameter (typical value)
        virial_parameter = ScientificRelation(
            relation_id="virial_parameter_molecular_clouds",
            name="Virial parameter for molecular clouds",
            relation_type=RelationType.CONSTANT_VALUE,
            expected_value=1.5,  # Near virial equilibrium
            uncertainty=0.5,
            variables=["virial_parameter"],
            units="dimensionless",
            citation="Bertoldi & McKee 1992, ApJ, 395, 140",
            confidence_level=0.95,
            domain="molecular_clouds"
        )

        # Add all relations
        for relation in [larson1, filament_width, salpeter_imf, larson2, virial_parameter]:
            self.add_relation(relation)

        logger.info("[PriorKB] Loaded default relations")

    def add_relation(self, relation: ScientificRelation):
        """Add a scientific relation to knowledge base"""
        self.relations[relation.relation_id] = relation

        # Update domain index
        if relation.domain:
            if relation.domain not in self.domain_relations:
                self.domain_relations[relation.domain] = []
            self.domain_relations[relation.domain].append(relation.relation_id)

        logger.debug(f"[PriorKB] Added relation: {relation.relation_id}")

    def get_relation(self, relation_id: str) -> Optional[ScientificRelation]:
        """Get relation by ID"""
        return self.relations.get(relation_id)

    def get_relations_by_domain(self, domain: str) -> List[ScientificRelation]:
        """Get all relations for a specific domain"""
        relation_ids = self.domain_relations.get(domain, [])
        return [self.relations[rid] for rid in relation_ids if rid in self.relations]

    def classify_result(
        self,
        observed_value: float,
        observed_uncertainty: float,
        relation_id: str,
        sample_size: Optional[int] = None
    ) -> Tuple[PriorClassification, Dict[str, Any]]:
        """
        Classify a result relative to prior knowledge.

        Args:
            observed_value: Observed/measured value
            observed_uncertainty: Uncertainty in observation
            relation_id: ID of relevant prior relation
            sample_size: Sample size for power analysis

        Returns:
            (classification, details) tuple with classification and supporting info
        """
        relation = self.get_relation(relation_id)
        if relation is None:
            logger.warning(f"[PriorKB] Unknown relation ID: {relation_id}")
            return PriorClassification.CANDIDATE_NOVEL, {"reason": "unknown_relation"}

        # Check consistency with prior
        is_consistent, deviation_sigma = relation.is_consistent_with(
            observed_value, observed_uncertainty
        )

        # Perform power analysis if sample size provided
        power_analysis = None
        if sample_size is not None:
            power_analysis = self.perform_power_analysis(
                observed_value, relation.expected_value, sample_size
            )

        # Make classification
        if is_consistent:
            # Result consistent with prior - this is confirmatory
            # IMPORTANT: Consistency with prior trumps power analysis
            # If we're replicating an expected result, power doesn't matter
            details = {
                "reason": "consistent_with_prior",
                "deviation_sigma": deviation_sigma,
                "prior_relation": relation.name,
                "prior_value": relation.expected_value,
                "prior_uncertainty": relation.uncertainty,
                "power_analysis": power_analysis,
                "note": "Consistency with prior takes precedence over power analysis"
            }
            return PriorClassification.CONFIRMATORY, details

        else:
            # Result inconsistent with prior
            # High-sigma deviations (> 3σ) should be classified as novel regardless of power
            # These are potentially paradigm-shifting discoveries
            if abs(deviation_sigma) > 3.0:
                details = {
                    "reason": "high_sigma_inconsistency",
                    "deviation_sigma": deviation_sigma,
                    "power_analysis": power_analysis,
                    "prior_relation": relation.name,
                    "prior_value": relation.expected_value,
                    "observed_value": observed_value,
                    "note": "High sigma deviation (>3σ) overrides power analysis"
                }
                return PriorClassification.NOVEL_DISCOVERY, details

            # Moderate deviation but underpowered
            elif power_analysis and power_analysis.is_underpowered:
                details = {
                    "reason": "underpowered",
                    "deviation_sigma": deviation_sigma,
                    "power_analysis": power_analysis,
                    "prior_relation": relation.name
                }
                return PriorClassification.UNDERPOWERED, details

            else:
                # Moderate deviation with adequate power
                details = {
                    "reason": "inconsistent_with_prior",
                    "deviation_sigma": deviation_sigma,
                    "power_analysis": power_analysis,
                    "prior_relation": relation.name,
                    "prior_value": relation.expected_value,
                    "observed_value": observed_value
                }
                return PriorClassification.CANDIDATE_NOVEL, details

    def perform_power_analysis(
        self,
        effect_size: float,
        null_value: float,
        sample_size: int,
        desired_power: float = 0.80,
        significance_level: float = 0.05
    ) -> PowerAnalysisResult:
        """
        Perform statistical power analysis.

        Args:
            effect_size: Observed effect size (difference from null)
            null_value: Null hypothesis value
            sample_size: Current sample size
            desired_power: Desired statistical power (default 0.80)
            significance_level: Significance level (default 0.05)

        Returns:
            PowerAnalysisResult with detailed analysis
        """
        # Standardized effect size (Cohen's d)
        pooled_std = 1.0  # Simplified - in practice would estimate from data
        cohens_d = abs(effect_size - null_value) / pooled_std

        # Approximate power analysis (simplified)
        # In practice, would use scipy.stats or specialized power analysis library
        import math

        # Required sample size for desired power (simplified formula)
        # n ≈ 16 / (Cohen's d)^2 for 80% power at alpha=0.05
        required_n = int(math.ceil(16.0 / (cohens_d**2)) if cohens_d > 0 else float('inf'))

        # Achieved power (approximate)
        if sample_size >= required_n:
            achieved_power = desired_power
        else:
            # Power scales roughly with sqrt(n)
            achieved_power = desired_power * math.sqrt(sample_size / required_n)
            achieved_power = min(achieved_power, 1.0)

        # Minimum detectable effect for current sample size
        if sample_size > 0:
            minimum_detectable_effect = pooled_std * 4.0 / math.sqrt(sample_size)
        else:
            minimum_detectable_effect = float('inf')

        # Check if underpowered
        is_underpowered = achieved_power < desired_power

        # Generate recommendation
        if is_underpowered:
            recommendation = (
                f"Underpowered: current n={sample_size}, required n={required_n} "
                f"for {desired_power:.0%} power to detect effect of size {cohens_d:.2f}. "
                f"Minimum detectable effect: {minimum_detectable_effect:.3f}"
            )
        else:
            recommendation = (
                f"Adequately powered: n={sample_size} achieves {achieved_power:.0%} power "
                f"for effect size {cohens_d:.2f}"
            )

        return PowerAnalysisResult(
            is_underpowered=is_underpowered,
            minimum_detectable_effect=minimum_detectable_effect,
            achieved_power=achieved_power,
            required_sample_size=required_n,
            current_sample_size=sample_size,
            effect_size_of_interest=cohens_d,
            recommendation=recommendation
        )

    def apply_fdr_correction(self, p_values: List[float], method: str = "benjamini-hochberg") -> List[bool]:
        """
        Apply False Discovery Rate (FDR) correction to multiple p-values.

        This is a critical pipeline step to prevent false discoveries from
        multiple comparisons.

        Args:
            p_values: List of raw p-values
            method: FDR correction method (default: Benjamini-Hochberg)

        Returns:
            List of boolean significance values after FDR correction
        """
        import numpy as np

        if not p_values:
            return []

        # Convert to numpy array
        p_array = np.array(p_values)

        # Sort p-values
        sorted_indices = np.argsort(p_array)
        sorted_p = p_array[sorted_indices]

        # Benjamini-Hochberg procedure
        n = len(p_values)
        bh_thresholds = np.arange(1, n + 1) / n * 0.05  # FDR threshold

        # Find largest p-value that is below threshold
        significant = np.zeros(n, dtype=bool)

        for i in range(n - 1, -1, -1):
            if sorted_p[i] <= bh_thresholds[i]:
                significant[i] = True
                break  # All smaller p-values are also significant

        # Unsort to original order
        original_significant = np.zeros(n, dtype=bool)
        original_significant[sorted_indices] = significant

        return original_significant.tolist()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded relations"""
        domain_counts = {
            domain: len(relation_ids)
            for domain, relation_ids in self.domain_relations.items()
        }

        return {
            "total_relations": len(self.relations),
            "domains_represented": list(self.domain_relations.keys()),
            "relations_by_domain": domain_counts,
            "config_path": str(self.config_path)
        }


def create_prior_knowledge_base(config_path: Optional[Path] = None) -> PriorKnowledgeBase:
    """
    Factory function to create PriorKnowledgeBase.

    Args:
        config_path: Path to YAML config file

    Returns:
        Configured PriorKnowledgeBase instance
    """
    return PriorKnowledgeBase(config_path)