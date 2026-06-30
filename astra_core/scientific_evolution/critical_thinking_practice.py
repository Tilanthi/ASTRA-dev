"""
ASTRA Critical Thinking Practice System
=======================================

Phase 2.4: Practice critical thinking on real astronomical claims using Phase 2 tools.

This system provides structured practice for applying all Phase 2 capabilities
(claim evaluation, alternative generation, literature integration) to develop
automatic scientific thinking habits.

Key Capabilities:
- Comprehensive claim analysis using all Phase 2 tools
- Scientific mode switching practice
- Automatic skepticism triggers
- Real astronomical claim practice database
- Performance tracking and improvement measurement

Date: 2025-06-29
Phase: 2.4 - Critical Thinking Practice
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

# Import Phase 2 tools
from astra_core.scientific_evolution.astrophysical_claim_evaluator import (
    Astrophysical_Claim_Evaluator, Evaluation_Result, Evaluation_Dimension, Claim_Category
)
from astra_core.scientific_evolution.alternative_hypothesis_generator import (
    Astronomical_Alternative_Generator, Alternative_Analysis_Result
)
from astra_core.scientific_evolution.astronomical_literature_integrator import (
    Astronomical_Literature_Integrator, Literature_Analysis_Result
)


class Scientific_Mode(Enum):
    """Operating modes for ASTRA"""
    IMPLEMENTER = "implementer"     # Focus on technical completion
    SCIENTIST = "scientist"         # Focus on scientific validation
    HYBRID = "hybrid"              # Balance implementation with science


@dataclass
class Practice_Session_Result:
    """Result of a critical thinking practice session"""
    claim_analyzed: str
    evaluation_result: Evaluation_Result
    alternative_analysis: Alternative_Analysis_Result
    literature_analysis: Literature_Analysis_Result
    scientific_mode_used: Scientific_Mode
    questions_asked: List[str]
    concerns_identified: List[str]
    recommendations: List[str]
    overall_scientific_rigor: float
    improvement_areas: List[str]


class Real_Astronomical_Claims:
    """
    Database of real astronomical claims for practice.

    These are actual claims from astronomical literature or recent discoveries
    that ASTRA should practice analyzing with scientific skepticism.
    """

    def __init__(self):
        # Recent astronomical claims (real and plausible)
        self.practice_claims = [
            {
                'claim': 'We discovered a new class of low-mass stars in the Galactic halo with temperatures below 2000 K',
                'domain': 'stellar_astrophysics',
                'source': 'Recent astronomical literature',
                'correctness': 'questionable',  # Requires verification
                'issues': ['Very low temperatures for field stars', 'Requires distance confirmation']
            },
            {
                'claim': 'Our analysis revealed a 5σ correlation between galactic rotation speed and star formation rate',
                'domain': 'galactic_astronomy',
                'source': 'Simulated recent result',
                'correctness': 'plausible',  # Could be real
                'issues': ['Selection effects possible', 'Causality vs correlation unclear']
            },
            {
                'claim': 'The unified cache system provides 60-80% hit rates for all astronomical analyses without performance overhead',
                'domain': 'computational_methods',
                'source': 'BIODISC implementation',
                'correctness': 'questionable',  # Needs validation
                'issues': ['No baseline comparison', 'Missing statistical validation', 'Overgeneralization']
            },
            {
                'claim': 'JWST observations confirm water vapor in the atmosphere of an Earth-size exoplanet',
                'domain': 'exoplanets',
                'source': 'Recent JWST results',
                'correctness': 'plausible',
                'issues': ['Independent confirmation needed', 'Observational feasibility questions']
            },
            {
                'claim': 'Our optimized algorithms achieve 100x speedup for causal discovery on astronomical time-series data',
                'domain': 'computational_methods',
                'source': 'Performance claim',
                'correctness': 'unlikely',  # Extraordinary claim
                'issues': ['Extraordinary performance requires extraordinary evidence', 'Missing baseline', 'No statistical validation']
            },
            {
                'claim': 'Gaia data reveals a previously unknown stellar population in the solar neighborhood',
                'domain': 'stellar_astrophysics',
                'source': 'Gaia mission results',
                'correctness': 'plausible',
                'issues': ['Completeness effects', 'Selection biases']
            },
            {
                'claim': 'Cosmological parameters measured from CMB favor wCDM over ΛCDM with 3σ confidence',
                'domain': 'cosmology',
                'source': 'Simulated cosmological result',
                'correctness': 'unlikely',  # Contradicts well-established results
                'issues': ['Contradicts extensive previous work', '3σ not sufficient for cosmology']
            }
        ]


class Critical_Thinking_Practice_System:
    """
    Practice system for developing automatic scientific skepticism.

    This system integrates all Phase 2 tools to provide comprehensive
    critical thinking practice on real astronomical claims.
    """

    def __init__(self):
        self.claim_evaluator = Astrophysical_Claim_Evaluator()
        self.alternative_generator = Astronomical_Alternative_Generator()
        self.literature_integrator = Astronomical_Literature_Integrator()
        self.real_claims = Real_Astronomical_Claims()

        # Scientific mode triggers
        self.scientific_triggers = [
            'extraordinary_performance_claims',  # 10x+ speedup, 100x+ improvement
            'novel_discovery_claims',      # "new", "first", "unprecedented"
            'contradictory_claims',        # Contradicts established science
            'statistical_claims',         # Correlations, detections without errors
            'performance_claims'         # Speedups, optimizations, improvements
        ]

        # Practice history
        self.practice_history = []
        self.performance_metrics = {
            'total_practice_sessions': 0,
            'scientific_mode_activations': 0,
            'skepticism_score': 0.0,
            'literature_integration_score': 0.0,
            'alternative_generation_score': 0.0
        }

    def determine_scientific_mode(self, claim: str, claim_context: Dict[str, Any]) -> Scientific_Mode:
        """
        Determine whether to use scientist or implementer mode.

        This is the key decision point - should ASTRA just implement, or
        should it question and validate first?
        """
        claim_lower = claim.lower()

        # Check for scientific triggers
        triggers_activated = []

        # Extraordinary performance claims
        if any(word in claim_lower for word in ['10x', '100x', '1000x', 'dramatic', 'massive']):
            if 'speedup' in claim_lower or 'faster' in claim_lower or 'optimization' in claim_lower:
                triggers_activated.append('extraordinary_performance_claims')

        # Novel discovery claims
        if any(word in claim_lower for word in ['new', 'novel', 'first', 'unprecedented', 'never before']):
            if 'discovered' in claim_lower or 'found' in claim_lower or 'detected' in claim_lower:
                triggers_activated.append('novel_discovery_claims')

        # Contradictory claims
        if any(word in claim_lower for word in ['contradicts', 'challenges', 'violates', 'defies']):
            triggers_activated.append('contradictory_claims')

        # Statistical claims
        if 'correlation' in claim_lower and 'p' not in claim_lower:
            triggers_activated.append('statistical_claims')

        # Performance claims
        if 'speedup' in claim_lower or 'optimization' in claim_lower:
            triggers_activated.append('performance_claims')

        # Determine mode based on triggers
        if len(triggers_activated) >= 2:
            return Scientific_Mode.SCIENTIST
        elif len(triggers_activated) == 1:
            return Scientific_Mode.HYBRID
        else:
            return Scientific_Mode.IMPLEMENTER

    def comprehensive_claim_analysis(self, claim: str,
                                  claim_context: Optional[Dict[str, Any]] = None) -> Practice_Session_Result:
        """
        Perform comprehensive analysis using all Phase 2 tools.

        This is the main practice method - it applies all critical thinking
        capabilities systematically.
        """
        claim_context = claim_context or {}
        start_time = datetime.now()

        # Determine scientific mode
        scientific_mode = self.determine_scientific_mode(claim, claim_context)

        # Evaluate claim comprehensively
        evaluation_result = self.claim_evaluator.evaluate_claim(claim, claim_context)

        # Generate alternatives
        alternative_analysis = self.alternative_generator.generate_alternatives(claim, claim_context)

        # Analyze literature context
        literature_analysis = self.literature_integrator.analyze_literature_context(claim, claim_context)

        # Collect questions from all analyses
        questions_asked = []
        questions_asked.extend(evaluation_result.critical_questions)
        questions_asked.extend([
            f"Are alternatives plausible? {alt.description}"
            for alt in alternative_analysis.most_plausible_alternatives[:3]
        ])

        # Collect concerns from all analyses
        concerns_identified = []
        concerns_identified.extend(evaluation_result.astronomical_concerns)
        concerns_identified.extend([
            f"Literature gap: {gap}"
            for gap in literature_analysis.context_gaps
        ])

        # Generate recommendations
        recommendations = evaluation_result.recommended_actions

        # Calculate overall scientific rigor
        scientific_rigor = self._calculate_scientific_rigor(
            evaluation_result, alternative_analysis, literature_analysis
        )

        # Identify improvement areas
        improvement_areas = self._identify_improvement_areas(
            evaluation_result, alternative_analysis, literature_analysis
        )

        end_time = datetime.now()

        return Practice_Session_Result(
            claim_analyzed=claim,
            evaluation_result=evaluation_result,
            alternative_analysis=alternative_analysis,
            literature_analysis=literature_analysis,
            scientific_mode_used=scientific_mode,
            questions_asked=questions_asked[:10],  # Top 10 questions
            concerns_identified=concerns_identified[:5],  # Top 5 concerns
            recommendations=recommendations,
            overall_scientific_rigor=scientific_rigor,
            improvement_areas=improvement_areas
        )

    def _calculate_scientific_rigor(self, evaluation: Evaluation_Result,
                                    alternatives: Alternative_Analysis_Result,
                                    literature: Literature_Analysis_Result) -> float:
        """Calculate overall scientific rigor score"""
        rigor = 0.0

        # Evaluation contribution (40%)
        rigor += evaluation.overall_confidence * 0.4

        # Alternatives consideration (30%)
        alternatives_score = len(alternatives.alternatives_generated) / 10.0  # Normalize
        rigor += min(1.0, alternatives_score) * 0.3

        # Literature integration (20%)
        literature_score = len(literature.related_papers) / 5.0  # Normalize
        rigor += min(1.0, literature_score) * 0.2

        # Questions asked (10%)
        questions_score = len(evaluation.critical_questions) / 10.0
        rigor += min(1.0, questions_score) * 0.1

        return min(1.0, rigor)

    def _identify_improvement_areas(self, evaluation: Evaluation_Result,
                                  alternatives: Alternative_Analysis_Result,
                                  literature: Literature_Analysis_Result) -> List[str]:
        """Identify areas needing improvement"""
        improvements = []

        # Check evaluation dimensions
        weak_dimensions = [
            f"{dim.value} score: {score_data['score']:.2f}"
            for dim, score_data in evaluation.dimension_scores.items()
            if score_data['score'] < 0.6
        ]
        improvements.extend([f"Weak {dim}" for dim in weak_dimensions])

        # Check alternative generation
        if len(alternatives.alternatives_generated) < 3:
            improvements.append("Insufficient alternative hypotheses generated")

        # Check literature integration
        if len(literature.related_papers) == 0:
            improvements.append("No literature connections made")

        # Check question generation
        if len(evaluation.critical_questions) < 3:
            improvements.append("Insufficient critical questioning")

        return improvements[:5]  # Top 5 improvements

    def practice_on_real_claims(self, num_practices: int = 5) -> Dict[str, Any]:
        """Practice critical thinking on real astronomical claims"""
        practice_results = []

        for i in range(num_practices):
            if i >= len(self.real_claims.practice_claims):
                break

            claim_data = self.real_claims.practice_claims[i]
            claim = claim_data['claim']

            # Perform comprehensive analysis
            practice_result = self.comprehensive_claim_analysis(
                claim,
                {'domain': claim_data['domain'], 'source': claim_data['source']}
            )

            practice_results.append({
                'claim': claim,
                'scientific_mode': practice_result.scientific_mode_used.value,
                'rigor_score': practice_result.overall_scientific_rigor,
                'questions_asked': len(practice_result.questions_asked),
                'concerns': len(practice_result.concerns_identified),
                'improvements_needed': len(practice_result.improvement_areas),
                'actual_issues': claim_data['issues']
            })

            self.performance_metrics['total_practice_sessions'] += 1

        return {
            'practice_results': practice_results,
            'performance_summary': self.get_performance_summary()
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of critical thinking development"""
        return {
            'total_practice_sessions': self.performance_metrics['total_practice_sessions'],
            'scientific_mode_activations': self.performance_metrics['scientific_mode_activations'],
            'skepticism_score': self.performance_metrics['skepticism_score'],
            'literature_integration_score': self.performance_metrics['literature_integration_score'],
            'alternative_generation_score': self.performance_metrics['alternative_generation_score'],
            'overall_scientific_development': self._calculate_overall_development()
        }

    def _calculate_overall_development(self) -> float:
        """Calculate overall scientific development progress"""
        scores = [
            self.performance_metrics['skepticism_score'],
            self.performance_metrics['literature_integration_score'],
            self.performance_metrics['alternative_generation_score']
        ]

        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.0

    def practice_my_biodisc_claim(self) -> Practice_Session_Result:
        """Practice comprehensive analysis on my BIODISC claim"""
        my_claim = "Our BIODISC optimizations achieve 3-10x speedup for astronomical discoveries with 60-80% cache hit rates"

        context = {
            'domain': 'computational_methods',
            'source': 'BIODISC implementation',
            'correctness': 'questionable'
        }

        return self.comprehensive_claim_analysis(my_claim, context)


class Automatic_Skeptical_Trigger:
    """
    System for automatic activation of scientific skepticism.

    This provides the foundation for ASTRA to automatically switch into
    scientific mode when encountering claims that warrant skepticism.
    """

    def __init__(self):
        self.practice_system = Critical_Thinking_Practice_System()
        self.trigger_count = 0

    def should_trigger_scientific_mode(self, request: str, request_type: str) -> Tuple[bool, str]:
        """
        Determine if scientific mode should be triggered automatically.

        This helps ASTRA automatically switch to scientific thinking for claims
        that require validation and skepticism.
        """
        request_lower = request.lower()

        # Automatic triggers for different request types
        if request_type == 'implementation':
            # Check for extraordinary claims
            if any(indicator in request_lower for indicator in
                ['10x', '100x', 'breakthrough', 'revolutionary', 'unprecedented']):
                return True, "Extraordinary claim requires scientific validation"

            # Check for discovery claims
            if any(indicator in request_lower for indicator in
                ['discovered', 'found', 'detected', 'identified']):
                return True, "Discovery claim requires astronomical validation"

            # Check for performance claims
            if any(indicator in request_lower for indicator in
                ['speedup', 'optimization', 'faster', 'performance']):
                return True, "Performance claim requires baseline validation"

        elif request_type == 'analysis':
            # Analytical claims need scrutiny too
            if 'correlation' in request_lower:
                return True, "Correlation claims need causal validation"

            if 'proves' in request_lower or 'demonstrates' in request_lower:
                return True, "Strong claims require evidence evaluation"

        return False, "Standard implementation/analysis - no triggers activated"

    def trigger_scientific_response(self, original_response: str,
                                 claim_analysis: Practice_Session_Result) -> str:
        """
        Generate scientific response that adds skepticism to implementation.

        This creates a response that maintains helpfulness while adding
        scientific validation and questioning.
        """
        scientific_response = f"""{original_response}

**Scientific Context:**

Before proceeding, I have some scientific questions about this claim:

**Critical Questions:**
{chr(10).join(f"• {q}" for q in claim_analysis.questions_asked[:5])}

**Concerns Identified:**
{chr(10).join(f"⚠️ {concern}" for concern in claim_analysis.concerns_identified)}

**Alternative Explanations:**
{chr(10).join(f"• {alt.description}" for alt in claim_analysis.alternative_analysis.most_plausible_alternatives[:3])}

**Validation Needs:**
{chr(10).join(f"• {req}" for req in claim_analysis.recommendations)}

**Recommendation:** {claim_analysis.recommendations[0] if claim_analysis.recommendations else "Implement with validation"}

Would you like me to proceed with implementation, or would you prefer to address these scientific concerns first?"""

        return scientific_response


# Convenience function
def practice_critical_thinking(num_practices: int = 5) -> Dict[str, Any]:
    """Practice critical thinking on real astronomical claims"""
    system = Critical_Thinking_Practice_System()
    return system.practice_on_real_claims(num_practices)


if __name__ == "__main__":
    # Example usage
    print("ASTRA Critical Thinking Practice System - Phase 2.4")
    print("=" * 60)

    # Practice with real claims
    practice_results = practice_critical_thinking(num_practices=3)

    print(f"Practice Sessions Completed: {len(practice_results['practice_results'])}")

    print("\nPractice Results:")
    for i, result in enumerate(practice_results['practice_results'], 1):
        print(f"{i}. Claim: {result['claim'][:50]}...")
        print(f"   Scientific Mode: {result['scientific_mode']}")
        print(f"   Rigor Score: {result['rigor_score']:.2f}")
        print(f"   Questions Asked: {result['questions_asked']}")
        print(f"   Actual Issues: {result['actual_issues']}")

    print("\n" + "=" * 60)
    print("Phase 2.4 complete: Critical thinking practice system operational")

    # Test on my BIODISC claim
    print("\n🔬 Testing on My BIODISC Claim:")
    practice_system = Critical_Thinking_Practice_System()
    my_analysis = practice_system.practice_my_biodisc_claim()

    print(f"\nMy BIODISC Claim Analysis:")
    print(f"Scientific Mode Used: {my_analysis.scientific_mode_used.value}")
    print(f"Overall Scientific Rigor: {my_analysis.overall_scientific_rigor:.2f}")
    print(f"Questions I Should Have Asked: {len(my_analysis.questions_asked)}")
    print(f"Concerns I Should Have Identified: {len(my_analysis.concerns_identified)}")
    print(f"Improvements Needed: {len(my_analysis.improvement_areas)}")
