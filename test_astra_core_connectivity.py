#!/usr/bin/env python3
"""
Deep connectivity test for astra_core module.

Tests all imports, dependencies, and cross-references to ensure
everything can communicate properly.
"""
import sys
import os
import traceback
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Add project root to path
ASTRA_ROOT = Path(__file__).parent
sys.path.insert(0, str(ASTRA_ROOT))

class ConnectivityTester:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.successes = []
        self.astra_root = ASTRA_ROOT
        self.astra_core_path = self.astra_root / "astra_core"

    def log_error(self, component: str, error: str):
        self.errors.append((component, error))
        print(f"❌ ERROR [{component}]: {error}")

    def log_warning(self, component: str, warning: str):
        self.warnings.append((component, warning))
        print(f"⚠️  WARNING [{component}]: {warning}")

    def log_success(self, component: str, message: str):
        self.successes.append((component, message))
        print(f"✅ SUCCESS [{component}]: {message}")

    def test_astra_core_import(self):
        """Test that astra_core can be imported."""
        print("\n" + "="*80)
        print("Testing astra_core package import")
        print("="*80)

        try:
            import astra_core
            self.log_success("astra_core", f"Package imported successfully (version {getattr(astra_core, '__version__', 'unknown')})")
            return True
        except Exception as e:
            self.log_error("astra_core", f"Failed to import: {e}")
            return False

    def test_main_exports(self):
        """Test main exports from astra_core.__init__."""
        print("\n" + "="*80)
        print("Testing main astra_core exports")
        print("="*80)

        try:
            import astra_core

            # Test Unified System
            if hasattr(astra_core, 'UnifiedSTANSystem'):
                self.log_success("astra_core.UnifiedSTANSystem", "Export available")
            else:
                self.log_warning("astra_core.UnifiedSTANSystem", "Not exported (may be optional)")

            # Test Memory Systems
            memory_exports = ['MORKOntology', 'MemoryGraph', 'MilvusVectorStore']
            for export in memory_exports:
                if hasattr(astra_core, export):
                    self.log_success(f"astra_core.{export}", "Export available")
                else:
                    self.log_warning(f"astra_core.{export}", "Not exported")

            # Test Causal Components
            causal_exports = ['StructuralCausalModel', 'PCAlgorithm', 'Intervention', 'CounterfactualQuery']
            for export in causal_exports:
                if hasattr(astra_core, export):
                    self.log_success(f"astra_core.{export}", "Export available")
                else:
                    self.log_warning(f"astra_core.{export}", "Not exported")

            # Test Domain System
            domain_exports = ['BaseDomainModule', 'DomainRegistry', 'ExoplanetDomain']
            for export in domain_exports:
                if hasattr(astra_core, export):
                    self.log_success(f"astra_core.{export}", "Export available")
                else:
                    self.log_warning(f"astra_core.{export}", "Not exported")

            return True

        except Exception as e:
            self.log_error("astra_core.exports", f"Failed to test exports: {e}")
            traceback.print_exc()
            return False

    def test_subdirectory_imports(self):
        """Test imports from astra_core subdirectories."""
        print("\n" + "="*80)
        print("Testing astra_core subdirectory imports")
        print("="*80)

        subdirs_to_test = [
            ('memory', ['memory_graph', 'vector_store', 'mork_ontology']),
            ('causal', ['model', 'discovery', 'inference']),
            ('core', ['unified', 'unified_enhanced']),
            ('reasoning', ['cross_domain_meta_learner']),
            ('physics', ['unified_physics']),
            ('domains', ['exoplanets', 'cosmology', 'gravitational_waves']),
        ]

        for subdir_name, modules in subdirs_to_test:
            subdir_path = self.astra_core_path / subdir_name
            if not subdir_path.exists():
                self.log_warning(f"astra_core.{subdir_name}", "Subdirectory does not exist")
                continue

            for module_name in modules:
                try:
                    full_module_name = f"astra_core.{subdir_name}.{module_name}"
                    importlib.import_module(full_module_name)
                    self.log_success(full_module_name, "Module imported successfully")
                except ImportError as e:
                    # Check if it's a package (has __init__.py)
                    module_path = subdir_path / f"{module_name}.py"
                    init_path = subdir_path / module_name / "__init__.py"

                    if module_path.exists() or init_path.exists():
                        self.log_error(full_module_name, f"Module exists but import failed: {e}")
                    else:
                        self.log_warning(full_module_name, f"Module does not exist")
                except Exception as e:
                    self.log_error(full_module_name, f"Unexpected error: {e}")

    def test_cross_references(self):
        """Test cross-references between modules."""
        print("\n" + "="*80)
        print("Testing cross-references between modules")
        print("="*80)

        # Test that core modules can reference memory
        try:
            from astra_core.memory import MemoryGraph, GraphNode
            from astra_core.core.unified import UnifiedSTANSystem

            self.log_success("cross_ref.core->memory", "Core can import from memory")
        except Exception as e:
            self.log_error("cross_ref.core->memory", f"Failed: {e}")

        # Test that causal modules can reference reasoning
        try:
            from astra_core.causal.model import StructuralCausalModel
            from astra_core.reasoning import CausalReasoner

            self.log_success("cross_ref.causal->reasoning", "Causal can import from reasoning")
        except Exception as e:
            self.log_warning("cross_ref.causal->reasoning", f"Failed: {e}")

        # Test that domains can reference physics
        try:
            from astra_core.domains import BaseDomainModule
            from astra_core.physics import UnifiedPhysicsEngine

            self.log_success("cross_ref.domains->physics", "Domains can import from physics")
        except Exception as e:
            self.log_warning("cross_ref.domains->physics", f"Failed: {e}")

    def test_data_connectivity(self):
        """Test connectivity to moved data folders."""
        print("\n" + "="*80)
        print("Testing data folder connectivity")
        print("="*80)

        data_folders = [
            'astra_core/data/hypotheses',
            'astra_core/data/knowledge',
            'astra_core/data/memory',
            'astra_core/data/logs',
            'astra_core/data/state',
            'astra_core/data/autotunnel_viz',
        ]

        for folder in data_folders:
            folder_path = self.astra_root / folder
            if folder_path.exists():
                self.log_success(folder, f"Folder exists with {len(list(folder_path.iterdir()))} items")
            else:
                self.log_warning(folder, "Folder does not exist (may not be created yet)")

    def test_factory_functions(self):
        """Test factory functions that create components."""
        print("\n" + "="*80)
        print("Testing factory functions")
        print("="*80)

        try:
            import astra_core

            # Test create_unified_stan_system
            if hasattr(astra_core, 'create_unified_stan_system'):
                self.log_success("create_unified_stan_system", "Factory function available")
            else:
                self.log_warning("create_unified_stan_system", "Factory function not available")

            # Test create_bayesian_structure_learner
            if hasattr(astra_core, 'create_bayesian_structure_learner'):
                self.log_success("create_bayesian_structure_learner", "Factory function available")
            else:
                self.log_warning("create_bayesian_structure_learner", "Factory function not available")

        except Exception as e:
            self.log_error("factory_functions", f"Failed: {e}")

    def test_dependencies(self):
        """Test external dependencies."""
        print("\n" + "="*80)
        print("Testing external dependencies")
        print("="*80)

        dependencies = [
            ('numpy', 'np'),
            ('pandas', 'pd'),
            ('networkx', 'nx'),
            ('scipy', 'sp'),
        ]

        for module_name, alias in dependencies:
            try:
                importlib.import_module(module_name)
                self.log_success(module_name, f"External dependency available (as {alias})")
            except ImportError:
                self.log_warning(module_name, "External dependency not available")

    def run_all_tests(self) -> Tuple[int, int, int]:
        """Run all tests and return (errors, warnings, successes)."""
        print("\n" + "="*80)
        print("ASTRA CORE CONNECTIVITY TEST SUITE")
        print("="*80)
        print(f"Testing: {self.astra_core_path}")
        print(f"Python files: {sum(1 for _ in self.astra_core_path.rglob('*.py'))}")

        self.test_astra_core_import()
        self.test_main_exports()
        self.test_subdirectory_imports()
        self.test_cross_references()
        self.test_data_connectivity()
        self.test_factory_functions()
        self.test_dependencies()

        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"✅ Successes: {len(self.successes)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")

        if self.errors:
            print("\nERROR DETAILS:")
            for component, error in self.errors:
                print(f"  [{component}] {error}")

        return len(self.errors), len(self.warnings), len(self.successes)


def main():
    tester = ConnectivityTester()
    errors, warnings, successes = tester.run_all_tests()

    if errors > 0:
        print(f"\n❌ TEST FAILED: {errors} errors found")
        return 1
    else:
        print(f"\n✅ ALL TESTS PASSED: {successes} successes, {warnings} warnings")
        return 0


if __name__ == "__main__":
    sys.exit(main())
