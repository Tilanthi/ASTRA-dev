"""
Meta Prompt Generator for Autocatalytic Self-Compiler

Generates improvement prompts based on error patterns and
performance analysis to guide architecture evolution.

Version: 4.0.0
Date: 2026-03-17
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re


class ErrorPattern(Enum):
    """Common error patterns in cognitive architecture"""
    CONTEXT_SWITCH_FAILURE = "context_switch"       # Failed to switch context
    MEMORY_RETRIEVAL_FAILURE = "memory_retrieval"   # Failed to retrieve memory
    CONFIDENCE_MISALIGNED = "confidence_misaligned"  # Confidence inaccurate
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"  # Temporal reasoning issue
    ABSTRACTION_MISMATCH = "abstraction_mismatch"   # Wrong abstraction level
    MIND_CONFLICT = "mind_conflict"                 # Mind disagreement unresolved
    BOTTLENECK = "bottleneck"                       # Performance bottleneck
    SAFETY_VIOLATION = "safety_violation"           # Safety check failed


class PromptCategory(Enum):
    """Categories of improvement prompts"""
    ARCHITECTURE = "architecture"      # Structural changes
    OPTIMIZATION = "optimization"      # Performance improvements
    FEATURE = "feature"               # New capabilities
    FIX = "fix"                       # Bug fixes
    REFACTOR = "refactor"             # Code quality


@dataclass
class ErrorInstance:
    """An instance of an error"""
    pattern: ErrorPattern
    description: str
    context: Dict[str, Any]
    severity: float  # 0.0 to 1.0
    frequency: int
    first_seen: float
    last_seen: float


@dataclass
class MetaPrompt:
    """A generated prompt for architecture improvement"""
    prompt_id: str
    category: PromptCategory
    title: str
    description: str
    target_component: str
    suggested_mutations: List[str]
    priority: float  # 0.0 to 1.0
    estimated_impact: float
    based_on_errors: List[ErrorPattern]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptGenerationResult:
    """Result of prompt generation"""
    prompts: List[MetaPrompt]
    total_errors_analyzed: int
    dominant_patterns: List[ErrorPattern]
    recommended_priority: str


class MetaPromptGenerator:
    """
    Generates improvement prompts based on error analysis.

    Features:
    - Detect error patterns
    - Generate targeted improvement prompts
    - Prioritize by impact and frequency
    - Track prompt effectiveness
    """

    def __init__(self):
        self.error_history: List[ErrorInstance] = []
        self.prompt_history: List[MetaPrompt] = []
        self.prompt_effectiveness: Dict[str, float] = {}
        self.pattern_templates: Dict[ErrorPattern, List[str]] = {}
        self._setup_templates()

    def _setup_templates(self) -> None:
        """Setup prompt templates for each error pattern."""
        self.pattern_templates = {
            ErrorPattern.CONTEXT_SWITCH_FAILURE: [
                "Add predictive context switching based on behavioral patterns",
                "Implement smoother context transitions with fade in/out",
                "Cache context state for faster restoration",
                "Add context prediction pre-loading"
            ],
            ErrorPattern.MEMORY_RETRIEVAL_FAILURE: [
                "Improve memory indexing with semantic hashing",
                "Add associative memory retrieval for related concepts",
                "Implement memory prioritization based on relevance",
                "Add fallback retrieval strategies"
            ],
            ErrorPattern.CONFIDENCE_MISALIGNED: [
                "Implement confidence calibration mechanism",
                "Add meta-cognitive confidence review",
                "Track confidence vs outcome for calibration",
                "Adjust confidence based on historical accuracy"
            ],
            ErrorPattern.TEMPORAL_INCONSISTENCY: [
                "Add temporal consistency checks",
                "Implement temporal hierarchy alignment",
                "Add event timeline validation",
                "Cross-reference temporal scales"
            ],
            ErrorPattern.ABSTRACTION_MISMATCH: [
                "Add automatic abstraction level detection",
                "Implement dynamic adjustment based on task",
                "Add abstraction quality feedback",
                "Cross-validate abstraction choice"
            ],
            ErrorPattern.MIND_CONFLICT: [
                "Implement anticipatory conflict resolution",
                "Add mind collaboration protocols",
                "Improve arbitration strategies",
                "Add cross-mind validation"
            ],
            ErrorPattern.BOTTLENECK: [
                "Parallelize bottleneck component",
                "Add caching for frequently accessed data",
                "Optimize algorithmic complexity",
                "Implement lazy evaluation"
            ],
            ErrorPattern.SAFETY_VIOLATION: [
                "Add additional safety validation",
                "Implement stricter bounds checking",
                "Add fail-safe mechanisms",
                "Improve error handling"
            ]
        }

    def record_error(
        self,
        pattern: ErrorPattern,
        description: str,
        context: Dict[str, Any],
        severity: float = 0.5
    ) -> None:
        """Record an error instance."""
        import time

        # Check if similar error exists
        existing = None
        for error in self.error_history:
            if error.pattern == pattern and error.description == description:
                existing = error
                break

        if existing:
            existing.frequency += 1
            existing.last_seen = time.time()
            existing.severity = max(existing.severity, severity)
        else:
            error = ErrorInstance(
                pattern=pattern,
                description=description,
                context=context,
                severity=severity,
                frequency=1,
                first_seen=time.time(),
                last_seen=time.time()
            )
            self.error_history.append(error)

    def analyze_errors(self) -> List[ErrorPattern]:
        """Analyze errors to identify dominant patterns."""
        pattern_scores = defaultdict(float)

        for error in self.error_history:
            # Score based on severity and frequency
            score = error.severity * (1 + error.frequency * 0.1)
            pattern_scores[error.pattern] += score

        # Sort by score
        sorted_patterns = sorted(
            pattern_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [p[0] for p in sorted_patterns]

    def generate_prompts(
        self,
        max_prompts: int = 10,
        focus_area: Optional[str] = None
    ) -> PromptGenerationResult:
        """
        Generate improvement prompts based on error analysis.

        Args:
            max_prompts: Maximum number of prompts to generate
            focus_area: Optional component to focus on

        Returns:
            PromptGenerationResult with generated prompts
        """
        dominant_patterns = self.analyze_errors()
        prompts = []

        for pattern in dominant_patterns[:max_prompts]:
            # Get relevant errors
            relevant_errors = [
                e for e in self.error_history
                if e.pattern == pattern
            ]

            if not relevant_errors:
                continue

            # Calculate priority
            total_severity = sum(e.severity for e in relevant_errors)
            total_frequency = sum(e.frequency for e in relevant_errors)
            priority = min(1.0, (total_severity * 0.6 + total_frequency * 0.1) / 10)

            # Generate prompts from templates
            templates = self.pattern_templates.get(pattern, [])
            for i, template in enumerate(templates):
                if len(prompts) >= max_prompts:
                    break

                # Determine category
                category = self._determine_category(pattern, i)

                # Determine target component
                target = self._determine_target(pattern, relevant_errors[0])

                prompt = MetaPrompt(
                    prompt_id=f"{pattern.value}_{i}_{int(time.time())}",
                    category=category,
                    title=self._generate_title(pattern, template),
                    description=template,
                    target_component=target if not focus_area else focus_area,
                    suggested_mutations=self._generate_mutations(pattern, template),
                    priority=priority,
                    estimated_impact=priority * 0.8,
                    based_on_errors=[pattern],
                    metadata={
                        "error_count": len(relevant_errors),
                        "total_severity": total_severity
                    }
                )
                prompts.append(prompt)

        self.prompt_history.extend(prompts)

        return PromptGenerationResult(
            prompts=prompts,
            total_errors_analyzed=len(self.error_history),
            dominant_patterns=dominant_patterns,
            recommended_priority=self._get_recommended_priority(prompts)
        )

    def _determine_category(self, pattern: ErrorPattern, index: int) -> PromptCategory:
        """Determine category for a prompt."""
        if pattern in [ErrorPattern.BOTTLENECK]:
            return PromptCategory.OPTIMIZATION
        elif pattern in [ErrorPattern.CONTEXT_SWITCH_FAILURE, ErrorPattern.MIND_CONFLICT]:
            return PromptCategory.ARCHITECTURE
        elif pattern in [ErrorPattern.SAFETY_VIOLATION]:
            return PromptCategory.FIX
        else:
            return PromptCategory.FEATURE if index == 0 else PromptCategory.OPTIMIZATION

    def _determine_target(self, pattern: ErrorPattern, error: ErrorInstance) -> str:
        """Determine target component for a prompt."""
        component_map = {
            ErrorPattern.CONTEXT_SWITCH_FAILURE: "meta_context_engine",
            ErrorPattern.MEMORY_RETRIEVAL_FAILURE: "memory",
            ErrorPattern.CONFIDENCE_MISALIGNED: "metacognitive_core",
            ErrorPattern.TEMPORAL_INCONSISTENCY: "temporal_hierarchy",
            ErrorPattern.ABSTRACTION_MISMATCH: "cognitive_relativity_navigator",
            ErrorPattern.MIND_CONFLICT: "multi_mind_orchestrator",
            ErrorPattern.BOTTLENECK: error.context.get("component", "core"),
            ErrorPattern.SAFETY_VIOLATION: error.context.get("component", "core")
        }
        return component_map.get(pattern, "core")

    def _generate_title(self, pattern: ErrorPattern, template: str) -> str:
        """Generate title for a prompt."""
        pattern_name = pattern.value.replace("_", " ").title()
        return f"Improve {pattern_name}: {template[:50]}..."

    def _generate_mutations(self, pattern: ErrorPattern, template: str) -> List[str]:
        """Generate specific mutation suggestions."""
        mutations = []

        # Extract action verbs from template
        actions = re.findall(r'\b(Add|Implement|Improve|Optimize|Parallelize|Cache)\s+(\w+)', template)

        for action, target in actions:
            mutation_type = "ADD_MODULE" if action == "Add" else "MODIFY_CONNECTION"
            mutations.append(f"{mutation_type}: {target}")

        return mutations if mutations else ["OPTIMIZE_FLOW: general"]

    def _get_recommended_priority(self, prompts: List[MetaPrompt]) -> str:
        """Get recommended priority level."""
        if not prompts:
            return "low"

        avg_priority = sum(p.priority for p in prompts) / len(prompts)

        if avg_priority > 0.7:
            return "high"
        elif avg_priority > 0.4:
            return "medium"
        else:
            return "low"

    def record_prompt_effectiveness(self, prompt_id: str, effectiveness: float) -> None:
        """Record how effective a prompt was."""
        self.prompt_effectiveness[prompt_id] = effectiveness

    def get_top_prompts(
        self,
        category: Optional[PromptCategory] = None,
        limit: int = 5
    ) -> List[MetaPrompt]:
        """Get top prompts by priority."""
        prompts = self.prompt_history

        if category:
            prompts = [p for p in prompts if p.category == category]

        return sorted(prompts, key=lambda p: p.priority, reverse=True)[:limit]

    def cleanup_old_errors(self, max_age: float = 604800.0) -> int:
        """Remove errors older than max_age (default 7 days)."""
        import time
        current_time = time.time()
        cutoff_time = current_time - max_age

        initial_count = len(self.error_history)
        self.error_history = [
            e for e in self.error_history
            if e.last_seen >= cutoff_time
        ]

        return initial_count - len(self.error_history)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about error patterns and prompts."""
        pattern_counts = defaultdict(int)
        for error in self.error_history:
            pattern_counts[error.pattern] += error.frequency

        return {
            "total_errors": len(self.error_history),
            "total_prompts": len(self.prompt_history),
            "pattern_distribution": {
                p.value: count for p, count in pattern_counts.items()
            },
            "avg_prompt_priority": sum(p.priority for p in self.prompt_history) / len(self.prompt_history) if self.prompt_history else 0,
            "effective_prompts": sum(1 for e in self.prompt_effectiveness.values() if e > 0.7)
        }


# =============================================================================
# Factory Functions
# =============================================================================

def create_meta_prompt_generator() -> MetaPromptGenerator:
    """Create a meta prompt generator."""
    return MetaPromptGenerator()
