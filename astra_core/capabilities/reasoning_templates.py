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
Chain-of-Thought Reasoning Templates for STAN V39

Provides structured reasoning prompts for each domain to force
externalized step-by-step reasoning and catch errors early.

Core capabilities:
- Domain-specific reasoning scaffolds
- Multi-step problem decomposition
- Verification checkpoints
- Answer format standardization

Date: 2025-12-11
Version: 39.1
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import re


class ReasoningStyle(Enum):
    """Styles of reasoning for different problem types"""
    DEDUCTIVE = "deductive"           # Logic, proofs
    INDUCTIVE = "inductive"           # Pattern recognition
    ABDUCTIVE = "abductive"           # Best explanation
    ANALOGICAL = "analogical"         # Transfer from similar
    CAUSAL = "causal"                 # Cause-effect chains
    COMPUTATIONAL = "computational"   # Step-by-step calculation
    RETRIEVAL = "retrieval"           # Fact lookup
    ELIMINATIVE = "eliminative"       # Process of elimination


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain"""
    step_number: int
    instruction: str
    expected_output: str
    verification: str = ""
    fallback: str = ""


@dataclass
class ReasoningTemplate:
    """Complete reasoning template for a domain"""
    domain: str
    description: str
    primary_style: ReasoningStyle
    secondary_styles: List[ReasoningStyle]
    steps: List[ReasoningStep]
    verification_prompt: str
    answer_format: str
    common_pitfalls: List[str] = field(default_factory=list)

    def format_prompt(self, question: str,
                      include_verification: bool = True) -> str:
        """Format the complete reasoning prompt"""
        parts = [f"Problem: {question}\n"]

        for step in self.steps:
            parts.append(f"Step {step.step_number}: {step.instruction}")
            if step.verification:
                parts.append(f"   [Check: {step.verification}]")

        if include_verification:
            parts.append(f"\nVerification: {self.verification_prompt}")

        parts.append(f"\n{self.answer_format}")

        return "\n".join(parts)

    def get_step_prompts(self) -> List[str]:
        """Get individual step prompts for iterative reasoning"""
        return [f"Step {s.step_number}: {s.instruction}" for s in self.steps]


# =============================================================================
# MATHEMATICS TEMPLATES
# =============================================================================

MATH_ALGEBRA_TEMPLATE = ReasoningTemplate(
    domain="Math_Algebra",
    description="Algebraic manipulation and equation solving",
    primary_style=ReasoningStyle.COMPUTATIONAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE],
    steps=[
        ReasoningStep(1, "Identify the type of equation (linear, quadratic, polynomial, system)",
                     "Equation type classification"),
        ReasoningStep(2, "List all given information, variables, and constraints",
                     "Variable inventory"),
        ReasoningStep(3, "Choose appropriate solving technique (factoring, quadratic formula, substitution)",
                     "Method selection",
                     verification="Is this the most efficient method?"),
        ReasoningStep(4, "Execute algebraic manipulation step by step, showing each transformation",
                     "Solution steps"),
        ReasoningStep(5, "Substitute solution back into original equation to verify",
                     "Verification result",
                     verification="Does LHS = RHS?"),
    ],
    verification_prompt="Check: Does the answer satisfy all original constraints?",
    answer_format="Answer: [final value or expression]",
    common_pitfalls=["Sign errors", "Division by zero", "Extraneous solutions from squaring"]
)

MATH_CALCULUS_TEMPLATE = ReasoningTemplate(
    domain="Math_Calculus",
    description="Differentiation, integration, and analysis",
    primary_style=ReasoningStyle.COMPUTATIONAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE],
    steps=[
        ReasoningStep(1, "Identify the calculus operation needed (derivative, integral, limit, series)",
                     "Operation type"),
        ReasoningStep(2, "Recognize function type and applicable rules (chain, product, quotient, u-sub, parts)",
                     "Rule selection"),
        ReasoningStep(3, "Break complex expression into simpler components if needed",
                     "Decomposition"),
        ReasoningStep(4, "Apply rules systematically, one at a time",
                     "Step-by-step calculation"),
        ReasoningStep(5, "Simplify result and check dimensions/units if applicable",
                     "Simplified answer",
                     verification="Can this be simplified further?"),
    ],
    verification_prompt="Verify: For derivatives, does differentiating the integral give back the original? For integrals, does differentiating give the integrand?",
    answer_format="Answer: [expression with constant C for indefinite integrals]",
    common_pitfalls=["Forgetting chain rule", "Missing +C", "Wrong limits of integration"]
)

MATH_PROOF_TEMPLATE = ReasoningTemplate(
    domain="Math_Proof",
    description="Mathematical proofs and logical arguments",
    primary_style=ReasoningStyle.DEDUCTIVE,
    secondary_styles=[ReasoningStyle.ELIMINATIVE],
    steps=[
        ReasoningStep(1, "State what needs to be proven (conclusion) and given assumptions (premises)",
                     "Theorem statement"),
        ReasoningStep(2, "Choose proof strategy (direct, contradiction, contrapositive, induction, construction)",
                     "Strategy selection"),
        ReasoningStep(3, "For induction: verify base case. For contradiction: assume negation",
                     "Setup step"),
        ReasoningStep(4, "Build logical chain from premises to conclusion, citing each inference rule",
                     "Proof body"),
        ReasoningStep(5, "Ensure all cases are covered and no gaps exist in reasoning",
                     "Completeness check",
                     verification="Is every step justified?"),
    ],
    verification_prompt="Review: Does every step follow logically? Are there any hidden assumptions?",
    answer_format="QED / Therefore, [conclusion statement]",
    common_pitfalls=["Circular reasoning", "Missing cases", "Unjustified steps", "Assuming what needs to be proved"]
)

MATH_COMBINATORICS_TEMPLATE = ReasoningTemplate(
    domain="Math_Combinatorics",
    description="Counting, probability, and discrete structures",
    primary_style=ReasoningStyle.COMPUTATIONAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE, ReasoningStyle.ELIMINATIVE],
    steps=[
        ReasoningStep(1, "Identify: Is this permutation, combination, or more complex counting?",
                     "Problem type"),
        ReasoningStep(2, "Define the sample space and determine if order matters, if repetition allowed",
                     "Constraints identification"),
        ReasoningStep(3, "Break into cases if needed (inclusion-exclusion, conditioning)",
                     "Case decomposition"),
        ReasoningStep(4, "Apply counting principle: multiply for AND, add for OR",
                     "Calculation"),
        ReasoningStep(5, "Verify with small example or alternative counting method",
                     "Sanity check",
                     verification="Does the answer have the right order of magnitude?"),
    ],
    verification_prompt="Check: For small n, does manual enumeration match the formula?",
    answer_format="Answer: [numerical value or formula]",
    common_pitfalls=["Overcounting", "Undercounting", "Confusing permutation/combination"]
)


# =============================================================================
# PHYSICS TEMPLATES
# =============================================================================

PHYSICS_MECHANICS_TEMPLATE = ReasoningTemplate(
    domain="Physics_Mechanics",
    description="Classical mechanics, forces, and motion",
    primary_style=ReasoningStyle.CAUSAL,
    secondary_styles=[ReasoningStyle.COMPUTATIONAL],
    steps=[
        ReasoningStep(1, "Draw free body diagram identifying all forces and their directions",
                     "Force diagram"),
        ReasoningStep(2, "Choose coordinate system (usually: +x right, +y up, or along incline)",
                     "Coordinate system"),
        ReasoningStep(3, "Write Newton's laws: ΣF = ma for each direction, or energy conservation",
                     "Governing equations"),
        ReasoningStep(4, "Solve algebraically first, then substitute numerical values",
                     "Symbolic then numeric solution"),
        ReasoningStep(5, "Check units and verify answer is physically reasonable",
                     "Unit analysis",
                     verification="Are units consistent? Is magnitude plausible?"),
    ],
    verification_prompt="Sanity check: Is the answer in the right ballpark? Does the sign make sense?",
    answer_format="Answer: [value] [units]",
    common_pitfalls=["Missing forces", "Sign errors", "Wrong reference frame", "Forgetting friction"]
)

PHYSICS_EM_TEMPLATE = ReasoningTemplate(
    domain="Physics_Electromagnetism",
    description="Electric and magnetic fields, circuits",
    primary_style=ReasoningStyle.CAUSAL,
    secondary_styles=[ReasoningStyle.COMPUTATIONAL, ReasoningStyle.ANALOGICAL],
    steps=[
        ReasoningStep(1, "Identify charge distributions, currents, and field sources",
                     "Source identification"),
        ReasoningStep(2, "Choose appropriate law: Coulomb, Gauss, Ampere, Faraday, or Biot-Savart",
                     "Law selection"),
        ReasoningStep(3, "Exploit symmetry to simplify (spherical, cylindrical, planar)",
                     "Symmetry analysis"),
        ReasoningStep(4, "Set up and evaluate integrals or apply circuit laws (Kirchhoff)",
                     "Mathematical solution"),
        ReasoningStep(5, "Check limiting cases (r→0, r→∞, special geometries)",
                     "Limit verification",
                     verification="Does answer reduce to known result in special cases?"),
    ],
    verification_prompt="Verify: Do units work out? Does answer have correct symmetry?",
    answer_format="Answer: [expression or value] [units: V, A, T, N/C, etc.]",
    common_pitfalls=["Wrong sign convention", "Missing factor of 4π", "Confusing E and V"]
)

PHYSICS_QUANTUM_TEMPLATE = ReasoningTemplate(
    domain="Physics_Quantum",
    description="Quantum mechanics and atomic physics",
    primary_style=ReasoningStyle.COMPUTATIONAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE],
    steps=[
        ReasoningStep(1, "Identify the quantum system and relevant Hamiltonian",
                     "System identification"),
        ReasoningStep(2, "Determine what observable is being measured and its operator",
                     "Observable specification"),
        ReasoningStep(3, "Write the state in appropriate basis (position, momentum, energy)",
                     "State representation"),
        ReasoningStep(4, "Apply operators, calculate expectation values or probabilities",
                     "Quantum calculation"),
        ReasoningStep(5, "Interpret result physically and check normalization",
                     "Physical interpretation",
                     verification="Is probability ≤ 1? Is wavefunction normalized?"),
    ],
    verification_prompt="Check: Are probabilities non-negative and sum to 1?",
    answer_format="Answer: [value with appropriate quantum numbers or probability]",
    common_pitfalls=["Forgetting normalization", "Wrong commutation relations", "Measurement collapse"]
)


# =============================================================================
# BIOLOGY/MEDICINE TEMPLATES
# =============================================================================

BIOLOGY_MOLECULAR_TEMPLATE = ReasoningTemplate(
    domain="Biology_Molecular",
    description="Molecular biology, genetics, biochemistry",
    primary_style=ReasoningStyle.CAUSAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE],
    steps=[
        ReasoningStep(1, "Identify the biological level: molecular, cellular, or pathway",
                     "System level"),
        ReasoningStep(2, "Trace the information flow: DNA → RNA → Protein → Function",
                     "Central dogma mapping"),
        ReasoningStep(3, "Consider regulatory mechanisms: transcription factors, epigenetics, post-translational",
                     "Regulation analysis"),
        ReasoningStep(4, "Apply known biochemical rules: base pairing, codon table, enzyme kinetics",
                     "Mechanistic reasoning"),
        ReasoningStep(5, "Verify against known biological constraints (reading frame, start/stop codons)",
                     "Biological validation",
                     verification="Is this consistent with known biology?"),
    ],
    verification_prompt="Cross-check: Does this match known pathways/mechanisms?",
    answer_format="Answer: [biological entity, sequence, or mechanism]",
    common_pitfalls=["5'→3' vs 3'→5' confusion", "Template vs coding strand", "Intron/exon boundaries"]
)

MEDICINE_DIAGNOSIS_TEMPLATE = ReasoningTemplate(
    domain="Medicine_Diagnosis",
    description="Clinical reasoning and differential diagnosis",
    primary_style=ReasoningStyle.ABDUCTIVE,
    secondary_styles=[ReasoningStyle.ELIMINATIVE, ReasoningStyle.CAUSAL],
    steps=[
        ReasoningStep(1, "Gather key symptoms, signs, and patient history",
                     "Clinical presentation"),
        ReasoningStep(2, "Generate differential diagnosis list (broad to narrow)",
                     "DDx generation"),
        ReasoningStep(3, "Apply pathophysiological reasoning: how could this symptom pattern arise?",
                     "Mechanistic analysis"),
        ReasoningStep(4, "Use discriminating features to narrow differentials (red flags, specific findings)",
                     "DDx refinement"),
        ReasoningStep(5, "Select most likely diagnosis using Occam's razor and prevalence",
                     "Final diagnosis",
                     verification="Does this explain ALL the findings?"),
    ],
    verification_prompt="Verify: Can one diagnosis explain all symptoms? Are there contradictions?",
    answer_format="Answer: [diagnosis] with key supporting features",
    common_pitfalls=["Anchoring bias", "Ignoring contradictory evidence", "Forgetting common things are common"]
)

BIOLOGY_ECOLOGY_TEMPLATE = ReasoningTemplate(
    domain="Biology_Ecology",
    description="Ecology, evolution, and population biology",
    primary_style=ReasoningStyle.CAUSAL,
    secondary_styles=[ReasoningStyle.INDUCTIVE],
    steps=[
        ReasoningStep(1, "Identify the ecological level: population, community, or ecosystem",
                     "Scale identification"),
        ReasoningStep(2, "Map the interactions: predation, competition, mutualism, parasitism",
                     "Interaction network"),
        ReasoningStep(3, "Consider evolutionary pressures and fitness consequences",
                     "Evolutionary analysis"),
        ReasoningStep(4, "Apply ecological principles: energy flow, nutrient cycling, carrying capacity",
                     "Ecological reasoning"),
        ReasoningStep(5, "Predict outcomes using population dynamics or equilibrium analysis",
                     "Prediction",
                     verification="Is this evolutionarily stable?"),
    ],
    verification_prompt="Check: Does this make evolutionary sense? Is it ecologically feasible?",
    answer_format="Answer: [ecological outcome or mechanism]",
    common_pitfalls=["Ignoring time scales", "Confusing proximate/ultimate causation"]
)


# =============================================================================
# CHEMISTRY TEMPLATES
# =============================================================================

CHEMISTRY_REACTION_TEMPLATE = ReasoningTemplate(
    domain="Chemistry_Reaction",
    description="Chemical reactions and mechanisms",
    primary_style=ReasoningStyle.CAUSAL,
    secondary_styles=[ReasoningStyle.COMPUTATIONAL],
    steps=[
        ReasoningStep(1, "Identify reaction type: acid-base, redox, substitution, elimination, addition",
                     "Reaction classification"),
        ReasoningStep(2, "Identify nucleophile/electrophile or oxidizing/reducing agents",
                     "Reagent roles"),
        ReasoningStep(3, "Draw electron-pushing arrows showing bond breaking/forming",
                     "Mechanism drawing"),
        ReasoningStep(4, "Track stereochemistry and regiochemistry (Markovnikov, anti-addition)",
                     "Selectivity analysis"),
        ReasoningStep(5, "Balance equation and verify atom/charge conservation",
                     "Conservation check",
                     verification="Are atoms and charges balanced?"),
    ],
    verification_prompt="Verify: Is the mechanism concerted or stepwise? Are intermediates reasonable?",
    answer_format="Answer: [product structure or reaction outcome]",
    common_pitfalls=["Wrong arrow pushing", "Ignoring stereochemistry", "Unstable intermediates"]
)

CHEMISTRY_STRUCTURE_TEMPLATE = ReasoningTemplate(
    domain="Chemistry_Structure",
    description="Molecular structure, bonding, and properties",
    primary_style=ReasoningStyle.DEDUCTIVE,
    secondary_styles=[ReasoningStyle.ANALOGICAL],
    steps=[
        ReasoningStep(1, "Count valence electrons and determine Lewis structure",
                     "Electron counting"),
        ReasoningStep(2, "Apply VSEPR to determine molecular geometry",
                     "Geometry determination"),
        ReasoningStep(3, "Analyze hybridization and orbital overlap",
                     "Bonding analysis"),
        ReasoningStep(4, "Predict polarity from electronegativity differences and geometry",
                     "Polarity assessment"),
        ReasoningStep(5, "Relate structure to physical properties (bp, mp, solubility)",
                     "Property prediction",
                     verification="Does structure explain observed properties?"),
    ],
    verification_prompt="Check: Does electron count match? Is geometry consistent with hybridization?",
    answer_format="Answer: [structure, geometry, or property]",
    common_pitfalls=["Forgetting lone pairs", "Wrong formal charges", "Ignoring resonance"]
)


# =============================================================================
# COMPUTER SCIENCE TEMPLATES
# =============================================================================

CS_ALGORITHM_TEMPLATE = ReasoningTemplate(
    domain="CS_Algorithm",
    description="Algorithm design and analysis",
    primary_style=ReasoningStyle.COMPUTATIONAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE],
    steps=[
        ReasoningStep(1, "Understand input/output specification and constraints",
                     "Problem specification"),
        ReasoningStep(2, "Identify algorithm paradigm: divide-conquer, DP, greedy, search",
                     "Paradigm selection"),
        ReasoningStep(3, "Define subproblems and recurrence relation (if applicable)",
                     "Subproblem structure"),
        ReasoningStep(4, "Analyze time and space complexity using Big-O",
                     "Complexity analysis"),
        ReasoningStep(5, "Trace through small example to verify correctness",
                     "Correctness verification",
                     verification="Does it handle edge cases?"),
    ],
    verification_prompt="Test: Run mentally on input size 1, 2, and a typical case",
    answer_format="Answer: [algorithm description or complexity]",
    common_pitfalls=["Off-by-one errors", "Missing base cases", "Incorrect complexity analysis"]
)

CS_SYSTEMS_TEMPLATE = ReasoningTemplate(
    domain="CS_Systems",
    description="Computer systems, networks, and architecture",
    primary_style=ReasoningStyle.CAUSAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE],
    steps=[
        ReasoningStep(1, "Identify system components and their interfaces",
                     "Component mapping"),
        ReasoningStep(2, "Trace data/control flow through the system",
                     "Flow analysis"),
        ReasoningStep(3, "Identify bottlenecks, race conditions, or failure modes",
                     "Problem identification"),
        ReasoningStep(4, "Apply relevant principles: caching, pipelining, protocols",
                     "Principle application"),
        ReasoningStep(5, "Calculate performance metrics (latency, throughput, bandwidth)",
                     "Quantitative analysis",
                     verification="Are units consistent?"),
    ],
    verification_prompt="Check: Does answer account for all system constraints?",
    answer_format="Answer: [system behavior, metric, or design choice]",
    common_pitfalls=["Ignoring concurrency", "Wrong units (bits vs bytes)", "Forgetting overhead"]
)


# =============================================================================
# HUMANITIES TEMPLATES
# =============================================================================

HUMANITIES_HISTORY_TEMPLATE = ReasoningTemplate(
    domain="Humanities_History",
    description="Historical analysis and interpretation",
    primary_style=ReasoningStyle.CAUSAL,
    secondary_styles=[ReasoningStyle.ABDUCTIVE],
    steps=[
        ReasoningStep(1, "Establish temporal and geographical context",
                     "Contextualization"),
        ReasoningStep(2, "Identify key actors, events, and their motivations",
                     "Actor-event mapping"),
        ReasoningStep(3, "Trace causal chains: what led to what?",
                     "Causal analysis"),
        ReasoningStep(4, "Consider multiple perspectives and potential biases in sources",
                     "Source criticism"),
        ReasoningStep(5, "Synthesize into coherent narrative or argument",
                     "Synthesis",
                     verification="Is this consistent with primary sources?"),
    ],
    verification_prompt="Verify: Does this fit the broader historical context?",
    answer_format="Answer: [historical fact, interpretation, or analysis]",
    common_pitfalls=["Anachronism", "Presentism", "Oversimplification", "Ignoring context"]
)

HUMANITIES_PHILOSOPHY_TEMPLATE = ReasoningTemplate(
    domain="Humanities_Philosophy",
    description="Philosophical reasoning and argumentation",
    primary_style=ReasoningStyle.DEDUCTIVE,
    secondary_styles=[ReasoningStyle.ANALOGICAL],
    steps=[
        ReasoningStep(1, "Identify the philosophical question and relevant domain (ethics, epistemology, metaphysics)",
                     "Question classification"),
        ReasoningStep(2, "State relevant philosophical positions and their proponents",
                     "Position mapping"),
        ReasoningStep(3, "Reconstruct arguments in premise-conclusion form",
                     "Argument reconstruction"),
        ReasoningStep(4, "Evaluate validity and soundness of arguments",
                     "Critical analysis"),
        ReasoningStep(5, "Consider objections and responses",
                     "Dialectical engagement",
                     verification="Are there counterexamples?"),
    ],
    verification_prompt="Check: Is the argument valid? Are premises true?",
    answer_format="Answer: [philosophical position or analysis]",
    common_pitfalls=["Strawman arguments", "False dichotomies", "Equivocation"]
)

HUMANITIES_LAW_TEMPLATE = ReasoningTemplate(
    domain="Humanities_Law",
    description="Legal reasoning and analysis",
    primary_style=ReasoningStyle.DEDUCTIVE,
    secondary_styles=[ReasoningStyle.ANALOGICAL],
    steps=[
        ReasoningStep(1, "Identify the legal issue and relevant area of law",
                     "Issue spotting"),
        ReasoningStep(2, "State the applicable rule, statute, or precedent",
                     "Rule statement"),
        ReasoningStep(3, "Analyze how facts apply to the legal rule",
                     "Application"),
        ReasoningStep(4, "Consider counterarguments and exceptions",
                     "Counter-analysis"),
        ReasoningStep(5, "Reach conclusion on likely outcome",
                     "Conclusion",
                     verification="Is this consistent with precedent?"),
    ],
    verification_prompt="Verify: Does this follow IRAC structure? Are all elements addressed?",
    answer_format="Answer: [legal conclusion with reasoning]",
    common_pitfalls=["Missing elements", "Ignoring jurisdiction", "Overgeneralizing"]
)


# =============================================================================
# OTHER/TRIVIA TEMPLATES
# =============================================================================

TRIVIA_FACTUAL_TEMPLATE = ReasoningTemplate(
    domain="Trivia_Factual",
    description="Factual recall and general knowledge",
    primary_style=ReasoningStyle.RETRIEVAL,
    secondary_styles=[ReasoningStyle.ELIMINATIVE],
    steps=[
        ReasoningStep(1, "Identify the category of knowledge (geography, history, science, arts)",
                     "Category identification"),
        ReasoningStep(2, "Recall relevant facts and associations",
                     "Memory retrieval"),
        ReasoningStep(3, "Cross-reference with related knowledge for consistency",
                     "Consistency check"),
        ReasoningStep(4, "For multiple choice: eliminate clearly wrong answers",
                     "Elimination"),
        ReasoningStep(5, "Select most confident answer based on available evidence",
                     "Answer selection",
                     verification="Is there any contradicting information?"),
    ],
    verification_prompt="Double-check: Does this fact align with what I know about the topic?",
    answer_format="Answer: [specific factual answer]",
    common_pitfalls=["Confusing similar facts", "Outdated information", "False confidence"]
)

GAMES_STRATEGY_TEMPLATE = ReasoningTemplate(
    domain="Games_Strategy",
    description="Strategic games and puzzles",
    primary_style=ReasoningStyle.COMPUTATIONAL,
    secondary_styles=[ReasoningStyle.DEDUCTIVE],
    steps=[
        ReasoningStep(1, "Understand the game rules and objective",
                     "Rule comprehension"),
        ReasoningStep(2, "Analyze the current position/state",
                     "Position analysis"),
        ReasoningStep(3, "Enumerate possible moves/actions",
                     "Move generation"),
        ReasoningStep(4, "Evaluate each option considering opponent's responses",
                     "Minimax reasoning"),
        ReasoningStep(5, "Select move that maximizes expected outcome",
                     "Decision",
                     verification="Did I consider opponent's best response?"),
    ],
    verification_prompt="Check: Is there a forcing sequence I missed?",
    answer_format="Answer: [move or strategy]",
    common_pitfalls=["Tunnel vision", "Ignoring opponent", "Missing tactics"]
)


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

DOMAIN_TEMPLATES: Dict[str, ReasoningTemplate] = {
    # Math
    'Mathematics': MATH_PROOF_TEMPLATE,
    'Applied Mathematics': MATH_CALCULUS_TEMPLATE,
    'Math': MATH_ALGEBRA_TEMPLATE,

    # Physics
    'Physics': PHYSICS_MECHANICS_TEMPLATE,

    # Biology/Medicine
    'Biology': BIOLOGY_MOLECULAR_TEMPLATE,
    'Medicine': MEDICINE_DIAGNOSIS_TEMPLATE,
    'Genetics': BIOLOGY_MOLECULAR_TEMPLATE,
    'Neuroscience': BIOLOGY_MOLECULAR_TEMPLATE,
    'Ecology': BIOLOGY_ECOLOGY_TEMPLATE,
    'Biochemistry': CHEMISTRY_STRUCTURE_TEMPLATE,

    # Chemistry
    'Chemistry': CHEMISTRY_REACTION_TEMPLATE,

    # Computer Science
    'Computer Science': CS_ALGORITHM_TEMPLATE,
    'Artificial Intelligence': CS_ALGORITHM_TEMPLATE,
    'Cybersecurity': CS_SYSTEMS_TEMPLATE,
    'Electrical Engineering': CS_SYSTEMS_TEMPLATE,

    # Humanities
    'History': HUMANITIES_HISTORY_TEMPLATE,
    'Philosophy': HUMANITIES_PHILOSOPHY_TEMPLATE,
    'Law': HUMANITIES_LAW_TEMPLATE,
    'Economics': HUMANITIES_PHILOSOPHY_TEMPLATE,
    'Linguistics': HUMANITIES_PHILOSOPHY_TEMPLATE,
    'Art History': HUMANITIES_HISTORY_TEMPLATE,
    'Musicology': HUMANITIES_HISTORY_TEMPLATE,

    # Other
    'Trivia': TRIVIA_FACTUAL_TEMPLATE,
    'Chess': GAMES_STRATEGY_TEMPLATE,
    'Game Design': GAMES_STRATEGY_TEMPLATE,
}

CATEGORY_TEMPLATES: Dict[str, ReasoningTemplate] = {
    'Math': MATH_ALGEBRA_TEMPLATE,
    'Physics': PHYSICS_MECHANICS_TEMPLATE,
    'Biology/Medicine': MEDICINE_DIAGNOSIS_TEMPLATE,
    'Chemistry': CHEMISTRY_REACTION_TEMPLATE,
    'Computer Science/AI': CS_ALGORITHM_TEMPLATE,
    'Humanities/Social Science': HUMANITIES_HISTORY_TEMPLATE,
    'Engineering': CS_SYSTEMS_TEMPLATE,
    'Other': TRIVIA_FACTUAL_TEMPLATE,
}


class ReasoningTemplateEngine:
    """
    Engine for selecting and applying reasoning templates.
    """

    def __init__(self):
        self.domain_templates = DOMAIN_TEMPLATES
        self.category_templates = CATEGORY_TEMPLATES
        self.usage_stats: Dict[str, int] = {}

    def get_template(self, subject: str = None,
                     category: str = None) -> ReasoningTemplate:
        """
        Get appropriate reasoning template.

        Args:
            subject: Specific subject (e.g., 'Physics', 'Chemistry')
            category: Broad category (e.g., 'Math', 'Biology/Medicine')

        Returns:
            Most appropriate ReasoningTemplate
        """
        # Try subject-specific first
        if subject and subject in self.domain_templates:
            template = self.domain_templates[subject]
            self.usage_stats[subject] = self.usage_stats.get(subject, 0) + 1
            return template

        # Fall back to category
        if category and category in self.category_templates:
            template = self.category_templates[category]
            self.usage_stats[category] = self.usage_stats.get(category, 0) + 1
            return template

        # Default to general retrieval
        return TRIVIA_FACTUAL_TEMPLATE

    def generate_cot_prompt(self, question: str,
                           subject: str = None,
                           category: str = None,
                           include_verification: bool = True) -> str:
        """
        Generate complete chain-of-thought prompt.

        Args:
            question: The question to answer
            subject: Subject area
            category: Category
            include_verification: Include verification step

        Returns:
            Formatted CoT prompt
        """
        template = self.get_template(subject, category)
        return template.format_prompt(question, include_verification)

    def get_reasoning_style(self, subject: str = None,
                           category: str = None) -> ReasoningStyle:
        """Get primary reasoning style for a domain"""
        template = self.get_template(subject, category)
        return template.primary_style

    def get_common_pitfalls(self, subject: str = None,
                           category: str = None) -> List[str]:
        """Get common pitfalls to avoid for a domain"""
        template = self.get_template(subject, category)
        return template.common_pitfalls

    def stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'n_templates': len(self.domain_templates),
            'n_categories': len(self.category_templates),
            'usage': self.usage_stats
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ReasoningTemplateEngine',
    'ReasoningTemplate',
    'ReasoningStep',
    'ReasoningStyle',
    'DOMAIN_TEMPLATES',
    'CATEGORY_TEMPLATES',
]


