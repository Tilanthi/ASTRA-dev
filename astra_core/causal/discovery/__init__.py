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
Causal Discovery Algorithms

Algorithms for learning causal structure from data:
- PC Algorithm: Constraint-based using conditional independence
- GES Algorithm: Score-based greedy search
- Temporal Discovery: Time-series causal discovery
- Bayesian Structure Learning: Posterior distribution over DAGs
- Expected Information Gain: Active discovery optimization
- Online Causal Learning: Incremental updates from streaming data
"""

from .pc_algorithm import PCAlgorithm
from .ges_algorithm import GESAlgorithm
try:
    from .temporal_discovery import TemporalCausalDiscovery
except ImportError:
    TemporalCausalDiscovery = None
try:
    from .temporal_discovery import granger_causality_test
except ImportError:
    granger_causality_test = None
from .independence import ConditionalIndependenceTest, TestType
try:
    from .independence import correlation_test
except ImportError:
    correlation_test = None

# V47+ Enhanced causal discovery
try:
    from .bayesian_structure_learning import (
        InferenceMethod,
        DAGPosteriorSample,
        BayesianStructureLearningResult,
        BayesianStructureLearner,
        create_bayesian_structure_learner,
    )
except ImportError:
    InferenceMethod = None
    DAGPosteriorSample = None
    BayesianStructureLearningResult = None
    BayesianStructureLearner = None
    create_bayesian_structure_learner = None

try:
    from .eig_calculator import (
        NoiseModel,
        ObservationPlan,
        EIGResult,
        LatentConfounderModel,
        ExpectedInformationGainCalculator,
        create_eig_calculator,
    )
except ImportError:
    NoiseModel = None
    ObservationPlan = None
    EIGResult = None
    LatentConfounderModel = None
    ExpectedInformationGainCalculator = None
    create_eig_calculator = None

try:
    from .online_causal_learning import (
        UpdateMethod,
        ConceptDriftDetector,
        OnlineLearningResult,
        OnlineCausalLearner,
        create_online_causal_learner,
    )
except ImportError:
    UpdateMethod = None
    ConceptDriftDetector = None
    OnlineLearningResult = None
    OnlineCausalLearner = None
    create_online_causal_learner = None

__all__ = [
    "PCAlgorithm",
    "GESAlgorithm",
    "ConditionalIndependenceTest",
    "TestType",
    # V47+ Enhanced modules
    "InferenceMethod",
    "DAGPosteriorSample",
    "BayesianStructureLearningResult",
    "BayesianStructureLearner",
    "create_bayesian_structure_learner",
    "NoiseModel",
    "ObservationPlan",
    "EIGResult",
    "LatentConfounderModel",
    "ExpectedInformationGainCalculator",
    "create_eig_calculator",
    "UpdateMethod",
    "ConceptDriftDetector",
    "OnlineLearningResult",
    "OnlineCausalLearner",
    "create_online_causal_learner",
]

# Conditionally export optional items
if TemporalCausalDiscovery is not None:
    __all__.append("TemporalCausalDiscovery")
if granger_causality_test is not None:
    __all__.append("granger_causality_test")
if correlation_test is not None:
    __all__.append("correlation_test")



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None


