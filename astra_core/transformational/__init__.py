"""
ASTRA Transformational Architecture Modules

This package implements the rigorous autonomous discovery architecture that
addresses fundamental issues in the current system:

- Data Scale-Up Layer: N≥30 clouds, train/holdout split
- Prior/Expectation Model: Knowledge base with established relations
- Discovery Gate: 4-stage rigorous validation
- Independent Evaluation Harness: External validation with synthetic ground truth
- Mechanism-Search: Symbolic regression on residuals
- Adversarial Critic: Independent falsification attempts
- Autonomy Loop Controller: Closed-loop scientific process

This architecture moves ASTRA from "sophisticated statistical automation with
a discovery narrative" to "rigorous, autonomous discovery behavior" with
defensible, reproducible results.

Version: 1.0.0
Date: 2026-07-04
"""

from astra_core.transformational.data_scale_layer import (
    DataScaleLayer,
    CloudRecord,
    create_data_scale_layer
)

from astra_core.transformational.prior_knowledge_base import (
    PriorKnowledgeBase,
    ScientificRelation,
    PriorClassification,
    create_prior_knowledge_base
)

from astra_core.transformational.discovery_gate import (
    DiscoveryGate,
    DiscoveryGateResult,
    GateStage,
    GateStatus,
    create_discovery_gate
)

from astra_core.transformational.integration_layer import (
    TransformationalIntegrationLayer,
    IntegrationMode,
    ValidationResult,
    create_integration_layer
)

__all__ = [
    # Data Scale Layer
    'DataScaleLayer',
    'CloudRecord',
    'create_data_scale_layer',

    # Prior Knowledge Base
    'PriorKnowledgeBase',
    'ScientificRelation',
    'PriorClassification',
    'create_prior_knowledge_base',

    # Discovery Gate
    'DiscoveryGate',
    'DiscoveryGateResult',
    'GateStage',
    'GateStatus',
    'create_discovery_gate',

    # Integration Layer
    'TransformationalIntegrationLayer',
    'IntegrationMode',
    'ValidationResult',
    'create_integration_layer',
]

__version__ = '1.0.0'
__author__ = 'ASTRA Transformational Architecture Team'