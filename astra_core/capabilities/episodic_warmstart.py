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
Episodic Memory Warm-Start Module for STAN V39

Pre-populates episodic memory with canonical exemplars to solve cold-start
problem and provide reference patterns for case-based reasoning.

Core capabilities:
- Canonical problem exemplars for each domain
- Strategy patterns that generalize across problems
- Reference solutions for similarity matching
- Bootstrap memory for immediate reasoning capability

Date: 2025-12-11
Version: 39.1
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import hashlib


class ExemplarType(Enum):
    """Types of canonical exemplars"""
    PROBLEM_SOLUTION = "problem_solution"      # Question → Answer pair
    STRATEGY_PATTERN = "strategy_pattern"      # Reusable reasoning pattern
    COMMON_MISTAKE = "common_mistake"          # Pitfall to avoid
    DOMAIN_RULE = "domain_rule"               # Key domain principle
    CROSS_DOMAIN_ANALOGY = "cross_domain"     # Transfer learning example


@dataclass
class CanonicalExemplar:
    """A canonical problem exemplar for episodic memory"""
    exemplar_id: str
    domain: str
    category: str
    exemplar_type: ExemplarType
    description: str
    problem_pattern: str          # Abstract problem pattern
    solution_strategy: str        # How to solve
    key_insights: List[str]       # Important realizations
    common_mistakes: List[str]    # What to avoid
    related_concepts: List[str]   # Domain concepts involved
    difficulty: float = 0.5       # 0-1 scale
    retrieval_keywords: List[str] = field(default_factory=list)

    def to_episode_dict(self) -> Dict[str, Any]:
        """Convert to episodic memory format"""
        return {
            'id': self.exemplar_id,
            'type': 'canonical_exemplar',
            'domain': self.domain,
            'category': self.category,
            'context': {
                'problem_pattern': self.problem_pattern,
                'description': self.description,
            },
            'actions': [self.solution_strategy],
            'outcomes': {
                'strategy': 'success',
                'insights': self.key_insights,
            },
            'metadata': {
                'exemplar_type': self.exemplar_type.value,
                'difficulty': self.difficulty,
                'keywords': self.retrieval_keywords,
                'mistakes_to_avoid': self.common_mistakes,
                'related_concepts': self.related_concepts,
            }
        }


# =============================================================================
# MATHEMATICS EXEMPLARS
# =============================================================================

MATH_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="math_proof_induction",
        domain="Mathematics",
        category="Math",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Mathematical induction for proving statements about all natural numbers",
        problem_pattern="Prove P(n) for all n ≥ n₀",
        solution_strategy="1) Verify base case P(n₀). 2) Assume P(k) true (induction hypothesis). "
                         "3) Prove P(k+1) using P(k). 4) Conclude by induction principle.",
        key_insights=[
            "The induction step must use the hypothesis",
            "Strong induction assumes P(n₀)...P(k) to prove P(k+1)",
            "Base case must match the claim's starting point"
        ],
        common_mistakes=[
            "Forgetting to verify base case",
            "Not using induction hypothesis in step 3",
            "Circular reasoning in induction step"
        ],
        related_concepts=["well-ordering", "recursion", "strong induction"],
        difficulty=0.4,
        retrieval_keywords=["induction", "prove for all n", "base case", "induction hypothesis"]
    ),
    CanonicalExemplar(
        exemplar_id="math_proof_contradiction",
        domain="Mathematics",
        category="Math",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Proof by contradiction for impossibility statements",
        problem_pattern="Prove X is impossible / there is no Y such that...",
        solution_strategy="1) Assume the negation (X is possible / there exists Y). "
                         "2) Derive logical consequences. 3) Reach a contradiction with known facts. "
                         "4) Conclude original statement must be true.",
        key_insights=[
            "Works well for proving non-existence or irrationality",
            "The contradiction must be a genuine logical impossibility",
            "Classic example: √2 is irrational"
        ],
        common_mistakes=[
            "The 'contradiction' is merely surprising, not impossible",
            "Errors in the derivation invalidate the proof",
            "Assuming what you want to prove"
        ],
        related_concepts=["negation", "excluded middle", "reductio ad absurdum"],
        difficulty=0.5,
        retrieval_keywords=["contradiction", "impossible", "assume", "irrational", "no solution"]
    ),
    CanonicalExemplar(
        exemplar_id="math_counting_bijection",
        domain="Mathematics",
        category="Math",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Bijective proof for counting problems",
        problem_pattern="Prove |A| = |B| by constructing bijection",
        solution_strategy="1) Define explicit map f: A → B. 2) Prove f is injective (a≠a' ⟹ f(a)≠f(a')). "
                         "3) Prove f is surjective (every b has preimage). 4) Conclude |A| = |B|.",
        key_insights=[
            "Combinatorial identities often have bijective proofs",
            "Sometimes the inverse map is easier to describe",
            "Bijections preserve structure, enabling transfer of properties"
        ],
        common_mistakes=[
            "Map is not well-defined on all of A",
            "Forgetting to verify both injectivity and surjectivity",
            "The 'obvious' bijection isn't actually one-to-one"
        ],
        related_concepts=["cardinality", "counting", "one-to-one correspondence"],
        difficulty=0.5,
        retrieval_keywords=["bijection", "same size", "count", "correspondence", "combinatorics"]
    ),
    CanonicalExemplar(
        exemplar_id="math_calculus_substitution",
        domain="Mathematics",
        category="Math",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="U-substitution for integration",
        problem_pattern="∫f(g(x))·g'(x)dx",
        solution_strategy="1) Identify inner function u = g(x). 2) Compute du = g'(x)dx. "
                         "3) Rewrite integral in terms of u. 4) Integrate. 5) Substitute back x.",
        key_insights=[
            "Look for a function and its derivative appearing together",
            "u-sub is reverse chain rule",
            "May need to adjust constants (multiply/divide)"
        ],
        common_mistakes=[
            "Forgetting to substitute limits in definite integrals",
            "Not converting dx to du completely",
            "Forgetting to substitute back at the end"
        ],
        related_concepts=["chain rule", "antiderivative", "integration"],
        difficulty=0.3,
        retrieval_keywords=["integrate", "substitution", "u-sub", "change of variables"]
    ),
    CanonicalExemplar(
        exemplar_id="math_linear_algebra_rank",
        domain="Mathematics",
        category="Math",
        exemplar_type=ExemplarType.DOMAIN_RULE,
        description="Rank-nullity theorem for linear maps",
        problem_pattern="Given linear map T: V → W, find dimensions of kernel and image",
        solution_strategy="Apply rank-nullity: dim(V) = rank(T) + nullity(T). "
                         "Find rank by reducing matrix to REF and counting pivots. "
                         "Nullity = dim(V) - rank.",
        key_insights=[
            "Rank = number of leading 1s in row echelon form",
            "Rank = column rank = row rank",
            "Full rank means injective (if square, also bijective)"
        ],
        common_mistakes=[
            "Confusing rank with matrix dimensions",
            "Errors in row reduction",
            "Forgetting that rank ≤ min(m, n)"
        ],
        related_concepts=["kernel", "image", "linear independence", "dimension"],
        difficulty=0.4,
        retrieval_keywords=["rank", "nullity", "kernel", "linear map", "dimension"]
    ),
]

# =============================================================================
# PHYSICS EXEMPLARS
# =============================================================================

PHYSICS_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="physics_conservation_energy",
        domain="Physics",
        category="Physics",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Energy conservation for mechanical systems",
        problem_pattern="Find final velocity/height given initial conditions",
        solution_strategy="1) Identify system and check if non-conservative forces do work. "
                         "2) Write KE + PE at initial state. 3) Write KE + PE at final state. "
                         "4) If conservative: E_i = E_f. If not: E_i + W_nc = E_f. 5) Solve.",
        key_insights=[
            "Energy is scalar - no direction complications",
            "Choose reference point for PE = 0 wisely",
            "Friction dissipates energy as heat (W_nc < 0)"
        ],
        common_mistakes=[
            "Forgetting to include all forms of PE (gravity, spring)",
            "Sign errors in potential energy",
            "Using energy when momentum conservation is needed"
        ],
        related_concepts=["kinetic energy", "potential energy", "work", "conservative forces"],
        difficulty=0.3,
        retrieval_keywords=["energy", "conservation", "velocity", "height", "spring", "pendulum"]
    ),
    CanonicalExemplar(
        exemplar_id="physics_free_body_diagram",
        domain="Physics",
        category="Physics",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Free body diagram analysis for force problems",
        problem_pattern="Find acceleration or unknown force in mechanical system",
        solution_strategy="1) Isolate object of interest. 2) Draw ALL forces: gravity, normal, friction, "
                         "tension, applied. 3) Choose coordinates (often along acceleration direction). "
                         "4) Apply ΣF = ma in each direction. 5) Solve system of equations.",
        key_insights=[
            "Normal force ⊥ to surface, adjusts to prevent penetration",
            "Tension is same throughout massless rope",
            "Static friction ≤ μN, kinetic friction = μN"
        ],
        common_mistakes=[
            "Drawing forces that don't act ON the object",
            "Wrong direction for friction (opposes relative motion)",
            "Forgetting centripetal acceleration in circular motion"
        ],
        related_concepts=["Newton's laws", "normal force", "friction", "tension"],
        difficulty=0.3,
        retrieval_keywords=["force", "acceleration", "friction", "tension", "incline", "pulley"]
    ),
    CanonicalExemplar(
        exemplar_id="physics_gauss_law",
        domain="Physics",
        category="Physics",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Gauss's law for symmetric charge distributions",
        problem_pattern="Find electric field from symmetric charge distribution",
        solution_strategy="1) Identify symmetry (spherical, cylindrical, planar). "
                         "2) Choose Gaussian surface matching symmetry (E·dA constant or zero). "
                         "3) Calculate enclosed charge Q_enc. "
                         "4) Apply ∮E·dA = Q_enc/ε₀. 5) Solve for E.",
        key_insights=[
            "Symmetry allows pulling E outside the integral",
            "Works for any closed surface, but smart choice simplifies",
            "Field outside uniformly charged sphere = point charge"
        ],
        common_mistakes=[
            "Gaussian surface not matching symmetry",
            "Using total charge instead of enclosed charge",
            "Wrong area calculation"
        ],
        related_concepts=["electric field", "flux", "charge distribution", "symmetry"],
        difficulty=0.5,
        retrieval_keywords=["Gauss", "electric field", "charge", "sphere", "cylinder", "plane"]
    ),
    CanonicalExemplar(
        exemplar_id="physics_kinematics_projectile",
        domain="Physics",
        category="Physics",
        exemplar_type=ExemplarType.PROBLEM_SOLUTION,
        description="Projectile motion analysis",
        problem_pattern="Find range, max height, or time of flight for projectile",
        solution_strategy="1) Separate into x (constant v) and y (constant a = -g) motions. "
                         "2) x: x = v₀cos(θ)·t. y: y = v₀sin(θ)·t - ½gt². "
                         "3) Use constraints (y=0 for landing, v_y=0 for max height). 4) Solve.",
        key_insights=[
            "Horizontal and vertical motions are independent",
            "Time of flight from y equation, then plug into x",
            "Max range at 45° (in vacuum)"
        ],
        common_mistakes=[
            "Mixing up x and y components",
            "Forgetting factor of 2 in range formula",
            "Not accounting for launch height ≠ landing height"
        ],
        related_concepts=["kinematics", "vectors", "parabola", "free fall"],
        difficulty=0.3,
        retrieval_keywords=["projectile", "range", "trajectory", "launch angle", "parabola"]
    ),
    CanonicalExemplar(
        exemplar_id="physics_quantum_uncertainty",
        domain="Physics",
        category="Physics",
        exemplar_type=ExemplarType.DOMAIN_RULE,
        description="Heisenberg uncertainty principle applications",
        problem_pattern="Estimate minimum uncertainty in position/momentum",
        solution_strategy="Apply ΔxΔp ≥ ℏ/2. Given constraint on one, find minimum bound on other. "
                         "For energy-time: ΔEΔt ≥ ℏ/2 (e.g., lifetime vs linewidth).",
        key_insights=[
            "Fundamental limit, not measurement limitation",
            "Used to estimate ground state energies",
            "Explains why electrons don't fall into nucleus"
        ],
        common_mistakes=[
            "Confusing uncertainty with experimental error",
            "Wrong factor (ℏ vs h)",
            "Applying to unrelated quantities"
        ],
        related_concepts=["wavefunction", "measurement", "complementarity"],
        difficulty=0.5,
        retrieval_keywords=["uncertainty", "Heisenberg", "momentum", "position", "quantum"]
    ),
]

# =============================================================================
# BIOLOGY/MEDICINE EXEMPLARS
# =============================================================================

BIOLOGY_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="bio_central_dogma",
        domain="Biology",
        category="Biology/Medicine",
        exemplar_type=ExemplarType.DOMAIN_RULE,
        description="Central dogma of molecular biology",
        problem_pattern="Predict protein sequence from DNA or analyze genetic mutations",
        solution_strategy="1) Identify coding strand vs template strand. "
                         "2) Transcribe: template 3'→5' → mRNA 5'→3' (U replaces T). "
                         "3) Translate: read codons 5'→3', use codon table, stop at stop codon.",
        key_insights=[
            "mRNA is complementary to template, same as coding (except U)",
            "Reading frame is crucial - frameshift mutations change everything downstream",
            "Start codon (AUG) sets the reading frame"
        ],
        common_mistakes=[
            "Confusing template vs coding strand",
            "Reading in wrong direction (always 5'→3' for translation)",
            "Off-by-one errors in reading frame"
        ],
        related_concepts=["transcription", "translation", "codon", "mutation"],
        difficulty=0.4,
        retrieval_keywords=["DNA", "RNA", "protein", "codon", "transcription", "translation"]
    ),
    CanonicalExemplar(
        exemplar_id="bio_mendelian_genetics",
        domain="Biology",
        category="Biology/Medicine",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Mendelian inheritance patterns",
        problem_pattern="Predict phenotype ratios or genotypes from crosses",
        solution_strategy="1) Define alleles (dominant/recessive notation). "
                         "2) Determine parental genotypes from phenotypes/pedigree. "
                         "3) Set up Punnett square. 4) Calculate genotype/phenotype ratios. "
                         "5) For multiple genes: use product rule if independent.",
        key_insights=[
            "3:1 ratio = both parents heterozygous for one gene",
            "9:3:3:1 = dihybrid cross with independent assortment",
            "Deviations suggest linkage or epistasis"
        ],
        common_mistakes=[
            "Assuming all traits follow simple dominance",
            "Ignoring X-linkage possibilities",
            "Forgetting incomplete dominance or codominance"
        ],
        related_concepts=["allele", "genotype", "phenotype", "Punnett square"],
        difficulty=0.4,
        retrieval_keywords=["genetics", "inheritance", "allele", "dominant", "recessive", "cross"]
    ),
    CanonicalExemplar(
        exemplar_id="med_differential_diagnosis",
        domain="Medicine",
        category="Biology/Medicine",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Systematic differential diagnosis approach",
        problem_pattern="Given symptoms, determine most likely diagnosis",
        solution_strategy="1) List symptoms by system (HEENT, cardiac, respiratory, etc). "
                         "2) Identify unifying anatomical/physiological cause. "
                         "3) Generate DDx using 'worst first' and 'common things common'. "
                         "4) Use pathognomonic signs to narrow. 5) Apply Occam's razor.",
        key_insights=[
            "Pathognomonic = unique to one disease (rare but diagnostic)",
            "Red flags warrant urgent workup (chest pain + SOB, worst headache)",
            "Age, risk factors, prevalence modify pretest probability"
        ],
        common_mistakes=[
            "Anchoring on first diagnosis",
            "Ignoring contradictory findings",
            "Assuming multiple problems when one explains all"
        ],
        related_concepts=["pathophysiology", "symptoms", "signs", "diagnosis"],
        difficulty=0.6,
        retrieval_keywords=["diagnosis", "symptoms", "differential", "pathology", "disease"]
    ),
    CanonicalExemplar(
        exemplar_id="bio_evolution_selection",
        domain="Biology",
        category="Biology/Medicine",
        exemplar_type=ExemplarType.DOMAIN_RULE,
        description="Natural selection and evolutionary reasoning",
        problem_pattern="Explain adaptation or predict evolutionary outcome",
        solution_strategy="1) Identify the trait and its variation. "
                         "2) Determine selective pressure (predation, competition, mate choice). "
                         "3) Link trait to differential survival/reproduction. "
                         "4) Consider genetic basis and heritability. 5) Predict direction of change.",
        key_insights=[
            "Selection acts on phenotype, evolution on genotype",
            "Trade-offs constrain optimization (no free lunch)",
            "Neutral theory: many changes are not selected"
        ],
        common_mistakes=[
            "Teleological thinking ('evolved TO do X')",
            "Ignoring constraints and trade-offs",
            "Group selection fallacy"
        ],
        related_concepts=["fitness", "adaptation", "selection", "drift"],
        difficulty=0.4,
        retrieval_keywords=["evolution", "selection", "adaptation", "fitness", "trait"]
    ),
    CanonicalExemplar(
        exemplar_id="bio_enzyme_kinetics",
        domain="Biology",
        category="Biology/Medicine",
        exemplar_type=ExemplarType.PROBLEM_SOLUTION,
        description="Michaelis-Menten enzyme kinetics",
        problem_pattern="Analyze enzyme behavior, inhibition, or regulation",
        solution_strategy="1) Recall v = Vmax[S]/(Km + [S]). "
                         "2) Km = substrate concentration at half Vmax (affinity indicator). "
                         "3) For inhibition: competitive (↑ apparent Km), non-competitive (↓ Vmax). "
                         "4) Use Lineweaver-Burk for graphical analysis: 1/v vs 1/[S].",
        key_insights=[
            "Low Km = high affinity",
            "Competitive inhibitor competes for active site",
            "Allosteric regulation changes kinetic parameters"
        ],
        common_mistakes=[
            "Confusing Km and Kd",
            "Wrong interpretation of inhibitor effects",
            "Assuming all enzymes follow MM kinetics"
        ],
        related_concepts=["enzyme", "substrate", "inhibition", "catalysis"],
        difficulty=0.5,
        retrieval_keywords=["enzyme", "kinetics", "Michaelis", "Vmax", "Km", "inhibitor"]
    ),
]

# =============================================================================
# CHEMISTRY EXEMPLARS
# =============================================================================

CHEMISTRY_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="chem_reaction_mechanism",
        domain="Chemistry",
        category="Chemistry",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Organic reaction mechanism analysis",
        problem_pattern="Draw mechanism and predict products of organic reaction",
        solution_strategy="1) Identify nucleophile (electron-rich) and electrophile (electron-poor). "
                         "2) Draw curved arrows from electron source to destination. "
                         "3) Track formal charges at each step. "
                         "4) Consider regio/stereochemistry. 5) Verify atom and charge balance.",
        key_insights=[
            "Electrons flow from high to low density",
            "Good leaving groups are stable anions",
            "Markovnikov: H goes to C with more H's (for HX addition)"
        ],
        common_mistakes=[
            "Arrows pointing wrong direction",
            "Creating pentavalent carbon",
            "Ignoring stereochemistry"
        ],
        related_concepts=["nucleophile", "electrophile", "leaving group", "arrow pushing"],
        difficulty=0.5,
        retrieval_keywords=["mechanism", "arrow", "nucleophile", "electrophile", "organic"]
    ),
    CanonicalExemplar(
        exemplar_id="chem_stoichiometry",
        domain="Chemistry",
        category="Chemistry",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Stoichiometric calculations",
        problem_pattern="Calculate amounts of reactants or products",
        solution_strategy="1) Write balanced equation. 2) Convert given quantity to moles. "
                         "3) Use mole ratio from coefficients. 4) Convert to requested units. "
                         "5) If excess reagent problem, find limiting reagent first.",
        key_insights=[
            "Coefficients = mole ratios",
            "Limiting reagent determines actual yield",
            "Percent yield = (actual/theoretical) × 100"
        ],
        common_mistakes=[
            "Using mass ratios instead of mole ratios",
            "Forgetting to identify limiting reagent",
            "Unbalanced equation"
        ],
        related_concepts=["mole", "limiting reagent", "yield", "balanced equation"],
        difficulty=0.3,
        retrieval_keywords=["stoichiometry", "moles", "limiting", "yield", "balanced"]
    ),
    CanonicalExemplar(
        exemplar_id="chem_acid_base",
        domain="Chemistry",
        category="Chemistry",
        exemplar_type=ExemplarType.DOMAIN_RULE,
        description="Acid-base equilibrium analysis",
        problem_pattern="Calculate pH or determine acid/base strength",
        solution_strategy="1) Identify acid/base and write equilibrium. "
                         "2) Use Ka/Kb relationship: Ka × Kb = Kw = 10⁻¹⁴. "
                         "3) Set up ICE table if needed. "
                         "4) For buffers: Henderson-Hasselbalch pH = pKa + log([A⁻]/[HA]).",
        key_insights=[
            "Strong acids/bases dissociate completely",
            "pKa + pKb = 14 for conjugate pairs",
            "Buffer capacity highest when pH ≈ pKa"
        ],
        common_mistakes=[
            "Forgetting that strong acids don't need Ka",
            "Log vs ln confusion",
            "Ignoring activity coefficients at high concentration"
        ],
        related_concepts=["pH", "pKa", "buffer", "equilibrium"],
        difficulty=0.4,
        retrieval_keywords=["acid", "base", "pH", "buffer", "equilibrium", "pKa"]
    ),
    CanonicalExemplar(
        exemplar_id="chem_molecular_orbital",
        domain="Chemistry",
        category="Chemistry",
        exemplar_type=ExemplarType.PROBLEM_SOLUTION,
        description="Molecular orbital theory analysis",
        problem_pattern="Determine bond order, magnetism, or stability",
        solution_strategy="1) Count total valence electrons. "
                         "2) Fill MO diagram (for homonuclear diatomics, different order for O₂+). "
                         "3) Bond order = (bonding - antibonding)/2. "
                         "4) Unpaired electrons → paramagnetic; all paired → diamagnetic.",
        key_insights=[
            "Bond order 0 = no bond",
            "σ2p and π2p order switches at O₂",
            "Explains O₂ paramagnetism (valence bond cannot)"
        ],
        common_mistakes=[
            "Wrong filling order",
            "Forgetting antibonding electrons",
            "Miscounting electrons"
        ],
        related_concepts=["orbital", "bond order", "paramagnetism", "bonding"],
        difficulty=0.5,
        retrieval_keywords=["molecular orbital", "MO", "bond order", "paramagnetic", "diamagnetic"]
    ),
]

# =============================================================================
# COMPUTER SCIENCE EXEMPLARS
# =============================================================================

CS_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="cs_complexity_analysis",
        domain="Computer Science",
        category="Computer Science/AI",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Big-O complexity analysis",
        problem_pattern="Determine time/space complexity of algorithm",
        solution_strategy="1) Identify basic operations counted. "
                         "2) Express count as function of input size n. "
                         "3) Find dominant term as n → ∞. "
                         "4) Drop constants and lower-order terms. "
                         "5) Express in O(), Ω(), or Θ() notation.",
        key_insights=[
            "Nested loops often multiply: O(n) × O(n) = O(n²)",
            "Recursion: use recurrence relations (Master theorem)",
            "Amortized analysis for operations that are sometimes expensive"
        ],
        common_mistakes=[
            "Confusing worst/average/best case",
            "Forgetting hidden complexity (sort, hashmap resizing)",
            "Wrong recurrence for divide-and-conquer"
        ],
        related_concepts=["Big-O", "recurrence", "worst case", "amortized"],
        difficulty=0.4,
        retrieval_keywords=["complexity", "Big-O", "time", "space", "algorithm"]
    ),
    CanonicalExemplar(
        exemplar_id="cs_dynamic_programming",
        domain="Computer Science",
        category="Computer Science/AI",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Dynamic programming approach",
        problem_pattern="Optimization problem with overlapping subproblems",
        solution_strategy="1) Define subproblem and state variables. "
                         "2) Write recurrence relating subproblems. "
                         "3) Identify base cases. "
                         "4) Choose memoization (top-down) or tabulation (bottom-up). "
                         "5) Reconstruct solution if needed.",
        key_insights=[
            "DP = recursion + memoization",
            "Optimal substructure: optimal solution uses optimal subsolutions",
            "State space defines memory usage"
        ],
        common_mistakes=[
            "Wrong state definition",
            "Missing base cases",
            "Off-by-one in array indexing"
        ],
        related_concepts=["memoization", "recursion", "optimization", "subproblem"],
        difficulty=0.6,
        retrieval_keywords=["dynamic programming", "DP", "memoization", "recurrence", "optimal"]
    ),
    CanonicalExemplar(
        exemplar_id="cs_graph_traversal",
        domain="Computer Science",
        category="Computer Science/AI",
        exemplar_type=ExemplarType.PROBLEM_SOLUTION,
        description="Graph traversal (BFS/DFS)",
        problem_pattern="Search, shortest path, or connectivity problems",
        solution_strategy="BFS: Queue, explore level by level, shortest path in unweighted graph. "
                         "DFS: Stack/recursion, go deep first, detect cycles, topological sort. "
                         "Track visited to avoid infinite loops.",
        key_insights=[
            "BFS for shortest path (unweighted), level-order properties",
            "DFS for cycle detection, topological sort, connected components",
            "Time: O(V+E) for adjacency list"
        ],
        common_mistakes=[
            "Forgetting visited set → infinite loop",
            "BFS for weighted shortest path (use Dijkstra)",
            "Wrong termination condition"
        ],
        related_concepts=["graph", "BFS", "DFS", "shortest path", "tree"],
        difficulty=0.4,
        retrieval_keywords=["graph", "BFS", "DFS", "traversal", "shortest path", "search"]
    ),
    CanonicalExemplar(
        exemplar_id="cs_np_completeness",
        domain="Computer Science",
        category="Computer Science/AI",
        exemplar_type=ExemplarType.DOMAIN_RULE,
        description="NP-completeness and computational hardness",
        problem_pattern="Classify problem difficulty or prove hardness",
        solution_strategy="1) P: polynomial-time solvable. NP: polynomial-time verifiable. "
                         "2) NP-complete: in NP AND all NP problems reduce to it. "
                         "3) To prove NP-complete: (a) show in NP, (b) reduce known NP-C to it. "
                         "4) Common NP-C: SAT, 3-SAT, Clique, Vertex Cover, TSP.",
        key_insights=[
            "If any NP-complete has poly-time algorithm, then P=NP",
            "Reduction direction matters: known-hard → new problem",
            "NP-hard: at least as hard as NP-complete (maybe harder)"
        ],
        common_mistakes=[
            "Reducing in wrong direction",
            "Confusing NP-hard and NP-complete",
            "Assuming NP = exponential"
        ],
        related_concepts=["P", "NP", "reduction", "decidability"],
        difficulty=0.7,
        retrieval_keywords=["NP", "NP-complete", "reduction", "complexity", "P vs NP"]
    ),
    CanonicalExemplar(
        exemplar_id="cs_probability_ml",
        domain="Computer Science",
        category="Computer Science/AI",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Probabilistic reasoning in ML/AI",
        problem_pattern="Apply Bayes' theorem or probabilistic inference",
        solution_strategy="1) Define events and prior probabilities. "
                         "2) Identify likelihood P(evidence|hypothesis). "
                         "3) Apply Bayes: P(H|E) = P(E|H)P(H) / P(E). "
                         "4) P(E) = sum over all hypotheses: Σ P(E|Hᵢ)P(Hᵢ).",
        key_insights=[
            "Prior × Likelihood ∝ Posterior",
            "Base rate neglect is a common error",
            "Naive Bayes assumes feature independence"
        ],
        common_mistakes=[
            "Confusing P(A|B) with P(B|A)",
            "Forgetting to normalize",
            "Ignoring prior probabilities"
        ],
        related_concepts=["Bayes", "probability", "likelihood", "posterior", "inference"],
        difficulty=0.5,
        retrieval_keywords=["Bayes", "probability", "posterior", "prior", "likelihood", "ML"]
    ),
]

# =============================================================================
# HUMANITIES EXEMPLARS
# =============================================================================

HUMANITIES_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="hum_historical_causation",
        domain="History",
        category="Humanities/Social Science",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Analyzing historical causation",
        problem_pattern="Explain why event X happened or effects of Y",
        solution_strategy="1) Identify long-term (structural) and short-term (trigger) causes. "
                         "2) Distinguish necessary from sufficient conditions. "
                         "3) Consider counterfactuals: would outcome differ without this factor? "
                         "4) Use primary sources to support causal claims. "
                         "5) Acknowledge multiple causation and historiographical debate.",
        key_insights=[
            "Correlation is not causation in history too",
            "Agency vs structure: individuals vs systemic forces",
            "Hindsight bias: outcomes weren't inevitable"
        ],
        common_mistakes=[
            "Monocausal explanations",
            "Presentism (judging past by present standards)",
            "Post hoc ergo propter hoc"
        ],
        related_concepts=["causation", "contingency", "historiography", "primary sources"],
        difficulty=0.5,
        retrieval_keywords=["cause", "effect", "why", "historical", "led to"]
    ),
    CanonicalExemplar(
        exemplar_id="hum_argument_analysis",
        domain="Philosophy",
        category="Humanities/Social Science",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Analyzing philosophical arguments",
        problem_pattern="Evaluate argument validity and soundness",
        solution_strategy="1) Identify conclusion and premises. "
                         "2) Reconstruct argument in standard form (P1, P2... ∴ C). "
                         "3) Check validity: does conclusion follow from premises? "
                         "4) Check soundness: are premises actually true? "
                         "5) Consider objections and possible responses.",
        key_insights=[
            "Valid ≠ Sound: valid argument can have false premises",
            "Common forms: modus ponens, modus tollens, dilemma",
            "Common fallacies: affirming consequent, denying antecedent"
        ],
        common_mistakes=[
            "Attacking strawman instead of actual argument",
            "Conflating validity with truth",
            "Missing implicit premises"
        ],
        related_concepts=["logic", "validity", "soundness", "fallacy"],
        difficulty=0.5,
        retrieval_keywords=["argument", "premise", "conclusion", "valid", "sound", "fallacy"]
    ),
    CanonicalExemplar(
        exemplar_id="hum_literary_analysis",
        domain="Literature",
        category="Humanities/Social Science",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Literary analysis and interpretation",
        problem_pattern="Analyze meaning, themes, or techniques in text",
        solution_strategy="1) Close read: identify key passages, imagery, symbols. "
                         "2) Consider context: author biography, historical period, genre conventions. "
                         "3) Identify literary devices: metaphor, irony, narrative voice. "
                         "4) Develop thesis about meaning or function. "
                         "5) Support with textual evidence.",
        key_insights=[
            "Interpretation requires evidence from text",
            "Authorial intent ≠ only valid meaning",
            "Form and content are interconnected"
        ],
        common_mistakes=[
            "Plot summary instead of analysis",
            "Unsupported generalizations",
            "Ignoring form (only focusing on 'what' not 'how')"
        ],
        related_concepts=["close reading", "theme", "symbolism", "narrative"],
        difficulty=0.5,
        retrieval_keywords=["literary", "theme", "symbol", "meaning", "interpretation"]
    ),
    CanonicalExemplar(
        exemplar_id="hum_economic_analysis",
        domain="Economics",
        category="Humanities/Social Science",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Economic analysis and reasoning",
        problem_pattern="Analyze market, policy, or economic phenomenon",
        solution_strategy="1) Identify agents and their incentives. "
                         "2) Define equilibrium condition. "
                         "3) Analyze how change shifts supply/demand or behavior. "
                         "4) Consider unintended consequences and second-order effects. "
                         "5) Distinguish positive (what is) from normative (what should be).",
        key_insights=[
            "Incentives matter: people respond to costs and benefits",
            "No free lunch: everything has opportunity cost",
            "Markets can fail: externalities, public goods, info asymmetry"
        ],
        common_mistakes=[
            "Ignoring unintended consequences",
            "Ceteris paribus violations",
            "Confusing correlation with causation"
        ],
        related_concepts=["supply", "demand", "equilibrium", "incentive", "market failure"],
        difficulty=0.5,
        retrieval_keywords=["economic", "market", "supply", "demand", "policy", "incentive"]
    ),
]

# =============================================================================
# OTHER/TRIVIA EXEMPLARS
# =============================================================================

OTHER_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="trivia_elimination",
        domain="Trivia",
        category="Other",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Process of elimination for multiple choice",
        problem_pattern="Select answer from multiple choices",
        solution_strategy="1) Read all options before deciding. "
                         "2) Eliminate clearly wrong answers. "
                         "3) Look for absolute words (always, never) - often wrong. "
                         "4) Consider which answer the question writer intended. "
                         "5) When stuck, go with first instinct unless clear reason to change.",
        key_insights=[
            "Usually at least one option is obviously wrong",
            "Two similar answers: one is often correct",
            "Extreme options less likely to be correct"
        ],
        common_mistakes=[
            "Overthinking simple questions",
            "Changing answer without good reason",
            "Falling for distractor that's 'almost right'"
        ],
        related_concepts=["multiple choice", "test strategy", "elimination"],
        difficulty=0.2,
        retrieval_keywords=["multiple choice", "options", "eliminate", "select"]
    ),
    CanonicalExemplar(
        exemplar_id="trivia_cross_reference",
        domain="Trivia",
        category="Other",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Cross-referencing facts for obscure questions",
        problem_pattern="Answer question requiring specific factual knowledge",
        solution_strategy="1) Parse question for all clues (dates, names, places). "
                         "2) Cross-reference: what do I know about each element? "
                         "3) Use temporal/geographical constraints to narrow. "
                         "4) Consider what's 'notable' enough to be asked. "
                         "5) Make educated guess using most confident partial knowledge.",
        key_insights=[
            "Questions usually test notable facts",
            "Multiple clues in question can be combined",
            "Round numbers, famous dates are common answers"
        ],
        common_mistakes=[
            "Giving up when not immediately sure",
            "Not using all information in question",
            "Confusing similar facts"
        ],
        related_concepts=["trivia", "general knowledge", "deduction"],
        difficulty=0.3,
        retrieval_keywords=["trivia", "fact", "who", "what", "when", "where"]
    ),
    CanonicalExemplar(
        exemplar_id="games_backtracking",
        domain="Games",
        category="Other",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Backtracking for puzzle solving",
        problem_pattern="Solve constraint satisfaction puzzle (Sudoku, etc)",
        solution_strategy="1) Apply all forced moves (constraints with one option). "
                         "2) If stuck, pick cell/variable with fewest options. "
                         "3) Make tentative choice and propagate constraints. "
                         "4) If contradiction reached, backtrack to last choice. "
                         "5) Repeat until solved or all paths exhausted.",
        key_insights=[
            "Constraint propagation reduces search space",
            "Minimum remaining values heuristic helps",
            "Keep track of choices to enable backtracking"
        ],
        common_mistakes=[
            "Not doing forced moves first",
            "Guessing when logic suffices",
            "Losing track of what was assumed"
        ],
        related_concepts=["constraint satisfaction", "search", "puzzle"],
        difficulty=0.4,
        retrieval_keywords=["puzzle", "sudoku", "constraint", "backtrack", "logic"]
    ),
    CanonicalExemplar(
        exemplar_id="games_cipher",
        domain="Cryptography",
        category="Other",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Breaking simple substitution ciphers",
        problem_pattern="Decrypt message encoded with substitution cipher",
        solution_strategy="1) Count letter frequencies - E, T, A, O most common in English. "
                         "2) Identify common short words (THE, AND, OF, A). "
                         "3) Use patterns: double letters, apostrophes, word endings (-ING, -TION). "
                         "4) Make tentative substitutions and look for real words. "
                         "5) Iterate until message makes sense.",
        key_insights=[
            "English letter frequencies are well-known",
            "Patterns preserve: if XYX in cipher, same in plain",
            "Context helps - what topic might message be about?"
        ],
        common_mistakes=[
            "Ignoring word boundaries",
            "Not using frequency analysis",
            "Giving up too early"
        ],
        related_concepts=["cipher", "frequency analysis", "cryptography"],
        difficulty=0.4,
        retrieval_keywords=["cipher", "code", "decrypt", "substitution", "frequency"]
    ),
]

# =============================================================================
# ENGINEERING EXEMPLARS
# =============================================================================

ENGINEERING_EXEMPLARS = [
    CanonicalExemplar(
        exemplar_id="eng_system_decomposition",
        domain="Engineering",
        category="Engineering",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="System decomposition for complex problems",
        problem_pattern="Analyze or design complex engineering system",
        solution_strategy="1) Define system boundaries and interfaces. "
                         "2) Decompose into subsystems (functional decomposition). "
                         "3) Analyze each subsystem independently. "
                         "4) Identify interactions and integration points. "
                         "5) Verify system-level requirements are met.",
        key_insights=[
            "Divide and conquer reduces complexity",
            "Interfaces are where errors hide",
            "Document assumptions at each level"
        ],
        common_mistakes=[
            "Missing interface requirements",
            "Optimizing subsystem at expense of system",
            "Ignoring cross-cutting concerns"
        ],
        related_concepts=["system engineering", "decomposition", "integration"],
        difficulty=0.5,
        retrieval_keywords=["system", "design", "decomposition", "interface", "engineering"]
    ),
    CanonicalExemplar(
        exemplar_id="eng_dimensional_analysis",
        domain="Engineering",
        category="Engineering",
        exemplar_type=ExemplarType.STRATEGY_PATTERN,
        description="Dimensional analysis for physical problems",
        problem_pattern="Derive relationship or check equation validity",
        solution_strategy="1) List all relevant variables and their dimensions. "
                         "2) Find dimensionless groups (Buckingham Pi theorem). "
                         "3) Express answer in terms of dimensionless parameters. "
                         "4) Use known limiting cases to determine form of relationship. "
                         "5) Verify dimensions match on both sides of equation.",
        key_insights=[
            "Dimensions must balance in any valid equation",
            "Dimensionless numbers characterize regimes (Re, Ma, Fr)",
            "Useful for scaling and similarity analysis"
        ],
        common_mistakes=[
            "Mixing unit systems (SI vs imperial)",
            "Forgetting dimensional constants (g, c, h)",
            "Not identifying all relevant variables"
        ],
        related_concepts=["units", "scaling", "similarity", "dimensionless numbers"],
        difficulty=0.4,
        retrieval_keywords=["dimensional", "units", "scaling", "Reynolds", "analysis"]
    ),
]


# =============================================================================
# MEMORY WARM-START SYSTEM
# =============================================================================

ALL_EXEMPLARS: List[CanonicalExemplar] = (
    MATH_EXEMPLARS +
    PHYSICS_EXEMPLARS +
    BIOLOGY_EXEMPLARS +
    CHEMISTRY_EXEMPLARS +
    CS_EXEMPLARS +
    HUMANITIES_EXEMPLARS +
    OTHER_EXEMPLARS +
    ENGINEERING_EXEMPLARS
)


class EpisodicWarmStart:
    """
    Warm-start system for episodic memory.

    Pre-populates episodic memory with canonical exemplars to enable
    immediate case-based reasoning without cold-start problem.
    """

    def __init__(self):
        self.exemplars = ALL_EXEMPLARS
        self.by_category: Dict[str, List[CanonicalExemplar]] = {}
        self.by_domain: Dict[str, List[CanonicalExemplar]] = {}
        self._index_exemplars()

    def _index_exemplars(self):
        """Build indices for fast retrieval"""
        for ex in self.exemplars:
            # By category
            if ex.category not in self.by_category:
                self.by_category[ex.category] = []
            self.by_category[ex.category].append(ex)

            # By domain
            if ex.domain not in self.by_domain:
                self.by_domain[ex.domain] = []
            self.by_domain[ex.domain].append(ex)

    def get_exemplars_for_category(self, category: str) -> List[CanonicalExemplar]:
        """Get all exemplars for a category"""
        return self.by_category.get(category, [])

    def get_exemplars_for_domain(self, domain: str) -> List[CanonicalExemplar]:
        """Get all exemplars for a domain"""
        return self.by_domain.get(domain, [])

    def search_by_keywords(self, keywords: List[str],
                          top_k: int = 5) -> List[CanonicalExemplar]:
        """
        Search exemplars by keyword matching.

        Args:
            keywords: Search terms
            top_k: Maximum results to return

        Returns:
            Most relevant exemplars
        """
        scores = []
        keywords_lower = [k.lower() for k in keywords]

        for ex in self.exemplars:
            score = 0
            all_text = ' '.join([
                ex.description.lower(),
                ex.problem_pattern.lower(),
                ex.solution_strategy.lower(),
                ' '.join(ex.retrieval_keywords).lower()
            ])

            for kw in keywords_lower:
                if kw in all_text:
                    score += 1
                if kw in [rk.lower() for rk in ex.retrieval_keywords]:
                    score += 2  # Bonus for keyword match

            if score > 0:
                scores.append((score, ex))

        scores.sort(key=lambda x: -x[0])
        return [ex for _, ex in scores[:top_k]]

    def seed_episodic_memory(self, episodic_memory) -> int:
        """
        Seed an EpisodicMemory instance with canonical exemplars.

        Args:
            episodic_memory: EpisodicMemory instance to seed

        Returns:
            Number of episodes added
        """
        count = 0
        for ex in self.exemplars:
            episode_dict = ex.to_episode_dict()
            episodic_memory.store_episode(
                episode_type='canonical_exemplar',
                context=episode_dict['context'],
                actions=episode_dict['actions'],
                outcomes=episode_dict['outcomes'],
                metadata=episode_dict['metadata']
            )
            count += 1
        return count

    def get_strategy_for_problem(self, question: str,
                                 category: str = None,
                                 subject: str = None) -> Optional[str]:
        """
        Get relevant strategy pattern for a problem.

        Args:
            question: The problem to solve
            category: Problem category
            subject: Specific subject

        Returns:
            Solution strategy string or None
        """
        candidates = []

        # Get by domain/category
        if subject and subject in self.by_domain:
            candidates.extend(self.by_domain[subject])
        if category and category in self.by_category:
            candidates.extend(self.by_category[category])

        # Search by keywords from question
        words = question.lower().split()
        keyword_matches = self.search_by_keywords(words, top_k=3)
        candidates.extend(keyword_matches)

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for ex in candidates:
            if ex.exemplar_id not in seen:
                seen.add(ex.exemplar_id)
                unique.append(ex)

        if unique:
            # Return strategy from best match (first unique)
            return unique[0].solution_strategy

        return None

    def stats(self) -> Dict[str, Any]:
        """Get statistics about exemplar library"""
        return {
            'total_exemplars': len(self.exemplars),
            'by_category': {k: len(v) for k, v in self.by_category.items()},
            'by_domain': {k: len(v) for k, v in self.by_domain.items()},
            'types': {
                t.value: sum(1 for ex in self.exemplars if ex.exemplar_type == t)
                for t in ExemplarType
            }
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'EpisodicWarmStart',
    'CanonicalExemplar',
    'ExemplarType',
    'ALL_EXEMPLARS',
    'MATH_EXEMPLARS',
    'PHYSICS_EXEMPLARS',
    'BIOLOGY_EXEMPLARS',
    'CHEMISTRY_EXEMPLARS',
    'CS_EXEMPLARS',
    'HUMANITIES_EXEMPLARS',
    'OTHER_EXEMPLARS',
    'ENGINEERING_EXEMPLARS',
]



def metacognitive_monitor(task_state: Dict[str, Any],
                         confidence_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Monitor task progress and trigger strategy changes when needed.

    Implements metacognitive control: detect when current strategy
    is failing and switch approaches.

    Args:
        task_state: Current task state and progress
        confidence_threshold: Minimum confidence to continue current strategy

    Returns:
        Metacognitive recommendations
    """
    import numpy as np

    # Assess progress
    progress = task_state.get('progress', 0.0)
    confidence = task_state.get('confidence', 0.5)
    time_elapsed = task_state.get('time_elapsed', 0.0)
    time_budget = task_state.get('time_budget', 1.0)

    recommendations = {
        'continue_current': True,
        'strategy_change': None,
        'confidence_adjustment': 0.0
    }

    # Check if confidence is too low
    if confidence < confidence_threshold:
        recommendations['continue_current'] = False
        recommendations['strategy_change'] = 'increase_effort'

    # Check if time is running out with low progress
    time_fraction = time_elapsed / time_budget
    if time_fraction > 0.7 and progress < 0.3:
        recommendations['continue_current'] = False
        recommendations['strategy_change'] = 'switch_to_approximate'

    # Check for stagnation
    recent_progress = task_state.get('recent_progress', [])
    if len(recent_progress) > 3:
        if all(p < 0.01 for p in recent_progress[-3:]):
            recommendations['continue_current'] = False
            recommendations['strategy_change'] = 'try_alternative_approach'

    return recommendations


def update_confidence_based_on_feedback(current_confidence: float,
                                       feedback: float,
                                       learning_rate: float = 0.1) -> float:
    """
    Update confidence estimate based on outcome feedback.

    Implements Bayesian-inspired confidence updating.

    Args:
        current_confidence: Current confidence estimate
        feedback: Actual outcome (0-1, where 1 = success)
        learning_rate: How quickly to update

    Returns:
        Updated confidence
    """
    error = feedback - current_confidence
    new_confidence = current_confidence + learning_rate * error

    # Clip to valid range
    new_confidence = max(0.0, min(1.0, new_confidence))

    return new_confidence
                scores.append((var, 0))
                continue
