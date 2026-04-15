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
ASTRA Live — Knowledge Isolation Mode
Discovers patterns without prior knowledge, generates competing hypotheses,
and performs intervention analysis.

As described in White & Dey (2026), Section 8 (Test Case 6).
"""
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field, asdict
import time

from .causal import pc_algorithm, fci_algorithm, test_intervention, CausalGraph
from .bayesian import rank_hypotheses, score_hypothesis


@dataclass
class DiscoveredPattern:
    variable_x: str
    variable_y: str
    correlation: float
    p_value: float
    classification: str  # "PURE_DISCOVERY", "GUIDED", "KNOWN"
    causal_status: str   # "causal", "confounded", "proxy", "unknown"
    hypothesis_scores: List[Dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class DiscoveryResult:
    patterns: List[DiscoveredPattern]
    causal_graph: Optional[Dict]
    interventions: List[Dict]
    hierarchy: List[Dict]  # Causal importance ranking
    timestamp: float = 0.0
    n_variables: int = 0
    n_samples: int = 0

    def to_dict(self):
        return {
            "patterns": [p.to_dict() for p in self.patterns],
            "causal_graph": self.causal_graph,
            "interventions": self.interventions,
            "hierarchy": self.hierarchy,
            "timestamp": self.timestamp,
            "n_variables": self.n_variables,
            "n_samples": self.n_samples,
        }


def blind_pattern_discovery(data: np.ndarray, variable_names: List[str],
                             alpha: float = 0.05) -> List[DiscoveredPattern]:
    """
    Phase 1: Test all variable pairs for significant correlations
    without using prior expectations.
    """
    patterns = []
    n_vars = len(variable_names)

    for i in range(n_vars):
        for j in range(i + 1, n_vars):
            x = data[:, i]
            y = data[:, j]

            # Skip if insufficient data
            valid = np.isfinite(x) & np.isfinite(y)
            if np.sum(valid) < 10:
                continue

            r, p = stats.pearsonr(x[valid], y[valid])

            if p < alpha:
                # Classify as PURE_DISCOVERY (no prior knowledge used)
                patterns.append(DiscoveredPattern(
                    variable_x=variable_names[i],
                    variable_y=variable_names[j],
                    correlation=float(r),
                    p_value=float(p),
                    classification="PURE_DISCOVERY",
                    causal_status="unknown",
                ))

    # Sort by significance
    patterns.sort(key=lambda p: p.p_value)
    return patterns


def generate_competing_hypotheses(pattern: DiscoveredPattern) -> List[Dict]:
    """
    Phase 3: Generate competing explanations for a discovered pattern.

    For each pattern, generate:
    H1: Causal (X directly causes Y)
    H2: Confounded (Both caused by third variable)
    H3: Selection/Observational bias
    """
    hypotheses = [
        {
            "name": f"Causal: {pattern.variable_x} → {pattern.variable_y}",
            "type": "causal",
            "evidence_fit": min(1.0, abs(pattern.correlation)),
            "plausibility": 0.6,
            "predictive_power": 0.7,
            "simplicity": 0.8,
        },
        {
            "name": f"Confounded: {pattern.variable_x} ↔ {pattern.variable_y} (third variable)",
            "type": "confounded",
            "evidence_fit": min(1.0, abs(pattern.correlation) * 0.9),
            "plausibility": 0.5,
            "predictive_power": 0.4,
            "simplicity": 0.5,
        },
        {
            "name": f"Selection bias: {pattern.variable_x} — {pattern.variable_y} (spurious)",
            "type": "selection",
            "evidence_fit": min(1.0, abs(pattern.correlation) * 0.5),
            "plausibility": 0.3,
            "predictive_power": 0.2,
            "simplicity": 0.6,
        },
    ]

    return rank_hypotheses(hypotheses)


def run_knowledge_isolation(data: np.ndarray, variable_names: List[str],
                             target_variable: str = None,
                             alpha: float = 0.05) -> DiscoveryResult:
    """
    Full knowledge isolation discovery pipeline (6 phases from Test Case 6).

    Phase 1: Blind pattern discovery
    Phase 2: Causal structure discovery (FCI)
    Phase 3: Hypothesis competition
    Phase 4: Dimensional analysis (skipped — requires physical dimensions)
    Phase 5: Physical validation (skipped — requires domain knowledge)
    Phase 6: Intervention analysis
    """
    n_samples, n_vars = data.shape

    # Phase 1: Blind pattern discovery
    patterns = blind_pattern_discovery(data, variable_names, alpha)

    # Phase 2: Causal structure discovery using FCI
    try:
        causal = fci_algorithm(data, variable_names, alpha)
        causal_dict = causal.to_dict()
    except Exception as e:
        causal_dict = {"error": str(e), "variables": variable_names}

    # Phase 3: Hypothesis competition for each pattern
    for pattern in patterns:
        pattern.hypothesis_scores = generate_competing_hypotheses(pattern)

        # Update causal status based on FCI results
        if "edges" in causal_dict:
            for edge in causal_dict["edges"]:
                if (edge.get("source") == pattern.variable_x and edge.get("target") == pattern.variable_y) or \
                   (edge.get("source") == pattern.variable_y and edge.get("target") == pattern.variable_x):
                    if edge.get("edge_type") == "x→":
                        pattern.causal_status = "causal"
                    elif edge.get("edge_type") == "o—o":
                        pattern.causal_status = "confounded"

    # Phase 6: Intervention analysis on top patterns
    interventions = []
    if target_variable and patterns:
        # Test interventions from the top correlated variables to the target
        target_patterns = [p for p in patterns
                          if target_variable in (p.variable_x, p.variable_y)]

        for pattern in target_patterns[:5]:
            cause = pattern.variable_x if pattern.variable_y == target_variable else pattern.variable_y
            effect = target_variable

            try:
                result = test_intervention(data, variable_names, cause, effect)
                interventions.append(result)
            except Exception as e:
                interventions.append({"cause": cause, "effect": effect, "error": str(e)})

    # Build causal importance hierarchy
    hierarchy = []
    if interventions:
        sorted_interventions = sorted(interventions,
                                      key=lambda x: x.get("causal_strength", 0),
                                      reverse=True)
        for i, interv in enumerate(sorted_interventions):
            if "error" not in interv:
                hierarchy.append({
                    "rank": i + 1,
                    "cause": interv["cause"],
                    "effect": interv["effect"],
                    "strength": interv["causal_strength"],
                    "significant": interv.get("significant", False),
                    "direction": interv.get("effect_direction", "unknown"),
                })

    return DiscoveryResult(
        patterns=patterns,
        causal_graph=causal_dict,
        interventions=interventions,
        hierarchy=hierarchy,
        timestamp=time.time(),
        n_variables=n_vars,
        n_samples=n_samples,
    )
