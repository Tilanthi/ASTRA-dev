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
Session Recovery Module
========================

Provides checkpoint and recovery mechanisms for session state.
Allows recovery after context compactification or system restart.

Date: 2026-03-24
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import json
import time
import os

from .bootstrap_memory import BootstrapMemory, MemoryPriority


@dataclass
class SessionCheckpoint:
    """A checkpoint of session state."""
    session_id: str
    timestamp: datetime
    working_memory_state: Optional[Dict] = None
    context: Dict[str, Any] = field(default_factory=dict)
    critical_items: List[str] = field(default_factory=list)
    active_tasks: List[str] = field(default_factory=list)
    recent_experiences: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'working_memory_state': self.working_memory_state,
            'context': self.context,
            'critical_items': self.critical_items,
            'active_tasks': self.active_tasks,
            'recent_experiences': self.recent_experiences
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionCheckpoint':
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class SessionRecovery:
    """
    Handles recovery of session state after compactification.

    Provides:
    - Periodic checkpointing
    - Recovery from most recent checkpoint
    - Continuity across instance changes

    Usage:
        bootstrap = BootstrapMemory()
        recovery = SessionRecovery(bootstrap)

        # Create checkpoint periodically
        recovery.create_checkpoint(working_memory, context)

        # Recover after compactification
        state = recovery.recover_from_checkpoint()
    """

    def __init__(self, bootstrap: BootstrapMemory):
        """
        Initialize session recovery.

        Args:
            bootstrap: BootstrapMemory instance
        """
        self.bootstrap = bootstrap
        self.session_id = self._generate_session_id()
        self.checkpoint_interval = 300  # 5 minutes
        self.last_checkpoint_time = time.time()
        self._max_checkpoints = 10  # Keep last 10 checkpoints

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return datetime.now().strftime('%Y%m%d_%H%M%S')

    def create_checkpoint(
        self,
        working_memory: Optional[Any] = None,
        current_context: Optional[Dict] = None,
        active_tasks: Optional[List] = None
    ) -> str:
        """
        Create a checkpoint of current session state.

        Args:
            working_memory: WorkingMemory instance to checkpoint
            current_context: Current conversation context
            active_tasks: List of active task IDs

        Returns:
            Path to the checkpoint file
        """
        # Prepare checkpoint data
        checkpoint = SessionCheckpoint(
            session_id=self.session_id,
            timestamp=datetime.now(),
            working_memory_state=self._serialize_working_memory(working_memory),
            context=current_context or {},
            critical_items=[item.id for item in self.bootstrap.get_critical_memories()],
            active_tasks=active_tasks or [],
            recent_experiences=self._get_recent_experiences()
        )

        # Ensure session_logs directory exists
        session_logs_dir = self.bootstrap.persistent_dir / "session_logs"
        session_logs_dir.mkdir(parents=True, exist_ok=True)

        # Save checkpoint
        checkpoint_path = session_logs_dir / f"checkpoint_{self.session_id}.json"

        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        # Update last checkpoint time
        self.last_checkpoint_time = time.time()

        # Clean up old checkpoints
        self._cleanup_old_checkpoints()

        return str(checkpoint_path)

    def recover_from_checkpoint(self, checkpoint_path: Optional[Path] = None) -> Optional[SessionCheckpoint]:
        """
        Recover session state from most recent checkpoint.

        Args:
            checkpoint_path: Optional specific checkpoint to recover from

        Returns:
            SessionCheckpoint if recovery successful, None otherwise
        """
        session_logs_dir = self.bootstrap.persistent_dir / "session_logs"

        if checkpoint_path:
            path = checkpoint_path
        else:
            # Find most recent checkpoint
            checkpoints = sorted(
                session_logs_dir.glob("checkpoint_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if not checkpoints:
                return None

            path = checkpoints[0]

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return SessionCheckpoint.from_dict(data)

        except Exception as e:
            print(f"Warning: Could not recover checkpoint: {e}")
            return None

    def _serialize_working_memory(self, working_memory: Optional[Any]) -> Optional[Dict]:
        """Serialize working memory state."""
        if working_memory is None:
            return None

        try:
            # Try to get state if available
            if hasattr(working_memory, 'get_state'):
                return working_memory.get_state()
            elif hasattr(working_memory, 'active'):
                return {
                    'active_items': len(working_memory.active),
                    'capacity': getattr(working_memory, 'capacity', 7)
                }
        except Exception:
            return None

    def _get_recent_experiences(self) -> List[Dict]:
        """Get recent experiences from episodic memory."""
        # This is a placeholder for when episodic memory is integrated
        return []

    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond the limit."""
        session_logs_dir = self.bootstrap.persistent_dir / "session_logs"

        checkpoints = sorted(
            session_logs_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove checkpoints beyond the limit
        for old_checkpoint in checkpoints[self._max_checkpoints:]:
            try:
                old_checkpoint.unlink()
            except Exception:
                pass

    def should_create_checkpoint(self) -> bool:
        """Check if enough time has passed for a new checkpoint."""
        return time.time() - self.last_checkpoint_time >= self.checkpoint_interval

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current session."""
        session_logs_dir = self.bootstrap.persistent_dir / "session_logs"

        checkpoints = list(session_logs_dir.glob("checkpoint_*.json"))

        return {
            'session_id': self.session_id,
            'checkpoints_count': len(checkpoints),
            'last_checkpoint': datetime.fromtimestamp(self.last_checkpoint_time).isoformat() if self.last_checkpoint_time else None,
            'checkpoint_interval': self.checkpoint_interval,
            'should_checkpoint': self.should_create_checkpoint()
        }

    def create_backup_checkpoint(self, label: str = "manual") -> str:
        """
        Create a backup checkpoint (stored in backups directory).

        Args:
            label: Label for the backup

        Returns:
            Path to the backup checkpoint
        """
        import shutil

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.bootstrap.persistent_dir / "backups" / "daily"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create the checkpoint in session_logs first
        checkpoint_path = self.create_checkpoint(
            working_memory=None,
            current_context={'backup_label': label}
        )

        # Copy to backup directory
        backup_path = backup_dir / f"backup_{label}_{timestamp}.json"
        if Path(checkpoint_path).exists():
            shutil.copy2(checkpoint_path, backup_path)

        return str(backup_path)


def create_session_recovery(bootstrap: Optional[BootstrapMemory] = None) -> SessionRecovery:
    """Create a session recovery instance."""
    if bootstrap is None:
        from .bootstrap_memory import create_bootstrap_memory
        bootstrap = create_bootstrap_memory()

    return SessionRecovery(bootstrap)


__all__ = [
    'SessionCheckpoint',
    'SessionRecovery',
    'create_session_recovery'
]
