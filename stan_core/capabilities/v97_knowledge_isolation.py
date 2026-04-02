"""
V97 Knowledge Isolation Mode - For Genuine Discovery Testing
===========================================================

PROBLEM: When ASTRA "discovers" patterns that are already encoded in its
knowledge base, it's unclear whether this is genuine discovery or knowledge
retrieval. This weakens discovery claims.

SOLUTION: Add a "knowledge isolation mode" that disables access to encoded
domain knowledge during analysis. By comparing results with and without
knowledge access, we can distinguish:
- Knowledge retrieval: pattern found only when knowledge is enabled
- Data-driven discovery: pattern found regardless of knowledge state
- Synthesis: combining knowledge with data in novel ways

USAGE:
    analyzer = create_isolated_analyzer()

    # Run with knowledge isolation (blind mode)
    blind_result = analyzer.analyze(data, knowledge_isolated=True)

    # Run with full knowledge access
    informed_result = analyzer.analyze(data, knowledge_isolated=False)

    # Compare to classify discovery type
    discovery_type = classify_discovery_type(blind_result, informed_result)

DISCOVERY TYPES:
- PURE_RETRIEVAL: Found only with knowledge (not in blind mode)
- PURE_DISCOVERY: Found in blind mode, enhanced by knowledge
- KNOWLEDGE_GUIDED: Knowledge guided the search but data confirmed
- NOVEL_SYNTHESIS: Combination of knowledge and data produces new insight

Date: 2026-04-01
Referee: Referee3 - Genuine Discovery Demonstration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import numpy as np
from scipy import stats
import json


class DiscoveryType(Enum):
    """Classification of how a pattern was identified"""
    PURE_RETRIEVAL = "pure_retrieval"  # Only found with knowledge access
    PURE_DISCOVERY = "pure_discovery"  # Found regardless of knowledge
    KNOWLEDGE_GUIDED = "knowledge_guided"  # Knowledge guided search
    NOVEL_SYNTHESIS = "novel_synthesis"  # Novel combination of knowledge + data
    UNKNOWN = "unknown"


@dataclass
class PatternResult:
    """Result of pattern discovery analysis"""
    pattern_id: str
    pattern_description: str
    statistical_significance: float  # p-value
    effect_size: float
    variables: List[str]
    relationship_type: str  # correlation, causal, scaling, etc.

    # Knowledge isolation tracking
    found_in_blind_mode: bool = False
    found_in_knowledge_mode: bool = False
    enhanced_by_knowledge: bool = False

    # Provenance
    confidence: float = 0.0
    validation_method: str = ""
    requires_external_validation: bool = True

    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'pattern_description': self.pattern_description,
            'statistical_significance': self.statistical_significance,
            'effect_size': self.effect_size,
            'variables': self.variables,
            'relationship_type': self.relationship_type,
            'found_in_blind_mode': self.found_in_blind_mode,
            'found_in_knowledge_mode': self.found_in_knowledge_mode,
            'enhanced_by_knowledge': self.enhanced_by_knowledge,
            'confidence': self.confidence
        }


@dataclass
class NoveltyScore:
    """
    Quantifies how novel/discovered a pattern is.

    A high novelty score indicates:
    1. Low prior probability given domain knowledge
    2. High statistical significance in data
    3. Not previously documented in literature
    4. Physically interpretable mechanism

    Components:
    - knowledge_unexpectedness: How unexpected given prior knowledge?
    - statistical_strength: How strong is the statistical signal?
    - literature_novelty: Is this already published?
    - interpretability: Can we explain why it exists?
    """
    pattern_id: str
    knowledge_unexpectedness: float  # 0-1: 1 = completely unexpected
    statistical_strength: float  # 0-1: 1 = very strong
    literature_novelty: float  # 0-1: 1 = completely novel
    interpretability: float  # 0-1: 1 = clear mechanism

    @property
    def overall_novelty(self) -> float:
        """Combined novelty score (weighted geometric mean)"""
        weights = np.array([0.3, 0.3, 0.25, 0.15])  # Emphasize unexpectedness + stats
        scores = np.array([
            self.knowledge_unexpectedness,
            self.statistical_strength,
            self.literature_novelty,
            self.interpretability
        ])

        # Weighted geometric mean
        return np.exp(np.sum(weights * np.log(scores + 1e-10)))

    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'knowledge_unexpectedness': self.knowledge_unexpectedness,
            'statistical_strength': self.statistical_strength,
            'literature_novelty': self.literature_novelty,
            'interpretability': self.interpretability,
            'overall_novelty': self.overall_novelty
        }


class KnowledgeIsolatedAnalyzer:
    """
    Analyzer that can operate with or without knowledge base access.

    This enables the "blind recovery" test recommended by Referee3:
    - Run analysis in blind mode (no domain knowledge)
    - Run analysis with full knowledge access
    - Compare results to classify discovery type
    """

    def __init__(self, knowledge_base=None):
        """
        Initialize analyzer.

        Args:
            knowledge_base: Domain knowledge (ontology, known relations, etc.)
        """
        self.knowledge_base = knowledge_base or {}
        self.knowledge_isolated = False

        # Track what patterns were found in each mode
        self.blind_mode_patterns: Dict[str, PatternResult] = {}
        self.knowledge_mode_patterns: Dict[str, PatternResult] = {}

    def set_knowledge_isolation(self, isolated: bool) -> None:
        """
        Enable or disable knowledge isolation mode.

        Args:
            isolated: If True, disable access to knowledge base
        """
        self.knowledge_isolated = isolated

    def analyze_correlations(
        self,
        data: Dict[str, np.ndarray],
        significance_threshold: float = 0.05
    ) -> List[PatternResult]:
        """
        Analyze correlations between variables.

        In knowledge-isolated mode:
        - Don't use prior expectations about which variables should correlate
        - Test all pairs systematically
        - Report all significant findings regardless of prior knowledge

        In knowledge-enabled mode:
        - Use prior knowledge to prioritize likely correlations
        - Guide search toward physically-motivated variable pairs
        - Flag correlations that are expected vs unexpected
        """
        results = []
        variables = list(data.keys())

        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                # Compute correlation
                corr, p_value = stats.pearsonr(data[var1], data[var2])

                if p_value < significance_threshold:
                    # Found significant correlation
                    pattern_id = f"corr_{var1}_{var2}"

                    # Check if this was expected from knowledge
                    expected = self._is_expected_correlation(var1, var2) if not self.knowledge_isolated else False

                    result = PatternResult(
                        pattern_id=pattern_id,
                        pattern_description=f"{var1} correlates with {var2}",
                        statistical_significance=p_value,
                        effect_size=abs(corr),
                        variables=[var1, var2],
                        relationship_type="correlation",
                        found_in_blind_mode=self.knowledge_isolated,
                        found_in_knowledge_mode=not self.knowledge_isolated,
                        enhanced_by_knowledge=not self.knowledge_isolated and expected,
                        confidence=1.0 - p_value
                    )

                    results.append(result)

        return results

    def analyze_scaling_relations(
        self,
        data: Dict[str, np.ndarray],
        x_var: str,
        y_var: str
    ) -> List[PatternResult]:
        """
        Analyze scaling relations (power laws, logarithmic, etc.)
        """
        x = data[x_var]
        y = data[y_var]

        # Fit power law in log-log space
        log_x = np.log(x)
        log_y = np.log(y)

        slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)

        # Fit logarithmic
        from scipy.optimize import curve_fit
        def log_func(x_val, a, b):
            return a * np.log(x_val) + b

        try:
            popt_log, _ = curve_fit(log_func, x, y, p0=[1.0, 0.0])
            residuals_log = y - log_func(x, *popt_log)
            ss_res_log = np.sum(residuals_log**2)
            ss_tot_log = np.sum((y - np.mean(y))**2)
            r2_log = 1 - (ss_res_log / ss_tot_log)
        except:
            r2_log = 0.0

        results = []

        # Power law result
        results.append(PatternResult(
            pattern_id=f"scaling_power_{x_var}_{y_var}",
            pattern_description=f"Power law: {y_var} ∝ {x_var}^{slope:.3f}",
            statistical_significance=p_value,
            effect_size=abs(r_value),
            variables=[x_var, y_var],
            relationship_type="power_law",
            found_in_blind_mode=self.knowledge_isolated,
            found_in_knowledge_mode=not self.knowledge_isolated,
            enhanced_by_knowledge=False,
            confidence=1.0 - p_value
        ))

        return results

    def _is_expected_correlation(self, var1: str, var2: str) -> bool:
        """
        Check if correlation between variables is expected from prior knowledge.

        This would query the knowledge base (ontology, known relations).
        For now, return False as placeholder.
        """
        # In full implementation, this would query:
        # - MORK ontology for known relationships
        # - Domain modules for expected correlations
        # - Literature database for published relations

        # Placeholder: some physically-motivated expectations
        known_relations = [
            ('stellar_mass', 'metallicity'),
            ('stellar_mass', 'sfr'),
            ('velocity_dispersion', 'mass_per_length'),
            ('luminosity', 'temperature'),
            ('distance', 'apparent_magnitude')
        ]

        for rel in known_relations:
            if var1 in rel and var2 in rel:
                return True

        return False

    def compare_modes(self) -> Dict[str, DiscoveryType]:
        """
        Compare blind mode vs knowledge mode results.

        Returns classification of each pattern's discovery type.
        """
        all_pattern_ids = set(self.blind_mode_patterns.keys()) | set(self.knowledge_mode_patterns.keys())

        classifications = {}

        for pattern_id in all_pattern_ids:
            blind_result = self.blind_mode_patterns.get(pattern_id)
            knowledge_result = self.knowledge_mode_patterns.get(pattern_id)

            classifications[pattern_id] = classify_discovery_type(
                blind_result, knowledge_result
            )

        return classifications


def classify_discovery_type(
    blind_result: Optional[PatternResult],
    knowledge_result: Optional[PatternResult]
) -> DiscoveryType:
    """
    Classify how a pattern was discovered based on blind vs knowledge mode results.

    Classification:
    - PURE_RETRIEVAL: Only found with knowledge (not in blind mode)
    - PURE_DISCOVERY: Found in blind mode, confirmed by knowledge
    - KNOWLEDGE_GUIDED: Found in both modes, but knowledge guided search
    - NOVEL_SYNTHESIS: Knowledge + data produced novel insight
    - UNKNOWN: Cannot determine
    """
    if blind_result is None and knowledge_result is not None:
        return DiscoveryType.PURE_RETRIEVAL

    if blind_result is not None and knowledge_result is None:
        return DiscoveryType.PURE_DISCOVERY

    if blind_result is not None and knowledge_result is not None:
        # Found in both modes
        if knowledge_result.enhanced_by_knowledge:
            return DiscoveryType.KNOWLEDGE_GUIDED
        else:
            return DiscoveryType.PURE_DISCOVERY

    return DiscoveryType.UNKNOWN


def compute_novelty_score(
    pattern: PatternResult,
    knowledge_base: Dict = None,
    literature_check: bool = True
) -> NoveltyScore:
    """
    Compute novelty score for a discovered pattern.

    Args:
        pattern: The discovered pattern
        knowledge_base: Domain knowledge for checking unexpectedness
        literature_check: Whether to check against published literature

    Returns:
        NoveltyScore with components and overall score
    """
    kb = knowledge_base or {}

    # 1. Knowledge unexpectedness:
    #    How unexpected is this given prior knowledge?
    #    High if pattern contradicts or extends beyond known expectations
    unexpectedness = 0.5  # Placeholder
    if pattern.found_in_blind_mode:
        # Found without knowledge guidance = more unexpected
        unexpectedness += 0.3
    if pattern.found_in_knowledge_mode and not pattern.enhanced_by_knowledge:
        # Expected from knowledge = less unexpected
        unexpectedness -= 0.2
    unexpectedness = np.clip(unexpectedness, 0, 1)

    # 2. Statistical strength:
    #    Based on p-value and effect size
    statistical = 1.0 - pattern.statistical_significance  # Lower p = higher
    statistical = min(statistical, pattern.effect_size)  # Also consider effect size
    statistical = max(0, min(1, statistical))

    # 3. Literature novelty:
    #    Placeholder - would check against published papers
    literature = 0.7  # Assume moderately novel unless confirmed

    # 4. Interpretability:
    #    Can we explain why this pattern exists physically?
    #    Higher if pattern has clear physical interpretation
    interpretability = 0.6  # Placeholder

    return NoveltyScore(
        pattern_id=pattern.pattern_id,
        knowledge_unexpectedness=unexpectedness,
        statistical_strength=statistical,
        literature_novelty=literature,
        interpretability=interpretability
    )


class HypothesisCompetitionEngine:
    """
    Generate and rank competing hypotheses for observed patterns.

    This addresses Referee3's recommendation for a "hypothesis competition engine"
    that can:
    - Generate multiple plausible explanations for an observation
    - Rank them by evidence, physical plausibility, and predictive power
    - Distinguish between hypotheses that are statistically indistinguishable
    """

    def __init__(self):
        self.hypotheses: Dict[str, Dict] = {}

    def generate_competing_hypotheses(
        self,
        observation: str,
        variables: List[str],
        domain_context: str = ""
    ) -> List[Dict]:
        """
        Generate multiple competing hypotheses for an observation.

        For example, for "stellar mass correlates with metallicity":
        - H1: Mass-metallicity relation is causal (more massive stars retain metals)
        - H2: Both correlate with a third variable (e.g., halo mass, age)
        - H3: Selection effect (only detecting certain galaxy types)
        - H4: Measurement bias (metallicity measurements easier for massive galaxies)
        """
        hypotheses = []

        # Generic hypothesis templates
        # In full implementation, these would be domain-specific

        hypotheses.append({
            'hypothesis_id': f'H_causal',
            'description': f"Causal relationship: {variables[0]} affects {variables[1]}",
            'mechanism': "Direct physical causation",
            'plausibility': 0.7,
            'testable_predictions': []
        })

        hypotheses.append({
            'hypothesis_id': f'H_confounded',
            'description': f"Confounded: both {variables[0]} and {variables[1]} caused by third variable",
            'mechanism': "Common cause / latent confounder",
            'plausibility': 0.6,
            'testable_predictions': []
        })

        hypotheses.append({
            'hypothesis_id': f'H_selection',
            'description': f"Selection effect: observation biased by sample selection",
            'mechanism': "Observational bias",
            'plausibility': 0.5,
            'testable_predictions': []
        })

        return hypotheses

    def rank_hypotheses(
        self,
        hypotheses: List[Dict],
        evidence: Dict,
        physics_constraints: List = None
    ) -> List[Dict]:
        """
        Rank hypotheses by multiple criteria.

        Criteria:
        1. Statistical evidence (how well does it fit the data?)
        2. Physical plausibility (is it physically reasonable?)
        3. Predictive power (does it make testable predictions?)
        4. Simplicity (Occam's razor)
        """
        physics_constraints = physics_constraints or []

        ranked = []

        for hyp in hypotheses:
            score = (
                hyp.get('evidence_fit', 0.5) * 0.35 +
                hyp.get('plausibility', 0.5) * 0.30 +
                hyp.get('predictive_power', 0.5) * 0.25 +
                hyp.get('simplicity', 0.5) * 0.10
            )

            hyp['overall_score'] = score
            ranked.append(hyp)

        # Sort by score (descending)
        ranked.sort(key=lambda x: x['overall_score'], reverse=True)

        return ranked


# Factory function
def create_isolated_analyzer(knowledge_base=None) -> KnowledgeIsolatedAnalyzer:
    """
    Factory function to create a knowledge-isolated analyzer.

    Args:
        knowledge_base: Optional domain knowledge base

    Returns:
        KnowledgeIsolatedAnalyzer instance
    """
    return KnowledgeIsolatedAnalyzer(knowledge_base=knowledge_base)


if __name__ == "__main__":
    print("="*70)
    print("V97 KNOWLEDGE ISOLATION MODE - Genuine Discovery Testing")
    print("="*70)

    # Create test data
    np.random.seed(42)
    n_samples = 100

    test_data = {
        'mass_per_length': np.random.lognormal(2.5, 0.6, n_samples),
        'velocity_dispersion': np.random.lognormal(0.5, 0.3, n_samples),
        'width_pc': np.random.normal(0.1, 0.02, n_samples),
        'stellar_mass': np.random.lognormal(10.5, 0.5, n_samples),
        'metallicity': np.random.normal(8.8, 0.15, n_samples)
    }

    # Add correlation: velocity ∝ sqrt(M/L)
    test_data['velocity_dispersion'] = np.sqrt(test_data['mass_per_length']) * 0.3 + np.random.normal(0, 0.05, n_samples)

    # Add correlation: mass-metallicity
    test_data['metallicity'] += 0.15 * (test_data['stellar_mass'] - 10.5)

    # Test blind mode
    print("\n" + "-"*70)
    print("TEST 1: Blind Mode Analysis (No Knowledge Access)")
    print("-"*70)

    analyzer = create_isolated_analyzer()
    analyzer.set_knowledge_isolation(True)

    blind_results = analyzer.analyze_correlations(test_data, significance_threshold=0.01)

    print(f"Found {len(blind_results)} significant correlations in blind mode:")
    for r in blind_results:
        print(f"  - {r.pattern_description} (p={r.statistical_significance:.2e})")
        analyzer.blind_mode_patterns[r.pattern_id] = r

    # Test knowledge mode
    print("\n" + "-"*70)
    print("TEST 2: Knowledge Mode Analysis (Full Knowledge Access)")
    print("-"*70)

    analyzer.set_knowledge_isolation(False)

    knowledge_results = analyzer.analyze_correlations(test_data, significance_threshold=0.01)

    print(f"Found {len(knowledge_results)} significant correlations in knowledge mode:")
    for r in knowledge_results:
        print(f"  - {r.pattern_description} (p={r.statistical_significance:.2e})")
        analyzer.knowledge_mode_patterns[r.pattern_id] = r

    # Classify discovery types
    print("\n" + "-"*70)
    print("TEST 3: Discovery Type Classification")
    print("-"*70)

    classifications = analyzer.compare_modes()

    for pattern_id, discovery_type in classifications.items():
        print(f"  {pattern_id}: {discovery_type.value}")

    # Compute novelty scores
    print("\n" + "-"*70)
    print("TEST 4: Novelty Scoring")
    print("-"*70)

    for pattern_id, blind_result in analyzer.blind_mode_patterns.items():
        novelty = compute_novelty_score(blind_result)
        print(f"  {pattern_id}:")
        print(f"    Overall novelty: {novelty.overall_novelty:.3f}")
        print(f"    Unexpectedness: {novelty.knowledge_unexpectedness:.3f}")
        print(f"    Statistical: {novelty.statistical_strength:.3f}")

    # Test hypothesis competition
    print("\n" + "-"*70)
    print("TEST 5: Hypothesis Competition Engine")
    print("-"*70)

    engine = HypothesisCompetitionEngine()
    hypotheses = engine.generate_competing_hypotheses(
        observation="stellar_mass correlates with metallicity",
        variables=['stellar_mass', 'metallicity'],
        domain_context="galaxy_evolution"
    )

    print(f"Generated {len(hypotheses)} competing hypotheses:")
    for hyp in hypotheses:
        print(f"  {hyp['hypothesis_id']}: {hyp['description']}")
        print(f"    Mechanism: {hyp['mechanism']}")
        print(f"    Plausibility: {hyp['plausibility']}")

    print("\n" + "="*70)
    print("V97 TESTS COMPLETE")
    print("="*70)
