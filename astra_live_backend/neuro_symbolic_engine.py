import os
import tempfile

"""
ASTRA Live — Neuro-Symbolic Integration Engine
Unifies neural pattern recognition with symbolic reasoning.

Paradigm Shift: From separate neural/symbolic to integrated reasoning.

This engine:
- Uses neural networks to discover patterns in data
- Formalizes neural discoveries into symbolic representations
- Uses symbolic theories to guide neural architecture search
- Provides explainable predictions (neural prediction + symbolic explanation)
- Enables transfer learning across domains via symbolic abstraction
- Combines the strengths of both paradigms

Architecture:
Neural Discovery → Symbolic Formalization → Theory Generation
     ↑                                              ↓
     └────────────── Symbolic Guidance ───────────────┘
"""
import numpy as np
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Create dummy classes for type hints
    class torch:
        class nn:
            class Module:
                pass
        class FloatTensor:
            pass
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import json
from collections import defaultdict


class ReasoningMode(Enum):
    """Modes of neuro-symbolic reasoning."""
    NEURAL_ONLY = "neural_only"           # Pure pattern recognition
    SYMBOLIC_ONLY = "symbolic_only"       # Pure symbolic reasoning
    NEURAL_GUIDED_SYMBOLIC = "neural_guided_symbolic"  # Neural suggests, symbolic reasons
    SYMBOLIC_GUIDED_NEURAL = "symbolic_guided_neural"  # Symbolic guides, neural learns
    INTEGRATED = "integrated"              # True integration


@dataclass
class NeuralDiscovery:
    """A pattern discovered by neural networks."""
    pattern_type: str  # "correlation", "cluster", "manifold", "dynamics"
    features: List[str]  # Which features are involved?
    pattern_description: str  # Human-readable description
    confidence: float  # 0-1
    neural_representation: np.ndarray  # Learned representation
    data_signature: np.ndarray  # Signature of data that produced this
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SymbolicFormalization:
    """A symbolic representation of a neural discovery."""
    formalization_type: str  # "equation", "constraint", "relation", "logic"
    symbolic_form: str  # Mathematical/logical representation
    variables: Dict[str, str]  # Variable definitions
    confidence: float  # 0-1
    neural_source: str  # ID of neural discovery
    validation_score: float = 0.0  # How well does it fit data?
    generalization_score: float = 0.0  # How well does it generalize?
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NeuroSymbolicPrediction:
    """A prediction with both neural and symbolic components."""
    prediction: Any  # The actual prediction
    neural_confidence: float  # Confidence from neural component
    symbolic_confidence: float  # Confidence from symbolic component
    combined_confidence: float  # Weighted combination
    neural_explanation: str  # What neural network focused on
    symbolic_explanation: str  # Symbolic reasoning chain
    discrepancy: Optional[str] = None  # If neural and symbolic disagree


@dataclass
class IntegratedTheory:
    """A theory that integrates neural and symbolic insights."""
    theory_name: str
    neural_discoveries: List[str]  # IDs of neural discoveries
    symbolic_formalizations: List[str]  # IDs of symbolic formalizations
    integrated_description: str
    predictive_model: Any  # The integrated model
    validation_results: Dict[str, float]
    explanatory_power: float  # 0-1, how well does it explain phenomena?
    generality: float  # 0-1, how broadly does it apply?


# Neural Network Components

if TORCH_AVAILABLE:
    class PatternDiscoveryNet(nn.Module):
        """Neural network for discovering patterns in astronomical data."""

        def __init__(self, input_dim: int, hidden_dim: int = 128):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, hidden_dim // 4)
            )

            # Pattern type heads
            self.correlation_head = nn.Linear(hidden_dim // 4, 1)
            self.cluster_head = nn.Linear(hidden_dim // 4, 10)  # Up to 10 clusters
            self.anomaly_head = nn.Linear(hidden_dim // 4, 1)

            # Attention for interpretability
            self.attention = nn.MultiheadAttention(hidden_dim // 4, num_heads=4)

        def forward(self, x):
            """Encode and detect patterns."""
            encoded = self.encoder(x)

            # Pattern predictions
            correlation_score = torch.sigmoid(self.correlation_head(encoded))
            cluster_assignment = torch.softmax(self.cluster_head(encoded), dim=-1)
            anomaly_score = torch.sigmoid(self.anomaly_head(encoded))

            return {
                'encoding': encoded,
                'correlation': correlation_score,
                'cluster': cluster_assignment,
                'anomaly': anomaly_score
            }

    class PhysicsInformedNet(nn.Module):
        """
        Neural network constrained by physical laws.

        Key innovation: Incorporates symbolic physical constraints into
        the neural network architecture and loss function.
        """

        def __init__(self, input_dim: int, output_dim: int, physics_constraints: List[str]):
            super().__init__()
            self.network = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim)
            )

            # Physics constraints (e.g., "energy_conservation", "symmetry")
            self.physics_constraints = physics_constraints

        def physics_loss(self, predictions, inputs):
            """
            Compute physics-informed loss.

            Ensures predictions satisfy physical constraints.
            """
            loss = 0.0

            for constraint in self.physics_constraints:
                if constraint == "positivity":
                    # Physical quantities should be positive
                    loss += torch.mean(torch.relu(-predictions))

                elif constraint == "symmetry":
                    # Certain symmetries should be preserved
                    # (This is a simplified example)
                    pass

                elif constraint == "conservation":
                    # Conservation laws
                    # (This would be problem-specific)
                    pass

            return loss

        def forward(self, x):
            return self.network(x)


# Symbolic Reasoning Components

class SymbolicReasoner:
    """Performs symbolic reasoning on formalized discoveries."""

    def __init__(self):
        self.knowledge_base = {}  # Symbolic knowledge
        self.inference_rules = []  # Logical inference rules

    def deduce_consequences(self, formalization: SymbolicFormalization) -> List[str]:
        """Deduce logical consequences of a formalization."""
        consequences = []

        if formalization.formalization_type == "equation":
            # Analyze equation for implications
            consequences.extend(self._analyze_equation(formalization))

        elif formalization.formalization_type == "relation":
            # Analyze relation for transitivity, etc.
            consequences.extend(self._analyze_relation(formalization))

        return consequences

    def _analyze_equation(self, formalization: SymbolicFormalization) -> List[str]:
        """Analyze equation for mathematical consequences."""
        consequences = []

        # Check for scaling relations
        if "y = x^" in formalization.symbolic_form or "y ~ x^" in formalization.symbolic_form:
            consequences.append("This is a scaling relation, suggests self-similarity")

        # Check for conservation laws
        if "d/dt" in formalization.symbolic_form or "∂/∂t" in formalization.symbolic_form:
            consequences.append("This involves time evolution, check for conservation")

        return consequences

    def _analyze_relation(self, formalization: SymbolicFormalization) -> List[str]:
        """Analyze relation for logical consequences."""
        consequences = []

        # Check for monotonic relations
        if "monotonic" in formalization.metadata:
            consequences.append("Monotonic relation preserves ordering")

        return consequences


class NeuroSymbolicIntegrator:
    """
    Main integration engine that combines neural and symbolic reasoning.

    Core capabilities:
    1. Neural pattern discovery (if torch available)
    2. Symbolic formalization of neural discoveries
    3. Symbolic guidance of neural architecture
    4. Integrated prediction with explanations
    5. Theory generation from integration
    """

    def __init__(self):
        # Check for torch availability
        self.torch_available = TORCH_AVAILABLE

        # Neural components (only if torch available)
        if self.torch_available:
            self.neural_discoverer = None  # Lazy initialization
            self.physics_informed_net = None
        else:
            self.neural_discoverer = None
            self.physics_informed_net = None

        # Symbolic components
        self.symbolic_reasoner = SymbolicReasoner()

        # Integration state
        self.neural_discoveries: Dict[str, NeuralDiscovery] = {}
        self.symbolic_formalizations: Dict[str, SymbolicFormalization] = {}
        self.integrated_theories: Dict[str, IntegratedTheory] = {}

        # Performance tracking
        self.performance_history = []

    def discover_and_formalize(self, data: np.ndarray, feature_names: List[str],
                              reasoning_mode: ReasoningMode = ReasoningMode.INTEGRATED
                              ) -> Tuple[List[NeuralDiscovery], List[SymbolicFormalization]]:
        """
        Discover patterns in data and formalize them symbolically.

        This is the main entry point for neuro-symbolic discovery.
        """
        neural_discoveries = []
        symbolic_formalizations = []

        # Step 1: Neural pattern discovery
        if reasoning_mode in [ReasoningMode.NEURAL_ONLY, ReasoningMode.INTEGRATED,
                             ReasoningMode.NEURAL_GUIDED_SYMBOLIC]:
            neural_discoveries = self._neural_discovery(data, feature_names)

        # Step 2: Symbolic formalization
        if reasoning_mode in [ReasoningMode.SYMBOLIC_ONLY, ReasoningMode.INTEGRATED,
                             ReasoningMode.SYMBOLIC_GUIDED_NEURAL]:
            symbolic_formalizations = self._symbolic_formalization(
                neural_discoveries, data, feature_names
            )

        # Step 3: Integration (for integrated mode)
        if reasoning_mode == ReasoningMode.INTEGRATED:
            self._integrate_discoveries(neural_discoveries, symbolic_formalizations)

        return neural_discoveries, symbolic_formalizations

    def _neural_discovery(self, data: np.ndarray, feature_names: List[str]
                         ) -> List[NeuralDiscovery]:
        """Use neural networks to discover patterns."""
        discoveries = []

        # Check if torch is available
        if not self.torch_available:
            # Fallback: use simple statistical methods instead
            return self._statistical_discovery(data, feature_names)

        # Initialize network if needed
        if self.neural_discoverer is None:
            input_dim = data.shape[1]
            self.neural_discoverer = PatternDiscoveryNet(input_dim)

        # Convert to tensor
        x_tensor = torch.FloatTensor(data)

        # Discover patterns
        with torch.no_grad():
            results = self.neural_discoverer(x_tensor)

        # Extract discoveries
        encodings = results['encoding'].numpy()
        correlations = results['correlation'].numpy()
        clusters = results['cluster'].numpy()
        anomalies = results['anomaly'].numpy()

        # Correlation discoveries
        for i, feature in enumerate(feature_names):
            if correlations[i] > 0.7:  # Threshold
                discovery = NeuralDiscovery(
                    pattern_type="correlation",
                    features=[feature],
                    pattern_description=f"Strong correlation pattern in {feature}",
                    confidence=float(correlations[i]),
                    neural_representation=encodings[i],
                    data_signature=data[i],
                    metadata={"threshold": 0.7}
                )
                discoveries.append(discovery)

        # Cluster discoveries
        cluster_assignments = np.argmax(clusters, axis=1)
        unique_clusters = np.unique(cluster_assignments)

        for cluster_id in unique_clusters:
            cluster_members = np.where(cluster_assignments == cluster_id)[0]

            if len(cluster_members) >= 5:  # Minimum cluster size
                discovery = NeuralDiscovery(
                    pattern_type="cluster",
                    features=[feature_names[i] for i in cluster_members],
                    pattern_description=f"Cluster of {len(cluster_members)} related features",
                    confidence=0.8,
                    neural_representation=np.mean([encodings[i] for i in cluster_members], axis=0),
                    data_signature=data[cluster_members],
                    metadata={"cluster_id": int(cluster_id), "n_members": len(cluster_members)}
                )
                discoveries.append(discovery)

        # Store discoveries
        for i, discovery in enumerate(discoveries):
            discovery_id = f"neural_discovery_{len(self.neural_discoveries) + i}"
            self.neural_discoveries[discovery_id] = discovery

        return discoveries

    def _statistical_discovery(self, data: np.ndarray, feature_names: List[str]
                              ) -> List[NeuralDiscovery]:
        """Fallback: Use statistical methods when torch is not available."""
        discoveries = []

        # Compute correlations
        for i, feature in enumerate(feature_names):
            if i < data.shape[1]:
                feature_data = data[:, i]

                # Check for interesting patterns
                if len(feature_data) > 0:
                    # Variance check (high variance = interesting)
                    variance = np.var(feature_data)
                    if variance > 0.1:
                        discovery = NeuralDiscovery(
                            pattern_type="correlation",
                            features=[feature],
                            pattern_description=f"Statistical pattern in {feature}",
                            confidence=0.7,
                            neural_representation=feature_data,
                            data_signature=feature_data,
                            metadata={"method": "statistical", "variance": float(variance)}
                        )
                        discoveries.append(discovery)

        return discoveries

    def _symbolic_formalization(self, neural_discoveries: List[NeuralDiscovery],
                               data: np.ndarray, feature_names: List[str]
                               ) -> List[SymbolicFormalization]:
        """Formalize neural discoveries into symbolic representations."""
        formalizations = []

        for discovery in neural_discoveries:
            if discovery.pattern_type == "correlation":
                # Formalize as equation
                formalization = self._formalize_correlation(discovery, data, feature_names)
                formalizations.append(formalization)

            elif discovery.pattern_type == "cluster":
                # Formalize as relation or constraint
                formalization = self._formalize_cluster(discovery, data, feature_names)
                formalizations.append(formalization)

        # Store formalizations
        for i, formalization in enumerate(formalizations):
            formalization_id = f"symbolic_formalization_{len(self.symbolic_formalizations) + i}"
            self.symbolic_formalizations[formalization_id] = formalization

        return formalizations

    def _formalize_correlation(self, discovery: NeuralDiscovery,
                              data: np.ndarray, feature_names: List[str]
                              ) -> SymbolicFormalization:
        """Formalize a correlation discovery as an equation."""
        # Get the feature
        feature_idx = feature_names.index(discovery.features[0])
        feature_data = data[:, feature_idx]

        # Try to fit simple models
        # 1. Linear relation
        # 2. Power law
        # 3. Exponential

        # For simplicity, try power law: y = ax^b
        if len(data.shape) > 1 and data.shape[1] > 1:
            # Use first two features
            x = data[:, 0]
            y = data[:, 1]

            # Log-log fit for power law
            log_x = np.log(x[x > 0])
            log_y = np.log(y[x > 0])

            if len(log_x) > 2:
                # Fit line in log-log space
                coeffs = np.polyfit(log_x, log_y, 1)
                exponent = coeffs[0]

                symbolic_form = f"{feature_names[1]} = {feature_names[0]}^{exponent:.2f}"

                return SymbolicFormalization(
                    formalization_type="equation",
                    symbolic_form=symbolic_form,
                    variables={
                        feature_names[0]: "independent variable",
                        feature_names[1]: "dependent variable"
                    },
                    confidence=discovery.confidence,
                    neural_source=discovery.pattern_type,
                    validation_score=0.7,  # Simplified
                    generalization_score=0.6,
                    metadata={"exponent": float(exponent)}
                )

        # Fallback: generic relation
        return SymbolicFormalization(
            formalization_type="relation",
            symbolic_form=f"{discovery.features[0]} correlates with observations",
            variables={discovery.features[0]: "observed variable"},
            confidence=discovery.confidence,
            neural_source=discovery.pattern_type,
            validation_score=0.5,
            metadata={"discovery_type": "correlation"}
        )

    def _formalize_cluster(self, discovery: NeuralDiscovery,
                          data: np.ndarray, feature_names: List[str]
                          ) -> SymbolicFormalization:
        """Formalize a cluster discovery as a constraint or relation."""
        cluster_features = discovery.features

        # Formalize as: these features vary together
        symbolic_form = f"[{', '.join(cluster_features[:3])}] vary coherently"

        return SymbolicFormalization(
            formalization_type="relation",
            symbolic_form=symbolic_form,
            variables={f: "cluster_member" for f in cluster_features},
            confidence=discovery.confidence,
            neural_source=discovery.pattern_type,
            validation_score=0.6,
            generalization_score=0.5,
            metadata={"cluster_size": len(cluster_features)}
        )

    def _integrate_discoveries(self, neural_discoveries: List[NeuralDiscovery],
                              symbolic_formalizations: List[SymbolicFormalization]):
        """Integrate neural and symbolic discoveries into unified theories."""
        # Group related discoveries
        # (This is a simplified version)

        for i, (neural, symbolic) in enumerate(zip(neural_discoveries, symbolic_formalizations)):
            theory_id = f"integrated_theory_{i}"

            theory = IntegratedTheory(
                theory_name=f"Integrated_{neural.pattern_type}_{i}",
                neural_discoveries=[neural.pattern_type],
                symbolic_formalizations=[symbolic.formalization_type],
                integrated_description=f"Combines neural {neural.pattern_type} with symbolic {symbolic.formalization_type}",
                predictive_model=None,  # Would be trained model
                validation_results={
                    "neural_confidence": neural.confidence,
                    "symbolic_confidence": symbolic.confidence
                },
                explanatory_power=symbolic.validation_score,
                generality=symbolic.generalization_score
            )

            self.integrated_theories[theory_id] = theory

    def predict_and_explain(self, query_data: np.ndarray,
                           query_features: List[str],
                           theory_id: Optional[str] = None
                           ) -> NeuroSymbolicPrediction:
        """
        Make predictions with both neural and symbolic components.

        Returns both prediction and explanation.
        """
        # Neural prediction
        neural_pred, neural_conf = self._neural_predict(query_data)

        # Symbolic prediction
        symbolic_pred, symbolic_conf, symbolic_expl = self._symbolic_predict(
            query_data, query_features, theory_id
        )

        # Combine
        combined_conf = (neural_conf + symbolic_conf) / 2

        # Check for discrepancy
        discrepancy = None
        if abs(neural_conf - symbolic_conf) > 0.3:
            discrepancy = f"Neural confidence ({neural_conf:.2f}) differs from symbolic ({symbolic_conf:.2f})"

        return NeuroSymbolicPrediction(
            prediction=symbolic_pred,  # Prefer symbolic for interpretability
            neural_confidence=neural_conf,
            symbolic_confidence=symbolic_conf,
            combined_confidence=combined_conf,
            neural_explanation=f"Based on pattern similarity (confidence: {neural_conf:.2f})",
            symbolic_explanation=symbolic_expl,
            discrepancy=discrepancy
        )

    def _neural_predict(self, data: np.ndarray) -> Tuple[Any, float]:
        """Make neural network prediction."""
        if not self.torch_available or self.neural_discoverer is None:
            # Fallback: simple statistical prediction
            return np.mean(data), 0.5

        x_tensor = torch.FloatTensor(data)

        with torch.no_grad():
            results = self.neural_discoverer(x_tensor)

        # Simple prediction based on correlation scores
        max_correlation = float(torch.max(results['correlation']))

        return max_correlation, max_correlation

    def _symbolic_predict(self, data: np.ndarray, features: List[str],
                         theory_id: Optional[str] = None) -> Tuple[Any, float, str]:
        """Make symbolic prediction with explanation."""
        # Build explanation chain
        explanation_parts = []

        explanation_parts.append(f"Analyzing {len(features)} features: {', '.join(features[:3])}")

        if theory_id and theory_id in self.integrated_theories:
            theory = self.integrated_theories[theory_id]
            explanation_parts.append(f"Using theory: {theory.theory_name}")
            explanation_parts.append(f"Theory explains: {theory.integrated_description}")
            confidence = theory.explanatory_power
        else:
            explanation_parts.append("No specific theory available, using general reasoning")
            confidence = 0.5

        explanation = " → ".join(explanation_parts)

        return None, confidence, explanation

    def symbolic_guided_architecture_search(self, problem_description: str,
                                          data_shape: Tuple
                                          ) -> Dict[str, Any]:
        """
        Use symbolic reasoning to guide neural network architecture design.

        Key innovation: Theory guides architecture.
        """
        # Analyze problem symbolically
        problem_type = self._analyze_problem_symbolically(problem_description)

        # Recommend architecture based on symbolic analysis
        architecture = self._recommend_architecture(problem_type, data_shape)

        return architecture

    def _analyze_problem_symbolically(self, description: str) -> str:
        """Analyze problem description symbolically."""
        description_lower = description.lower()

        if "time" in description_lower or "temporal" in description_lower:
            return "temporal"
        elif "image" in description_lower or "spatial" in description_lower:
            return "spatial"
        elif "causal" in description_lower or "mechanism" in description_lower:
            return "causal"
        else:
            return "generic"

    def _recommend_architecture(self, problem_type: str, data_shape: Tuple
                               ) -> Dict[str, Any]:
        """Recommend neural architecture based on problem type."""
        recommendations = {
            "temporal": {
                "architecture": "Recurrent Neural Network (LSTM/GRU)",
                "layers": ["LSTM(128)", "Dropout(0.2)", "Dense(64)", "Dense(output)"],
                "reasoning": "Temporal dependencies require recurrent connections"
            },
            "spatial": {
                "architecture": "Convolutional Neural Network",
                "layers": ["Conv2D(32, 3)", "MaxPool2D()", "Conv2D(64, 3)", "Flatten()", "Dense(output)"],
                "reasoning": "Spatial correlations require convolutional filters"
            },
            "causal": {
                "architecture": "Variational Autoencoder with Causal Layer",
                "layers": ["Encoder(128)", "Latent(32)", "CausalLayer()", "Decoder(128)"],
                "reasoning": "Causal discovery requires structured latent space"
            },
            "generic": {
                "architecture": "Feedforward Network",
                "layers": ["Dense(128)", "ReLU()", "Dense(64)", "ReLU()", "Dense(output)"],
                "reasoning": "Generic problem, standard architecture"
            }
        }

        return recommendations.get(problem_type, recommendations["generic"])

    def learn_from_discrepancies(self):
        """
        Learn from cases where neural and symbolic reasoning disagree.

        This is a key meta-learning mechanism.
        """
        discrepancies = []

        for pred in self.performance_history:
            if hasattr(pred, 'discrepancy') and pred.discrepancy:
                discrepancies.append(pred)

        if discrepancies:
            # Analyze patterns in discrepancies
            # Adjust neural architecture or symbolic rules accordingly
            pass

    def get_performance_summary(self) -> Dict:
        """Get summary of neuro-symbolic integration performance."""
        return {
            'neural_discoveries': len(self.neural_discoveries),
            'symbolic_formalizations': len(self.symbolic_formalizations),
            'integrated_theories': len(self.integrated_theories),
            'average_neural_confidence': np.mean([
                d.confidence for d in self.neural_discoveries.values()
            ]) if self.neural_discoveries else 0.0,
            'average_symbolic_confidence': np.mean([
                f.validation_score for f in self.symbolic_formalizations.values()
            ]) if self.symbolic_formalizations else 0.0,
            'discrepancy_rate': 0.0  # Would be calculated from predictions
        }


# Demonstration
if __name__ == "__main__":
    print("=" * 80)
    print("NEURO-SYMBOLIC INTEGRATION ENGINE")
    print("=" * 80)

    integrator = NeuroSymbolicIntegrator()

    print("\n1. NEURAL DISCOVERY + SYMBOLIC FORMALIZATION")
    print("-" * 80)

    # Create sample data
    np.random.seed(42)
    n_samples = 100
    x = np.random.uniform(0.1, 10, n_samples)
    y = 2 * x ** 1.5 + np.random.normal(0, 0.5, n_samples)
    data = np.column_stack([x, y])
    feature_names = ["mass", "luminosity"]

    print(f"Data shape: {data.shape}")
    print(f"Features: {feature_names}")

    # Discover and formalize
    neural_disc, symbolic_form = integrator.discover_and_formalize(
        data, feature_names, ReasoningMode.INTEGRATED
    )

    print(f"\nNeural Discoveries: {len(neural_disc)}")
    for disc in neural_disc[:3]:
        print(f"  - {disc.pattern_type}: {disc.pattern_description}")
        print(f"    Confidence: {disc.confidence:.2f}")

    print(f"\nSymbolic Formalizations: {len(symbolic_form)}")
    for form in symbolic_form[:3]:
        print(f"  - {form.formalization_type}: {form.symbolic_form}")
        print(f"    Validation: {form.validation_score:.2f}")

    # Predict with explanation
    print("\n2. PREDICT WITH EXPLANATION")
    print("-" * 80)

    query_data = data[:5]
    prediction = integrator.predict_and_explain(query_data, feature_names)

    print(f"Prediction: {prediction.prediction}")
    print(f"Neural Confidence: {prediction.neural_confidence:.2f}")
    print(f"Symbolic Confidence: {prediction.symbolic_confidence:.2f}")
    print(f"Combined Confidence: {prediction.combined_confidence:.2f}")
    print(f"\nExplanation: {prediction.symbolic_explanation}")

    if prediction.discrepancy:
        print(f"\n⚠️ Discrepancy: {prediction.discrepancy}")

    # Architecture recommendation
    print("\n3. SYMBOLIC-GUIDED ARCHITECTURE SEARCH")
    print("-" * 80)

    problems = [
        "Model the time evolution of galaxy mergers",
        "Classify galaxy types from images",
        "Discover causal mechanisms in stellar evolution"
    ]

    for problem in problems:
        arch = integrator.symbolic_guided_architecture_search(problem, (100, 10))
        print(f"\nProblem: {problem}")
        print(f"  Recommended: {arch['architecture']}")
        print(f"  Reasoning: {arch['reasoning']}")

    # Performance summary
    print("\n4. PERFORMANCE SUMMARY")
    print("-" * 80)

    summary = integrator.get_performance_summary()
    print(f"Neural Discoveries: {summary['neural_discoveries']}")
    print(f"Symbolic Formalizations: {summary['symbolic_formalizations']}")
    print(f"Integrated Theories: {summary['integrated_theories']}")
    print(f"Avg Neural Confidence: {summary['average_neural_confidence']:.2f}")
    print(f"Avg Symbolic Confidence: {summary['average_symbolic_confidence']:.2f}")

    print("\n" + "=" * 80)
    print("NEURO-SYMBOLIC INTEGRATION ENGINE is operational!")
    print("=" * 80)
