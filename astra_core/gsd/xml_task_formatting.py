"""
XML Task Formatting Module
===========================

Implements GSD's XML-structured task format optimized for Claude.

This module provides XML-based task specification with verification steps,
following the pattern from https://github.com/glittercowboy/get-shit-done

Example XML structure:
<task type="auto">
  <name>Create login endpoint</name>
  <files>src/app/api/auth/login/route.ts</files>
  <action>
    Use jose for JWT (not jsonwebtoken - CommonJS issues).
    Validate credentials against users table.
    Return httpOnly cookie on success.
  </action>
  <verify>curl -X POST localhost:3000/api/auth/login returns 200 + Set-Cookie</verify>
  <done>Valid credentials return cookie, invalid return 401</done>
</task>
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from xml.dom import minidom
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import re
import hashlib
import json


class TaskType(Enum):
    """Task types for classification and routing."""
    AUTO = "auto"
    SCIENTIFIC_DISCOVERY = "scientific_discovery"
    CAUSAL_ANALYSIS = "causal_analysis"
    MARKET_ANALYSIS = "market_analysis"
    ASTRONOMY = "astronomy"
    TRADING = "trading"
    MATHEMATICAL = "mathematical"
    CODE_GENERATION = "code_generation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    OPTIMIZATION = "optimization"
    DEBUGGING = "debugging"
    INTEGRATION = "integration"


class TaskPriority(Enum):
    """Priority levels for task scheduling."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Status tracking for task execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskVerification:
    """Verification step for task completion."""
    command: str
    expected_output: str
    timeout_seconds: int = 30
    required: bool = True

    def to_xml_element(self) -> ET.Element:
        """Convert to XML element."""
        elem = ET.Element("verify")
        elem.set("timeout", str(self.timeout_seconds))
        elem.set("required", str(self.required).lower())
        elem.text = self.command
        return elem

    @classmethod
    def from_xml_element(cls, element: ET.Element) -> 'TaskVerification':
        """Create from XML element."""
        return cls(
            command=element.text or "",
            expected_output=element.get("expected", ""),
            timeout_seconds=int(element.get("timeout", "30")),
            required=element.get("required", "true").lower() == "true"
        )


@dataclass
class XMLTask:
    """
    XML-formatted task specification.

    Attributes:
        id: Unique task identifier (SHA-256 hash)
        type: Task type for routing
        name: Human-readable task name
        files: List of files this task operates on
        action: Detailed action description
        verification: List of verification steps
        done: Definition of done criteria
        priority: Task priority level
        status: Current task status
        dependencies: List of task IDs this depends on
        metadata: Additional task metadata
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update
    """
    id: str = field(default_factory=lambda: hashlib.sha256(
        f"{id(__class__)}{__import__('time').time()}".encode()
    ).hexdigest()[:16])
    type: TaskType = TaskType.AUTO
    name: str = ""
    files: List[str] = field(default_factory=list)
    action: str = ""
    verification: List[TaskVerification] = field(default_factory=list)
    done: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())

    def to_xml(self, pretty: bool = True) -> str:
        """
        Convert task to XML string.

        Args:
            pretty: Whether to pretty-print the XML

        Returns:
            XML string representation of task
        """
        root = ET.Element("task")
        root.set("type", self.type.value)
        root.set("priority", self.priority.value)
        root.set("status", self.status.value)
        root.set("id", self.id)

        # Name
        name_elem = ET.SubElement(root, "name")
        name_elem.text = self.name

        # Files
        if self.files:
            files_elem = ET.SubElement(root, "files")
            files_elem.text = ",".join(self.files)

        # Action
        action_elem = ET.SubElement(root, "action")
        action_elem.text = self.action

        # Verification steps
        for verify in self.verification:
            root.append(verify.to_xml_element())

        # Done criteria
        if self.done:
            done_elem = ET.SubElement(root, "done")
            done_elem.text = self.done

        # Dependencies
        if self.dependencies:
            deps_elem = ET.SubElement(root, "dependencies")
            deps_elem.text = ",".join(self.dependencies)

        # Metadata
        if self.metadata:
            meta_elem = ET.SubElement(root, "metadata")
            meta_elem.text = json.dumps(self.metadata)

        # Timestamps
        timestamps = ET.SubElement(root, "timestamps")
        ET.SubElement(timestamps, "created").text = self.created_at
        ET.SubElement(timestamps, "updated").text = self.updated_at

        if pretty:
            rough_string = ET.tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ", encoding='unicode')
        else:
            return ET.tostring(root, encoding='unicode')

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "files": self.files,
            "action": self.action,
            "verification": [
                {
                    "command": v.command,
                    "expected_output": v.expected_output,
                    "timeout_seconds": v.timeout_seconds,
                    "required": v.required
                }
                for v in self.verification
            ],
            "done": self.done,
            "priority": self.priority.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_xml(cls, xml_string: str) -> 'XMLTask':
        """
        Create task from XML string.

        Args:
            xml_string: XML string representation

        Returns:
            XMLTask instance
        """
        root = ET.fromstring(xml_string)

        task = cls(
            id=root.get("id", hashlib.sha256(xml_string.encode()).hexdigest()[:16]),
            type=TaskType(root.get("type", "auto")),
            priority=TaskPriority(root.get("priority", "medium")),
            status=TaskStatus(root.get("status", "pending"))
        )

        # Name
        name_elem = root.find("name")
        if name_elem is not None:
            task.name = name_elem.text or ""

        # Files
        files_elem = root.find("files")
        if files_elem is not None and files_elem.text:
            task.files = [f.strip() for f in files_elem.text.split(",")]

        # Action
        action_elem = root.find("action")
        if action_elem is not None:
            task.action = action_elem.text or ""

        # Verification
        task.verification = [
            TaskVerification.from_xml_element(v)
            for v in root.findall("verify")
        ]

        # Done
        done_elem = root.find("done")
        if done_elem is not None:
            task.done = done_elem.text or ""

        # Dependencies
        deps_elem = root.find("dependencies")
        if deps_elem is not None and deps_elem.text:
            task.dependencies = [
                d.strip() for d in deps_elem.text.split(",")
                if d.strip()
            ]

        return task
