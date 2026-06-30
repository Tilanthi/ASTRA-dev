"""
Context Manager - Unified Context Management
==============================================

This module provides unified context management for ASTRA to prevent
context window overflow by coordinating all context-related systems.

Features:
- Automatic context usage monitoring
- Checkpoint creation and compression
- Discovery log monitoring
- Emergency context compression

Version: 1.0.0
Date: 2026-06-29
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Unified context management system
    """

    def __init__(self):
        """Initialize context manager"""
        from astra_core.context_monitor import get_context_monitor
        from astra_core.discovery_log_monitor import get_discovery_monitor

        self.context_monitor = get_context_monitor()
        self.discovery_monitor = get_discovery_monitor()

        self.checkpoint_dir = Path.home() / ".astra_persistent" / "conversation_context"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def get_context_summary(self) -> str:
        """
        Get a brief context summary for session restoration

        Returns:
            Brief context summary (max 10 lines)
        """
        lines = []

        # Context monitor status
        context_status = self.context_monitor.check_context_status(0)
        lines.append(f"Context: {context_status['usage_percentage']:.1f}% - {context_status['level']}")

        # Discovery status
        discovery_status = self.discovery_monitor.get_brief_status()
        lines.append(f"Discovery: {discovery_status}")

        # Recent checkpoints
        checkpoint_count = len(list(self.checkpoint_dir.glob("checkpoint_*.json")))
        lines.append(f"Checkpoints: {checkpoint_count} available")

        return "\n".join(lines)

    def check_and_manage_context(self,
                                  conversation_length: int,
                                  conversation_summary: str,
                                  key_points: List[str],
                                  active_tasks: List[Dict]) -> Optional[str]:
        """
        Check context usage and manage if needed

        Args:
            conversation_length: Current conversation length
            conversation_summary: Brief conversation summary
            key_points: Key points to preserve
            active_tasks: Active tasks list

        Returns:
            Checkpoint ID if compression was performed
        """
        status = self.context_monitor.check_context_status(conversation_length)

        if status["action_required"]:
            logger.warning(f"Context management needed: {status['action_required']}")

            if status["action_required"] == "emergency_compression":
                # Emergency mode - aggressive compression
                return self._emergency_compression(conversation_summary, key_points, active_tasks)
            elif status["action_required"] == "create_checkpoint":
                # Normal checkpoint creation
                return self.context_monitor.create_compressed_checkpoint(
                    conversation_summary, key_points, active_tasks
                )

        return None

    def _emergency_compression(self,
                               conversation_summary: str,
                               key_points: List[str],
                               active_tasks: List[Dict]) -> str:
        """
        Perform emergency context compression

        Returns:
            Checkpoint ID
        """
        logger.critical("EMERGENCY CONTEXT COMPRESSION ACTIVATED")

        # Create ultra-compressed checkpoint
        compressed_summary = conversation_summary[:200] + "..." if len(conversation_summary) > 200 else conversation_summary
        essential_points = key_points[:3] if len(key_points) > 3 else key_points

        checkpoint_id = self.context_monitor.create_compressed_checkpoint(
            compressed_summary, essential_points, active_tasks
        )

        # Also create discovery checkpoint
        self.discovery_monitor.create_summary_checkpoint()

        return checkpoint_id

    def get_restoration_summary(self) -> str:
        """
        Get a restoration summary for session continuation

        Returns:
            Brief restoration context (max 15 lines)
        """
        lines = [
            "═══════════════════════════════════════════════════════════════",
            "🔄 CONTEXT RESTORATION",
            "═══════════════════════════════════════════════════════════════",
            "",
            f"Restored: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            self.get_context_summary(),
            "",
            "───────────────────────────────────────────────────────────────",
            "Session context ready",
            "───────────────────────────────────────────────────────────────"
        ]

        return "\n".join(lines)


# Singleton instance
_context_manager_instance = None


def get_context_manager() -> ContextManager:
    """Get the singleton context manager instance"""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager()
    return _context_manager_instance


def auto_manage_context(conversation_length: int,
                        conversation_summary: str,
                        key_points: List[str],
                        active_tasks: List[Dict]) -> Optional[str]:
    """
    Automatically manage context usage

    This is the main entry point for automatic context management.
    Call this periodically to check and manage context usage.

    Args:
        conversation_length: Current conversation length
        conversation_summary: Brief conversation summary
        key_points: Key points to preserve
        active_tasks: Active tasks list

    Returns:
        Checkpoint ID if compression was performed, None otherwise
    """
    manager = get_context_manager()
    return manager.check_and_manage_context(
        conversation_length, conversation_summary, key_points, active_tasks
    )


def get_session_context_summary() -> str:
    """
    Get a brief session context summary

    Returns:
        Brief context summary for display
    """
    manager = get_context_manager()
    return manager.get_restoration_summary()
