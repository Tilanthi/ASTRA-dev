"""
Phase 4: Episodic Memory System

Enables learning from specific problem-solving experiences:
- Episode storage with rich context
- Relevant episode retrieval
- Pattern extraction across episodes
- Bayesian prior updating from experience
"""

import re
import math
import hashlib
import time
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict


class OutcomeType(Enum):
    """Types of problem-solving outcomes"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class ReasoningStrategy(Enum):
    """Reasoning strategies used"""
    DIRECT = "direct"
    DECOMPOSITION = "decomposition"
    ANALOGY = "analogy"
    HYPOTHESIS = "hypothesis"
    FORMAL = "formal"
    CAUSAL = "causal"
    RETRIEVAL = "retrieval"
    ENSEMBLE = "ensemble"


@dataclass
class Episode:
    """A single problem-solving episode"""
    episode_id: str
    timestamp: float
    problem: str
    category: str
    domain: str

    # Reasoning process
    reasoning_trace: List[str]
    strategies_used: List[ReasoningStrategy]
    intermediate_results: List[Dict[str, Any]]

    # Outcome
    answer: str
    outcome: OutcomeType
    confidence: float
    actual_correct: Optional[bool] = None

    # Context
    tools_used: List[str] = field(default_factory=list)
    knowledge_retrieved: List[str] = field(default_factory=list)
    similar_problems_referenced: List[str] = field(default_factory=list)

    # Metadata
    duration_seconds: float = 0.0
    difficulty_estimate: float = 0.5
    key_insights: List[str] = field(default_factory=list)
    failure_points: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'episode_id': self.episode_id,
            'timestamp': self.timestamp,
            'problem': self.problem,
            'category': self.category,
            'domain': self.domain,
            'answer': self.answer,
            'outcome': self.outcome.value,
            'confidence': self.confidence,
            'actual_correct': self.actual_correct,
            'strategies_used': [s.value for s in self.strategies_used],
            'tools_used': self.tools_used,
            'duration_seconds': self.duration_seconds,
            'difficulty_estimate': self.difficulty_estimate,
            'key_insights': self.key_insights,
            'failure_points': self.failure_points
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Episode':
        return cls(
            episode_id=data['episode_id'],
            timestamp=data['timestamp'],
            problem=data['problem'],
            category=data.get('category', ''),
            domain=data.get('domain', ''),
            reasoning_trace=data.get('reasoning_trace', []),
            strategies_used=[ReasoningStrategy(s) for s in data.get('strategies_used', [])],
            intermediate_results=data.get('intermediate_results', []),
            answer=data['answer'],
            outcome=OutcomeType(data['outcome']),
            confidence=data['confidence'],
            actual_correct=data.get('actual_correct'),
            tools_used=data.get('tools_used', []),
            knowledge_retrieved=data.get('knowledge_retrieved', []),
            similar_problems_referenced=data.get('similar_problems_referenced', []),
            duration_seconds=data.get('duration_seconds', 0.0),
            difficulty_estimate=data.get('difficulty_estimate', 0.5),
            key_insights=data.get('key_insights', []),
            failure_points=data.get('failure_points', [])
        )


@dataclass
class Pattern:
    """A pattern extracted from multiple episodes"""
    pattern_id: str
    name: str
    description: str

    # Pattern characteristics
    problem_signature: str  # Abstracted problem type
    successful_strategies: List[ReasoningStrategy]
    common_tools: List[str]
    typical_confidence: float

    # Supporting evidence
    supporting_episodes: List[str]  # Episode IDs
    success_rate: float
    sample_size: int

    # Conditions
    applicable_categories: Set[str]
    applicable_domains: Set[str]
    difficulty_range: Tuple[float, float]

    # Usage stats
    times_applied: int = 0
    application_success_rate: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'name': self.name,
            'description': self.description,
            'problem_signature': self.problem_signature,
            'successful_strategies': [s.value for s in self.successful_strategies],
            'common_tools': self.common_tools,
            'typical_confidence': self.typical_confidence,
            'supporting_episodes': self.supporting_episodes,
            'success_rate': self.success_rate,
            'sample_size': self.sample_size,
            'applicable_categories': list(self.applicable_categories),
            'applicable_domains': list(self.applicable_domains),
            'difficulty_range': self.difficulty_range,
            'times_applied': self.times_applied,
            'application_success_rate': self.application_success_rate
        }


class MemoryIndex:
    """
    Index for efficient episode retrieval.
    """

    def __init__(self):
        # Multiple indices for different retrieval needs
        self.by_category: Dict[str, List[str]] = defaultdict(list)
        self.by_domain: Dict[str, List[str]] = defaultdict(list)
        self.by_outcome: Dict[OutcomeType, List[str]] = defaultdict(list)
        self.by_strategy: Dict[ReasoningStrategy, List[str]] = defaultdict(list)
        self.by_keyword: Dict[str, List[str]] = defaultdict(list)

        # Temporal index
        self.chronological: List[Tuple[float, str]] = []

    def add(self, episode: Episode):
        """Add episode to indices"""
        eid = episode.episode_id

        # Category index
        self.by_category[episode.category.lower()].append(eid)

        # Domain index
        self.by_domain[episode.domain.lower()].append(eid)

        # Outcome index
        self.by_outcome[episode.outcome].append(eid)

        # Strategy index
        for strategy in episode.strategies_used:
            self.by_strategy[strategy].append(eid)

        # Keyword index
        keywords = self._extract_keywords(episode.problem)
        for keyword in keywords:
            self.by_keyword[keyword].append(eid)

        # Temporal index
        self.chronological.append((episode.timestamp, eid))
        self.chronological.sort()

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
                    'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                    'have', 'been', 'were', 'being', 'what', 'when', 'where',
                    'which', 'while', 'with', 'this', 'that', 'from', 'they'}
        return set(words) - stopwords

    def query(self, criteria: Dict[str, Any]) -> List[str]:
        """Query episodes matching criteria"""
        result_sets = []

        if 'category' in criteria:
            result_sets.append(set(self.by_category[criteria['category'].lower()]))

        if 'domain' in criteria:
            result_sets.append(set(self.by_domain[criteria['domain'].lower()]))

        if 'outcome' in criteria:
            result_sets.append(set(self.by_outcome[criteria['outcome']]))

        if 'strategy' in criteria:
            result_sets.append(set(self.by_strategy[criteria['strategy']]))

        if 'keywords' in criteria:
            keyword_matches = set()
            for kw in criteria['keywords']:
                keyword_matches.update(self.by_keyword.get(kw.lower(), []))
            if keyword_matches:
                result_sets.append(keyword_matches)

        if not result_sets:
            return [eid for _, eid in self.chronological]

        # Intersection of all criteria
        result = result_sets[0]
        for rs in result_sets[1:]:
            result &= rs

        return list(result)

    def get_recent(self, n: int = 10) -> List[str]:
        """Get n most recent episode IDs"""
        return [eid for _, eid in self.chronological[-n:]][::-1]


class PatternExtractor:
    """
    Extracts patterns from multiple episodes.
    """

    def __init__(self):
        self.min_episodes_for_pattern = 3

    def extract(self, episodes: List[Episode]) -> List[Pattern]:
        """
        Extract patterns from a list of episodes.

        Args:
            episodes: Episodes to analyze

        Returns:
            Extracted patterns
        """
        if len(episodes) < self.min_episodes_for_pattern:
            return []

        patterns = []

        # Group by outcome first
        successful = [e for e in episodes if e.outcome == OutcomeType.SUCCESS]
        failed = [e for e in episodes if e.outcome == OutcomeType.FAILURE]

        # Extract success patterns
        if len(successful) >= self.min_episodes_for_pattern:
            success_patterns = self._extract_from_group(successful, "success")
            patterns.extend(success_patterns)

        # Extract failure patterns (anti-patterns)
        if len(failed) >= self.min_episodes_for_pattern:
            failure_patterns = self._extract_from_group(failed, "failure")
            patterns.extend(failure_patterns)

        # Extract category-specific patterns
        category_groups = defaultdict(list)
        for e in episodes:
            category_groups[e.category].append(e)

        for category, cat_episodes in category_groups.items():
            if len(cat_episodes) >= self.min_episodes_for_pattern:
                cat_patterns = self._extract_from_group(
                    cat_episodes, f"category_{category}"
                )
                patterns.extend(cat_patterns)

        return patterns

    def _extract_from_group(self, episodes: List[Episode], group_name: str) -> List[Pattern]:
        """Extract patterns from a group of episodes"""
        patterns = []

        # Find common strategies
        strategy_counts = defaultdict(int)
        for e in episodes:
            for s in e.strategies_used:
                strategy_counts[s] += 1

        # Strategies appearing in majority of episodes
        threshold = len(episodes) / 2
        common_strategies = [s for s, c in strategy_counts.items() if c >= threshold]

        # Find common tools
        tool_counts = defaultdict(int)
        for e in episodes:
            for t in e.tools_used:
                tool_counts[t] += 1
        common_tools = [t for t, c in tool_counts.items() if c >= threshold]

        # Calculate success rate
        successes = sum(1 for e in episodes if e.outcome == OutcomeType.SUCCESS)
        success_rate = successes / len(episodes)

        # Calculate typical confidence
        avg_confidence = sum(e.confidence for e in episodes) / len(episodes)

        # Collect categories and domains
        categories = {e.category for e in episodes if e.category}
        domains = {e.domain for e in episodes if e.domain}

        # Difficulty range
        difficulties = [e.difficulty_estimate for e in episodes]
        diff_range = (min(difficulties), max(difficulties))

        # Generate problem signature
        signature = self._generate_signature(episodes)

        # Create pattern
        pattern_id = hashlib.md5(f"{group_name}_{signature}".encode()).hexdigest()[:12]

        pattern = Pattern(
            pattern_id=pattern_id,
            name=f"Pattern_{group_name}",
            description=f"Pattern from {len(episodes)} episodes in {group_name}",
            problem_signature=signature,
            successful_strategies=common_strategies,
            common_tools=common_tools,
            typical_confidence=avg_confidence,
            supporting_episodes=[e.episode_id for e in episodes],
            success_rate=success_rate,
            sample_size=len(episodes),
            applicable_categories=categories,
            applicable_domains=domains,
            difficulty_range=diff_range
        )

        patterns.append(pattern)

        return patterns

    def _generate_signature(self, episodes: List[Episode]) -> str:
        """Generate a problem signature from episodes"""
        # Extract common structural elements
        all_keywords = []
        for e in episodes:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', e.problem.lower())
            all_keywords.extend(words)

        # Find most common keywords
        keyword_counts = defaultdict(int)
        for kw in all_keywords:
            keyword_counts[kw] += 1

        top_keywords = sorted(keyword_counts.items(), key=lambda x: -x[1])[:5]
        signature = '_'.join(kw for kw, _ in top_keywords)

        return signature if signature else "general"


class BayesianPriorUpdater:
    """
    Updates Bayesian priors based on episodes.
    """

    def __init__(self):
        # Prior distributions for various quantities
        self.category_success_priors: Dict[str, Tuple[float, float]] = {}  # Beta(a, b)
        self.strategy_effectiveness: Dict[ReasoningStrategy, Tuple[float, float]] = {}
        self.difficulty_priors: Dict[str, Tuple[float, float]] = {}  # Normal(mu, sigma)

        # Initialize with uniform priors
        self._initialize_priors()

    def _initialize_priors(self):
        """Initialize with uninformative priors"""
        # Beta(1, 1) = Uniform
        for strategy in ReasoningStrategy:
            self.strategy_effectiveness[strategy] = (1.0, 1.0)

    def update_from_episode(self, episode: Episode):
        """Update priors based on a single episode"""
        # Update category success prior
        category = episode.category.lower()
        if category not in self.category_success_priors:
            self.category_success_priors[category] = (1.0, 1.0)

        a, b = self.category_success_priors[category]
        if episode.actual_correct or episode.outcome == OutcomeType.SUCCESS:
            self.category_success_priors[category] = (a + 1, b)
        else:
            self.category_success_priors[category] = (a, b + 1)

        # Update strategy effectiveness
        for strategy in episode.strategies_used:
            a, b = self.strategy_effectiveness[strategy]
            if episode.outcome == OutcomeType.SUCCESS:
                self.strategy_effectiveness[strategy] = (a + 1, b)
            elif episode.outcome == OutcomeType.FAILURE:
                self.strategy_effectiveness[strategy] = (a, b + 1)

    def update_from_episodes(self, episodes: List[Episode]):
        """Update priors from multiple episodes"""
        for episode in episodes:
            self.update_from_episode(episode)

    def get_category_prior(self, category: str) -> float:
        """Get expected success probability for a category"""
        category = category.lower()
        if category not in self.category_success_priors:
            return 0.5  # Uniform prior

        a, b = self.category_success_priors[category]
        return a / (a + b)  # Expected value of Beta distribution

    def get_strategy_effectiveness(self, strategy: ReasoningStrategy) -> float:
        """Get expected effectiveness for a strategy"""
        a, b = self.strategy_effectiveness[strategy]
        return a / (a + b)

    def get_best_strategies(self, k: int = 3) -> List[Tuple[ReasoningStrategy, float]]:
        """Get k best strategies by effectiveness"""
        effectiveness = [
            (s, self.get_strategy_effectiveness(s))
            for s in self.strategy_effectiveness.keys()
        ]
        effectiveness.sort(key=lambda x: -x[1])
        return effectiveness[:k]

    def get_prior_confidence(self, category: str) -> float:
        """Get confidence in the prior (based on sample size)"""
        category = category.lower()
        if category not in self.category_success_priors:
            return 0.1  # Low confidence for unknown categories

        a, b = self.category_success_priors[category]
        n = a + b - 2  # Subtract initial priors

        # Confidence increases with sample size
        return min(0.95, 0.1 + 0.85 * (1 - math.exp(-n / 20)))


class EpisodicMemory:
    """
    Main episodic memory system.

    Stores, retrieves, and learns from problem-solving episodes.
    """

    def __init__(self, max_episodes: int = 10000):
        """
        Initialize episodic memory.

        Args:
            max_episodes: Maximum episodes to store
        """
        self.max_episodes = max_episodes

        # Episode storage
        self.episodes: Dict[str, Episode] = {}

        # Index for retrieval
        self.index = MemoryIndex()

        # Pattern extraction
        self.pattern_extractor = PatternExtractor()
        self.patterns: Dict[str, Pattern] = {}

        # Bayesian priors
        self.prior_updater = BayesianPriorUpdater()

        # Statistics
        self.stats = {
            'episodes_stored': 0,
            'episodes_retrieved': 0,
            'patterns_extracted': 0,
            'priors_updated': 0
        }

    def store_episode(self, episode: Episode):
        """
        Store an episode in memory.

        Args:
            episode: Episode to store
        """
        # Check capacity
        if len(self.episodes) >= self.max_episodes:
            self._evict_oldest()

        # Store episode
        self.episodes[episode.episode_id] = episode

        # Update index
        self.index.add(episode)

        # Update priors
        self.prior_updater.update_from_episode(episode)
        self.stats['priors_updated'] += 1

        self.stats['episodes_stored'] += 1

    def _evict_oldest(self):
        """Evict oldest episode to make room"""
        if not self.index.chronological:
            return

        # Find oldest
        oldest_time, oldest_id = self.index.chronological[0]

        # Remove from storage
        if oldest_id in self.episodes:
            del self.episodes[oldest_id]

        # Remove from chronological index (full rebuild would be cleaner but slower)
        self.index.chronological = self.index.chronological[1:]

    def retrieve_relevant(self, problem: str, category: str = "",
                         k: int = 5) -> List[Episode]:
        """
        Retrieve relevant episodes for a problem.

        Args:
            problem: Current problem
            category: Optional category hint
            k: Number of episodes to retrieve

        Returns:
            List of relevant episodes
        """
        # Extract query features
        keywords = self._extract_keywords(problem)

        # Build query criteria
        criteria = {'keywords': list(keywords)}
        if category:
            criteria['category'] = category

        # Query index
        candidate_ids = self.index.query(criteria)

        # Score and rank candidates
        scored = []
        for eid in candidate_ids:
            if eid in self.episodes:
                episode = self.episodes[eid]
                score = self._relevance_score(problem, episode, keywords)
                scored.append((score, episode))

        # Sort by score
        scored.sort(key=lambda x: -x[0])

        self.stats['episodes_retrieved'] += min(k, len(scored))

        return [ep for _, ep in scored[:k]]

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
                    'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                    'have', 'been', 'were', 'being', 'what', 'when', 'where',
                    'which', 'while', 'with', 'this', 'that', 'from', 'they'}
        return set(words) - stopwords

    def _relevance_score(self, query: str, episode: Episode,
                        query_keywords: Set[str]) -> float:
        """Calculate relevance score for an episode"""
        score = 0.0

        # Keyword overlap
        episode_keywords = self._extract_keywords(episode.problem)
        if query_keywords and episode_keywords:
            overlap = len(query_keywords & episode_keywords)
            score += 0.4 * (overlap / max(len(query_keywords), 1))

        # Outcome bonus (prefer successful episodes)
        if episode.outcome == OutcomeType.SUCCESS:
            score += 0.2

        # Recency bonus
        recency = 1.0 / (1.0 + (time.time() - episode.timestamp) / 86400)  # Decay per day
        score += 0.2 * recency

        # Confidence bonus
        score += 0.2 * episode.confidence

        return score

    def extract_patterns(self, min_episodes: int = 5) -> List[Pattern]:
        """
        Extract patterns from stored episodes.

        Args:
            min_episodes: Minimum episodes required for pattern extraction

        Returns:
            Newly extracted patterns
        """
        if len(self.episodes) < min_episodes:
            return []

        episodes = list(self.episodes.values())
        patterns = self.pattern_extractor.extract(episodes)

        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern
            self.stats['patterns_extracted'] += 1

        return patterns

    def get_applicable_patterns(self, problem: str, category: str = "") -> List[Pattern]:
        """
        Find patterns applicable to a problem.

        Args:
            problem: Current problem
            category: Optional category

        Returns:
            Applicable patterns
        """
        applicable = []

        for pattern in self.patterns.values():
            # Check category match
            if category and category.lower() not in {c.lower() for c in pattern.applicable_categories}:
                continue

            # Check success rate threshold
            if pattern.success_rate < 0.3:
                continue

            applicable.append(pattern)

        # Sort by success rate
        applicable.sort(key=lambda p: -p.success_rate)

        return applicable

    def get_strategy_recommendation(self, problem: str, category: str = "") -> Dict[str, Any]:
        """
        Get strategy recommendation based on experience.

        Args:
            problem: Current problem
            category: Optional category

        Returns:
            Strategy recommendation with confidence
        """
        # Get best overall strategies
        best_strategies = self.prior_updater.get_best_strategies(3)

        # Get category-specific prior
        category_success = self.prior_updater.get_category_prior(category)
        prior_confidence = self.prior_updater.get_prior_confidence(category)

        # Find similar successful episodes
        successful_episodes = self.retrieve_relevant(problem, category, k=5)
        successful_episodes = [e for e in successful_episodes if e.outcome == OutcomeType.SUCCESS]

        # Extract strategies from successful similar problems
        similar_strategies = defaultdict(int)
        for ep in successful_episodes:
            for s in ep.strategies_used:
                similar_strategies[s] += 1

        # Combine evidence
        recommended_strategies = []
        for strategy, effectiveness in best_strategies:
            similar_count = similar_strategies.get(strategy, 0)
            combined_score = 0.5 * effectiveness + 0.5 * (similar_count / max(len(successful_episodes), 1))
            recommended_strategies.append((strategy, combined_score))

        recommended_strategies.sort(key=lambda x: -x[1])

        return {
            'recommended_strategies': [
                {'strategy': s.value, 'score': score}
                for s, score in recommended_strategies
            ],
            'expected_success_rate': category_success,
            'confidence': prior_confidence,
            'based_on_episodes': len(successful_episodes),
            'supporting_patterns': len(self.get_applicable_patterns(problem, category))
        }

    def record_outcome(self, episode_id: str, was_correct: bool):
        """
        Record actual outcome for an episode.

        Args:
            episode_id: Episode ID
            was_correct: Whether answer was correct
        """
        if episode_id in self.episodes:
            self.episodes[episode_id].actual_correct = was_correct

            # Update outcome if different
            if was_correct and self.episodes[episode_id].outcome != OutcomeType.SUCCESS:
                self.episodes[episode_id].outcome = OutcomeType.SUCCESS
            elif not was_correct and self.episodes[episode_id].outcome == OutcomeType.SUCCESS:
                self.episodes[episode_id].outcome = OutcomeType.FAILURE

            # Re-update priors
            self.prior_updater.update_from_episode(self.episodes[episode_id])

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            **self.stats,
            'total_episodes': len(self.episodes),
            'total_patterns': len(self.patterns),
            'category_count': len(self.index.by_category),
            'domain_count': len(self.index.by_domain)
        }

    def save_to_file(self, filepath: str):
        """Save memory to file"""
        data = {
            'episodes': {eid: ep.to_dict() for eid, ep in self.episodes.items()},
            'patterns': {pid: p.to_dict() for pid, p in self.patterns.items()},
            'stats': self.stats
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: str):
        """Load memory from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Load episodes
        for eid, ep_data in data.get('episodes', {}).items():
            episode = Episode.from_dict(ep_data)
            self.episodes[eid] = episode
            self.index.add(episode)
            self.prior_updater.update_from_episode(episode)

        # Load stats
        self.stats = data.get('stats', self.stats)

    def create_episode(self, problem: str, answer: str, reasoning_trace: List[str],
                      strategies_used: List[str], category: str = "",
                      domain: str = "", confidence: float = 0.5,
                      outcome: str = "unknown", **kwargs) -> Episode:
        """
        Helper to create and store an episode.

        Args:
            problem: Problem text
            answer: Answer given
            reasoning_trace: Reasoning steps
            strategies_used: Names of strategies used
            category: Problem category
            domain: Problem domain
            confidence: Confidence in answer
            outcome: Outcome type
            **kwargs: Additional episode fields

        Returns:
            Created episode
        """
        # Generate episode ID
        episode_id = hashlib.md5(
            f"{problem[:100]}_{time.time()}".encode()
        ).hexdigest()
        return episode_id
