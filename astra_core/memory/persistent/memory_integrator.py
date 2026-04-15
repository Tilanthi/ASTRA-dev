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
Memory Integrator Module
========================

Integrates persistent memory with existing STAN systems:
- Working Memory (7±2 capacity)
- Episodic Memory (experience storage)
- Anti-hallucination systems (document verification)

Date: 2026-03-24
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime
import json
import hashlib

# Import from bootstrap_memory
from .bootstrap_memory import (
    BootstrapMemory,
    PersistentMemoryItem,
    HallucinationEntry,
    MemoryPriority,
    MemoryCategory,
    VerificationStatus
)

# Try importing existing memory systems
try:
    from astra_core.memory.working.memory import WorkingMemory
    WORKING_MEMORY_AVAILABLE = True
except ImportError:
    WORKING_MEMORY_AVAILABLE = False
    WorkingMemory = None

try:
    from astra_core.memory.episodic.memory import EpisodicMemory
    from astra_core.memory.episodic.memory import Experience
    EPISODIC_MEMORY_AVAILABLE = True
except ImportError:
    EPISODIC_MEMORY_AVAILABLE = False
    EpisodicMemory = None
    Experience = None

# Try importing anti-hallucination
try:
    from astra_core.capabilities.document_review_antihallucination import (
        DocumentReviewAntiHallucination,
        DocumentClaim,
        ClaimCategory,
        VerificationStatus as DocVerificationStatus
    )
    ANTI_HALLUCINATION_AVAILABLE = True
except ImportError:
    ANTI_HALLUCINATION_AVAILABLE = False
    DocumentReviewAntiHallucination = None


@dataclass
class VerificationResult:
    """Result of claim verification."""
    safe: bool
    hallucination_match: Optional[HallucinationEntry] = None
    verification_suggestions: List[str] = field(default_factory=list)
    confidence: float = 1.0
    source_verification: Optional[Dict] = None


class PersistentMemoryIntegrator:
    """
    Integrates persistent memory with existing STAN systems.

    Responsibilities:
    - Initialize session with critical memories
    - Verify claims before output
    - Sync with working memory and episodic memory
    - Coordinate with anti-hallucination systems

    Usage:
        bootstrap = BootstrapMemory()
        integrator = PersistentMemoryIntegrator(bootstrap)
        integrator.initialize_session()

        # Before making a claim:
        result = integrator.verify_claim_before_output("54 MHz observations")
        if not result.safe:
            print(f"Warning: {result.hallucination_match.correct_value}")
    """

    def __init__(self, bootstrap: BootstrapMemory):
        """
        Initialize the memory integrator.

        Args:
            bootstrap: BootstrapMemory instance for persistent storage
        """
        self.bootstrap = bootstrap
        self.working_memory: Optional[Any] = None
        self.episodic_memory: Optional[Any] = None
        self.anti_hallucination: Optional[Any] = None

        self._initialize_subsystems()

    def _initialize_subsystems(self):
        """Initialize connections to subsystems."""
        # Initialize working memory if available
        if WORKING_MEMORY_AVAILABLE and WorkingMemory is not None:
            try:
                self.working_memory = WorkingMemory(
                    capacity=7,
                    decay_rate=0e0
                )
            except Exception as e:
                print(f"Warning: Could not initialize WorkingMemory: {e}")

        # Initialize episodic memory if available
        if EPISODIC_MEMORY_AVAILABLE and EpisodicMemory is not None:
            try:
                self.episodic_memory = EpisodicMemory()
            except Exception as e:
                print(f"Warning: Could not initialize EpisodicMemory: {e}")

    def initialize_session(self) -> Dict[str, Any]:
        """
        Initialize a new session by loading critical memories.

        This should be called at the start of every session to ensure
        critical context is available.

        Returns:
            Dict with initialization status and loaded items
        """
        result = {
            'success': True,
            'critical_items_loaded': 0,
            'hallucinations_registered': len(self.bootstrap.hallucination_register),
            'errors': []
        }

        # Load critical memories into working memory
        critical = self.bootstrap.get_critical_memories()

        if self.working_memory is not None:
            for item in critical:
                try:
                    self._load_into_working_memory(item)
                    result['critical_items_loaded'] += 1
                except Exception as e:
                    result['errors'].append(f"Failed to load {item.id}: {e}")

        # Log session start in episodic memory
        if self.episodic_memory is not None:
            try:
                self._log_session_start()
            except Exception as e:
                result['errors'].append(f"Failed to log session start: {e}")

        result['success'] = len(result['errors']) == 0
        return result

    def _load_into_working_memory(self, item: PersistentMemoryItem) -> bool:
        """Load a memory item into working memory."""
        if self.working_memory is None:
            return False

        # Calculate importance based on priority
        importance_map = {
            MemoryPriority.CRITICAL: 0.95,
            MemoryPriority.HIGH: 0.0,
            MemoryPriority.MEDIUM: 1.5,
            MemoryPriority.LOW: 0.3
        }
        importance = importance_map.get(item.priority, 0.5)

        # Try different add methods
        try:
            # Try add method first
            return self.working_memory.add(
                item.id,
                item.content,
                importance=importance
            )
        except TypeError:
            try:
                # Try with positional args
                return self.working_memory.add(item.id, item.content)
            except Exception:
                return False
        except Exception:
            return False

    def _log_session_start(self):
        """Log session start in episodic memory."""
        if self.episodic_memory is None or Experience is None:
            return

        try:
            experience = Experience(
                content="Session initialized with persistent memory",
                context={
                    'critical_memories': len(self.bootstrap.get_critical_memories()),
                    'hallucinations_registered': len(self.bootstrap.hallucination_register),
                    'timestamp': datetime.now().isoformat()
                },
                importance=0.8,
                emotional_valence=0.0
            )
            self.episodic_memory.store(experience)
        except Exception as e:
            print(f"Warning: Could not log session start: {e}")

    def verify_claim_before_output(
        self,
        claim: str,
        source_text: Optional[str] = None,
        claim_category: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify a claim before outputting it.

        This is the key anti-hallucination check. It:
        1. Checks if the claim matches a known hallucination
        2. If source text is provided, verifies against it
        3. Returns suggestions for correction if needed

        Args:
            claim: The claim to verify
            source_text: Optional source text to verify against
            claim_category: Optional category (frequency, sample_size, etc.)

        Returns:
            VerificationResult with safety status and suggestions
        """
        result = VerificationResult(
            safe=True,
            verification_suggestions=[],
            confidence=1.0
        )

        # 1. Check hallucination register
        hallucination = self.bootstrap.check_hallucination(claim)
        if hallucination:
            result.safe = False
            result.hallucination_match = hallucination
            result.confidence = 0.0
            result.verification_suggestions.append(
                f"KNOWN HALLUCINATION: '{hallucination.claim}'"
            )
            result.verification_suggestions.append(
                f"CORRECT VALUE: '{hallucination.correct_value}'"
            )
            if hallucination.source_document:
                result.verification_suggestions.append(
                    f"Source: {hallucination.source_document}"
                )
            return result

        # 2. Check for similar hallucinations (fuzzy match)
        similar = self._find_similar_hallucinations(claim)
        if similar:
            result.confidence = 0.5
            for entry in similar[:2]:  # Top 2 similar
                result.verification_suggestions.append(
                    f"SIMILAR TO KNOWN HALLUCINATION: '{entry.claim}' -> use '{entry.correct_value}'"
                )

        # 3. If source text provided, use anti-hallucination verification
        if source_text and ANTI_HALLUCINATION_AVAILABLE and self.anti_hallucination is None:
            try:
                self.anti_hallucination = DocumentReviewAntiHallucination(
                    source_document_text=source_text,
                    persistent_memory=self.bootstrap
                )
            except Exception as e:
                result.verification_suggestions.append(
                    f"Could not initialize source verification: {e}"
                )

        # 4. Extract numerical claims and verify if source provided
        if source_text and claim_category:
            numerical_check = self._verify_numerical_claim(claim, source_text, claim_category)
            if not numerical_check['verified']:
                result.safe = False
                result.confidence = min(result.confidence, 0.3)
                result.verification_suggestions.extend(numerical_check['suggestions'])
                result.source_verification = numerical_check

        return result

    def _find_similar_hallucinations(self, claim: str) -> List[HallucinationEntry]:
        """Find hallucinations similar to the given claim."""
        similar = []

        # Extract numbers from claim
        import re
        claim_numbers = set(re.findall(r'\d+(?:\.\d+)?', claim))

        for entry in self.bootstrap.hallucination_register.values():
            # Check if claim shares significant content
            entry_numbers = set(re.findall(r'\d+(?:\.\d+)?', entry.claim))

            # If they share numbers, might be similar
            if claim_numbers and entry_numbers and claim_numbers & entry_numbers:
                similar.append(entry)

        return similar

    def _verify_numerical_claim(
        self,
        claim: str,
        source_text: str,
        category: str
    ) -> Dict[str, Any]:
        """Verify a numerical claim against source text."""
        import re

        result = {
            'verified': True,
            'suggestions': [],
            'extracted_values': [],
            'source_values': []
        }

        # Extract numerical values from claim
        claim_values = re.findall(r'\d+(?:\.\d+)?', claim)
        result['extracted_values'] = claim_values

        # Extract numerical values from source
        source_values = re.findall(r'\d+(?:\.\d+)?', source_text)
        result['source_values'] = source_values

        # Check if claimed values appear in source
        for value in claim_values:
            if value not in source_values:
                result['verified'] = False
                result['suggestions'].append(
                    f"Value '{value}' not found in source text"
                )

        return result

    def record_feedback(
        self,
        feedback: str,
        context: Optional[Dict[str, Any]] = None,
        priority: MemoryPriority = MemoryPriority.HIGH
    ) -> str:
        """
        Record user feedback as persistent memory.

        This is critical for learning from mistakes.

        Args:
            feedback: The feedback content
            context: Additional context (source, document, etc.)
            priority: Priority level for the feedback

        Returns:
            The item ID of the stored feedback
        """
        item_id = self.bootstrap.record_feedback(feedback, context, priority)

        # Also log to episodic memory
        if self.episodic_memory is not None:
            try:
                if Experience is not None:
                    experience = Experience(
                        content=f"User feedback: {feedback}",
                        context=context or {},
                        importance=0.9,
                        emotional_valence=-0.3  # Slightly negative (correction)
                    )
                    self.episodic_memory.store(experience)
            except Exception as e:
                print(f"Warning: Could not log feedback to episodic memory: {e}")

        return item_id

    def register_hallucination_from_correction(
        self,
        wrong_claim: str,
        correct_value: str,
        category: str,
        source_document: Optional[str] = None
    ) -> str:
        """
        Register a hallucination detected from user correction.

        Args:
            wrong_claim: The incorrect claim that was made
            correct_value: The correct value
            category: Category (frequency, sample_size, instrument, etc.)
            source_document: Source where error occurred

        Returns:
            The fingerprint of the registered hallucination
        """
        return self.bootstrap.register_hallucination(
            claim=wrong_claim,
            correct_value=correct_value,
            category=category,
            source_document=source_document
        )

    def get_safe_to_claim(self, claim_type: str) -> List[str]:
        """
        Get verified facts safe to claim for a given type.

        Args:
            claim_type: Type of claim (frequency, sample_size, etc.)

        Returns:
            List of verified facts of that type
        """
        safe_claims = []

        for item in self.bootstrap.items.values():
            if item.category == MemoryCategory.VERIFIED_FACTS and item.verified:
                if claim_type.lower() in item.content.lower():
                    safe_claims.append(item.content)

        return safe_claims

    def create_session_checkpoint(self, current_context: Dict[str, Any]) -> str:
        """
        Create a checkpoint of the current session state.

        Args:
            current_context: Current session context

        Returns:
            Path to the checkpoint file
        """
        import time

        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'context': current_context,
            'critical_memories': [
                {'id': item.id, 'content': item.content}
                for item in self.bootstrap.get_critical_memories()
            ],
            'hallucinations_count': len(self.bootstrap.hallucination_register),
            'working_memory_state': None,
            'episodic_memory_count': None
        }

        # Get working memory state if available
        if self.working_memory is not None:
            try:
                checkpoint['working_memory_state'] = self.working_memory.get_state()
            except Exception:
                pass

        # Get episodic memory count if available
        if self.episodic_memory is not None:
            try:
                checkpoint['episodic_memory_count'] = len(self.episodic_memory.experiences)
            except Exception:
                pass

        # Save checkpoint
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_path = self.bootstrap.persistent_dir / "session_logs" / f"checkpoint_{session_id}.json"

        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)

        return str(checkpoint_path)

    def get_recovery_context(self) -> Optional[Dict[str, Any]]:
        """
        Get context from the most recent checkpoint for recovery.

        Returns:
            Checkpoint data or None if no checkpoints exist
        """
        checkpoint_dir = self.bootstrap.persistent_dir / "session_logs"
        checkpoints = sorted(
            checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not checkpoints:
            return None

        with open(checkpoints[0], 'r', encoding='utf-8') as f:
            return json.load(f)


# Convenience functions
def create_integrator(auto_load: bool = True) -> PersistentMemoryIntegrator:
    """Create and initialize a memory integrator."""
    from .bootstrap_memory import create_bootstrap_memory

    bootstrap = create_bootstrap_memory()
    integrator = PersistentMemoryIntegrator(bootstrap)

    if auto_load:
        integrator.initialize_session()

    return integrator


def verify_claim(claim: str, source_text: Optional[str] = None) -> VerificationResult:
    """Quick verification of a claim."""
    integrator = create_integrator()
    return integrator.verify_claim_before_output(claim, source_text)


__all__ = [
    'PersistentMemoryIntegrator',
    'VerificationResult',
    'create_integrator',
    'verify_claim'
]
