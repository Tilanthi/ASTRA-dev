"""
Code Analyzer for STAN Self-Evolution

Analyzes the astra_core codebase to identify:
- Potential improvement targets
- Code complexity
- Dependencies between modules
- Areas for optimization

This guides the mutation engine toward impactful changes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import ast
import os
import re
from collections import defaultdict
from pathlib import Path


@dataclass
class AnalysisResult:
    """Result of code analysis"""
    filepath: str
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    complexity: float
    lines_of_code: int
    dependencies: Set[str]
    improvement_potential: float
    suggested_mutations: List[str]


class CodeAnalyzer:
    """
    Analyzes astra_core codebase to guide evolution.

    Identifies high-value targets for mutation and provides
    insights into code structure.
    """

    def __init__(self, stan_core_path: str = "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO"):
        self.stan_core_path = stan_core_path
        self.cache: Dict[str, AnalysisResult] = {}
        self.file_tree: Dict[str, List[str]] = {}

    def analyze_codebase(self) -> Dict[str, Any]:
        """
        Analyze entire astra_core codebase.

        Returns:
            Summary of codebase structure
        """
        summary = {
            'total_files': 0,
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'by_module': {},
            'high_potential_targets': [],
        }

        # Find all Python files
        python_files = self._find_python_files()

        for filepath in python_files:
            result = self.analyze_file(filepath)

            if result:
                summary['total_files'] += 1
                summary['total_lines'] += result.lines_of_code
                summary['total_functions'] += len(result.functions)
                summary['total_classes'] += len(result.classes)

                # Group by module
                module = self._get_module_name(filepath)
                if module not in summary['by_module']:
                    summary['by_module'][module] = {
                        'files': [],
                        'lines': 0,
                        'functions': 0,
                        'classes': 0,
                    }

                summary['by_module'][module]['files'].append(filepath)
                summary['by_module'][module]['lines'] += result.lines_of_code
                summary['by_module'][module]['functions'] += len(result.functions)
                summary['by_module'][module]['classes'] += len(result.classes)

                # Track high potential targets
                if result.improvement_potential > 0.5:
                    summary['high_potential_targets'].append({
                        'file': filepath,
                        'potential': result.improvement_potential,
                        'suggestions': result.suggested_mutations,
                    })

        return summary

    def analyze_file(self, filepath: str) -> Optional[AnalysisResult]:
        """
        Analyze a single Python file.

        Args:
            filepath: Relative path to file from astra_core_path

        Returns:
            AnalysisResult or None if analysis fails
        """
        if filepath in self.cache:
            return self.cache[filepath]

        full_path = os.path.join(self.stan_core_path, filepath)

        if not os.path.exists(full_path):
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()

            tree = ast.parse(code)

            # Extract components
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)
            imports = self._extract_imports(tree)
            dependencies = self._extract_dependencies(code, tree)

            # Calculate complexity
            complexity = self._calculate_complexity(tree)

            # Calculate improvement potential
            improvement_potential = self._calculate_improvement_potential(
                filepath, functions, classes, complexity
            )

            # Generate suggestions
            suggestions = self._generate_mutation_suggestions(
                filepath, functions, classes, complexity
            )

            result = AnalysisResult(
                filepath=filepath,
                functions=functions,
                classes=classes,
                imports=imports,
                complexity=complexity,
                lines_of_code=len(code.splitlines()),
                dependencies=dependencies,
                improvement_potential=improvement_potential,
                suggested_mutations=suggestions
            )

            self.cache[filepath] = result
            return result

        except Exception as e:
            return None

    def _find_python_files(self) -> List[str]:
        """Find all Python files in astra_core"""
        python_files = []

        for root, dirs, files in os.walk(self.stan_core_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.evolution_backups']]

            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.stan_core_path)
                    python_files.append(rel_path)

        return python_files

    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function information"""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list],
                    'docstring': ast.get_docstring(node),
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                }

                # Calculate function complexity
                func_info['complexity'] = self._calculate_function_complexity(node)

                functions.append(func_info)

        return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class information"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'bases': [self._get_node_name(base) for base in node.bases],
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    'docstring': ast.get_docstring(node),
                }

                classes.append(class_info)

        return classes

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        return imports

    def _extract_dependencies(self, code: str, tree: ast.AST) -> Set[str]:
        """Extract file dependencies"""
        dependencies = set()

        # Find astra_core imports
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('astra_core'):
                            dependencies.add(alias.name)
                else:
                    module = node.module if node.module else ''
                    if module.startswith('astra_core'):
                        dependencies.add(module)

        return dependencies

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity of the file"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return float(complexity)

    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> float:
        """Calculate complexity of a single function"""
        complexity = 1

        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return float(complexity)

    def _calculate_improvement_potential(self, filepath: str,
                                        functions: List[Dict[str, Any]],
                                        classes: List[Dict[str, Any]],
                                        complexity: float) -> float:
        """Calculate potential for improvement (0-1)"""
        potential = 0.0

        # High complexity files have more optimization potential
        if complexity > 20:
            potential += 0.3
        elif complexity > 10:
            potential += 0.1

        # Files with many functions could benefit from refactoring
        if len(functions) > 10:
            potential += 0.2
        elif len(functions) > 5:
            potential += 0.1

        # Core capability files have higher potential
        capability_keywords = [
            'causal', 'inference', 'discovery', 'reasoning',
            'pattern', 'abstraction', 'uncertainty', 'multi_scale'
        ]

        filepath_lower = filepath.lower()
        for keyword in capability_keywords:
            if keyword in filepath_lower:
                potential += 0.15
                break

        # Files in specific directories
        if 'astro_physics' in filepath:
            potential += 0.2
        elif 'causal' in filepath:
            potential += 0.2
        elif 'reasoning' in filepath:
            potential += 0.15

        return min(potential, 1.0)

    def _generate_mutation_suggestions(self, filepath: str,
                                      functions: List[Dict[str, Any]],
                                      classes: List[Dict[str, Any]],
                                      complexity: float) -> List[str]:
        """Generate specific mutation suggestions"""
        suggestions = []

        # High complexity suggestions
        if complexity > 20:
            suggestions.append("Refactor complex functions for better maintainability")
            suggestions.append("Add helper functions to reduce nesting")

        # Function-level suggestions
        complex_funcs = [f for f in functions if f.get('complexity', 0) > 10]
        if complex_funcs:
            suggestions.append(f"Optimize {len(complex_funcs)} complex functions")

        # Capability-specific suggestions
        if 'causal' in filepath.lower():
            suggestions.append("Add conditional independence tests")
            suggestions.append("Improve confounder detection")

        elif 'pattern' in filepath.lower():
            suggestions.append("Add multi-scale pattern detection")
            suggestions.append("Implement wavelet-based analysis")

        elif 'uncertainty' in filepath.lower():
            suggestions.append("Add Bayesian inference methods")
            suggestions.append("Implement Monte Carlo sampling")

        return suggestions

    def _get_module_name(self, filepath: str) -> str:
        """Extract module name from filepath"""
        parts = filepath.split(os.sep)

        if 'astra_core' in parts:
            idx = parts.index('astra_core')
            if idx + 1 < len(parts):
                return parts[idx + 1]

        return 'root'

    def _get_node_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_node_name(node.value)}[]"
        else:
            return str(type(node).__name__)

    def get_high_value_targets(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get high-value targets for mutation"""
        analysis = self.analyze_codebase()

        targets = analysis.get('high_potential_targets', [])

        # Sort by potential and return top N
        targets.sort(key=lambda x: x['potential'], reverse=True)

        return targets[:top_n]


__all__ = [
    'AnalysisResult',
    'CodeAnalyzer',
]
