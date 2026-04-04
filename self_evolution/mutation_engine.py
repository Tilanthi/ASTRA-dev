"""
Mutation Engine for STAN Self-Evolution

Generates code modifications (mutations) to explore the space of
potential improvements. Mutations are:
- Targeted: Focus on specific capability areas
- Safe: Maintain code validity
- Reversible: Can rollback if needed
- Diverse: Explore different improvement strategies
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import ast
import os
import re
import shutil
import time
from pathlib import Path
import hashlib


class MutationType(Enum):
    """Types of code mutations"""
    # Algorithm improvements
    ALGORITHM_OPTIMIZATION = "algorithm_optimization"
    NUMERICAL_PRECISION = "numerical_precision"
    CONVERGENCE_ACCELERATION = "convergence_acceleration"

    # Reasoning enhancements
    CAUSAL_MODEL_UPDATE = "causal_model_update"
    INFERENCE_RULE_ADDITION = "inference_rule_addition"
    ABSTRACTION_REFINEMENT = "abstraction_refinement"

    # Knowledge integration
    DOMAIN_KNOWLEDGE_ADDITION = "domain_knowledge_addition"
    CROSS_DOMAIN_LINKING = "cross_domain_linking"
    PHYSICS_CONSTRAINT_ADDITION = "physics_constraint_addition"

    # Architecture changes
    MODULE_INTEGRATION = "module_integration"
    CAPABILITY_COMPOSITION = "capability_composition"
    MEMORY_OPTIMIZATION = "memory_optimization"

    # Parameter tuning
    HYPERPARAMETER_ADJUSTMENT = "hyperparameter_adjustment"
    THRESHOLD_OPTIMIZATION = "threshold_optimization"


@dataclass
class MutationSpec:
    """Specification for a mutation"""
    mutation_type: MutationType
    target_file: str
    target_function: Optional[str] = None
    description: str = ""
    code_changes: Dict[str, str] = field(default_factory=dict)  # pattern -> replacement
    new_code: Optional[str] = None
    validation_tests: List[str] = field(default_factory=list)
    expected_improvement: str = ""  # Which metric should improve


@dataclass
class MutationResult:
    """Result of applying a mutation"""
    mutation_spec: MutationSpec
    success: bool
    files_modified: List[str]
    backup_paths: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    validation_passed: bool = False
    timestamp: float = field(default_factory=time.time)


class CodeAnalyzer:
    """Analyzes code to identify mutation targets"""

    def __init__(self, stan_core_path: str):
        self.stan_core_path = stan_core_path
        self.cache: Dict[str, Any] = {}

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze a Python file and extract structure"""
        if filepath in self.cache:
            return self.cache[filepath]

        full_path = os.path.join(self.stan_core_path, filepath)

        if not os.path.exists(full_path):
            return {'error': 'File not found'}

        try:
            with open(full_path, 'r') as f:
                code = f.read()

            tree = ast.parse(code)

            analysis = {
                'filepath': filepath,
                'functions': [],
                'classes': [],
                'imports': [],
                'complexity': 0,
                'lines': len(code.splitlines()),
            }

            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'lineno': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node),
                    }
                    analysis['functions'].append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        'name': node.name,
                        'lineno': node.lineno,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    }
                    analysis['classes'].append(class_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis['imports'].append(alias.name)
                    else:
                        module = node.module if node.module else ''
                        for alias in node.names:
                            analysis['imports'].append(f"{module}.{alias.name}")

            self.cache[filepath] = analysis
            return analysis

        except Exception as e:
            return {'error': str(e)}

    def find_mutation_targets(self, capability_area: str) -> List[MutationSpec]:
        """Find potential mutation targets for a capability area"""
        targets = []

        # Map capability areas to files
        area_to_files = {
            'causal_inference': [
                'astra_core/causal/discovery/pc_algorithm.py',
                'astra_core/causal/model/counterfactual.py',
            ],
            'pattern_discovery': [
                'astra_core/astro_physics/spectral_line_analysis.py',
                'astra_core/arc_agi/pattern_library.py',
            ],
            'abstraction': [
                'astra_core/reasoning/abstraction_stack.py',
                'astra_core/memory/abstraction_memory.py',
            ],
            'uncertainty': [
                'astra_core/astro_physics/uncertainty_quantification.py',
            ],
            'multi_scale': [
                'astra_core/astro_physics/multiscale_coupling.py',
            ],
        }

        files = area_to_files.get(capability_area, [])

        for filepath in files:
            analysis = self.analyze_file(filepath)

            if 'error' not in analysis:
                for func in analysis.get('functions', []):
                    targets.append(self._create_mutation_spec(
                        filepath, func['name'], capability_area
                    ))

        return targets

    def _create_mutation_spec(self, filepath: str, func_name: str,
                             capability_area: str) -> MutationSpec:
        """Create a mutation spec for a function"""
        # Determine mutation type based on capability area
        mutation_types = {
            'causal_inference': MutationType.CAUSAL_MODEL_UPDATE,
            'pattern_discovery': MutationType.ALGORITHM_OPTIMIZATION,
            'abstraction': MutationType.ABSTRACTION_REFINEMENT,
            'uncertainty': MutationType.NUMERICAL_PRECISION,
            'multi_scale': MutationType.CAPABILITY_COMPOSITION,
        }

        mutation_type = mutation_types.get(capability_area, MutationType.ALGORITHM_OPTIMIZATION)

        return MutationSpec(
            mutation_type=mutation_type,
            target_file=filepath,
            target_function=func_name,
            description=f"Improve {func_name} for better {capability_area}",
            expected_improvement=capability_area
        )


class MutationEngine:
    """
    Engine for generating and applying code mutations.

    The mutation engine explores the space of potential improvements
    by making targeted code modifications and testing their effects.
    """

    def __init__(self, stan_core_path: str):
        self.stan_core_path = stan_core_path
        self.analyzer = CodeAnalyzer(stan_core_path)
        self.mutation_history: List[MutationResult] = []
        self.backup_dir = os.path.join(stan_core_path, ".evolution_backups")

        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def generate_mutations(self, capability_profile: Dict[str, float],
                         num_mutations: int = 10) -> List[MutationSpec]:
        """
        Generate mutations targeting weak capabilities.

        Args:
            capability_profile: Current capability scores
            num_mutations: Number of mutations to generate

        Returns:
            List of mutation specifications
        """
        mutations = []

        # Identify weakest capabilities
        sorted_capabilities = sorted(capability_profile.items(), key=lambda x: x[1])

        # Generate mutations for weakest areas
        for capability, score in sorted_capabilities[:num_mutations]:
            mutation = self._generate_targeted_mutation(capability, score)
            if mutation:
                mutations.append(mutation)

        # Add some exploratory mutations
        exploratory = self._generate_exploratory_mutations(num_mutations // 2)
        mutations.extend(exploratory)

        return mutations[:num_mutations]

    def _generate_targeted_mutation(self, capability: str, score: float) -> Optional[MutationSpec]:
        """Generate a mutation targeting a specific capability"""
        # Map capabilities to implementation strategies
        strategies = {
            'pattern_discovery': self._improve_pattern_discovery,
            'causal_inference': self._improve_causal_inference,
            'abstraction_formation': self._improve_abstraction,
            'uncertainty_quantification': self._improve_uncertainty,
            'multi_scale_inference': self._improve_multi_scale,
        }

        strategy = strategies.get(capability)
        if strategy:
            return strategy()

        return None

    def _improve_pattern_discovery(self) -> MutationSpec:
        """Generate mutation to improve pattern discovery"""
        return MutationSpec(
            mutation_type=MutationType.ALGORITHM_OPTIMIZATION,
            target_file="astra_core/astro_physics/spectral_line_analysis.py",
            target_function="identify_lines",
            description="Add multi-scale pattern detection for spectral lines",
            code_changes={
                "# Simple thresholding": "# Multi-scale thresholding with wavelet detection",
                "find_peaks": "find_peaks_plus_wavelets",
            },
            expected_improvement="pattern_discovery"
        )

    def _improve_causal_inference(self) -> MutationSpec:
        """Generate mutation to improve causal inference"""
        return MutationSpec(
            mutation_type=MutationType.CAUSAL_MODEL_UPDATE,
            target_file="astra_core/causal/discovery/pc_algorithm.py",
            target_function="discover_structure",
            description="Add conditional independence tests for time-series data",
            code_changes={
                "independence_test": "conditional_independence_test_with_lag",
            },
            expected_improvement="causal_inference"
        )

    def _improve_abstraction(self) -> MutationSpec:
        """Generate mutation to improve abstraction formation"""
        return MutationSpec(
            mutation_type=MutationType.ABSTRACTION_REFINEMENT,
            target_file="astra_core/reasoning/abstraction_stack.py",
            target_function="extract_principle",
            description="Add symbolic abstraction from numerical patterns",
            new_code='''
def extract_principle_enhanced(examples):
    """Extract principle with symbolic reasoning"""
    # Numerical pattern
    numerical = extract_principle(examples)

    # Add symbolic interpretation
    symbolic = interpret_symbolically(examples)

    # Combine
    return {"numerical": numerical, "symbolic": symbolic}
''',
            expected_improvement="abstraction_formation"
        )

    def _improve_uncertainty(self) -> MutationSpec:
        """Generate mutation to improve uncertainty quantification"""
        return MutationSpec(
            mutation_type=MutationType.NUMERICAL_PRECISION,
            target_file="astra_core/astro_physics/uncertainty_quantification.py",
            target_function="propagate_uncertainty",
            description="Add Bayesian uncertainty propagation",
            code_changes={
                "linear_propagation": "bayesian_propagation_mcmc",
            },
            expected_improvement="uncertainty_quantification"
        )

    def _improve_multi_scale(self) -> MutationSpec:
        """Generate mutation to improve multi-scale inference"""
        return MutationSpec(
            mutation_type=MutationType.CAPABILITY_COMPOSITION,
            target_file="astra_core/astro_physics/multiscale_coupling.py",
            target_function="integrate_scales",
            description="Add scale-crossing constraints from physics",
            new_code='''
def integrate_scales_with_constraints(scales_data):
    """Integrate scales with physical constraints"""
    result = integrate_scales(scales_data)

    # Add conservation laws across scales
    result = apply_conservation_laws(result)

    # Add energy cascade constraints
    result = apply_energy_cascade(result)

    return result
''',
            expected_improvement="multi_scale_inference"
        )

    def _generate_exploratory_mutations(self, count: int) -> List[MutationSpec]:
        """Generate exploratory mutations for novel improvements"""
        mutations = []

        exploratory_ideas = [
            MutationSpec(
                mutation_type=MutationType.CROSS_DOMAIN_LINKING,
                target_file="astra_core/astro_physics/physics.py",
                description="Link quantum mechanics with stellar astrophysics",
                expected_improvement="cross_domain_transfer"
            ),
            MutationSpec(
                mutation_type=MutationType.PHYSICS_CONSTRAINT_ADDITION,
                target_file="astra_core/causal/model/scm.py",
                description="Add thermodynamic constraints to causal models",
                expected_improvement="logical_consistency"
            ),
            MutationSpec(
                mutation_type=MutationType.MODULE_INTEGRATION,
                target_file="astra_core/__init__.py",
                description="Integrate swarm intelligence with causal discovery",
                expected_improvement="generalization_score"
            ),
        ]

        return exploratory_ideas[:count]

    def apply_mutation(self, mutation: MutationSpec) -> MutationResult:
        """
        Apply a mutation to the codebase.

        Args:
            mutation: Mutation specification

        Returns:
            MutationResult with outcome
        """
        result = MutationResult(
            mutation_spec=mutation,
            success=False,
            files_modified=[]
        )

        try:
            target_path = os.path.join(self.stan_core_path, mutation.target_file)

            if not os.path.exists(target_path):
                result.error_message = f"Target file not found: {target_path}"
                return result

            # Create backup
            backup_path = self._create_backup(target_path)
            result.backup_paths[mutation.target_file] = backup_path

            # Read original code
            with open(target_path, 'r') as f:
                original_code = f.read()

            # Apply mutation
            if mutation.new_code:
                # For new code additions
                modified_code = self._apply_new_code(original_code, mutation)
            elif mutation.code_changes:
                # For code replacements
                modified_code = self._apply_code_changes(original_code, mutation)
            else:
                result.error_message = "No code changes specified"
                return result

            # Write modified code
            with open(target_path, 'w') as f:
                f.write(modified_code)

            result.success = True
            result.files_modified.append(mutation.target_file)

            # Run validation tests
            result.validation_passed = self._validate_mutation(mutation)

        except Exception as e:
            result.error_message = str(e)
            # Rollback on error
            self._rollback_mutation(result)

        self.mutation_history.append(result)
        return result

    def _create_backup(self, filepath: str) -> str:
        """Create backup of a file"""
        timestamp = int(time.time())
        hash_val = hashlib.md5(filepath.encode()).hexdigest()[:8]

        filename = os.path.basename(filepath)
        backup_name = f"{filename}.{timestamp}.{hash_val}.bak"

        backup_path = os.path.join(self.backup_dir, backup_name)
        shutil.copy2(filepath, backup_path)

        return backup_path

    def _apply_new_code(self, original_code: str, mutation: MutationSpec) -> str:
        """Apply new code addition"""
        if mutation.target_function:
            # Find target function and add new code after it
            pattern = f"def {mutation.target_function}("
            if pattern in original_code:
                # Find the end of the function
                lines = original_code.split('\n')
                insert_idx = len(lines)

                for i, line in enumerate(lines):
                    if pattern in line:
                        # Find the end of this function
                        indent = len(line) - len(line.lstrip())
                        for j in range(i + 1, len(lines)):
                            if j < len(lines) and lines[j].strip() and not lines[j].startswith(' ' * (indent + 1)):
                                insert_idx = j
                                break
                        break

                # Insert new code
                new_lines = lines[:insert_idx] + [mutation.new_code] + lines[insert_idx:]
                return '\n'.join(new_lines)

        # If no specific target, append to file
        return original_code + '\n\n' + mutation.new_code

    def _apply_code_changes(self, original_code: str, mutation: MutationSpec) -> str:
        """Apply code replacements"""
        modified_code = original_code

        for pattern, replacement in mutation.code_changes.items():
            modified_code = modified_code.replace(pattern, replacement)

        return modified_code

    def _validate_mutation(self, mutation: MutationSpec) -> bool:
        """Validate that mutation doesn't break syntax"""
        try:
            target_path = os.path.join(self.stan_core_path, mutation.target_file)

            with open(target_path, 'r') as f:
                code = f.read()

            # Check syntax
            ast.parse(code)

            return True

        except Exception:
            return False

    def rollback_mutation(self, result: MutationResult) -> bool:
        """
        Rollback a mutation.

        Args:
            result: MutationResult to rollback

        Returns:
            True if rollback successful
        """
        return self._rollback_mutation(result)

    def _rollback_mutation(self, result: MutationResult) -> bool:
        """Internal rollback implementation"""
        try:
            for filepath, backup_path in result.backup_paths.items():
                target_path = os.path.join(self.stan_core_path, filepath)

                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, target_path)
                    return True

            return False

        except Exception:
            return False


__all__ = [
    'MutationType',
    'MutationSpec',
    'MutationResult',
    'CodeAnalyzer',
    'MutationEngine',
]
