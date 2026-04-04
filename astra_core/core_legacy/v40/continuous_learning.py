"""
Continuous Learning System for STAN V40

Implements:
- Pattern storage and retrieval
- Failure analysis
- Heuristic updating
- Curriculum-based self-improvement

Target: Adaptive performance improvement over time

Date: 2025-12-11
Version: 40.0
"""

import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from enum import Enum
from collections import defaultdict
import math


class LearningEventType(Enum):
    """Types of learning events"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"


class PatternType(Enum):
    """Types of learned patterns"""
    PROBLEM_SOLUTION = "problem_solution"
    ERROR_CORRECTION = "error_correction"
    STRATEGY_SELECTION = "strategy_selection"
    HEURISTIC = "heuristic"
    ANALOGY = "analogy"


@dataclass
class LearningEvent:
    """A learning event from problem solving"""
    event_id: str
    event_type: LearningEventType
    timestamp: float

    # Problem info
    question: str
    category: str
    problem_hash: str  # For similarity lookup

    # Solution info
    predicted_answer: Any
    correct_answer: Optional[Any] = None
    was_correct: Optional[bool] = None

    # Strategy info
    strategy_used: str = ""
    confidence: float = 0.0
    reasoning_trace: List[str] = field(default_factory=list)

    # Metadata
    time_taken: float = 0.0
    resources_used: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'id': self.event_id,
            'type': self.event_type.value,
            'category': self.category,
            'correct': self.was_correct,
            'confidence': self.confidence,
            'strategy': self.strategy_used
        }


@dataclass
class LearnedPattern:
    """A learned pattern"""
    pattern_id: str
    pattern_type: PatternType
    created_at: float

    # Pattern content
    trigger: str  # What triggers this pattern
    response: str  # What to do
    context: Dict[str, Any] = field(default_factory=dict)

    # Quality metrics
    usage_count: int = 0
    success_count: int = 0
    confidence: float = 0.5

    # Relevance
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.5
        return self.success_count / self.usage_count

    def to_dict(self) -> Dict:
        return {
            'id': self.pattern_id,
            'type': self.pattern_type.value,
            'trigger': self.trigger[:100],
            'confidence': self.confidence,
            'success_rate': self.success_rate()
        }


@dataclass
class CurriculumItem:
    """An item in the learning curriculum"""
    item_id: str
    difficulty: float  # 0-1
    category: str
    problem_type: str

    # Training data
    question: str
    answer: Any
    explanation: str = ""

    # Progress
    attempts: int = 0
    successes: int = 0
    mastery: float = 0.0

    def update_mastery(self, correct: bool) -> None:
        """Update mastery based on attempt result"""
        self.attempts += 1
        if correct:
            self.successes += 1

        # Mastery with recency weighting
        base_rate = self.successes / self.attempts
        recency_bonus = 0.1 if correct else -0.1
        self.mastery = base_rate * 0.8 + (self.mastery + recency_bonus) * 0.2
        self.mastery = max(0.0, min(1.0, self.mastery))


class PatternLibrary:
    """
    Library of learned patterns.

    Stores and retrieves patterns for:
    - Problem-solution mappings
    - Error corrections
    - Strategy selections
    """

    def __init__(self, max_patterns: int = 10000):
        self.max_patterns = max_patterns

        # Pattern storage
        self.patterns: Dict[str, LearnedPattern] = {}

        # Indices for lookup
        self.by_category: Dict[str, Set[str]] = defaultdict(set)
        self.by_keyword: Dict[str, Set[str]] = defaultdict(set)
        self.by_type: Dict[PatternType, Set[str]] = defaultdict(set)

        # Statistics
        self.patterns_created = 0
        self.patterns_used = 0

    def add_pattern(self, pattern: LearnedPattern) -> None:
        """Add a pattern to the library"""
        # Check capacity
        if len(self.patterns) >= self.max_patterns:
            self._evict_weakest()

        # Store pattern
        self.patterns[pattern.pattern_id] = pattern

        # Update indices
        for cat in pattern.categories:
            self.by_category[cat].add(pattern.pattern_id)
        for kw in pattern.keywords:
            self.by_keyword[kw.lower()].add(pattern.pattern_id)
        self.by_type[pattern.pattern_type].add(pattern.pattern_id)

        self.patterns_created += 1

    def find_patterns(self, query: str,
                     category: str = None,
                     pattern_type: PatternType = None,
                     top_k: int = 5) -> List[LearnedPattern]:
        """Find relevant patterns"""
        candidates = set(self.patterns.keys())

        # Filter by category
        if category and category in self.by_category:
            candidates &= self.by_category[category]

        # Filter by type
        if pattern_type and pattern_type in self.by_type:
            candidates &= self.by_type[pattern_type]

        # Score by keyword overlap
        query_words = set(query.lower().split())
        scored = []

        for pid in candidates:
            pattern = self.patterns[pid]
            keyword_overlap = len(query_words & set(pattern.keywords))
            trigger_match = self._fuzzy_match(query, pattern.trigger)

            score = keyword_overlap * 0.3 + trigger_match * 0.4 + pattern.confidence * 0.3
            scored.append((score, pattern))

        # Sort and return top-k
        scored.sort(key=lambda x: -x[0])
        self.patterns_used += min(top_k, len(scored))

        return [p for _, p in scored[:top_k]]

    def update_pattern(self, pattern_id: str, success: bool) -> None:
        """Update pattern statistics after use"""
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.usage_count += 1
            if success:
                pattern.success_count += 1

            # Update confidence
            pattern.confidence = (pattern.confidence * 0.9 +
                                pattern.success_rate() * 0.1)

    def _fuzzy_match(self, query: str, trigger: str) -> float:
        """Fuzzy match score between query and trigger"""
        query_words = set(query.lower().split())
        trigger_words = set(trigger.lower().split())

        if not trigger_words:
            return 0.0

        overlap = len(query_words & trigger_words)
        return overlap / len(trigger_words)

    def _evict_weakest(self) -> None:
        """Remove weakest patterns to make room"""
        # Score patterns by value
        scored = []
        for pid, pattern in self.patterns.items():
            # Value = recency + success rate
            age = time.time() - pattern.created_at
            recency_score = 1.0 / (1.0 + age / 86400)  # Days
            value = recency_score * 0.3 + pattern.success_rate() * 0.7
            scored.append((value, pid))

        # Remove bottom 10%
        scored.sort()
        to_remove = len(scored) // 10

        for _, pid in scored[:to_remove]:
            self._remove_pattern(pid)

    def _remove_pattern(self, pattern_id: str) -> None:
        """Remove a pattern from library"""
        if pattern_id not in self.patterns:
            return

        pattern = self.patterns[pattern_id]

        # Remove from indices
        for cat in pattern.categories:
            self.by_category[cat].discard(pattern_id)
        for kw in pattern.keywords:
            self.by_keyword[kw.lower()].discard(pattern_id)
        self.by_type[pattern.pattern_type].discard(pattern_id)

        del self.patterns[pattern_id]


class FailureAnalyzer:
    """
    Analyzes failures to extract learnings.

    Identifies:
    - Common failure patterns
    - Missing knowledge areas
    - Strategy mismatches
    """

    def __init__(self):
        # Failure storage
        self.failures: List[LearningEvent] = []

        # Analysis results
        self.failure_categories: Dict[str, int] = defaultdict(int)
        self.failure_patterns: Dict[str, List[str]] = defaultdict(list)

        # Statistics
        self.analyses_performed = 0

    def record_failure(self, event: LearningEvent) -> None:
        """Record a failure for analysis"""
        self.failures.append(event)
        self.failure_categories[event.category] += 1

    def analyze(self, event: LearningEvent) -> Dict[str, Any]:
        """Analyze a single failure"""
        self.analyses_performed += 1

        analysis = {
            'event_id': event.event_id,
            'category': event.category,
            'failure_type': self._classify_failure(event),
            'possible_causes': self._identify_causes(event),
            'suggestions': self._generate_suggestions(event)
        }

        # Store pattern
        pattern_key = f"{event.category}_{analysis['failure_type']}"
        self.failure_patterns[pattern_key].append(event.event_id)

        return analysis

    def _classify_failure(self, event: LearningEvent) -> str:
        """Classify the type of failure"""
        # Check confidence
        if event.confidence < 0.3:
            return "low_confidence"

        # Check if answer was close
        if event.predicted_answer and event.correct_answer:
            pred_str = str(event.predicted_answer).lower()
            correct_str = str(event.correct_answer).lower()

            if pred_str in correct_str or correct_str in pred_str:
                return "partial_match"

        # Check reasoning trace
        if not event.reasoning_trace:
            return "no_reasoning"
        if len(event.reasoning_trace) < 2:
            return "insufficient_reasoning"

        # Check time
        if event.time_taken > 25:
            return "timeout_related"

        return "incorrect_reasoning"

    def _identify_causes(self, event: LearningEvent) -> List[str]:
        """Identify possible causes of failure"""
        causes = []

        # Knowledge gap
        if "unknown" in str(event.reasoning_trace).lower():
            causes.append("knowledge_gap")

        # Strategy mismatch
        if event.confidence > 0.7 and not event.was_correct:
            causes.append("overconfident_wrong_strategy")

        # Complexity
        if len(event.question) > 500:
            causes.append("high_complexity")

        # Category-specific issues
        if event.category == "Math" and not any(c.isdigit() for c in str(event.predicted_answer)):
            causes.append("missing_numeric_answer")

        if not causes:
            causes.append("unknown")

        return causes

    def _generate_suggestions(self, event: LearningEvent) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        failure_type = self._classify_failure(event)

        if failure_type == "low_confidence":
            suggestions.append("Use more reasoning samples")
            suggestions.append("Retrieve additional knowledge")

        elif failure_type == "partial_match":
            suggestions.append("Check answer format requirements")
            suggestions.append("Verify unit consistency")

        elif failure_type == "no_reasoning":
            suggestions.append("Force chain-of-thought reasoning")
            suggestions.append("Decompose problem into steps")

        elif failure_type == "timeout_related":
            suggestions.append("Use simpler strategy first")
            suggestions.append("Set tighter time limits")

        else:
            suggestions.append("Review reasoning trace for errors")
            suggestions.append("Try alternative strategy")

        return suggestions

    def get_weakness_report(self) -> Dict[str, Any]:
        """Generate report of weaknesses"""
        total = len(self.failures)
        if total == 0:
            return {'status': 'no_failures'}

        return {
            'total_failures': total,
            'by_category': dict(self.failure_categories),
            'worst_category': max(self.failure_categories.items(),
                                key=lambda x: x[1])[0] if self.failure_categories else None,
            'common_patterns': [
                (k, len(v)) for k, v in sorted(
                    self.failure_patterns.items(),
                    key=lambda x: -len(x[1])
                )[:5]
            ]
        }


class CurriculumManager:
    """
    Manages learning curriculum for self-improvement.

    Implements:
    - Difficulty progression
    - Weakness targeting
    - Spaced repetition
    """

    def __init__(self):
        # Curriculum items
        self.items: Dict[str, CurriculumItem] = {}

        # By difficulty tier
        self.by_difficulty: Dict[str, List[str]] = {
            'easy': [],
            'medium': [],
            'hard': [],
            'expert': []
        }

        # By category
        self.by_category: Dict[str, List[str]] = defaultdict(list)

        # Current learner state
        self.current_level: Dict[str, float] = {}  # category -> mastery
        self.items_completed: Set[str] = set()

    def add_item(self, item: CurriculumItem) -> None:
        """Add curriculum item"""
        self.items[item.item_id] = item
        self.by_category[item.category].append(item.item_id)

        # Classify by difficulty
        if item.difficulty < 0.25:
            self.by_difficulty['easy'].append(item.item_id)
        elif item.difficulty < 0.5:
            self.by_difficulty['medium'].append(item.item_id)
        elif item.difficulty < 0.75:
            self.by_difficulty['hard'].append(item.item_id)
        else:
            self.by_difficulty['expert'].append(item.item_id)

    def get_next_item(self, weakness_report: Dict = None) -> Optional[CurriculumItem]:
        """Get next curriculum item to study"""
        # Priority 1: Target weaknesses
        if weakness_report and weakness_report.get('worst_category'):
            weak_cat = weakness_report['worst_category']
            candidates = [iid for iid in self.by_category[weak_cat]
                        if iid not in self.items_completed]

            if candidates:
                # Get appropriate difficulty
                level = self.current_level.get(weak_cat, 0.3)
                best = self._find_appropriate(candidates, level)
                if best:
                    return self.items[best]

        # Priority 2: Progress in current level
        for category, level in sorted(self.current_level.items(), key=lambda x: x[1]):
            candidates = [iid for iid in self.by_category[category]
                        if iid not in self.items_completed]

            if candidates:
                best = self._find_appropriate(candidates, level)
                if best:
                    return self.items[best]

        # Priority 3: Any unmastered item
        for iid, item in self.items.items():
            if iid not in self.items_completed and item.mastery < 0.8:
                return item

        return None

    def _find_appropriate(self, candidates: List[str],
                         current_level: float) -> Optional[str]:
        """Find item at appropriate difficulty"""
        # Target difficulty slightly above current level
        target = min(1.0, current_level + 0.1)

        best_id = None
        best_diff = float('inf')

        for iid in candidates:
            item = self.items[iid]
            diff = abs(item.difficulty - target)
            if diff < best_diff:
                best_diff = diff
                best_id = iid

        return best_id

    def record_attempt(self, item_id: str, correct: bool) -> None:
        """Record an attempt on curriculum item"""
        if item_id not in self.items:
            return

        item = self.items[item_id]
        item.update_mastery(correct)

        # Update category level
        cat_items = [self.items[i] for i in self.by_category[item.category]]
        if cat_items:
            avg_mastery = sum(i.mastery for i in cat_items) / len(cat_items)
            self.current_level[item.category] = avg_mastery

        # Mark as completed if mastered
        if item.mastery >= 0.8:
            self.items_completed.add(item_id)

    def get_progress_report(self) -> Dict[str, Any]:
        """Get curriculum progress report"""
        total = len(self.items)
        completed = len(self.items_completed)

        return {
            'total_items': total,
            'completed': completed,
            'progress': completed / total if total > 0 else 0,
            'by_category': dict(self.current_level),
            'by_difficulty': {
                tier: len([iid for iid in items if iid in self.items_completed])
                for tier, items in self.by_difficulty.items()
            }
        }


class ContinuousLearner:
    """
    Main continuous learning system.

    Orchestrates:
    - Event recording
    - Pattern extraction
    - Failure analysis
    - Curriculum-based improvement
    """

    def __init__(self):
        self.pattern_library = PatternLibrary()
        self.failure_analyzer = FailureAnalyzer()
        self.curriculum_manager = CurriculumManager()

        # Event history
        self.events: List[LearningEvent] = []
        self.event_counter = 0

        # Statistics
        self.total_events = 0
        self.correct_count = 0
        self.patterns_extracted = 0

    def record_event(self, question: str,
                    predicted_answer: Any,
                    correct_answer: Any = None,
                    was_correct: bool = None,
                    category: str = "",
                    strategy: str = "",
                    confidence: float = 0.5,
                    reasoning_trace: List[str] = None,
                    time_taken: float = 0.0) -> LearningEvent:
        """Record a learning event"""
        self.event_counter += 1

        # Determine event type
        if was_correct is None and correct_answer is not None:
            was_correct = str(predicted_answer).lower().strip() == \
                         str(correct_answer).lower().strip()

        if was_correct:
            event_type = LearningEventType.SUCCESS
            self.correct_count += 1
        elif was_correct is False:
            event_type = LearningEventType.FAILURE
        else:
            event_type = LearningEventType.PARTIAL

        event = LearningEvent(
            event_id=f"event_{self.event_counter}",
            event_type=event_type,
            timestamp=time.time(),
            question=question,
            category=category,
            problem_hash=self._hash_question(question),
            predicted_answer=predicted_answer,
            correct_answer=correct_answer,
            was_correct=was_correct,
            strategy_used=strategy,
            confidence=confidence,
            reasoning_trace=reasoning_trace or [],
            time_taken=time_taken
        )

        self.events.append(event)
        self.total_events += 1

        # Process event
        self._process_event(event)

        return event

    def _hash_question(self, question: str) -> str:
        """Generate hash for question similarity lookup"""
        # Normalize
        normalized = question.lower().strip()
        # Remove common words
        words = [w for w in normalized.split()
                if len(w) > 3 and w not in {'what', 'which', 'that', 'this'}]
        # Hash
        return hashlib.md5(' '.join(sorted(words)).encode()).hexdigest()[:16]

    def _process_event(self, event: LearningEvent) -> None:
        """Process a learning event"""
        if event.event_type == LearningEventType.SUCCESS:
            # Extract pattern from success
            self._extract_success_pattern(event)
        elif event.event_type == LearningEventType.FAILURE:
            # Analyze failure
            self.failure_analyzer.record_failure(event)
            analysis = self.failure_analyzer.analyze(event)

            # Create error correction pattern
            self._create_error_pattern(event, analysis)

    def _extract_success_pattern(self, event: LearningEvent) -> None:
        """Extract pattern from successful solution"""
        # Create problem-solution pattern
        pattern = LearnedPattern(
            pattern_id=f"pattern_{self.patterns_extracted}",
            pattern_type=PatternType.PROBLEM_SOLUTION,
            created_at=time.time(),
            trigger=event.question[:200],
            response=str(event.predicted_answer),
            context={
                'strategy': event.strategy_used,
                'confidence': event.confidence
            },
            categories=[event.category] if event.category else [],
            keywords=self._extract_keywords(event.question)
        )

        self.pattern_library.add_pattern(pattern)
        self.patterns_extracted += 1

    def _create_error_pattern(self, event: LearningEvent,
                             analysis: Dict) -> None:
        """Create error correction pattern"""
        pattern = LearnedPattern(
            pattern_id=f"error_{self.patterns_extracted}",
            pattern_type=PatternType.ERROR_CORRECTION,
            created_at=time.time(),
            trigger=f"{event.category}: {analysis['failure_type']}",
            response="; ".join(analysis['suggestions']),
            context={
                'causes': analysis['possible_causes'],
                'original_answer': str(event.predicted_answer),
                'correct_answer': str(event.correct_answer)
            },
            categories=[event.category] if event.category else [],
            keywords=self._extract_keywords(event.question)
        )

        self.pattern_library.add_pattern(pattern)
        self.patterns_extracted += 1

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = text.lower().split()
        # Filter common words and short words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what',
                    'which', 'who', 'how', 'when', 'where', 'why', 'that',
                    'this', 'for', 'and', 'but', 'or', 'if', 'then', 'of',
                    'to', 'in', 'on', 'at', 'by', 'from', 'with'}

        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return list(set(keywords))[:10]

    def get_recommendations(self, question: str,
                           category: str = "") -> Dict[str, Any]:
        """Get recommendations for solving a problem"""
        # Find relevant patterns
        solution_patterns = self.pattern_library.find_patterns(
            question, category, PatternType.PROBLEM_SOLUTION
        )

        error_patterns = self.pattern_library.find_patterns(
            question, category, PatternType.ERROR_CORRECTION
        )

        # Get weakness info
        weakness = self.failure_analyzer.get_weakness_report()

        return {
            'similar_solutions': [p.to_dict() for p in solution_patterns[:3]],
            'pitfalls_to_avoid': [p.to_dict() for p in error_patterns[:2]],
            'category_weakness': weakness.get('by_category', {}).get(category, 0),
            'recommended_strategy': self._recommend_strategy(question, category)
        }

    def _recommend_strategy(self, question: str, category: str) -> str:
        """Recommend strategy based on learned patterns"""
        # Find successful strategy patterns
        patterns = self.pattern_library.find_patterns(
            question, category, PatternType.STRATEGY_SELECTION
        )

        if patterns:
            best = max(patterns, key=lambda p: p.success_rate())
            return best.response

        # Default recommendations by category
        defaults = {
            'Math': 'decomposition',
            'Physics': 'decomposition',
            'Chemistry': 'retrieval',
            'Biology': 'retrieval',
            'CS': 'formal_logic',
            'Humanities': 'retrieval',
        }

        return defaults.get(category, 'self_consistency')

    def improve_from_curriculum(self) -> Optional[Dict[str, Any]]:
        """Get next curriculum item and train on it"""
        weakness = self.failure_analyzer.get_weakness_report()
        item = self.curriculum_manager.get_next_item(weakness)

        if item:
            return {
                'item': item.item_id,
                'question': item.question,
                'category': item.category,
                'difficulty': item.difficulty
            }

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'total_events': self.total_events,
            'correct_rate': self.correct_count / self.total_events if self.total_events > 0 else 0,
            'patterns_stored': len(self.pattern_library.patterns),
            'patterns_used': self.pattern_library.patterns_used,
            'failures_analyzed': self.failure_analyzer.analyses_performed,
            'curriculum_progress': self.curriculum_manager.get_progress_report()
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ContinuousLearner',
    'LearningEvent',
    'LearningEventType',
    'PatternLibrary',
    'LearnedPattern',
    'PatternType',
    'FailureAnalyzer',
    'CurriculumManager',
    'CurriculumItem',
]
