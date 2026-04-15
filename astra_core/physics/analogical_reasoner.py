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
Physical analogical reasoning engine for STAN-XI-ASTRO

Applies analogical reasoning to novel physical phenomena.
Enables transfer of understanding from known to novel phenomena.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PhysicalAnalogy:
    """
    An analogy between physical phenomena

    Attributes:
        source_phenomenon: Known phenomenon
        target_phenomenon: Novel phenomenon
        structural_similarity: How structurally similar (0-1)
        mapping: Mapping of concepts between phenomena
        differences: Key differences between phenomena
        confidence: Confidence in the analogy
    """
    source_phenomenon: str
    target_phenomenon: str
    structural_similarity: float
    mapping: Dict[str, str] = field(default_factory=dict)
    differences: List[str] = field(default_factory=list)
    confidence: float = 0.8

    def __post_init__(self):
        if not 0 <= self.structural_similarity <= 1:
            raise ValueError("structural_similarity must be between 0 and 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class Phenomenon:
    """
    Representation of a physical phenomenon

    Attributes:
        name: Phenomenon name
        structure: Structural description
        parameters: Physical parameters
        equations: Governing equations
        key_features: Important features
    """
    name: str
    structure: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    equations: List[str] = field(default_factory=list)
    key_features: List[str] = field(default_factory=list)


class PhysicalAnalogicalReasoner:
    """
    Analogical reasoning for physical intuition

    Enables transfer of understanding from known to novel phenomena.
    """

    def __init__(self):
        """Initialize analogical reasoner"""
        self.phenomena_database: Dict[str, Phenomenon] = {}
        self.analogy_history: List[PhysicalAnalogy] = []

        # Register common phenomena
        self._register_common_phenomena()

        logger.info("PhysicalAnalogicalReasoner initialized")

    def _register_common_phenomena(self):
        """Register common astrophysical phenomena"""
        # Black hole accretion
        self.register_phenomenon(Phenomenon(
            name="accretion_disk",
            structure={
                "type": "rotating_disk",
                "components": ["central_mass", "disk", "viscosity", "magnetic_field"],
                "interactions": ["gravitational", "viscous_heating", "magnetic_torque"],
                "driving_forces": ["gravity"],
                "dissipative": "viscosity"
            },
            parameters={
                "mass_range": (1e33, 1e40),
                "temperature_range": (1e4, 1e8),
                "density_range": (1e-15, 1e-8)
            },
            equations=[
                "Navier-Stokes with viscosity",
                "Energy equation: Q_visc = nu * (dOmega/dr)^2",
                "Angular momentum transport"
            ],
            key_features=["accretion_power", "jet_formation", "spectral_energy_distribution"]
        ))

        # Stellar oscillation
        self.register_phenomenon(Phenomenon(
            name="stellar_oscillation",
            structure={
                "type": "oscillating_sphere",
                "components": ["star", "oscillation_modes", "driving", "damping"],
                "interactions": ["pressure", "gravity", "radiation"],
                "driving_forces": ["pressure_gradient", "turbulence"],
                "dissipative": ["radiation_damping"]
            },
            parameters={
                "period_range": (1e-3, 1),
                "amplitude_range": (1e-6, 1e-2),
                "frequency_range": (1e-6, 1)
            },
            equations=[
                "Wave equation with gravity",
                "Boundary conditions at surface",
                "Mode coupling"
            ],
            key_features=["p_modes", "g_modes", "asteroseismology"]
        ))

        # Planetary rings
        self.register_phenomenon(Phenomenon(
            name="planetary_rings",
            structure={
                "type": "disk_system",
                "components": ["particles", "central_body", "shepherd_moons"],
                "interactions": ["collisions", "gravitational_perturbations"],
                "driving_forces": ["gravity", "orbital_mechanics"],
                "dissipative": ["inelastic_collisions"]
            },
            parameters={
                "particle_size_range": (1e-4, 10),
                "optical_depth_range": (0.01, 10),
                "velocity_range": (1e3, 3e4)
            },
            equations=[
                "Balance of gravitational and collisional forces",
                "Viscous spreading equation",
                "Gap opening by moons"
            ],
            key_features=["resonances", "spokes", "gaps"]
        ))

    def register_phenomenon(self, phenomenon: Phenomenon) -> None:
        """
        Register a physical phenomenon in the database

        Args:
            phenomenon: Phenomenon to register
        """
        self.phenomena_database[phenomenon.name] = phenomenon
        logger.info(f"Registered phenomenon: {phenomenon.name}")

    def find_analogies(
        self,
        target_phenomenon: str,
        min_similarity: float = 0.3
    ) -> List[PhysicalAnalogy]:
        """
        Find analogies to a target phenomenon

        Args:
            target_phenomenon: Phenomenon to find analogies for
            min_similarity: Minimum similarity threshold

        Returns:
            List of candidate analogies ranked by similarity
        """
        if target_phenomenon not in self.phenomena_database:
            logger.warning(f"Target phenomenon not in database: {target_phenomenon}")
            return []

        target = self.phenomena_database[target_phenomenon]
        analogies = []

        for source_name, source_data in self.phenomena_database.items():
            if source_name == target_phenomenon:
                continue

            # Compute structural similarity
            similarity, mapping = self._compute_structural_similarity(
                target.structure,
                source_data.structure
            )

            if similarity >= min_similarity:
                # Identify differences
                differences = self._identify_differences(
                    target, source_data, mapping
                )

                analogy = PhysicalAnalogy(
                    source_phenomenon=source_name,
                    target_phenomenon=target_phenomenon,
                    structural_similarity=similarity,
                    mapping=mapping,
                    differences=differences,
                    confidence=similarity * 0.8
                )
                analogies.append(analogy)

        # Sort by similarity
        analogies.sort(key=lambda x: x.structural_similarity, reverse=True)

        return analogies

    def apply_analogy(
        self,
        analogy: PhysicalAnalogy,
        target_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply analogy to generate understanding/predictions

        Args:
            analogy: Analogy to apply
            target_parameters: Parameters for target phenomenon

        Returns:
            Predictions and insights transferred from analogy
        """
        source_phenomenon = self.phenomena_database.get(analogy.source_phenomenon)

        if source_phenomenon is None:
            logger.warning(f"Source phenomenon not found: {analogy.source_phenomenon}")
            return {
                'insights': [],
                'predictions': {},
                'confidence': 0.0,
                'caveats': analogy.differences
            }

        # Transfer understanding through mapping
        insights = []
        predictions = {}

        for source_concept, target_concept in analogy.mapping.items():
            # Transfer qualitative understanding
            if source_concept in source_phenomenon.structure:
                source_understanding = source_phenomenon.structure[source_concept]

                insight = {
                    'concept': target_concept,
                    'understanding': self._adapt_understanding(
                        source_understanding,
                        target_parameters.get(target_concept, {})
                    ),
                    'source': source_concept,
                    'confidence': analogy.confidence
                }
                insights.append(insight)

        # Generate predictions based on transferred equations
        for eq in source_phenomenon.equations:
            adapted_eq = self._adapt_equation(eq, analogy.mapping)
            predictions[adapted_eq] = analogy.confidence

        self.analogy_history.append(analogy)

        return {
            'insights': insights,
            'predictions': predictions,
            'confidence': analogy.confidence,
            'caveats': analogy.differences
        }

    def _compute_structural_similarity(
        self,
        structure_a: Dict[str, Any],
        structure_b: Dict[str, Any]
    ) -> Tuple[float, Dict[str, str]]:
        """
        Compute structural similarity between two phenomena

        Returns:
            (similarity_score, concept_mapping)
        """
        # Extract structural features
        features_a = self._extract_structural_features(structure_a)
        features_b = self._extract_structural_features(structure_b)

        # Compute feature overlap
        all_features = set(features_a.keys()) | set(features_b.keys())
        common_features = set(features_a.keys()) & set(features_b.keys())

        if not all_features:
            return 0.0, {}

        # Jaccard similarity
        similarity = len(common_features) / len(all_features)

        # Create concept mapping
        mapping = {}
        for feature in common_features:
            if self._features_match(features_a[feature], features_b[feature]):
                mapping[feature] = feature

        return similarity, mapping

    def _extract_structural_features(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structural features from phenomenon"""
        features = {}

        # Type
        if 'type' in structure:
            features['type'] = structure['type']

        # Components
        if 'components' in structure:
            for comp in structure['components']:
                features[comp] = structure['components'][comp] if isinstance(structure['components'], dict) else comp

        # Interactions
        if 'interactions' in structure:
            for i, interaction in enumerate(structure['interactions']):
                features[f'interaction_{i}'] = interaction

        # Driving forces
        if 'driving_forces' in structure:
            for i, force in enumerate(structure['driving_forces']):
                features[f'driving_{i}'] = force

        # Dissipative processes
        if 'dissipative' in structure:
            features['dissipation'] = structure['dissipative']

        return features

    def _features_match(self, feature_a: Any, feature_b: Any) -> bool:
        """Check if two features match"""
        if isinstance(feature_a, dict) and isinstance(feature_b, dict):
            return self._dicts_match(feature_a, feature_b)
        return feature_a == feature_b

    def _dicts_match(self, dict_a: Dict[str, Any], dict_b: Dict[str, Any]) -> bool:
        """Check if dictionaries match (with numerical tolerance)"""
        if set(dict_a.keys()) != set(dict_b.keys()):
            return False

        for key in dict_a:
            val_a = dict_a[key]
            val_b = dict_b[key]

            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                if abs(val_a - val_b) / max(abs(val_a), 1e-10) > 0.1:
                    return False
            elif val_a != val_b:
                return False

        return True

    def _identify_differences(
        self,
        target: Phenomenon,
        source: Phenomenon,
        mapping: Dict[str, str]
    ) -> List[str]:
        """Identify key differences between phenomena"""
        differences = []

        # Check for unmapped concepts
        target_concepts = set(target.structure.keys())
        source_concepts = set(source.structure.keys())
        mapped_source = set(mapping.keys())

        for concept in target_concepts - mapped_source - {'type'}:
            differences.append(f"No analog for {concept}")

        # Check for different parameter ranges
        if 'parameters' in target.structure and 'parameters' in source.structure:
            for param in set(target.structure['parameters']) & set(source.structure['parameters']):
                range_a = target.structure['parameters'][param]
                range_b = source.structure['parameters'][param]
                if self._ranges_differ(range_a, range_b):
                    differences.append(f"Different range for {param}")

        return differences

    def _ranges_differ(self, range_a: Any, range_b: Any) -> bool:
        """Check if parameter ranges differ significantly"""
        if isinstance(range_a, (list, tuple)) and isinstance(range_b, (list, tuple)):
            if len(range_a) >= 2 and len(range_b) >= 2:
                return abs(range_a[0] - range_b[0]) > 0.1 * max(abs(range_a[0]), abs(range_b[0]))
        return range_a != range_b

    def _adapt_understanding(self, source_understanding: Any, target_parameters: Dict[str, Any]) -> Any:
        """Adapt understanding from source to target context"""
        return source_understanding

    def _adapt_equation(self, equation: str, mapping: Dict[str, str]) -> str:
        """Adapt equation using concept mapping"""
        adapted = equation
        for source_concept, target_concept in mapping.items():
            adapted = adapted.replace(source_concept, target_concept)
        return adapted

    def get_analogy_history(self) -> List[PhysicalAnalogy]:
        """Get history of applied analogies"""
        return self.analogy_history.copy()

    def get_status(self) -> Dict[str, Any]:
        """Get analogical reasoner status"""
        return {
            'registered_phenomena': list(self.phenomena_database.keys()),
            'analogies_applied': len(self.analogy_history),
            'phenomena_count': len(self.phenomena_database)
        }
