"""
Context Quality Monitoring Module
=================================

Monitors context window usage and degradation signals to ensure
consistent quality across long conversations.

This module implements GSD's context window management strategy:
- Track token usage
- Detect quality degradation
- Trigger context refresh when needed
- Manage subagent spawning for fresh context

Based on: https://github.com/glittercowboy/get-shit-done
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import time
import threading
from collections import deque


class QualityThreshold(Enum):
    """Quality threshold levels for context degradation."""
    EXCELLENT = 1.0      # Full quality, fresh context
    GOOD = 0.9          # Minor degradation, still reliable
    ACCEPTABLE = 0.8    # Noticeable degradation, consider refresh
    POOR = 0.7          # Significant degradation, refresh recommended
    CRITICAL = 0.6      # Severe degradation, refresh required


class DegradationSignal(Enum):
    """Signals that indicate context degradation."""
    # Direct signals
    CONCISE_RESPONSE = "concise_response"           # "I'll be more concise now"
    SKIPPED_STEPS = "skipped_steps"                  # Skipping implementation details
    REDUCED_VERBOSITY = "reduced_verbosity"          # Less detailed explanations
    SUMMARIZATION = "summarization"                  # Summarizing instead of full detail

    # Indirect signals
    REPETITION = "repetition"                        # Repeating previous information
    INCONSISTENCY = "inconsistency"                  # Contradicting earlier statements
    FORGETFULNESS = "forgetfulness"                  # "As I mentioned earlier..." when it wasn't
    QUALITY_DECLINE = "quality_decline"              # Lower quality responses
    TIMEOUT = "timeout"                              # Response timeouts

    # Context signals
    HIGH_TOKEN_COUNT = "high_token_count"            # Approaching token limit
    LONG_HISTORY = "long_history"                    # Many messages in history
    LARGE_FILE_CONTEXT = "large_file_context"        # Large files loaded


class ContextRefreshStrategy(Enum):
    """Strategies for refreshing context."""
    SUBAGENT_SPAWN = "subagent_spawn"                # Spawn fresh subagent (GSD approach)
    SUMMARY_COMPRESSION = "summary_compression"      # Compress history to summary
    SELECTIVE_TRUNCATION = "selective_truncation"    # Remove old messages selectively
    MEMORY_OFFLOAD = "memory_offload"                # Store old context in memory system
    FULL_RESET = "full_reset"                        # Complete context reset


@dataclass
class ContextMetrics:
    """
    Metrics for tracking context quality.

    Attributes:
        token_count: Estimated token count for current context
        quality_score: Current quality score (0-1)
        degradation_signals: List of detected degradation signals
        message_count: Number of messages in conversation
        last_refresh: Timestamp of last context refresh
        refresh_count: Number of times context has been refreshed
        average_response_length: Average length of recent responses
        file_context_size: Total size of files in context
    """
    token_count: int = 0
    quality_score: float = 1.0
    degradation_signals: List[DegradationSignal] = field(default_factory=list)
    message_count: int = 0
    last_refresh: float = field(default_factory=time.time)
    refresh_count: int = 0
    average_response_length: float = 0.0
    file_context_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token_count": self.token_count,
            "quality_score": self.quality_score,
            "degradation_signals": [s.value for s in self.degradation_signals],
            "message_count": self.message_count,
            "last_refresh": self.last_refresh,
            "refresh_count": self.refresh_count,
            "average_response_length": self.average_response_length,
            "file_context_size": self.file_context_size
        }


class TokenEstimator:
    """
    Estimate token counts for various inputs.

    Uses a simple heuristic: ~4 characters per token for English text.
    For more accuracy, consider using tiktoken or similar library.
    """

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for text string."""
        # Rough estimation: 4 characters per token
