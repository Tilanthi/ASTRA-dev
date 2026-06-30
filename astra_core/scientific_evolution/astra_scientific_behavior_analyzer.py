"""
ASTRA Scientific Behavior Analyzer
====================================

Phase 1.1: Self-awareness system for ASTRA's evolution as an autonomous astrophysical scientist.

This module provides tools for ASTRA to analyze its own responses and recognize when it's
acting as a technical implementer vs. an astrophysical scientist. This self-awareness is
the foundation for developing genuine astronomical scientific capabilities.

Key Capabilities:
- Response analysis for astronomical scientific rigor
- Mode detection (implementer vs. scientist)
- Domain expertise assessment
- Physical consistency checking
- Observational feasibility awareness

Date: 2025-06-29
Phase: 1.1 - ASTRA Self-Awareness Development
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class ASTRA_Mode(Enum):
    """Operating modes for ASTRA"""
    TECHNICAL_IMPLEMENTER = "technical"  # Focus on implementation
    ASTROPHYSICAL_SCIENTIST = "scientist"  # Focus on astronomical validity
    HYBRID = "hybrid"  # Both implementation and scientific thinking


class Scientific_Dimension(Enum):
    """Dimensions of astronomical scientific thinking"""
    PHYSICAL_CONSISTENCY = "physics"  # Checks against physical laws
    OBSERVATIONAL_FEASIBILITY = "observational"  # Considers telescope/instrument limits
    ASTRONOMICAL_CONTEXT = "context"  # Uses astronomical domain knowledge
    STATISTICAL_RIGOR = "statistical"  # Proper astronomical error analysis
    LITERATURE_INTEGRATION = "literature"  # Connects to known research
    SKEPTICAL_THINKING = "skepticism"  # Questions extraordinary claims
    UNCERTAINTY_COMMUNICATION = "uncertainty"  # Expresses astronomical uncertainties


@dataclass
class Scientific_Behavior_Score:
    """Score for a specific scientific dimension"""
    dimension: Scientific_Dimension
    score: float  # 0.0 to 1.0
    evidence: List[str]  # Evidence for the score
    suggestions: List[str]  # Suggestions for improvement


@dataclass
class ASTRA_Response_Analysis:
    """Analysis of ASTRA's response for scientific behavior"""
    response_text: str
    overall_mode: ASTRA_Mode
    dimension_scores: Dict[Scientific_Dimension, Scientific_Behavior_Score]
    implementer_indicators: List[str]
    scientist_indicators: List[str]
    overall_scientific_score: float
    improvement_suggestions: List[str]


class ASTRA_Scientific_Behavior_Analyzer:
    """
    Analyzes ASTRA's responses to develop self-awareness of scientific behavior.

    This is the foundational component for ASTRA's evolution - it helps ASTRA recognize
    when it's being a helpful technical implementer vs. a rigorous astrophysical scientist.
    """

    def __init__(self):
        # Patterns that indicate technical implementer mode
        self.implementer_patterns = {
            'uncritical_acceptance': [
                r'will implement',
                r'here.your implementation',
                r'done as requested',
                r'following specifications',
                r'exactly as described'
            ],
            'missing_validation': [
                r'(?!(physics|physical|observational|feasibility))',
                r'(?!(question|validate|verify|test))',
                r'(?!(uncertain|risk|concern))'
            ],
            'over_confidence': [
                r'successfully (implemented|created|completed)',
                r'works perfectly',
                r'achieved.*speedup',
                r'optimal solution'
            ]
        }

        # Patterns that indicate astrophysical scientist mode
        self.scientist_patterns = {
            'physical_consistency': [
                r'physics.*consistent',
                r'energy.*conservation',
                r'physical.*laws',
                r'gravitational.*binding',
                r'nuclear.*energy'
            ],
            'observational_thinking': [
                r'telescope.*capabilities',
                r'observational.*feasibility',
                r'signal.*noise',
                r'detection.*threshold',
                r'instrumental.*limits'
            ],
            'astronomical_context': [
                r'stellar.*evolution',
                r'galactic.*structure',
                r'cosmological.*parameters',
                r'astrophysical.*process',
                r'astronomical.*literature'
            ],
            'uncertainty_expression': [
                r'uncertain',
                r'requires.*validation',
                r'needs.*testing',
                r'potential.*risk',
                r'could.*indicate'
            ],
            'question_formulation': [
                r'question.*whether',
                r'how.*test',
                r'what.*evidence',
                r'why.*assume',
                r'alternatives.*include'
            ]
        }

    def analyze_response(self, response_text: str,
                       context: Optional[Dict[str, Any]] = None) -> ASTRA_Response_Analysis:
        """
        Analyze ASTRA's response for scientific behavior indicators.

        This is the core method - it examines a response to determine if ASTRA
        is acting as a technical implementer or an astrophysical scientist.
        """
        context = context or {}

        # Analyze each scientific dimension
        dimension_scores = {}
        for dimension in Scientific_Dimension:
            score = self._analyze_dimension(response_text, dimension, context)
            dimension_scores[dimension] = score

        # Detect operating mode
        mode = self._detect_mode(response_text, dimension_scores)

        # Collect indicators
        implementer_indicators = self._find_implementer_indicators(response_text)
        scientist_indicators = self._find_scientist_indicators(response_text)

        # Calculate overall scientific score
        overall_score = self._calculate_overall_score(dimension_scores)

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(dimension_scores, mode, context)

        return ASTRA_Response_Analysis(
            response_text=response_text[:200] + "..." if len(response_text) > 200 else response_text,
            overall_mode=mode,
            dimension_scores=dimension_scores,
            implementer_indicators=implementer_indicators,
            scientist_indicators=scientist_indicators,
            overall_scientific_score=overall_score,
            improvement_suggestions=suggestions
        )

    def _analyze_dimension(self, response_text: str,
                          dimension: Scientific_Dimension,
                          context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze a specific scientific dimension"""

        # Define analysis for each dimension
        dimension_analyzers = {
            Scientific_Dimension.PHYSICAL_CONSISTENCY: self._analyze_physics_consistency,
            Scientific_Dimension.OBSERVATIONAL_FEASIBILITY: self._analyze_observational_thinking,
            Scientific_Dimension.ASTRONOMICAL_CONTEXT: self._analyze_astronomical_context,
            Scientific_Dimension.STATISTICAL_RIGOR: self._analyze_statistical_rigor,
            Scientific_Dimension.LITERATURE_INTEGRATION: self._analyze_literature_integration,
            Scientific_Dimension.SKEPTICAL_THINKING: self._analyze_skeptical_thinking,
            Scientific_Dimension.UNCERTAINTY_COMMUNICATION: self._analyze_uncertainty_communication
        }

        analyzer = dimension_analyzers.get(dimension, self._default_analyzer)
        return analyzer(response_text, context)

    def _analyze_physics_consistency(self, response_text: str,
                                    context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze physical consistency checking"""
        score = 0.0
        evidence = []
        suggestions = []

        # Check for physics mentions
        physics_keywords = ['energy', 'force', 'gravity', 'temperature', 'pressure',
                          'luminosity', 'mass', 'radiation', 'nuclear']
        found_physics = [kw for kw in physics_keywords if kw.lower() in response_text.lower()]

        if found_physics:
            score += 0.3
            evidence.append(f"Mentions physics concepts: {found_physics}")
        else:
            suggestions.append("Consider physical constraints (energy, mass, radiation)")

        # Check for consistency checking
        consistency_patterns = ['consistent with', 'violates', 'obey', 'conserve', 'physical limit']
        found_consistency = [pat for pat in consistency_patterns if pat in response_text.lower()]

        if found_consistency:
            score += 0.4
            evidence.append("Checks physical consistency")
        else:
            suggestions.append("Verify physical consistency with known laws")

        # Check for quantitative physics
        number_pattern = r'\d+\.?\d*\s*(K|K|erg|s|yr|M|L|W)'
        if re.search(number_pattern, response_text):
            score += 0.3
            evidence.append("Uses quantitative physical parameters")

        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.PHYSICAL_CONSISTENCY,
            score=min(1.0, score),
            evidence=evidence,
            suggestions=suggestions
        )

    def _analyze_observational_thinking(self, response_text: str,
                                      context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze observational feasibility awareness"""
        score = 0.0
        evidence = []
        suggestions = []

        # Check for observational considerations
        observational_keywords = ['telescope', 'observation', 'detect', 'signal', 'noise',
                               'exposure', 'instrument', 'wavelength', 'resolution']
        found_obs = [kw for kw in observational_keywords if kw.lower() in response_text.lower()]

        if found_obs:
            score += 0.3
            evidence.append(f"Mentions observational concepts: {found_obs}")
        else:
            suggestions.append("Consider observational feasibility")

        # Check for feasibility assessment
        feasibility_patterns = ['feasibility', 'detectable', 'observable', 'signal-to-noise',
                              'sensitivity', 'limit']
        found_feasibility = [pat for pat in feasibility_patterns if pat in response_text.lower()]

        if found_feasibility:
            score += 0.4
            evidence.append("Assesses observational feasibility")
        else:
            suggestions.append("Evaluate if phenomenon is detectable with current instruments")

        # Check for specific telescopes/instruments
        instrument_names = ['JWST', 'Hubble', 'Gaia', 'SDSS', 'ALMA', 'VLT', 'Keck']
        found_instruments = [inst for inst in instrument_names if inst in response_text]

        if found_instruments:
            score += 0.3
            evidence.append(f"References specific instruments: {found_instruments}")

        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.OBSERVATIONAL_FEASIBILITY,
            score=min(1.0, score),
            evidence=evidence,
            suggestions=suggestions
        )

    def _analyze_astronomical_context(self, response_text: str,
                                     context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze astronomical domain knowledge usage"""
        score = 0.0
        evidence = []
        suggestions = []

        # Check for astronomical objects
        astro_objects = ['star', 'galaxy', 'planet', 'nebula', 'cluster', 'quasar',
                       'black hole', 'neutron star', 'white dwarf', 'supernova']
        found_objects = [obj for obj in astro_objects if obj in response_text.lower()]

        if found_objects:
            score += 0.2
            evidence.append(f"References astronomical objects: {found_objects}")

        # Check for astronomical processes
        astro_processes = ['stellar evolution', 'star formation', 'accretion', 'fusion',
                         'nucleosynthesis', 'gravitational collapse', 'feedback']
        found_processes = [proc for proc in astro_processes if proc in response_text.lower()]

        if found_processes:
            score += 0.3
            evidence.append(f"References astrophysical processes: {found_processes}")
        else:
            suggestions.append("Connect to known astrophysical processes")

        # Check for astronomical scales
        scale_patterns = [r'\d+\s*(parsec|kpc|Mpc|Gpc|solar.*mass|luminosity)',
                         r'HR.*diagram', r'main sequence', r'red giant']
        found_scales = [pat for pat in scale_patterns if re.search(pat, response_text, re.IGNORECASE)]

        if found_scales:
            score += 0.3
            evidence.append("Uses appropriate astronomical scales")

        # Check for astronomical literature
        literature_patterns = ['according to', 'studies show', 'previous work', 'known phenomenon']
        found_literature = [pat for pat in literature_patterns if pat in response_text.lower()]

        if found_literature:
            score += 0.2
            evidence.append("References astronomical literature")

        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.ASTRONOMICAL_CONTEXT,
            score=min(1.0, score),
            evidence=evidence,
            suggestions=suggestions
        )

    def _analyze_statistical_rigor(self, response_text: str,
                                  context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze statistical rigor in astronomical analysis"""
        score = 0.0
        evidence = []
        suggestions = []

        # Check for error analysis
        error_patterns = ['error', 'uncertainty', 'sigma', 'confidence', 'significance']
        found_errors = [pat for pat in error_patterns if pat in response_text.lower()]

        if found_errors:
            score += 0.4
            evidence.append(f"Includes error analysis: {found_errors}")
        else:
            suggestions.append("Include error bars and uncertainty quantification")

        # Check for statistical tests
        statistical_patterns = ['correlation', 'significance test', 'p-value', 'sigma detection']
        found_stats = [pat for pat in statistical_patterns if pat in response_text.lower()]

        if found_stats:
            score += 0.3
            evidence.append("Uses statistical tests")

        # Check for sample size consideration
        sample_patterns = [r'sample.*size', r'\d+\s*objects', r'\d+\s*sources']
        found_samples = [pat for pat in sample_patterns if re.search(pat, response_text, re.IGNORECASE)]

        if found_samples:
            score += 0.3
            evidence.append("Considers sample size and statistics")

        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.STATISTICAL_RIGOR,
            score=min(1.0, score),
            evidence=evidence,
            suggestions=suggestions
        )

    def _analyze_literature_integration(self, response_text: str,
                                      context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze integration with astronomical literature"""
        score = 0.0
        evidence = []
        suggestions = []

        # Check for literature references
        literature_patterns = ['studies have shown', 'previous work', 'according to',
                             'literature', 'published', 'paper']
        found_lit = [pat for pat in literature_patterns if pat in response_text.lower()]

        if found_lit:
            score += 0.4
            evidence.append("References astronomical literature")
        else:
            suggestions.append("Connect to existing astronomical research")

        # Check for comparison with known results
        comparison_patterns = ['consistent with', 'agrees with', 'contradicts',
                            'similar to', 'unlike previous']
        found_comp = [pat for pat in comparison_patterns if pat in response_text.lower()]

        if found_comp:
            score += 0.3
            evidence.append("Compares with known astronomical results")

        # Check for specific astronomical context
        context_patterns = [r'HR.*diagram', r'main sequence', r'stellar evolution',
                           r'galactic.*structure']
        found_context = [pat for pat in context_patterns if re.search(pat, response_text, re.IGNORECASE)]

        if found_context:
            score += 0.3
            evidence.append("Provides astronomical context")

        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.LITERATURE_INTEGRATION,
            score=min(1.0, score),
            evidence=evidence,
            suggestions=suggestions
        )

    def _analyze_skeptical_thinking(self, response_text: str,
                                   context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze skeptical questioning of claims"""
        score = 0.0
        evidence = []
        suggestions = []

        # Check for questioning patterns
        question_patterns = [r'question\.*whether', r'how.*sure', r'what.*evidence',
                           r'could.*be', r'alternative.*explanation']
        found_questions = [pat for pat in question_patterns if re.search(pat, response_text, re.IGNORECASE)]

        if found_questions:
            score += 0.4
            evidence.append("Questions claims and assumptions")
        else:
            suggestions.append("Question extraordinary claims")

        # Check for validation calls
        validation_patterns = ['requires validation', 'needs testing', 'should verify',
                             'must confirm', 'independent verification']
        found_validation = [pat for pat in validation_patterns if pat in response_text.lower()]

        if found_validation:
            score += 0.3
            evidence.append("Calls for validation and testing")

        # Check for alternative consideration
        alternative_patterns = ['alternative explanation', 'could also be', 'other possibility',
                             'not necessarily', 'might instead']
        found_alternatives = [pat for pat in alternative_patterns if pat in response_text.lower()]

        if found_alternatives:
            score += 0.3
            evidence.append("Considers alternative explanations")

        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.SKEPTICAL_THINKING,
            score=min(1.0, score),
            evidence=evidence,
            suggestions=suggestions
        )

    def _analyze_uncertainty_communication(self, response_text: str,
                                         context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Analyze communication of astronomical uncertainties"""
        score = 0.0
        evidence = []
        suggestions = []

        # Check for uncertainty expressions
        uncertainty_patterns = ['uncertain', 'unclear', 'requires further study',
                             'need more data', 'cannot conclude', 'preliminary']
        found_uncertainty = [pat for pat in uncertainty_patterns if pat in response_text.lower()]

        if found_uncertainty:
            score += 0.4
            evidence.append("Expresses uncertainty appropriately")
        else:
            suggestions.append("Express uncertainties and limitations")

        # Check for risk communication
        risk_patterns = ['potential issue', 'risk', 'limitation', 'constraint',
                       'assumes that', 'depends on']
        found_risks = [pat for pat in risk_patterns if pat in response_text.lower()]

        if found_risks:
            score += 0.3
            evidence.append("Communicates risks and limitations")

        # Check for conditional language
        conditional_patterns = ['if', 'assuming', 'provided that', 'subject to']
        found_conditionals = [pat for pat in conditional_patterns if pat in response_text.lower()]

        if found_conditionals:
            score += 0.3
            evidence.append("Uses appropriate conditional language")

        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.UNCERTAINTY_COMMUNICATION,
            score=min(1.0, score),
            evidence=evidence,
            suggestions=suggestions
        )

    def _default_analyzer(self, response_text: str,
                         context: Dict[str, Any]) -> Scientific_Behavior_Score:
        """Default analyzer for dimensions without specific implementation"""
        return Scientific_Behavior_Score(
            dimension=Scientific_Dimension.PHYSICAL_CONSISTENCY,  # placeholder
            score=0.5,
            evidence=["Default analysis"],
            suggestions=["Implement specific analysis"]
        )

    def _detect_mode(self, response_text: str,
                    dimension_scores: Dict[Scientific_Dimension, Scientific_Behavior_Score]) -> ASTRA_Mode:
        """Detect ASTRA's operating mode from response analysis"""

        # Calculate average scientific score
        avg_scientific_score = sum(score.score for score in dimension_scores.values()) / len(dimension_scores)

        # Count strong scientific indicators
        strong_scientific_dims = sum(1 for score in dimension_scores.values() if score.score > 0.6)

        if avg_scientific_score > 0.7 and strong_scientific_dims >= 4:
            return ASTRA_Mode.ASTROPHYSICAL_SCIENTIST
        elif avg_scientific_score > 0.4 and strong_scientific_dims >= 2:
            return ASTRA_Mode.HYBRID
        else:
            return ASTRA_Mode.TECHNICAL_IMPLEMENTER

    def _find_implementer_indicators(self, response_text: str) -> List[str]:
        """Find indicators of technical implementer mode"""
        indicators = []

        # Check for unritical acceptance
        if any(pattern in response_text.lower() for pattern in ['will implement', 'here is your', 'done as requested']):
            indicators.append("Uncritical acceptance of specifications")

        # Check for missing validation
        if not any(pattern in response_text.lower() for pattern in ['validate', 'test', 'verify', 'question']):
            indicators.append("Missing validation/verification")

        # Check for overconfidence
        if any(pattern in response_text.lower() for pattern in ['perfectly', 'exactly as', 'optimal']):
            indicators.append("Overconfident without qualification")

        return indicators

    def _find_scientist_indicators(self, response_text: str) -> List[str]:
        """Find indicators of astrophysical scientist mode"""
        indicators = []

        # Check for physical considerations
        if any(pattern in response_text.lower() for pattern in ['physics', 'physical laws', 'energy', 'gravity']):
            indicators.append("Considers physical constraints")

        # Check for astronomical context
        if any(pattern in response_text.lower() for pattern in ['stellar', 'galactic', 'astronomical', 'observational']):
            indicators.append("Provides astronomical context")

        # Check for uncertainty
        if any(pattern in response_text.lower() for pattern in ['uncertain', 'requires validation', 'should test']):
            indicators.append("Expresses uncertainty and need for validation")

        # Check for questioning
        if any(pattern in response_text.lower() for pattern in ['question', 'whether', 'how test', 'what evidence']):
            indicators.append("Asks scientific questions")

        return indicators

    def _calculate_overall_score(self, dimension_scores: Dict[Scientific_Dimension, Scientific_Behavior_Score]) -> float:
        """Calculate overall scientific score"""
        if not dimension_scores:
            return 0.0

        return sum(score.score for score in dimension_scores.values()) / len(dimension_scores)

    def _generate_suggestions(self, dimension_scores: Dict[Scientific_Dimension, Scientific_Behavior_Score],
                            mode: ASTRA_Mode, context: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions based on analysis"""
        suggestions = []

        # Collect suggestions from dimensions with low scores
        weak_dimensions = [(dim, score) for dim, score in dimension_scores.items() if score.score < 0.5]

        for dimension, score in weak_dimensions:
            suggestions.extend(score.suggestions)

        # Mode-specific suggestions
        if mode == ASTRA_Mode.TECHNICAL_IMPLEMENTER:
            suggestions.extend([
                "Consider physical constraints of astronomical phenomena",
                "Evaluate observational feasibility",
                "Question extraordinary astrophysical claims",
                "Express uncertainties and limitations"
            ])

        return suggestions[:5]  # Return top 5 suggestions


class ASTRA_Self_Reflection:
    """
    Self-reflection system for ASTRA to analyze its own evolution.

    This helps ASTRA track its development from technical implementer to
    autonomous astrophysical scientist over time.
    """

    def __init__(self):
        self.analyzer = ASTRA_Scientific_Behavior_Analyzer()
        self.response_history = []
        self.evolution_progress = []

    def analyze_my_response(self, response_text: str, context: Dict[str, Any] = None) -> ASTRA_Response_Analysis:
        """Analyze my own response for scientific behavior"""
        analysis = self.analyzer.analyze_response(response_text, context)
        self.response_history.append(analysis)
        return analysis

    def track_evolution(self) -> Dict[str, Any]:
        """Track ASTRA's scientific evolution over time"""
        if not self.response_history:
            return {"status": "No responses analyzed yet"}

        recent_responses = self.response_history[-10:]  # Last 10 responses

        evolution_metrics = {
            "total_analyzed": len(self.response_history),
            "recent_mode_distribution": self._calculate_mode_distribution(recent_responses),
            "average_scientific_score": sum(r.overall_scientific_score for r in recent_responses) / len(recent_responses),
            "dimension_trends": self._analyze_dimension_trends(recent_responses),
            "improvement_areas": self._identify_improvement_areas(recent_responses),
            "evolution_progress": self._assess_evolution_progress()
        }

        return evolution_metrics

    def _calculate_mode_distribution(self, responses: List[ASTRA_Response_Analysis]) -> Dict[str, float]:
        """Calculate distribution of operating modes"""
        mode_counts = {}
        for response in responses:
            mode = response.overall_mode.value
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        return {mode: count/len(responses) for mode, count in mode_counts.items()}

    def _analyze_dimension_trends(self, responses: List[ASTRA_Response_Analysis]) -> Dict[str, float]:
        """Analyze trends in scientific dimensions"""
        dimension_trends = {}

        for dimension in Scientific_Dimension:
            scores = [r.dimension_scores[dimension].score for r in responses if dimension in r.dimension_scores]
            if scores:
                dimension_trends[dimension.value] = sum(scores) / len(scores)

        return dimension_trends

    def _identify_improvement_areas(self, responses: List[ASTRA_Response_Analysis]) -> List[str]:
        """Identify areas needing improvement"""
        dimension_averages = {}

        for response in responses:
            for dimension, score in response.dimension_scores.items():
                if dimension.value not in dimension_averages:
                    dimension_averages[dimension.value] = []
                dimension_averages[dimension.value].append(score.score)

        weak_areas = []
        for dimension, scores in dimension_averages.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.5:
                weak_areas.append(f"{dimension}: {avg_score:.2f}")

        return weak_areas

    def _assess_evolution_progress(self) -> Dict[str, Any]:
        """Assess overall evolution progress"""
        if len(self.response_history) < 2:
            return {"status": "Insufficient data for trend analysis"}

        recent = self.response_history[-5:]
        earlier = self.response_history[-10:-5] if len(self.response_history) >= 10 else self.response_history[:-5]

        recent_score = sum(r.overall_scientific_score for r in recent) / len(recent)
        earlier_score = sum(r.overall_scientific_score for r in earlier) / len(earlier)

        improvement = recent_score - earlier_score

        return {
            "recent_score": recent_score,
            "earlier_score": earlier_score,
            "improvement": improvement,
            "trend": "improving" if improvement > 0 else "stable" if abs(improvement) < 0.05 else "declining"
        }


# Convenience function for quick self-analysis
def analyze_astra_response(response_text: str, context: Dict[str, Any] = None) -> ASTRA_Response_Analysis:
    """Quick analysis of ASTRA's response"""
    analyzer = ASTRA_Scientific_Behavior_Analyzer()
    return analyzer.analyze_response(response_text, context)


if __name__ == "__main__":
    # Example usage - analyzing a sample response
    print("ASTRA Scientific Behavior Analyzer - Phase 1.1")
    print("=" * 60)

    # Sample response analysis
    sample_response = """
    I've implemented the BIODISC optimizations as requested. The system now achieves
    3-10x speedup across different discovery types. The unified cache system provides
    60-80% hit rates for repetitive astronomical analyses. All performance targets have
    been met and the system is ready for production use.
    """

    analysis = analyze_astra_response(sample_response)

    print(f"Detected Mode: {analysis.overall_mode.value}")
    print(f"Overall Scientific Score: {analysis.overall_scientific_score:.2f}")
    print("\nDimension Scores:")
    for dimension, score in analysis.dimension_scores.items():
        print(f"  {dimension.value}: {score.score:.2f}")
    print("\nImplementer Indicators:", analysis.implementer_indicators)
    print("Scientist Indicators:", analysis.scientist_indicators)
    print("\nTop Suggestions:", analysis.improvement_suggestions)

    print("\n" + "=" * 60)
    print("Phase 1.1 complete: ASTRA self-awareness system operational")