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
GSD (Get Shit Done) Upgrade Framework for STAN
================================================

This module implements the GSD-inspired context engineering, XML task formatting,
and spec-driven development capabilities integrated into STAN.

Based on techniques from: https://github.com/glittercowboy/get-shit-done

Core Components:
- XMLTaskFormatter: Structured XML task formatting for Claude optimization
- ContextQualityMonitor: Track context window degradation
- RequirementsExtractor: Spec-driven requirements gathering
- CodebaseMapper: Brownfield codebase analysis
- AtomicCommitWorkflow: Structured git workflow

Version: 1.0.0
Date: 2026-01-03
"""

__version__ = "1.0.0"

# =============================================================================
# XML Task Formatting
# =============================================================================
try:
    from .xml_task_formatting import (
        XMLTask,
        TaskType,
        TaskPriority,
        TaskStatus,
        XMLTaskFormatter,
        TaskVerification,
        parse_xml_task,
        generate_xml_task,
        validate_xml_task
    )
except ImportError:
    XMLTask = None
    TaskType = None
    TaskPriority = None
    TaskStatus = None
    XMLTaskFormatter = None
    TaskVerification = None
    parse_xml_task = None
    generate_xml_task = None
    validate_xml_task = None

# =============================================================================
# Context Quality Monitoring
# =============================================================================
try:
    from .context_quality import (
        ContextQualityMonitor,
        ContextMetrics,
        QualityThreshold,
        DegradationSignal,
        ContextRefreshStrategy,
        TokenEstimator
    )
except ImportError:
    ContextQualityMonitor = None
    ContextMetrics = None
    QualityThreshold = None
    DegradationSignal = None
    ContextRefreshStrategy = None
    TokenEstimator = None

# =============================================================================
# Spec-Driven Requirements
# =============================================================================
try:
    from .spec_driven_development import (
        RequirementsExtractor,
        ProjectSpec,
        RequirementCategory,
        QuestionGenerator,
        RequirementsValidator,
        extract_requirements,
        validate_spec
    )
except ImportError:
    RequirementsExtractor = None
    ProjectSpec = None
    RequirementCategory = None
    QuestionGenerator = None
    RequirementsValidator = None
    extract_requirements = None
    validate_spec = None

# =============================================================================
# Brownfield Codebase Analysis
# =============================================================================
try:
    from .codebase_mapper import (
        CodebaseMapper,
        CodebaseDocumentation,
        StackDocument,
        ArchitectureDocument,
        StructureDocument,
        ConventionsDocument,
        TestingDocument,
        IntegrationsDocument,
        ConcernsDocument,
        map_codebase,
        spawn_parallel_analysis
    )
except ImportError:
    CodebaseMapper = None
    CodebaseDocumentation = None
    StackDocument = None
    ArchitectureDocument = None
    StructureDocument = None
    ConventionsDocument = None
    TestingDocument = None
    IntegrationsDocument = None
    ConcernsDocument = None
    map_codebase = None
