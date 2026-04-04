"""
Brownfield Codebase Analyzer
=============================

Implements GSD's parallel codebase mapping for existing projects.

Spawns parallel agents to analyze codebase and creates documentation:
- STACK.md - Languages, frameworks, dependencies
- ARCHITECTURE.md - Patterns, layers, data flow
- STRUCTURE.md - Directory layout, where things live
- CONVENTIONS.md - Code style, naming patterns
- TESTING.md - Test framework, patterns
- INTEGRATIONS.md - External services, APIs
- CONCERNS.md - Tech debt, known issues, fragile areas

Based on: https://github.com/glittercowboy/get-shit-done
"""

from __future__ import annotations
import os
import re
import ast
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter, defaultdict


@dataclass
class StackDocument:
    """Technology stack documentation."""
    languages: Dict[str, int] = field(default_factory=dict)  # language -> file count
    frameworks: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # file -> imports
    build_tools: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate STACK.md content."""
        lines = [
            "# Technology Stack",
            "",
            "## Languages",
            ""
        ]

        for lang, count in sorted(self.languages.items(), key=lambda x: -x[1]):
            lines.append(f"- {lang}: {count} files")

        lines.extend([
            "",
            "## Frameworks",
            ""
        ])

        for fw in self.frameworks:
            lines.append(f"- {fw}")

        if self.build_tools:
            lines.extend(["", "## Build Tools", ""])
            for tool in self.build_tools:
                lines.append(f"- {tool}")

        if self.package_managers:
            lines.extend(["", "## Package Managers", ""])
            for pm in self.package_managers:
                lines.append(f"- {pm}")

        lines.extend(["", "## Key Dependencies", ""])

        # Aggregate top dependencies
        dep_counter = Counter()
        for deps in self.dependencies.values():
            dep_counter.update(deps)

        for dep, count in dep_counter.most_common(20):
            lines.append(f"- {dep} (used in {count} files)")

        return "\n".join(lines)


@dataclass
class ArchitectureDocument:
    """Architecture documentation."""
    patterns: List[str] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)
    data_flow: List[str] = field(default_factory=list)
    components: Dict[str, List[str]] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Generate ARCHITECTURE.md content."""
        lines = [
            "# Architecture",
            "",
            "## Design Patterns",
            ""
        ]

        for pattern in self.patterns:
            lines.append(f"- {pattern}")

        lines.extend(["", "## System Layers", ""])

        for layer in self.layers:
            lines.append(f"- {layer}")

        if self.data_flow:
            lines.extend(["", "## Data Flow", ""])
            for flow in self.data_flow:
                lines.append(f"- {flow}")

        if self.components:
            lines.extend(["", "## Components", ""])
            for comp_type, comps in self.components.items():
                lines.append(f"\n### {comp_type}")
                for comp in comps:
                    lines.append(f"- {comp}")

        return "\n".join(lines)


@dataclass
class StructureDocument:
    """Directory structure documentation."""
    directories: Dict[str, List[str]] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    key_files: Dict[str, str] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Generate STRUCTURE.md content."""
        lines = [
            "# Directory Structure",
            "",
            "## Entry Points",
            ""
        ]

        for entry in self.entry_points:
            lines.append(f"- `{entry}`")

        lines.extend(["", "## Directory Layout", ""])

        for dir_path, contents in sorted(self.directories.items()):
            lines.append(f"\n### {dir_path}")
            for item in contents[:10]:  # Limit per directory
                lines.append(f"- {item}")
            if len(contents) > 10:
                lines.append(f"- ... and {len(contents) - 10} more")

        if self.key_files:
            lines.extend(["", "## Key Files", ""])
            for name, path in self.key_files.items():
                lines.append(f"- {name}: `{path}`")

        return "\n".join(lines)


@dataclass
class ConventionsDocument:
    """Code conventions documentation."""
    naming_patterns: Dict[str, List[str]] = field(default_factory=dict)
    code_style: List[str] = field(default_factory=list)
    formatting: Dict[str, str] = field(default_factory=dict)
    docstring_style: str = ""

    def to_markdown(self) -> str:
        """Generate CONVENTIONS.md content."""
        lines = [
            "# Code Conventions",
            "",
            "## Naming Patterns",
            ""
        ]

        for pattern_type, patterns in self.naming_patterns.items():
            lines.append(f"\n### {pattern_type}")
            for pattern in patterns[:5]:
                lines.append(f"- {pattern}")

        if self.code_style:
            lines.extend(["", "## Code Style", ""])
            for style in self.code_style:
                lines.append(f"- {style}")

        if self.formatting:
            lines.extend(["", "## Formatting", ""])
            for key, value in self.formatting.items():
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)


@dataclass
class TestingDocument:
    """Testing documentation."""
    test_framework: str = ""
    test_patterns: List[str] = field(default_factory=list)
    test_locations: List[str] = field(default_factory=list)
    mock_usage: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate TESTING.md content."""
        lines = [
            "# Testing",
            "",
            "## Test Framework",
            "",
            f"{self.test_framework or 'Not detected'}",
            "",
            "## Test Patterns",
            ""
        ]

        for pattern in self.test_patterns:
            lines.append(f"- {pattern}")

        lines.extend(["", "## Test Locations", ""])

        for location in self.test_locations:
            lines.append(f"- {location}")

        return "\n".join(lines)


@dataclass
class IntegrationsDocument:
    """External integrations documentation."""
    apis: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    external_libs: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate INTEGRATIONS.md content."""
        lines = [
            "# External Integrations",
            ""
        ]

        if self.apis:
            lines.extend(["## APIs", ""] + [f"- {api}" for api in self.apis] + [""])

        if self.services:
            lines.extend(["## Services", ""] + [f"- {svc}" for svc in self.services] + [""])

        if self.databases:
            lines.extend(["## Databases", ""] + [f"- {db}" for db in self.databases] + [""])

        if self.external_libs:
            lines.extend(["## External Libraries", ""] + [f"- {lib}" for lib in self.external_libs] + [""])

        return "\n".join(lines)


@dataclass
class ConcernsDocument:
    """Technical concerns documentation."""
    tech_debt: List[str] = field(default_factory=list)
    known_issues: List[str] = field(default_factory=list)
    fragile_areas: List[str] = field(default_factory=list)
    improvement_opportunities: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate CONCERNS.md content."""
        lines = [
            "# Technical Concerns",
            ""
        ]

        if self.tech_debt:
            lines.extend(["## Technical Debt", ""] + [f"- {item}" for item in self.tech_debt] + [""])

        if self.known_issues:
            lines.extend(["## Known Issues", ""] + [f"- {item}" for item in self.known_issues] + [""])

        if self.fragile_areas:
            lines.extend(["## Fragile Areas", ""] + [f"- {item}" for item in self.fragile_areas] + [""])

        if self.improvement_opportunities:
            lines.extend(["## Improvement Opportunities", ""] + [f"- {item}" for item in self.improvement_opportunities] + [""])

        return "\n".join(lines)


@dataclass
class CodebaseDocumentation:
    """Complete codebase documentation."""
    stack: StackDocument = field(default_factory=StackDocument)
    architecture: ArchitectureDocument = field(default_factory=ArchitectureDocument)
    structure: StructureDocument = field(default_factory=StructureDocument)
    conventions: ConventionsDocument = field(default_factory=ConventionsDocument)
    testing: TestingDocument = field(default_factory=TestingDocument)
    integrations: IntegrationsDocument = field(default_factory=IntegrationsDocument)
    concerns: ConcernsDocument = field(default_factory=ConcernsDocument)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def save_all(self, output_dir: str) -> None:
        """Save all documentation files."""
        output_path = Path(output_dir) / ".planning" / "codebase"
        output_path.mkdir(parents=True, exist_ok=True)

        (output_path / "STACK.md").write_text(self.stack.to_markdown())
        (output_path / "ARCHITECTURE.md").write_text(self.architecture.to_markdown())
        (output_path / "STRUCTURE.md").write_text(self.structure.to_markdown())
        (output_path / "CONVENTIONS.md").write_text(self.conventions.to_markdown())
        (output_path / "TESTING.md").write_text(self.testing.to_markdown())
        (output_path / "INTEGRATIONS.md").write_text(self.integrations.to_markdown())
        (output_path / "CONCERNS.md").write_text(self.concerns.to_markdown())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stack": self.stack.__dict__,
            "architecture": self.architecture.__dict__,
            "structure": self.structure.__dict__,
            "conventions": self.conventions.__dict__,
            "testing": self.testing.__dict__,
            "integrations": self.integrations.__dict__,
            "concerns": self.concerns.__dict__,
            "metadata": self.metadata
        }


class CodebaseMapper:
    """
    Map existing codebase through parallel analysis.

    Spawns parallel agents to analyze different aspects of the codebase,
    similar to GSD's `/gsd:map-codebase` command.
    """

    def __init__(self, max_workers: int = 7):
        """
        Initialize codebase mapper.

        Args:
            max_workers: Number of parallel workers for analysis
        """
        self.max_workers = max_workers

    def map_codebase(self, path: str) -> CodebaseDocumentation:
        """
        Map the codebase at the given path.

        Args:
            path: Path to codebase root

        Returns:
            Complete codebase documentation
        """
        path_obj = Path(path).resolve()

        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path}")

        # Spawn parallel analysis
        docs = CodebaseDocumentation()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._analyze_stack, path_obj): "stack",
                executor.submit(self._analyze_architecture, path_obj): "architecture",
                executor.submit(self._analyze_structure, path_obj): "structure",
                executor.submit(self._analyze_conventions, path_obj): "conventions",
                executor.submit(self._analyze_testing, path_obj): "testing",
                executor.submit(self._analyze_integrations, path_obj): "integrations",
