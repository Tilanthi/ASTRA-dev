"""
Swarm Intelligence & MORK Integration

MeTTa Optimal Reduction Kernel (MORK) - Stigmergic Reasoning Engine
Based on CSIG-main (Collective Symbolic Intelligence - Gordon Edition)

Provides:
- Symbolic reasoning substrate for S-expressions
- Stigmergic field persistence (tau, eta, c_k)
- Gordon's biological principles
- Multi-colony knowledge store
- Swarm orchestration with pheromone dynamics
- Vector memory and knowledge graph

Merged from:
- mork/: Core MORK models and client
- swarm_intelligence/: Orchestrator and evolution
- swarm_memory/: Memory graph and vector stores

Date: 2025-12-13
Version: 2.0
"""

# Core MORK models
from .models import (
    AgentNamespace,
    BiologicalField,
    FieldType,
    PheromoneField,
    SymbolicAbstraction
)

# MORK client for storage
from .client import (
    MORKClient,
    LocalMORKStorage
)

# Gordon's transforms
from .transforms import (
    GordonTransforms,
    GORDON_PARAMS
)

# Swarm orchestration
from .orchestrator import (
    SwarmOrchestrator,
    SwarmAgent,
    AgentType,
    AgentState,
    AgentConfig
)

# Pheromone dynamics
from ..intelligence.pheromone_dynamics import (
    DigitalPheromoneField,
    PheromoneType,
    PheromoneDeposit
)

# LEAP core evolution
from .leapcore_evolution import (
    LEAPCoreEvolution,
    EvolutionConfig,
    Chromosome,
    Gene
)

# Memory systems
from .memory_graph import (
    MemoryGraph,
    GraphNode,
    GraphEdge
)

from .milvus_store import (
    InMemoryVectorIndex,
    MilvusVectorStore,
    VectorRecord,
    SearchResult
)

from .rrf_fusion import (
    ThreeWayRRF,
    RRFResult,
    RankingConfig
)

# Expanded MORK ontology
from .mork_expanded import (
    ExpandedMORK,
    MORKConcept,
    ScientificDomain
)

__all__ = [
    # Core MORK models
    'AgentNamespace',
    'BiologicalField',
    'FieldType',
    'PheromoneField',
    'SymbolicAbstraction',

    # MORK client
    'MORKClient',
    'LocalMORKStorage',

    # Gordon transforms
    'GordonTransforms',
    'GORDON_PARAMS',

    # Swarm orchestration
    'SwarmOrchestrator',
    'SwarmAgent',
    'AgentType',
    'AgentState',
    'AgentConfig',

    # Pheromone dynamics
    'DigitalPheromoneField',
    'PheromoneType',
    'PheromoneDeposit',

    # LEAP evolution
    'LEAPCoreEvolution',
    'EvolutionConfig',
    'Chromosome',
    'Gene',

    # Memory systems
    'MemoryGraph',
    'GraphNode',
    'GraphEdge',
    'InMemoryVectorIndex',
    'MilvusVectorStore',
    'VectorRecord',
    'SearchResult',
    'ThreeWayRRF',
    'RRFResult',
    'RankingConfig',

    # Expanded MORK
    'ExpandedMORK',
    'MORKConcept',
    'ScientificDomain',
]

__version__ = '2.0'
