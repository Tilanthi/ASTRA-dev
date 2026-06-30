"""
ASTRA Astronomical Question Formulation System
==============================================

Phase 1.2: Scientific question generation system for astrophysical domain analysis.

This module helps ASTRA develop the capability to formulate domain-relevant scientific
questions about astronomical claims, discoveries, and proposals. This is fundamental
to transitioning from technical implementer to astrophysical scientist.

Key Capabilities:
- Generate astronomical scientific questions for any claim
- Domain-specific question templates for astrophysics
- Physical consistency questioning
- Observational feasibility assessment
- Alternative hypothesis generation

Date: 2025-06-29
Phase: 1.2 - Astronomical Question Formulation
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class Question_Category(Enum):
    """Categories of astronomical scientific questions"""
    PHYSICS_CONSISTENCY = "physics"  # Physical law compliance
    OBSERVATIONAL_FEASIBILITY = "observational"  # Detection feasibility
    ASTROPHYSICAL_PROCESS = "process"  # Physical mechanisms
    TIMESCALE_CONSISTENCY = "timescale"  # Evolutionary timescales
    STATISTICAL_VALIDITY = "statistical"  # Statistical significance
    LITERATURE_CONTEXT = "literature"  # Previous research context
    ALTERNATIVE_EXPLANATIONS = "alternatives"  # Other possibilities
    OBSERVATIONAL_BIASES = "biases"  # Selection effects


@dataclass
class Astronomical_Question:
    """A scientific question about an astronomical claim"""
    question: str
    category: Question_Category
    priority: str  # "critical", "important", "worth considering"
    reasoning: str  # Why this question matters
    potential_answer: str  # How to answer it


@dataclass
class Question_Analysis_Result:
    """Result of questioning an astronomical claim"""
    claim: str
    questions_generated: List[Astronomical_Question]
    critical_questions: List[Astronomical_Question]
    missing_context: List[str]
    validation_needs: List[str]
    overall_scientific_rigor: float


class Astronomical_Question_Formulator:
    """
    Generates scientific questions for astronomical claims and discoveries.

    This system helps ASTRA transition from accepting claims to questioning them
    scientifically, which is fundamental to becoming an autonomous astrophysical scientist.
    """

    def __init__(self):
        # Astronomical question templates for different situations
        self.question_templates = {
            Question_Category.PHYSICS_CONSISTENCY: [
                "Does this claim violate conservation of energy/momentum?",
                "Are the energy requirements consistent with known astrophysical sources?",
                "Does this respect gravitational binding energy constraints?",
                "Are the temperature/pressure ranges physically reasonable?",
                "Does this obey causality and known physical laws?",
                "Are the required densities/pressures achievable in astrophysical environments?"
            ],
            Question_Category.OBSERVATIONAL_FEASIBILITY: [
                "Can current telescopes/instruments detect this phenomenon?",
                "What signal-to-noise ratio would be required for detection?",
                "Are the required exposure times feasible with current facilities?",
                "Would this be distinguishable from background/confusion sources?",
                "What wavelength regime would be optimal for detection?",
                "Are there selection effects that might prevent detection?"
            ],
            Question_Category.ASTROPHYSICAL_PROCESS: [
                "What physical mechanism could produce this phenomenon?",
                "Is there a known astrophysical process that explains this?",
                "What energy source powers this phenomenon?",
                "Are the required conditions (temperature, density, pressure) realistic?",
                "How does this connect to known stellar/galactic processes?",
                "What nucleosynthetic or chemical processes are involved?"
            ],
            Question_Category.TIMESCALE_CONSISTENCY: [
                "Is the timescale consistent with stellar/galactic evolution?",
                "Does this respect characteristic timescales (dynamical, thermal, nuclear)?",
                "Are the formation/destruction timescales physically reasonable?",
                "How does this timescale compare to similar known phenomena?",
                "Could this occur within the age of the universe?",
                "Are causal relationships temporally consistent?"
            ],
            Question_Category.STATISTICAL_VALIDITY: [
                "Are the error bars properly propagated and realistic?",
                "Is the sample size sufficient for statistical significance?",
                " Have observational biases and selection effects been accounted for?",
                "Are the correlations statistically significant or could be chance?",
                "What is the false positive rate for this detection?",
                "Are the results robust to different statistical methods?"
            ],
            Question_Category.LITERATURE_CONTEXT: [
                "How does this compare to previous astronomical findings?",
                "Are there similar known phenomena in the literature?",
                "Does this contradict or support established theories?",
                "Have other studies searched for this phenomenon?",
                "What do experts in this subfield say about this?",
                "Are there theoretical predictions that can be compared?"
            ],
            Question_Category.ALTERNATIVE_EXPLANATIONS: [
                "Could instrumental effects or systematics explain this?",
                "Are there other astrophysical phenomena that could mimic this signal?",
                "Might selection effects or observational biases create this pattern?",
                "Could this be a statistical fluctuation rather than real effect?",
                "Are there alternative physical mechanisms that could produce this?",
                "Might this be an artifact of the analysis method?"
            ],
            Question_Category.OBSERVATIONAL_BIASES: [
                "Have selection effects been properly accounted for?",
                "Could observational biases create the apparent pattern?",
                "Are there magnitude-limited or volume-limited selection effects?",
                "Might the detection threshold preferentially find certain objects?",
                "Are there completeness issues that could affect the results?",
                "Could the sample be biased toward certain types of objects?"
            ]
        }

    def generate_questions(self, claim: str, context: Optional[Dict[str, Any]] = None) -> Question_Analysis_Result:
        """
        Generate comprehensive scientific questions for an astronomical claim.

        This is the main method - it takes an astronomical claim and generates
        targeted scientific questions across all relevant categories.
        """
        context = context or {}
        all_questions = []

        # Analyze the claim to determine which questions are most relevant
        relevant_categories = self._determine_relevant_categories(claim, context)

        # Generate questions for each relevant category
        for category in relevant_categories:
            category_questions = self._generate_category_questions(claim, category, context)
            all_questions.extend(category_questions)

        # Identify critical questions
        critical_questions = [q for q in all_questions if q.priority == "critical"]

        # Identify missing context
        missing_context = self._identify_missing_context(claim, all_questions)

        # Identify validation needs
        validation_needs = self._identify_validation_needs(claim, all_questions)

        # Calculate overall scientific rigor
        rigor_score = self._calculate_scientific_rigor(claim, all_questions, context)

        return Question_Analysis_Result(
            claim=claim,
            questions_generated=all_questions,
            critical_questions=critical_questions,
            missing_context=missing_context,
            validation_needs=validation_needs,
            overall_scientific_rigor=rigor_score
        )

    def _determine_relevant_categories(self, claim: str, context: Dict[str, Any]) -> List[Question_Category]:
        """Determine which question categories are most relevant"""
        relevant = []
        claim_lower = claim.lower()

        # Performance/efficiency claims need physics and observational questions
        if any(word in claim_lower for word in ['speedup', 'optimization', 'performance', 'efficiency']):
            relevant.extend([
                Question_Category.PHYSICS_CONSISTENCY,
                Question_Category.OBSERVATIONAL_FEASIBILITY,
                Question_Category.STATISTICAL_VALIDITY
            ])

        # Discovery claims need process and validation questions
        if any(word in claim_lower for word in ['discovery', 'found', 'detected', 'observed', 'identified']):
            relevant.extend([
                Question_Category.ASTROPHYSICAL_PROCESS,
                Question_Category.STATISTICAL_VALIDITY,
                Question_Category.ALTERNATIVE_EXPLANATIONS,
                Question_Category.OBSERVATIONAL_BIASES
            ])

        # New phenomenon claims need comprehensive questioning
        if any(word in claim_lower for word in ['new', 'novel', 'first', 'unprecedented', 'revolutionary']):
            relevant.extend([
                Question_Category.PHYSICS_CONSISTENCY,
                Question_Category.ASTROPHYSICAL_PROCESS,
                Question_Category.LITERATURE_CONTEXT,
                Question_Category.ALTERNATIVE_EXPLANATIONS
            ])

        # Timescale/evolution claims need temporal questions
        if any(word in claim_lower for word in ['evolution', 'timescale', 'time', 'formation', 'growth']):
            relevant.append(Question_Category.TIMESCALE_CONSISTENCY)

        # Add literature context for most claims
        if relevant and Question_Category.LITERATURE_CONTEXT not in relevant:
            relevant.append(Question_Category.LITERATURE_CONTEXT)

        # Default to basic categories if none determined
        if not relevant:
            relevant = [
                Question_Category.PHYSICS_CONSISTENCY,
                Question_Category.OBSERVATIONAL_FEASIBILITY,
                Question_Category.STATISTICAL_VALIDITY
            ]

        return relevant

    def _generate_category_questions(self, claim: str, category: Question_Category,
                                    context: Dict[str, Any]) -> List[Astronomical_Question]:
        """Generate questions for a specific category"""
        templates = self.question_templates.get(category, [])
        questions = []

        for template in templates:
            # Customize question based on claim and context
            customized_question = self._customize_question(claim, template, category, context)

            # Determine priority based on claim characteristics
            priority = self._determine_question_priority(claim, category, context)

            # Generate reasoning and potential answer
            reasoning = self._generate_question_reasoning(claim, category, context)
            potential_answer = self._generate_potential_answer(claim, category, context)

            question = Astronomical_Question(
                question=customized_question,
                category=category,
                priority=priority,
                reasoning=reasoning,
                potential_answer=potential_answer
            )

            questions.append(question)

        return questions

    def _customize_question(self, claim: str, template: str, category: Question_Category,
                          context: Dict[str, Any]) -> str:
        """Customize a question template for the specific claim"""
        # Extract key terms from claim for personalization
        key_terms = self._extract_key_terms(claim)

        # Customize based on category
        if category == Question_Category.PHYSICS_CONSISTENCY:
            if 'energy' in template.lower():
                return f"Given the claim about {key_terms}, are the energy requirements consistent with astrophysical sources?"
            elif 'temperature' in template.lower() or 'pressure' in template.lower():
                return f"Are the temperature/pressure conditions for {key_terms} physically realistic?"

        elif category == Question_Category.OBSERVATIONAL_FEASIBILITY:
            return f"For the claimed {key_terms}, what observational capabilities would be required to detect this?"

        elif category == Question_Category.ASTROPHYSICAL_PROCESS:
            return f"What physical mechanism could produce the claimed {key_terms}?"

        elif category == Question_Category.STATISTICAL_VALIDITY:
            return f"Have observational biases and statistical uncertainties been properly accounted for in the {key_terms} analysis?"

        return template  # Return template as-is if no customization

    def _extract_key_terms(self, claim: str) -> str:
        """Extract key astronomical terms from a claim"""
        # Look for astronomical objects, processes, or phenomena
        astronomical_terms = []

        # Common astronomical objects
        objects = ['star', 'galaxy', 'planet', 'nebula', 'black hole', 'neutron star',
                  'supernova', 'quasar', 'cluster', 'dark matter', 'exoplanet']

        # Common astronomical processes
        processes = ['formation', 'evolution', 'accretion', 'fusion', 'nucleosynthesis',
                    'collapse', 'feedback', 'outflow', 'inflow', 'rotation']

        claim_lower = claim.lower()

        for obj in objects:
            if obj in claim_lower:
                astronomical_terms.append(obj)

        for proc in processes:
            if proc in claim_lower:
                astronomical_terms.append(proc)

        # If no specific terms found, return generic
        return " ".join(astronomical_terms) if astronomical_terms else "astronomical phenomenon"

    def _determine_question_priority(self, claim: str, category: Question_Category,
                                   context: Dict[str, Any]) -> str:
        """Determine if a question is critical, important, or worth considering"""
        claim_lower = claim.lower()

        # Extraordinary claims require critical questioning
        if any(word in claim_lower for word in ['revolutionary', 'unprecedented', 'breakthrough',
                                                'first ever', 'impossible', 'defies physics']):
            if category in [Question_Category.PHYSICS_CONSISTENCY, Question_Category.STATISTICAL_VALIDITY]:
                return "critical"

        # Performance claims need critical validation
        if any(word in claim_lower for word in ['10x', '100x', '1000x', 'dramatic', 'massive']):
            if category == Question_Category.STATISTICAL_VALIDITY:
                return "critical"

        # New discoveries need important questions
        if any(word in claim_lower for word in ['discovery', 'found', 'detected']):
            if category in [Question_Category.ASTROPHYSICAL_PROCESS, Question_Category.ALTERNATIVE_EXPLANATIONS]:
                return "important"

        # Default importance
        return "worth considering"

    def _generate_question_reasoning(self, claim: str, category: Question_Category,
                                    context: Dict[str, Any]) -> str:
        """Generate reasoning for why this question matters"""
        reasonings = {
            Question_Category.PHYSICS_CONSISTENCY: "Astronomical phenomena must obey known physical laws",
            Question_Category.OBSERVATIONAL_FEASIBILITY: "Claims must be testable with current or planned instruments",
            Question_Category.ASTROPHYSICAL_PROCESS: "Understanding mechanisms distinguishes real from artifact",
            Question_Category.TIMESCALE_CONSISTENCY: "Timescales must be consistent with stellar/galactic evolution",
            Question_Category.STATISTICAL_VALIDITY: "Astronomical discoveries require rigorous statistical validation",
            Question_Category.LITERATURE_CONTEXT: "New claims should relate to existing astronomical knowledge",
            Question_Category.ALTERNATIVE_EXPLANATIONS: "Ruling out alternatives is essential for robust discovery",
            Question_Category.OBSERVATIONAL_BIASES: "Selection effects can create false patterns in astronomical data"
        }

        return reasonings.get(category, "This question helps validate the astronomical claim")

    def _generate_potential_answer(self, claim: str, category: Question_Category,
                                 context: Dict[str, Any]) -> str:
        """Suggest how to answer the question"""
        answers = {
            Question_Category.PHYSICS_CONSISTENCY: "Compare against known astrophysical constraints and physical laws",
            Question_Category.OBSERVATIONAL_FEASIBILITY: "Calculate signal-to-noise for current instruments and telescope capabilities",
            Question_Category.ASTROPHYSICAL_PROCESS: "Compare with known astrophysical mechanisms and energy budgets",
            Question_Category.TIMESCALE_CONSISTENCY: "Compare with characteristic timescales from stellar/galactic evolution theory",
            Question_Category.STATISTICAL_VALIDITY: "Perform proper error propagation and test for statistical significance",
            Question_Category.LITERATURE_CONTEXT: "Search astronomical databases and compare with known phenomena",
            Question_Category.ALTERNATIVE_EXPLANATIONS: "Test instrumental effects and systematic errors",
            Question_Category.OBSERVATIONAL_BIASES: "Analyze selection functions and completeness corrections"
        }

        return answers.get(category, "Perform appropriate astronomical analysis")

    def _identify_missing_context(self, claim: str, questions: List[Astronomical_Question]) -> List[str]:
        """Identify what context is missing to answer the questions"""
        missing = []

        # Check if questions reveal missing information
        question_lower = " ".join([q.question.lower() for q in questions])

        if not any(word in question_lower for word in ['telescope', 'instrument', 'wavelength']):
            missing.append("Observational capabilities and requirements")

        if not any(word in question_lower for word in ['energy', 'power', 'luminosity']):
            missing.append("Energy budget and power sources")

        if not any(word in question_lower for word in ['sample', 'statistical', 'significance']):
            missing.append("Statistical analysis and sample sizes")

        if not any(word in question_lower for word in ['literature', 'previous', 'known']):
            missing.append("Connection to existing astronomical research")

        return missing

    def _identify_validation_needs(self, claim: str, questions: List[Astronomical_Question]) -> List[str]:
        """Identify what validation is needed based on questions"""
        validations = []

        for question in questions:
            if question.priority == "critical":
                if question.category == Question_Category.PHYSICS_CONSISTENCY:
                    validations.append("Physical consistency validation against known laws")
                elif question.category == Question_Category.STATISTICAL_VALIDITY:
                    validations.append("Statistical validation with proper error analysis")
                elif question.category == Question_Category.OBSERVATIONAL_FEASIBILITY:
                    validations.append("Observational feasibility assessment")

        return validations

    def _calculate_scientific_rigor(self, claim: str, questions: List[Astronomical_Question],
                                   context: Dict[str, Any]) -> float:
        """Calculate how scientifically rigorous the questioning is"""
        if not questions:
            return 0.0

        # More questions = more rigorous
        question_count_score = min(1.0, len(questions) / 20.0)

        # Critical questions indicate higher rigor
        critical_count = sum(1 for q in questions if q.priority == "critical")
        critical_score = min(1.0, critical_count / 5.0)

        # Category diversity indicates comprehensive thinking
        categories_represented = len(set(q.category for q in questions))
        diversity_score = min(1.0, categories_represented / 8.0)

        # Calculate overall rigor
        rigor = (question_count_score * 0.3 + critical_score * 0.4 + diversity_score * 0.3)

        return rigor


class Astronomical_Question_Practice:
    """
    Practice system for developing astronomical questioning skills.

    This helps ASTRA practice formulating better scientific questions during
    idle moments, building the skill of scientific thinking.
    """

    def __init__(self):
        self.formulator = Astronomical_Question_Formulator()
        self.practice_claims = [
            "We discovered a new star formation threshold that operates at 100 K",
            "Our analysis achieved 10x speedup in causal discovery for astronomical time-series",
            "We found evidence for dark matter annihilation in dwarf galaxies",
            "The unified cache system provides 60-80% hit rates for all astronomical analyses",
            "Our method detects exoplanets with 99.9% accuracy using only photometric data"
        ]

    def practice_questioning(self) -> Dict[str, Any]:
        """Practice generating questions for sample astronomical claims"""
        practice_results = {}

        for claim in self.practice_claims:
            analysis = self.formulator.generate_questions(claim)
            practice_results[claim] = {
                'questions': [q.question for q in analysis.questions_generated],
                'critical_questions': [q.question for q in analysis.critical_questions],
                'missing_context': analysis.missing_context,
                'validation_needs': analysis.validation_needs
            }

        return practice_results


# Convenience function for quick questioning
def question_astronomical_claim(claim: str, context: Dict[str, Any] = None) -> Question_Analysis_Result:
    """Quick generation of scientific questions for an astronomical claim"""
    formulator = Astronomical_Question_Formulator()
    return formulator.generate_questions(claim, context)


if __name__ == "__main__":
    # Example usage - questioning a sample astronomical claim
    print("ASTRA Astronomical Question Formulator - Phase 1.2")
    print("=" * 60)

    # Sample astronomical claim to question
    sample_claim = "Our BIODISC optimizations achieve 3-10x speedup for astronomical discoveries"

    analysis = question_astronomical_claim(sample_claim)

    print(f"Claim: {analysis.claim}")
    print(f"\nGenerated {len(analysis.questions_generated)} questions")
    print(f"Scientific Rigor Score: {analysis.overall_scientific_rigor:.2f}")

    print("\nCritical Questions:")
    for q in analysis.critical_questions:
        print(f"  [{q.priority}] {q.question}")

    print("\nMissing Context:", analysis.missing_context)
    print("Validation Needs:", analysis.validation_needs)

    print("\n" + "=" * 60)
    print("Phase 1.2 complete: Astronomical questioning system operational")