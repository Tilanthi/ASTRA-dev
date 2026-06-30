"""
Discovery Log Monitor - Streamlined Log Monitoring
====================================================

This module monitors autonomous discovery logs and provides
summarized updates instead of full log processing to prevent
context overflow.

Key Features:
- Checkpoint-based log summaries
- Configurable output verbosity
- Context-aware monitoring
- Automatic log rotation

Version: 1.0.0
Date: 2026-06-29
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


class DiscoveryLogMonitor:
    """
    Monitor discovery logs with context-aware output
    """

    def __init__(self,
                 log_path: Optional[str] = None,
                 max_summary_lines: int = 5,
                 summary_interval_minutes: int = 30):
        """
        Initialize discovery log monitor

        Args:
            log_path: Path to discovery log file
            max_summary_lines: Maximum lines in summary output
            summary_interval_minutes: Minutes between summary updates
        """
        self.log_path = Path(log_path) if log_path else Path.home() / ".astra_persistent" / "24_7_genuine_discovery.log"
        self.max_summary_lines = max_summary_lines
        self.summary_interval = timedelta(minutes=summary_interval_minutes)

        self.last_summary_position = 0
        self.last_summary_time = None
        self.discovery_count = 0

    def get_recent_summary(self, max_lines: int = None) -> str:
        """
        Get a brief summary of recent discovery activity

        Args:
            max_lines: Maximum lines to include in summary

        Returns:
            Brief summary string (context-aware, limited length)
        """
        if not self.log_path.exists():
            return "No discovery log found"

        lines_to_show = max_lines or self.max_summary_lines

        try:
            with open(self.log_path, 'r') as f:
                # Get last N lines
                lines = f.readlines()
                recent_lines = lines[-lines_to_show:] if len(lines) > lines_to_show else lines

                # Extract key information
                summary_lines = []
                for line in recent_lines:
                    # Only include lines with discovery markers
                    if any(marker in line for marker in ["DISCOVERY", "genuine", "cycle", "hypothesis"]):
                        # Truncate long lines
                        if len(line) > 200:
                            line = line[:200] + "..."
                        summary_lines.append(line.strip())

                if not summary_lines:
                    return f"Log exists ({len(lines)} lines) - no recent discoveries"

                # Create concise summary
                summary = f"📊 Discovery Activity ({len(lines)} total lines)\n"
                summary += f"Recent ({len(summary_lines)} key events):\n"
                summary += "\n".join(summary_lines[-3:])  # Only last 3 important lines

                return summary

        except Exception as e:
            logger.error(f"Failed to read discovery log: {e}")
            return f"Error reading discovery log: {e}"

    def get_discovery_stats(self) -> Dict[str, any]:
        """
        Get statistics about discovery activity

        Returns:
            Dictionary with discovery statistics
        """
        if not self.log_path.exists():
            return {
                "log_exists": False,
                "total_discoveries": 0,
                "last_activity": None
            }

        try:
            with open(self.log_path, 'r') as f:
                lines = f.readlines()

            # Count discoveries
            discovery_count = sum(1 for line in lines if "DISCOVERY" in line or "genuine" in line)

            # Get last activity time
            last_line = lines[-1].strip() if lines else ""
            last_activity = None
            if last_line:
                try:
                    # Try to extract timestamp from log line
                    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', last_line)
                    if timestamp_match:
                        last_activity = timestamp_match.group()
                except:
                    pass

            return {
                "log_exists": True,
                "total_lines": len(lines),
                "total_discoveries": discovery_count,
                "last_activity": last_activity,
                "log_size_kb": self.log_path.stat().st_size / 1024
            }

        except Exception as e:
            logger.error(f"Failed to get discovery stats: {e}")
            return {"error": str(e)}

    def create_summary_checkpoint(self) -> str:
        """
        Create a summary checkpoint to avoid re-reading entire log

        Returns:
            Checkpoint ID
        """
        import uuid

        stats = self.get_discovery_stats()
        checkpoint_id = str(uuid.uuid4())[:8]

        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "checkpoint_id": checkpoint_id,
            "discovery_stats": stats,
            "recent_summary": self.get_recent_summary(3)
        }

        checkpoint_dir = Path.home() / ".astra_persistent" / "conversation_context"
        checkpoint_dir.mkdir(parents_t=checkpoint_dir, exist_ok=True)

        checkpoint_file = checkpoint_dir / f"discovery_checkpoint_{checkpoint_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Created discovery checkpoint: {checkpoint_id}")
        return checkpoint_id

    def get_brief_status(self) -> str:
        """
        Get a very brief status message (1-2 lines max)

        Returns:
            Brief status string
        """
        stats = self.get_discovery_stats()

        if not stats.get("log_exists"):
            return "Discovery log: Not found"

        return (f"Discovery log: {stats.get('total_discoveries', 0)} discoveries, "
                f"{stats.get('total_lines', 0)} lines, "
                f"{stats.get('log_size_kb', 0):.1f} KB")


# Singleton instance
_discovery_monitor_instance = None


def get_discovery_monitor() -> DiscoveryLogMonitor:
    """Get the singleton discovery monitor instance"""
    global _discovery_monitor_instance
    if _discovery_monitor_instance is None:
        _discovery_monitor_instance = DiscoveryLogMonitor()
    return _discovery_monitor_instance


def get_discovery_status_brief() -> str:
    """
    Get a brief discovery status for context display (1-2 lines)

    Returns:
        Brief status string
    """
    monitor = get_discovery_monitor()
    return monitor.get_brief_status()
