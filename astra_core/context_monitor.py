"""
Context Monitor - Prevent Context Window Overflow
===================================================

This module monitors context usage and prevents overflow by:
1. Tracking context usage at start of each turn
2. Creating compressed checkpoints before hitting limits
3. Managing autonomous discovery output to prevent bloat
4. Providing emergency context compression when needed

Version: 1.0.0
Date: 2026-06-29
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ContextMonitor:
    """
    Monitor and manage context window usage to prevent overflow
    """

    def __init__(self,
                 warning_threshold: float = 0.70,
                 critical_threshold: float = 0.85,
                 emergency_threshold: float = 0.95):
        """
        Initialize context monitor

        Args:
            warning_threshold: Warn when context usage exceeds this (0.70 = 70%)
            critical_threshold: Create checkpoint at this threshold (0.85 = 85%)
            emergency_threshold: Emergency compression mode (0.95 = 95%)
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.emergency_threshold = emergency_threshold

        self.checkpoint_dir = Path.home() / ".astra_persistent" / "conversation_context"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.current_context_usage = 0.0
        self.last_checkpoint_time = None

    def estimate_context_usage(self, conversation_length: int,
                                max_context_tokens: int = 200000) -> float:
        """
        Estimate current context usage based on conversation length

        Args:
            conversation_length: Current length of conversation
            max_context_tokens: Maximum context window size

        Returns:
            Estimated context usage as percentage (0.0 to 1.0)
        """
        # Rough estimate: ~4 chars per token, conversation includes messages
        estimated_tokens = conversation_length / 4
        usage = min(estimated_tokens / max_context_tokens, 1.0)
        return usage

    def check_context_status(self, conversation_length: int) -> Dict[str, Any]:
        """
        Check current context status and return recommendations

        Args:
            conversation_length: Current conversation length

        Returns:
            Status dict with usage, level, and actions needed
        """
        usage = self.estimate_context_usage(conversation_length)
        self.current_context_usage = usage

        status = {
            "usage_percentage": usage * 100,
            "usage_decimal": usage,
            "level": "normal",
            "action_required": None,
            "recommendation": "Continue normally"
        }

        if usage >= self.emergency_threshold:
            status["level"] = "emergency"
            status["action_required"] = "emergency_compression"
            status["recommendation"] = "EMERGENCY: Aggressive compression required immediately"
        elif usage >= self.critical_threshold:
            status["level"] = "critical"
            status["action_required"] = "create_checkpoint"
            status["recommendation"] = "CRITICAL: Create compressed checkpoint now"
        elif usage >= self.warning_threshold:
            status["level"] = "warning"
            status["action_required"] = "prepare_checkpoint"
            status["recommendation"] = "WARNING: Prepare for checkpoint compression"

        return status

    def create_compressed_checkpoint(self,
                                    conversation_summary: str,
                                    key_points: list,
                                    active_tasks: list) -> str:
        """
        Create a compressed checkpoint to free up context

        Args:
            conversation_summary: Brief summary of conversation
            key_points: List of key points to preserve
            active_tasks: List of active tasks

        Returns:
            Checkpoint ID
        """
        import uuid

        checkpoint_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()

        checkpoint = {
            "timestamp": timestamp,
            "checkpoint_id": checkpoint_id,
            "compressed_summary": conversation_summary,
            "key_points": key_points,
            "active_tasks": active_tasks,
            "context_usage_at_creation": self.current_context_usage
        }

        checkpoint_file = self.checkpoint_dir / f"checkpoint_{checkpoint_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        # Update index
        self._update_checkpoint_index(checkpoint_id, timestamp)

        self.last_checkpoint_time = timestamp
        logger.info(f"Created compressed checkpoint: {checkpoint_id}")

        return checkpoint_id

    def _update_checkpoint_index(self, checkpoint_id: str, timestamp: str):
        """Update the checkpoint index file"""
        index_file = self.checkpoint_dir / "checkpoint_index.json"

        try:
            if index_file.exists():
                with open(index_file, 'r') as f:
                    index = json.load(f)
            else:
                index = {"checkpoints": [], "last_updated": None}

            # Add new checkpoint
            index["checkpoints"].insert(0, {
                "id": checkpoint_id,
                "timestamp": timestamp
            })

            # Keep only last 10 checkpoints
            index["checkpoints"] = index["checkpoints"][:10]
            index["last_updated"] = timestamp

            with open(index_file, 'w') as f:
                json.dump(index, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to update checkpoint index: {e}")

    def get_monitoring_summary(self) -> str:
        """
        Get a brief summary of current monitoring status

        Returns:
            Brief status string (max 3 lines)
        """
        status = self.check_context_status(0)  # Will use current usage

        summary = f"Context Monitor: {status['usage_percentage']:.1f}% - {status['level'].upper()}"

        if status["action_required"]:
            summary += f" | Action: {status['action_required']}"

        return summary


# Singleton instance for easy access
_context_monitor_instance = None


def get_context_monitor() -> ContextMonitor:
    """Get the singleton context monitor instance"""
    global _context_monitor_instance
    if _context_monitor_instance is None:
        _context_monitor_instance = ContextMonitor()
    return _context_monitor_instance


def check_context_and_compress_if_needed(conversation_length: int,
                                        conversation_summary: str,
                                        key_points: list,
                                        active_tasks: list) -> Optional[str]:
    """
    Check context usage and compress if needed

    Returns:
        Checkpoint ID if compression was performed, None otherwise
    """
    monitor = get_context_monitor()
    status = monitor.check_context_status(conversation_length)

    if status["action_required"] in ["create_checkpoint", "emergency_compression"]:
        logger.warning(f"Context usage at {status['usage_percentage']:.1f}% - creating checkpoint")
        return monitor.create_compressed_checkpoint(
            conversation_summary, key_points, active_tasks
        )

    return None
