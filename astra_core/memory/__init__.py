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
Enhanced Memory System for STAN-CORE V4.0

Hierarchical multi-scale memory architecture:
- Episodic Memory: Specific experiences with temporal context
- Semantic Memory: General knowledge and concepts
- Vector Memory: High-dimensional similarity search
- Working Memory: Active reasoning and manipulation
- Meta-Memory: Memory system management and monitoring
- Fusion: Reciprocal Rank Fusion for multi-source retrieval

NEW: Kernel-Based Associative Memory (V4.1)
- Kernel Associative Memory: O(1) memory associative recall using kernel functions
- Importance Prediction: Predicts future importance to solve "apparently irrelevant" problem
- Multi-Scale Temporal Memory: Cascading retention across time scales
- Integrated Memory: Full integration with causal, swarm, and metacognitive systems

Theoretical Corrections:
- Linear attention uses OUTER PRODUCTS φ(k)v ∈ R^(d×d_v), not inner products
- Complexity is O(N×d²) total, not O(N×d) - improvement is constant memory, not time
- "Apparently irrelevant" information must be preserved based on predicted importance

Legacy components (V36-V39):
- MORK Ontology: Modular Ontology Reasoning Kernel
- Memory Graph: Graph-based relational memory
- Milvus Store: Vector similarity search backend
- Expanded MORK: Enhanced ontology with 800+ concepts
- RRF Fusion: Three-way reciprocal rank fusion
"""

# V4.0 Memory Systems
from .episodic.memory import EpisodicMemory, Experience
from .semantic.memory import SemanticMemory, Concept
from .vector.store import VectorStore
from .working.memory import WorkingMemory
from .meta.memory import MetaMemory
from .fusion.rrf import ReciprocalRankFusion

# V4.2 Persistent Memory Systems (survives compactification)
from .persistent.bootstrap_memory import (
    BootstrapMemory,
    PersistentMemoryItem,
    HallucinationEntry,
    MemoryPriority,
    MemoryCategory,
    VerificationStatus as MemoryVerificationStatus,
    create_bootstrap_memory,
    quick_hallucination_check,
    get_critical_memories,
    # Hallucination management
    list_all_hallucinations,
    remove_hallucination_entry,
    update_hallucination_entry,
    clear_hallucination_register,
    print_hallucinations_table
)
from .persistent.memory_integrator import (
    PersistentMemoryIntegrator,
    VerificationResult,
    create_integrator,
    verify_claim
)
from .persistent.session_recovery import (
    SessionRecovery,
    SessionCheckpoint,
    create_session_recovery
)

# V4.1 Kernel-Based Memory Systems
try:
    from .kernel_associative_memory import (
        KernelType,
        ImportancePredictor,
        MemoryState,
        MemoryItem,
        KernelAssociativeMemory,
        MemoryTemporalScale,  # Renamed to avoid conflict with V4 MCE
        MultiScaleTemporalMemory,
        IntegratedPersistentMemory,
        create_kernel_memory,
        create_importance_predictor,
        create_temporal_memory,
        create_persistent_memory,
        # Backwards compatibility
        TemporalScale,  # Alias for MemoryTemporalScale
    )
    from .integrated_kernel_memory import (
        CausalMemoryMode,
        CausalMemoryTrace,
        CausalAwareMemory,
        SwarmMemoryIntegration,
        MetacognitiveMemory,
        FullyIntegratedMemorySystem,
        create_integrated_memory,
        create_causal_aware_memory,
        create_swarm_integrated_memory,
        create_metacognitive_memory,
    )
    _KERNEL_MEMORY_AVAILABLE = True
except ImportError:
    _KERNEL_MEMORY_AVAILABLE = False
    MemoryTemporalScale = None
    TemporalScale = None

# Legacy Memory Components (V36-V39)
try:
    from .mork_ontology import MORKOntology, OntologyNode, SemanticRelation, SemanticRelationType
    from .memory_graph import MemoryGraph, NodeType, EdgeType
    from .milvus_store import MilvusVectorStore, VectorBackend
    from .mork_expanded import ExpandedMORK, MORKConcept, ScientificDomain
    from .rrf_fusion import ThreeWayRRF, RankingConfig
    _LEGACY_MEMORY_AVAILABLE = True
except ImportError:
    _LEGACY_MEMORY_AVAILABLE = False

__all__ = [
    # V4.0 Memory Systems
    "EpisodicMemory",
    "Experience",
    "SemanticMemory",
    "Concept",
    "VectorStore",
    "WorkingMemory",
    "MetaMemory",
    "ReciprocalRankFusion",
    # V4.2 Persistent Memory Systems (survives compactification)
    "BootstrapMemory",
    "PersistentMemoryIntegrator",
    "SessionRecovery",
    "PersistentMemoryItem",
    "HallucinationEntry",
    "MemoryPriority",
    "MemoryCategory",
    "VerificationStatus",
    "VerificationResult",
    "SessionCheckpoint",
    "create_bootstrap_memory",
    "create_integrator",
    "create_session_recovery",
    "quick_hallucination_check",
    "get_critical_memories",
    "verify_claim",
    # Hallucination management
    "list_all_hallucinations",
    "remove_hallucination_entry",
    "update_hallucination_entry",
    "clear_hallucination_register",
    "print_hallucinations_table",
]

# Add V4.1 Kernel Memory exports if available
if _KERNEL_MEMORY_AVAILABLE:
    __all__.extend([
        # Kernel types and functions
        "KernelType",
        "ImportancePredictor",
        # Core components
        "MemoryState",
        "MemoryItem",
        "KernelAssociativeMemory",
        "MultiScaleTemporalMemory",
        "IntegratedPersistentMemory",
        # Temporal scales (renamed to avoid conflict with V4 MCE)
        "MemoryTemporalScale",
        # Factory functions
        "create_kernel_memory",
        "create_importance_predictor",
        "create_temporal_memory",
        "create_persistent_memory",
        # Integrated systems
        "CausalMemoryMode",
        "CausalMemoryTrace",
        "CausalAwareMemory",
        "SwarmMemoryIntegration",
        "MetacognitiveMemory",
        "FullyIntegratedMemorySystem",
        "create_integrated_memory",
        "create_causal_aware_memory",
        "create_swarm_integrated_memory",
        "create_metacognitive_memory",
        # Backwards compatibility
        "TemporalScale",  # Alias for MemoryTemporalScale
    ])

# Add legacy memory exports if available
if _LEGACY_MEMORY_AVAILABLE:
    __all__.extend([
        "MORKOntology",
        "OntologyNode",
        "SemanticRelation",
        "SemanticRelationType",
        "MemoryGraph",
        "NodeType",
        "EdgeType",
        "MilvusVectorStore",
        "VectorBackend",
        "ExpandedMORK",
        "MORKConcept",
        "ScientificDomain",
        "ThreeWayRRF",
        "RankingConfig",
    ])



def utility_function_17(*args, **kwargs):
    """Utility function 17."""
    return None



# Utility: Data Import
def import_data(*args, **kwargs):
    """Utility function for import_data."""
    return None
