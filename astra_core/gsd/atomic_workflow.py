"""
Atomic Commit Workflow Module
==============================

Implements GSD's atomic commit pattern with structured git workflow.

Every task completion results in:
- Atomic commit with clear message
- SUMMARY.md documenting outcomes
- STATE.md update with decisions and position

Based on: https://github.com/glittercowboy/get-shit-done
"""

from __future__ import annotations
import os
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime

try:
    from .xml_task_formatting import XMLTask, TaskStatus
except ImportError:
    # Define minimal types if import fails
    class XMLTask:
        id: str = ""
        name: str = ""
        status: str = "pending"

    class TaskStatus:
        PENDING = "pending"
        COMPLETED = "completed"
        FAILED = "failed"


class CommitStrategy(Enum):
    """Commit strategy options."""
    ATOMIC = "atomic"           # One commit per task
    BATCH = "batch"             # Batch multiple tasks
    SQUASH = "squash"           # Squash into single commit
    INTERACTIVE = "interactive" # Interactive git rebase


@dataclass
class TaskCompletion:
    """
    Result of task completion with commit info.

    Attributes:
        task: The completed task
        success: Whether task completed successfully
        commit_hash: Git commit hash if committed
        commit_message: Commit message used
        files_changed: List of files that were changed
        summary: Summary of what was done
        issues: Any issues encountered
        timestamp: Completion timestamp
    """
    task: XMLTask
    success: bool
    commit_hash: str = ""
    commit_message: str = ""
    files_changed: List[str] = field(default_factory=list)
    summary: str = ""
    issues: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": getattr(self.task, 'id', ''),
            "task_name": getattr(self.task, 'name', ''),
            "success": self.success,
            "commit_hash": self.commit_hash,
            "commit_message": self.commit_message,
            "files_changed": self.files_changed,
            "summary": self.summary,
            "issues": self.issues,
            "timestamp": self.timestamp
        }


@dataclass
class StateEntry:
    """
    Entry for STATE.md file.

    Tracks decisions, blockers, and position across sessions.
    """
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_id: str = ""
    decision: str = ""
    rationale: str = ""
    blockers: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert to markdown for STATE.md."""
        lines = [
            f"## {self.timestamp}",
            "",
            f"**Task**: {self.task_id}",
            "",
        ]

        if self.decision:
            lines.extend(["### Decision", "", f"{self.decision}", ""])

        if self.rationale:
            lines.extend(["### Rationale", "", f"{self.rationale}", ""])

        if self.blockers:
            lines.extend(["### Blockers", ""] + [f"- {b}" for b in self.blockers] + [""])

        if self.next_steps:
            lines.extend(["### Next Steps", ""] + [f"- {s}" for s in self.next_steps] + [""])

        return "\n".join(lines)


@dataclass
class SummaryEntry:
    """
    Entry for SUMMARY.md file.

    Documents what happened, what changed, committed to history.
    """
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_id: str = ""
    task_name: str = ""
    changes: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert to markdown for SUMMARY.md."""
        lines = [
            f"## {self.timestamp} - {self.task_name}",
            f"",
            f"**Task ID**: {self.task_id}",
            f"",
        ]

        if self.changes:
            lines.extend(["### Changes", ""] + [f"- {c}" for c in self.changes] + [""])

        if self.outcomes:
            lines.extend(["### Outcomes", ""] + [f"- {o}" for o in self.outcomes] + [""])

        if self.files_modified:
            lines.extend(["### Files Modified", ""] + [f"- `{f}`" for f in self.files_modified] + [""])

        return "\n".join(lines)


class SummaryGenerator:
    """Generate summaries for task completion."""

    @staticmethod
    def generate_summary(task: XMLTask, files_changed: List[str], outcomes: List[str]) -> str:
        """
        Generate a summary for task completion.

        Args:
            task: The completed task
            files_changed: List of files that were changed
            outcomes: List of outcomes achieved

        Returns:
            Summary string
        """
        lines = [
            f"Completed task: {task.name}",
            "",
            "Changes made:",
        ]

        for f in files_changed:
            lines.append(f"  - {f}")

        lines.extend(["", "Outcomes:"])

        for outcome in outcomes:
            lines.append(f"  - {outcome}")

        return "\n".join(lines)


class StateManager:
    """
    Manage STATE.md file across sessions.

    STATE.md provides living memory that persists across sessions,
    tracking decisions, blockers, and position.
    """

    def __init__(self, project_root: str):
        """
        Initialize state manager.

        Args:
            project_root: Root directory of project
        """
        self.project_root = Path(project_root)
        self.state_file = self.project_root / ".planning" / "STATE.md"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def add_entry(self, entry: StateEntry) -> None:
        """Add an entry to STATE.md."""
        content = entry.to_markdown()

        if self.state_file.exists():
            existing = self.state_file.read_text()
            content = existing + "\n\n" + content

        self.state_file.write_text(content)

    def get_current_state(self) -> str:
        """Get current state content."""
        if self.state_file.exists():
            return self.state_file.read_text()
        return ""


class AtomicCommitWorkflow:
    """
    Implement atomic commit workflow for task completion.

    Every task:
    1. Verifies completion
    2. Stages relevant files
    3. Creates atomic commit with clear message
    4. Generates SUMMARY.md entry
    5. Updates STATE.md
    """

    def __init__(
        self,
        strategy: CommitStrategy = CommitStrategy.ATOMIC,
        project_root: str = ".",
        auto_commit: bool = False,
        verify_callback: Optional[Callable[[XMLTask], bool]] = None
    ):
        """
        Initialize atomic commit workflow.

        Args:
            strategy: Commit strategy to use
            project_root: Root directory of project
            auto_commit: Whether to automatically commit
            verify_callback: Optional callback to verify task completion
        """
        self.strategy = strategy
        self.project_root = Path(project_root).resolve()
        self.auto_commit = auto_commit
        self.verify_callback = verify_callback

        # Create planning directory
        self.planning_dir = self.project_root / ".planning"
        self.planning_dir.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.state_manager = StateManager(str(self.project_root))

    def complete_task(
        self,
        task: XMLTask,
        files_changed: List[str] = None,
        outcomes: List[str] = None,
        commit_message: str = None
    ) -> TaskCompletion:
        """
        Complete a task with atomic commit and documentation.

        Args:
            task: The task to complete
            files_changed: List of files that were changed
            outcomes: List of outcomes achieved
            commit_message: Custom commit message
