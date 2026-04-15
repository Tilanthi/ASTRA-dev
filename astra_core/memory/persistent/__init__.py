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
Persistent Memory Module
===========================

Exports for the persistent memory system that survives:
- Context buffer compactification
- Instance to instance changes
- Complete computer restarts

Usage:
    from astra_core.memory.persistent import (
        BootstrapMemory,
        PersistentMemoryIntegrator,
        SessionRecovery,
        create_bootstrap_memory,
        create_integrator
    )

    # Initialize at session start
    bootstrap = create_bootstrap_memory()
    integrator = PersistentMemoryIntegrator(bootstrap)
    integrator.initialize_session()

    # Verify claims before output
    result = integrator.verify_claim_before_output("54 MHz observations")
    if not result.safe:
        print(f"Warning: Known hallucination!")
        print(f"Correct value: {result.hallucination_match.correct_value}")
"""

from .bootstrap_memory import (
    BootstrapMemory,
    MemoryPriority,
    MemoryCategory,
    VerificationStatus,
    PersistentMemoryItem,
    HallucinationEntry,
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

from .memory_integrator import (
    PersistentMemoryIntegrator,
    VerificationResult,
    create_integrator,
    verify_claim
)

from .session_recovery import (
    SessionRecovery,
    SessionCheckpoint,
    create_session_recovery
)

__all__ = [
    # Core classes
    'BootstrapMemory',
    'PersistentMemoryIntegrator',
    'SessionRecovery',

    # Data classes
    'PersistentMemoryItem',
    'HallucinationEntry',
    'SessionCheckpoint',
    'VerificationResult',

    # Enums
    'MemoryPriority',
    'MemoryCategory',
    'VerificationStatus',

    # Factory functions
    'create_bootstrap_memory',
    'create_integrator',
    'create_session_recovery',

    # Convenience functions
    'quick_hallucination_check',
    'get_critical_memories',
    'verify_claim',

    # Hallucination management
    'list_all_hallucinations',
    'remove_hallucination_entry',
    'update_hallucination_entry',
    'clear_hallucination_register',
    'print_hallucinations_table'
]
