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
V92 Automated Scientific Discovery Engine
=========================================

This module represents the pinnacle of STAN's evolution - an automated
scientific discovery system capable of generating hypotheses, discovering
causal relationships, applying mathematical intuition, and designing experiments.
"""

from .v92_system import (
    V92CompleteSystem,
    V92Config,
    ScientificDiscovery,
    create_v92_system,
    create_v92_explorer,
    create_v92_validator,
    create_v92_mathematician,
    create_v92_experimentalist
)

from .hypothesis_engine import (
    HypothesisGenerator,
    Hypothesis,
    HypothesisType
)

from .mathematical_intuition import (
    MathematicalIntuitionModule,
    MathematicalConjecture,
    Proof,
    MathDomain,
    ProofStatus
)

from .causal_discovery import (
    CausalDiscoveryEngine,
    CausalModel,
    CausalRelation,
    Intervention,
    Counterfactual,
    DiscoveryMethod
)

from .experimental_design import (
    ExperimentalDesignEngine,
    ExperimentalDesign,
    ExperimentalVariable,
    Treatment,
    ExperimentalType,
    SimulationResult
)

__all__ = [
    # Main system
    'V92CompleteSystem',
    'V92Config',
    'ScientificDiscovery',
    'create_v92_system',
    'create_v92_explorer',
    'create_v92_validator',
    'create_v92_mathematician',
    'create_v92_experimentalist',

    # Hypothesis generation
    'HypothesisGenerator',
    'Hypothesis',
    'HypothesisType',

    # Mathematical intuition
    'MathematicalIntuitionModule',
    'MathematicalConjecture',
    'Proof',
    'MathDomain',
    'ProofStatus',

    # Causal discovery
    'CausalDiscoveryEngine',
    'CausalModel',
    'CausalRelation',
    'Intervention',
    'Counterfactual',
    'DiscoveryMethod',

    # Experimental design
    'ExperimentalDesignEngine',
    'ExperimentalDesign',
    'ExperimentalVariable',
    'Treatment',
    'ExperimentalType',
    'SimulationResult'
]