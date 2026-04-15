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
ASTRA Live — Conceptual Blending Engine
Creates novel theoretical concepts by blending concepts from different domains.

Based on Gärdenfors' theory of conceptual spaces and cognitive linguistics.
Key insight: Innovation often comes from combining concepts across domains.

Examples from physics:
- ER=EPR: Entanglement ↔ Wormholes (Maldacena, Susskind)
- Holography: Quantum field theory ↔ Gravity (AdS/CFT)
- Thermodynamics: Black holes ↔ Thermodynamic systems
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class ConceptualDimension(Enum):
    """Dimensions for conceptual space representation."""
    SPATIAL = "spatial"        # Space, position, extension
    TEMPORAL = "temporal"      # Time, evolution, causality
    MATERIAL = "material"      # Substance, mass, energy
    DYNAMIC = "dynamic"        # Force, interaction, change
    INFORMATION = "information"  # Entropy, information, complexity
    STRUCTURAL = "structural"  # Topology, geometry, symmetry
    QUALITATIVE = "qualitative"  # Emergent properties, consciousness


@dataclass
class Concept:
    """A concept in multi-dimensional conceptual space."""
    name: str
    domain: str
    dimensions: Dict[ConceptualDimension, float]  # Position in each dimension
    properties: Set[str] = field(default_factory=set)
    relations: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConceptualBlend:
    """A novel concept created by blending two source concepts."""
    name: str
    source1: str
    source2: str
    domains: Tuple[str, str]
    blended_dimensions: Dict[ConceptualDimension, float]
    description: str
    theoretical_implications: List[str]
    confidence: float


@dataclass
class ConceptualAnalogy:
    """An analogy discovered between two domains."""
    domain1: str
    domain2: str
    concept1: str
    concept2: str
    similarity: float
    shared_dimensions: List[ConceptualDimension]
    mapping: Dict[str, str]


class ConceptualBlender:
    """
    Creates novel theoretical concepts through cross-domain blending.

    Methodology:
    1. Represent concepts in multi-dimensional space
    2. Find analogies between domains
    3. Blend concepts to create new theoretical constructs
    4. Generate testable predictions
    """

    def __init__(self):
        # Define conceptual spaces for major physics domains
        self.conceptual_spaces = self._initialize_conceptual_spaces()
        self.known_blends = []

    def _initialize_conceptual_spaces(self) -> Dict[str, Dict[str, Concept]]:
        """Initialize conceptual spaces for major physics domains."""
        spaces = {
            "quantum_mechanics": {
                "entanglement": Concept(
                    "entanglement", "quantum_mechanics",
                    {ConceptualDimension.INFORMATION: 0.9,
                     ConceptualDimension.STRUCTURAL: 0.7,
                     ConceptualDimension.SPATIAL: 0.5},
                    {"non-local correlations", "coherent superposition", "Bell inequalities"}
                ),
                "superposition": Concept(
                    "superposition", "quantum_mechanics",
                    {ConceptualDimension.INFORMATION: 0.8,
                     ConceptualDimension.STRUCTURAL: 0.6},
                    {"coexistence of states", "wave function collapse", "quantum interference"}
                ),
                "wave_function": Concept(
                    "wave_function", "quantum_mechanics",
                    {ConceptualDimension.INFORMATION: 0.9,
                     ConceptualDimension.STRUCTURAL: 0.8,
                     ConceptualDimension.SPATIAL: 0.6},
                    {"probability amplitude", "Hilbert space", "unitarity evolution"}
                ),
            },
            "general_relativity": {
                "spacetime": Concept(
                    "spacetime", "general_relativity",
                    {ConceptualDimension.SPATIAL: 0.9,
                     ConceptualDimension.TEMPORAL: 0.9,
                     ConceptualDimension.STRUCTURAL: 0.8},
                    {"curved geometry", "metric tensor", "Einstein equations"}
                ),
                "black_hole": Concept(
                    "black_hole", "general_relativity",
                    {ConceptualDimension.SPATIAL: 0.8,
                     ConceptualDimension.TEMPORAL: 0.7,
                     ConceptualDimension.MATERIAL: 0.9,
                     ConceptualDimension.INFORMATION: 0.6},
                    {"event horizon", "singularity", "gravitational collapse"}
                ),
                "wormhole": Concept(
                    "wormhole", "general_relativity",
                    {ConceptualDimension.SPATIAL: 0.9,
                     ConceptualDimension.TEMPORAL: 0.8,
                     ConceptualDimension.STRUCTURAL: 0.7},
                    {"Einstein-Rosen bridge", "topological feature", "causality connection"}
                ),
            },
            "thermodynamics": {
                "entropy": Concept(
                    "entropy", "thermodynamics",
                    {ConceptualDimension.INFORMATION: 0.8,
                     ConceptualDimension.MATERIAL: 0.6},
                    {"second law", "disorder", "statistical mechanics"}
                ),
                "temperature": Concept(
                    "temperature", "thermodynamics",
                    {ConceptualDimension.MATERIAL: 0.7,
                     ConceptualDimension.DYNAMIC: 0.6},
                    {"thermal equilibrium", "heat", "kinetic energy"}
                ),
                "free_energy": Concept(
                    "free_energy", "thermodynamics",
                    {ConceptualDimension.MATERIAL: 0.7,
                     ConceptualDimension.INFORMATION: 0.5},
                    {"available work", "Gibbs", "Helmholtz"}
                ),
            },
            "astrophysics": {
                "galaxy": Concept(
                    "galaxy", "astrophysics",
                    {ConceptualDimension.SPATIAL: 0.8,
                     ConceptualDimension.MATERIAL: 0.9,
                     ConceptualDimension.STRUCTURAL: 0.6},
                    {"stellar populations", "dark matter", "rotation curves"}
                ),
                "star_formation": Concept(
                    "star_formation", "astrophysics",
                    {ConceptualDimension.MATERIAL: 0.8,
                     ConceptualDimension.TEMPORAL: 0.7,
                     ConceptualDimension.DYNAMIC: 0.6},
                    {"molecular clouds", "Jeans instability", "initial mass function"}
                ),
                "accretion": Concept(
                    "accretion", "astrophysics",
                    {ConceptualDimension.MATERIAL: 0.8,
                     ConceptualDimension.DYNAMIC: 0.7,
                     ConceptualDimension.SPATIAL: 0.6},
                    {"disk formation", "angular momentum", "viscosity"}
                ),
            }
        }

        return spaces

    def find_conceptual_analogy(self, domain1: str, domain2: str,
                                min_similarity: float = 0.3) -> List[ConceptualAnalogy]:
        """
        Find analogies between two domains based on conceptual similarity.

        Returns analogies sorted by similarity score.
        """
        if domain1 not in self.conceptual_spaces or domain2 not in self.conceptual_spaces:
            return []

        analogies = []
        space1 = self.conceptual_spaces[domain1]
        space2 = self.conceptual_spaces[domain2]

        for name1, concept1 in space1.items():
            for name2, concept2 in space2.items():
                # Calculate similarity based on shared dimensions
                similarity = self._calculate_conceptual_similarity(concept1, concept2)
                shared_dims = self._get_shared_dimensions(concept1, concept2)

                if similarity >= min_similarity:
                    # Create mapping of properties
                    mapping = self._create_concept_mapping(concept1, concept2)

                    analogies.append(ConceptualAnalogy(
                        domain1=domain1,
                        domain2=domain2,
                        concept1=name1,
                        concept2=name2,
                        similarity=similarity,
                        shared_dimensions=shared_dims,
                        mapping=mapping
                    ))

        # Sort by similarity (descending)
        analogies.sort(key=lambda a: a.similarity, reverse=True)
        return analogies

    def create_conceptual_blend(self, concept1_name: str, concept2_name: str,
                               blend_name: str,
                               domain1: Optional[str] = None,
                               domain2: Optional[str] = None) -> Optional[ConceptualBlend]:
        """
        Create a novel theoretical concept by blending two existing concepts.

        This is how many theoretical breakthroughs happen:
        - ER=EPR: Entanglement + Wormhole
        - Holography: Quantum fields + Geometry
        - Black hole thermodynamics: Gravity + Thermodynamics
        """
        # Find the concepts
        concept1 = self._find_concept(concept1_name, domain1)
        concept2 = self._find_concept(concept2_name, domain2)

        if concept1 is None or concept2 is None:
            return None

        # Blend dimensions (weighted average favoring more extreme values)
        blended_dims = {}
        for dim in ConceptualDimension:
            val1 = concept1.dimensions.get(dim, 0)
            val2 = concept2.dimensions.get(dim, 0)
            # Blend: average, but enhance if both are high
            if val1 > 0.5 and val2 > 0.5:
                blended_dims[dim] = min(1.0, (val1 + val2) / 2 * 1.2)
            else:
                blended_dims[dim] = (val1 + val2) / 2

        # Generate description
        description = f"Blend of {concept1.name} ({concept1.domain}) and {concept2.name} ({concept2.domain})"

        # Generate theoretical implications
        implications = self._generate_blend_implications(concept1, concept2)

        # Calculate confidence based on novelty and coherence
        confidence = self._calculate_blend_confidence(concept1, concept2, blended_dims)

        blend = ConceptualBlend(
            name=blend_name,
            source1=concept1.name,
            source2=concept2.name,
            domains=(concept1.domain, concept2.domain),
            blended_dimensions=blended_dims,
            description=description,
            theoretical_implications=implications,
            confidence=confidence
        )

        self.known_blends.append(blend)
        return blend

    def discover_novel_theoretical_concepts(self, target_domain: str,
                                           min_novelty: float = 0.5) -> List[ConceptualBlend]:
        """
        Automatically discover novel theoretical concepts for a domain.

        Uses cross-domain blending to generate new theoretical constructs.
        """
        novel_concepts = []

        # Skip if target domain not in our spaces
        if target_domain not in self.conceptual_spaces:
            return []

        # Try blending with concepts from other domains
        for other_domain, concepts in self.conceptual_spaces.items():
            if other_domain == target_domain:
                continue

            for target_concept_name in self.conceptual_spaces[target_domain].keys():
                for other_concept_name in concepts.keys():
                    # Create blend
                    blend_name = f"{target_concept_name}-{other_concept_name}_blend"
                    blend = self.create_conceptual_blend(
                        target_concept_name, other_concept_name,
                        blend_name, target_domain, other_domain
                    )

                    if blend and blend.confidence >= min_novelty:
                        # Check if truly novel
                        if not self._is_similar_to_known(blend):
                            novel_concepts.append(blend)

        # Sort by confidence/novelty
        novel_concepts.sort(key=lambda b: b.confidence, reverse=True)
        return novel_concepts[:10]  # Top 10

    def _calculate_conceptual_similarity(self, concept1: Concept, concept2: Concept) -> float:
        """Calculate similarity between two concepts [0-1]."""
        # Find common dimensions
        all_dims = set(concept1.dimensions.keys()) | set(concept2.dimensions.keys())

        if not all_dims:
            return 0.0

        # Calculate cosine-like similarity
        dot_product = 0.0
        norm1 = 0.0
        norm2 = 0.0

        for dim in all_dims:
            val1 = concept1.dimensions.get(dim, 0)
            val2 = concept2.dimensions.get(dim, 0)
            dot_product += val1 * val2
            norm1 += val1 * val1
            norm2 += val2 * val2

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (np.sqrt(norm1) * np.sqrt(norm2))

    def _get_shared_dimensions(self, concept1: Concept, concept2: Concept) -> List[ConceptualDimension]:
        """Get dimensions where both concepts have significant values."""
        shared = []
        for dim in ConceptualDimension:
            val1 = concept1.dimensions.get(dim, 0)
            val2 = concept2.dimensions.get(dim, 0)
            if val1 > 0.3 and val2 > 0.3:
                shared.append(dim)
        return shared

    def _create_concept_mapping(self, concept1: Concept, concept2: Concept) -> Dict[str, str]:
        """Create a mapping of properties from concept1 to concept2."""
        mapping = {}
        for prop1 in concept1.properties:
            # Find similar property in concept2
            for prop2 in concept2.properties:
                if self._property_similarity(prop1, prop2) > 0.5:
                    mapping[prop1] = prop2
                    break
        return mapping

    def _property_similarity(self, prop1: str, prop2: str) -> float:
        """Simple string similarity for properties."""
        # Simple word overlap
        words1 = set(prop1.lower().split('_'))
        words2 = set(prop2.lower().split('_'))
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0

    def _find_concept(self, name: str, domain: Optional[str] = None) -> Optional[Concept]:
        """Find a concept by name (and optionally domain)."""
        if domain:
            if domain in self.conceptual_spaces:
                return self.conceptual_spaces[domain].get(name)
        else:
            # Search all domains
            for space in self.conceptual_spaces.values():
                if name in space:
                    return space[name]
        return None

    def _generate_blend_implications(self, concept1: Concept, concept2: Concept) -> List[str]:
        """Generate theoretical implications of blending two concepts."""
        implications = []

        # Domain-specific implications
        domains = {concept1.domain, concept2.domain}

        if "quantum_mechanics" in domains and "general_relativity" in domains:
            implications.append("Quantum gravity effects at macroscopic scales")
            implications.append("Spacetime emerges from entanglement structure")
            implications.append("Black hole information is encoded in Hawking radiation")

        if "thermodynamics" in domains and "general_relativity" in domains:
            implications.append("Black holes have thermodynamic properties")
            implications.append("Entropy bounds apply to gravitational systems")
            implications.append("Temperature associated with horizons")

        if "quantum_mechanics" in domains and "astrophysics" in domains:
            implications.append("Quantum coherence at astronomical scales")
            implications.append("Macroscopic quantum phenomena in extreme environments")

        # Generic implications
        implications.append(f"Novel interaction between {concept1.domain} and {concept2.domain}")
        implications.append("Testable predictions from cross-domain correspondence")

        return implications[:5]  # Top 5

    def _calculate_blend_confidence(self, concept1: Concept, concept2: Concept,
                                    blended_dims: Dict[ConceptualDimension, float]) -> float:
        """Calculate confidence score for a conceptual blend."""
        # Base confidence from dimensional coherence
        values = list(blended_dims.values())
        coherence = np.std(values) if len(values) > 1 else 0
        base_conf = 1.0 - min(coherence, 1.0)

        # Boost for complementary domains
        domain_boost = 0.2 if concept1.domain != concept2.domain else 0.0

        # Penalty for extreme blends (too novel)
        novelty_penalty = 0.1 if np.mean(values) < 0.3 else 0.0

        confidence = base_conf + domain_boost - novelty_penalty
        return np.clip(confidence, 0.0, 1.0)

    def _is_similar_to_known(self, blend: ConceptualBlend) -> bool:
        """Check if blend is similar to already known blends."""
        for known in self.known_blends:
            # Check same source concepts
            if {blend.source1, blend.source2} == {known.source1, known.source2}:
                return True
        return False


# Demonstration
if __name__ == "__main__":
    print("=" * 80)
    print("CONCEPTUAL BLENDING ENGINE")
    print("=" * 80)

    blender = ConceptualBlender()

    # Example 1: Find analogies between quantum mechanics and general relativity
    print("\n1. ANALOGY: Quantum Mechanics ↔ General Relativity")
    print("-" * 80)

    analogies = blender.find_conceptual_analogy("quantum_mechanics", "general_relativity")

    for analogy in analogies[:3]:
        print(f"\n{analogy.concept1} ↔ {analogy.concept2}")
        print(f"  Similarity: {analogy.similarity:.3f}")
        print(f"  Shared dimensions: {[d.value for d in analogy.shared_dimensions]}")

    # Example 2: Create ER=EPR blend
    print("\n2. BLEND: Entanglement + Wormhole = ER=EPR Correspondence")
    print("-" * 80)

    blend = blender.create_conceptual_blend("entanglement", "wormhole", "ER=EPR Correspondence")

    if blend:
        print(f"Name: {blend.name}")
        print(f"Domains: {blend.domains}")
        print(f"Description: {blend.description}")
        print(f"Confidence: {blend.confidence:.3f}")
        print("\nTheoretical Implications:")
        for imp in blend.theoretical_implications[:3]:
            print(f"  • {imp}")

    # Example 3: Discover novel concepts for astrophysics
    print("\n3. NOVEL CONCEPTS for Astrophysics")
    print("-" * 80)

    novel = blender.discover_novel_theoretical_concepts("astrophysics", min_novelty=0.4)

    for i, concept in enumerate(novel[:3], 1):
        print(f"\n{i}. {concept.name}")
        print(f"   Blend: {concept.source1} + {concept.source2}")
        print(f"   Confidence: {concept.confidence:.3f}")
        print(f"   {concept.description}")
