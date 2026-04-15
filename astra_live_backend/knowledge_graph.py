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
ASTRA Live — Dynamic Knowledge Graph
The semantic brain that integrates all astronomical knowledge.

Paradigm Shift: From static databases to living knowledge representation.

This Knowledge Graph:
- Represents entities (objects, concepts, theories, observations)
- Represents relationships (causes, predicts, contradicts, explains)
- Propagates belief updates across the network
- Identifies knowledge gaps and contradictions
- Discovers cross-domain analogies
- Tracks temporal evolution of knowledge
- Quantifies uncertainty at every level
"""
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import json
from datetime import datetime
import sqlite3
import os


class RelationType(Enum):
    """Types of relationships in the knowledge graph."""
    # Structural relationships
    IS_A = "is_a"                    # Taxonomy: "A black hole IS_A stellar remnant"
    PART_OF = "part_of"              # Mereology: "A planet IS_PART_OF a solar system"
    HAS_PROPERTY = "has_property"    # Attribution: "A galaxy HAS_PROPERTY spiral_arms"

    # Causal relationships
    CAUSES = "causes"                # Direct causation
    ENABLES = "enables"              # Enabling condition
    PREVENTS = "prevents"            # Prevention
    CORRELATES_WITH = "correlates_with"  # Statistical correlation

    # Theoretical relationships
    PREDICTS = "predicts"            # Theory predicts observation
    EXPLAINS = "explains"            # Theory explains phenomenon
    CONTRADICTS = "contradicts"      # Theories contradict
    SUPPORTS = "supports"            # Evidence supports theory
    REFUTES = "refutes"              # Evidence refutes theory

    # Temporal relationships
    PRECEDES = "precedes"            # Time ordering
    EVOLVES_INTO = "evolves_into"    # Evolutionary change

    # Similarity relationships
    ANALOGOUS_TO = "analogous_to"    # Cross-domain analogy
    SIMILAR_TO = "similar_to"        # Similarity within domain

    # Epistemic relationships
    CERTAIN = "certain"              # High confidence
    UNCERTAIN = "uncertain"          # Low confidence
    CONTROVERSIAL = "controversial"  # Disagreement in field


class EntityType(Enum):
    """Types of entities in the knowledge graph."""
    # Physical objects
    ASTROPHYSICAL_OBJECT = "astrophysical_object"  # Star, galaxy, black hole...
    OBSERVABLE = "observable"                      # Mass, luminosity, redshift...

    # Theoretical constructs
    THEORY = "theory"                              # GR, MOND, inflation...
    HYPOTHESIS = "hypothesis"                      # Specific claim
    PREDICTION = "prediction"                      # Testable prediction

    # Observational
    OBSERVATION = "observation"                    # Actual measurement
    MEASUREMENT = "measurement"                    # Data point

    # Conceptual
    CONCEPT = "concept"                            # Abstract concept
    PARAMETER = "parameter"                        # Physical parameter
    REGIME = "regime"                              # Physical regime (e.g., low_acceleration)


@dataclass
class Entity:
    """An entity in the knowledge graph."""
    id: str
    name: str
    entity_type: EntityType
    domain: str  # "astrophysics", "cosmology", "stellar_evolution", etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    confidence: float = 1.0  # Confidence in this entity's existence/definition
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Relation:
    """A relationship between two entities."""
    id: str
    source: str  # Entity ID
    target: str  # Entity ID
    relation_type: RelationType
    confidence: float  # 0-1
    evidence: List[str] = field(default_factory=list)  # Evidence IDs
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['relation_type'] = self.relation_type.value
        return d


@dataclass
class KnowledgeGap:
    """A gap in the knowledge graph."""
    gap_type: str  # "missing_entity", "missing_relation", "contradiction", "uncertainty"
    description: str
    entities_involved: List[str]
    priority: float  # 0-1, how important to fill?
    suggestions: List[str] = field(default_factory=list)
    estimated_difficulty: float = 0.5  # 0-1
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BeliefUpdate:
    """A belief propagation event."""
    trigger_entity: str
    trigger_type: str  # "new_entity", "new_relation", "confidence_change"
    affected_entities: List[str]
    confidence_deltas: Dict[str, float]  # entity_id -> delta
    propagation_depth: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DynamicKnowledgeGraph:
    """
    The semantic brain of ASTRA.

    Core capabilities:
    1. Entity and relation management with uncertainty quantification
    2. Belief propagation across the network
    3. Knowledge gap identification
    4. Contradiction detection
    5. Cross-domain analogy discovery
    6. Temporal evolution tracking
    7. Query and reasoning support
    """

    def __init__(self, db_path: str = "astra_knowledge.db"):
        # Graph structure
        self.graph = nx.MultiDiGraph()

        # Entity and relation indices
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}

        # Domain indices for efficient cross-domain queries
        self.domain_entities: Dict[str, Set[str]] = defaultdict(set)
        self.domain_relations: Dict[str, Set[str]] = defaultdict(set)

        # Knowledge gaps
        self.knowledge_gaps: List[KnowledgeGap] = []

        # Belief propagation history
        self.belief_updates: List[BeliefUpdate] = []

        # Counters for IDs
        self._entity_counter = 0
        self._relation_counter = 0

        # Persistent storage
        self.db_path = db_path
        self._init_db()
        self._load_from_db()

    def _init_db(self):
        """Initialize SQLite database for persistence."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                domain TEXT NOT NULL,
                properties TEXT,
                aliases TEXT,
                confidence REAL DEFAULT 1.0,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Relations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                evidence TEXT,
                metadata TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (source) REFERENCES entities(id),
                FOREIGN KEY (target) REFERENCES entities(id)
            )
        """)

        # Knowledge gaps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_gaps (
                gap_type TEXT,
                description TEXT,
                entities_involved TEXT,
                priority REAL,
                suggestions TEXT,
                estimated_difficulty REAL,
                discovered_at TEXT
            )
        """)

        # Belief updates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS belief_updates (
                trigger_entity TEXT,
                trigger_type TEXT,
                affected_entities TEXT,
                confidence_deltas TEXT,
                propagation_depth INTEGER,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _load_from_db(self):
        """Load entities and relations from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load entities
        cursor.execute("SELECT * FROM entities")
        for row in cursor.fetchall():
            entity = Entity(
                id=row[0],
                name=row[1],
                entity_type=EntityType(row[2]),
                domain=row[3],
                properties=json.loads(row[4]) if row[4] else {},
                aliases=json.loads(row[5]) if row[5] else [],
                confidence=row[6],
                created_at=row[7],
                updated_at=row[8]
            )
            self.entities[entity.id] = entity
            self.domain_entities[entity.domain].add(entity.id)
            self.graph.add_node(entity.id, **entity.to_dict())

            # Update counter
            entity_num = int(entity.id.split('_')[-1])
            if entity_num > self._entity_counter:
                self._entity_counter = entity_num

        # Load relations
        cursor.execute("SELECT * FROM relations")
        for row in cursor.fetchall():
            relation = Relation(
                id=row[0],
                source=row[1],
                target=row[2],
                relation_type=RelationType(row[3]),
                confidence=row[4],
                evidence=json.loads(row[5]) if row[5] else [],
                metadata=json.loads(row[6]) if row[6] else {},
                created_at=row[7],
                updated_at=row[8]
            )
            self.relations[relation.id] = relation
            self.domain_relations[
                self.entities[relation.source].domain
            ].add(relation.id)
            self.graph.add_edge(
                relation.source,
                relation.target,
                key=relation.id,
                **relation.to_dict()
            )

            # Update counter
            rel_num = int(relation.id.split('_')[-1])
            if rel_num > self._relation_counter:
                self._relation_counter = rel_num

        conn.close()

    def add_entity(self, name: str, entity_type: EntityType, domain: str,
                   properties: Dict[str, Any] = None,
                   aliases: List[str] = None,
                   confidence: float = 1.0) -> Entity:
        """Add a new entity to the knowledge graph."""
        self._entity_counter += 1
        entity_id = f"entity_{self._entity_counter}"

        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            domain=domain,
            properties=properties or {},
            aliases=aliases or [],
            confidence=confidence
        )

        self.entities[entity_id] = entity
        self.domain_entities[domain].add(entity_id)
        self.graph.add_node(entity_id, **entity.to_dict())

        # Persist to DB
        self._persist_entity(entity)

        return entity

    def add_relation(self, source_id: str, target_id: str,
                    relation_type: RelationType,
                    confidence: float = 1.0,
                    evidence: List[str] = None,
                    metadata: Dict[str, Any] = None) -> Optional[Relation]:
        """Add a new relation between entities."""
        if source_id not in self.entities or target_id not in self.entities:
            return None

        self._relation_counter += 1
        relation_id = f"rel_{self._relation_counter}"

        relation = Relation(
            id=relation_id,
            source=source_id,
            target=target_id,
            relation_type=relation_type,
            confidence=confidence,
            evidence=evidence or [],
            metadata=metadata or {}
        )

        self.relations[relation_id] = relation
        source_domain = self.entities[source_id].domain
        self.domain_relations[source_domain].add(relation_id)
        self.graph.add_edge(source_id, target_id, key=relation_id, **relation.to_dict())

        # Persist to DB
        self._persist_relation(relation)

        # Trigger belief propagation
        self._propagate_belief(relation)

        return relation

    def _propagate_belief(self, trigger_relation: Relation):
        """
        Propagate belief updates through the network.

        When a relation is added or updated, beliefs about related entities
        should be updated based on the new information.
        """
        affected_entities = set()
        confidence_deltas = {}

        # Get the source and target entities
        source = self.entities[trigger_relation.source]
        target = self.entities[trigger_relation.target]

        # Propagate confidence based on relation type
        if trigger_relation.relation_type in [RelationType.SUPPORTS, RelationType.CERTAIN]:
            # Positive evidence increases confidence
            delta = trigger_relation.confidence * 0.1
            confidence_deltas[target.id] = delta
            affected_entities.add(target.id)

        elif trigger_relation.relation_type in [RelationType.REFUTES, RelationType.CONTRADICTS]:
            # Negative evidence decreases confidence
            delta = -trigger_relation.confidence * 0.1
            confidence_deltas[target.id] = delta
            affected_entities.add(target.id)

        # Propagate to related entities (one-hop)
        for entity_id in list(affected_entities):
            # Get neighbors
            neighbors = list(self.graph.neighbors(entity_id))
            for neighbor_id in neighbors:
                if neighbor_id not in affected_entities:
                    # Attenuate propagation
                    attenuated_delta = confidence_deltas[entity_id] * 0.5
                    confidence_deltas[neighbor_id] = attenuated_delta
                    affected_entities.add(neighbor_id)

        # Apply updates
        for entity_id, delta in confidence_deltas.items():
            if entity_id in self.entities:
                old_confidence = self.entities[entity_id].confidence
                new_confidence = np.clip(old_confidence + delta, 0.0, 1.0)
                self.entities[entity_id].confidence = new_confidence
                self.entities[entity_id].updated_at = datetime.now().isoformat()

        # Record belief update
        if affected_entities:
            belief_update = BeliefUpdate(
                trigger_entity=trigger_relation.source,
                trigger_type="new_relation",
                affected_entities=list(affected_entities),
                confidence_deltas=confidence_deltas,
                propagation_depth=1
            )
            self.belief_updates.append(belief_update)

            # Persist
            self._persist_belief_update(belief_update)

    def find_knowledge_gaps(self) -> List[KnowledgeGap]:
        """
        Identify gaps in the knowledge graph.

        Returns:
            List of KnowledgeGap objects representing missing information
        """
        gaps = []

        # 1. Missing relations between related entities
        # Find entities in same domain that aren't connected
        for domain, entity_ids in self.domain_entities.items():
            entity_list = list(entity_ids)
            for i, entity_id in enumerate(entity_list):
                for other_id in entity_list[i+1:]:
                    # Check if entities are related
                    if not self.graph.has_edge(entity_id, other_id) and \
                       not self.graph.has_edge(other_id, entity_id):
                        # Check if they should be related (same type, similar properties)
                        entity1 = self.entities[entity_id]
                        entity2 = self.entities[other_id]

                        if self._should_be_related(entity1, entity2):
                            gaps.append(KnowledgeGap(
                                gap_type="missing_relation",
                                description=f"Potential relation between {entity1.name} and {entity2.name}",
                                entities_involved=[entity_id, other_id],
                                priority=0.5,
                                suggestions=[
                                    f"Investigate causal relationship between {entity1.name} and {entity2.name}",
                                    f"Check for correlation in observational data"
                                ]
                            ))

        # 2. Low confidence entities that need more evidence
        low_confidence_entities = [
            e for e in self.entities.values()
            if e.confidence < 0.5 and e.entity_type in [EntityType.THEORY, EntityType.HYPOTHESIS]
        ]

        for entity in low_confidence_entities[:5]:  # Top 5
            gaps.append(KnowledgeGap(
                gap_type="uncertainty",
                description=f"Low confidence in {entity.name} (confidence: {entity.confidence:.2f})",
                entities_involved=[entity.id],
                priority=1.0 - entity.confidence,
                suggestions=[
                    f"Search for observational evidence supporting {entity.name}",
                    f"Design critical experiment to test {entity.name}",
                    f"Check theoretical consistency with established physics"
                ]
            ))

        # 3. Contradictions in the graph
        contradictions = self._find_contradictions()
        for contradiction in contradictions:
            gaps.append(KnowledgeGap(
                gap_type="contradiction",
                description=contradiction['description'],
                entities_involved=contradiction['entities'],
                priority=1.0,  # Contradictions are high priority
                suggestions=[
                    "Investigate which claim is supported by stronger evidence",
                    "Check for context-dependent validity (different regimes?)",
                    "Look for theoretical framework that resolves contradiction"
                ]
            ))

        # 4. Missing entities in important domains
        for domain in ["cosmology", "stellar_evolution", "galaxy_formation"]:
            if domain not in self.domain_entities or len(self.domain_entities[domain]) < 10:
                gaps.append(KnowledgeGap(
                    gap_type="missing_entities",
                    description=f"Limited knowledge representation in {domain}",
                    entities_involved=[],
                    priority=0.7,
                    suggestions=[
                        f"Import key concepts from {domain}",
                        f"Add major theories and predictions in {domain}",
                        f"Incorporate recent discoveries from {domain}"
                    ]
                ))

        # Store gaps
        self.knowledge_gaps = gaps

        return gaps

    def _should_be_related(self, entity1: Entity, entity2: Entity) -> bool:
        """Check if two entities should have a relation."""
        # Same type entities might be related
        if entity1.entity_type == entity2.entity_type:
            if entity1.entity_type in [EntityType.THEORY, EntityType.HYPOTHESIS]:
                return True  # Theories often relate to other theories

        # Check for property overlap
        props1 = set(entity1.properties.keys())
        props2 = set(entity2.properties.keys())
        if props1 & props2:  # Overlapping properties
            return True

        return False

    def _find_contradictions(self) -> List[Dict]:
        """Find contradictions in the knowledge graph."""
        contradictions = []

        # Look for pairs of entities with CONTRADICTS relation
        for rel_id, relation in self.relations.items():
            if relation.relation_type == RelationType.CONTRADICTS:
                contradictions.append({
                    'description': f"{self.entities[relation.source].name} contradicts {self.entities[relation.target].name}",
                    'entities': [relation.source, relation.target]
                })

        # Look for entities with both SUPPORTS and REFUTES relations to same target
        for entity_id, entity in self.entities.items():
            # Get all relations where this entity is the source
            outgoing_rels = [
                rel for rel in self.relations.values()
                if rel.source == entity_id
            ]

            # Group by target
            by_target = defaultdict(list)
            for rel in outgoing_rels:
                by_target[rel.target].append(rel)

            # Check for conflicting relations to same target
            for target_id, rels in by_target.items():
                if len(rels) > 1:
                    relation_types = {rel.relation_type for rel in rels}
                    if RelationType.SUPPORTS in relation_types and \
                       RelationType.REFUTES in relation_types:
                        contradictions.append({
                            'description': f"{entity.name} both supports and refutes {self.entities[target_id].name}",
                            'entities': [entity_id, target_id]
                        })

        return contradictions

    def find_cross_domain_analogies(self) -> List[Dict]:
        """
        Discover analogies across different domains.

        Returns:
            List of analogy discoveries with similarity scores
        """
        analogies = []

        # Compare entities across domains
        domains = list(self.domain_entities.keys())

        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                # Get entities from both domains
                entities1 = [self.entities[eid] for eid in self.domain_entities[domain1]]
                entities2 = [self.entities[eid] for eid in self.domain_entities[domain2]]

                # Compare structural similarity
                for e1 in entities1:
                    for e2 in entities2:
                        similarity = self._compute_entity_similarity(e1, e2)

                        if similarity > 0.6:  # Threshold for analogy
                            # Find shared structural properties
                            shared_props = set(e1.properties.keys()) & set(e2.properties.keys())

                            analogies.append({
                                'domain1': domain1,
                                'domain2': domain2,
                                'entity1': e1.name,
                                'entity2': e2.name,
                                'similarity': similarity,
                                'shared_properties': list(shared_props),
                                'analogy_type': self._classify_analogy(e1, e2)
                            })

        # Sort by similarity
        analogies.sort(key=lambda x: x['similarity'], reverse=True)

        return analogies[:10]  # Top 10 analogies

    def _compute_entity_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """Compute similarity between two entities."""
        # Type similarity
        type_score = 1.0 if entity1.entity_type == entity2.entity_type else 0.5

        # Property overlap
        props1 = set(entity1.properties.keys())
        props2 = set(entity2.properties.keys())
        if props1 or props2:
            property_score = len(props1 & props2) / len(props1 | props2)
        else:
            property_score = 0.0

        # Domain similarity (different domains get lower score)
        domain_score = 1.0 if entity1.domain == entity2.domain else 0.7

        # Combine scores
        similarity = (type_score * 0.3 + property_score * 0.5 + domain_score * 0.2)

        return similarity

    def _classify_analogy(self, entity1: Entity, entity2: Entity) -> str:
        """Classify the type of analogy."""
        if entity1.entity_type == EntityType.THEORY and \
           entity2.entity_type == EntityType.THEORY:
            return "theoretical"
        elif entity1.domain != entity2.domain:
            return "cross_domain"
        else:
            return "structural"

    def query(self, query_type: str, **kwargs) -> List[Dict]:
        """
        Query the knowledge graph.

        Args:
            query_type: Type of query ("entity", "relation", "path", "neighbors")
            **kwargs: Query parameters

        Returns:
            List of matching entities/relations/paths
        """
        results = []

        if query_type == "entity":
            # Find entities matching criteria
            for entity in self.entities.values():
                match = True
                if 'name' in kwargs and kwargs['name'].lower() not in entity.name.lower():
                    match = False
                if 'entity_type' in kwargs and entity.entity_type != kwargs['entity_type']:
                    match = False
                if 'domain' in kwargs and entity.domain != kwargs['domain']:
                    match = False
                if 'min_confidence' in kwargs and entity.confidence < kwargs['min_confidence']:
                    match = False

                if match:
                    results.append(entity.to_dict())

        elif query_type == "relation":
            # Find relations matching criteria
            for relation in self.relations.values():
                match = True
                if 'relation_type' in kwargs and relation.relation_type != kwargs['relation_type']:
                    match = False
                if 'source' in kwargs and relation.source != kwargs['source']:
                    match = False
                if 'target' in kwargs and relation.target != kwargs['target']:
                    match = False
                if 'min_confidence' in kwargs and relation.confidence < kwargs['min_confidence']:
                    match = False

                if match:
                    results.append(relation.to_dict())

        elif query_type == "path":
            # Find path between entities
            if 'source' in kwargs and 'target' in kwargs:
                try:
                    path = nx.shortest_path(
                        self.graph,
                        source=kwargs['source'],
                        target=kwargs['target']
                    )
                    results.append({
                        'path': path,
                        'length': len(path) - 1,
                        'entities': [self.entities[nid].name for nid in path]
                    })
                except nx.NetworkXNoPath:
                    pass

        elif query_type == "neighbors":
            # Get neighbors of an entity
            if 'entity_id' in kwargs:
                entity_id = kwargs['entity_id']
                neighbors = list(self.graph.neighbors(entity_id))
                for neighbor_id in neighbors:
                    relation = self.graph.edges[entity_id, neighbor_id]
                    results.append({
                        'entity': self.entities[neighbor_id].to_dict(),
                        'relation': relation
                    })

        return results

    def get_statistics(self) -> Dict:
        """Get statistics about the knowledge graph."""
        return {
            'total_entities': len(self.entities),
            'total_relations': len(self.relations),
            'domains': {domain: len(entities) for domain, entities in self.domain_entities.items()},
            'entity_types': {
                etype.value: sum(1 for e in self.entities.values() if e.entity_type == etype)
                for etype in EntityType
            },
            'relation_types': {
                rtype.value: sum(1 for r in self.relations.values() if r.relation_type == rtype)
                for rtype in RelationType
            },
            'knowledge_gaps': len(self.knowledge_gaps),
            'belief_updates': len(self.belief_updates),
            'graph_density': nx.density(self.graph),
            'connected_components': nx.number_connected_components(self.graph.to_undirected())
        }

    def visualize_subgraph(self, entity_id: str, depth: int = 2) -> Dict:
        """
        Extract a subgraph around an entity for visualization.

        Args:
            entity_id: Central entity
            depth: How many hops to include

        Returns:
            Dictionary with nodes and edges for visualization
        """
        nodes = set()
        edges = set()

        # BFS to collect nodes and edges
        visited = set()
        queue = [(entity_id, 0)]

        while queue:
            current, dist = queue.pop(0)

            if current in visited or dist > depth:
                continue

            visited.add(current)
            nodes.add(current)

            # Get neighbors
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited and dist < depth:
                    queue.append((neighbor, dist + 1))

                # Add edge
                edge_key = tuple(sorted([current, neighbor]))
                edges.add(edge_key)

        # Build result
        result = {
            'nodes': [self.entities[nid].to_dict() for nid in nodes if nid in self.entities],
            'edges': []
        }

        for source, target in edges:
            # Get all relations between these nodes
            if self.graph.has_edge(source, target):
                for key, edge_data in self.graph[source][target].items():
                    result['edges'].append({
                        'source': source,
                        'target': target,
                        'relation_type': edge_data.get('relation_type'),
                        'confidence': edge_data.get('confidence', 1.0)
                    })

        return result

    # Persistence methods

    def _persist_entity(self, entity: Entity):
        """Save entity to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO entities
            (id, name, entity_type, domain, properties, aliases, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.id, entity.name, entity.entity_type.value, entity.domain,
            json.dumps(entity.properties), json.dumps(entity.aliases),
            entity.confidence, entity.created_at, entity.updated_at
        ))

        conn.commit()
        conn.close()

    def _persist_relation(self, relation: Relation):
        """Save relation to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO relations
            (id, source, target, relation_type, confidence, evidence, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            relation.id, relation.source, relation.target,
            relation.relation_type.value, relation.confidence,
            json.dumps(relation.evidence), json.dumps(relation.metadata),
            relation.created_at, relation.updated_at
        ))

        conn.commit()
        conn.close()

    def _persist_belief_update(self, belief_update: BeliefUpdate):
        """Save belief update to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO belief_updates
            (trigger_entity, trigger_type, affected_entities, confidence_deltas, propagation_depth, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            belief_update.trigger_entity, belief_update.trigger_type,
            json.dumps(belief_update.affected_entities),
            json.dumps(belief_update.confidence_deltas),
            belief_update.propagation_depth, belief_update.timestamp
        ))

        conn.commit()
        conn.close()


# Demonstration
if __name__ == "__main__":
    print("=" * 80)
    print("DYNAMIC KNOWLEDGE GRAPH - The Semantic Brain")
    print("=" * 80)

    # Initialize
    kg = DynamicKnowledgeGraph()

    print("\n1. CREATING INITIAL KNOWLEDGE BASE")
    print("-" * 80)

    # Add astrophysical entities
    black_hole = kg.add_entity(
        name="Black Hole",
        entity_type=EntityType.ASTROPHYSICAL_OBJECT,
        domain="astrophysics",
        properties={
            "mass_range": [3, 1e10],  # Solar masses
            "radius": "schwarzschild_radius",
            "key_feature": "event_horizon"
        },
        aliases=["BH", "gravitational singularity"]
    )

    galaxy = kg.add_entity(
        name="Galaxy",
        entity_type=EntityType.ASTROPHYSICAL_OBJECT,
        domain="astrophysics",
        properties={
            "mass_range": [1e8, 1e12],
            "components": ["stars", "gas", "dust", "dark_matter"]
        }
    )

    # Add theories
    general_relativity = kg.add_entity(
        name="General Relativity",
        entity_type=EntityType.THEORY,
        domain="gravitation",
        properties={
            "author": "Einstein",
            "year": 1915,
            "key_equation": "G_mu_nu = 8piG T_mu_nu"
        },
        confidence=0.99
    )

    mond = kg.add_entity(
        name="MOND",
        entity_type=EntityType.THEORY,
        domain="gravitation",
        properties={
            "author": "Milgrom",
            "year": 1983,
            "key_parameter": "a0"
        },
        confidence=0.6
    )

    # Add relations
    kg.add_relation(
        source_id=black_hole.id,
        target_id=galaxy.id,
        relation_type=RelationType.PART_OF,
        confidence=0.9,
        metadata={"context": "Supermassive black holes at galaxy centers"}
    )

    kg.add_relation(
        source_id=general_relativity.id,
        target_id=black_hole.id,
        relation_type=RelationType.PREDICTS,
        confidence=0.99,
        evidence=["einstein_1915", "observations"]
    )

    kg.add_relation(
        source_id=mond.id,
        target_id=galaxy.id,
        relation_type=RelationType.EXPLAINS,
        confidence=0.7,
        metadata={"regime": "low_acceleration"}
    )

    kg.add_relation(
        source_id=general_relativity.id,
        target_id=mond.id,
        relation_type=RelationType.CONTRADICTS,
        confidence=0.8,
        metadata={"reason": "Different predictions for low acceleration"}
    )

    print(f"Created {len(kg.entities)} entities")
    print(f"Created {len(kg.relations)} relations")

    # Query
    print("\n2. QUERIES")
    print("-" * 80)

    # Find all theories
    theories = kg.query(query_type="entity", entity_type=EntityType.THEORY)
    print(f"\nTheories in knowledge graph:")
    for theory in theories:
        print(f"  - {theory['name']} (confidence: {theory['confidence']:.2f})")

    # Find contradictions
    print("\n3. KNOWLEDGE GAPS")
    print("-" * 80)

    gaps = kg.find_knowledge_gaps()
    print(f"\nFound {len(gaps)} knowledge gaps:")
    for i, gap in enumerate(gaps[:5], 1):
        print(f"  {i}. {gap.gap_type}: {gap.description}")
        print(f"     Priority: {gap.priority:.2f}")

    # Find cross-domain analogies
    print("\n4. CROSS-DOMAIN ANALOGIES")
    print("-" * 80)

    analogies = kg.find_cross_domain_analogies()
    print(f"\nFound {len(analogies)} cross-domain analogies:")
    for analogy in analogies[:3]:
        print(f"  - {analogy['entity1']} ({analogy['domain1']}) ↔ {analogy['entity2']} ({analogy['domain2']})")
        print(f"    Similarity: {analogy['similarity']:.2f}")

    # Statistics
    print("\n5. STATISTICS")
    print("-" * 80)

    stats = kg.get_statistics()
    print(f"\nKnowledge Graph Statistics:")
    print(f"  Entities: {stats['total_entities']}")
    print(f"  Relations: {stats['total_relations']}")
    print(f"  Domains: {stats['domains']}")
    print(f"  Knowledge Gaps: {stats['knowledge_gaps']}")
    print(f"  Belief Updates: {stats['belief_updates']}")
    print(f"  Graph Density: {stats['graph_density']:.3f}")

    print("\n" + "=" * 80)
    print("DYNAMIC KNOWLEDGE GRAPH is operational!")
    print("=" * 80)
