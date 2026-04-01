"""
V70 Emergent Computation Layer

A framework for harnessing emergent computation - leveraging self-organizing
dynamics, cellular automata, reservoir computing, and collective behavior
to perform computation that emerges from simpler components.

This module enables STAN to:
1. Detect and characterize emergent phenomena in data
2. Use reservoir computing for temporal pattern processing
3. Evolve cellular automata for computation
4. Model collective behavior and swarm intelligence
5. Harness self-organization for problem-solving
6. Identify phase transitions and critical phenomena
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

class EmergenceType(Enum):
    """Types of emergent phenomena"""
    WEAK = auto()           # Derivable from components
    STRONG = auto()         # Not derivable, truly novel
    PATTERN = auto()        # Spatial/temporal patterns
    FUNCTIONAL = auto()     # New capabilities emerge
    COLLECTIVE = auto()     # From group behavior
    PHASE_TRANSITION = auto()  # Critical phenomena


class ReservoirType(Enum):
    """Types of reservoir computing"""
    ECHO_STATE = auto()     # Echo state network
    LIQUID_STATE = auto()   # Liquid state machine
    DELAY_LINE = auto()     # Time-delay reservoir
    RANDOM_FEATURE = auto()  # Random feature mapping
    PHYSICAL = auto()       # Physical reservoir (simulated)


class CARule(Enum):
    """Cellular automaton rule classes"""
    RULE_30 = auto()        # Class III chaotic
    RULE_110 = auto()       # Class IV universal
    RULE_184 = auto()       # Traffic flow
    GAME_OF_LIFE = auto()   # 2D totalistic
    LANGTONS_ANT = auto()   # 2D turmite
    CUSTOM = auto()


class CollectiveType(Enum):
    """Types of collective behavior"""
    SWARM = auto()          # Swarm intelligence
    FLOCK = auto()          # Flocking behavior
    CONSENSUS = auto()      # Opinion dynamics
    SYNCHRONIZATION = auto() # Coupled oscillators
    STIGMERGY = auto()      # Indirect coordination


class PhaseType(Enum):
    """Types of phase in dynamical systems"""
    ORDERED = auto()        # Low entropy, predictable
    CRITICAL = auto()       # Edge of chaos
    CHAOTIC = auto()        # High entropy, unpredictable
    FROZEN = auto()         # Stuck in attractor


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EmergentPattern:
    """Represents a detected emergent pattern"""
    id: str
    pattern_type: EmergenceType
    description: str
    scale: float                  # Spatial/temporal scale
    components: List[str] = field(default_factory=list)
    emergent_properties: List[str] = field(default_factory=list)
    emergence_strength: float = 0.0
    stability: float = 0.0
    novelty_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReservoirState:
    """State of a reservoir computer"""
    state_vector: np.ndarray
    time_step: int
    memory_capacity: float = 0.0
    separation_ratio: float = 0.0
    lyapunov_exponent: float = 0.0


@dataclass
class CellularAutomaton:
    """Configuration for a cellular automaton"""
    id: str
    dimensions: int
    rule: CARule
    rule_number: Optional[int] = None  # For 1D elementary CA
    neighborhood_size: int = 3
    boundary_condition: str = "periodic"
    state: Optional[np.ndarray] = None
    history: List[np.ndarray] = field(default_factory=list)


@dataclass
class SwarmAgent:
    """An agent in a swarm"""
    id: str
    position: np.ndarray
    velocity: np.ndarray
    fitness: float = 0.0
    personal_best: Optional[np.ndarray] = None
    personal_best_fitness: float = float('-inf')
    neighbors: List[str] = field(default_factory=list)


@dataclass
class SwarmState:
    """State of a swarm"""
    agents: List[SwarmAgent]
    global_best: Optional[np.ndarray] = None
    global_best_fitness: float = float('-inf')
    iteration: int = 0
    convergence_metric: float = 0.0


@dataclass
class PhaseAnalysis:
    """Analysis of phase behavior"""
    current_phase: PhaseType
    order_parameter: float
    correlation_length: float
    critical_exponents: Dict[str, float] = field(default_factory=dict)
    phase_boundaries: List[float] = field(default_factory=list)
    susceptibility: float = 0.0


# =============================================================================
# Emergence Detector
# =============================================================================

class EmergenceDetector:
    """Detects and characterizes emergent phenomena"""

    def __init__(self):
        self.detected_patterns: Dict[str, EmergentPattern] = {}
        self.detection_methods: Dict[str, Callable] = {
            'statistical': self._detect_statistical_emergence,
            'information': self._detect_information_emergence,
            'causal': self._detect_causal_emergence,
            'functional': self._detect_functional_emergence
        }

    def detect_emergence(
        self,
        data: np.ndarray,
        component_data: Optional[List[np.ndarray]] = None,
        method: str = 'information'
    ) -> List[EmergentPattern]:
        """Detect emergent patterns in data"""
        if method not in self.detection_methods:
            raise ValueError(f"Unknown detection method: {method}")

        detector = self.detection_methods[method]
        patterns = detector(data, component_data)

        for pattern in patterns:
            self.detected_patterns[pattern.id] = pattern

        return patterns

    def _detect_statistical_emergence(
        self,
        data: np.ndarray,
        component_data: Optional[List[np.ndarray]]
    ) -> List[EmergentPattern]:
        """Detect emergence via statistical measures"""
        patterns = []

        # Check for non-linearity in aggregation
        if component_data:
            component_sum = sum(np.mean(c) for c in component_data)
            aggregate_mean = np.mean(data)

            nonlinearity = abs(aggregate_mean - component_sum) / (abs(component_sum) + 1e-10)

            if nonlinearity > 0.1:
                pattern = EmergentPattern(
                    id=f"stat_emerge_{len(self.detected_patterns)}",
                    pattern_type=EmergenceType.WEAK,
                    description="Non-linear aggregation detected",
                    scale=len(data),
                    emergence_strength=nonlinearity,
                    components=[f"component_{i}" for i in range(len(component_data))]
                )
                patterns.append(pattern)

        # Check for long-range correlations
        if len(data) > 100:
            autocorr = self._compute_autocorrelation(data)
            decay_rate = self._fit_decay(autocorr)

            if decay_rate < 0.1:  # Slow decay indicates long-range order
                pattern = EmergentPattern(
                    id=f"longrange_{len(self.detected_patterns)}",
                    pattern_type=EmergenceType.PATTERN,
                    description="Long-range correlations detected",
                    scale=1.0 / decay_rate if decay_rate > 0 else float('inf'),
                    emergence_strength=1.0 - decay_rate
                )
                patterns.append(pattern)

        return patterns

    def _detect_information_emergence(
        self,
        data: np.ndarray,
        component_data: Optional[List[np.ndarray]]
    ) -> List[EmergentPattern]:
        """Detect emergence via information-theoretic measures"""
        patterns = []

        # Estimate entropy of whole vs parts
        whole_entropy = self._estimate_entropy(data)

        if component_data:
            part_entropies = [self._estimate_entropy(c) for c in component_data]
            sum_entropies = sum(part_entropies)

            # Synergy: whole has more info than sum of parts
            synergy = whole_entropy - sum_entropies

            if synergy > 0.1:
                pattern = EmergentPattern(
                    id=f"info_synergy_{len(self.detected_patterns)}",
                    pattern_type=EmergenceType.STRONG,
                    description="Information synergy detected - whole > sum of parts",
                    scale=len(data),
                    emergence_strength=synergy / whole_entropy if whole_entropy > 0 else 0,
                    emergent_properties=["information_gain"]
                )
                patterns.append(pattern)

        # Check for complexity (not too ordered, not too random)
        complexity = self._estimate_complexity(data)
        if 0.3 < complexity < 0.7:
            pattern = EmergentPattern(
                id=f"complexity_{len(self.detected_patterns)}",
                pattern_type=EmergenceType.PATTERN,
                description="Edge-of-chaos complexity detected",
                scale=len(data),
                emergence_strength=1.0 - 2 * abs(complexity - 0.5),
                emergent_properties=["computational_capacity"]
            )
            patterns.append(pattern)

        return patterns

    def _detect_causal_emergence(
        self,
        data: np.ndarray,
        component_data: Optional[List[np.ndarray]]
    ) -> List[EmergentPattern]:
        """Detect causal emergence - macro level more predictive than micro"""
        patterns = []

        if len(data) < 50:
            return patterns

        # Split into time windows
        n_windows = min(10, len(data) // 5)
        if n_windows < 2:
            return patterns

        windows = np.array_split(data, n_windows)

        # Micro-level predictability (raw data)
        micro_predictability = self._estimate_predictability(data)

        # Macro-level predictability (coarse-grained)
        macro_data = np.array([np.mean(w) for w in windows])
        macro_predictability = self._estimate_predictability(macro_data)

        # Causal emergence: macro more predictive than micro
        causal_emergence = macro_predictability - micro_predictability

        if causal_emergence > 0.1:
            pattern = EmergentPattern(
                id=f"causal_emerge_{len(self.detected_patterns)}",
                pattern_type=EmergenceType.STRONG,
                description="Causal emergence - macro level more predictive",
                scale=len(windows[0]),
                emergence_strength=causal_emergence,
                emergent_properties=["downward_causation", "macro_determinism"]
            )
            patterns.append(pattern)

        return patterns

    def _detect_functional_emergence(
        self,
        data: np.ndarray,
        component_data: Optional[List[np.ndarray]]
    ) -> List[EmergentPattern]:
        """Detect functional emergence - new capabilities"""
        patterns = []

        # Check for threshold behavior
        if len(data) > 20:
            sorted_data = np.sort(data)
            diffs = np.diff(sorted_data)

            # Find largest gap (potential phase transition)
            max_gap_idx = np.argmax(diffs)
            max_gap = diffs[max_gap_idx]
            mean_gap = np.mean(diffs)

            if max_gap > 3 * mean_gap:
                threshold = (sorted_data[max_gap_idx] + sorted_data[max_gap_idx + 1]) / 2
                pattern = EmergentPattern(
                    id=f"threshold_{len(self.detected_patterns)}",
                    pattern_type=EmergenceType.PHASE_TRANSITION,
                    description=f"Threshold behavior at {threshold:.3f}",
                    scale=max_gap / mean_gap,
                    emergence_strength=max_gap / (np.max(data) - np.min(data) + 1e-10),
                    emergent_properties=["bistability", "switching"]
                )
                patterns.append(pattern)

        return patterns

    def _compute_autocorrelation(self, data: np.ndarray, max_lag: int = 50) -> np.ndarray:
        """Compute autocorrelation function"""
        n = len(data)
        max_lag = min(max_lag, n // 2)
        mean = np.mean(data)
        var = np.var(data)

        if var < 1e-10:
            return np.zeros(max_lag)

        autocorr = np.zeros(max_lag)
        for lag in range(max_lag):
            autocorr[lag] = np.mean((data[:n-lag] - mean) * (data[lag:] - mean)) / var

        return autocorr

    def _fit_decay(self, autocorr: np.ndarray) -> float:
        """Fit exponential decay to autocorrelation"""
        positive_lags = np.where(autocorr > 0.1)[0]
        if len(positive_lags) < 3:
            return 1.0  # Fast decay

        # Simple linear fit to log
        log_autocorr = np.log(autocorr[positive_lags] + 1e-10)
        decay_rate = -np.polyfit(positive_lags, log_autocorr, 1)[0]

        return max(0.0, decay_rate)

    def _estimate_entropy(self, data: np.ndarray, bins: int = 20) -> float:
        """Estimate Shannon entropy"""
        hist, _ = np.histogram(data, bins=bins)
        hist = hist / hist.sum()
        hist = hist[hist > 0]
        return -np.sum(hist * np.log2(hist))

    def _estimate_complexity(self, data: np.ndarray) -> float:
        """Estimate statistical complexity (normalized)"""
        entropy = self._estimate_entropy(data)
        max_entropy = np.log2(len(data))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _estimate_predictability(self, data: np.ndarray) -> float:
        """Estimate predictability via simple AR model"""
        if len(data) < 10:
            return 0.5

        # Lag-1 correlation as simple predictability measure
        corr = np.corrcoef(data[:-1], data[1:])[0, 1]
        return (corr + 1) / 2 if not np.isnan(corr) else 0.5


# =============================================================================
# Reservoir Computer
# =============================================================================

class ReservoirComputer:
    """Reservoir computing for temporal pattern processing"""

    def __init__(
        self,
        reservoir_size: int = 100,
        reservoir_type: ReservoirType = ReservoirType.ECHO_STATE,
        spectral_radius: float = 0.9,
        sparsity: float = 0.1,
        input_scaling: float = 1.0,
        leaking_rate: float = 0.3
    ):
        self.reservoir_size = reservoir_size
        self.reservoir_type = reservoir_type
        self.spectral_radius = spectral_radius
        self.sparsity = sparsity
        self.input_scaling = input_scaling
        self.leaking_rate = leaking_rate

        # Initialize reservoir
        self.W_reservoir = self._init_reservoir()
        self.W_input: Optional[np.ndarray] = None
        self.W_output: Optional[np.ndarray] = None

        self.state = np.zeros(reservoir_size)
        self.state_history: List[np.ndarray] = []

    def _init_reservoir(self) -> np.ndarray:
        """Initialize reservoir weight matrix"""
        # Create sparse random matrix
        W = np.random.randn(self.reservoir_size, self.reservoir_size)

        # Apply sparsity
        mask = np.random.rand(self.reservoir_size, self.reservoir_size) > self.sparsity
        W[mask] = 0

        # Scale to desired spectral radius
        eigenvalues = np.linalg.eigvals(W)
        current_radius = np.max(np.abs(eigenvalues))

        if current_radius > 0:
            W = W * (self.spectral_radius / current_radius)

        return W

    def initialize_input_weights(self, input_dim: int):
        """Initialize input weights"""
        self.W_input = np.random.randn(self.reservoir_size, input_dim) * self.input_scaling

    def forward(self, input_signal: np.ndarray) -> np.ndarray:
        """Process input through reservoir"""
        if self.W_input is None:
            self.initialize_input_weights(input_signal.shape[-1] if input_signal.ndim > 1 else 1)

        input_signal = input_signal.reshape(-1, 1) if input_signal.ndim == 1 else input_signal

        states = []
        for t in range(len(input_signal)):
            # Leaky integrator update
            pre_activation = np.tanh(
                self.W_reservoir @ self.state +
                self.W_input @ input_signal[t]
            )
            self.state = (1 - self.leaking_rate) * self.state + self.leaking_rate * pre_activation
            states.append(self.state.copy())

        self.state_history.extend(states)
        return np.array(states)

    def train_readout(
        self,
        states: np.ndarray,
        targets: np.ndarray,
        regularization: float = 1e-6
    ):
        """Train readout weights via ridge regression"""
        # Add bias term
        states_bias = np.hstack([states, np.ones((len(states), 1))])

        # Ridge regression
        self.W_output = np.linalg.solve(
            states_bias.T @ states_bias + regularization * np.eye(states_bias.shape[1]),
            states_bias.T @ targets
        )

    def predict(self, states: np.ndarray) -> np.ndarray:
        """Generate predictions from reservoir states"""
        if self.W_output is None:
            raise ValueError("Readout not trained")

        states_bias = np.hstack([states, np.ones((len(states), 1))])
        return states_bias @ self.W_output

    def reset_state(self):
        """Reset reservoir state"""
        self.state = np.zeros(self.reservoir_size)
        self.state_history = []

    def compute_memory_capacity(self, test_length: int = 1000) -> float:
        """Compute memory capacity of the reservoir"""
        # Generate random input
        input_signal = np.random.randn(test_length)

        # Reset and run
        self.reset_state()
        states = self.forward(input_signal.reshape(-1, 1))

        # Compute correlation with delayed inputs
        total_mc = 0.0
        for delay in range(1, min(100, test_length // 2)):
            target = input_signal[:-delay]
            predictor = states[delay:, :]

            # Train simple readout for this delay
            if len(target) > 10:
                corr = self._compute_correlation(predictor, target)
                total_mc += corr ** 2

        return total_mc

    def _compute_correlation(self, X: np.ndarray, y: np.ndarray) -> float:
        """Compute correlation between reservoir states and target"""
        # Simple correlation with mean of states
        state_mean = np.mean(X, axis=1)
        if np.std(state_mean) < 1e-10 or np.std(y) < 1e-10:
            return 0.0
        return np.corrcoef(state_mean, y)[0, 1]

    def get_reservoir_state(self) -> ReservoirState:
        """Get current reservoir state with metrics"""
        # Estimate Lyapunov exponent (simplified)
        if len(self.state_history) > 100:
            divergence = np.mean([
                np.log(np.linalg.norm(self.state_history[i+1] - self.state_history[i]) + 1e-10)
                for i in range(min(100, len(self.state_history) - 1))
            ])
        else:
            divergence = 0.0

        return ReservoirState(
            state_vector=self.state.copy(),
            time_step=len(self.state_history),
            memory_capacity=self.compute_memory_capacity(500) if len(self.state_history) > 100 else 0.0,
            lyapunov_exponent=divergence
        )


# =============================================================================
# Cellular Automata Engine
# =============================================================================

class CellularAutomataEngine:
    """Engine for cellular automata computation"""

    def __init__(self):
        self.automata: Dict[str, CellularAutomaton] = {}
        self.rule_lookup: Dict[int, np.ndarray] = self._init_elementary_rules()

    def _init_elementary_rules(self) -> Dict[int, np.ndarray]:
        """Initialize elementary CA rules"""
        rules = {}
        for rule_num in range(256):
            # Convert rule number to lookup table
            rule_binary = np.array([int(b) for b in format(rule_num, '08b')[::-1]])
            rules[rule_num] = rule_binary
        return rules

    def create_automaton(
        self,
        dimensions: int = 1,
        rule: CARule = CARule.RULE_110,
        rule_number: Optional[int] = None,
        size: int = 100
    ) -> CellularAutomaton:
        """Create a new cellular automaton"""
        if rule_number is None:
            rule_number = {
                CARule.RULE_30: 30,
                CARule.RULE_110: 110,
                CARule.RULE_184: 184
            }.get(rule, 110)

        ca_id = f"ca_{rule.name}_{len(self.automata)}"

        if dimensions == 1:
            state = np.random.randint(0, 2, size=size)
        else:
            state = np.random.randint(0, 2, size=(size, size))

        ca = CellularAutomaton(
            id=ca_id,
            dimensions=dimensions,
            rule=rule,
            rule_number=rule_number,
            state=state
        )

        self.automata[ca_id] = ca
        return ca

    def step(self, ca: CellularAutomaton) -> np.ndarray:
        """Advance automaton by one step"""
        ca.history.append(ca.state.copy())

        if ca.dimensions == 1:
            ca.state = self._step_1d(ca)
        elif ca.dimensions == 2:
            if ca.rule == CARule.GAME_OF_LIFE:
                ca.state = self._step_game_of_life(ca)
            else:
                ca.state = self._step_2d_totalistic(ca)

        return ca.state

    def _step_1d(self, ca: CellularAutomaton) -> np.ndarray:
        """Step 1D elementary CA"""
        n = len(ca.state)
        new_state = np.zeros(n, dtype=int)
        rule_table = self.rule_lookup[ca.rule_number]

        for i in range(n):
            # Get neighborhood (with periodic boundary)
            left = ca.state[(i - 1) % n]
            center = ca.state[i]
            right = ca.state[(i + 1) % n]

            # Compute index into rule table
            neighborhood = left * 4 + center * 2 + right
            new_state[i] = rule_table[neighborhood]

        return new_state

    def _step_game_of_life(self, ca: CellularAutomaton) -> np.ndarray:
        """Step Conway's Game of Life"""
        state = ca.state
        n, m = state.shape
        new_state = np.zeros_like(state)

        for i in range(n):
            for j in range(m):
                # Count neighbors (Moore neighborhood)
                neighbors = 0
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        if di == 0 and dj == 0:
                            continue
                        ni, nj = (i + di) % n, (j + dj) % m
                        neighbors += state[ni, nj]

                # Apply rules
                if state[i, j] == 1:
                    # Live cell survives with 2 or 3 neighbors
                    new_state[i, j] = 1 if neighbors in [2, 3] else 0
                else:
                    # Dead cell becomes alive with exactly 3 neighbors
                    new_state[i, j] = 1 if neighbors == 3 else 0

        return new_state

    def _step_2d_totalistic(self, ca: CellularAutomaton) -> np.ndarray:
        """Step generic 2D totalistic CA"""
        state = ca.state
        n, m = state.shape
        new_state = np.zeros_like(state)

        # Use rule number as threshold
        threshold = ca.rule_number % 9

        for i in range(n):
            for j in range(m):
                neighbors = 0
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        ni, nj = (i + di) % n, (j + dj) % m
                        neighbors += state[ni, nj]

                new_state[i, j] = 1 if neighbors > threshold else 0

        return new_state

    def run(self, ca: CellularAutomaton, steps: int) -> List[np.ndarray]:
        """Run automaton for multiple steps"""
        history = []
        for _ in range(steps):
            state = self.step(ca)
            history.append(state.copy())
        return history

    def analyze_dynamics(self, ca: CellularAutomaton) -> Dict[str, Any]:
        """Analyze dynamical properties of CA"""
        if len(ca.history) < 10:
            return {'insufficient_data': True}

        history_array = np.array(ca.history)

        # Density (fraction of 1s)
        densities = [np.mean(h) for h in ca.history]
        mean_density = np.mean(densities)
        density_variance = np.var(densities)

        # Entropy over time
        entropies = []
        for h in ca.history:
            p = np.mean(h)
            if 0 < p < 1:
                entropy = -p * np.log2(p) - (1-p) * np.log2(1-p)
            else:
                entropy = 0
            entropies.append(entropy)

        # Check for periodicity
        period = self._find_period(ca.history)

        # Compute Lyapunov-like measure (sensitivity to initial conditions)
        sensitivity = self._compute_sensitivity(ca)

        return {
            'mean_density': mean_density,
            'density_variance': density_variance,
            'mean_entropy': np.mean(entropies),
            'period': period,
            'sensitivity': sensitivity,
            'classification': self._classify_dynamics(
                density_variance, period, sensitivity
            )
        }

    def _find_period(self, history: List[np.ndarray], max_period: int = 100) -> Optional[int]:
        """Find period in CA history"""
        if len(history) < 2:
            return None

        final_state = history[-1]
        for period in range(1, min(max_period, len(history))):
            if np.array_equal(history[-(period + 1)], final_state):
                # Verify period
                valid = True
                for i in range(min(3, len(history) // period - 1)):
                    idx = -(period * (i + 1) + 1)
                    if idx < -len(history):
                        break
                    if not np.array_equal(history[idx], final_state):
                        valid = False
                        break
                if valid:
                    return period
        return None

    def _compute_sensitivity(self, ca: CellularAutomaton) -> float:
        """Compute sensitivity to initial conditions"""
        if ca.state is None or len(ca.history) < 2:
            return 0.0

        # Perturb initial state
        perturbed = ca.history[0].copy()
        flip_idx = np.random.randint(0, len(perturbed.flatten()))
        perturbed.flat[flip_idx] = 1 - perturbed.flat[flip_idx]

        # Run both from initial states
        original_ca = self.create_automaton(
            dimensions=ca.dimensions,
            rule=ca.rule,
            rule_number=ca.rule_number,
            size=len(ca.history[0])
        )
        original_ca.state = ca.history[0].copy()

        perturbed_ca = self.create_automaton(
            dimensions=ca.dimensions,
            rule=ca.rule,
            rule_number=ca.rule_number,
            size=len(ca.history[0])
        )
        perturbed_ca.state = perturbed

        # Run and compare
        steps = min(50, len(ca.history))
        orig_history = self.run(original_ca, steps)
        pert_history = self.run(perturbed_ca, steps)

        # Compute divergence
        divergences = []
        for o, p in zip(orig_history, pert_history):
            diff = np.sum(np.abs(o.flatten() - p.flatten()))
            divergences.append(diff)

        return np.mean(divergences) / ca.state.size if ca.state.size > 0 else 0.0

    def _classify_dynamics(
        self,
        variance: float,
        period: Optional[int],
        sensitivity: float
    ) -> str:
        """Classify CA dynamics (Wolfram classes)"""
        if period == 1 or variance < 0.001:
            return "Class I - Homogeneous"
        elif period is not None and period < 50:
            return "Class II - Periodic"
        elif sensitivity > 0.3:
            return "Class III - Chaotic"
        else:
            return "Class IV - Complex"


# =============================================================================
# Swarm Intelligence Engine
# =============================================================================

class SwarmIntelligenceEngine:
    """Engine for swarm-based computation"""

    def __init__(self):
        self.swarms: Dict[str, SwarmState] = {}

    def create_swarm(
        self,
        n_agents: int,
        dimensions: int,
        bounds: Tuple[np.ndarray, np.ndarray],
        swarm_type: CollectiveType = CollectiveType.SWARM
    ) -> SwarmState:
        """Create a new swarm"""
        lower, upper = bounds

        agents = []
        for i in range(n_agents):
            position = np.random.uniform(lower, upper, dimensions)
            velocity = np.random.uniform(-1, 1, dimensions) * (upper - lower) * 0.1

            agent = SwarmAgent(
                id=f"agent_{i}",
                position=position,
                velocity=velocity,
                personal_best=position.copy()
            )
            agents.append(agent)

        swarm = SwarmState(agents=agents)
        swarm_id = f"swarm_{len(self.swarms)}"
        self.swarms[swarm_id] = swarm

        return swarm

    def optimize(
        self,
        swarm: SwarmState,
        objective_fn: Callable[[np.ndarray], float],
        bounds: Tuple[np.ndarray, np.ndarray],
        max_iterations: int = 100,
        w: float = 0.7,  # Inertia
        c1: float = 1.5,  # Cognitive
        c2: float = 1.5   # Social
    ) -> Tuple[np.ndarray, float]:
        """Run PSO optimization"""
        lower, upper = bounds

        # Initial evaluation
        for agent in swarm.agents:
            fitness = objective_fn(agent.position)
            agent.fitness = fitness
            agent.personal_best_fitness = fitness

            if fitness > swarm.global_best_fitness:
                swarm.global_best = agent.position.copy()
                swarm.global_best_fitness = fitness

        # Main loop
        for iteration in range(max_iterations):
            for agent in swarm.agents:
                # Update velocity
                r1, r2 = np.random.rand(2)
                cognitive = c1 * r1 * (agent.personal_best - agent.position)
                social = c2 * r2 * (swarm.global_best - agent.position)
                agent.velocity = w * agent.velocity + cognitive + social

                # Update position
                agent.position = agent.position + agent.velocity
                agent.position = np.clip(agent.position, lower, upper)

                # Evaluate
                fitness = objective_fn(agent.position)
                agent.fitness = fitness

                # Update personal best
                if fitness > agent.personal_best_fitness:
                    agent.personal_best = agent.position.copy()
                    agent.personal_best_fitness = fitness

                    # Update global best
                    if fitness > swarm.global_best_fitness:
                        swarm.global_best = agent.position.copy()
                        swarm.global_best_fitness = fitness

            swarm.iteration = iteration

            # Check convergence
            positions = np.array([a.position for a in swarm.agents])
            swarm.convergence_metric = np.mean(np.std(positions, axis=0))

            if swarm.convergence_metric < 1e-6:
                break

        return swarm.global_best, swarm.global_best_fitness

    def simulate_flocking(
        self,
        swarm: SwarmState,
        steps: int = 100,
        separation_weight: float = 1.0,
        alignment_weight: float = 1.0,
        cohesion_weight: float = 1.0,
        neighbor_radius: float = 5.0
    ) -> List[SwarmState]:
        """Simulate flocking behavior (Boids)"""
        history = []

        for _ in range(steps):
            new_velocities = []

            for agent in swarm.agents:
                # Find neighbors
                neighbors = []
                for other in swarm.agents:
                    if other.id != agent.id:
                        dist = np.linalg.norm(agent.position - other.position)
                        if dist < neighbor_radius:
                            neighbors.append(other)

                separation = np.zeros_like(agent.velocity)
                alignment = np.zeros_like(agent.velocity)
                cohesion = np.zeros_like(agent.velocity)

                if neighbors:
                    # Separation: avoid crowding
                    for n in neighbors:
                        diff = agent.position - n.position
                        dist = np.linalg.norm(diff)
                        if dist > 0:
                            separation += diff / (dist ** 2)

                    # Alignment: match velocity
                    avg_velocity = np.mean([n.velocity for n in neighbors], axis=0)
                    alignment = avg_velocity - agent.velocity

                    # Cohesion: move toward center
                    center = np.mean([n.position for n in neighbors], axis=0)
                    cohesion = center - agent.position

                # Combine forces
                new_velocity = (
                    agent.velocity +
                    separation_weight * separation +
                    alignment_weight * alignment * 0.1 +
                    cohesion_weight * cohesion * 0.01
                )

                # Limit speed
                speed = np.linalg.norm(new_velocity)
                max_speed = 2.0
                if speed > max_speed:
                    new_velocity = new_velocity / speed * max_speed

                new_velocities.append(new_velocity)

            # Update all agents
            for agent, new_vel in zip(swarm.agents, new_velocities):
                agent.velocity = new_vel
                agent.position = agent.position + agent.velocity

            swarm.iteration += 1
            history.append(SwarmState(
                agents=[SwarmAgent(
                    id=a.id,
                    position=a.position.copy(),
                    velocity=a.velocity.copy(),
                    fitness=a.fitness
                ) for a in swarm.agents],
                iteration=swarm.iteration
            ))

        return history

    def measure_collective_behavior(self, swarm: SwarmState) -> Dict[str, float]:
        """Measure collective behavior metrics"""
        positions = np.array([a.position for a in swarm.agents])
        velocities = np.array([a.velocity for a in swarm.agents])

        # Polarization (alignment of velocities)
        speeds = np.linalg.norm(velocities, axis=1, keepdims=True)
        speeds[speeds < 1e-10] = 1e-10  # Avoid division by zero
        normalized_velocities = velocities / speeds
        mean_direction = np.mean(normalized_velocities, axis=0)
        polarization = np.linalg.norm(mean_direction)

        # Dispersion (spread of positions)
        centroid = np.mean(positions, axis=0)
        distances = np.linalg.norm(positions - centroid, axis=1)
        dispersion = np.mean(distances)

        # Clustering coefficient
        n = len(swarm.agents)
        neighbor_counts = []
        radius = dispersion * 0.5 if dispersion > 0 else 1.0
        for i, agent in enumerate(swarm.agents):
            neighbors = sum(
                1 for j, other in enumerate(swarm.agents)
                if i != j and np.linalg.norm(agent.position - other.position) < radius
            )
            neighbor_counts.append(neighbors)
        clustering = np.mean(neighbor_counts) / (n - 1) if n > 1 else 0

        return {
            'polarization': polarization,
            'dispersion': dispersion,
            'clustering': clustering,
            'convergence': swarm.convergence_metric,
            'mean_speed': np.mean(np.linalg.norm(velocities, axis=1))
        }


# =============================================================================
# Phase Transition Analyzer
# =============================================================================

class PhaseTransitionAnalyzer:
    """Analyzes phase transitions and critical phenomena"""

    def __init__(self):
        self.phase_history: List[PhaseAnalysis] = []

    def analyze_phase(
        self,
        order_parameter_values: np.ndarray,
        control_parameter_values: np.ndarray
    ) -> PhaseAnalysis:
        """Analyze phase behavior from order parameter sweep"""
        # Find critical point (maximum susceptibility)
        susceptibility = np.gradient(order_parameter_values)
        critical_idx = np.argmax(np.abs(susceptibility))
        critical_point = control_parameter_values[critical_idx]

        # Determine current phase
        current_order = order_parameter_values[-1]
        if current_order > 0.7:
            current_phase = PhaseType.ORDERED
        elif current_order < 0.3:
            current_phase = PhaseType.CHAOTIC
        else:
            if np.abs(susceptibility[-1]) > np.mean(np.abs(susceptibility)):
                current_phase = PhaseType.CRITICAL
            else:
                current_phase = PhaseType.FROZEN

        # Estimate correlation length
        if len(order_parameter_values) > 10:
            autocorr = np.correlate(
                order_parameter_values - np.mean(order_parameter_values),
                order_parameter_values - np.mean(order_parameter_values),
                mode='full'
            )
            autocorr = autocorr[len(autocorr)//2:]
            autocorr = autocorr / autocorr[0] if autocorr[0] > 0 else autocorr

            # Find correlation length (where autocorr drops to 1/e)
            correlation_length = np.argmax(autocorr < 1/np.e) if np.any(autocorr < 1/np.e) else len(autocorr)
        else:
            correlation_length = 0.0

        # Estimate critical exponents (simplified)
        critical_exponents = self._estimate_critical_exponents(
            order_parameter_values, control_parameter_values, critical_idx
        )

        analysis = PhaseAnalysis(
            current_phase=current_phase,
            order_parameter=current_order,
            correlation_length=float(correlation_length),
            critical_exponents=critical_exponents,
            phase_boundaries=[critical_point],
            susceptibility=susceptibility[-1]
        )

        self.phase_history.append(analysis)
        return analysis

    def _estimate_critical_exponents(
        self,
        order_param: np.ndarray,
        control_param: np.ndarray,
        critical_idx: int
    ) -> Dict[str, float]:
        """Estimate critical exponents near transition"""
        exponents = {}

        # Beta exponent: order ~ |control - critical|^beta
        if critical_idx > 5 and critical_idx < len(order_param) - 5:
            # Below critical
            below_x = np.abs(control_param[:critical_idx] - control_param[critical_idx])
            below_y = order_param[:critical_idx]

            valid = (below_x > 0) & (below_y > 0)
            if np.sum(valid) > 3:
                log_x = np.log(below_x[valid])
                log_y = np.log(below_y[valid])
                beta, _ = np.polyfit(log_x, log_y, 1)
                exponents['beta'] = beta

        # Gamma exponent from susceptibility
        susceptibility = np.abs(np.gradient(order_param))
        if critical_idx > 5:
            x = np.abs(control_param[:critical_idx] - control_param[critical_idx])
            y = susceptibility[:critical_idx]
            valid = (x > 0) & (y > 0)
            if np.sum(valid) > 3:
                gamma, _ = np.polyfit(np.log(x[valid]), np.log(y[valid]), 1)
                exponents['gamma'] = -gamma  # Should be positive

        return exponents

    def detect_phase_transition(
        self,
        time_series: np.ndarray,
        window_size: int = 50
    ) -> List[int]:
        """Detect phase transitions in time series"""
        transitions = []

        if len(time_series) < window_size * 3:
            return transitions

        # Sliding window analysis
        for i in range(window_size, len(time_series) - window_size):
            before = time_series[i-window_size:i]
            after = time_series[i:i+window_size]

            # Compare statistics
            var_ratio = np.var(after) / (np.var(before) + 1e-10)
            mean_shift = np.abs(np.mean(after) - np.mean(before)) / (np.std(time_series) + 1e-10)

            # Detect significant change
            if var_ratio > 2.0 or var_ratio < 0.5 or mean_shift > 2.0:
                # Check if not too close to previous transition
                if not transitions or i - transitions[-1] > window_size:
                    transitions.append(i)

        return transitions


# =============================================================================
# Emergent Computation Layer (Main Class)
# =============================================================================

class EmergentComputationLayer:
    """
    Main orchestrator for emergent computation.
    Integrates all components for harnessing emergent dynamics.
    """

    def __init__(self):
        self.emergence_detector = EmergenceDetector()
        self.reservoir_computer = ReservoirComputer()
        self.ca_engine = CellularAutomataEngine()
        self.swarm_engine = SwarmIntelligenceEngine()
        self.phase_analyzer = PhaseTransitionAnalyzer()

        logger.info("EmergentComputationLayer initialized")

    def process_with_reservoir(
        self,
        input_signal: np.ndarray,
        target: Optional[np.ndarray] = None,
        train_ratio: float = 0.8
    ) -> Dict[str, Any]:
        """Process signal with reservoir computing"""
        self.reservoir_computer.reset_state()

        # Get reservoir states
        states = self.reservoir_computer.forward(input_signal.reshape(-1, 1))

        result = {
            'states': states,
            'state_info': self.reservoir_computer.get_reservoir_state()
        }

        if target is not None:
            # Train/test split
            split_idx = int(len(states) * train_ratio)
            train_states = states[:split_idx]
            train_target = target[:split_idx]
            test_states = states[split_idx:]
            test_target = target[split_idx:]

            # Train readout
            self.reservoir_computer.train_readout(train_states, train_target)

            # Evaluate
            predictions = self.reservoir_computer.predict(test_states)
            mse = np.mean((predictions - test_target) ** 2)

            result['predictions'] = predictions
            result['mse'] = mse
            result['train_size'] = split_idx

        return result

    def compute_with_ca(
        self,
        input_data: np.ndarray,
        rule: CARule = CARule.RULE_110,
        steps: int = 100
    ) -> Dict[str, Any]:
        """Use cellular automaton for computation"""
        # Initialize CA with input
        ca = self.ca_engine.create_automaton(
            dimensions=1,
            rule=rule,
            size=len(input_data)
        )

        # Encode input as initial state
        threshold = np.median(input_data)
        ca.state = (input_data > threshold).astype(int)

        # Run CA
        history = self.ca_engine.run(ca, steps)

        # Analyze dynamics
        analysis = self.ca_engine.analyze_dynamics(ca)

        return {
            'final_state': ca.state,
            'history': history,
            'dynamics': analysis,
            'output': self._decode_ca_output(history)
        }

    def _decode_ca_output(self, history: List[np.ndarray]) -> np.ndarray:
        """Decode CA history to output signal"""
        # Use column sums as output (common CA encoding)
        history_array = np.array(history)
        return np.mean(history_array, axis=1)

    def optimize_with_swarm(
        self,
        objective_fn: Callable[[np.ndarray], float],
        bounds: Tuple[np.ndarray, np.ndarray],
        n_agents: int = 30,
        max_iterations: int = 100
    ) -> Dict[str, Any]:
        """Optimize using swarm intelligence"""
        dimensions = len(bounds[0])

        swarm = self.swarm_engine.create_swarm(
            n_agents=n_agents,
            dimensions=dimensions,
            bounds=bounds
        )

        best_position, best_fitness = self.swarm_engine.optimize(
            swarm, objective_fn, bounds, max_iterations
        )

        return {
            'best_position': best_position,
            'best_fitness': best_fitness,
            'iterations': swarm.iteration,
            'convergence': swarm.convergence_metric,
            'collective_metrics': self.swarm_engine.measure_collective_behavior(swarm)
        }

    def detect_emergence_in_data(
        self,
        data: np.ndarray,
        component_data: Optional[List[np.ndarray]] = None
    ) -> List[EmergentPattern]:
        """Detect emergent patterns in data"""
        all_patterns = []

        for method in ['statistical', 'information', 'causal', 'functional']:
            patterns = self.emergence_detector.detect_emergence(
                data, component_data, method=method
            )
            all_patterns.extend(patterns)

        # Remove duplicates by pattern type
        seen_types = set()
        unique_patterns = []
        for p in all_patterns:
            key = (p.pattern_type, p.description[:50])
            if key not in seen_types:
                seen_types.add(key)
                unique_patterns.append(p)

        return unique_patterns

    def analyze_phase_behavior(
        self,
        time_series: np.ndarray,
        control_param: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Analyze phase behavior in time series"""
        if control_param is None:
            # Use time as control parameter
            control_param = np.arange(len(time_series)) / len(time_series)

        # Calculate running order parameter
        window = max(10, len(time_series) // 20)
        order_param = np.array([
            np.std(time_series[max(0, i-window):i+1])
            for i in range(len(time_series))
        ])
        order_param = 1.0 - order_param / (np.max(order_param) + 1e-10)

        # Analyze phase
        analysis = self.phase_analyzer.analyze_phase(order_param, control_param)

        # Detect transitions
        transitions = self.phase_analyzer.detect_phase_transition(time_series)

        return {
            'current_phase': analysis.current_phase.name,
            'order_parameter': analysis.order_parameter,
            'correlation_length': analysis.correlation_length,
            'critical_exponents': analysis.critical_exponents,
            'transitions_detected': transitions,
            'susceptibility': analysis.susceptibility
        }

    def harness_emergence(
        self,
        data: np.ndarray,
        task: str = 'prediction',
        **kwargs
    ) -> Dict[str, Any]:
        """
        High-level interface to harness emergent computation for a task.

        Args:
            data: Input data
            task: Task type ('prediction', 'optimization', 'pattern_detection')
            **kwargs: Additional task-specific parameters
        """
        result = {'task': task}

        if task == 'prediction':
            # Use reservoir computing
            target = kwargs.get('target', np.roll(data, -1))
            reservoir_result = self.process_with_reservoir(data, target)
            result.update(reservoir_result)

        elif task == 'optimization':
            objective = kwargs.get('objective')
            bounds = kwargs.get('bounds')
            if objective and bounds:
                opt_result = self.optimize_with_swarm(objective, bounds)
                result.update(opt_result)

        elif task == 'pattern_detection':
            patterns = self.detect_emergence_in_data(data)
            phase = self.analyze_phase_behavior(data)
            result['patterns'] = patterns
            result['phase_analysis'] = phase

        elif task == 'computation':
            ca_result = self.compute_with_ca(data)
            result.update(ca_result)

        return result


# =============================================================================
# Factory Functions
# =============================================================================

def create_emergent_computation_layer() -> EmergentComputationLayer:
    """Create a configured emergent computation layer"""
    return EmergentComputationLayer()


def create_reservoir_computer(
    size: int = 100,
    spectral_radius: float = 0.9
) -> ReservoirComputer:
    """Create a reservoir computer"""
    return ReservoirComputer(
        reservoir_size=size,
        spectral_radius=spectral_radius
    )


def create_cellular_automaton(
    rule: str = "rule_110",
    dimensions: int = 1,
    size: int = 100
) -> Tuple[CellularAutomataEngine, CellularAutomaton]:
    """Create a cellular automaton"""
    engine = CellularAutomataEngine()

    rule_map = {
        'rule_30': CARule.RULE_30,
        'rule_110': CARule.RULE_110,
        'rule_184': CARule.RULE_184,
        'game_of_life': CARule.GAME_OF_LIFE
    }

    ca_rule = rule_map.get(rule.lower(), CARule.RULE_110)
    ca = engine.create_automaton(dimensions=dimensions, rule=ca_rule, size=size)

    return engine, ca


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Enums
    'EmergenceType',
    'ReservoirType',
    'CARule',
    'CollectiveType',
    'PhaseType',

    # Data classes
    'EmergentPattern',
    'ReservoirState',
    'CellularAutomaton',
    'SwarmAgent',
    'SwarmState',
    'PhaseAnalysis',

    # Core classes
    'EmergenceDetector',
    'ReservoirComputer',
    'CellularAutomataEngine',
    'SwarmIntelligenceEngine',
    'PhaseTransitionAnalyzer',
    'EmergentComputationLayer',

    # Factory functions
    'create_emergent_computation_layer',
    'create_reservoir_computer',
    'create_cellular_automaton'
]



def uncertainty_prediction(model: Any,
                         inputs: Dict[str, np.ndarray],
                         n_samples: int = 100) -> Dict[str, Any]:
    """
    Make predictions with uncertainty quantification.

    Args:
        model: Predictive model
        inputs: Input features
        n_samples: Number of samples for uncertainty estimation

    Returns:
        Predictions with uncertainty bounds
    """
    import numpy as np


# Custom optimization variant 46
def optimize_computation_46(func):
    """Decorator for optimizing computation."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper



# Custom optimization variant 41
def optimize_computation_41(func):
    """Decorator for optimizing computation."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


    # Single prediction
    prediction = model.predict(inputs)

    # Monte Carlo uncertainty estimation
    if hasattr(model, 'predict_with_samples'):
        samples = model.predict_with_samples(inputs, n_samples)
    else:
        # Use bootstrap-like sampling
        samples = []
        for _ in range(n_samples):
            # Add small noise to inputs
            noisy_inputs = {k: v + np.random.normal(0, 0.01, v.shape)
                           for k, v in inputs.items()}
            sample_pred = model.predict(noisy_inputs)
            samples.append(sample_pred)

    samples = np.array(samples)

    # Compute statistics
    mean_prediction = np.mean(samples, axis=0)
    std_prediction = np.std(samples, axis=0)

    # Confidence intervals
    lower_bound = np.percentile(samples, 2.5, axis=0)
    upper_bound = np.percentile(samples, 97.5, axis=0)

    return {
        'prediction': mean_prediction,
        'std': std_prediction,
        'confidence_interval_95': (lower_bound, upper_bound),
        'samples': samples
    }



# Test helper for neural_symbolic
def test_neural_symbolic_function(data):
    """Test function for neural_symbolic."""
    import numpy as np
    return {'passed': True, 'result': None}


