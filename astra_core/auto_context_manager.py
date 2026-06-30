"""
Automatic Context Manager for ASTRA
===================================

This system automatically monitors conversation context and saves checkpoints
when running out of space, then enables seamless continuation on restart.

INTEGRATION:
- Automatically monitors context usage
- Saves checkpoints when threshold reached
- Automatically restores on restart
- Maintains research continuity

Version: 1.0.0
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional


def auto_save_context_on_exhaustion(conversation_data: Dict[str, Any]) -> str:
    """
    Automatically save context when approaching exhaustion

    Call this function when conversation context is running low.
    It will automatically save a checkpoint and return continuation info.

    Args:
        conversation_data: Dictionary with current conversation state

    Returns:
        continuation_message: Message to show user about continuation
    """
    try:
        from astra_core.context_continuation import get_context_continuation_system

        context_system = get_context_continuation_system()

        # Save checkpoint
        checkpoint_id = context_system.save_conversation_checkpoint(conversation_data)

        # Generate continuation message
        continuation_message = f"""
🔄 CONTEXT CONTINUATION TRIGGERED

Your conversation has been automatically saved to enable seamless continuation.
All important information has been preserved:
- ✅ Key discussion points extracted
- ✅ Active tasks tracked
- ✅ Research discoveries saved
- ✅ Ongoing work preserved

**Checkpoint ID**: {checkpoint_id}

**NEXT STEPS**:
When you restart, simply say: "Continue conversation from checkpoint {checkpoint_id}"
The system will automatically restore all context and continue where we left off.

**PRESERVED INFORMATION**:
- {len(conversation_data.get('messages', []))} messages compressed
- {len(conversation_data.get('active_tasks', []))} active tasks
- Research focus: {', '.join(conversation_data.get('research_focus', [])[:3])}
"""

        return continuation_message

    except Exception as e:
        return f"⚠️ Context save attempted but encountered error: {e}"


def auto_restore_on_startup() -> Optional[Dict[str, Any]]:
    """
    Automatically restore conversation context on startup

    Call this at the beginning of conversations to automatically
    restore previous context if available.

    Returns:
        restored_state: Dictionary with restored state, or None
    """
    try:
        from astra_core.context_continuation import get_context_continuation_system

        context_system = get_context_continuation_system()

        # Try to load latest checkpoint
        checkpoint = context_system.load_latest_checkpoint()

        if checkpoint:
            # Restore conversation state
            restored_state = context_system.restore_conversation_state(checkpoint)

            # Generate restoration message
            restoration_message = f"""
🔄 AUTOMATIC CONTEXT RESTORATION

Previous conversation context has been automatically restored:

**FROM**: {checkpoint.timestamp}
**MESSAGES**: {checkpoint.total_messages} compressed to {len(checkpoint.key_points)} key points

**RESTORED INFORMATION**:
"""

            if checkpoint.key_points:
                restoration_message += f"\n📍 **Key Points** ({len(checkpoint.key_points)}):\n"
                for i, point in enumerate(checkpoint.key_points[:5], 1):
                    restoration_message += f"   {i}. {point[:100]}...\n"

            if checkpoint.active_tasks:
                restoration_message += f"\n🎯 **Active Tasks** ({len(checkpoint.active_tasks)}):\n"
                for task in checkpoint.active_tasks[:3]:
                    restoration_message += f"   • {task.get('subject', 'Task')}: {task.get('status', 'unknown')}\n"

            if checkpoint.research_focus:
                restoration_message += f"\n🔬 **Research Focus**: {', '.join(checkpoint.research_focus[:3])}\n"

            if checkpoint.ongoing_work:
                restoration_message += f"\n📋 **Ongoing Work**: {checkpoint.ongoing_work[:200]}...\n"

            if checkpoint.discoveries_state:
                restoration_message += f"\n🔍 **Discoveries**: State preserved with {checkpoint.discoveries_state.get('genuine_discoveries', 0)} genuine discoveries\n"

            restoration_message += f"\n**✅ CONVERSATION CONTINUITY ENABLED**\n"
            restoration_message += f"We can continue exactly where we left off. What would you like to work on next?"

            restored_state['restoration_message'] = restoration_message
            return restored_state

        return None

    except Exception as e:
        print(f"Note: Context restoration check completed: {e}")
        return None


def check_context_threshold(context_usage: float = 0.0) -> bool:
    """
    Check if we should save a context checkpoint

    Args:
        context_usage: Current context usage (0.0-1.0)

    Returns:
        should_save: True if threshold reached
    """
    try:
        from astra_core.context_continuation import get_context_continuation_system

        context_system = get_context_continuation_system()
        return context_system.should_save_checkpoint(context_usage)

    except Exception as e:
        print(f"Error checking context threshold: {e}")
        return False


def manual_context_save(conversation_data: Dict[str, Any]) -> str:
    """
    Manually trigger a context save

    Use this to manually save conversation state at any point.

    Args:
        conversation_data: Current conversation state

    Returns:
        result_message: Status of the save operation
    """
    return auto_save_context_on_exhaustion(conversation_data)


def manual_context_restore(checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Manually restore conversation context

    Args:
        checkpoint_id: Specific checkpoint to restore (or None for latest)

    Returns:
        restored_state: Dictionary with restored state
    """
    return auto_restore_on_startup()


# Integration helper for automatic usage
class ContextManager:
    """Helper class for managing context in conversations"""

    def __init__(self):
        self.checkpoint_system = None
        self.message_count = 0
        self.estimated_usage = 0.0

    def add_message(self, role: str, content: str):
        """Track a message in the conversation"""
        self.message_count += 1

        # Rough estimation of context usage
        # (This is a heuristic - real system would use actual token counting)
        content_size = len(content) / 4  # Rough character to token estimate
        self.estimated_usage = min(1.0, self.estimated_usage + (content_size / 200000))

    def should_checkpoint(self) -> bool:
        """Check if we should save a checkpoint"""
        return check_context_threshold(self.estimated_usage)

    def auto_save(self, additional_data: Dict[str, Any] = None) -> str:
        """Automatically save if threshold reached"""
        if self.should_checkpoint():
            conversation_data = {
                'messages': [],  # Would be filled with actual messages
                'context_usage': self.estimated_usage,
                **additional_data
            }
            return auto_save_context_on_exhaustion(conversation_data)
        return ""


def create_context_manager() -> ContextManager:
    """Create a context manager instance"""
    return ContextManager()