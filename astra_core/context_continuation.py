"""
ASTRA Context Continuation System
=================================

This system handles conversation context exhaustion by automatically saving,
compressing, and restoring conversation state to enable seamless continuation
when context limits are reached.

PROBLEM SOLVED:
- When conversation context runs out, automatically save important information
- On restart, automatically restore saved state
- Maintain continuity of research, discoveries, and work progress
- Enable indefinite long-term conversations without loss of context

Version: 1.0.0
Date: 2026-06-28
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import threading
import time


@dataclass
class ConversationCheckpoint:
    """A saved point in the conversation for continuation"""
    timestamp: str
    checkpoint_id: str
    session_id: str

    # Conversation state
    total_messages: int
    compressed_summary: str
    key_points: List[str]
    active_tasks: List[Dict]
    decisions_made: List[Dict]
    context_weight: int  # Estimated context size

    # ASTRA-specific state
    discoveries_state: Optional[Dict] = None
    research_focus: List[str] = field(default_factory=list)
    important_entities: List[str] = field(default_factory=list)
    ongoing_work: str = ""

    # Technical details
    message_indices: List[int] = field(default_factory=list)  # Which messages this checkpoint covers
    next_continuation_point: int = 0


class ContextContinuationSystem:
    """
    System for managing conversation context continuation

    Automatically saves conversation checkpoints and enables
    seamless restoration when context is exhausted.
    """

    def __init__(self, context_threshold: float = 0.85):
        """
        Initialize context continuation system

        Args:
            context_threshold: When to trigger checkpoint (0.0-1.0 of context used)
        """
        self.context_threshold = context_threshold
        self.storage_path = Path.home() / ".astra_persistent" / "conversation_context"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.session_id = self._generate_session_id()
        self.checkpoints: List[ConversationCheckpoint] = []
        self.current_checkpoint: Optional[ConversationCheckpoint] = None

        # Load existing session
        self._load_session_state()

    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        return hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]

    def save_conversation_checkpoint(self, conversation_data: Dict[str, Any]) -> str:
        """
        Save a checkpoint of the current conversation state

        Args:
            conversation_data: Dictionary containing:
                - messages: List of conversation messages
                - context_usage: Current context usage (0.0-1.0)
                - active_tasks: List of currently active tasks
                - discoveries_state: Current autonomous discoveries state
                - research_focus: Current research priorities
                - important_entities: Key entities/concepts discussed

        Returns:
            checkpoint_id: ID of the saved checkpoint
        """
        try:
            # Compress conversation into key information
            compressed_summary = self._compress_conversation(conversation_data.get('messages', []))
            key_points = self._extract_key_points(conversation_data.get('messages', []))
            decisions = self._extract_decisions(conversation_data.get('messages', []))

            # Create checkpoint
            checkpoint = ConversationCheckpoint(
                timestamp=datetime.now().isoformat(),
                checkpoint_id=self._generate_checkpoint_id(),
                session_id=self.session_id,
                total_messages=len(conversation_data.get('messages', [])),
                compressed_summary=compressed_summary,
                key_points=key_points,
                active_tasks=conversation_data.get('active_tasks', []),
                decisions_made=decisions,
                context_weight=conversation_data.get('context_usage', 0.0),
                discoveries_state=conversation_data.get('discoveries_state'),
                research_focus=conversation_data.get('research_focus', []),
                important_entities=conversation_data.get('important_entities', []),
                ongoing_work=conversation_data.get('ongoing_work', ''),
                message_indices=list(range(len(conversation_data.get('messages', [])))),
                next_continuation_point=len(conversation_data.get('messages', []))
            )

            # Save checkpoint
            checkpoint_file = self.storage_path / f"checkpoint_{checkpoint.checkpoint_id}.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(asdict(checkpoint), f, indent=2)

            # Update index
            self._update_checkpoint_index(checkpoint)

            self.current_checkpoint = checkpoint
            self.checkpoints.append(checkpoint)

            print(f"✅ Context checkpoint saved: {checkpoint.checkpoint_id}")
            print(f"   Compressed {checkpoint.total_messages} messages into {len(key_points)} key points")

            return checkpoint.checkpoint_id

        except Exception as e:
            print(f"❌ Error saving checkpoint: {e}")
            return ""

    def load_latest_checkpoint(self) -> Optional[ConversationCheckpoint]:
        """
        Load the most recent checkpoint for continuation

        Returns:
            Checkpoint if available, None otherwise
        """
        try:
            index_file = self.storage_path / "checkpoint_index.json"

            if not index_file.exists():
                print("📝 No previous conversation context found - starting fresh")
                return None

            with open(index_file) as f:
                index = json.load(f)

            if not index.get('checkpoints'):
                print("📝 No checkpoints available - starting fresh")
                return None

            # Load latest checkpoint
            latest_id = index['checkpoints'][-1]['checkpoint_id']
            checkpoint_file = self.storage_path / f"checkpoint_{latest_id}.json"

            if not checkpoint_file.exists():
                print(f"❌ Checkpoint file not found: {checkpoint_file}")
                return None

            with open(checkpoint_file) as f:
                checkpoint_data = json.load(f)

            checkpoint = ConversationCheckpoint(**checkpoint_data)

            print(f"🔄 Context checkpoint loaded: {checkpoint.checkpoint_id}")
            print(f"   From: {checkpoint.timestamp}")
            print(f"   Messages compressed: {checkpoint.total_messages} → {len(checkpoint.key_points)} key points")
            print(f"   Active tasks: {len(checkpoint.active_tasks)}")
            print(f"   Research focus: {', '.join(checkpoint.research_focus[:3])}")

            if checkpoint.ongoing_work:
                print(f"   📋 Ongoing work: {checkpoint.ongoing_work[:200]}...")

            return checkpoint

        except Exception as e:
            print(f"❌ Error loading checkpoint: {e}")
            return None

    def restore_conversation_state(self, checkpoint: ConversationCheckpoint) -> Dict[str, Any]:
        """
        Restore conversation state from checkpoint

        Args:
            checkpoint: Checkpoint to restore from

        Returns:
            Dictionary with restored conversation state
        """
        return {
            'checkpoint_id': checkpoint.checkpoint_id,
            'session_continued': True,
            'previous_summary': checkpoint.compressed_summary,
            'key_points': checkpoint.key_points,
            'active_tasks': checkpoint.active_tasks,
            'decisions_made': checkpoint.decisions_made,
            'discoveries_state': checkpoint.discoveries_state,
            'research_focus': checkpoint.research_focus,
            'important_entities': checkpoint.important_entities,
            'ongoing_work': checkpoint.ongoing_work,
            'message_count': checkpoint.total_messages,
            'continuation_point': checkpoint.next_continuation_point
        }

    def _compress_conversation(self, messages: List[Dict]) -> str:
        """Compress conversation into summary"""
        if not messages:
            return "No previous conversation"

        # Extract and compress content
        content_summary = []

        for msg in messages[-20:]:  # Focus on recent messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')

            if role == 'user':
                content_summary.append(f"User: {content[:100]}...")
            elif 'assistant' in role:
                # Extract key points from assistant messages
                if '✅' in content or '❌' in content:
                    content_summary.append(f"Key action completed")

        return " | ".join(content_summary[-5:])  # Last 5 compressed items

    def _extract_key_points(self, messages: List[Dict]) -> List[str]:
        """Extract key points from conversation"""
        key_points = []

        for msg in messages:
            content = msg.get('content', '')

            # Look for important markers
            if any(marker in content for marker in ['✅', '🎯', '🔬', '📊', '⚠️']):
                # Extract the sentence containing the marker
                sentences = content.split('.')
                for sentence in sentences:
                    if any(marker in sentence for marker in ['✅', '🎯', '🔬', '📊', '⚠️']):
                        key_points.append(sentence.strip()[:200])
                        break

        return key_points[-10:]  # Last 10 key points

    def _extract_decisions(self, messages: List[Dict]) -> List[Dict]:
        """Extract important decisions made"""
        decisions = []

        for msg in messages:
            content = msg.get('content', '')

            if 'decision' in content.lower() or 'chose' in content.lower():
                decisions.append({
                    'timestamp': datetime.now().isoformat(),
                    'decision': content[:200],
                    'type': 'user_or_system'
                })

        return decisions

    def _generate_checkpoint_id(self) -> str:
        """Generate unique checkpoint identifier"""
        return hashlib.md5(f"{self.session_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]

    def _update_checkpoint_index(self, checkpoint: ConversationCheckpoint):
        """Update the checkpoint index file"""
        index_file = self.storage_path / "checkpoint_index.json"

        try:
            if index_file.exists():
                with open(index_file) as f:
                    index = json.load(f)
            else:
                index = {'checkpoints': [], 'session_id': self.session_id}

            # Add checkpoint to index
            index['checkpoints'].append({
                'checkpoint_id': checkpoint.checkpoint_id,
                'timestamp': checkpoint.timestamp,
                'message_count': checkpoint.total_messages,
                'key_points_count': len(checkpoint.key_points)
            })

            # Keep only last 10 checkpoints
            index['checkpoints'] = index['checkpoints'][-10:]

            with open(index_file, 'w') as f:
                json.dump(index, f, indent=2)

        except Exception as e:
            print(f"Error updating checkpoint index: {e}")

    def _load_session_state(self):
        """Load previous session state if available"""
        try:
            index_file = self.storage_path / "checkpoint_index.json"

            if index_file.exists():
                with open(index_file) as f:
                    index = json.load(f)

                if index.get('checkpoints'):
                    print(f"📂 Found {len(index['checkpoints'])} previous conversation checkpoints")
                    latest = index['checkpoints'][-1]
                    print(f"   Latest: {latest['timestamp']} ({latest['message_count']} messages)")

        except Exception as e:
            print(f"Note: Could not load session state: {e}")

    def should_save_checkpoint(self, context_usage: float) -> bool:
        """Determine if it's time to save a checkpoint"""
        return context_usage >= self.context_threshold


def create_context_continuation_system(context_threshold: float = 0.85) -> ContextContinuationSystem:
    """Create and initialize context continuation system"""
    return ContextContinuationSystem(context_threshold)


# Global instance
_context_continuation: Optional[ContextContinuationSystem] = None


def get_context_continuation_system() -> ContextContinuationSystem:
    """Get global context continuation system instance"""
    global _context_continuation

    if _context_continuation is None:
        _context_continuation = create_context_continuation_system()

    return _context_continuation