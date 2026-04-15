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
Continuous Learning Integration Module for STAN V41

Implements mechanisms for the system to learn and improve from experience
without explicit retraining. Knowledge is accumulated, refined, and
consolidated across sessions.

Key capabilities:
- Experience accumulation: Store and index problem-solving episodes
- Pattern extraction: Identify successful strategies from experience
- Knowledge consolidation: Merge and refine accumulated knowledge
- Skill transfer: Apply learned skills to new domains
- Capability evolution: Improve reasoning methods over time
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, Tuple
from enum import Enum, auto
from datetime import datetime
import uuid
from collections import defaultdict
import json
import math
import hashlib


class ExperienceType(Enum):
    """Types of experiences"""
    PROBLEM_SOLVING = auto()    # Solved a problem
    ERROR_RECOVERY = auto()     # Recovered from error
    INSIGHT = auto()            # Gained new understanding
    SKILL_ACQUISITION = auto()  # Learned new skill
    KNOWLEDGE_UPDATE = auto()   # Updated existing knowledge
    STRATEGY_DISCOVERY = auto() # Found effective strategy


class LearningSignal(Enum):
    """Types of learning signals"""
    SUCCESS = auto()            # Task completed successfully
    FAILURE = auto()            # Task failed
    PARTIAL = auto()            # Partially successful
    FEEDBACK = auto()           # External feedback received
    SELF_ASSESSMENT = auto()    # Internal quality assessment


class ConsolidationStrategy(Enum):
    """Strategies for knowledge consolidation"""
    MERGE = auto()              # Combine similar knowledge
    REFINE = auto()             # Update with new evidence
    ABSTRACT = auto()           # Extract general principle
    SPECIALIZE = auto()         # Create domain-specific version
    PRUNE = auto()              # Remove outdated knowledge


@dataclass
class Experience:
    """A recorded experience for learning"""
    experience_id: str
    experience_type: ExperienceType
    timestamp: datetime = field(default_factory=datetime.now)

    # Context
    domain: str = ""
    task_description: str = ""
    initial_state: Dict[str, Any] = field(default_factory=dict)

    # Process
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    capabilities_used: List[str] = field(default_factory=list)
    reasoning_trace: List[str] = field(default_factory=list)

    # Outcome
    result: str = ""
    success_score: float = 0.5
    learning_signal: LearningSignal = LearningSignal.PARTIAL

    # Derived
    key_factors: List[str] = field(default_factory=list)  # What made it work/fail
    generalizable_patterns: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.experience_id:
            self.experience_id = f"EXP-{uuid.uuid4().hex[:8]}"

    @property
    def signature(self) -> str:
        """Generate a signature for similarity matching"""
        sig_content = f"{self.domain}:{self.task_description[:50]}"
        return hashlib.md5(sig_content.encode()).hexdigest()[:12]


@dataclass
class LearnedPattern:
    """A pattern extracted from experiences"""
    pattern_id: str
    name: str
    description: str

    # Pattern specification
    trigger_conditions: List[str]       # When to apply
    action_sequence: List[str]          # What to do
    expected_outcome: str

    # Evidence
    source_experiences: List[str]       # Experience IDs
    success_rate: float = 0.0
    application_count: int = 0

    # Scope
    domains: List[str] = field(default_factory=list)
    generality: float = 0.5             # 0 = specific, 1 = general

    # Confidence
    confidence: float = 0.5
    last_validated: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.pattern_id:
            self.pattern_id = f"PTN-{uuid.uuid4().hex[:8]}"

    def update_from_application(self, success: bool):
        """Update pattern statistics after application"""
        self.application_count += 1
        # Exponential moving average for success rate
        alpha = 0.1
        outcome = 1.0 if success else 0.0
        self.success_rate = alpha * outcome + (1 - alpha) * self.success_rate


@dataclass
class LearnedSkill:
    """A skill learned from experience"""
    skill_id: str
    name: str
    description: str

    # Skill definition
    preconditions: List[str]            # What must be true to apply
    procedure: List[str]                # Steps to execute
    postconditions: List[str]           # What should be true after

    # Performance
    proficiency: float = 0.0            # 0 = novice, 1 = expert
    execution_count: int = 0
    avg_quality: float = 0.5

    # Transfer
    source_domain: str = ""
    applicable_domains: List[str] = field(default_factory=list)

    # Metadata
    acquired_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

    def __post_init__(self):
        if not self.skill_id:
            self.skill_id = f"SKL-{uuid.uuid4().hex[:8]}"


@dataclass
class KnowledgeItem:
    """An item of knowledge to be consolidated"""
    item_id: str
    content: str
    source: str                         # Where it came from

    # Classification
    domain: str
    knowledge_type: str                 # "fact", "rule", "heuristic", "concept"

    # Quality
    confidence: float = 0.5
    evidence_count: int = 1
    contradiction_count: int = 0

    # Relations
    supports: List[str] = field(default_factory=list)     # Item IDs
    contradicts: List[str] = field(default_factory=list)
    generalizes: Optional[str] = None   # More general item ID
    specializes: Optional[str] = None   # More specific item ID

    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.item_id:
            self.item_id = f"KNI-{uuid.uuid4().hex[:8]}"


class ExperienceStore:
    """Stores and indexes experiences for learning"""

    def __init__(self, max_experiences: int = 10000):
        self.experiences: Dict[str, Experience] = {}
        self.max_experiences = max_experiences

        # Indices
        self.by_domain: Dict[str, List[str]] = defaultdict(list)
        self.by_type: Dict[ExperienceType, List[str]] = defaultdict(list)
        self.by_signal: Dict[LearningSignal, List[str]] = defaultdict(list)
        self.by_signature: Dict[str, List[str]] = defaultdict(list)

    def store(self, experience: Experience) -> str:
        """Store an experience"""
        # Enforce capacity
        if len(self.experiences) >= self.max_experiences:
            self._evict_oldest()

        self.experiences[experience.experience_id] = experience

        # Update indices
        self.by_domain[experience.domain].append(experience.experience_id)
        self.by_type[experience.experience_type].append(experience.experience_id)
        self.by_signal[experience.learning_signal].append(experience.experience_id)
        self.by_signature[experience.signature].append(experience.experience_id)

        return experience.experience_id

    def retrieve_similar(
        self,
        query_experience: Experience,
        limit: int = 10
    ) -> List[Experience]:
        """Retrieve experiences similar to query"""
        # First check signature match
        similar_ids = self.by_signature.get(query_experience.signature, [])

        # Then check domain match
        domain_ids = self.by_domain.get(query_experience.domain, [])

        # Combine and deduplicate
        candidates = list(set(similar_ids + domain_ids))

        # Score by similarity
        scored = []
        for eid in candidates:
            exp = self.experiences.get(eid)
            if exp:
                sim = self._compute_similarity(query_experience, exp)
                scored.append((sim, exp))

        # Sort and return top
        scored.sort(key=lambda x: x[0], reverse=True)
        return [exp for _, exp in scored[:limit]]

    def get_successful(self, domain: str = None, limit: int = 50) -> List[Experience]:
        """Get successful experiences"""
        success_ids = self.by_signal.get(LearningSignal.SUCCESS, [])

        if domain:
            domain_ids = set(self.by_domain.get(domain, []))
            success_ids = [eid for eid in success_ids if eid in domain_ids]

        experiences = [self.experiences[eid] for eid in success_ids if eid in self.experiences]
        experiences.sort(key=lambda e: e.success_score, reverse=True)
        return experiences[:limit]

    def _compute_similarity(self, exp1: Experience, exp2: Experience) -> float:
        """Compute similarity between experiences"""
        if exp1.experience_id == exp2.experience_id:
            return 0.0  # Don't match self

        score = 0.0

        # Same domain
        if exp1.domain == exp2.domain:
            score += 0.3

        # Same signature
        if exp1.signature == exp2.signature:
            score += 0.3

        # Same type
        if exp1.experience_type == exp2.experience_type:
            score += 0.2

        # Capability overlap
        caps1 = set(exp1.capabilities_used)
        caps2 = set(exp2.capabilities_used)
        if caps1 and caps2:
            overlap = len(caps1 & caps2) / len(caps1 | caps2)
            score += 0.2 * overlap

        return score

    def _evict_oldest(self):
        """Evict oldest, least valuable experiences"""
        if not self.experiences:
            return

        # Sort by age and success
        sorted_exps = sorted(
            self.experiences.values(),
            key=lambda e: (e.success_score, -e.timestamp.timestamp())
        )

        # Remove bottom 10%
        to_remove = len(self.experiences) // 10
        for exp in sorted_exps[:to_remove]:
            del self.experiences[exp.experience_id]


class PatternExtractor:
    """Extracts patterns from successful experiences"""

    def __init__(self, min_support: int = 3):
        self.min_support = min_support

    def extract_patterns(
        self,
        experiences: List[Experience]
    ) -> List[LearnedPattern]:
        """Extract patterns from experiences"""
        patterns = []

        # Group by domain
        by_domain = defaultdict(list)
        for exp in experiences:
            if exp.success_score >= 0.7:  # Only from successful experiences
                by_domain[exp.domain].append(exp)

        for domain, domain_exps in by_domain.items():
            if len(domain_exps) >= self.min_support:
                domain_patterns = self._extract_domain_patterns(domain, domain_exps)
                patterns.extend(domain_patterns)

        return patterns

    def _extract_domain_patterns(
        self,
        domain: str,
        experiences: List[Experience]
    ) -> List[LearnedPattern]:
        """Extract patterns within a domain"""
        patterns = []

        # Find common action sequences
        action_sequences = self._find_common_sequences(
            [exp.actions_taken for exp in experiences]
        )

        for seq_key, (sequence, support) in action_sequences.items():
            if support >= self.min_support:
                # Find common conditions
                conditions = self._find_common_conditions(
                    [exp for exp in experiences if self._contains_sequence(exp.actions_taken, sequence)]
                )

                pattern = LearnedPattern(
                    pattern_id="",
                    name=f"Pattern in {domain}: {seq_key[:30]}",
                    description=f"Common successful approach in {domain}",
                    trigger_conditions=conditions,
                    action_sequence=sequence,
                    expected_outcome="Success",
                    source_experiences=[exp.experience_id for exp in experiences[:5]],
                    success_rate=sum(e.success_score for e in experiences) / len(experiences),
                    domains=[domain],
                    generality=0.5,
                    confidence=min(1.0, support / 10)
                )
                patterns.append(pattern)

        return patterns

    def _find_common_sequences(
        self,
        action_lists: List[List[Dict[str, Any]]]
    ) -> Dict[str, Tuple[List[str], int]]:
        """Find common action sequences"""
        # Simplify actions to strings
        simplified = []
        for actions in action_lists:
            simplified.append([str(a.get("type", "action")) for a in actions])

        # Find common subsequences
        sequence_counts = defaultdict(int)
        for seq in simplified:
            for length in range(1, min(5, len(seq) + 1)):
                for i in range(len(seq) - length + 1):
                    subseq = tuple(seq[i:i+length])
                    sequence_counts[subseq] += 1

        # Return sequences with sufficient support
        result = {}
        for seq, count in sequence_counts.items():
            if count >= self.min_support:
                key = "->".join(seq)
                result[key] = (list(seq), count)

        return result

    def _find_common_conditions(
        self,
        experiences: List[Experience]
    ) -> List[str]:
        """Find common trigger conditions"""
        if not experiences:
            return []

        # Collect all key factors
        all_factors = []
        for exp in experiences:
            all_factors.extend(exp.key_factors)

        # Find frequently occurring factors
        factor_counts = defaultdict(int)
        for factor in all_factors:
            factor_counts[factor] += 1

        threshold = len(experiences) * 0.5
        common = [f for f, c in factor_counts.items() if c >= threshold]

        return common[:5]  # Top 5 conditions

    def _contains_sequence(
        self,
        actions: List[Dict[str, Any]],
        sequence: List[str]
    ) -> bool:
        """Check if actions contain the sequence"""
        simplified = [str(a.get("type", "action")) for a in actions]
        seq_str = "->".join(sequence)
        actions_str = "->".join(simplified)
        return seq_str in actions_str


class KnowledgeConsolidator:
    """Consolidates and refines accumulated knowledge"""

    def __init__(self):
        self.knowledge: Dict[str, KnowledgeItem] = {}

    def add_knowledge(self, item: KnowledgeItem) -> str:
        """Add a knowledge item"""
        # Check for similar existing knowledge
        similar = self._find_similar(item)

        if similar:
            # Consolidate with existing
            self._consolidate(similar, item)
            return similar.item_id
        else:
            self.knowledge[item.item_id] = item
            return item.item_id

    def consolidate_all(self) -> List[str]:
        """Run consolidation across all knowledge"""
        consolidated = []

        items = list(self.knowledge.values())
        for i, item1 in enumerate(items):
            for item2 in items[i+1:]:
                if self._should_merge(item1, item2):
                    merged_id = self._merge(item1, item2)
                    consolidated.append(merged_id)

        return consolidated

    def prune(self, confidence_threshold: float = 0.3) -> List[str]:
        """Prune low-confidence or contradicted knowledge"""
        pruned = []

        for item_id, item in list(self.knowledge.items()):
            # Low confidence
            if item.confidence < confidence_threshold:
                pruned.append(item_id)
                del self.knowledge[item_id]
                continue

            # More contradictions than evidence
            if item.contradiction_count > item.evidence_count:
                pruned.append(item_id)
                del self.knowledge[item_id]

        return pruned

    def _find_similar(self, item: KnowledgeItem) -> Optional[KnowledgeItem]:
        """Find similar existing knowledge"""
        for existing in self.knowledge.values():
            if existing.domain == item.domain:
                # Simple content similarity
                if self._content_similarity(existing.content, item.content) > 0.7:
                    return existing
        return None

    def _consolidate(self, existing: KnowledgeItem, new: KnowledgeItem):
        """Consolidate new knowledge with existing"""
        # Increase evidence
        existing.evidence_count += 1

        # Update confidence (weighted average)
        total_evidence = existing.evidence_count
        existing.confidence = (
            (existing.confidence * (total_evidence - 1) + new.confidence) / total_evidence
        )

        existing.last_updated = datetime.now()

    def _should_merge(self, item1: KnowledgeItem, item2: KnowledgeItem) -> bool:
        """Determine if two items should be merged"""
        if item1.domain != item2.domain:
            return False
        if item1.knowledge_type != item2.knowledge_type:
            return False
        return self._content_similarity(item1.content, item2.content) > 0.8

    def _merge(self, item1: KnowledgeItem, item2: KnowledgeItem) -> str:
        """Merge two knowledge items"""
        # Keep the one with more evidence
        if item1.evidence_count >= item2.evidence_count:
            keeper, other = item1, item2
        else:
            keeper, other = item2, item1

        # Update keeper with other's evidence
        keeper.evidence_count += other.evidence_count
        keeper.confidence = (keeper.confidence + other.confidence) / 2
        keeper.last_updated = datetime.now()

        # Remove other
        if other.item_id in self.knowledge:
            del self.knowledge[other.item_id]

        return keeper.item_id

    def _content_similarity(self, text1: str, text2: str) -> float:
        """Compute content similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)


class SkillTransferEngine:
    """Transfers learned skills to new domains"""

    def __init__(self):
        self.skills: Dict[str, LearnedSkill] = {}
        self.transfer_history: List[Dict[str, Any]] = []

    def add_skill(self, skill: LearnedSkill):
        """Add a learned skill"""
        self.skills[skill.skill_id] = skill

    def find_transferable(
        self,
        target_domain: str,
        task_requirements: List[str]
    ) -> List[Tuple[LearnedSkill, float]]:
        """Find skills transferable to target domain"""
        candidates = []

        for skill in self.skills.values():
            if target_domain in skill.applicable_domains:
                # Already known to apply
                score = skill.proficiency
            else:
                # Estimate transferability
                score = self._estimate_transferability(skill, target_domain, task_requirements)

            if score > 0.3:
                candidates.append((skill, score))

        return sorted(candidates, key=lambda x: x[1], reverse=True)

    def _estimate_transferability(
        self,
        skill: LearnedSkill,
        target_domain: str,
        requirements: List[str]
    ) -> float:
        """Estimate how transferable a skill is"""
        score = 0.0

        # Check precondition relevance
        for precond in skill.preconditions:
            for req in requirements:
                if any(word in req.lower() for word in precond.lower().split()):
                    score += 0.2
                    break

        # Check procedure applicability
        procedure_words = " ".join(skill.procedure).lower().split()
        req_words = " ".join(requirements).lower().split()
        overlap = len(set(procedure_words) & set(req_words))
        score += min(0.3, overlap * 0.05)

        # Proficiency factor
        score *= skill.proficiency

        return min(1.0, score)

    def apply_skill(
        self,
        skill_id: str,
        target_domain: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a skill to a new context"""
        skill = self.skills.get(skill_id)
        if not skill:
            return {"success": False, "error": "Skill not found"}

        # Check preconditions
        precond_met = self._check_preconditions(skill, context)
        if not precond_met:
            return {
                "success": False,
                "error": "Preconditions not met",
                "missing": [p for p in skill.preconditions if not self._precondition_satisfied(p, context)]
            }

        # Adapt procedure to context
        adapted = self._adapt_procedure(skill.procedure, target_domain, context)

        # Update skill
        skill.execution_count += 1
        skill.last_used = datetime.now()
        if target_domain not in skill.applicable_domains:
            skill.applicable_domains.append(target_domain)

        self.transfer_history.append({
            "skill_id": skill_id,
            "target_domain": target_domain,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "success": True,
            "adapted_procedure": adapted,
            "postconditions": skill.postconditions
        }

    def _check_preconditions(self, skill: LearnedSkill, context: Dict[str, Any]) -> bool:
        """Check if preconditions are satisfied"""
        for precond in skill.preconditions:
            if not self._precondition_satisfied(precond, context):
                return False
        return True

    def _precondition_satisfied(self, precond: str, context: Dict[str, Any]) -> bool:
        """Check single precondition"""
        # Simplified check - in practice would be more sophisticated
        context_str = str(context).lower()
        return any(word in context_str for word in precond.lower().split())

    def _adapt_procedure(
        self,
        procedure: List[str],
        target_domain: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Adapt procedure steps to new context"""
        adapted = []
        for step in procedure:
            # Simple adaptation - add domain context
            adapted_step = f"[{target_domain}] {step}"
            adapted.append(adapted_step)
        return adapted

    def record_outcome(self, skill_id: str, success: bool, quality: float):
        """Record outcome of skill application"""
        skill = self.skills.get(skill_id)
        if skill:
            # Update proficiency
            alpha = 0.1
            outcome = quality if success else quality * 0.5
            skill.proficiency = alpha * outcome + (1 - alpha) * skill.proficiency

            # Update average quality
            n = skill.execution_count
            skill.avg_quality = (skill.avg_quality * (n - 1) + quality) / n


class ContinuousLearner:
    """
    Main continuous learning engine.
    Coordinates experience storage, pattern extraction, knowledge consolidation,
    and skill transfer.
    """

    def __init__(self, storage_path: str = None):
        self.experience_store = ExperienceStore()
        self.pattern_extractor = PatternExtractor()
        self.knowledge_consolidator = KnowledgeConsolidator()
        self.skill_transfer = SkillTransferEngine()

        self.patterns: Dict[str, LearnedPattern] = {}
        self.storage_path = storage_path

        # Statistics
        self.total_experiences = 0
        self.patterns_extracted = 0
        self.skills_transferred = 0

        # Event callbacks
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        """Register callback"""
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any):
        """Emit event"""
        for callback in self._callbacks[event]:
            callback(data)

    # Experience management
    def record_experience(
        self,
        domain: str,
        task_description: str,
        actions: List[Dict[str, Any]],
        capabilities: List[str],
        result: str,
        success_score: float,
        key_factors: List[str] = None
    ) -> Experience:
        """Record a problem-solving experience"""
        experience = Experience(
            experience_id="",
            experience_type=ExperienceType.PROBLEM_SOLVING,
            domain=domain,
            task_description=task_description,
            actions_taken=actions,
            capabilities_used=capabilities,
            result=result,
            success_score=success_score,
            learning_signal=self._score_to_signal(success_score),
            key_factors=key_factors or []
        )

        self.experience_store.store(experience)
        self.total_experiences += 1

        # Trigger learning if enough experiences
        if self.total_experiences % 10 == 0:
            self._periodic_learning()

        self._emit("experience_recorded", experience)
        return experience

    def record_error_recovery(
        self,
        domain: str,
        error_description: str,
        recovery_actions: List[Dict[str, Any]],
        success: bool
    ) -> Experience:
        """Record an error recovery experience"""
        experience = Experience(
            experience_id="",
            experience_type=ExperienceType.ERROR_RECOVERY,
            domain=domain,
            task_description=f"Error: {error_description}",
            actions_taken=recovery_actions,
            result="Recovered" if success else "Failed",
            success_score=1.0 if success else 0.0,
            learning_signal=LearningSignal.SUCCESS if success else LearningSignal.FAILURE
        )

        self.experience_store.store(experience)
        self._emit("error_recovery_recorded", experience)
        return experience

    def _score_to_signal(self, score: float) -> LearningSignal:
        """Convert success score to learning signal"""
        if score >= 0.8:
            return LearningSignal.SUCCESS
        elif score >= 0.5:
            return LearningSignal.PARTIAL
        else:
            return LearningSignal.FAILURE

    # Pattern extraction
    def extract_patterns(self, domain: str = None) -> List[LearnedPattern]:
        """Extract patterns from experiences"""
        if domain:
            experiences = self.experience_store.get_successful(domain)
        else:
            experiences = self.experience_store.get_successful()

        patterns = self.pattern_extractor.extract_patterns(experiences)

        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern
            self.patterns_extracted += 1

        self._emit("patterns_extracted", patterns)
        return patterns

    def apply_pattern(
        self,
        pattern_id: str,
        context: Dict[str, Any]
    ) -> Optional[List[str]]:
        """Apply a learned pattern"""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return None

        # Check trigger conditions
        context_str = str(context).lower()
        conditions_met = all(
            any(word in context_str for word in cond.lower().split())
            for cond in pattern.trigger_conditions
        )

        if not conditions_met:
            return None

        pattern.application_count += 1
        return pattern.action_sequence

    def record_pattern_outcome(self, pattern_id: str, success: bool):
        """Record outcome of pattern application"""
        pattern = self.patterns.get(pattern_id)
        if pattern:
            pattern.update_from_application(success)
            pattern.last_validated = datetime.now()

    # Knowledge consolidation
    def add_knowledge(
        self,
        content: str,
        domain: str,
        knowledge_type: str,
        source: str,
        confidence: float = 0.5
    ) -> str:
        """Add knowledge for consolidation"""
        item = KnowledgeItem(
            item_id="",
            content=content,
            source=source,
            domain=domain,
            knowledge_type=knowledge_type,
            confidence=confidence
        )

        item_id = self.knowledge_consolidator.add_knowledge(item)
        self._emit("knowledge_added", item)
        return item_id

    def consolidate_knowledge(self) -> Dict[str, Any]:
        """Run knowledge consolidation"""
        merged = self.knowledge_consolidator.consolidate_all()
        pruned = self.knowledge_consolidator.prune()

        result = {
            "merged": len(merged),
            "pruned": len(pruned),
            "remaining": len(self.knowledge_consolidator.knowledge)
        }

        self._emit("knowledge_consolidated", result)
        return result

    # Skill learning and transfer
    def learn_skill(
        self,
        name: str,
        description: str,
        preconditions: List[str],
        procedure: List[str],
        postconditions: List[str],
        source_domain: str
    ) -> LearnedSkill:
        """Learn a new skill"""
        skill = LearnedSkill(
            skill_id="",
            name=name,
            description=description,
            preconditions=preconditions,
            procedure=procedure,
            postconditions=postconditions,
            source_domain=source_domain,
            applicable_domains=[source_domain]
        )

        self.skill_transfer.add_skill(skill)
        self._emit("skill_learned", skill)
        return skill

    def find_applicable_skills(
        self,
        target_domain: str,
        requirements: List[str]
    ) -> List[Tuple[LearnedSkill, float]]:
        """Find skills applicable to a task"""
        return self.skill_transfer.find_transferable(target_domain, requirements)

    def transfer_skill(
        self,
        skill_id: str,
        target_domain: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transfer a skill to a new domain"""
        result = self.skill_transfer.apply_skill(skill_id, target_domain, context)

        if result["success"]:
            self.skills_transferred += 1
            self._emit("skill_transferred", {
                "skill_id": skill_id,
                "target_domain": target_domain
            })

        return result

    # Periodic learning
    def _periodic_learning(self):
        """Run periodic learning tasks"""
        # Extract patterns
        patterns = self.extract_patterns()

        # Consolidate knowledge
        self.consolidate_knowledge()

        self._emit("periodic_learning_complete", {
            "patterns_found": len(patterns),
            "total_experiences": self.total_experiences
        })

    # Query capabilities
    def get_relevant_experience(
        self,
        task: str,
        domain: str
    ) -> List[Experience]:
        """Get experiences relevant to a task"""
        query = Experience(
            experience_id="query",
            experience_type=ExperienceType.PROBLEM_SOLVING,
            domain=domain,
            task_description=task
        )
        return self.experience_store.retrieve_similar(query)

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning state"""
        return {
            "experiences": {
                "total": self.total_experiences,
                "by_signal": {
                    signal.name: len(ids)
                    for signal, ids in self.experience_store.by_signal.items()
                }
            },
            "patterns": {
                "total": self.patterns_extracted,
                "active": len([p for p in self.patterns.values() if p.application_count > 0]),
                "avg_success_rate": sum(p.success_rate for p in self.patterns.values()) / max(1, len(self.patterns))
            },
            "knowledge": {
                "items": len(self.knowledge_consolidator.knowledge)
            },
            "skills": {
                "total": len(self.skill_transfer.skills),
                "transfers": self.skills_transferred
            }
        }

    # Persistence
    def save_state(self, path: str = None):
        """Save learning state to file"""
        path = path or self.storage_path
        if not path:
            return

        state = {
            "patterns": {
                pid: {
                    "name": p.name,
                    "description": p.description,
                    "trigger_conditions": p.trigger_conditions,
                    "action_sequence": p.action_sequence,
                    "success_rate": p.success_rate,
                    "application_count": p.application_count,
                    "domains": p.domains
                }
                for pid, p in self.patterns.items()
            },
            "skills": {
                sid: {
                    "name": s.name,
                    "description": s.description,
                    "proficiency": s.proficiency,
                    "source_domain": s.source_domain,
                    "applicable_domains": s.applicable_domains
                }
                for sid, s in self.skill_transfer.skills.items()
            },
            "stats": {
                "total_experiences": self.total_experiences,
                "patterns_extracted": self.patterns_extracted,
                "skills_transferred": self.skills_transferred
            }
        }

        with open(path, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: str = None):
        """Load state from file"""
        if path is None:
            path = self.state_path

        try:
            with open(path, 'r') as f:
                state = json.load(f)

            self.total_experiences = state.get('total_experiences', 0)
            self.patterns_extracted = state.get('patterns_extracted', 0)
            self.skills_transferred = state.get('skills_transferred', 0)

            return True
        except Exception as e:
            print(f"Failed to load state: {e}")
            return False
