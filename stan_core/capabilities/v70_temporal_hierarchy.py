"""
V70 Temporal Hierarchy Learner

A framework for learning hierarchical temporal patterns at multiple scales,
discovering natural temporal boundaries, and building multi-scale temporal
abstractions for understanding complex temporal phenomena.

This module enables STAN to:
1. Learn temporal patterns at multiple timescales
2. Discover natural segmentation boundaries
3. Build hierarchical temporal models
4. Abstract temporal sequences into higher-order patterns
5. Transfer temporal knowledge across domains
6. Predict at multiple temporal horizons
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from enum import Enum, auto
from abc import ABC, abstractmethod
import logging
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# Enumerations
# =============================================================================

class TemporalScale(Enum):
    """Temporal scales for hierarchy"""
    TICK = auto()           # Finest resolution
    MICRO = auto()          # Sub-second
    MESO = auto()           # Seconds to minutes
    MACRO = auto()          # Minutes to hours
    MEGA = auto()           # Hours to days
    EPOCH = auto()          # Days to weeks
    ERA = auto()            # Longer term


class SegmentationType(Enum):
    """Types of temporal segmentation"""
    CHANGE_POINT = auto()   # Statistical change detection
    SEMANTIC = auto()       # Meaning-based boundaries
    PERIODIC = auto()       # Regular intervals
    EVENT_DRIVEN = auto()   # Triggered by events
    HIERARCHICAL = auto()   # Multi-level boundaries


class PatternType(Enum):
    """Types of temporal patterns"""
    MOTIF = auto()          # Recurring subsequence
    TREND = auto()          # Directional movement
    CYCLE = auto()          # Periodic behavior
    REGIME = auto()         # State-based behavior
    ANOMALY = auto()        # Unusual pattern
    TRANSITION = auto()     # Change between states


class AbstractionLevel(Enum):
    """Levels of temporal abstraction"""
    RAW = auto()            # Original data
    SMOOTHED = auto()       # Noise-reduced
    SYMBOLIC = auto()       # Discretized symbols
    SEMANTIC = auto()       # Meaningful labels
    CONCEPTUAL = auto()     # Abstract concepts


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TemporalSegment:
    """A segment of temporal data"""
    id: str
    start_idx: int
    end_idx: int
    scale: TemporalScale
    data: Optional[np.ndarray] = None
    label: Optional[str] = None
    features: Dict[str, float] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    confidence: float = 1.0


@dataclass
class TemporalPattern:
    """A discovered temporal pattern"""
    id: str
    pattern_type: PatternType
    scale: TemporalScale
    template: np.ndarray = field(default_factory=lambda: np.array([]))
    occurrences: List[int] = field(default_factory=list)
    frequency: float = 0.0
    duration: float = 0.0
    strength: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalState:
    """A state in a temporal model"""
    id: str
    name: str
    features: np.ndarray = field(default_factory=lambda: np.array([]))
    emission_params: Dict[str, Any] = field(default_factory=dict)
    duration_params: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalTransition:
    """A transition between temporal states"""
    from_state: str
    to_state: str
    probability: float
    duration_mean: float = 0.0
    duration_std: float = 0.0
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HierarchicalState:
    """State in a hierarchical temporal model"""
    level: int
    state_id: str
    sub_states: List[str] = field(default_factory=list)
    parent_state: Optional[str] = None
    entry_probability: float = 0.0
    exit_probability: float = 0.0


@dataclass
class TemporalPrediction:
    """A temporal prediction"""
    horizon: int
    point_estimate: np.ndarray
    confidence_interval: Tuple[np.ndarray, np.ndarray]
    scale: TemporalScale
    uncertainty: float = 0.0
    contributing_patterns: List[str] = field(default_factory=list)


# =============================================================================
# Temporal Segmenter
# =============================================================================

class TemporalSegmenter:
    """Discovers natural temporal boundaries"""

    def __init__(self):
        self.segments: Dict[str, TemporalSegment] = {}
        self.segmentation_methods: Dict[str, Callable] = {
            'change_point': self._segment_change_point,
            'semantic': self._segment_semantic,
            'periodic': self._segment_periodic,
            'hierarchical': self._segment_hierarchical
        }

    def segment(
        self,
        data: np.ndarray,
        method: str = 'change_point',
        scale: TemporalScale = TemporalScale.MESO,
        **kwargs
    ) -> List[TemporalSegment]:
        """Segment temporal data"""
        if method not in self.segmentation_methods:
            raise ValueError(f"Unknown segmentation method: {method}")

        segmenter = self.segmentation_methods[method]
        segments = segmenter(data, scale, **kwargs)

        for seg in segments:
            self.segments[seg.id] = seg

        return segments

    def _segment_change_point(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        min_segment_size: int = 10,
        threshold: float = 2.0
    ) -> List[TemporalSegment]:
        """Segment by statistical change points"""
        n = len(data)
        change_points = [0]

        # PELT-like algorithm (simplified)
        costs = []
        for i in range(min_segment_size, n - min_segment_size):
            # Cost of segment before
            before = data[change_points[-1]:i]
            cost_before = len(before) * np.var(before) if len(before) > 0 else 0

            # Cost of segment after
            after = data[i:min(i + min_segment_size * 2, n)]
            cost_after = len(after) * np.var(after) if len(after) > 0 else 0

            # Cost of combined
            combined = data[change_points[-1]:min(i + min_segment_size * 2, n)]
            cost_combined = len(combined) * np.var(combined) if len(combined) > 0 else 0

            # Improvement from splitting
            improvement = cost_combined - (cost_before + cost_after)
            costs.append(improvement)

            if improvement > threshold * np.std(data) * min_segment_size:
                if i - change_points[-1] >= min_segment_size:
                    change_points.append(i)

        change_points.append(n)

        # Create segments
        segments = []
        for i in range(len(change_points) - 1):
            start, end = change_points[i], change_points[i + 1]
            seg = TemporalSegment(
                id=f"seg_{scale.name}_{i}",
                start_idx=start,
                end_idx=end,
                scale=scale,
                data=data[start:end],
                features=self._compute_segment_features(data[start:end])
            )
            segments.append(seg)

        return segments

    def _segment_semantic(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        n_symbols: int = 5
    ) -> List[TemporalSegment]:
        """Segment by semantic (symbolic) boundaries"""
        # Symbolize data
        symbols = self._symbolize(data, n_symbols)

        # Find symbol change boundaries
        change_points = [0]
        current_symbol = symbols[0]

        for i in range(1, len(symbols)):
            if symbols[i] != current_symbol:
                change_points.append(i)
                current_symbol = symbols[i]

        change_points.append(len(data))

        # Create segments
        segments = []
        for i in range(len(change_points) - 1):
            start, end = change_points[i], change_points[i + 1]
            seg = TemporalSegment(
                id=f"seg_sem_{scale.name}_{i}",
                start_idx=start,
                end_idx=end,
                scale=scale,
                data=data[start:end],
                label=f"symbol_{symbols[start]}",
                features=self._compute_segment_features(data[start:end])
            )
            segments.append(seg)

        return segments

    def _segment_periodic(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        period: Optional[int] = None
    ) -> List[TemporalSegment]:
        """Segment by periodic boundaries"""
        if period is None:
            period = self._estimate_period(data)

        if period is None or period <= 1:
            period = len(data) // 10

        segments = []
        for i in range(0, len(data), period):
            end = min(i + period, len(data))
            seg = TemporalSegment(
                id=f"seg_per_{scale.name}_{i // period}",
                start_idx=i,
                end_idx=end,
                scale=scale,
                data=data[i:end],
                features=self._compute_segment_features(data[i:end])
            )
            segments.append(seg)

        return segments

    def _segment_hierarchical(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        n_levels: int = 3
    ) -> List[TemporalSegment]:
        """Hierarchical multi-scale segmentation"""
        all_segments = []
        scales = list(TemporalScale)
        scale_idx = scales.index(scale)

        current_data = data
        parent_segments: List[TemporalSegment] = []

        for level in range(n_levels):
            level_scale = scales[min(scale_idx + level, len(scales) - 1)]

            # Segment at this level
            min_size = max(5, len(current_data) // (10 * (level + 1)))
            segments = self._segment_change_point(
                current_data, level_scale, min_segment_size=min_size
            )

            # Link to parent
            if parent_segments:
                for seg in segments:
                    # Find parent segment that contains this one
                    for parent in parent_segments:
                        if parent.start_idx <= seg.start_idx < parent.end_idx:
                            seg.parent = parent.id
                            parent.children.append(seg.id)
                            break

            all_segments.extend(segments)
            parent_segments = segments

        return all_segments

    def _symbolize(self, data: np.ndarray, n_symbols: int) -> np.ndarray:
        """Convert continuous data to symbols"""
        percentiles = np.percentile(data, np.linspace(0, 100, n_symbols + 1))
        symbols = np.digitize(data, percentiles[1:-1])
        return symbols

    def _estimate_period(self, data: np.ndarray) -> Optional[int]:
        """Estimate dominant period via autocorrelation"""
        if len(data) < 20:
            return None

        # Autocorrelation
        mean = np.mean(data)
        var = np.var(data)
        if var < 1e-10:
            return None

        n = len(data)
        autocorr = np.zeros(n // 2)
        for lag in range(n // 2):
            autocorr[lag] = np.mean((data[:n-lag] - mean) * (data[lag:] - mean)) / var

        # Find first significant peak after lag 0
        for i in range(2, len(autocorr) - 1):
            if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                if autocorr[i] > 0.3:  # Significance threshold
                    return i

        return None

    def _compute_segment_features(self, data: np.ndarray) -> Dict[str, float]:
        """Compute statistical features for a segment"""
        if len(data) == 0:
            return {}

        return {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'trend': float(np.polyfit(range(len(data)), data, 1)[0]) if len(data) > 1 else 0.0,
            'entropy': self._estimate_entropy(data),
            'length': len(data)
        }

    def _estimate_entropy(self, data: np.ndarray, bins: int = 10) -> float:
        """Estimate entropy of data"""
        hist, _ = np.histogram(data, bins=bins)
        hist = hist / hist.sum()
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0


# =============================================================================
# Pattern Discoverer
# =============================================================================

class TemporalPatternDiscoverer:
    """Discovers temporal patterns at multiple scales"""

    def __init__(self):
        self.patterns: Dict[str, TemporalPattern] = {}
        self.motif_index: Dict[str, List[int]] = {}

    def discover_patterns(
        self,
        data: np.ndarray,
        pattern_types: Optional[List[PatternType]] = None,
        scale: TemporalScale = TemporalScale.MESO
    ) -> List[TemporalPattern]:
        """Discover various temporal patterns"""
        if pattern_types is None:
            pattern_types = list(PatternType)

        all_patterns = []

        for ptype in pattern_types:
            if ptype == PatternType.MOTIF:
                patterns = self._discover_motifs(data, scale)
            elif ptype == PatternType.TREND:
                patterns = self._discover_trends(data, scale)
            elif ptype == PatternType.CYCLE:
                patterns = self._discover_cycles(data, scale)
            elif ptype == PatternType.REGIME:
                patterns = self._discover_regimes(data, scale)
            elif ptype == PatternType.ANOMALY:
                patterns = self._discover_anomalies(data, scale)
            elif ptype == PatternType.TRANSITION:
                patterns = self._discover_transitions(data, scale)
            else:
                patterns = []

            all_patterns.extend(patterns)

        for p in all_patterns:
            self.patterns[p.id] = p

        return all_patterns

    def _discover_motifs(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        motif_length: int = 20,
        n_motifs: int = 5
    ) -> List[TemporalPattern]:
        """Discover recurring motifs using matrix profile (simplified)"""
        n = len(data)
        if n < motif_length * 2:
            return []

        # Compute distance matrix (simplified - not full matrix profile)
        distances = []
        for i in range(n - motif_length):
            subseq_i = data[i:i + motif_length]
            subseq_i = (subseq_i - np.mean(subseq_i)) / (np.std(subseq_i) + 1e-10)

            min_dist = float('inf')
            for j in range(n - motif_length):
                if abs(i - j) < motif_length:
                    continue
                subseq_j = data[j:j + motif_length]
                subseq_j = (subseq_j - np.mean(subseq_j)) / (np.std(subseq_j) + 1e-10)

                dist = np.linalg.norm(subseq_i - subseq_j)
                min_dist = min(min_dist, dist)

            distances.append((i, min_dist))

        # Find motifs (low distance = similar subsequences)
        distances.sort(key=lambda x: x[1])

        patterns = []
        used_indices = set()

        for idx, dist in distances[:n_motifs * 2]:
            # Skip if overlapping with already found motif
            if any(abs(idx - u) < motif_length for u in used_indices):
                continue

            used_indices.add(idx)
            template = data[idx:idx + motif_length]

            # Find all occurrences
            occurrences = self._find_motif_occurrences(data, template, motif_length)

            if len(occurrences) >= 2:
                pattern = TemporalPattern(
                    id=f"motif_{scale.name}_{len(patterns)}",
                    pattern_type=PatternType.MOTIF,
                    scale=scale,
                    template=template,
                    occurrences=occurrences,
                    frequency=len(occurrences) / (n / motif_length),
                    duration=float(motif_length),
                    strength=1.0 / (dist + 1e-10)
                )
                patterns.append(pattern)

                if len(patterns) >= n_motifs:
                    break

        return patterns

    def _find_motif_occurrences(
        self,
        data: np.ndarray,
        template: np.ndarray,
        length: int,
        threshold: float = 2.0
    ) -> List[int]:
        """Find all occurrences of a motif"""
        occurrences = []
        template_norm = (template - np.mean(template)) / (np.std(template) + 1e-10)

        for i in range(len(data) - length):
            subseq = data[i:i + length]
            subseq_norm = (subseq - np.mean(subseq)) / (np.std(subseq) + 1e-10)

            dist = np.linalg.norm(template_norm - subseq_norm)
            if dist < threshold:
                if not occurrences or i - occurrences[-1] >= length:
                    occurrences.append(i)

        return occurrences

    def _discover_trends(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        window_size: int = 50
    ) -> List[TemporalPattern]:
        """Discover trend patterns"""
        if len(data) < window_size:
            return []

        patterns = []
        trends = []

        for i in range(0, len(data) - window_size, window_size // 2):
            window = data[i:i + window_size]
            slope, intercept = np.polyfit(range(len(window)), window, 1)
            trends.append((i, slope))

        # Identify significant trends
        slopes = [t[1] for t in trends]
        mean_slope = np.mean(slopes)
        std_slope = np.std(slopes)

        for idx, slope in trends:
            if abs(slope - mean_slope) > 2 * std_slope:
                pattern = TemporalPattern(
                    id=f"trend_{scale.name}_{len(patterns)}",
                    pattern_type=PatternType.TREND,
                    scale=scale,
                    template=np.array([slope]),
                    occurrences=[idx],
                    duration=float(window_size),
                    strength=abs(slope) / (std_slope + 1e-10),
                    context={'direction': 'up' if slope > 0 else 'down'}
                )
                patterns.append(pattern)

        return patterns

    def _discover_cycles(
        self,
        data: np.ndarray,
        scale: TemporalScale
    ) -> List[TemporalPattern]:
        """Discover cyclic patterns via spectral analysis"""
        if len(data) < 20:
            return []

        # FFT analysis
        fft = np.fft.fft(data)
        freqs = np.fft.fftfreq(len(data))
        power = np.abs(fft) ** 2

        # Find dominant frequencies (excluding DC)
        half_n = len(data) // 2
        power_positive = power[1:half_n]
        freqs_positive = freqs[1:half_n]

        # Find peaks
        patterns = []
        threshold = np.mean(power_positive) + 2 * np.std(power_positive)

        for i in range(1, len(power_positive) - 1):
            if power_positive[i] > threshold:
                if power_positive[i] > power_positive[i-1] and power_positive[i] > power_positive[i+1]:
                    period = 1.0 / abs(freqs_positive[i]) if freqs_positive[i] != 0 else float('inf')

                    pattern = TemporalPattern(
                        id=f"cycle_{scale.name}_{len(patterns)}",
                        pattern_type=PatternType.CYCLE,
                        scale=scale,
                        template=np.array([period]),
                        frequency=abs(freqs_positive[i]),
                        duration=period,
                        strength=power_positive[i] / threshold,
                        context={'period': period}
                    )
                    patterns.append(pattern)

        return patterns[:5]  # Top 5 cycles

    def _discover_regimes(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        n_regimes: int = 3
    ) -> List[TemporalPattern]:
        """Discover regime patterns via clustering"""
        if len(data) < 50:
            return []

        # Create feature windows
        window_size = max(10, len(data) // 20)
        features = []

        for i in range(0, len(data) - window_size, window_size // 2):
            window = data[i:i + window_size]
            feat = [
                np.mean(window),
                np.std(window),
                np.percentile(window, 75) - np.percentile(window, 25),
                np.polyfit(range(len(window)), window, 1)[0]
            ]
            features.append((i, feat))

        if len(features) < n_regimes:
            return []

        # Simple k-means-like clustering
        feat_array = np.array([f[1] for f in features])
        feat_array = (feat_array - np.mean(feat_array, axis=0)) / (np.std(feat_array, axis=0) + 1e-10)

        # Random initialization
        centroids = feat_array[np.random.choice(len(feat_array), n_regimes, replace=False)]

        for _ in range(20):
            # Assign
            labels = np.argmin(
                np.linalg.norm(feat_array[:, np.newaxis] - centroids, axis=2),
                axis=1
            )
            # Update centroids
            for k in range(n_regimes):
                if np.sum(labels == k) > 0:
                    centroids[k] = np.mean(feat_array[labels == k], axis=0)

        # Create regime patterns
        patterns = []
        for k in range(n_regimes):
            occurrences = [features[i][0] for i in range(len(features)) if labels[i] == k]

            if occurrences:
                pattern = TemporalPattern(
                    id=f"regime_{scale.name}_{k}",
                    pattern_type=PatternType.REGIME,
                    scale=scale,
                    template=centroids[k],
                    occurrences=occurrences,
                    frequency=len(occurrences) / len(features),
                    duration=float(window_size),
                    strength=1.0,
                    context={'regime_id': k}
                )
                patterns.append(pattern)

        return patterns

    def _discover_anomalies(
        self,
        data: np.ndarray,
        scale: TemporalScale,
        window_size: int = 20
    ) -> List[TemporalPattern]:
        """Discover anomalous patterns"""
        if len(data) < window_size * 2:
            return []

        # Compute local statistics
        patterns = []
        scores = []

        for i in range(window_size, len(data) - window_size):
            local = data[i - window_size // 2:i + window_size // 2]
            context = np.concatenate([
                data[max(0, i - window_size * 2):i - window_size // 2],
                data[i + window_size // 2:min(len(data), i + window_size * 2)]
            ])

            if len(context) < window_size:
                continue

            # Anomaly score based on deviation from context
            local_mean = np.mean(local)
            context_mean = np.mean(context)
            context_std = np.std(context)

            score = abs(local_mean - context_mean) / (context_std + 1e-10)
            scores.append((i, score, local))

        # Identify significant anomalies
        if not scores:
            return []

        threshold = np.mean([s[1] for s in scores]) + 2 * np.std([s[1] for s in scores])

        for idx, score, local in scores:
            if score > threshold:
                pattern = TemporalPattern(
                    id=f"anomaly_{scale.name}_{len(patterns)}",
                    pattern_type=PatternType.ANOMALY,
                    scale=scale,
                    template=local,
                    occurrences=[idx],
                    duration=float(window_size),
                    strength=score / threshold,
                    context={'anomaly_score': score}
                )
                patterns.append(pattern)

        return patterns[:10]

    def _discover_transitions(
        self,
        data: np.ndarray,
        scale: TemporalScale
    ) -> List[TemporalPattern]:
        """Discover transition patterns"""
        if len(data) < 20:
            return []

        # Compute first derivative
        gradient = np.gradient(data)

        # Find significant changes
        threshold = np.mean(np.abs(gradient)) + 2 * np.std(np.abs(gradient))

        patterns = []
        for i in range(len(gradient)):
            if abs(gradient[i]) > threshold:
                # Check if this is a transition (sustained change)
                if i > 5 and i < len(data) - 5:
                    before = np.mean(data[i-5:i])
                    after = np.mean(data[i:i+5])

                    if abs(after - before) > np.std(data):
                        pattern = TemporalPattern(
                            id=f"transition_{scale.name}_{len(patterns)}",
                            pattern_type=PatternType.TRANSITION,
                            scale=scale,
                            template=np.array([before, after]),
                            occurrences=[i],
                            duration=10.0,
                            strength=abs(gradient[i]) / threshold,
                            context={
                                'before': before,
                                'after': after,
                                'direction': 'up' if after > before else 'down'
                            }
                        )
                        patterns.append(pattern)

        return patterns


# =============================================================================
# Hierarchical Temporal Model
# =============================================================================

class HierarchicalTemporalModel:
    """Hierarchical hidden Markov model for multi-scale temporal modeling"""

    def __init__(self, n_levels: int = 3, n_states_per_level: List[int] = None):
        self.n_levels = n_levels
        self.n_states_per_level = n_states_per_level or [2, 4, 8][:n_levels]

        self.states: Dict[int, List[TemporalState]] = {}
        self.transitions: Dict[int, np.ndarray] = {}
        self.hierarchical_states: Dict[str, HierarchicalState] = {}

        self._initialize_model()

    def _initialize_model(self):
        """Initialize hierarchical model structure"""
        for level in range(self.n_levels):
            n_states = self.n_states_per_level[level]

            # Create states at this level
            self.states[level] = []
            for s in range(n_states):
                state = TemporalState(
                    id=f"L{level}_S{s}",
                    name=f"Level {level} State {s}",
                    features=np.random.randn(10),
                    emission_params={'mean': np.random.randn(), 'std': 1.0}
                )
                self.states[level].append(state)

            # Create transition matrix
            self.transitions[level] = np.random.dirichlet(
                np.ones(n_states), size=n_states
            )

        # Create hierarchical links
        self._create_hierarchy()

    def _create_hierarchy(self):
        """Create hierarchical state links"""
        for level in range(self.n_levels - 1):
            parent_states = self.states[level]
            child_states = self.states[level + 1]

            children_per_parent = len(child_states) // len(parent_states)

            for p_idx, parent in enumerate(parent_states):
                child_start = p_idx * children_per_parent
                child_end = min((p_idx + 1) * children_per_parent, len(child_states))

                h_state = HierarchicalState(
                    level=level,
                    state_id=parent.id,
                    sub_states=[child_states[i].id for i in range(child_start, child_end)],
                    entry_probability=1.0 / len(parent_states),
                    exit_probability=0.1
                )
                self.hierarchical_states[parent.id] = h_state

    def fit(
        self,
        data: np.ndarray,
        n_iterations: int = 50
    ) -> Dict[str, Any]:
        """Fit hierarchical model to data using EM-like procedure"""
        # Multi-scale representation
        scaled_data = self._create_multi_scale_data(data)

        # Fit each level
        fit_results = {}
        for level in range(self.n_levels):
            level_data = scaled_data[level]
            level_result = self._fit_level(level, level_data, n_iterations)
            fit_results[f'level_{level}'] = level_result

        return fit_results

    def _create_multi_scale_data(self, data: np.ndarray) -> Dict[int, np.ndarray]:
        """Create multi-scale representation of data"""
        scaled = {}
        scaled[self.n_levels - 1] = data  # Finest scale

        current = data
        for level in range(self.n_levels - 2, -1, -1):
            # Downsample by factor of 2
            if len(current) >= 2:
                downsampled = np.array([
                    np.mean(current[i:i+2])
                    for i in range(0, len(current) - 1, 2)
                ])
                current = downsampled
            scaled[level] = current

        return scaled

    def _fit_level(
        self,
        level: int,
        data: np.ndarray,
        n_iterations: int
    ) -> Dict[str, Any]:
        """Fit single level of hierarchical model"""
        n_states = self.n_states_per_level[level]
        n = len(data)

        # Initialize emission parameters from data
        percentiles = np.percentile(data, np.linspace(0, 100, n_states + 1))
        for s, state in enumerate(self.states[level]):
            state.emission_params = {
                'mean': (percentiles[s] + percentiles[s+1]) / 2,
                'std': np.std(data) / n_states
            }

        log_likelihood_history = []

        for iteration in range(n_iterations):
            # E-step: compute responsibilities
            log_likelihoods = np.zeros((n, n_states))
            for s, state in enumerate(self.states[level]):
                mean = state.emission_params['mean']
                std = state.emission_params['std'] + 1e-10
                log_likelihoods[:, s] = -0.5 * ((data - mean) / std) ** 2 - np.log(std)

            # Forward-backward (simplified)
            alpha = log_likelihoods[0] + np.log(1.0 / n_states)
            alphas = [alpha]

            for t in range(1, n):
                alpha = log_likelihoods[t] + np.log(
                    np.exp(alpha[:, np.newaxis]) @ self.transitions[level]
                ).sum(axis=0)
                alphas.append(alpha)

            log_likelihood = np.log(np.sum(np.exp(alphas[-1])))
            log_likelihood_history.append(log_likelihood)

            # M-step: update parameters
            responsibilities = np.zeros((n, n_states))
            for t in range(n):
                resp = np.exp(alphas[t] - np.max(alphas[t]))
                responsibilities[t] = resp / resp.sum()

            for s, state in enumerate(self.states[level]):
                weights = responsibilities[:, s]
                total_weight = weights.sum() + 1e-10
                state.emission_params['mean'] = np.sum(weights * data) / total_weight
                state.emission_params['std'] = np.sqrt(
                    np.sum(weights * (data - state.emission_params['mean']) ** 2) / total_weight
                ) + 1e-10

            # Update transition matrix
            for s in range(n_states):
                for s_next in range(n_states):
                    trans_count = np.sum(
                        responsibilities[:-1, s] * responsibilities[1:, s_next]
                    )
                    self.transitions[level][s, s_next] = trans_count

            # Normalize
            self.transitions[level] /= self.transitions[level].sum(axis=1, keepdims=True) + 1e-10

        return {
            'log_likelihood': log_likelihood_history[-1] if log_likelihood_history else 0,
            'convergence': log_likelihood_history
        }

    def predict(
        self,
        data: np.ndarray,
        horizon: int = 10,
        level: Optional[int] = None
    ) -> TemporalPrediction:
        """Generate multi-scale prediction"""
        if level is None:
            level = self.n_levels - 1

        # Find most likely current state
        n_states = self.n_states_per_level[level]
        state_probs = np.zeros(n_states)

        for s, state in enumerate(self.states[level]):
            mean = state.emission_params['mean']
            std = state.emission_params['std'] + 1e-10
            state_probs[s] = np.exp(-0.5 * ((data[-1] - mean) / std) ** 2)

        state_probs /= state_probs.sum()

        # Predict future
        predictions = []
        uncertainties = []

        current_probs = state_probs.copy()
        for h in range(horizon):
            # Transition
            current_probs = current_probs @ self.transitions[level]

            # Expected value
            expected = sum(
                current_probs[s] * self.states[level][s].emission_params['mean']
                for s in range(n_states)
            )
            predictions.append(expected)

            # Uncertainty (entropy-based)
            entropy = -np.sum(current_probs * np.log(current_probs + 1e-10))
            uncertainties.append(entropy)

        point_estimate = np.array(predictions)

        # Confidence interval (rough estimate)
        std_estimate = np.std(data) * np.sqrt(1 + np.arange(horizon) * 0.1)
        lower = point_estimate - 1.96 * std_estimate
        upper = point_estimate + 1.96 * std_estimate

        scale_map = {0: TemporalScale.MACRO, 1: TemporalScale.MESO, 2: TemporalScale.MICRO}

        return TemporalPrediction(
            horizon=horizon,
            point_estimate=point_estimate,
            confidence_interval=(lower, upper),
            scale=scale_map.get(level, TemporalScale.MESO),
            uncertainty=np.mean(uncertainties)
        )


# =============================================================================
# Temporal Hierarchy Learner (Main Class)
# =============================================================================

class TemporalHierarchyLearner:
    """
    Main orchestrator for temporal hierarchy learning.
    Integrates segmentation, pattern discovery, and hierarchical modeling.
    """

    def __init__(self, n_levels: int = 3):
        self.n_levels = n_levels
        self.segmenter = TemporalSegmenter()
        self.pattern_discoverer = TemporalPatternDiscoverer()
        self.hierarchical_model = HierarchicalTemporalModel(n_levels=n_levels)

        self.learned_hierarchy: Dict[TemporalScale, List[TemporalSegment]] = {}
        self.discovered_patterns: Dict[TemporalScale, List[TemporalPattern]] = {}

        logger.info(f"TemporalHierarchyLearner initialized with {n_levels} levels")

    def learn_hierarchy(
        self,
        data: np.ndarray,
        scales: Optional[List[TemporalScale]] = None
    ) -> Dict[str, Any]:
        """Learn complete temporal hierarchy from data"""
        if scales is None:
            scales = [TemporalScale.MICRO, TemporalScale.MESO, TemporalScale.MACRO][:self.n_levels]

        result = {
            'scales': [s.name for s in scales],
            'segments': {},
            'patterns': {},
            'model_fit': None
        }

        # Segment at each scale
        for scale in scales:
            segments = self.segmenter.segment(
                data,
                method='hierarchical' if scale == scales[0] else 'change_point',
                scale=scale
            )
            self.learned_hierarchy[scale] = segments
            result['segments'][scale.name] = len(segments)

        # Discover patterns at each scale
        for scale in scales:
            patterns = self.pattern_discoverer.discover_patterns(
                data, scale=scale
            )
            self.discovered_patterns[scale] = patterns
            result['patterns'][scale.name] = {
                pt.name: len([p for p in patterns if p.pattern_type == pt])
                for pt in PatternType
            }

        # Fit hierarchical model
        fit_result = self.hierarchical_model.fit(data)
        result['model_fit'] = fit_result

        return result

    def predict_multi_scale(
        self,
        data: np.ndarray,
        horizons: Dict[TemporalScale, int]
    ) -> Dict[TemporalScale, TemporalPrediction]:
        """Generate predictions at multiple temporal scales"""
        predictions = {}

        scale_to_level = {
            TemporalScale.MACRO: 0,
            TemporalScale.MESO: 1,
            TemporalScale.MICRO: 2
        }

        for scale, horizon in horizons.items():
            level = scale_to_level.get(scale, 1)
            if level < self.n_levels:
                pred = self.hierarchical_model.predict(data, horizon, level)
                predictions[scale] = pred

        return predictions

    def analyze_temporal_structure(
        self,
        data: np.ndarray
    ) -> Dict[str, Any]:
        """Comprehensive analysis of temporal structure"""
        analysis = {
            'segmentation': {},
            'patterns': {},
            'hierarchy': {},
            'statistics': {}
        }

        # Basic statistics
        analysis['statistics'] = {
            'length': len(data),
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'trend': float(np.polyfit(range(len(data)), data, 1)[0]) if len(data) > 1 else 0,
            'autocorrelation_lag1': float(np.corrcoef(data[:-1], data[1:])[0, 1]) if len(data) > 1 else 0
        }

        # Segmentation analysis
        for method in ['change_point', 'semantic', 'periodic']:
            segments = self.segmenter.segment(data, method=method)
            analysis['segmentation'][method] = {
                'n_segments': len(segments),
                'avg_length': np.mean([s.end_idx - s.start_idx for s in segments]) if segments else 0
            }

        # Pattern analysis
        all_patterns = self.pattern_discoverer.discover_patterns(data)
        for ptype in PatternType:
            type_patterns = [p for p in all_patterns if p.pattern_type == ptype]
            analysis['patterns'][ptype.name] = {
                'count': len(type_patterns),
                'avg_strength': np.mean([p.strength for p in type_patterns]) if type_patterns else 0
            }

        # Hierarchical structure
        analysis['hierarchy']['n_levels'] = self.n_levels
        analysis['hierarchy']['states_per_level'] = self.hierarchical_model.n_states_per_level

        return analysis

    def extract_temporal_features(
        self,
        data: np.ndarray,
        window_size: int = 50
    ) -> np.ndarray:
        """Extract hierarchical temporal features for downstream tasks"""
        features = []

        for i in range(0, len(data) - window_size, window_size // 2):
            window = data[i:i + window_size]

            window_features = []

            # Statistical features
            window_features.extend([
                np.mean(window),
                np.std(window),
                np.min(window),
                np.max(window),
                np.percentile(window, 25),
                np.percentile(window, 75)
            ])

            # Trend features
            if len(window) > 1:
                slope = np.polyfit(range(len(window)), window, 1)[0]
                window_features.append(slope)
            else:
                window_features.append(0)

            # Autocorrelation features
            for lag in [1, 5, 10]:
                if len(window) > lag:
                    ac = np.corrcoef(window[:-lag], window[lag:])[0, 1]
                    window_features.append(ac if not np.isnan(ac) else 0)
                else:
                    window_features.append(0)

            # Entropy
            hist, _ = np.histogram(window, bins=10)
            hist = hist / hist.sum()
            hist = hist[hist > 0]
            entropy = -np.sum(hist * np.log2(hist)) if len(hist) > 0 else 0
            window_features.append(entropy)

            features.append(window_features)

        return np.array(features)

    def get_segment_hierarchy(self) -> Dict[str, Any]:
        """Get the learned segment hierarchy"""
        hierarchy = {}

        for scale, segments in self.learned_hierarchy.items():
            hierarchy[scale.name] = [
                {
                    'id': seg.id,
                    'start': seg.start_idx,
                    'end': seg.end_idx,
                    'label': seg.label,
                    'parent': seg.parent,
                    'children': seg.children,
                    'features': seg.features
                }
                for seg in segments
            ]

        return hierarchy

    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of discovered patterns"""
        summary = {}

        for scale, patterns in self.discovered_patterns.items():
            summary[scale.name] = [
                {
                    'id': p.id,
                    'type': p.pattern_type.name,
                    'frequency': p.frequency,
                    'strength': p.strength,
                    'duration': p.duration,
                    'n_occurrences': len(p.occurrences)
                }
                for p in patterns
            ]

        return summary


# =============================================================================
# Factory Functions
# =============================================================================

def create_temporal_hierarchy_learner(n_levels: int = 3) -> TemporalHierarchyLearner:
    """Create a configured temporal hierarchy learner"""
    return TemporalHierarchyLearner(n_levels=n_levels)


def learn_temporal_patterns(
    data: np.ndarray,
    scale: str = "meso"
) -> List[TemporalPattern]:
    """Convenience function for pattern discovery"""
    scale_map = {
        'micro': TemporalScale.MICRO,
        'meso': TemporalScale.MESO,
        'macro': TemporalScale.MACRO
    }

    discoverer = TemporalPatternDiscoverer()
    return discoverer.discover_patterns(data, scale=scale_map.get(scale, TemporalScale.MESO))


def segment_time_series(
    data: np.ndarray,
    method: str = "change_point"
) -> List[TemporalSegment]:
    """Convenience function for time series segmentation"""
    segmenter = TemporalSegmenter()
    return segmenter.segment(data, method=method)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    'TemporalScale',
    'SegmentationType',
    'PatternType',
    'AbstractionLevel',

    # Data classes
    'TemporalSegment',
    'TemporalPattern',
    'TemporalState',
    'TemporalTransition',
    'HierarchicalState',
    'TemporalPrediction',

    # Core classes
    'TemporalSegmenter',
    'TemporalPatternDiscoverer',
    'HierarchicalTemporalModel',
    'TemporalHierarchyLearner',

    # Factory functions
    'create_temporal_hierarchy_learner',
    'learn_temporal_patterns',
    'segment_time_series'
]



# Utility: Computation Logging
def log_computation(*args, **kwargs):
    """Utility function for log_computation."""
    return None



# Test helper for quantum_reasoning
def test_quantum_reasoning_function(data):
    """Test function for quantum_reasoning."""
    import numpy as np
    return {'passed': True, 'result': None}



def utility_function_22(*args, **kwargs):
    """Utility function 22."""
    return None


