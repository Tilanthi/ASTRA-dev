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
Stigmergic Memory for STAR-Learn

Implements biological field-based memory using MORK ontology parameters:
- TAU (τ): Aggregation pheromone (attracts to successful paths)
- ETA (η): Repulsion pheromone (avoids failed paths)
- C_K: Concentration parameter (memory persistence)

This enables:
1. Pheromone trails for solution path reinforcement
2. Biological field dynamics for collective intelligence
3. Swarm coordination without direct communication
4. Long-term knowledge persistence
5. Emergent behavior from simple rules
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import hashlib


class FieldType(Enum):
    """Types of biological fields"""
    AGGREGATION = "aggregation"  # TAU: attracts to success
    REPULSION = "repulsion"  # ETA: avoids failure
    MEMORY = "memory"  # C_K: persistence


@dataclass
class BiologicalFieldState:
    """State of biological fields at a location"""
    tau: float = 0.0  # Aggregation pheromone
    eta: float = 0.0  # Repulsion pheromone
    c_k: float = 0.5  # Concentration/memory

    # Location/Context
    location: str = ""
    domain: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    # Timestamp
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tau': self.tau,
            'eta': self.eta,
            'c_k': self.c_k,
            'location': self.location,
            'domain': self.domain,
            'context': self.context,
            'last_updated': self.last_updated
        }


@dataclass
class PheromoneTrail:
    """A pheromone trail deposited by agents"""
    trail_id: str
    location: str
    strength: float
    field_type: FieldType

    # Path information
    path_signature: str = ""
    domain: str = ""

    # Agent information
    agent_id: str = ""
    discovery_reward: float = 0.0

    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    decay_rate: float = 0.95

    def age(self, current_time: Optional[datetime] = None) -> float:
        """Calculate age of trail in seconds."""
        trail_time = datetime.fromisoformat(self.timestamp)
        ref_time = current_time or datetime.now()
        return (ref_time - trail_time).total_seconds()

    def decayed_strength(self, current_time: Optional[datetime] = None) -> float:
        """Calculate strength after decay."""
        age_hours = self.age(current_time) / 3600
        decay_factor = self.decay_rate ** age_hours
        return self.strength * decay_factor


@dataclass
class DiscoverySignature:
    """Signature of a discovery for similarity matching"""
    signature_id: str
    content_hash: str
    domain: str
    key_concepts: List[str]

    # Success metrics
    reward: float = 0.0
    novelty: float = 0.0
    confidence: float = 0.0

    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_discovery(cls, discovery: Dict[str, Any]) -> 'DiscoverySignature':
        """Create signature from discovery data."""
        content = discovery.get('content', '')
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Extract key concepts (simple word extraction)
        words = content.lower().split()
        key_concepts = [w for w in words if len(w) > 5 and w.isalpha()][:10]

        return cls(
            signature_id=f"sig_{content_hash}",
            content_hash=content_hash,
            domain=discovery.get('domain', 'unknown'),
            key_concepts=key_concepts,
            reward=discovery.get('reward', 0.0),
            novelty=discovery.get('novelty', 0.0),
            confidence=discovery.get('confidence', 0.0)
        )


@dataclass
class StigmergicConfig:
    """Configuration for stigmergic memory"""
    # Field dynamics
    tau_decay_rate: float = 0.95  # Aggregation pheromone decay
    eta_decay_rate: float = 0.90  # Repulsion pheromone decay
    c_k_learning_rate: float = 0.1  # Memory formation rate

    # Deposit parameters
    max_pheromone_strength: float = 10.0
    min_pheromone_strength: float = 0.01

    # Spatial parameters
    neighborhood_radius: float = 0.2  # Influence radius
    diffusion_rate: float = 0.1  # Pheromone diffusion

    # Memory limits
    max_trails: int = 10000
    max_discoveries: int = 5000
    max_field_locations: int = 1000

    # Swarm coordination
    enable_swarm_coordination: bool = True
    n_agent_types: int = 5  # Explorer, Falsifier, Analogist, etc.

    # Persistence
    persistence_interval: int = 100  # Save every N updates
    persistence_path: str = "stigmergic_memory.json"


class StigmergicMemory:
    """
    Stigmergic Memory using biological field dynamics.

    Implements MORK-inspired biological fields for:
    1. Pheromone-based path reinforcement
    2. Swarm coordination without direct communication
    3. Long-term knowledge persistence
    4. Emergent collective intelligence
    """

    def __init__(self, config: Optional[StigmergicConfig] = None):
        """
        Initialize stigmergic memory.

        Args:
            config: Stigmergic configuration
        """
        self.config = config or StigmergicConfig()

        # Biological fields (location -> field state)
        self.fields: Dict[str, BiologicalFieldState] = {}

        # Pheromone trails
        self.trails: List[PheromoneTrail] = []

        # Discovery signatures
        self.discoveries: List[DiscoverySignature] = []

        # Statistics
        self.total_deposits = 0
        self.total_discoveries = 0
        self.last_update_time = datetime.now()

    def deposit_pheromone(
        self,
        trail: Dict[str, Any]
    ) -> str:
        """
        Deposit a pheromone trail.

        Args:
            trail: Trail data with location, strength, domain, etc.

        Returns:
            Trail ID
        """
        trail_id = f"trail_{hash(str(trail)) & 0xffffffff:08x}"

        pheromone = PheromoneTrail(
            trail_id=trail_id,
            location=trail.get('location', 'unknown'),
            strength=trail.get('strength', 1.0),
            field_type=FieldType(trail.get('field_type', 'aggregation')),
            path_signature=trail.get('path', ''),
            domain=trail.get('domain', 'unknown'),
            agent_id=trail.get('agent_id', ''),
            discovery_reward=trail.get('reward', 0.0)
        )

        self.trails.append(pheromone)
        self.total_deposits += 1

        # Update biological field at location
        self._update_field_from_trail(pheromone)

        # Limit trail count
        if len(self.trails) > self.config.max_trails:
            # Remove oldest/weakest trails
            self.trails = sorted(
                self.trails,
                key=lambda t: t.decayed_strength(),
                reverse=True
            )[:self.config.max_trails]

        return trail_id

    def _update_field_from_trail(self, trail: PheromoneTrail):
        """Update biological field based on pheromone trail."""
        location = trail.location

        if location not in self.fields:
            self.fields[location] = BiologicalFieldState(
                location=location,
                domain=trail.domain
            )

        field = self.fields[location]

        # Update field values based on trail type
        if trail.field_type == FieldType.AGGREGATION:
            # Strengthen aggregation (success)
            field.tau += trail.strength * self.config.c_k_learning_rate
        elif trail.field_type == FieldType.REPULSION:
            # Strengthen repulsion (failure)
            field.eta += trail.strength * self.config.c_k_learning_rate

        # Update memory concentration based on reward
        if trail.discovery_reward > 0:
            field.c_k += trail.discovery_reward * self.config.c_k_learning_rate

        # Clamp values
        field.tau = min(field.tau, self.config.max_pheromone_strength)
        field.eta = min(field.eta, self.config.max_pheromone_strength)
        field.c_k = min(max(field.c_k, 0.0), 1.0)

        field.last_updated = datetime.now().isoformat()

        # Limit field locations
        if len(self.fields) > self.config.max_field_locations:
            # Remove weakest fields
            self.fields = dict(
                sorted(
                    self.fields.items(),
                    key=lambda x: x[1].c_k,
                    reverse=True
                )[:self.config.max_field_locations]
            )

    def update_biological_field(
        self,
        update: Dict[str, float]
    ) -> bool:
        """
        Update biological field parameters.

        Args:
            update: Dict with tau, eta, c_k updates

        Returns:
            Success status
        """
        # For global updates, update all fields
        # For location-specific, would need location parameter

        for field in self.fields.values():
            if 'TAU' in update:
                field.tau += update['TAU'] * self.config.c_k_learning_rate
            if 'ETA' in update:
                field.eta += update['ETA'] * self.config.c_k_learning_rate
            if 'C_K' in update:
                field.c_k += update['C_K'] * self.config.c_k_learning_rate

            # Clamp values
            field.tau = min(max(field.tau, 0), self.config.max_pheromone_strength)
            field.eta = min(max(field.eta, 0), self.config.max_pheromone_strength)
            field.c_k = min(max(field.c_k, 0), 1.0)

        return True

    def get_field_at(self, location: str) -> Optional[BiologicalFieldState]:
        """
        Get biological field state at a location.

        Args:
            location: Location identifier

        Returns:
            Field state or None if not found
        """
        # Direct lookup
        if location in self.fields:
            return self.fields[location]

        # Neighborhood search
        neighborhood = self._get_neighborhood(location)
        if neighborhood:
            # Return aggregated field
            return self._aggregate_neighborhood_fields(neighborhood)

        return None

    def _get_neighborhood(self, location: str) -> List[str]:
        """Get locations within neighborhood radius."""
        # Simple string similarity for neighborhood
        # In production, would use actual spatial coordinates
        neighborhood = []

        for other_location in self.fields.keys():
            similarity = self._location_similarity(location, other_location)
            if similarity >= (1 - self.config.neighborhood_radius):
                neighborhood.append(other_location)

        return neighborhood

    def _location_similarity(self, loc1: str, loc2: str) -> float:
        """Calculate similarity between locations."""
        # Simple similarity: same domain = similar
        if loc1 == loc2:
            return 1.0

        # Extract domains
        domain1 = loc1.split('_')[0] if '_' in loc1 else loc1
        domain2 = loc2.split('_')[0] if '_' in loc2 else loc2

        if domain1 == domain2:
            return 0.7  # Same domain = somewhat similar

        return 0.0

    def _aggregate_neighborhood_fields(
        self,
        neighborhood: List[str]
    ) -> BiologicalFieldState:
        """Aggregate fields in neighborhood."""
        if not neighborhood:
            return BiologicalFieldState()

        # Average field values
        fields = [self.fields[loc] for loc in neighborhood if loc in self.fields]

        if not fields:
            return BiologicalFieldState()

        return BiologicalFieldState(
            tau=np.mean([f.tau for f in fields]),
            eta=np.mean([f.eta for f in fields]),
            c_k=np.mean([f.c_k for f in fields]),
            location=f"neighborhood_of_{neighborhood[0]}",
            domain=fields[0].domain
        )

    def add_discovery(self, discovery: Dict[str, Any]) -> str:
        """
        Add a discovery signature to memory.

        Args:
            discovery: Discovery data

        Returns:
            Signature ID
        """
        signature = DiscoverySignature.from_discovery(discovery)
        self.discoveries.append(signature)
        self.total_discoveries += 1

        # Limit discovery count
        if len(self.discoveries) > self.config.max_discoveries:
            # Keep best discoveries
            self.discoveries = sorted(
                self.discoveries,
                key=lambda d: d.reward,
                reverse=True
            )[:self.config.max_discoveries]

        return signature.signature_id

    def find_similar_discoveries(
        self,
        query: str,
        domain: Optional[str] = None,
        n_results: int = 10
    ) -> List[DiscoverySignature]:
        """
        Find discoveries similar to a query.

        Args:
            query: Query text
            domain: Optional domain filter
            n_results: Number of results to return

        Returns:
            List of similar discovery signatures
        """
        # Hash query
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]

        # Calculate similarity to each discovery
        similarities = []
        for discovery in self.discoveries:
            if domain and discovery.domain != domain:
                continue

            # Simple hash-based similarity
            similarity = self._hash_similarity(query_hash, discovery.content_hash)

            # Check concept overlap
            query_words = set(query.lower().split())
            discovery_concepts = set(discovery.key_concepts)
            concept_overlap = len(query_words & discovery_concepts) / max(len(query_words), 1)

            combined_sim = 0.7 * similarity + 0.3 * concept_overlap

            similarities.append((discovery, combined_sim))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top results
        return [d for d, _ in similarities[:n_results]]

    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes."""
        if hash1 == hash2:
            return 1.0

        # Hamming distance
        xor = int(hash1, 16) ^ int(hash2, 16)
        distance = bin(xor).count('1')
        max_distance = len(hash1) * 4

        return 1.0 - (distance / max_distance)

    def decay_fields(self):
        """Apply temporal decay to all fields."""
        for field in self.fields.values():
            field.tau *= self.config.tau_decay_rate
            field.eta *= self.config.eta_decay_rate
            # c_k (memory) decays more slowly
            field.c_k *= 0.999

        # Remove very weak fields
        self.fields = {
            loc: field
            for loc, field in self.fields.items()
            if field.tau > self.config.min_pheromone_strength or
               field.eta > self.config.min_pheromone_strength or
               field.c_k > 0.01
        }

    def get_swarm_recommendations(
        self,
        current_location: str,
        agent_type: str = "explorer"
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations for swarm agents based on pheromone fields.

        Args:
            current_location: Current agent location
            agent_type: Type of agent

        Returns:
            List of recommended actions/locations
        """
        recommendations = []

        # Get current field
        current_field = self.get_field_at(current_location)

        # If no field info, return random exploration
        if not current_field:
            return [{
                'action': 'explore',
                'confidence': 0.5,
                'reason': 'no pheromone information'
            }]

        # Based on agent type and field, recommend actions
        if agent_type == "explorer":
            # Explorers seek high TAU (success) but avoid high ETA (failure)
            for location, field in self.fields.items():
                if location == current_location:
                    continue

                # Calculate attraction
                attraction = field.tau - field.eta

                if attraction > 0.5:
                    recommendations.append({
                        'action': 'move_to',
                        'target': location,
                        'confidence': min(attraction / 5.0, 1.0),
                        'reason': f'high aggregation (TAU={field.tau:.2f})'
                    })

        elif agent_type == "falsifier":
            # Falsifiers seek high C_K (well-established theories)
            for location, field in self.fields.items():
                if field.c_k > 0.7:
                    recommendations.append({
                        'action': 'test',
                        'target': location,
                        'confidence': field.c_k,
                        'reason': f'well-established theory (C_K={field.c_k:.2f})'
                    })

        # Sort by confidence
        recommendations.sort(key=lambda r: r['confidence'], reverse=True)

        return recommendations[:5]  # Return top 5

    def analyze_gaps(self) -> Dict[str, float]:
        """
        Analyze knowledge gaps based on field coverage.

        Returns:
            Dict mapping domains to gap scores (0=no gap, 1=large gap)
        """
        # Group fields by domain
        domain_fields: Dict[str, List[BiologicalFieldState]] = {}

        for field in self.fields.values():
            domain = field.domain
            if domain not in domain_fields:
                domain_fields[domain] = []
            domain_fields[domain].append(field)

        # Calculate gap for each domain
        gaps = {}

        # Common domains to check
        common_domains = [
            'astrophysics', 'causal_inference', 'physics',
            'mathematics', 'astronomy', 'general'
        ]

        for domain in common_domains:
            fields = domain_fields.get(domain, [])

            if not fields:
                # No fields = large gap
                gaps[domain] = 0.8
            else:
                # Calculate average C_K (memory strength)
                avg_ck = np.mean([f.c_k for f in fields])
                # Gap = 1 - memory strength
                gaps[domain] = 1.0 - avg_ck

        return gaps

    def get_integration_score(self) -> float:
        """
        Calculate how well integrated the stigmergic memory is.

        Returns:
            Integration score (0-1)
        """
        if not self.fields:
            return 0.0

        # Metrics
        field_coverage = min(len(self.fields) / 100, 1.0)  # Up to 100 locations
        discovery_coverage = min(len(self.discoveries) / 100, 1.0)
        avg_memory_strength = np.mean([f.c_k for f in self.fields.values()])

        # Combined score
        return (field_coverage + discovery_coverage + avg_memory_strength) / 3

    def get_state(self) -> Dict[str, Any]:
        """Get current memory state."""
        return {
            'n_fields': len(self.fields),
            'n_trails': len(self.trails),
            'n_discoveries': len(self.discoveries),
            'total_deposits': self.total_deposits,
            'total_discoveries': self.total_discoveries,
            'avg_tau': np.mean([f.tau for f in self.fields.values()]) if self.fields else 0,
            'avg_eta': np.mean([f.eta for f in self.fields.values()]) if self.fields else 0,
            'avg_c_k': np.mean([f.c_k for f in self.fields.values()]) if self.fields else 0,
            'domains': list(set(f.domain for f in self.fields.values())),
            'integration_score': self.get_integration_score()
        }

    def persist(self, path: Optional[str] = None):
        """Persist memory to disk."""
        path = path or self.config.persistence_path

        data = {
            'fields': {loc: f.to_dict() for loc, f in self.fields.items()},
            'trails': [
                {
                    'trail_id': t.trail_id,
                    'location': t.location,
                    'strength': t.strength,
                    'field_type': t.field_type.value,
                    'path_signature': t.path_signature,
                    'domain': t.domain,
                    'timestamp': t.timestamp
                }
                for t in self.trails[-1000:]  # Last 1000 trails
            ],
            'discoveries': [
                {
                    'signature_id': d.signature_id,
                    'content_hash': d.content_hash,
                    'domain': d.domain,
                    'key_concepts': d.key_concepts,
                    'reward': d.reward,
                    'novelty': d.novelty,
                    'timestamp': d.timestamp
                }
                for d in self.discoveries[-500:]  # Last 500 discoveries
            ],
            'statistics': {
                'total_deposits': self.total_deposits,
                'total_discoveries': self.total_discoveries,
                'last_update': self.last_update_time.isoformat()
            }
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
