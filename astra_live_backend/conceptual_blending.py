"""
ASTRA Live — Conceptual Blending Engine
Enables deep cross-domain analogy and conceptual innovation.

Based on:
- Conceptual spaces theory (Gärdenfors)
- Structure-mapping theory (Gentner)
- Conceptual blending (Fauconnier & Turner)
- Analogical reasoning in science (Nersessian, Holyoak)
"""
import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from enum import Enum
import json


class ConceptualDimension(Enum):
    """Fundamental dimensions of conceptual spaces."""
    SPATIAL = "spatial"          # geometry, topology, dimensionality
    TEMPORAL = "temporal"          # time, causality, evolution
    MATERIAL = "material"          # substance, fields, matter
    DYNAMIC = "dynamic"            # forces, interactions, dynamics
    INFORMATION = "information"    # entropy, information, complexity
    STRUCTURAL = "structural"      # organization, hierarchy, networks
    QUALITATIVE = "qualitative"    # properties, qualities, attributes


@dataclass
class Concept:
    """A scientific concept with dimensional structure."""
    name: str
    domain: str
    dimensional_signature: Dict[ConceptualDimension, float]
    relations: List[str]  # Relations to other concepts
    instances: List[str]  # Examples
    theoretical_role: str  # How used in theory


@dataclass
class ConceptualSpace:
    """A domain represented as a multi-dimensional conceptual space."""
    domain_name: str
    concepts: Dict[str, Concept]
    dimensional_structure: Dict[ConceptualDimension, Tuple[float, float]]
    # For each dimension: (min, max) range of values in this domain


@dataclass
class ConceptualBlend:
    """A novel concept created by blending from multiple domains."""
    name: str
    source_concepts: List[Concept]
    blended_dimensions: Dict[ConceptualDimension, float]
    novel_aspects: List[str]
    theoretical_implications: List[str]
    testable_predictions: List[str]
    blend_strength: float  # How coherent is the blend?


class ConceptualBlender:
    """
    Creates novel theoretical concepts through deep cross-domain analogy.

    Key insight: Scientific innovation often comes from blending
    conceptual structures from apparently unrelated domains.

    Examples from history:
    - Rutherford atom → Solar system (planetary model)
    - De Broglie → Light as wave + particle → Matter waves
    - Gell-Mann → "Eightfold Way" → Quarks (from Buddhist philosophy)
    - 't Hooft → Duality → Gauge theories + string theory
    """

    def __init__(self):
        # Define conceptual spaces for major scientific domains
        self.conceptual_spaces = self._initialize_conceptual_spaces()
        self.blend_history = []

    def _initialize_conceptual_spaces(self) -> Dict[str, ConceptualSpace]:
        """Initialize conceptual spaces for key domains."""
        spaces = {}

        # GRAVITY / GENERAL RELATIVITY
        spaces["gravity"] = ConceptualSpace(
            domain_name="gravity",
            concepts={
                "metric": Concept("metric", "gravity",
                    {ConceptualDimension.SPATIAL: 0.9, ConceptualDimension.STRUCTURAL: 0.7},
                    ["curvature", "geometry", "distance"], ["g_μν", "line element"], "Describes geometry"),
                "curvature": Concept("curvature", "gravity",
                    {ConceptualDimension.SPATIAL: 0.8, ConceptualDimension.DYNAMIC: 0.6},
                    ["tidal forces", "geodesic deviation"], ["R_μν", "Gaussian curvature"], "Spacetime curvature"),
                "geodesic": Concept("geodesic", "gravity",
                    {ConceptualDimension.SPATIAL: 0.9, ConceptualDimension.DYNAMIC: 0.5},
                    ["free fall", "shortest path"], ["orbital path", "light ray"], "Paths in curved spacetime"),
                "event_horizon": Concept("event_horizon", "gravity",
                    {ConceptualDimension.SPATIAL: 0.7, ConceptualDimension.INFORMATION: 0.8},
                    ["no escape", "causality boundary"], ["black hole surface"], "Information boundary"),
                "gravitational_waves": Concept("gravitational_waves", "gravity",
                    {ConceptualDimension.SPATIAL: 0.6, ConceptualDimension.DYNAMIC: 0.9,
                     ConceptualDimension.INFORMATION: 0.5},
                    ["ripples in spacetime", "propagating curvature"], ["GW150914"], "Carry energy & information")
            },
            dimensional_structure={
                ConceptualDimension.SPATIAL: (0.0, 1.0),  # Geometry is central
                ConceptualDimension.TEMPORAL: (0.2, 0.8),  # Time is geometric
                ConceptualDimension.MATERIAL: (0.0, 0.3),  # Matter curves geometry
                ConceptualDimension.DYNAMIC: (0.3, 0.9),  # Dynamics through geometry
                ConceptualDimension.INFORMATION: (0.0, 0.8),  # Event horizons, holography
                ConceptualDimension.STRUCTURAL: (0.3, 0.8),  # Manifold structure
                ConceptualDimension.QUALITATIVE: (0.1, 0.6)  # Qualitative features
            }
        )

        # QUANTUM MECHANICS
        spaces["quantum"] = ConceptualSpace(
            domain_name="quantum",
            concepts={
                "wavefunction": Concept("wavefunction", "quantum",
                    {ConceptualDimension.INFORMATION: 0.9, ConceptualDimension.STRUCTURAL: 0.6},
                    ["probability_amplitude", "superposition"], ["ψ", "state vector"], "Complete state description"),
                "superposition": Concept("superposition", "quantum",
                    {ConceptualDimension.STRUCTURAL: 0.8, ConceptualDimension.INFORMATION: 0.7},
                    ["multiple states", "coherence"], ["Schrödinger cat", "qubit"], "Quantum parallelism"),
                "entanglement": Concept("entanglement", "quantum",
                    {ConceptualDimension.INFORMATION: 1.0, ConceptualDimension.STRUCTURAL: 0.7},
                    ["nonlocal correlation", "EPR paradox"], ["Bell pairs", "GHZ state"], "Nonlocal information structure"),
                "uncertainty": Concept("uncertainty", "quantum",
                    {ConceptualDimension.INFORMATION: 0.8, ConceptualDimension.STRUCTURAL: 0.5},
                    ["complementary observables", "measurement disturbance"], ["Heisenberg"], "Fundamental limit to knowledge"),
                "quantum_field": Concept("quantum_field", "quantum",
                    {ConceptualDimension.MATERIAL: 0.7, ConceptualDimension.DYNAMIC: 0.8,
                     ConceptualDimension.INFORMATION: 0.6},
                    ["particles as excitations", "field quantization"], ["photons", "electrons"], "Matter as fields")
            },
            dimensional_structure={
                ConceptualDimension.SPATIAL: (0.1, 0.5),  # Position is an observable
                ConceptualDimension.TEMPORAL: (0.2, 0.6),  # Time evolution (unitary)
                ConceptualDimension.MATERIAL: (0.3, 0.8),  # Particles, fields
                ConceptualDimension.DYNAMIC: (0.5, 0.9),  # Time evolution, measurement
                ConceptualDimension.INFORMATION: (0.8, 1.0),  # Central: quantum information
                ConceptualDimension.STRUCTURAL: (0.5, 0.9),  # Hilbert space structure
                ConceptualDimension.QUALITATIVE: (0.4, 0.8)  # Qualitative quantum features
            }
        )

        # THERMODYNAMICS / STATISTICAL MECHANICS
        spaces["thermodynamics"] = ConceptualSpace(
            domain_name="thermodynamics",
            concepts={
                "entropy": Concept("entropy", "thermodynamics",
                    {ConceptualDimension.INFORMATION: 0.9, ConceptualDimension.STRUCTURAL: 0.6},
                    ["disorder", "missing_information", "arrow_of_time"], ["S", "Boltzmann entropy"], "Information content"),
                "temperature": Concept("temperature", "thermodynamics",
                    {ConceptualDimension.DYNAMIC: 0.7, ConceptualDimension.STRUCTURAL: 0.5},
                    ["thermal_equilibrium", "energy_distribution"], ["T", "beta"], "Equilibrium parameter"),
                "heat": Concept("heat", "thermodynamics",
                    {ConceptualDimension.DYNAMIC: 0.8, ConceptualDimension.MATERIAL: 0.6},
                    ["energy_transfer", "random_motion"], ["Q", "thermal_energy"], "Energy in transit"),
                "phase_transition": Concept("phase_transition", "thermodynamics",
                    {ConceptualDimension.STRUCTURAL: 0.9, ConceptualDimension.QUALITATIVE: 0.7},
                    ["critical_point", "order_parameter"], ["boiling", "ferromagnetism"], "Abrupt structural change"),
                "equilibrium": Concept("equilibrium", "thermodynamics",
                    {ConceptualDimension.STRUCTURAL: 0.6, ConceptualDimension.TEMPORAL: 0.7},
                    ["maximum_entropy", "no_net_flow"], ["thermal_equilibrium"], "Stationary state")
            },
            dimensional_structure={
                ConceptualDimension.SPATIAL: (0.1, 0.4),
                ConceptualDimension.TEMPORAL: (0.3, 0.7),  # Time's arrow
                ConceptualDimension.MATERIAL: (0.4, 0.8),
                ConceptualDimension.DYNAMIC: (0.5, 0.9),
                ConceptualDimension.INFORMATION: (0.6, 1.0),  # Entropy is central
                ConceptualDimension.STRUCTURAL: (0.4, 0.8),  # Phases, structures
                ConceptualDimension.QUALITATIVE: (0.5, 0.8)
            }
        )

        # INFORMATION THEORY
        spaces["information"] = ConceptualSpace(
            domain_name="information",
            concepts={
                "information": Concept("information", "information",
                    {ConceptualDimension.INFORMATION: 1.0},
                    ["reduction_of_uncertainty", "data", "meaning"], ["bits", "Shannon entropy"], "Fundamental quantity"),
                "channel": Concept("channel", "information",
                    {ConceptualDimension.STRUCTURAL: 0.7, ConceptualDimension.INFORMATION: 0.8},
                    ["communication_medium", "noise", "capacity"], ["classical_channel", "quantum_channel"], "Information transmission"),
                "code": Concept("code", "information",
                    {ConceptualDimension.STRUCTURAL: 0.8, ConceptualDimension.INFORMATION: 0.7},
                    ["encoding", "compression", "error_correction"], ["Huffman", "Turbo code"], "Information representation"),
                "mutual_information": Concept("mutual_information", "information",
                    {ConceptualDimension.INFORMATION: 0.9, ConceptualDimension.STRUCTURAL: 0.6},
                    ["shared_information", "correlation"], ["I(X;Y)"], "Information shared between systems"),
                "complexity": Concept("complexity", "information",
                    {ConceptualDimension.STRUCTURAL: 0.8, ConceptualDimension.INFORMATION: 0.7},
                    ["Kolmogorov_complexity", "computational_cost"], ["algorithmic_complexity"], "Description length")
            },
            dimensional_structure={
                ConceptualDimension.SPATIAL: (0.0, 0.2),
                ConceptualDimension.TEMPORAL: (0.2, 0.5),
                ConceptualDimension.MATERIAL: (0.0, 0.3),
                ConceptualDimension.DYNAMIC: (0.3, 0.6),
                ConceptualDimension.INFORMATION: (0.9, 1.0),  # Primary dimension
                ConceptualDimension.STRUCTURAL: (0.5, 0.9),
                ConceptualDimension.QUALITATIVE: (0.4, 0.7)
            }
        )

        # BIOLOGY / EVOLUTION
        spaces["biology"] = ConceptualSpace(
            domain_name="biology",
            concepts={
                "evolution": Concept("evolution", "biology",
                    {ConceptualDimension.TEMPORAL: 0.9, ConceptualDimension.STRUCTURAL: 0.7},
                    ["natural_selection", "adaptation", "common_descent"], ["Darwinian_evolution"], "Optimization over time"),
                "organism": Concept("organism", "biology",
                    {ConceptualDimension.STRUCTURAL: 0.8, ConceptualDimension.MATERIAL: 0.9},
                    ["living_system", "metabolism"], ["bacteria", "animals"], "Structured matter"),
                "ecosystem": Concept("ecosystem", "biology",
                    {ConceptualDimension.STRUCTURAL: 0.9, ConceptualDimension.DYNAMIC: 0.8},
                    ["interdependence", "food_web", "niche"], ["forest", "reef"], "Complex adaptive system"),
                "gene": Concept("gene", "biology",
                    {ConceptualDimension.INFORMATION: 0.8, ConceptualDimension.STRUCTURAL: 0.6},
                    ["heredity", "information_carrier"], ["DNA", "RNA"], "Informational molecule"),
                "fitness": Concept("fitness", "biology",
                    {ConceptualDimension.DYNAMIC: 0.7, ConceptualDimension.STRUCTURAL: 0.5},
                    ["reproductive_success", "optimization_target"], ["adaptation"], "Optimization criterion")
            },
            dimensional_structure={
                ConceptualDimension.SPATIAL: (0.3, 0.7),
                ConceptualDimension.TEMPORAL: (0.5, 1.0),  # Evolution is temporal
                ConceptualDimension.MATERIAL: (0.6, 0.9),
                ConceptualDimension.DYNAMIC: (0.6, 0.9),
                ConceptualDimension.INFORMATION: (0.5, 0.8),  # Genetic information
                ConceptualDimension.STRUCTURAL: (0.6, 0.9),
                ConceptualDimension.QUALITATIVE: (0.6, 0.9)
            }
        )

        return spaces

    def find_conceptual_analogy(self, domain1: str, domain2: str,
                                min_similarity: float = 0.5) -> List[Tuple[Concept, Concept, float]]:
        """
        Find analogical relationships between concepts in different domains.

        Uses dimensional similarity to identify candidate analogies.
        """
        space1 = self.conceptual_spaces.get(domain1)
        space2 = self.conceptual_spaces.get(domain2)

        if not space1 or not space2:
            return []

        analogies = []

        for name1, concept1 in space1.concepts.items():
            for name2, concept2 in space2.concepts.items():
                # Calculate dimensional similarity
                similarity = self._conceptual_similarity(concept1, concept2)

                if similarity >= min_similarity:
                    analogies.append((concept1, concept2, similarity))

        # Sort by similarity
        analogies.sort(key=lambda x: x[2], reverse=True)

        return analogies

    def _conceptual_similarity(self, concept1: Concept, concept2: Concept) -> float:
        """Calculate similarity between two concepts based on dimensional signatures."""
        sig1 = concept1.dimensional_signature
        sig2 = concept2.dimensional_signature

        # Cosine similarity
        dot_product = sum(sig1.get(dim, 0) * sig2.get(dim, 0)
                          for dim in ConceptualDimension)

        norm1 = np.sqrt(sum(v**2 for v in sig1.values()))
        norm2 = np.sqrt(sum(v**2 for v in sig2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def create_conceptual_blend(self, concept1: Concept, concept2: Concept,
                               blend_name: str = None) -> ConceptualBlend:
        """
        Create a novel concept by blending two concepts from different domains.

        This is how theoretical innovation happens:
        - De Broglie: Matter (from mechanics) + Wave (from optics) → Matter waves
        - Shannon: Thermodynamics (entropy) + Information → Information theory
        - 't Hooft: Gauge theory + String theory → Gauge/gravity duality
        """
        if blend_name is None:
            blend_name = f"{concept1.name}_{concept2.name}_blend"

        # Blend dimensional signatures (weighted average)
        blended_signature = {}
        for dim in ConceptualDimension:
            v1 = concept1.dimensional_signature.get(dim, 0)
            v2 = concept2.dimensional_signature.get(dim, 0)
            # Blend emphasizes dimensions where both are strong
            blended_signature[dim] = np.sqrt(v1 * v2)  # Geometric mean

        # Generate novel aspects
        novel_aspects = self._generate_novel_aspects(concept1, concept2)

        # Generate theoretical implications
        implications = self._generate_theoretical_implications(concept1, concept2)

        # Generate testable predictions
        predictions = self._generate_testable_predictions(concept1, concept2, blended_signature)

        # Calculate blend strength (coherence)
        blend_strength = self._calculate_blend_strength(concept1, concept2, blended_signature)

        blend = ConceptualBlend(
            name=blend_name,
            source_concepts=[concept1, concept2],
            blended_dimensions=blended_signature,
            novel_aspects=novel_aspects,
            theoretical_implications=implications,
            testable_predictions=predictions,
            blend_strength=blend_strength
        )

        self.blend_history.append(blend)
        return blend

    def _generate_novel_aspects(self, concept1: Concept, concept2: Concept) -> List[str]:
        """Generate novel aspects that emerge from the blend."""
        novel = []

        # Combine relations
        combined_relations = list(set(concept1.relations + concept2.relations))
        novel.append(f"Unified understanding: {', '.join(combined_relations[:3])}")

        # Cross-domain insights
        if concept1.domain != concept2.domain:
            novel.append(f"Cross-domain insight: {concept1.domain} concept applied to {concept2.domain}")

        # Qualitative blending
        novel.append(f"Qualitative transfer: {concept1.theoretical_role} + {concept2.theoretical_role}")

        return novel

    def _generate_theoretical_implications(self, concept1: Concept, concept2: Concept) -> List[str]:
        """Generate theoretical implications of the blend."""
        implications = []

        # General implications based on concept domains
        domain_pairs = {
            ("quantum", "gravity"): [
                "Quantum gravity effects at microscopic scales",
                "Modification of uncertainty principle near gravitational sources",
                "Holographic principle: gravity encodes quantum information"
            ],
            ("thermodynamics", "gravity"): [
                "Black hole thermodynamics is fundamental, not analogy",
                "Universe as heat engine: cosmological entropic processes",
                "Gravitational entropy as cosmological constant"
            ],
            ("information", "gravity"): [
                "Spacetime geometry from quantum entanglement",
                "Holographic bound: information capacity scales with surface area",
                "ER = EPR: wormholes correspond to entanglement"
            ],
            ("information", "quantum"): [
                "Quantum states as information carriers",
                "Measurement as information extraction",
                "Decoherence as information loss to environment"
            ],
            ("biology", "physics"): [
                "Universe evolves through selection effects (anthropic principle)",
                "Cosmological natural selection: baby universes with varied constants",
                "Fitness landscapes in theory space"
            ]
        }

        domains = tuple(sorted([concept1.domain, concept2.domain]))
        if domains in domain_pairs:
            implications.extend(domain_pairs[domains])

        # Specific to the concepts
        implications.append(f"Mathematical framework: Combining {concept1.name} formalism with {concept2.name}")

        return implications

    def _generate_testable_predictions(self, concept1: Concept, concept2: Concept,
                                      blended_dims: Dict) -> List[str]:
        """Generate testable predictions from the blend."""
        predictions = []

        # Information-theoretic blends predict informational effects
        if blended_dims.get(ConceptualDimension.INFORMATION, 0) > 0.7:
            predictions.append("Information-theoretic limits on physical measurements")
            predictions.append("Entropic bounds on correlation functions")

        # Structural blends predict new structures
        if blended_dims.get(ConceptualDimension.STRUCTURAL, 0) > 0.7:
            predictions.append("Novel structural phases at critical points")
            predictions.append("Topological protection of certain states")

        # Dynamic blends predict new dynamics
        if blended_dims.get(ConceptualDimension.DYNAMIC, 0) > 0.7:
            predictions.append("Modified equations of motion with memory effects")
            predictions.append("Non-Markovian dynamics in certain regimes")

        # Specific cross-domain predictions
        if "entropy" in [concept1.name, concept2.name]:
            if "gravity" in [concept1.domain, concept2.domain]:
                predictions.append("Black hole entropy follows area law: S = A/4")
                predictions.append("Gravitational waves carry entropy")

        if "entanglement" in [concept1.name, concept2.name]:
            if "gravity" in [concept1.domain, concept2.domain]:
                predictions.append("Quantum correlations affect spacetime geometry")
                predictions.append("Entanglement harvesting across horizons")

        return predictions

    def _calculate_blend_strength(self, concept1: Concept, concept2: Concept,
                                  blended_dims: Dict) -> float:
        """Calculate how coherent the blend is."""
        # Blend strength based on:
        # 1. Dimensional complementarity (different strengths add value)
        # 2. Domain distance (more distant domains → more novel)
        # 3. Theoretical compatibility

        # Domain distance
        if concept1.domain == concept2.domain:
            domain_distance = 0.0
        else:
            domain_distance = 1.0

        # Dimensional complementarity: domains where one is strong, other is weak
        complementarity = 0.0
        for dim in ConceptualDimension:
            v1 = concept1.dimensional_signature.get(dim, 0)
            v2 = concept2.dimensional_signature.get(dim, 0)
            # Complement if one strong, one weak
            complementarity += abs(v1 - v2) / 2.0

        complementarity /= len(ConceptualDimension)

        # Theoretical compatibility based on relations
        relation_overlap = len(set(concept1.relations) & set(concept2.relations))
        relation_union = len(set(concept1.relations) | set(concept2.relations))
        compatibility = relation_overlap / relation_union if relation_union > 0 else 0

        # Overall blend strength
        strength = 0.4 * domain_distance + 0.3 * complementarity + 0.3 * compatibility

        return strength

    def discover_novel_theoretical_concepts(self, target_domain: str,
                                            min_novelty: float = 0.6) -> List[ConceptualBlend]:
        """
        Discover novel theoretical concepts for a target domain by blending
        with concepts from other domains.
        """
        target_space = self.conceptual_spaces.get(target_domain)
        if not target_space:
            return []

        novel_blends = []

        # Try blending each concept from target with concepts from other domains
        for target_concept in target_space.concepts.values():
            for other_domain, other_space in self.conceptual_spaces.items():
                if other_domain == target_domain:
                    continue

                for other_concept in other_space.concepts.values():
                    # Find high-similarity concept pairs
                    similarity = self._conceptual_similarity(target_concept, other_concept)

                    # Only blend if moderately similar (different enough to be interesting,
                    # similar enough to be coherent)
                    if 0.3 < similarity < 0.8:
                        blend = self.create_conceptual_blend(target_concept, other_concept)

                        if blend.blend_strength >= min_novelty:
                            novel_blends.append(blend)

        # Sort by blend strength
        novel_blends.sort(key=lambda b: b.blend_strength, reverse=True)

        return novel_blends


# Demonstration
if __name__ == "__main__":
    blender = ConceptualBlender()

    print("=" * 80)
    print("CONCEPTUAL BLENDING ENGINE")
    print("=" * 80)

    # Example 1: Find analogies between quantum mechanics and gravity
    print("\n1. ANALOGIES: Quantum Mechanics ↔ Gravity")
    print("-" * 80)
    analogies = blender.find_conceptual_analogy("quantum", "gravity", min_similarity=0.4)
    for concept1, concept2, similarity in analogies[:5]:
        print(f"{concept1.name} (quantum) ↔ {concept2.name} (gravity): {similarity:.2f}")

    # Example 2: Create novel blend
    print("\n2. CONCEPTUAL BLEND: Entanglement (quantum) + Event Horizon (gravity)")
    print("-" * 80)
    entanglement = blender.conceptual_spaces["quantum"].concepts["entanglement"]
    horizon = blender.conceptual_spaces["gravity"].concepts["event_horizon"]
    blend = blender.create_conceptual_blend(entanglement, horizon, "Quantum_Black_Hole_Entanglement")

    print(f"Blend: {blend.name}")
    print(f"Strength: {blend.blend_strength:.2f}")
    print(f"Novel aspects:")
    for aspect in blend.novel_aspects:
        print(f"  - {aspect}")
    print(f"Theoretical implications:")
    for impl in blend.theoretical_implications[:3]:
        print(f"  - {impl}")
    print(f"Testable predictions:")
    for pred in blend.testable_predictions[:3]:
        print(f"  - {pred}")

    # Example 3: Discover novel concepts for gravity
    print("\n3. NOVEL CONCEPT DISCOVERY for Gravity")
    print("-" * 80)
    novel_concepts = blender.discover_novel_theoretical_concepts("gravity", min_novelty=0.5)
    for i, blend in enumerate(novel_concepts[:3]):
        print(f"\n{i+1}. {blend.name} (strength: {blend.blend_strength:.2f})")
        print(f"   Sources: {blend.source_concepts[0].name} ({blend.source_concepts[0].domain}) + "
              f"{blend.source_concepts[1].name} ({blend.source_concepts[1].domain})")
        print(f"   Key prediction: {blend.testable_predictions[0] if blend.testable_predictions else 'N/A'}")
