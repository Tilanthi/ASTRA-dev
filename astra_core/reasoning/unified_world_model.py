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
Unified World Model & Belief State System for STAN V41

The foundational layer that all modules read from and write to.
Enables hypothesis accumulation, real-time belief updating,
and coherent reasoning across all capabilities.

This is the core AGI-like integration layer.

Date: 2025-12-11
Version: 41.0
"""

import time
import uuid
import math
import copy
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
import threading
import json


class BeliefType(Enum):
    """Types of beliefs in the world model"""
    HYPOTHESIS = "hypothesis"
    CAUSAL_RELATION = "causal_relation"
    CONSTRAINT = "constraint"
    FACT = "fact"
    ABSTRACTION = "abstraction"
    OBSERVATION = "observation"
    INFERENCE = "inference"
    EXTERNAL_KNOWLEDGE = "external_knowledge"


class EvidenceSource(Enum):
    """Sources of evidence for beliefs"""
    CAUSAL_DISCOVERY = "causal_discovery"
    ABDUCTIVE_INFERENCE = "abductive_inference"
    ACTIVE_EXPERIMENT = "active_experiment"
    EPISODIC_MEMORY = "episodic_memory"
    SYMBOLIC_MATH = "symbolic_math"
    PROOF_VALIDATOR = "proof_validator"
    QUANTITATIVE_REASONER = "quantitative_reasoner"
    EXTERNAL_KNOWLEDGE = "external_knowledge"
    LLM_INFERENCE = "llm_inference"
    META_LEARNING = "meta_learning"
    ABSTRACTION_LEARNING = "abstraction_learning"
    USER_INPUT = "user_input"
    COUNTERFACTUAL = "counterfactual"
    ANALOGY = "analogy"
    THEORY_SYNTHESIS = "theory_synthesis"


class ConfidenceLevel(Enum):
    """Qualitative confidence levels"""
    CERTAIN = 0.95
    HIGH = 0.80
    MODERATE = 0.60
    LOW = 0.40
    SPECULATIVE = 0.20
    UNKNOWN = 0.0


@dataclass
class Evidence:
    """A piece of evidence supporting or opposing a belief"""
    evidence_id: str
    source: EvidenceSource
    content: str
    strength: float  # -1.0 (strong against) to 1.0 (strong support)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.evidence_id:
            self.evidence_id = f"ev_{uuid.uuid4().hex[:8]}"


@dataclass
class Belief:
    """A belief in the world model with multi-source confidence"""
    belief_id: str
    belief_type: BeliefType
    statement: str
    confidence: float = 0.5
    evidence: List[Evidence] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    source_confidences: Dict[EvidenceSource, float] = field(default_factory=dict)
    related_beliefs: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.belief_id:
            self.belief_id = f"bel_{uuid.uuid4().hex[:8]}"

    def add_evidence(self, evidence: Evidence):
        """Add evidence and update confidence"""
        self.evidence.append(evidence)
        self.source_confidences[evidence.source] = evidence.strength
        self._recalculate_confidence()
        self.updated_at = time.time()

    def _recalculate_confidence(self):
        """Recalculate confidence from all evidence using Bayesian-like aggregation"""
        if not self.evidence:
            return

        # Weight evidence by source reliability
        source_weights = {
            EvidenceSource.PROOF_VALIDATOR: 1.0,
            EvidenceSource.SYMBOLIC_MATH: 0.95,
            EvidenceSource.CAUSAL_DISCOVERY: 0.85,
            EvidenceSource.QUANTITATIVE_REASONER: 0.85,
            EvidenceSource.ACTIVE_EXPERIMENT: 0.80,
            EvidenceSource.EXTERNAL_KNOWLEDGE: 0.75,
            EvidenceSource.ABDUCTIVE_INFERENCE: 0.70,
            EvidenceSource.LLM_INFERENCE: 0.65,
            EvidenceSource.EPISODIC_MEMORY: 0.60,
            EvidenceSource.ANALOGY: 0.55,
            EvidenceSource.META_LEARNING: 0.50,
            EvidenceSource.USER_INPUT: 0.70,
        }

        total_weight = 0
        weighted_sum = 0

        for ev in self.evidence:
            weight = source_weights.get(ev.source, 0.5)
            # Convert strength (-1 to 1) to confidence contribution (0 to 1)
            contribution = (ev.strength + 1) / 2
            weighted_sum += contribution * weight
            total_weight += weight

        if total_weight > 0:
            self.confidence = weighted_sum / total_weight

    def get_confidence_breakdown(self) -> Dict[str, float]:
        """Get confidence breakdown by source"""
        return {src.value: conf for src, conf in self.source_confidences.items()}


@dataclass
class CausalEdge:
    """A causal relationship in the world model"""
    edge_id: str
    cause: str
    effect: str
    strength: float = 0.5  # Causal strength
    confidence: float = 0.5
    mechanism: Optional[str] = None
    confounders: List[str] = field(default_factory=list)
    mediators: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)

    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = f"edge_{uuid.uuid4().hex[:8]}"


@dataclass
class Constraint:
    """A constraint or rule in the world model"""
    constraint_id: str
    constraint_type: str  # "prohibition", "requirement", "implication", "equivalence"
    expression: str
    confidence: float = 1.0
    source: EvidenceSource = EvidenceSource.USER_INPUT
    is_hard: bool = False  # Hard constraints must be satisfied

    def __post_init__(self):
        if not self.constraint_id:
            self.constraint_id = f"con_{uuid.uuid4().hex[:8]}"


@dataclass
class AbstractionTemplate:
    """A learned abstraction/pattern"""
    template_id: str
    name: str
    expression: str  # Symbolic expression
    variables: List[str]
    domain: str
    confidence: float = 0.5
    instances: List[Dict[str, Any]] = field(default_factory=list)
    related_templates: Set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.template_id:
            self.template_id = f"tmpl_{uuid.uuid4().hex[:8]}"


@dataclass
class Hypothesis:
    """A hypothesis under consideration"""
    hypothesis_id: str
    statement: str
    confidence: float = 0.5
    status: str = "active"  # active, confirmed, refuted, suspended
    evidence_for: List[Evidence] = field(default_factory=list)
    evidence_against: List[Evidence] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)
    tests_performed: List[str] = field(default_factory=list)
    competing_hypotheses: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.hypothesis_id:
            self.hypothesis_id = f"hyp_{uuid.uuid4().hex[:8]}"

    def add_supporting_evidence(self, evidence: Evidence):
        """Add evidence supporting this hypothesis"""
        self.evidence_for.append(evidence)
        self._update_confidence()

    def add_opposing_evidence(self, evidence: Evidence):
        """Add evidence against this hypothesis"""
        self.evidence_against.append(evidence)
        self._update_confidence()

    def _update_confidence(self):
        """Update confidence based on evidence balance"""
        support = sum(e.strength for e in self.evidence_for) if self.evidence_for else 0
        oppose = sum(abs(e.strength) for e in self.evidence_against) if self.evidence_against else 0

        total = support + oppose
        if total > 0:
            self.confidence = support / total
        else:
            self.confidence = 0.5


class CausalGraph:
    """Causal graph within the world model"""

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, CausalEdge] = {}
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node: str):
        """Add a node to the causal graph"""
        self.nodes.add(node)

    def add_edge(self, edge: CausalEdge):
        """Add a causal edge"""
        self.nodes.add(edge.cause)
        self.nodes.add(edge.effect)
        self.edges[edge.edge_id] = edge
        self.adjacency[edge.cause].add(edge.effect)
        self.reverse_adjacency[edge.effect].add(edge.cause)

    def get_parents(self, node: str) -> Set[str]:
        """Get causal parents of a node"""
        return self.reverse_adjacency.get(node, set())

    def get_children(self, node: str) -> Set[str]:
        """Get causal children of a node"""
        return self.adjacency.get(node, set())

    def get_ancestors(self, node: str) -> Set[str]:
        """Get all ancestors of a node"""
        ancestors = set()
        to_visit = list(self.get_parents(node))

        while to_visit:
            current = to_visit.pop()
            if current not in ancestors:
                ancestors.add(current)
                to_visit.extend(self.get_parents(current))

        return ancestors

    def get_descendants(self, node: str) -> Set[str]:
        """Get all descendants of a node"""
        descendants = set()
        to_visit = list(self.get_children(node))

        while to_visit:
            current = to_visit.pop()
            if current not in descendants:
                descendants.add(current)
                to_visit.extend(self.get_children(current))

        return descendants

    def get_edge_between(self, cause: str, effect: str) -> Optional[CausalEdge]:
        """Get edge between two nodes"""
        for edge in self.edges.values():
            if edge.cause == cause and edge.effect == effect:
                return edge
        return None

    def has_path(self, source: str, target: str) -> bool:
        """Check if there's a directed path from source to target"""
        return target in self.get_descendants(source)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'nodes': list(self.nodes),
            'edges': [
                {
                    'id': e.edge_id,
                    'cause': e.cause,
                    'effect': e.effect,
                    'strength': e.strength,
                    'confidence': e.confidence,
                    'mechanism': e.mechanism
                }
                for e in self.edges.values()
            ]
        }


class BeliefState:
    """
    Current belief state - a snapshot of all beliefs at a point in time.
    Supports entropy calculation and belief updating.
    """

    def __init__(self):
        self.beliefs: Dict[str, Belief] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.timestamp: float = time.time()
        self.entropy: float = 1.0  # Maximum uncertainty

    def add_belief(self, belief: Belief):
        """Add or update a belief"""
        self.beliefs[belief.belief_id] = belief
        self._update_entropy()

    def add_hypothesis(self, hypothesis: Hypothesis):
        """Add or update a hypothesis"""
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis
        self._update_entropy()

    def get_belief_by_statement(self, statement: str) -> Optional[Belief]:
        """Find belief by statement (approximate match)"""
        statement_lower = statement.lower()
        for belief in self.beliefs.values():
            if statement_lower in belief.statement.lower():
                return belief
        return None

    def get_top_hypotheses(self, n: int = 5) -> List[Hypothesis]:
        """Get top n hypotheses by confidence"""
        active = [h for h in self.hypotheses.values() if h.status == "active"]
        return sorted(active, key=lambda h: h.confidence, reverse=True)[:n]

    def _update_entropy(self):
        """Calculate entropy of belief state"""
        if not self.beliefs and not self.hypotheses:
            self.entropy = 1.0
            return

        # Calculate entropy from confidence distribution
        confidences = [b.confidence for b in self.beliefs.values()]
        confidences.extend([h.confidence for h in self.hypotheses.values()])

        if not confidences:
            self.entropy = 1.0
            return

        # Normalize to probabilities
        total = sum(confidences)
        if total == 0:
            self.entropy = 1.0
            return

        probs = [c / total for c in confidences if c > 0]

        # Shannon entropy
        self.entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        # Normalize by maximum possible entropy
        max_entropy = math.log2(len(probs)) if len(probs) > 1 else 1
        self.entropy = self.entropy / max_entropy if max_entropy > 0 else 0

    def get_uncertainty_by_topic(self) -> Dict[str, float]:
        """Get uncertainty levels by topic/tag"""
        topic_beliefs = defaultdict(list)

        for belief in self.beliefs.values():
            for tag in belief.tags:
                topic_beliefs[tag].append(belief.confidence)

        uncertainties = {}
        for topic, confs in topic_beliefs.items():
            avg_conf = sum(confs) / len(confs)
            uncertainties[topic] = 1 - avg_conf

        return uncertainties

    def snapshot(self) -> 'BeliefState':
        """Create a copy of current belief state"""
        new_state = BeliefState()
        new_state.beliefs = copy.deepcopy(self.beliefs)
        new_state.hypotheses = copy.deepcopy(self.hypotheses)
        new_state.timestamp = time.time()
        new_state._update_entropy()
        return new_state


class UnifiedWorldModel:
    """
    The Unified World Model - central knowledge representation for STAN V41.

    All modules read from and write to this model, enabling:
    - Hypothesis accumulation from multiple sources
    - Real-time belief updating
    - Coherent reasoning across capabilities
    - Knowledge persistence and retrieval
    """

    def __init__(self):
        # Core knowledge structures
        self.belief_state: BeliefState = BeliefState()
        self.causal_graph: CausalGraph = CausalGraph()
        self.constraints: Dict[str, Constraint] = {}
        self.abstractions: Dict[str, AbstractionTemplate] = {}

        # External knowledge cache
        self.external_facts: Dict[str, Dict[str, Any]] = {}

        # Episodic traces
        self.reasoning_traces: List[Dict[str, Any]] = []

        # Model metadata
        self.created_at: float = time.time()
        self.last_updated: float = time.time()
        self.update_count: int = 0

        # Thread safety
        self._lock = threading.RLock()

        # Change listeners
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)

    # ==================== Belief Management ====================

    def add_belief(self, belief: Belief, notify: bool = True):
        """Add or update a belief in the world model"""
        with self._lock:
            self.belief_state.add_belief(belief)
            self._mark_updated()

            if notify:
                self._notify_listeners('belief_added', belief)

    def get_belief(self, belief_id: str) -> Optional[Belief]:
        """Get a belief by ID"""
        return self.belief_state.beliefs.get(belief_id)

    def find_beliefs(self,
                    belief_type: Optional[BeliefType] = None,
                    tags: Optional[Set[str]] = None,
                    min_confidence: float = 0.0) -> List[Belief]:
        """Find beliefs matching criteria"""
        results = []

        for belief in self.belief_state.beliefs.values():
            if belief_type and belief.belief_type != belief_type:
                continue
            if tags and not tags.intersection(belief.tags):
                continue
            if belief.confidence < min_confidence:
                continue
            results.append(belief)

        return sorted(results, key=lambda b: b.confidence, reverse=True)

    def update_belief_confidence(self, belief_id: str,
                                  evidence: Evidence) -> Optional[Belief]:
        """Update a belief with new evidence"""
        with self._lock:
            belief = self.get_belief(belief_id)
            if belief:
                belief.add_evidence(evidence)
                self._mark_updated()
                self._notify_listeners('belief_updated', belief)
            return belief

    # ==================== Hypothesis Management ====================

    def add_hypothesis(self, hypothesis: Hypothesis, notify: bool = True):
        """Add or update a hypothesis"""
        with self._lock:
            self.belief_state.add_hypothesis(hypothesis)
            self._mark_updated()

            if notify:
                self._notify_listeners('hypothesis_added', hypothesis)

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        """Get a hypothesis by ID"""
        return self.belief_state.hypotheses.get(hypothesis_id)

    def get_active_hypotheses(self) -> List[Hypothesis]:
        """Get all active hypotheses"""
        return [h for h in self.belief_state.hypotheses.values()
                if h.status == "active"]

    def update_hypothesis(self, hypothesis_id: str,
                          evidence: Evidence,
                          is_supporting: bool = True) -> Optional[Hypothesis]:
        """Update hypothesis with new evidence"""
        with self._lock:
            hypothesis = self.get_hypothesis(hypothesis_id)
            if hypothesis:
                if is_supporting:
                    hypothesis.add_supporting_evidence(evidence)
                else:
                    hypothesis.add_opposing_evidence(evidence)
                self._mark_updated()
                self._notify_listeners('hypothesis_updated', hypothesis)
            return hypothesis

    def refute_hypothesis(self, hypothesis_id: str, reason: str):
        """Mark a hypothesis as refuted"""
        with self._lock:
            hypothesis = self.get_hypothesis(hypothesis_id)
            if hypothesis:
                hypothesis.status = "refuted"
                hypothesis.metadata['refutation_reason'] = reason
                self._mark_updated()
                self._notify_listeners('hypothesis_refuted', hypothesis)

    def confirm_hypothesis(self, hypothesis_id: str):
        """Mark a hypothesis as confirmed"""
        with self._lock:
            hypothesis = self.get_hypothesis(hypothesis_id)
            if hypothesis:
                hypothesis.status = "confirmed"
                self._mark_updated()
                self._notify_listeners('hypothesis_confirmed', hypothesis)

    # ==================== Causal Graph Management ====================

    def add_causal_edge(self, edge: CausalEdge, notify: bool = True):
        """Add a causal relationship"""
        with self._lock:
            self.causal_graph.add_edge(edge)
            self._mark_updated()

            if notify:
                self._notify_listeners('causal_edge_added', edge)

    def get_causal_parents(self, variable: str) -> Set[str]:
        """Get causal parents of a variable"""
        return self.causal_graph.get_parents(variable)

    def get_causal_children(self, variable: str) -> Set[str]:
        """Get causal children of a variable"""
        return self.causal_graph.get_children(variable)

    def has_causal_path(self, cause: str, effect: str) -> bool:
        """Check if there's a causal path between variables"""
        return self.causal_graph.has_path(cause, effect)

    def get_causal_mechanism(self, cause: str, effect: str) -> Optional[str]:
        """Get the mechanism for a causal relationship"""
        edge = self.causal_graph.get_edge_between(cause, effect)
        return edge.mechanism if edge else None

    # ==================== Constraint Management ====================

    def add_constraint(self, constraint: Constraint, notify: bool = True):
        """Add a constraint to the world model"""
        with self._lock:
            self.constraints[constraint.constraint_id] = constraint
            self._mark_updated()

            if notify:
                self._notify_listeners('constraint_added', constraint)

    def get_constraints(self, constraint_type: Optional[str] = None) -> List[Constraint]:
        """Get constraints, optionally filtered by type"""
        if constraint_type:
            return [c for c in self.constraints.values()
                    if c.constraint_type == constraint_type]
        return list(self.constraints.values())

    def check_constraint_violation(self, statement: str) -> List[Constraint]:
        """Check if a statement violates any constraints"""
        violations = []
        for constraint in self.constraints.values():
            if constraint.is_hard:
                # Simple keyword-based check (would be more sophisticated in practice)
                if self._constraint_conflicts(constraint, statement):
                    violations.append(constraint)
        return violations

    def _constraint_conflicts(self, constraint: Constraint, statement: str) -> bool:
        """Check if statement conflicts with constraint"""
        # Simplified check - in practice would use symbolic reasoning
        if constraint.constraint_type == "prohibition":
            # Check if statement contains prohibited elements
            return constraint.expression.lower() in statement.lower()
        return False

    # ==================== Abstraction Management ====================

    def add_abstraction(self, template: AbstractionTemplate, notify: bool = True):
        """Add a learned abstraction"""
        with self._lock:
            self.abstractions[template.template_id] = template
            self._mark_updated()

            if notify:
                self._notify_listeners('abstraction_added', template)

    def get_abstractions(self, domain: Optional[str] = None) -> List[AbstractionTemplate]:
        """Get abstractions, optionally filtered by domain"""
        if domain:
            return [a for a in self.abstractions.values() if a.domain == domain]
        return list(self.abstractions.values())

    def find_matching_abstraction(self, pattern: str) -> Optional[AbstractionTemplate]:
        """Find an abstraction matching a pattern"""
        # Simple matching - would use more sophisticated pattern matching
        for template in self.abstractions.values():
            if pattern.lower() in template.name.lower():
                return template
        return None

    # ==================== External Knowledge ====================

    def add_external_fact(self, source: str, key: str,
                          value: Any, confidence: float = 0.7):
        """Add a fact from external knowledge source"""
        with self._lock:
            if source not in self.external_facts:
                self.external_facts[source] = {}

            self.external_facts[source][key] = {
                'value': value,
                'confidence': confidence,
                'timestamp': time.time()
            }
            self._mark_updated()

    def get_external_fact(self, source: str, key: str) -> Optional[Any]:
        """Get an external fact"""
        if source in self.external_facts:
            fact = self.external_facts[source].get(key)
            return fact['value'] if fact else None
        return None

    # ==================== Reasoning Traces ====================

    def add_reasoning_step(self, step: Dict[str, Any]):
        """Add a reasoning step to the trace"""
        with self._lock:
            step['timestamp'] = time.time()
            self.reasoning_traces.append(step)

            # Keep only recent traces (last 1000)
            if len(self.reasoning_traces) > 1000:
                self.reasoning_traces = self.reasoning_traces[-1000:]

    def get_recent_traces(self, n: int = 50) -> List[Dict[str, Any]]:
        """Get recent reasoning traces"""
        return self.reasoning_traces[-n:]

    # ==================== State Management ====================

    def get_entropy(self) -> float:
        """Get current entropy (uncertainty) of the world model"""
        return self.belief_state.entropy

    def get_confidence_summary(self) -> Dict[str, float]:
        """Get summary of confidence levels across the model"""
        return {
            'avg_belief_confidence': (
                sum(b.confidence for b in self.belief_state.beliefs.values()) /
                max(1, len(self.belief_state.beliefs))
            ),
            'avg_hypothesis_confidence': (
                sum(h.confidence for h in self.belief_state.hypotheses.values()) /
                max(1, len(self.belief_state.hypotheses))
            ),
            'n_beliefs': len(self.belief_state.beliefs),
            'n_hypotheses': len(self.belief_state.hypotheses),
            'n_causal_edges': len(self.causal_graph.edges),
            'n_constraints': len(self.constraints),
            'n_abstractions': len(self.abstractions),
            'entropy': self.belief_state.entropy
        }

    def snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of the current world model state"""
        with self._lock:
            return {
                'timestamp': time.time(),
                'belief_state': {
                    'n_beliefs': len(self.belief_state.beliefs),
                    'n_hypotheses': len(self.belief_state.hypotheses),
                    'entropy': self.belief_state.entropy
                },
                'causal_graph': self.causal_graph.to_dict(),
                'n_constraints': len(self.constraints),
                'n_abstractions': len(self.abstractions),
                'update_count': self.update_count
            }

    def _mark_updated(self):
        """Mark the model as updated"""
        self.last_updated = time.time()
        self.update_count += 1

    # ==================== Event System ====================

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to world model events"""
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from world model events"""
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)


# ==================== World Model Factory ====================
# Singleton instance for system-wide use
_world_model_instance: Optional[UnifiedWorldModel] = None


def get_world_model(config: Optional[Dict[str, Any]] = None) -> UnifiedWorldModel:
    """
    Get or create the singleton world model instance.

    This factory function provides system-wide access to the unified world model,
    enabling all modules to share the same knowledge representation.

    Args:
        config: Optional configuration dictionary (not currently used)

    Returns:
        The singleton UnifiedWorldModel instance
    """
    global _world_model_instance

    if _world_model_instance is None:
        _world_model_instance = UnifiedWorldModel()

        # Initialize with basic physics knowledge if available
        try:
            from .world_model_factory import _initialize_ism_knowledge
            _initialize_ism_knowledge(_world_model_instance)
        except ImportError:
            # Factory module not available, use basic initialization
            pass

    return _world_model_instance


def reset_world_model():
    """Reset the world model singleton (useful for testing)"""
    global _world_model_instance
    _world_model_instance = None
