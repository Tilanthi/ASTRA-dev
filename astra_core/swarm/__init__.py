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
