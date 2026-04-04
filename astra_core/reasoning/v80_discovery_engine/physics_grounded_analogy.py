"""
Physics-Grounded Analogical Reasoning Module

Addresses Limitation 2: Superficial analogies that lack physical meaning

This module validates analogies by checking:
- Causal similarity: Do the systems share causal mechanisms?
- Energy/momentum scale: Are the physical scales compatible?
- Governing equations: Do they share mathematical structure?
- Dimensional consistency: Can units be meaningfully mapped?
- Conservation laws: Are the same invariants present?
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from scipy.spatial.distance import cosine
from scipy.stats import pearsonr, spearmanr
import warnings
import re


@dataclass
class PhysicalSystem:
    """Represents a physical system for analogy comparison."""
    name: str
    variables: Dict[str, str]  # variable -> unit
    governing_equations: List[str]
    conservation_laws: List[str]
    characteristic_scales: Dict[str, float]  # quantity -> scale
    causal_structure: Optional[Dict[str, List[str]]] = None  # variable -> causes/effects


@dataclass
class Analogy:
    """Represents an analogy between systems."""
    source_system: str
    target_system: str
    similarity_score: float
    physical_grounding: float  # How physically meaningful is the analogy
    structural_similarity: Dict[str, float]
    validity_criteria: List[str]
    confidence: float
    explanation: str


class PhysicsGroundedAnalogy:
    """
    Validate analogies by physical grounding rather than surface features.

    Methods:
    1. Causal Similarity: Compare causal graphs
    2. Scale Compatibility: Check if energy/momentum scales match
    3. Equation Structure: Compare differential equation operators
    4. Dimensional Analysis: Validate unit mappings
    5. Conservation Law Validation: Ensure invariants match
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize physics-grounded analogical reasoning engine.

        Args:
            config: Configuration dict with keys:
                - scale_tolerance: Tolerance for scale differences (default: 1.0)
                - min_grounding_score: Minimum physical grounding (default: 0.5)
                - use_causal_validation: Enable causal structure comparison (default: True)
        """
        config = config or {}
        self.scale_tolerance = config.get('scale_tolerance', 1.0)
        self.min_grounding_score = config.get('min_grounding_score', 0.5)
        self.use_causal_validation = config.get('use_causal_validation', True)

        # Known physical systems database
        self.systems_db: Dict[str, PhysicalSystem] = {}

        # Build initial database
        self._build_systems_database()

        # Validated analogies cache
        self.analogy_cache: Dict[Tuple[str, str], Analogy] = {}

    def _build_systems_database(self):
        """Build database of known physical systems."""
        # Molecular cloud collapse
        self.systems_db['molecular_cloud'] = PhysicalSystem(
            name='Molecular Cloud Collapse',
            variables={'mass': 'kg', 'radius': 'm', 'velocity': 'm/s', 'temperature': 'K',
                       'magnetic_field': 'T', 'density': 'kg/m^3'},
            governing_equations=[
                'Jeans instability: d²ρ/dt² = (c_s² + v_A²)∇²ρ + 4πGρρ',
                'Virial theorem: 2K + U + M = 0'
            ],
            conservation_laws=['mass', 'momentum', 'energy', 'magnetic_flux'],
            characteristic_scales={'jeans_mass': 1e30, 'jeans_length': 1e16, 'temperature': 10},
            causal_structure={
                'density': ['temperature', 'magnetic_field'],
                'temperature': ['heating_rate', 'cooling_rate'],
                'collapse': ['density', 'temperature', 'magnetic_field']
            }
        )

        # Protoplanetary disk
        self.systems_db['protoplanetary_disk'] = PhysicalSystem(
            name='Protoplanetary Disk',
            variables={'mass': 'kg', 'radius': 'm', 'angular_velocity': 'rad/s',
                       'viscosity': 'm^2/s', 'temperature': 'K'},
            governing_equations=[
                'Disk diffusion: ∂Σ/∂t = (3/r)∂/∂r[√(r)∂(νΣ√r)/∂r]',
                'Radial drift: v_r = -2ν/(3r)'
            ],
            conservation_laws=['mass', 'angular_momentum', 'energy'],
            characteristic_scales={'disk_radius': 1e11, 'accretion_rate': 1e-8, 'temperature': 100},
            causal_structure={
                'accretion': ['viscosity', 'mass'],
                'temperature': ['accretion_rate', 'irradiation'],
                'gap_formation': ['planet_mass', 'disk_viscosity']
            }
        )

        # Stellar atmosphere
        self.systems_db['stellar_atmosphere'] = PhysicalSystem(
            name='Stellar Atmosphere',
            variables={'temperature': 'K', 'pressure': 'Pa', 'density': 'kg/m^3',
                       'optical_depth': 'dimensionless'},
            governing_equations=[
                'Radiative transfer: dI/dτ = -I + S',
                'Hydrostatic equilibrium: dP/dτ = g/κ'
            ],
            conservation_laws=['energy', 'momentum'],
            characteristic_scales={'pressure': 1e4, 'temperature': 1e4, 'optical_depth': 1},
            causal_structure={
                'temperature': ['optical_depth', 'heating'],
                'pressure': ['temperature', 'gravity'],
                'line_formation': ['temperature', 'pressure', 'optical_depth']
            }
        )

        # Accretion disk
        self.systems_db['accretion_disk'] = PhysicalSystem(
            name='Accretion Disk',
            variables={'mass': 'kg', 'accretion_rate': 'kg/s', 'radius': 'm',
                       'magnetic_field': 'T', 'viscosity': 'm^2/s'},
            governing_equations=[
                'Shakura-Sunyaev: ν = αc_sH',
                'Energy balance: Q_vis = Q_adv + Q_rad'
            ],
            conservation_laws=['mass', 'angular_momentum', 'energy'],
            characteristic_scales={'inner_radius': 1e8, 'accretion_rate': 1e18, 'temperature': 1e7},
            causal_structure={
                'luminosity': ['accretion_rate', 'efficiency'],
                'temperature': ['accretion_rate', 'radius', 'viscosity'],
                'jet_formation': ['magnetic_field', 'accretion_rate']
            }
        )

        # Interstellar medium
        self.systems_db['interstellar_medium'] = PhysicalSystem(
            name='Interstellar Medium',
            variables={'density': 'kg/m^3', 'temperature': 'K', 'pressure': 'Pa',
                       'magnetic_field': 'T', 'cosmic_ray_flux': 'm^-2s^-1'},
            governing_equations=[
                'MHD equations: ∂ρ/∂t + ∇·(ρv) = 0',
                'Energy equation: ρ(∂e/∂t + v·∇e) = -P∇·v + heating - cooling'
            ],
            conservation_laws=['mass', 'momentum', 'energy', 'magnetic_flux'],
            characteristic_scales={'density': 1e-21, 'temperature': 100, 'magnetic_field': 1e-10},
            causal_structure={
                'temperature': ['cosmic_ray_flux', 'heating', 'cooling'],
                'ionization': ['cosmic_ray_flux', 'uv_flux'],
                'turbulence': ['supernova_rate', 'shear']
            }
        )

    def validate_analogy(
        self,
        source_system: str,
        target_system: str
    ) -> Analogy:
        """
        Validate whether an analogy between systems is physically grounded.

        Args:
            source_system: Name of source system
            target_system: Name of target system

        Returns:
            Analogy object with validation results
        """
        # Check cache first
        cache_key = (source_system, target_system)
        if cache_key in self.analogy_cache:
            return self.analogy_cache[cache_key]

        # Get system objects
        source = self.systems_db.get(source_system)
        target = self.systems_db.get(target_system)

        if source is None or target is None:
            raise ValueError(f"System(s) not found in database: {source_system}, {target_system}")

        # Compute various similarity metrics
        structural_sim = self._compute_structural_similarity(source, target)
        scale_sim = self._compute_scale_compatibility(source, target)
        causal_sim = self._compute_causal_similarity(source, target) if self.use_causal_validation else 0.5
        conservation_sim = self._compute_conservation_law_similarity(source, target)

        # Overall physical grounding score
        physical_grounding = np.mean([
            scale_sim,
            causal_sim,
            conservation_sim
        ])

        # Overall similarity (structural + physical)
        similarity_score = 0.4 * np.mean(list(structural_sim.values())) + 0.6 * physical_grounding

        # Generate validity criteria
        validity_criteria = self._generate_validity_criteria(source, target, {
            'structural': structural_sim,
            'scale': scale_sim,
            'causal': causal_sim,
            'conservation': conservation_sim
        })

        # Generate explanation
        explanation = self._generate_explanation(source, target, {
            'structural': structural_sim,
            'scale': scale_sim,
            'causal': causal_sim,
            'conservation': conservation_sim,
            'grounding': physical_grounding
        })

        analogy = Analogy(
            source_system=source_system,
            target_system=target_system,
            similarity_score=float(similarity_score),
            physical_grounding=float(physical_grounding),
            structural_similarity=structural_sim,
            validity_criteria=validity_criteria,
            confidence=float(similarity_score * physical_grounding),
            explanation=explanation
        )

        # Cache result
        self.analogy_cache[cache_key] = analogy

        return analogy

    def _compute_structural_similarity(
        self,
        source: PhysicalSystem,
        target: PhysicalSystem
    ) -> Dict[str, float]:
        """Compute structural similarity between systems."""
        similarity = {}

        # Variable overlap (same physical quantities)
        source_vars = set(source.variables.keys())
        target_vars = set(target.variables.keys())
        overlap = source_vars & target_vars
        union = source_vars | target_vars
        similarity['variable_overlap'] = len(overlap) / len(union) if union else 0

        # Equation structure similarity
        source_eq_patterns = self._extract_equation_patterns(source.governing_equations)
        target_eq_patterns = self._extract_equation_patterns(target.governing_equations)

        pattern_overlap = source_eq_patterns & target_eq_patterns
        pattern_union = source_eq_patterns | target_eq_patterns
        similarity['equation_structure'] = len(pattern_overlap) / len(pattern_union) if pattern_union else 0

        # Dimensional similarity (based on variable types)
        similarity['dimensional'] = self._compute_dimensional_similarity(source, target)

        return similarity

    def _extract_equation_patterns(self, equations: List[str]) -> set:
        """Extract mathematical patterns from equations."""
        patterns = set()

        # Look for differential operators
        if any('∂' in eq or 'd²' in eq or 'd/dt' in eq for eq in equations):
            patterns.add('differential_equation')

        # Look for specific operators
        if any('∇' in eq or 'grad' in eq.lower() for eq in equations):
            patterns.add('gradient_operator')

        if any('∇²' in eq or 'laplacian' in eq.lower() for eq in equations):
            patterns.add('laplacian_operator')

        # Look for conservation form
        if any('∂/∂t + ∇·' in eq or 'continuity' in eq.lower() for eq in equations):
            patterns.add('conservation_form')

        # Look for source terms
        if any(' heating ' in eq or ' cooling' in eq or ' source' in eq.lower() for eq in equations):
            patterns.add('source_terms')

        return patterns

    def _compute_dimensional_similarity(
        self,
        source: PhysicalSystem,
        target: PhysicalSystem
    ) -> float:
        """Check if variables have compatible dimensions."""
        # Simple: count variables with same unit type
        source_units = set(source.variables.values())
        target_units = set(target.variables.values())

        overlap = source_units & target_units
        union = source_units | target_units

        return len(overlap) / len(union) if union else 0

    def _compute_scale_compatibility(
        self,
        source: PhysicalSystem,
        target: PhysicalSystem
    ) -> float:
        """Check if characteristic scales are compatible."""
        if not source.characteristic_scales or not target.characteristic_scales:
            return 0.5

        # Compare scales (within tolerance)
        compatibilities = []

        for scale_name, source_scale in source.characteristic_scales.items():
            if scale_name in target.characteristic_scales:
                target_scale = target.characteristic_scales[scale_name]

                # Compute log ratio
                log_ratio = np.log10(source_scale / (target_scale + 1e-10))

                # Check if within tolerance
                if abs(log_ratio) < self.scale_tolerance:
                    compatibilities.append(1.0)
                else:
                    # Partial credit for being within 2x tolerance
                    compatibilities.append(max(0, 1 - abs(log_ratio) / (2 * self.scale_tolerance)))

        return np.mean(compatibilities) if compatibilities else 0.5

    def _compute_causal_similarity(
        self,
        source: PhysicalSystem,
        target: PhysicalSystem
    ) -> float:
        """Compare causal structures."""
        if source.causal_structure is None or target.causal_structure is None:
            return 0.5

        # Compare causal graphs
        source_causes = set()
        target_causes = set()

        for effects in source.causal_structure.values():
            source_causes.update(effects)

        for effects in target.causal_structure.values():
            target_causes.update(effects)

        # Also compare causal relations
        source_relations = set()
        for cause, effects in source.causal_structure.items():
            for effect in effects:
                source_relations.add(f"{cause}->{effect}")

        target_relations = set()
        for cause, effects in target.causal_structure.items():
            for effect in effects:
                target_relations.add(f"{cause}->{effect}")

        # Jaccard similarity
        intersection = source_relations & target_relations
        union = source_relations | target_relations

        return len(intersection) / len(union) if union else 0

    def _compute_conservation_law_similarity(
        self,
        source: PhysicalSystem,
        target: PhysicalSystem
    ) -> float:
        """Compare conservation laws."""
        source_laws = set(source.conservation_laws)
        target_laws = set(target.conservation_laws)

        intersection = source_laws & target_laws
        union = source_laws | target_laws

        return len(intersection) / len(union) if union else 0

    def _generate_validity_criteria(
        self,
        source: PhysicalSystem,
        target: PhysicalSystem,
        similarities: Dict[str, Any]
    ) -> List[str]:
        """Generate criteria for analogy validity."""
        criteria = []

        # Scale-based criteria
        if similarities['scale'] < 0.7:
            criteria.append(
                "Analogy limited by scale mismatch: consider renormalization"
            )

        # Causal structure criteria
        if similarities['causal'] < 0.5:
            criteria.append(
                "Causal mechanisms differ: analogy may be superficial"
            )

        # Conservation law criteria
        if similarities['conservation'] < 0.5:
            criteria.append(
                "Different conservation laws: analogy may break down"
            )

        # Overall grounding
        if similarities.get('grounding', 0.5) < self.min_grounding_score:
            criteria.append(
                "WARNING: Analogy lacks physical grounding - do not use for inference"
            )

        return criteria

    def _generate_explanation(
        self,
        source: PhysicalSystem,
        target: PhysicalSystem,
        similarities: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation of analogy validity."""
        parts = []

        # Overall assessment
        grounding = similarities.get('grounding', 0.5)
        if grounding > 0.7:
            parts.append("Strong physical grounding: systems share fundamental physics.")
        elif grounding > 0.5:
            parts.append("Moderate physical grounding: analogy useful but caution required.")
        else:
            parts.append("Weak physical grounding: analogy may be superficial.")

        # Specific similarities
        if similarities['structural']['variable_overlap'] > 0.5:
            parts.append(
                f"High variable overlap ({similarities['structural']['variable_overlap']:.1%}): "
                "similar physical quantities."
            )

        if similarities['scale'] > 0.7:
            parts.append(
                f"Scales are compatible: can apply similar scaling laws."
            )
        elif similarities['scale'] < 0.4:
            parts.append(
                f"Scales differ significantly: need rescaling for analogy."
            )

        if similarities['causal'] > 0.6:
            parts.append(
                f"Causal structures similar: mechanisms may transfer."
            )

        if similarities['conservation'] > 0.7:
            parts.append(
                f"Same conservation laws: fundamental invariants match."
            )

        return " ".join(parts)

    def find_best_analogies(
        self,
        target_system: str,
        top_k: int = 3
    ) -> List[Analogy]:
        """
        Find the best analogies to a target system.

        Args:
            target_system: System to find analogies for
            top_k: Number of top analogies to return

        Returns:
            List of best analogies, sorted by physical grounding
        """
        if target_system not in self.systems_db:
            raise ValueError(f"Target system {target_system} not in database")

        analogies = []

        for source_name in self.systems_db:
            if source_name == target_system:
                continue

            try:
                analogy = self.validate_analogy(source_name, target_system)
                analogies.append(analogy)
            except Exception as e:
                warnings.warn(f"Failed to validate analogy {source_name}->{target_system}: {e}")

        # Sort by physical grounding, then similarity
        analogies.sort(key=lambda a: (a.physical_grounding, a.similarity_score), reverse=True)

        return analogies[:top_k]

    def learn_from_analogy(
        self,
        source_system: str,
        target_system: str,
        source_data: np.ndarray,
        target_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Transfer knowledge from source to target system via analogy.

        Only proceeds if analogy is physically grounded.

        Args:
            source_system: Source system name
            target_system: Target system name
            source_data: Data from source system
            target_data: Data from target system

        Returns:
            Transferred knowledge with confidence estimates
        """
        # First validate analogy
        analogy = self.validate_analogy(source_system, target_system)

        if analogy.physical_grounding < self.min_grounding_score:
            return {
                'success': False,
                'reason': f"Analogy not sufficiently physically grounded (score: {analogy.physical_grounding:.2f})",
                'criteria': analogy.validity_criteria
            }

        # Transfer is allowed - proceed with knowledge transfer
        # Simple implementation: rescale source patterns to target

        transferred = {
            'success': True,
            'analogy': analogy,
            'confidence': analogy.confidence,
            'transferred_patterns': [],
            'warnings': analogy.validity_criteria
        }

        # Find patterns in source that can be transferred
        source_patterns = self._find_scale_invariant_patterns(source_data)

        # Rescale to target using scale ratio
        scale_ratio = self._estimate_scale_ratio(source_system, target_system)

        for pattern in source_patterns:
            transferred['transferred_patterns'].append({
                'pattern': pattern,
                'rescaled_pattern': pattern * scale_ratio,
                'confidence': analogy.confidence * 0.8  # Discount for transfer
            })

        return transferred

    def _find_scale_invariant_patterns(self, data: np.ndarray) -> np.ndarray:
        """Find patterns that are scale-invariant."""
        # Simple: use principal components as patterns
        if not SKLEARN_AVAILABLE:
            # Fallback: use simple statistics
            return np.mean(data, axis=0)

        from sklearn.decomposition import PCA

        pca = PCA(n_components=min(3, data.shape[1]))
        patterns = pca.components_

        return patterns

    def _estimate_scale_ratio(
        self,
        source_system: str,
        target_system: str
    ) -> float:
        """Estimate scale ratio between systems."""
        source = self.systems_db[source_system]
        target = self.systems_db[target_system]

        # Use first characteristic scale as reference
        if source.characteristic_scales and target.characteristic_scales:
            source_scale = list(source.characteristic_scales.values())[0]
            target_scale = list(target.characteristic_scales.values())[0]
            return target_scale / (source_scale + 1e-10)

        return 1.0


def demo_physics_grounded_analogy():
    """Demonstrate physics-grounded analogical reasoning."""
    print("=" * 60)
    print("Physics-Grounded Analogical Reasoning Module Demo")
    print("=" * 60)

    # Initialize
    analogy_engine = PhysicsGroundedAnalogy()

    # Test analogy between molecular cloud and protoplanetary disk
    print("\nValidating analogy: molecular_cloud -> protoplanetary_disk")
    analogy = analogy_engine.validate_analogy('molecular_cloud', 'protoplanetary_disk')

    print(f"\nSimilarity Score: {analogy.similarity_score:.2f}")
    print(f"Physical Grounding: {analogy.physical_grounding:.2f}")
    print(f"Confidence: {analogy.confidence:.2f}")
    print(f"\nExplanation: {analogy.explanation}")
    print(f"\nValidity Criteria:")
    for criterion in analogy.validity_criteria:
        print(f"  - {criterion}")

    # Find best analogies
    print("\n" + "=" * 60)
    print("Finding best analogies for accretion_disk:")
    print("=" * 60)

    best_analogies = analogy_engine.find_best_analogies('accretion_disk', top_k=3)

    for i, analogy in enumerate(best_analogies, 1):
        print(f"\n{i}. {analogy.source_system} -> {analogy.target_system}")
        print(f"   Physical Grounding: {analogy.physical_grounding:.2f}")
        print(f"   Confidence: {analogy.confidence:.2f}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    demo_physics_grounded_analogy()
