"""
Abstraction Memory for Cognitive-Relativity Navigator

Stores abstraction hierarchies with multi-level relationships,
enabling efficient zoom operations and abstraction management.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class AbstractionType(Enum):
    """Types of abstraction content"""
    FACT = "fact"              # Atomic, verifiable fact
    CONCEPT = "concept"        # Abstract concept
    PRINCIPLE = "principle"    # General principle
    THEORY = "theory"          # Theoretical framework
    PHILOSOPHY = "philosophy"  # High-level philosophy


@dataclass
class AbstractionContent:
    """Content at an abstraction level"""
    content_type: AbstractionType
    text: str
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AbstractionEdge:
    """Relationship between abstraction levels"""
    parent_level: str
    child_level: str
    edge_type: str  # "generalizes", "specializes", "exemplifies"
    strength: float
    compression_ratio: float  # How much info is compressed


@dataclass
class AbstractionQuery:
    """A query with associated abstraction preferences"""
    query_text: str
    preferred_height: int  # 0-100
    height_tolerance: int = 20
    temporal_context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZoomPath:
    """A path through abstraction levels"""
    levels: List[str]
    total_height_delta: int
    compression_ratios: List[float]
    estimated_quality: float


class AbstractionMemory:
    """
    Stores and manages abstraction hierarchies.

    Enables efficient storage and retrieval of multi-level
    abstractions with parent-child relationships.
    """

    def __init__(self):
        # level_id -> content
        self.levels: Dict[str, AbstractionContent] = {}

        # level_id -> height (0-100)
        self.heights: Dict[str, int] = {}

        # level_id -> children
        self.children: Dict[str, List[str]] = {}

        # level_id -> parent
        self.parents: Dict[str, str] = {}

        # Edges for detailed relationships
        self.edges: List[AbstractionEdge] = []

        # height -> list of level_ids
        self.height_index: Dict[int, List[str]] = {}

        # keyword -> level_ids
        self.keyword_index: Dict[str, Set[str]] = {}

        # Access tracking
        self.access_count: Dict[str, int] = {}
        self.last_access: Dict[str, float] = {}

    def add_level(
        self,
        level_id: str,
        height: int,
        content: AbstractionContent
    ) -> None:
        """Add an abstraction level."""
        if level_id in self.levels:
            return

        self.levels[level_id] = content
        self.heights[level_id] = height
        self.children[level_id] = []
        self.access_count[level_id] = 0
        self.last_access[level_id] = time.time()

        # Index by height
        if height not in self.height_index:
            self.height_index[height] = []
        self.height_index[height].append(level_id)

        # Index by keywords
        for keyword in content.keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()
            self.keyword_index[keyword].add(level_id)

    def add_relationship(
        self,
        parent_id: str,
        child_id: str,
        edge_type: str = "generalizes",
        strength: float = 1.0,
        compression_ratio: float = 1.0
    ) -> None:
        """Add a parent-child relationship."""
        if parent_id not in self.levels or child_id not in self.levels:
            return

        self.children[parent_id].append(child_id)
        self.parents[child_id] = parent_id

        edge = AbstractionEdge(
            parent_level=parent_id,
            child_level=child_id,
            edge_type=edge_type,
            strength=strength,
            compression_ratio=compression_ratio
        )
        self.edges.append(edge)

    def get_level(self, level_id: str) -> Optional[AbstractionContent]:
        """Get content for a level."""
        if level_id in self.levels:
            self.access_count[level_id] += 1
            self.last_access[level_id] = time.time()
            return self.levels[level_id]
        return None

    def get_children(self, level_id: str) -> List[str]:
        """Get children of a level."""
        return self.children.get(level_id, [])

    def get_parent(self, level_id: str) -> Optional[str]:
        """Get parent of a level."""
        return self.parents.get(level_id)

    def get_levels_at_height(
        self,
        target_height: int,
        tolerance: int = 0
    ) -> List[Tuple[str, AbstractionContent]]:
        """Get all levels within a height range."""
        results = []

        for h in range(target_height - tolerance, target_height + tolerance + 1):
            if h in self.height_index:
                for level_id in self.height_index[h]:
                    if level_id in self.levels:
                        results.append((level_id, self.levels[level_id]))

        return results

    def find_path(
        self,
        from_level: str,
        to_height: int
    ) -> Optional[ZoomPath]:
        """Find a path from one level to another height."""
        if from_level not in self.levels:
            return None

        current_height = self.heights.get(from_level, 50)
        height_delta = to_height - current_height

        if height_delta == 0:
            return ZoomPath(
                levels=[from_level],
                total_height_delta=0,
                compression_ratios=[],
                estimated_quality=1.0
            )

        path = [from_level]
        ratios = []
        current = from_level

        if height_delta > 0:
            # Zoom out (move to parents)
            while current and self.heights.get(current, 50) < to_height:
                parent = self.parents.get(current)
                if not parent:
                    break
                path.append(parent)
                ratios.append(self._get_compression_ratio(current, parent))
                current = parent
        else:
            # Zoom in (move to children)
            while current and self.heights.get(current, 50) > to_height:
                children = self.children.get(current, [])
                if not children:
                    break
                # Pick child closest to target height
                best_child = min(
                    children,
                    key=lambda c: abs(self.heights.get(c, 50) - to_height)
                )
                path.append(best_child)
                ratios.append(self._get_compression_ratio(best_child, current))
                current = best_child

        if len(path) > 1:
            return ZoomPath(
                levels=path,
                total_height_delta=height_delta,
                compression_ratios=ratios,
                estimated_quality=self._estimate_path_quality(path, ratios)
            )

        return None

    def _get_compression_ratio(self, child: str, parent: str) -> float:
        """Get compression ratio between child and parent."""
        for edge in self.edges:
            if edge.child_level == child and edge.parent_level == parent:
                return edge.compression_ratio
        return 1.0

    def _estimate_path_quality(self, path: List[str], ratios: List[float]) -> float:
        """Estimate quality of a zoom path."""
        if not ratios:
            return 1.0

        # Quality decreases with more hops and high compression
        hop_penalty = 1.0 - (len(path) - 1) * 0.05
        compression_penalty = 1.0 - sum(ratios) / len(ratios) * 0.2

        return max(0.0, min(1.0, hop_penalty * compression_penalty))

    def search_by_keywords(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """Search levels by keyword relevance."""
        scores = defaultdict(float)

        for keyword in keywords:
            if keyword in self.keyword_index:
                for level_id in self.keyword_index[keyword]:
                    scores[level_id] += 1.0

        # Normalize by number of keywords
        for level_id in scores:
            scores[level_id] /= len(keywords)

        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def get_level_range(
        self,
        min_height: int,
        max_height: int
    ) -> List[Tuple[str, int, AbstractionContent]]:
        """Get all levels in a height range."""
        results = []

        for h in range(min_height, max_height + 1):
            if h in self.height_index:
                for level_id in self.height_index[h]:
                    if level_id in self.levels:
                        results.append((
                            level_id,
                            h,
                            self.levels[level_id]
                        ))

        return sorted(results, key=lambda x: x[1])

    def compress_levels(
        self,
        start_level: str,
        end_level: str
    ) -> Optional[AbstractionContent]:
        """Create compressed abstraction from range of levels."""
        if start_level not in self.levels or end_level not in self.levels:
            return None

        # Collect all levels in range
        path = self.find_path(start_level, self.heights[end_level])
        if not path:
            return None

        # Combine content
        all_text = []
        all_keywords = set()
        all_examples = []

        for level_id in path.levels:
            content = self.levels.get(level_id)
            if content:
                all_text.append(content.text)
                all_keywords.update(content.keywords)
                all_examples.extend(content.examples)

        # Determine dominant type
        type_counts = defaultdict(int)
        for level_id in path.levels:
            content = self.levels.get(level_id)
            if content:
                type_counts[content.content_type] += 1

        dominant_type = max(type_counts, key=type_counts.get) if type_counts else AbstractionType.CONCEPT

        return AbstractionContent(
            content_type=dominant_type,
            text=" | ".join(all_text),
            keywords=list(all_keywords),
            examples=all_examples[:10],  # Limit examples
            relationships=[f"Compressed from {len(path.levels)} levels"]
        )

    def expand_level(
        self,
        level_id: str,
        depth: int = 1
    ) -> List[Tuple[str, AbstractionContent]]:
        """Expand a level into its children."""
        results = []

        if level_id not in self.levels:
            return results

        # BFS to get children at specified depth
        from collections import deque

        queue = deque([(level_id, 0)])
        visited = set()

        while queue:
            current, d = queue.popleft()

            if d > depth or current in visited:
                continue

            visited.add(current)

            if current != level_id and current in self.levels:
                results.append((current, self.levels[current]))

            for child in self.children.get(current, []):
                queue.append((child, d + 1))

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_levels = len(self.levels)
        total_edges = len(self.edges)

        height_distribution = defaultdict(int)
        for h in self.heights.values():
            height_distribution[h] += 1

        avg_access = sum(self.access_count.values()) / total_levels if total_levels > 0 else 0

        return {
            "total_levels": total_levels,
            "total_edges": total_edges,
            "height_distribution": dict(height_distribution),
            "average_access_count": avg_access,
            "root_levels": len([l for l in self.levels if l not in self.parents]),
            "leaf_levels": len([l for l in self.levels if l not in self.children or not self.children[l]])
        }

    def prune_unreachable(self) -> int:
        """Remove levels not reachable from any root."""
        # Find all roots (levels without parents)
        roots = [
            level_id for level_id in self.levels
            if level_id not in self.parents
        ]

        # BFS from roots to find reachable
        reachable = set()
        from collections import deque

        for root in roots:
            queue = deque([root])
            while queue:
                current = queue.popleft()
                if current in reachable:
                    continue
                reachable.add(current)
                queue.extend(self.children.get(current, []))

        # Remove unreachable
        to_remove = set(self.levels.keys()) - reachable
        for level_id in to_remove:
            self.remove_level(level_id)

        return len(to_remove)

    def remove_level(self, level_id: str) -> bool:
        """Remove a level and its relationships."""
        if level_id not in self.levels:
            return False

        # Remove from parent's children
        parent = self.parents.get(level_id)
        if parent and parent in self.children:
            self.children[parent] = [c for c in self.children[parent] if c != level_id]

        # Remove from children's parents
        for child in self.children.get(level_id, []):
            if child in self.parents:
                del self.parents[child]

        # Remove from indexes
        h = self.heights.get(level_id)
        if h and h in self.height_index:
            self.height_index[h] = [l for l in self.height_index[h] if l != level_id]

        for keyword, level_ids in self.keyword_index.items():
            level_ids.discard(level_id)

        # Remove
        del self.levels[level_id]
        del self.heights[level_id]
        del self.children[level_id]
        if level_id in self.parents:
            del self.parents[level_id]
        if level_id in self.access_count:
            del self.access_count[level_id]
        if level_id in self.last_access:
            del self.last_access[level_id]

        self.edges = [e for e in self.edges if e.parent_level != level_id and e.child_level != level_id]

        return True


# =============================================================================
# Factory Functions
# =============================================================================

def create_abstraction_memory() -> AbstractionMemory:
    """Create an abstraction memory."""
    return AbstractionMemory()



def build_abstraction_hierarchy(examples: List[Dict[str, Any]],
                                max_levels: int = 4) -> Dict[str, Any]:
    """
    Build hierarchical abstractions from concrete examples.

    Creates levels of abstraction from specific instances to universal principles.

    Args:
        examples: List of concrete examples with features
        max_levels: Maximum levels of abstraction

    Returns:
        Dictionary with hierarchical abstractions
    """
    import numpy as np
    from collections import defaultdict

    hierarchy = {
        'level_0_instances': examples,
        'level_1_concepts': [],
        'level_2_patterns': [],
        'level_3_principles': []
    }

    # Level 1: Group similar instances into concepts
    feature_vectors = []
    for ex in examples:
        features = _extract_features(ex)
        feature_vectors.append(features)

    # Cluster by similarity
    if len(feature_vectors) > 1:
        clusters = _cluster_by_similarity(feature_vectors, n_clusters=min(5, len(examples)))

        for cluster_id in range(max(clusters) + 1):
            cluster_examples = [ex for ex, c in zip(examples, clusters) if c == cluster_id]
            if cluster_examples:
                concept = _form_concept(cluster_examples)
                hierarchy['level_1_concepts'].append(concept)

    # Level 2: Extract patterns across concepts
    if hierarchy['level_1_concepts']:
        for i, concept1 in enumerate(hierarchy['level_1_concepts']):
            for concept2 in hierarchy['level_1_concepts'][i+1:]:
                pattern = _find_common_pattern([concept1, concept2])
                if pattern and pattern not in hierarchy['level_2_patterns']:
                    hierarchy['level_2_patterns'].append(pattern)

    # Level 3: Abstract universal principles
    if hierarchy['level_2_patterns']:
        principle = _extract_principle(hierarchy['level_2_patterns'])
        if principle:
            hierarchy['level_3_principles'].append(principle)

    return hierarchy


def _extract_features(example: Dict[str, Any]) -> np.ndarray:
    """Extract feature vector from example."""
    features = []

    # Extract numeric features
    for v in example.values():
        if isinstance(v, (int, float)):
            features.append(v)
        elif isinstance(v, str):
            # Simple string encoding
            features.append(len(v) / 100.0)
        elif isinstance(v, list):
            features.append(len(v))
        elif isinstance(v, dict):
            features.append(len(v))

    return np.array(features[:10] if len(features) > 10 else features + [0.0] * (10 - len(features)))


def _cluster_by_similarity(vectors: List[np.ndarray],
                           n_clusters: int = 3) -> List[int]:
    """Cluster vectors by similarity."""
    import numpy as np
    from sklearn.cluster import KMeans

    # Pad vectors to same length
    max_len = max(len(v) for v in vectors)
    padded = []
    for v in vectors:
        if len(v) < max_len:
            padded_v = np.pad(v, (0, max_len - len(v)), 'constant')
        else:
            padded_v = v[:max_len]
        padded.append(padded_v)

    X = np.array(padded)

    if len(X) >= n_clusters:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X)
    else:
        clusters = list(range(len(X)))

    return list(clusters)


def _form_concept(examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Form a concept from a group of examples."""
    common_features = {}

    for key in examples[0].keys():
        values = [ex.get(key) for ex in examples]
        if values and all(v == values[0] for v in values):
            common_features[key] = values[0]

    return {
        'name': f"concept_{id(examples)}",
        'common_features': common_features,
        'num_instances': len(examples),
        'examples': examples[:2]  # Keep representative examples
    }


def _find_common_pattern(concepts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find common pattern across concepts."""
    import numpy as np

    if len(concepts) < 2:
        return None

    pattern = {
        'name': f"pattern_{id(concepts)}",
        'source_concepts': len(concepts),
        'abstraction_level': 2
    }

    return pattern


def _extract_principle(patterns: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Extract universal principle from patterns."""
    if not patterns:
        return None

    return {
        'name': f"principle_{id(patterns)}",
        'num_patterns': len(patterns),
        'abstraction_level': 3,
        'generality': len(patterns) / 10.0
    }



def form_concept_from_examples(examples: List[Dict[str, Any]],
                              concept_name: str = None) -> Dict[str, Any]:
    """
    Form a concept from concrete examples.

    Args:
        examples: List of examples
        concept_name: Optional name for the concept

    Returns:
        Concept definition with essential features
    """
    import numpy as np
    from collections import Counter

    if not examples:
        return None

    # Extract common features
    all_features = {}
    feature_counts = Counter()

    for example in examples:
        for key, value in example.items():
            if key not in all_features:
                all_features[key] = []
            all_features[key].append(value)
            feature_counts[key] += 1

    # Identify essential features (present in most examples)
    essential_features = {}
    for key, values in all_features.items():
        if feature_counts[key] >= len(examples) * 0.7:  # Present in 70%+ examples
            # For continuous: compute mean
            if all(isinstance(v, (int, float)) for v in values):
                essential_features[key] = {
                    'type': 'continuous',
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'range': [float(np.min(values)), float(np.max(values))]
                }
            # For categorical: most common
            else:
                counter = Counter(values)
                essential_features[key] = {
                    'type': 'categorical',
                    'most_common': counter.most_common(1)[0][0],
                    'frequency': counter.most_common(1)[0][1] / len(values)
                }

    concept = {
        'name': concept_name or f"concept_{id(examples)}",
        'essential_features': essential_features,
        'num_examples': len(examples),
        'coverage': len(essential_features) / len(all_features) if all_features else 0,
        'examples': examples[:3]  # Keep representative examples
    }

    return concept



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """
    Detect patterns using autocorrelation analysis.

    Args:
        data: Input signal
        max_lag: Maximum lag to check (None for len(data)//4)

    Returns:
        Dictionary with autocorrelation results and detected periods
    """
    import numpy as np

    if max_lag is None:
        max_lag = len(data) // 4

    # Compute autocorrelation
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]

    # Normalize
    autocorr = autocorr / autocorr[0]

    # Find peaks
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(autocorr[:max_lag], height=0.2)

    # Estimate periods from peaks
    periods = []
    for peak in peaks:
        if peak > 0:
            periods.append(peak)

    return {
        'autocorrelation': autocorr[:max_lag],
        'peaks': peaks.tolist(),
        'periods': periods,
        'dominant_period': periods[0] if periods else None
    }



def detect_change_points(data: np.ndarray, min_size: int = 10, penalty: float = 1.0) -> List[int]:
    """
    Detect change points in time series data.

    Args:
        data: Input time series
        min_size: Minimum segment size between change points
        penalty: Penalty for additional change points

    Returns:
        List of change point indices
    """
    import numpy as np

    n = len(data)
    change_points = []

    # Compute cumulative statistics
    cumsum = np.cumsum(data)
    cumsum_sq = np.cumsum(data**2)

    # Scan for change points
    i = min_size
    while i < n - min_size:
        # Check if there's a significant change at position i
        before_mean = cumsum[i] / i
        after_mean = (cumsum[n-1] - cumsum[i]) / (n - i)

        before_var = (cumsum_sq[i] / i) - before_mean**2
        after_var = ((cumsum_sq[n-1] - cumsum_sq[i]) / (n - i)) - after_mean**2

        # Test for significant change
        if abs(before_mean - after_mean) > penalty * np.sqrt(before_var + after_var + 1e-10):
            change_points.append(i)
            i += min_size  # Skip ahead
        else:
            i += 1

    return change_points



def direct_lingam(data: np.ndarray) -> Dict[str, Any]:
    """
    Apply DirectLiNGAM algorithm for causal discovery.

    Uses non-Gaussianity to estimate causal order and structure.

    Args:
        data: Data matrix (n_samples x n_variables)

    Returns:
        Dictionary with causal matrix and causal order
    """
    import numpy as np

    n_samples, n_vars = data.shape

    # Standardize data
    data = (data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-10)

    # Initialize
    causal_order = []
    remaining_vars = list(range(n_vars))
    B = np.zeros((n_vars, n_vars))  # Causal matrix

    for _ in range(n_vars):
        scores = []

        for var in remaining_vars:
            # Compute independence score using non-Gaussianity
            test_vars = [v for v in remaining_vars if v != var]

            if not test_vars:
                scores.append((var, 0))
                continue
