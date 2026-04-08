"""
Astronomical Knowledge Graph

A specialized knowledge graph for representing astronomical objects,
physical relationships, and observational constraints.

Key features:
1. Nodes represent physical objects (stars, galaxies, black holes)
2. Edges represent physical relationships (orbits, lenses, radiates)
3. Includes hierarchical scales (stellar → galactic → cosmological)
4. Supports uncertainty and measurement errors
5. Integrates with physics constraints
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


# =============================================================================
# NODE TYPES
# =============================================================================

class AstroNodeType(Enum):
    """Astronomical object and concept types"""

    # Physical Objects
    STAR = "star"
    GALAXY = "galaxy"
    BLACK_HOLE = "black_hole"
    NEUTRON_STAR = "neutron_star"
    WHITE_DWARF = "white_dwarf"
    PLANET = "planet"
    ASTEROID = "asteroid"
    COMET = "comet"
    NEBULA = "nebula"
    CLUSTER = "cluster"  # Star cluster or galaxy cluster
    QUASAR = "quasar"
    DARK_MATTER_HALO = "dark_matter_halo"

    # Molecular Cloud / ISM Objects
    MOLECULAR_CLOUD = "molecular_cloud"
    GIANT_MOLECULAR_CLOUD = "giant_molecular_cloud"
    CLOUD_COMPLEX = "cloud_complex"
    FILAMENT = "filament"
    DENSE_CORE = "dense_core"
    PROTOSTAR = "protostar"
    HII_REGION = "hii_region"
    PHOTODISSOCIATION_REGION = "photodissociation_region"
    SUPERNOVA_REMNANT = "supernova_remnant"

    # ISM Phases
    WARM_NEUTRAL_MEDIUM = "warm_neutral_medium"
    COLD_NEUTRAL_MEDIUM = "cold_neutral_medium"
    WARM_IONIZED_MEDIUM = "warm_ionized_medium"
    HOT_IONIZED_MEDIUM = "hot_ionized_medium"

    # Dust Components
    DUST_GRAIN = "dust_grain"
    PAH = "pah"  # Polycyclic Aromatic Hydrocarbons
    ICE_MANTLE = "ice_mantle"
    SILICATE_GRAIN = "silicate_grain"
    CARBONACEOUS_GRAIN = "carbonaceous_grain"

    # Observational
    OBSERVATION = "observation"
    SPECTRUM = "spectrum"
    IMAGE = "image"
    LIGHT_CURVE = "light_curve"
    MEASUREMENT = "measurement"

    # Physical Properties
    PHYSICAL_PROPERTY = "physical_property"
    DERIVED_QUANTITY = "derived_quantity"

    # Theoretical
    MODEL = "model"
    HYPOTHESIS = "hypothesis"
    MECHANISM = "mechanism"
    CONSTRAINT = "constraint"

    # Spatial/Temporal
    POSITION = "position"
    EPOCH = "epoch"
    EVENT = "event"


class RelationType(Enum):
    """Types of relationships between astronomical entities"""

    # Physical relationships
    ORBITS = "orbits"
    HOSTS = "hosts"  # Galaxy hosts star, star hosts planet
    LENSES = "lenses"  # Gravitational lensing
    ACCRETES_FROM = "accretes_from"
    MERGES_WITH = "merges_with"
    EJECTS = "ejects"
    IRRADIATES = "irradiates"

    # Observational relationships
    OBSERVED_BY = "observed_by"
    MEASURED_AS = "measured_as"
    CONSTRAINS = "constrains"
    DERIVED_FROM = "derived_from"

    # Structural relationships
    CONTAINS = "contains"
    PART_OF = "part_of"
    ASSOCIATED_WITH = "associated_with"

    # Causal relationships
    CAUSES = "causes"
    PRODUCES = "produces"
    REQUIRES = "requires"
    EXCLUDES = "excludes"

    # Similarity/Analogy
    ANALOGOUS_TO = "analogous_to"
    SIMILAR_TO = "similar_to"
    SAME_CLASS_AS = "same_class_as"

    # Molecular Cloud / ISM relationships
    FRAGMENTS_INTO = "fragments_into"           # Cloud → cores/filaments
    COLLAPSES_TO = "collapses_to"              # Core → protostar
    SHIELDS = "shields"                         # Cloud shields interior from UV
    HEATS = "heats"                            # Radiation heats gas/dust
    COOLS = "cools"                            # Molecules cool gas
    SUPPORTS = "supports"                       # Turbulence/B-field supports against gravity
    DRIVES_TURBULENCE = "drives_turbulence"    # Feedback → turbulence
    OUTFLOWS_INTO = "outflows_into"            # Protostar → outflow → cloud
    PHOTOIONIZES = "photoionizes"              # O/B star → HII region
    PHOTODISSOCIATES = "photodissociates"      # UV → PDR
    TRACES = "traces"                          # Molecule traces physical conditions
    DEPLETES_ONTO = "depletes_onto"            # Gas species → dust grains
    EVAPORATES_FROM = "evaporates_from"        # Ice mantle → gas phase
    EMITS_AT = "emits_at"                      # Source → spectral line/wavelength
    ABSORBS_AT = "absorbs_at"                  # Medium → absorption feature


# =============================================================================
# NODE DEFINITIONS
# =============================================================================

@dataclass
class UncertainValue:
    """A value with associated uncertainty"""
    value: float
    uncertainty: float
    unit: str
    confidence: float = 0.68  # Default 1-sigma

    def __str__(self):
        return f"{self.value:.4g} ± {self.uncertainty:.2g} {self.unit}"

    def to_dict(self) -> Dict:
        return {
            'value': self.value,
            'uncertainty': self.uncertainty,
            'unit': self.unit,
            'confidence': self.confidence
        }


@dataclass
class AstroNode:
    """Base class for astronomical knowledge graph nodes"""
    node_id: str
    node_type: AstroNodeType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    uncertainties: Dict[str, UncertainValue] = field(default_factory=dict)
    provenance: str = ""  # Source of information
    created: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # Confidence in node's existence/validity

    def add_property(self, key: str, value: Any, uncertainty: float = None,
                     unit: str = "", confidence: float = 0.68):
        """Add a property with optional uncertainty"""
        self.properties[key] = value
        if uncertainty is not None:
            self.uncertainties[key] = UncertainValue(value, uncertainty, unit, confidence)

    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'name': self.name,
            'properties': self.properties,
            'uncertainties': {k: v.to_dict() for k, v in self.uncertainties.items()},
            'provenance': self.provenance,
            'confidence': self.confidence
        }


@dataclass
class AstroEdge:
    """Relationship between astronomical entities"""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)
    bidirectional: bool = False

    def to_dict(self) -> Dict:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type.value,
            'properties': self.properties,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'bidirectional': self.bidirectional
        }


# =============================================================================
# SPECIALIZED NODE TYPES
# =============================================================================

@dataclass
class StarNode(AstroNode):
    """Node representing a star"""
    spectral_type: str = ""
    luminosity_class: str = ""

    def __post_init__(self):
        self.node_type = AstroNodeType.STAR


@dataclass
class GalaxyNode(AstroNode):
    """Node representing a galaxy"""
    morphology: str = ""  # Hubble type
    redshift: float = 0.0

    def __post_init__(self):
        self.node_type = AstroNodeType.GALAXY


@dataclass
class ObservationNode(AstroNode):
    """Node representing an observation"""
    instrument: str = ""
    wavelength_range: Tuple[float, float] = (0, 0)  # nm
    observation_date: datetime = None
    exposure_time: float = 0.0  # seconds

    def __post_init__(self):
        self.node_type = AstroNodeType.OBSERVATION


@dataclass
class MechanismNode(AstroNode):
    """Node representing a physical mechanism (from V36 mechanism discovery)"""
    equation: str = ""
    functional_form: str = ""
    domain: str = ""
    is_novel: bool = False

    def __post_init__(self):
        self.node_type = AstroNodeType.MECHANISM


@dataclass
class HypothesisNode(AstroNode):
    """Node representing a scientific hypothesis"""
    parameters: Dict[str, Any] = field(default_factory=dict)
    predictions: List[str] = field(default_factory=list)
    falsifiable: bool = True
    status: str = "untested"  # untested, supported, falsified

    def __post_init__(self):
        self.node_type = AstroNodeType.HYPOTHESIS


# =============================================================================
# MOLECULAR CLOUD & ISM NODE TYPES
# =============================================================================

@dataclass
class MolecularCloudNode(AstroNode):
    """Node representing a molecular cloud or cloud structure"""
    cloud_type: str = "molecular_cloud"  # GMC, filament, core, etc.
    mass_msun: float = 0.0
    radius_pc: float = 0.0
    mean_column_density: float = 0.0  # N_H2 in cm⁻²
    mean_volume_density: float = 0.0  # n_H2 in cm⁻³
    velocity_dispersion: float = 0.0  # km/s
    virial_parameter: float = 0.0
    mach_number: float = 0.0
    T_kin: float = 15.0  # K
    T_dust: float = 15.0  # K
    distance_pc: float = 0.0
    galactic_l: float = 0.0  # deg
    galactic_b: float = 0.0  # deg

    def __post_init__(self):
        self.node_type = AstroNodeType.MOLECULAR_CLOUD


@dataclass
class FilamentNode(AstroNode):
    """Node representing a filamentary structure"""
    length_pc: float = 0.0
    width_pc: float = 0.0  # FWHM
    aspect_ratio: float = 0.0
    line_mass: float = 0.0  # M_sun/pc
    critical_line_mass: float = 0.0  # M_sun/pc
    is_supercritical: bool = False
    n_cores: int = 0
    parent_cloud: str = ""

    def __post_init__(self):
        self.node_type = AstroNodeType.FILAMENT


@dataclass
class DenseCoreNode(AstroNode):
    """Node representing a dense core"""
    core_type: str = "starless"  # starless, prestellar, protostellar
    mass_msun: float = 0.0
    radius_pc: float = 0.0
    peak_density: float = 0.0  # cm⁻³
    T_kin: float = 10.0  # K
    is_bound: bool = False
    is_collapsing: bool = False
    has_infall_signature: bool = False
    has_outflow: bool = False
    parent_filament: str = ""
    parent_cloud: str = ""

    def __post_init__(self):
        self.node_type = AstroNodeType.DENSE_CORE


@dataclass
class DustNode(AstroNode):
    """Node representing dust properties in a region"""
    T_dust: float = 20.0  # K
    T_dust_uncertainty: float = 2.0
    beta: float = 1.8  # Emissivity spectral index
    beta_uncertainty: float = 0.1
    kappa_850: float = 1.85  # Opacity at 850μm (cm²/g)
    gas_to_dust: float = 100.0
    A_V: float = 0.0  # Visual extinction
    dust_model: str = "MRN"  # MRN, WD01, Ossenkopf, etc.
    has_ice_mantles: bool = False
    has_grain_growth: bool = False

    def __post_init__(self):
        self.node_type = AstroNodeType.DUST_GRAIN


@dataclass
class MolecularLineNode(AstroNode):
    """Node representing a molecular line observation"""
    molecule: str = ""
    transition: str = ""  # e.g., "J=1-0", "(1,1)"
    rest_frequency_ghz: float = 0.0
    integrated_intensity: float = 0.0  # K km/s
    peak_temperature: float = 0.0  # K
    line_width: float = 0.0  # km/s
    v_lsr: float = 0.0  # km/s
    optical_depth: float = 0.0
    excitation_temp: float = 0.0  # K
    column_density: float = 0.0  # cm⁻²
    abundance: float = 0.0  # relative to H2

    def __post_init__(self):
        self.node_type = AstroNodeType.SPECTRUM


@dataclass
class ISMPhaseNode(AstroNode):
    """Node representing an ISM phase"""
    phase: str = "CNM"  # WNM, CNM, WIM, HIM
    temperature: float = 0.0  # K
    density: float = 0.0  # cm⁻³
    ionization_fraction: float = 0.0
    filling_factor: float = 0.0
    pressure: float = 0.0  # K cm⁻³

    def __post_init__(self):
        if self.phase == "WNM":
            self.node_type = AstroNodeType.WARM_NEUTRAL_MEDIUM
        elif self.phase == "CNM":
            self.node_type = AstroNodeType.COLD_NEUTRAL_MEDIUM
        elif self.phase == "WIM":
            self.node_type = AstroNodeType.WARM_IONIZED_MEDIUM
        else:
            self.node_type = AstroNodeType.HOT_IONIZED_MEDIUM


# =============================================================================
# ASTRONOMICAL KNOWLEDGE GRAPH
# =============================================================================

class AstronomicalKnowledgeGraph:
    """
    Knowledge graph for astronomical inference

    Key features:
    1. Physical constraint validation on edges
    2. Hierarchical scale organization
    3. Uncertainty propagation
    4. Provenance tracking
    5. Hypothesis management
    """

    def __init__(self, name: str = "astro_kg"):
        self.name = name
        self.nodes: Dict[str, AstroNode] = {}
        self.edges: List[AstroEdge] = []

        # Indices for fast lookup
        self.type_index: Dict[AstroNodeType, Set[str]] = {}
        self.name_index: Dict[str, str] = {}  # name -> node_id
        self.adjacency: Dict[str, List[str]] = {}  # node_id -> [connected_node_ids]

        # Hypothesis tracking
        self.hypotheses: Dict[str, HypothesisNode] = {}
        self.active_hypothesis: Optional[str] = None

        # Scale hierarchy
        self.scale_hierarchy = [
            'subatomic', 'atomic', 'molecular', 'planetary', 'stellar',
            'galactic', 'cluster', 'cosmological'
        ]

    # =========================================================================
    # NODE OPERATIONS
    # =========================================================================

    def add_node(self, node: AstroNode) -> str:
        """Add a node to the graph"""
        self.nodes[node.node_id] = node

        # Update type index
        if node.node_type not in self.type_index:
            self.type_index[node.node_type] = set()
        self.type_index[node.node_type].add(node.node_id)

        # Update name index
        self.name_index[node.name.lower()] = node.node_id

        # Initialize adjacency
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []

        return node.node_id

    def get_node(self, node_id: str) -> Optional[AstroNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)

    def find_by_name(self, name: str) -> Optional[AstroNode]:
        """Find a node by name"""
        node_id = self.name_index.get(name.lower())
        if node_id:
            return self.nodes.get(node_id)
        return None

    def find_by_type(self, node_type: AstroNodeType) -> List[AstroNode]:
        """Find all nodes of a given type"""
        node_ids = self.type_index.get(node_type, set())
        return [self.nodes[nid] for nid in node_ids]

    # =========================================================================
    # EDGE OPERATIONS
    # =========================================================================

    def add_edge(self, edge: AstroEdge) -> bool:
        """Add an edge to the graph"""
        # Validate nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            return False

        self.edges.append(edge)

        # Update adjacency
        self.adjacency[edge.source_id].append(edge.target_id)
        if edge.bidirectional:
            self.adjacency[edge.target_id].append(edge.source_id)

        return True

    def get_edges_from(self, node_id: str) -> List[AstroEdge]:
        """Get all edges originating from a node"""
        return [e for e in self.edges if e.source_id == node_id]

    def get_edges_to(self, node_id: str) -> List[AstroEdge]:
        """Get all edges pointing to a node"""
        return [e for e in self.edges if e.target_id == node_id]

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get all nodes connected to a given node"""
        return self.adjacency.get(node_id, [])

    # =========================================================================
    # CAUSAL CHAIN OPERATIONS
    # =========================================================================

    def find_causal_chain(self, source_id: str, target_id: str,
                          max_depth: int = 5) -> List[List[str]]:
        """
        Find causal chains connecting two nodes

        Uses BFS to find paths through CAUSES/PRODUCES edges.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        causal_relations = {RelationType.CAUSES, RelationType.PRODUCES, RelationType.REQUIRES}

        # BFS
        queue = [[source_id]]
        found_paths = []

        while queue:
            path = queue.pop(0)
            current = path[-1]

            if len(path) > max_depth:
                continue

            if current == target_id:
                found_paths.append(path)
                continue

            # Get causal edges from current node
            for edge in self.get_edges_from(current):
                if edge.relation_type in causal_relations:
                    if edge.target_id not in path:  # Avoid cycles
                        queue.append(path + [edge.target_id])

        return found_paths

    def get_causal_ancestors(self, node_id: str, max_depth: int = 10) -> Set[str]:
        """Get all causal ancestors of a node"""
        ancestors = set()
        causal_relations = {RelationType.CAUSES, RelationType.PRODUCES}

        to_visit = [node_id]
        depth = 0

        while to_visit and depth < max_depth:
            current = to_visit.pop(0)
            for edge in self.get_edges_to(current):
                if edge.relation_type in causal_relations:
                    if edge.source_id not in ancestors:
                        ancestors.add(edge.source_id)
                        to_visit.append(edge.source_id)
            depth += 1

        return ancestors

    # =========================================================================
    # HYPOTHESIS MANAGEMENT
    # =========================================================================

    def add_hypothesis(self, hypothesis: HypothesisNode) -> str:
        """Add a hypothesis to the graph"""
        self.add_node(hypothesis)
        self.hypotheses[hypothesis.node_id] = hypothesis
        return hypothesis.node_id

    def set_active_hypothesis(self, hypothesis_id: str):
        """Set the currently active hypothesis"""
        if hypothesis_id in self.hypotheses:
            self.active_hypothesis = hypothesis_id

    def evaluate_hypothesis(self, hypothesis_id: str,
                            observations: Dict) -> Dict:
        """
        Evaluate a hypothesis against observations

        Returns dict with support score, conflicts, and status.
        """
        hypothesis = self.hypotheses.get(hypothesis_id)
        if not hypothesis:
            return {'error': 'Hypothesis not found'}

        # Find all constraints that apply to this hypothesis
        constraint_edges = [
            e for e in self.get_edges_to(hypothesis_id)
            if e.relation_type == RelationType.CONSTRAINS
        ]

        supports = []
        conflicts = []

        for edge in constraint_edges:
            constraint_node = self.get_node(edge.source_id)
            if constraint_node:
                # Check if observation satisfies constraint
                # (Simplified - would need proper constraint checking)
                supports.append(constraint_node.name)

        # Calculate support score
        total_constraints = len(constraint_edges)
        support_score = len(supports) / max(1, total_constraints)

        return {
            'hypothesis_id': hypothesis_id,
            'support_score': support_score,
            'supports': supports,
            'conflicts': conflicts,
            'status': 'supported' if support_score > 0.7 else 'uncertain'
        }

    # =========================================================================
    # ANALOGY DETECTION
    # =========================================================================

    def find_analogies(self, node_id: str, threshold: float = 0.7) -> List[Dict]:
        """
        Find analogous nodes based on structural similarity

        Two nodes are analogous if they:
        1. Have similar connection patterns
        2. Have similar property distributions
        3. Play similar roles in their local subgraphs
        """
        source_node = self.get_node(node_id)
        if not source_node:
            return []

        analogies = []

        for other_id, other_node in self.nodes.items():
            if other_id == node_id:
                continue

            similarity = self._compute_structural_similarity(node_id, other_id)

            if similarity > threshold:
                analogies.append({
                    'node_id': other_id,
                    'name': other_node.name,
                    'similarity': similarity,
                    'shared_relations': self._get_shared_relation_types(node_id, other_id)
                })

        return sorted(analogies, key=lambda x: x['similarity'], reverse=True)

    def _compute_structural_similarity(self, id1: str, id2: str) -> float:
        """Compute structural similarity between two nodes"""
        # Get relation types for each node
        relations1 = set(e.relation_type for e in self.get_edges_from(id1))
        relations1.update(e.relation_type for e in self.get_edges_to(id1))

        relations2 = set(e.relation_type for e in self.get_edges_from(id2))
        relations2.update(e.relation_type for e in self.get_edges_to(id2))

        # Jaccard similarity
        if not relations1 and not relations2:
            return 0.0

        intersection = len(relations1 & relations2)
        union = len(relations1 | relations2)

        return intersection / union if union > 0 else 0.0

    def _get_shared_relation_types(self, id1: str, id2: str) -> List[str]:
        """Get relation types shared by two nodes"""
        relations1 = set(e.relation_type for e in self.get_edges_from(id1))
        relations1.update(e.relation_type for e in self.get_edges_to(id1))

        relations2 = set(e.relation_type for e in self.get_edges_from(id2))
        relations2.update(e.relation_type for e in self.get_edges_to(id2))

        return [r.value for r in relations1 & relations2]

    # =========================================================================
    # UNCERTAINTY PROPAGATION
    # =========================================================================

    def propagate_uncertainty(self, source_id: str, property_name: str) -> Dict[str, UncertainValue]:
        """
        Propagate uncertainty from a source node to derived quantities

        Uses edges marked as DERIVED_FROM to trace the uncertainty chain.
        """
        source_node = self.get_node(source_id)
        if not source_node or property_name not in source_node.uncertainties:
            return {}

        source_uncertainty = source_node.uncertainties[property_name]
        propagated = {source_id: source_uncertainty}

        # Find all nodes derived from this one
        derived_edges = [e for e in self.edges if e.relation_type == RelationType.DERIVED_FROM]

        for edge in derived_edges:
            if edge.target_id == source_id:
                derived_node = self.get_node(edge.source_id)
                if derived_node:
                    # Simplified propagation (in reality would use proper error propagation)
                    propagation_factor = edge.properties.get('propagation_factor', 1.0)
                    propagated_value = UncertainValue(
                        value=derived_node.properties.get(property_name, 0),
                        uncertainty=source_uncertainty.uncertainty * propagation_factor,
                        unit=source_uncertainty.unit,
                        confidence=source_uncertainty.confidence
                    )
                    propagated[edge.source_id] = propagated_value

        return propagated

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def save(self, filepath: str):
        """Save graph to JSON file"""
        data = {
            'name': self.name,
            'nodes': {nid: node.to_dict() for nid, node in self.nodes.items()},
            'edges': [edge.to_dict() for edge in self.edges]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, filepath: str):
        """Load graph from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.name = data['name']
        # Would need to reconstruct nodes and edges from dicts

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'nodes_by_type': {
                t.value: len(ids) for t, ids in self.type_index.items()
            },
            'edges_by_type': self._count_edges_by_type(),
            'hypotheses': len(self.hypotheses),
            'average_degree': self._average_degree()
        }

    def _count_edges_by_type(self) -> Dict[str, int]:
        counts = {}
        for edge in self.edges:
            t = edge.relation_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _average_degree(self) -> float:
        if not self.nodes:
            return 0.0
        total_degree = sum(len(neighbors) for neighbors in self.adjacency.values())
        return total_degree / len(self.nodes)

    # =========================================================================
    # MOLECULAR CLOUD ONTOLOGY
    # =========================================================================

    def build_ism_ontology(self):
        """
        Build the canonical ISM/molecular cloud ontology

        Creates standard nodes for ISM phases, molecular tracers,
        and canonical relationships between them.
        """
        # ISM Phases
        ism_phases = [
            ISMPhaseNode(node_id="ism_him", node_type=AstroNodeType.HOT_IONIZED_MEDIUM,
                        name="Hot Ionized Medium", phase="HIM",
                        temperature=1e6, density=0.003, ionization_fraction=1.0,
                        filling_factor=0.5, pressure=3000),
            ISMPhaseNode(node_id="ism_wim", node_type=AstroNodeType.WARM_IONIZED_MEDIUM,
                        name="Warm Ionized Medium", phase="WIM",
                        temperature=8000, density=0.1, ionization_fraction=0.9,
                        filling_factor=0.15, pressure=3000),
            ISMPhaseNode(node_id="ism_wnm", node_type=AstroNodeType.WARM_NEUTRAL_MEDIUM,
                        name="Warm Neutral Medium", phase="WNM",
                        temperature=8000, density=0.5, ionization_fraction=0.01,
                        filling_factor=0.3, pressure=3000),
            ISMPhaseNode(node_id="ism_cnm", node_type=AstroNodeType.COLD_NEUTRAL_MEDIUM,
                        name="Cold Neutral Medium", phase="CNM",
                        temperature=80, density=30, ionization_fraction=1e-4,
                        filling_factor=0.02, pressure=3000),
        ]

        for phase in ism_phases:
            self.add_node(phase)

        # Phase transition edges
        self.add_edge(AstroEdge(
            source_id="ism_wnm", target_id="ism_cnm",
            relation_type=RelationType.COOLS,
            properties={'mechanism': 'thermal_instability', 'timescale': '1 Myr'},
            confidence=0.9
        ))

        self.add_edge(AstroEdge(
            source_id="ism_cnm", target_id="ism_wnm",
            relation_type=RelationType.HEATS,
            properties={'mechanism': 'photoelectric_heating', 'timescale': '0.1 Myr'},
            confidence=0.9
        ))

    def add_molecular_cloud_hierarchy(self, cloud_name: str,
                                       cloud_data: Dict,
                                       filaments: List[Dict] = None,
                                       cores: List[Dict] = None):
        """
        Add a hierarchical molecular cloud structure to the graph

        Parameters
        ----------
        cloud_name : str
            Name of the cloud (e.g., "Taurus", "Orion A")
        cloud_data : dict
            Properties of the cloud
        filaments : list of dict
            Filament data within the cloud
        cores : list of dict
            Dense core data within filaments/cloud
        """
        # Create cloud node
        cloud_id = f"cloud_{cloud_name.lower().replace(' ', '_')}"
        cloud_node = MolecularCloudNode(
            node_id=cloud_id,
            node_type=AstroNodeType.MOLECULAR_CLOUD,
            name=cloud_name,
            cloud_type=cloud_data.get('type', 'molecular_cloud'),
            mass_msun=cloud_data.get('mass', 0),
            radius_pc=cloud_data.get('radius', 0),
            mean_column_density=cloud_data.get('N_H2', 0),
            mean_volume_density=cloud_data.get('n_H2', 0),
            velocity_dispersion=cloud_data.get('sigma_v', 0),
            virial_parameter=cloud_data.get('alpha_vir', 0),
            mach_number=cloud_data.get('mach', 0),
            T_kin=cloud_data.get('T_kin', 15),
            T_dust=cloud_data.get('T_dust', 15),
            distance_pc=cloud_data.get('distance', 0),
            galactic_l=cloud_data.get('l', 0),
            galactic_b=cloud_data.get('b', 0),
        )
        self.add_node(cloud_node)

        # Add filaments
        if filaments:
            for i, fil_data in enumerate(filaments):
                fil_name = fil_data.get('name', f"Filament_{i+1}")
                fil_id = f"{cloud_id}_fil_{i}"
                fil_node = FilamentNode(
                    node_id=fil_id,
                    node_type=AstroNodeType.FILAMENT,
                    name=f"{cloud_name} {fil_name}",
                    length_pc=fil_data.get('length', 0),
                    width_pc=fil_data.get('width', 0.1),
                    aspect_ratio=fil_data.get('aspect_ratio', 0),
                    line_mass=fil_data.get('line_mass', 0),
                    critical_line_mass=fil_data.get('M_line_crit', 16.6),  # M_sun/pc at 10K
                    is_supercritical=fil_data.get('is_supercritical', False),
                    n_cores=fil_data.get('n_cores', 0),
                    parent_cloud=cloud_id,
                )
                self.add_node(fil_node)

                # Cloud contains filament
                self.add_edge(AstroEdge(
                    source_id=cloud_id, target_id=fil_id,
                    relation_type=RelationType.CONTAINS,
                    confidence=1.0
                ))

                # Cloud fragments into filament
                self.add_edge(AstroEdge(
                    source_id=cloud_id, target_id=fil_id,
                    relation_type=RelationType.FRAGMENTS_INTO,
                    properties={'mechanism': 'turbulent_compression'},
                    confidence=0.8
                ))

        # Add cores
        if cores:
            for i, core_data in enumerate(cores):
                core_name = core_data.get('name', f"Core_{i+1}")
                core_id = f"{cloud_id}_core_{i}"
                parent_fil = core_data.get('parent_filament', '')

                core_node = DenseCoreNode(
                    node_id=core_id,
                    node_type=AstroNodeType.DENSE_CORE,
                    name=f"{cloud_name} {core_name}",
                    core_type=core_data.get('type', 'starless'),
                    mass_msun=core_data.get('mass', 0),
                    radius_pc=core_data.get('radius', 0),
                    peak_density=core_data.get('n_peak', 0),
                    T_kin=core_data.get('T_kin', 10),
                    is_bound=core_data.get('is_bound', False),
                    is_collapsing=core_data.get('is_collapsing', False),
                    has_infall_signature=core_data.get('has_infall', False),
                    has_outflow=core_data.get('has_outflow', False),
                    parent_filament=parent_fil,
                    parent_cloud=cloud_id,
                )
                self.add_node(core_node)

                # Filament contains core (if parent specified)
                if parent_fil and parent_fil in self.nodes:
                    self.add_edge(AstroEdge(
                        source_id=parent_fil, target_id=core_id,
                        relation_type=RelationType.CONTAINS,
                        confidence=1.0
                    ))
                    self.add_edge(AstroEdge(
                        source_id=parent_fil, target_id=core_id,
                        relation_type=RelationType.FRAGMENTS_INTO,
                        properties={'mechanism': 'gravitational_fragmentation'},
                        confidence=0.9
                    ))
                else:
                    # Direct cloud → core
                    self.add_edge(AstroEdge(
                        source_id=cloud_id, target_id=core_id,
                        relation_type=RelationType.CONTAINS,
                        confidence=1.0
                    ))

                # Collapsing core produces protostar
                if core_data.get('is_collapsing', False):
                    self.add_edge(AstroEdge(
                        source_id=core_id, target_id=core_id,
                        relation_type=RelationType.COLLAPSES_TO,
                        properties={'outcome': 'protostar', 'timescale': 't_ff'},
                        confidence=0.7
                    ))

        return cloud_id

    def add_molecular_tracer(self, cloud_id: str, molecule: str,
                              transition: str, observation: Dict) -> str:
        """
        Add a molecular line observation as a node linked to a cloud

        Parameters
        ----------
        cloud_id : str
            ID of the parent cloud node
        molecule : str
            Molecule name (e.g., "12CO", "NH3", "N2H+")
        transition : str
            Transition (e.g., "J=1-0", "(1,1)")
        observation : dict
            Observation data

        Returns
        -------
        str
            Node ID of the created molecular line node
        """
        line_id = f"{cloud_id}_{molecule}_{transition}".replace('=', '').replace('(', '').replace(')', '')

        line_node = MolecularLineNode(
            node_id=line_id,
            node_type=AstroNodeType.SPECTRUM,
            name=f"{molecule} {transition}",
            molecule=molecule,
            transition=transition,
            rest_frequency_ghz=observation.get('freq_ghz', 0),
            integrated_intensity=observation.get('W', 0),
            peak_temperature=observation.get('T_peak', 0),
            line_width=observation.get('delta_v', 0),
            v_lsr=observation.get('v_lsr', 0),
            optical_depth=observation.get('tau', 0),
            excitation_temp=observation.get('T_ex', 0),
            column_density=observation.get('N', 0),
            abundance=observation.get('X', 0),
        )
        self.add_node(line_node)

        # Cloud emits at this line
        self.add_edge(AstroEdge(
            source_id=cloud_id, target_id=line_id,
            relation_type=RelationType.EMITS_AT,
            confidence=1.0
        ))

        # Molecule traces certain physical conditions
        tracer_type = self._get_tracer_type(molecule)
        self.add_edge(AstroEdge(
            source_id=line_id, target_id=cloud_id,
            relation_type=RelationType.TRACES,
            properties={'traces': tracer_type, 'critical_density': self._get_n_crit(molecule)},
            confidence=0.9
        ))

        return line_id

    def _get_tracer_type(self, molecule: str) -> str:
        """Get what physical conditions a molecule traces"""
        tracers = {
            '12CO': 'bulk_gas',
            '13CO': 'moderate_density',
            'C18O': 'column_density',
            'HCN': 'dense_gas',
            'HCO+': 'dense_gas',
            'N2H+': 'cold_dense_gas',
            'NH3': 'temperature',
            'CS': 'dense_gas',
            'H2CO': 'temperature',
            'CH3OH': 'hot_cores',
            'SiO': 'shocks',
            'H2O': 'shocks',
        }
        return tracers.get(molecule, 'unknown')

    def _get_n_crit(self, molecule: str) -> float:
        """Get critical density for a molecule (cm⁻³)"""
        n_crit = {
            '12CO': 2e3,
            '13CO': 2e3,
            'C18O': 2e3,
            'HCN': 3e6,
            'HCO+': 2e5,
            'N2H+': 2e5,
            'NH3': 2e4,
            'CS': 5e5,
            'H2CO': 1e5,
        }
        return n_crit.get(molecule, 1e4)

    def get_cloud_subgraph(self, cloud_id: str) -> 'AstronomicalKnowledgeGraph':
        """
        Extract subgraph containing a cloud and all related nodes

        Returns a new KG containing only the cloud and its
        associated filaments, cores, and observations.
        """
        subgraph = AstronomicalKnowledgeGraph(name=f"subgraph_{cloud_id}")

        # Get cloud node
        cloud_node = self.get_node(cloud_id)
        if not cloud_node:
            return subgraph

        # BFS to find all connected nodes
        visited = set()
        to_visit = [cloud_id]

        while to_visit:
            current_id = to_visit.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            node = self.get_node(current_id)
            if node:
                subgraph.add_node(node)

            # Get neighbors
            for edge in self.get_edges_from(current_id):
                if edge.target_id not in visited:
                    to_visit.append(edge.target_id)
            for edge in self.get_edges_to(current_id):
                if edge.source_id not in visited:
                    to_visit.append(edge.source_id)

        # Add relevant edges
        for edge in self.edges:
            if edge.source_id in visited and edge.target_id in visited:
                subgraph.add_edge(edge)

        return subgraph



def predict_next_in_sequence(sequence: List[Any],
                            method: str = 'autoregressive') -> Dict[str, Any]:
    """
    Predict the next element in a sequence.

    Args:
        sequence: Observed sequence
        method: Prediction method ('autoregressive', 'markov', 'fft')

    Returns:
        Dictionary with prediction and confidence
    """
    import numpy as np

    if len(sequence) < 2:
        return {'prediction': None, 'confidence': 0.0}

    if method == 'autoregressive':
        # Fit AR(1) model: x_t = c + phi * x_{t-1}
        x = np.array(sequence)
        x_lag = x[:-1]
        x_current = x[1:]

        # Linear regression
        A = np.vstack([x_lag, np.ones(len(x_lag))]).T
        phi, c = np.linalg.lstsq(A, x_current, rcond=None)[0]

        # Predict next
        if len(x) > 0:
            prediction = c + phi * x[-1]

            # Estimate confidence from residuals
            residuals = x_current - (c + phi * x_lag)
            std = np.std(residuals)
            confidence = 1.0 / (1.0 + std)

            return {
                'prediction': float(prediction),
                'confidence': float(confidence),
                'method': 'autoregressive'
            }

    elif method == 'markov':
        # Simple Markov chain
        transitions = {}
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_val = sequence[i + 1]
            if current not in transitions:
                transitions[current] = {}
            if next_val not in transitions[current]:
                transitions[current][next_val] = 0
            transitions[current][next_val] += 1

        # Predict from last state
        last = sequence[-1]
        if last in transitions:
            total = sum(transitions[last].values())
            most_likely = max(transitions[last].items(), key=lambda x: x[1])
            prediction = most_likely[0]
            confidence = most_likely[1] / total

            return {
                'prediction': prediction,
                'confidence': float(confidence),
                'method': 'markov'
            }

    return {'prediction': None, 'confidence': 0.0}



def bootstrap_uncertainty(data: np.ndarray,
                         estimator_func: callable,
                         n_bootstrap: int = 1000,
                         ci_level: float = 0.95) -> Dict[str, Any]:
    """
    Estimate uncertainty using bootstrap resampling.

    Args:
        data: Input data
        estimator_func: Function that computes estimate from data
        n_bootstrap: Number of bootstrap samples
        ci_level: Confidence interval level

    Returns:
        Dictionary with estimate and confidence interval
    """
    import numpy as np

    n = len(data)
    estimates = []

    for _ in range(n_bootstrap):
        # Bootstrap sampling
        sample = np.random.choice(data, size=len(data), replace=True)
        estimate = estimator_func(sample)
        estimates.append(estimate)

    # Compute confidence interval
    alpha = 1 - ci_level
    lower = np.percentile(estimates, 100 * alpha / 2)
    upper = np.percentile(estimates, 100 * (1 - alpha / 2))
    point_estimate = estimator_func(data)

    return {
        'estimate': point_estimate,
        'ci_lower': lower,
        'ci_upper': upper,
        'ci_level': ci_level
    }
