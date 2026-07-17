"""
Astronomical knowledge graph for ASTRO.

A populated graph of astrophysical entities (species, ISM phases, processes,
quantities, mechanisms) linked by physically-meaningful relations, with each
edge carrying the quantitative condition under which it holds. Intended as a
domain-intelligence substrate for the discovery system: queries return valid
physical chains (e.g. molecular_cloud --gravitational_collapse--> star).

The seed knowledge is standard PhD-level ISM/star-formation physics
(Hollenbach & Tielens 1999; Draine "Physics of the ISM and IGM"; McKee &
Ostriker 2007; Stahler & Palla "The Formation of Stars").
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum


class AstroNodeType(Enum):
    SOURCE = "source"
    SPECIES = "species"
    PHASE = "phase"
    PROCESS = "process"
    QUANTITY = "quantity"
    MECHANISM = "mechanism"
    OBSERVABLE = "observable"
    REGION = "region"


class RelationType(Enum):
    TRACES = "traces"               # species traces a phase/quantity
    COMPOSED_OF = "composed_of"
    TRANSFORMS_INTO = "transforms_into"
    OBSERVED_IN = "observed_in"
    DEPENDS_ON = "depends_on"
    FORMS_VIA = "forms_via"         # phase/object forms via a process
    HEATED_BY = "heated_by"
    COOLS_TO = "cools_to"
    IONIZES = "ionizes"
    SHIELDS = "shields"
    DRIVES = "drives"               # process drives another
    FEEDS = "feeds"                 # mechanism feeds back


@dataclass
class AstroNode:
    name: str
    node_type: AstroNodeType
    metadata: Dict = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.node_type))


@dataclass
class AstroEdge:
    source: str
    target: str
    relation: RelationType
    condition: str = ""             # quantitative condition under which it holds


@dataclass
class MechanismNode(AstroNode):
    """A physical mechanism (e.g. Jeans instability, photoionisation)."""
    def __post_init__(self):
        if self.node_type != AstroNodeType.MECHANISM:
            self.node_type = AstroNodeType.MECHANISM


@dataclass
class HypothesisNode(AstroNode):
    """A scientific hypothesis (used by the discovery system)."""
    hypothesis_id: str = ""
    status: str = "proposed"        # proposed | testing | supported | rejected
    def __post_init__(self):
        if self.node_type != AstroNodeType.HYPOTHESIS:
            self.node_type = AstroNodeType.HYPOTHESIS


class AstronomicalKnowledgeGraph:
    """Directed knowledge graph with name-keyed nodes and adjacency queries."""

    def __init__(self):
        self.nodes: Dict[str, AstroNode] = {}
        self.edges: List[AstroEdge] = []
        self._adj: Dict[str, List[AstroEdge]] = {}

    # -- construction -------------------------------------------------------
    def add_node(self, node: AstroNode) -> AstroNode:
        self.nodes[node.name] = node
        self._adj.setdefault(node.name, [])
        return node

    def add_edge(self, source: str, target: str, relation: RelationType,
                 condition: str = "") -> AstroEdge:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError(f"unknown node(s): {source}, {target}")
        e = AstroEdge(source, target, relation, condition)
        self.edges.append(e)
        self._adj[source].append(e)
        return e

    # -- queries ------------------------------------------------------------
    def neighbors(self, name: str, relation: RelationType = None) -> List[str]:
        out = []
        for e in self._adj.get(name, []):
            if relation is None or e.relation == relation:
                out.append(e.target)
        return out

    def relation_between(self, a: str, b: str) -> List[AstroEdge]:
        return [e for e in self._adj.get(a, []) if e.target == b]

    def shortest_path(self, start: str, goal: str) -> Optional[List[str]]:
        """BFS over directed edges."""
        if start == goal:
            return [start]
        seen = {start}
        queue = [[start]]
        while queue:
            path = queue.pop(0)
            for nxt in self.neighbors(path[-1]):
                if nxt in seen:
                    continue
                if nxt == goal:
                    return path + [nxt]
                seen.add(nxt)
                queue.append(path + [nxt])
        return None

    # -- population ---------------------------------------------------------
    @classmethod
    def seed_standard_astronomy(cls) -> "AstronomicalKnowledgeGraph":
        """Populate with standard ISM / star-formation knowledge."""
        g = cls()

        def N(name, ntype, **md):
            return g.add_node(AstroNode(name, ntype, md))

        # species
        N('H', AstroNodeType.SPECIES); N('H2', AstroNodeType.SPECIES)
        N('H+', AstroNodeType.SPECIES); N('C+', AstroNodeType.SPECIES)
        N('C', AstroNodeType.SPECIES); N('CO', AstroNodeType.SPECIES)
        N('dust', AstroNodeType.SPECIES); N('O_star', AstroNodeType.SOURCE)
        # phases / regions
        N('CNM', AstroNodeType.PHASE); N('WNM', AstroNodeType.PHASE)
        N('molecular_cloud', AstroNodeType.PHASE)
        N('HII_region', AstroNodeType.PHASE); N('PDR', AstroNodeType.PHASE)
        N('star', AstroNodeType.SOURCE); N('protostar', AstroNodeType.SOURCE)
        # processes / mechanisms
        N('gravitational_collapse', AstroNodeType.MECHANISM)
        N('photoionisation', AstroNodeType.MECHANISM)
        N('photodissociation', AstroNodeType.MECHANISM)
        N('self_shielding', AstroNodeType.MECHANISM)
        N('Jeans_instability', AstroNodeType.MECHANISM)
        N('stellar_feedback', AstroNodeType.PROCESS)
        N('supernova', AstroNodeType.PROCESS)
        # quantities / observables
        N('visual_extinction_Av', AstroNodeType.QUANTITY)
        N('CO_line_emission', AstroNodeType.OBSERVABLE)
        N('dust_continuum', AstroNodeType.OBSERVABLE)
        N('Ha_emission', AstroNodeType.OBSERVABLE)

        # relations (with quantitative conditions where relevant)
        R = RelationType
        g.add_edge('H2', 'H', R.COMPOSED_OF, '2 H atoms')
        g.add_edge('CO', 'molecular_cloud', R.TRACES, 'X_CO ~ 1e-4 (CO/H2); valid A_V > ~1.5 mag')
        g.add_edge('CO', 'CO_line_emission', R.OBSERVED_IN, '(sub)mm rotational lines')
        g.add_edge('dust', 'dust_continuum', R.OBSERVED_IN, 'FIR/submm modified blackbody')
        g.add_edge('dust', 'H2', R.SHIELDS, 'dust attenuation enables H2 self-shielding; A_V > ~0.1-0.5')
        g.add_edge('visual_extinction_Av', 'CO', R.TRANSFORMS_INTO,
                   'C+ -> C -> CO as A_V rises; CO abundant for A_V > ~1.5')
        g.add_edge('visual_extinction_Av', 'H2', R.TRANSFORMS_INTO,
                   'H -> H2 transition at A_V > ~0.1-0.3')
        g.add_edge('C+', 'C', R.TRANSFORMS_INTO, 'recombination at A_V ~ 0.5')
        g.add_edge('C', 'CO', R.TRANSFORMS_INTO, 'CO formation at A_V ~ 1.5')
        g.add_edge('O_star', 'H', R.IONIZES, 'ionising photons Q > ~1e45 s^-1')
        g.add_edge('photoionisation', 'HII_region', R.FORMS_VIA, 'Strmgren sphere; T_e ~ 1e4 K')
        g.add_edge('HII_region', 'Ha_emission', R.OBSERVED_IN, 'Halpha recombination')
        g.add_edge('molecular_cloud', 'protostar', R.FORMS_VIA,
                   'Jeans instability; M > M_J')
        g.add_edge('Jeans_instability', 'gravitational_collapse', R.DRIVES,
                   'M_J = (pi^(5/2)/6) c_s^3 / (G^(3/2) rho^(1/2))')
        g.add_edge('gravitational_collapse', 'protostar', R.FORMS_VIA, 'core collapse + accretion')
        g.add_edge('protostar', 'star', R.TRANSFORMS_INTO, 'main-sequence ignition')
        g.add_edge('star', 'stellar_feedback', R.DRIVES, 'winds + radiation')
        g.add_edge('star', 'supernova', R.TRANSFORMS_INTO, 'M_init > 8 Msun')
        g.add_edge('supernova', 'molecular_cloud', R.FEEDS,
                   'triggers/compresses gas; injects 1e51 erg')
        g.add_edge('PDR', 'C+', R.OBSERVED_IN, '[CII] 158 um dominant coolant at A_V < 1')
        g.add_edge('WNM', 'CNM', R.TRANSFORMS_INTO, 'thermal instability; T ~ 1e4 -> ~100 K')
        g.add_edge('CNM', 'molecular_cloud', R.TRANSFORMS_INTO, 'further cooling + shielding')

        return g


__all__ = [
    'AstroNodeType', 'RelationType', 'AstroNode', 'AstroEdge',
    'MechanismNode', 'HypothesisNode', 'AstronomicalKnowledgeGraph',
]
