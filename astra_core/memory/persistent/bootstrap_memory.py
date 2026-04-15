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
Bootstrap Memory Module - Persistent Memory System
===================================================

CRITICAL MODULE: Provides persistent memory that survives:
1. Context buffer compactification
2. Instance to instance changes (new Claude sessions)
3. Complete computer restarts

Key Innovation: Uses a BOOTSTRAP.md file that is ALWAYS read at session start,
containing critical memories, hallucination register, and user preferences.

This solves the problem of losing critical context during long conversations
when the context buffer gets compactified.

Date: 2026-03-24
Version: 1.0.0
Motivation: Memory persistence issue raised after PN_24March review incident
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from pathlib import Path
from datetime import datetime
import json
import hashlib
import re
import os


class MemoryPriority(Enum):
    """Priority levels for persistent memory items."""
    CRITICAL = 0  # Always loaded, never evicted - hallucinations, user preferences
    HIGH = 1      # Loaded on startup, rare eviction - feedback, verified facts
    MEDIUM = 2    # Loaded as needed - domain knowledge
    LOW = 3       # Archive, loaded on demand - session summaries


class MemoryCategory(Enum):
    """Categories of persistent memory."""
    HALLUCINATION_REGISTER = "hallucination_register"
    USER_PREFERENCES = "user_preferences"
    USER_FEEDBACK = "user_feedback"
    VERIFIED_FACTS = "verified_facts"
    CRITICAL_KNOWLEDGE = "critical_knowledge"
    SESSION_SUMMARIES = "session_summaries"
    DOCUMENT_VERIFICATION = "document_verification"


class VerificationStatus(Enum):
    """Status of memory verification."""
    VERIFIED = "verified"          # Verified against source
    UNVERIFIED = "unverified"      # Not yet verified
    DISPUTED = "disputed"          # User has disputed this
    SUPERSEDED = "superseded"      # Replaced by newer information


@dataclass
class HallucinationEntry:
    """
    Entry in the hallucination register.

    Tracks claims that were found to be false, along with the correct value
    and verification trail. Used to prevent repeating the same mistakes.
    """
    claim: str                                    # The false claim that was made
    claim_fingerprint: str                        # MD5 hash for quick lookup
    correct_value: str                           # The correct/verified value
    category: str                                 # 'frequency', 'sample_size', 'instrument', etc.
    source_document: Optional[str] = None        # Document where error occurred
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    first_detected: datetime = field(default_factory=datetime.now)
    last_occurrence: Optional[datetime] = None
    occurrences: int = 0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'claim': self.claim,
            'claim_fingerprint': self.claim_fingerprint,
            'correct_value': self.correct_value,
            'category': self.category,
            'source_document': self.source_document,
            'verification_status': self.verification_status.value,
            'first_detected': self.first_detected.isoformat() if isinstance(self.first_detected, datetime) else self.first_detected,
            'last_occurrence': self.last_occurrence.isoformat() if self.last_occurrence else None,
            'occurrences': self.occurrences,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'HallucinationEntry':
        """Create from dictionary."""
        if isinstance(data.get('first_detected'), str):
            data['first_detected'] = datetime.fromisoformat(data['first_detected'])
        if data.get('last_occurrence') and isinstance(data['last_occurrence'], str):
            data['last_occurrence'] = datetime.fromisoformat(data['last_occurrence'])
        if isinstance(data.get('verification_status'), str):
            data['verification_status'] = VerificationStatus(data['verification_status'])
        return cls(**data)


@dataclass
class PersistentMemoryItem:
    """
    A single persistent memory item.

    Represents a piece of information that should persist across sessions,
    with full tracking of verification status and access patterns.
    """
    id: str                                       # Unique identifier
    category: MemoryCategory                      # Type of memory
    priority: MemoryPriority                      # Importance level
    content: str                                  # The actual memory content
    verified: bool = False                        # Whether verified against source
    source: Optional[str] = None                 # Source document/origin
    verification_trail: List[str] = field(default_factory=list)  # How verified
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'category': self.category.value,
            'priority': self.priority.value,
            'content': self.content,
            'verified': self.verified,
            'source': self.source,
            'verification_trail': self.verification_trail,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'last_accessed': self.last_accessed.isoformat() if isinstance(self.last_accessed, datetime) else self.last_accessed,
            'access_count': self.access_count,
            'tags': list(self.tags),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PersistentMemoryItem':
        """Create from dictionary."""
        if isinstance(data.get('category'), str):
            data['category'] = MemoryCategory(data['category'])
        if isinstance(data.get('priority'), int):
            data['priority'] = MemoryPriority(data['priority'])
        elif isinstance(data.get('priority'), str):
            data['priority'] = MemoryPriority[data['priority']]
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('last_accessed'), str):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        if isinstance(data.get('tags'), list):
            data['tags'] = set(data['tags'])
        return cls(**data)


class BootstrapMemory:
    """
    Bootstrap Memory System - Always loaded at session start.

    This is the core of the persistent memory system. It provides:
    1. Storage for critical memories that survive all resets
    2. Hallucination register to prevent repeating mistakes
    3. User preference storage
    4. Automatic persistence to disk

    The key innovation is the BOOTSTRAP.md file which is human-readable
    and can be inspected/edited by the user.

    Usage:
        bootstrap = BootstrapMemory()
        bootstrap.initialize_session()

        # Check for hallucinations
        result = bootstrap.check_hallucination("54 MHz observations")
        if result:
            print(f"Known hallucination! Correct value: {result.correct_value}")

        # Store critical memory
        bootstrap.store_memory(PersistentMemoryItem(
            id="pref_verify_freqs",
            category=MemoryCategory.USER_PREFERENCES,
            priority=MemoryPriority.CRITICAL,
            content="Always verify frequencies against source text"
        ))
    """

    # Default persistent directory
    DEFAULT_PERSISTENT_DIR = Path.home() / ".astra_persistent"

    def __init__(self, persistent_dir: Optional[Path] = None, auto_load: bool = True):
        """
        Initialize bootstrap memory.

        Args:
            persistent_dir: Directory for persistent storage (default: ~/.astra_persistent)
            auto_load: Whether to automatically load existing data
        """
        self.persistent_dir = Path(persistent_dir) if persistent_dir else self.DEFAULT_PERSISTENT_DIR
        self.items: Dict[str, PersistentMemoryItem] = {}
        self.hallucination_register: Dict[str, HallucinationEntry] = {}

        # Ensure directory structure exists
        self._ensure_directory_structure()

        # Load existing data
        if auto_load:
            self._load_all()

    def _ensure_directory_structure(self) -> None:
        """Create directory structure if it doesn't exist."""
        dirs = [
            self.persistent_dir,
            self.persistent_dir / "session_logs",
            self.persistent_dir / "backups" / "daily",
            self.persistent_dir / "backups" / "weekly"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _compute_fingerprint(self, claim: str) -> str:
        """Compute MD5 fingerprint of a claim for quick lookup."""
        # Normalize the claim for consistent fingerprinting
        normalized = claim.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()

    def _load_all(self) -> None:
        """Load all persistent data from disk."""
        self._load_memory_store()
        self._load_hallucination_register()

    def _load_memory_store(self) -> None:
        """Load memory store from JSON file."""
        store_path = self.persistent_dir / "memory_store.json"
        if store_path.exists():
            try:
                with open(store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for item_data in data.get('items', []):
                    try:
                        item = PersistentMemoryItem.from_dict(item_data)
                        self.items[item.id] = item
                    except Exception as e:
                        print(f"Warning: Could not load memory item: {e}")
            except Exception as e:
                print(f"Warning: Could not load memory store: {e}")

    def _load_hallucination_register(self) -> None:
        """Load hallucination register from JSON file."""
        register_path = self.persistent_dir / "hallucination_register.json"
        if register_path.exists():
            try:
                with open(register_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for entry_data in data.get('hallucinations', []):
                    try:
                        entry = HallucinationEntry.from_dict(entry_data)
                        self.hallucination_register[entry.claim_fingerprint] = entry
                    except Exception as e:
                        print(f"Warning: Could not load hallucination entry: {e}")
            except Exception as e:
                print(f"Warning: Could not load hallucination register: {e}")

    def _save_memory_store(self) -> None:
        """Save memory store to JSON file."""
        store_path = self.persistent_dir / "memory_store.json"
        try:
            data = {
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'items': [item.to_dict() for item in self.items.values()]
            }
            with open(store_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save memory store: {e}")

    def _save_hallucination_register(self) -> None:
        """Save hallucination register to JSON file."""
        register_path = self.persistent_dir / "hallucination_register.json"
        try:
            data = {
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'hallucinations': [entry.to_dict() for entry in self.hallucination_register.values()],
                'metadata': {
                    'total_hallucinations': len(self.hallucination_register)
                }
            }
            with open(register_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save hallucination register: {e}")

    def _update_bootstrap_file(self) -> None:
        """Generate and save human-readable BOOTSTRAP.md file."""
        bootstrap_path = self.persistent_dir / "BOOTSTRAP.md"

        lines = [
            "# STAN_XI_ASTRO Persistent Memory Bootstrap",
            f"# Last Updated: {datetime.now().isoformat()}",
            "# Version: 1.0.0",
            "",
            "## CRITICAL: User Preferences",
            "These preferences MUST be followed in all interactions:",
            ""
        ]

        # Add user preferences
        prefs = [item for item in self.items.values()
                 if item.category == MemoryCategory.USER_PREFERENCES]
        for pref in sorted(prefs, key=lambda x: x.created_at, reverse=True)[:20]:
            lines.append(f"- {pref.content}")

        lines.extend(["", "## HALLUCINATION REGISTER (DO NOT REPEAT)", ""])
        lines.append("These claims are KNOWN TO BE FALSE. Never make these claims:")
        lines.append("")

        # Add hallucination entries
        for entry in self.hallucination_register.values():
            lines.append(f"- **CLAIM**: \"{entry.claim}\"")
            lines.append(f"  **CORRECT**: \"{entry.correct_value}\"")
            lines.append(f"  **CATEGORY**: {entry.category}")
            if entry.notes:
                lines.append(f"  **NOTES**: {'; '.join(entry.notes)}")
            lines.append("")

        lines.extend(["", "## VERIFIED FACTS", ""])
        lines.append("These facts have been verified against source documents:")
        lines.append("")

        # Add verified facts
        facts = [item for item in self.items.values()
                 if item.category == MemoryCategory.VERIFIED_FACTS and item.verified]
        for fact in sorted(facts, key=lambda x: x.access_count, reverse=True)[:30]:
            lines.append(f"- {fact.content}")
            if fact.source:
                lines.append(f"  (Source: {fact.source})")

        lines.extend(["", "## RECENT FEEDBACK", ""])
        # Add recent feedback
        feedback = [item for item in self.items.values()
                    if item.category == MemoryCategory.USER_FEEDBACK]
        for fb in sorted(feedback, key=lambda x: x.created_at, reverse=True)[:10]:
            date_str = fb.created_at.strftime('%Y-%m-%d')
            lines.append(f"- [{date_str}] {fb.content}")

        try:
            with open(bootstrap_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        except Exception as e:
            print(f"Warning: Could not update bootstrap file: {e}")

    # Public API

    def initialize_session(self) -> Dict[str, Any]:
        """
        Initialize a session by loading all critical memories.

        Returns:
            Dictionary with initialization status and loaded items
        """
        self._load_all()

        critical_count = len([i for i in self.items.values()
                              if i.priority == MemoryPriority.CRITICAL])
        hallucination_count = len(self.hallucination_register)

        return {
            'status': 'initialized',
            'total_memories': len(self.items),
            'critical_memories': critical_count,
            'hallucinations_registered': hallucination_count,
            'persistent_dir': str(self.persistent_dir)
        }

    def get_critical_memories(self) -> List[PersistentMemoryItem]:
        """Get all CRITICAL priority memory items."""
        return [item for item in self.items.values()
                if item.priority == MemoryPriority.CRITICAL]

    def get_memories_by_category(self, category: MemoryCategory) -> List[PersistentMemoryItem]:
        """Get all memory items in a specific category."""
        return [item for item in self.items.values()
                if item.category == category]

    def check_hallucination(self, claim: str) -> Optional[HallucinationEntry]:
        """
        Check if a claim matches a known hallucination.

        Args:
            claim: The claim to check

        Returns:
            HallucinationEntry if found, None otherwise
        """
        fingerprint = self._compute_fingerprint(claim)

        # Direct fingerprint match
        if fingerprint in self.hallucination_register:
            entry = self.hallucination_register[fingerprint]
            entry.occurrences += 1
            entry.last_occurrence = datetime.now()
            return entry

        # Also check for partial matches (key phrases)
        claim_lower = claim.lower()
        for entry in self.hallucination_register.values():
            # Check if key parts of the claim match
            if self._claims_similar(claim_lower, entry.claim.lower()):
                return entry

        return None

    def _claims_similar(self, claim1: str, claim2: str) -> bool:
        """Check if two claims are semantically similar."""
        # Extract key numbers and units
        numbers1 = set(re.findall(r'\d+(?:\.\d+)?', claim1))
        numbers2 = set(re.findall(r'\d+(?:\.\d+)?', claim2))

        # Extract key units
        units1 = set(re.findall(r'\b(mhz|ghz|khz|hz)\b', claim1))
        units2 = set(re.findall(r'\b(mhz|ghz|khz|hz)\b', claim2))

        # If same numbers and units, likely similar
        if numbers1 and numbers1 == numbers2 and units1 == units2:
            return True

        return False

    def register_hallucination(
        self,
        claim: str,
        correct_value: str,
        category: str,
        source_document: Optional[str] = None,
        notes: Optional[List[str]] = None
    ) -> HallucinationEntry:
        """
        Register a new hallucination for future prevention.

        Args:
            claim: The false claim that was made
            correct_value: The correct/verified value
            category: Category of hallucination (e.g., 'frequency', 'sample_size')
            source_document: Document where the error occurred
            notes: Additional notes about the hallucination

        Returns:
            The created HallucinationEntry
        """
        fingerprint = self._compute_fingerprint(claim)

        entry = HallucinationEntry(
            claim=claim,
            claim_fingerprint=fingerprint,
            correct_value=correct_value,
            category=category,
            source_document=source_document,
            notes=notes or []
        )

        self.hallucination_register[fingerprint] = entry
        self._save_hallucination_register()
        self._update_bootstrap_file()

        return entry

    def store_memory(
        self,
        item: PersistentMemoryItem,
        update_bootstrap: bool = True
    ) -> str:
        """
        Store a persistent memory item.

        Args:
            item: The memory item to store
            update_bootstrap: Whether to update the bootstrap file

        Returns:
            The item ID
        """
        self.items[item.id] = item
        self._save_memory_store()

        if update_bootstrap and item.priority == MemoryPriority.CRITICAL:
            self._update_bootstrap_file()

        return item.id

    def record_feedback(
        self,
        feedback: str,
        context: Optional[Dict[str, Any]] = None,
        priority: MemoryPriority = MemoryPriority.HIGH
    ) -> str:
        """
        Record user feedback as persistent memory.

        Args:
            feedback: The feedback content
            context: Additional context (source, etc.)
            priority: Priority level for the feedback

        Returns:
            The item ID
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        item = PersistentMemoryItem(
            id=f"feedback_{timestamp}",
            category=MemoryCategory.USER_FEEDBACK,
            priority=priority,
            content=feedback,
            verified=True,
            source=context.get('source') if context else None,
            metadata=context or {}
        )

        return self.store_memory(item)

    def add_verified_fact(
        self,
        fact: str,
        source: str,
        tags: Optional[Set[str]] = None,
        priority: MemoryPriority = MemoryPriority.HIGH
    ) -> str:
        """
        Add a verified fact to persistent memory.

        Args:
            fact: The verified fact content
            source: Source document or origin
            tags: Tags for categorization
            priority: Priority level

        Returns:
            The item ID
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fact_hash = hashlib.md5(fact.encode()).hexdigest()[:8]

        item = PersistentMemoryItem(
            id=f"fact_{timestamp}_{fact_hash}",
            category=MemoryCategory.VERIFIED_FACTS,
            priority=priority,
            content=fact,
            verified=True,
            source=source,
            tags=tags or set(),
            verification_trail=[f"Verified against: {source}"]
        )

        return self.store_memory(item)

    def add_user_preference(
        self,
        preference: str,
        priority: MemoryPriority = MemoryPriority.CRITICAL
    ) -> str:
        """
        Add a user preference to persistent memory.

        Args:
            preference: The preference content
            priority: Priority level (default CRITICAL)

        Returns:
            The item ID
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pref_hash = hashlib.md5(preference.encode()).hexdigest()[:8]

        item = PersistentMemoryItem(
            id=f"pref_{timestamp}_{pref_hash}",
            category=MemoryCategory.USER_PREFERENCES,
            priority=priority,
            content=preference,
            verified=True,
            source="user"
        )

        return self.store_memory(item)

    def get_bootstrap_content(self) -> str:
        """Get the content of the bootstrap file."""
        bootstrap_path = self.persistent_dir / "BOOTSTRAP.md"
        if bootstrap_path.exists():
            with open(bootstrap_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def create_backup(self, label: str = "manual") -> str:
        """
        Create a backup of the current memory state.

        Args:
            label: Label for the backup

        Returns:
            Path to the backup file
        """
        import shutil
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.persistent_dir / "backups" / "daily"
        backup_path = backup_dir / f"backup_{label}_{timestamp}"

        backup_path.mkdir(parents=True, exist_ok=True)

        # Copy all files
        for filename in ["memory_store.json", "hallucination_register.json", "BOOTSTRAP.md"]:
            src = self.persistent_dir / filename
            if src.exists():
                shutil.copy2(src, backup_path / filename)

        return str(backup_path)

    # ==================== Hallucination Management ====================

    def list_hallucinations(self) -> List[Dict[str, Any]]:
        """
        List all registered hallucinations.

        Returns:
            List of hallucination entries as dictionaries
        """
        result = []
        for entry in self.hallucination_register.values():
            result.append({
                'claim': entry.claim,
                'correct_value': entry.correct_value,
                'category': entry.category,
                'source_document': entry.source_document,
                'occurrences': entry.occurrences,
                'first_detected': entry.first_detected.isoformat() if entry.first_detected else None
            })
        return result

    def remove_hallucination(self, claim: str) -> bool:
        """
        Remove a hallucination entry from the register.

        Use this when a previously registered hallucination is no longer
        relevant (e.g., you actually do make 54 MHz observations in a new paper).

        Args:
            claim: The claim text to remove (or partial match)

        Returns:
            True if removed, False if not found
        """
        # Try exact fingerprint match first
        fingerprint = self._compute_fingerprint(claim)
        if fingerprint in self.hallucination_register:
            del self.hallucination_register[fingerprint]
            self._save_hallucination_register()
            self._update_bootstrap_file()
            return True

        # Try partial match
        claim_lower = claim.lower()
        keys_to_remove = []
        for key, entry in self.hallucination_register.items():
            if claim_lower in entry.claim.lower() or entry.claim.lower() in claim_lower:
                keys_to_remove.append(key)

        if keys_to_remove:
            for key in keys_to_remove:
                del self.hallucination_register[key]
            self._save_hallucination_register()
            self._update_bootstrap_file()
            return True

        return False

    def update_hallucination(
        self,
        claim: str,
        new_correct_value: Optional[str] = None,
        new_category: Optional[str] = None,
        new_notes: Optional[List[str]] = None
    ) -> bool:
        """
        Update an existing hallucination entry.

        Args:
            claim: The claim to update (or partial match)
            new_correct_value: New correct value (optional)
            new_category: New category (optional)
            new_notes: New notes (optional, replaces existing)

        Returns:
            True if updated, False if not found
        """
        # Find the entry
        fingerprint = self._compute_fingerprint(claim)
        entry = None

        if fingerprint in self.hallucination_register:
            entry = self.hallucination_register[fingerprint]
        else:
            # Try partial match
            claim_lower = claim.lower()
            for key, e in self.hallucination_register.items():
                if claim_lower in e.claim.lower() or e.claim.lower() in claim_lower:
                    entry = e
                    break

        if entry is None:
            return False

        # Update fields
        if new_correct_value is not None:
            entry.correct_value = new_correct_value
        if new_category is not None:
            entry.category = new_category
        if new_notes is not None:
            entry.notes = new_notes

        self._save_hallucination_register()
        self._update_bootstrap_file()
        return True

    def clear_all_hallucinations(self, confirm: bool = False) -> bool:
        """
        Clear all hallucination entries.

        Args:
            confirm: Must be True to actually clear

        Returns:
            True if cleared, False if not confirmed
        """
        if not confirm:
            return False

        self.hallucination_register.clear()
        self._save_hallucination_register()
        self._update_bootstrap_file()
        return True

    def get_hallucination(self, claim: str) -> Optional[HallucinationEntry]:
        """
        Get a specific hallucination entry without incrementing occurrence count.

        Args:
            claim: The claim to look up

        Returns:
            HallucinationEntry if found, None otherwise
        """
        fingerprint = self._compute_fingerprint(claim)
        return self.hallucination_register.get(fingerprint)

    def print_hallucinations_table(self) -> str:
        """
        Print a formatted table of all hallucinations.

        Returns:
            Formatted string table
        """
        if not self.hallucination_register:
            return "No hallucinations registered."

        lines = ["| Wrong Claim | Correct Value | Category |"]
        lines.append("|-------------|---------------|----------|")

        for entry in self.hallucination_register.values():
            claim_short = entry.claim[:30] + "..." if len(entry.claim) > 30 else entry.claim
            correct_short = entry.correct_value[:30] + "..." if len(entry.correct_value) > 30 else entry.correct_value
            lines.append(f"| {claim_short} | {correct_short} | {entry.category} |")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the persistent memory."""
        return {
            'total_items': len(self.items),
            'hallucinations_registered': len(self.hallucination_register),
            'by_priority': {
                'critical': len([i for i in self.items.values() if i.priority == MemoryPriority.CRITICAL]),
                'high': len([i for i in self.items.values() if i.priority == MemoryPriority.HIGH]),
                'medium': len([i for i in self.items.values() if i.priority == MemoryPriority.MEDIUM]),
                'low': len([i for i in self.items.values() if i.priority == MemoryPriority.LOW])
            },
            'by_category': {
                cat.value: len([i for i in self.items.values() if i.category == cat])
                for cat in MemoryCategory
            },
            'persistent_dir': str(self.persistent_dir)
        }


# Convenience functions

def create_bootstrap_memory(persistent_dir: Optional[Path] = None) -> BootstrapMemory:
    """Create and initialize a BootstrapMemory instance."""
    return BootstrapMemory(persistent_dir=persistent_dir, auto_load=True)


def quick_hallucination_check(claim: str) -> Optional[HallucinationEntry]:
    """Quick check if a claim is a known hallucination."""
    bootstrap = create_bootstrap_memory()
    return bootstrap.check_hallucination(claim)


def get_critical_memories() -> List[PersistentMemoryItem]:
    """Get all critical memories from the bootstrap."""
    bootstrap = create_bootstrap_memory()
    return bootstrap.get_critical_memories()


def list_all_hallucinations() -> List[Dict[str, Any]]:
    """List all registered hallucinations."""
    bootstrap = create_bootstrap_memory()
    return bootstrap.list_hallucinations()


def remove_hallucination_entry(claim: str) -> bool:
    """
    Remove a hallucination entry from the register.

    Args:
        claim: The claim text to remove (or partial match)

    Returns:
        True if removed, False if not found
    """
    bootstrap = create_bootstrap_memory()
    return bootstrap.remove_hallucination(claim)


def update_hallucination_entry(
    claim: str,
    new_correct_value: Optional[str] = None,
    new_category: Optional[str] = None,
    new_notes: Optional[List[str]] = None
) -> bool:
    """
    Update an existing hallucination entry.

    Args:
        claim: The claim to update
        new_correct_value: New correct value (optional)
        new_category: New category (optional)
        new_notes: New notes (optional)

    Returns:
        True if updated, False if not found
    """
    bootstrap = create_bootstrap_memory()
    return bootstrap.update_hallucination(claim, new_correct_value, new_category, new_notes)


def clear_hallucination_register(confirm: bool = False) -> bool:
    """
    Clear all hallucination entries.

    Args:
        confirm: Must be True to actually clear

    Returns:
        True if cleared, False if not confirmed
    """
    bootstrap = create_bootstrap_memory()
    return bootstrap.clear_all_hallucinations(confirm)


def print_hallucinations_table() -> str:
    """Print a formatted table of all hallucinations."""
    bootstrap = create_bootstrap_memory()
    return bootstrap.print_hallucinations_table()


__all__ = [
    'MemoryPriority',
    'MemoryCategory',
    'VerificationStatus',
    'HallucinationEntry',
    'PersistentMemoryItem',
    'BootstrapMemory',
    'create_bootstrap_memory',
    'quick_hallucination_check',
    'get_critical_memories',
    # Hallucination management
    'list_all_hallucinations',
    'remove_hallucination_entry',
    'update_hallucination_entry',
    'clear_hallucination_register',
    'print_hallucinations_table'
]
