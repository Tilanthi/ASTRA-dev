"""
ASTRA Orchestration Layer - Kubernetes-Style Architecture

Implements cloud-native orchestration patterns for autonomous scientific discovery:
- Declarative API with reconciliation loops
- Controller pattern for resource management
- Operator pattern for domain-specific workflows
- Service mesh for multi-mind orchestration
- Event-driven memory systems
- CRD-based extensibility

Version: 1.0.0
Date: 2026-05-16
"""

from .declarative import (
    DeclarativeResource,
    ResourceSpec,
    ResourceStatus,
    ReconciliationLoop,
    DeclarativeAPI,
    TaskSpec,
    TaskResource,
    ResourceState,
)

from .controllers import (
    Controller,
    ControllerManager,
    WatchEvent,
    EventType,
)

from .operators import (
    Operator,
    DomainOperator,
    FilamentAnalysisOperator,
    DiscoveryOperator,
)

from .control_plane import (
    ControlPlane,
    DataPlane,
    OrchestratedSystem,
)

from .service_mesh import (
    ServiceMesh,
    SidecarProxy,
    MindSidecar,
    MindServiceMesh,
)

from .observability import (
    MetricsCollector,
    ObservabilityStack,
    HealthCheck,
)

from .crd import (
    CustomResourceDefinition,
    CRDRegistry,
    CapabilityCRD,
)

from .integrated_system import (
    OrchestratedASTRASystem,
    OrchestratedASTRAConfig,
    create_orchestrated_astra_system,
)

__all__ = [
    # Declarative API
    "DeclarativeResource",
    "ResourceSpec",
    "ResourceStatus",
    "ReconciliationLoop",
    "DeclarativeAPI",
    "TaskSpec",
    "TaskResource",
    "ResourceState",

    # Controllers
    "Controller",
    "ControllerManager",
    "WatchEvent",
    "EventType",

    # Operators
    "Operator",
    "DomainOperator",
    "FilamentAnalysisOperator",
    "DiscoveryOperator",

    # Control Plane
    "ControlPlane",
    "DataPlane",
    "OrchestratedSystem",

    # Service Mesh
    "ServiceMesh",
    "SidecarProxy",
    "MindSidecar",
    "MindServiceMesh",

    # Observability
    "MetricsCollector",
    "ObservabilityStack",
    "HealthCheck",

    # CRD
    "CustomResourceDefinition",
    "CRDRegistry",
    "CapabilityCRD",

    # Integrated System
    "OrchestratedASTRASystem",
    "OrchestratedASTRAConfig",
    "create_orchestrated_astra_system",
]
