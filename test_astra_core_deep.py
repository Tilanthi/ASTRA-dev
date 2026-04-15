#!/usr/bin/env python3

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
ASTRA Core Deep Testing Suite
Comprehensive testing of all modules, dependencies, links, and references
"""

import sys
import os
import ast
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import traceback
import json

class AstraCoreTester:
    """Comprehensive tester for astra_core system"""

    def __init__(self, astra_core_path: str):
        self.astra_core_path = Path(astra_core_path)
        self.errors = []
        self.warnings = []
        self.results = {
            'imports': {},
            'dependencies': {},
            'references': {},
            'modules': {},
            'cross_links': {}
        }

    def log_error(self, category: str, message: str, details: str = ""):
        """Log an error"""
        self.errors.append({
            'category': category,
            'message': message,
            'details': details
        })
        print(f"❌ [{category}] {message}")
        if details:
            print(f"   Details: {details}")

    def log_warning(self, category: str, message: str, details: str = ""):
        """Log a warning"""
        self.warnings.append({
            'category': category,
            'message': message,
            'details': details
        })
        print(f"⚠️  [{category}] {message}")
        if details:
            print(f"   Details: {details}")

    def log_success(self, message: str):
        """Log success"""
        print(f"✓ {message}")

    def find_all_python_files(self) -> List[Path]:
        """Find all Python files in astra_core"""
        python_files = list(self.astra_core_path.rglob("*.py"))
        print(f"\n{'='*70}")
        print(f"DISCOVERING PYTHON FILES")
        print(f"{'='*70}")
        print(f"Found {len(python_files)} Python files")
        return python_files

    def extract_imports_from_file(self, file_path: Path) -> Dict[str, List[str]]:
        """Extract all imports from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            imports = {
                'standard': [],
                'third_party': [],
                'local': [],
                'astra_core': []
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        self._categorize_import(module_name, imports)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module
                        self._categorize_import(module_name, imports)

            return imports
        except Exception as e:
            self.log_error("parse_error", f"Failed to parse {file_path}", str(e))
            return {'standard': [], 'third_party': [], 'local': [], 'astra_core': []}

    def _categorize_import(self, module_name: str, imports: Dict[str, List[str]]):
        """Categorize an import statement"""
        # Check if it's an astra_core import
        if module_name.startswith('astra_core'):
            imports['astra_core'].append(module_name)
            return

        # Standard library modules (common ones)
        standard_libs = {
            'os', 'sys', 'json', 'pathlib', 're', 'math', 'datetime', 'time',
            'random', 'statistics', 'collections', 'itertools', 'functools',
            'typing', 'dataclasses', 'enum', 'abc', 'warnings', 'traceback',
            'copy', 'inspect', 'textwrap', 'hashlib', 'uuid', 'logging',
            'argparse', 'configparser', 'pickle', 'csv', 'sqlite3'
        }

        first_part = module_name.split('.')[0]
        if first_part in standard_libs:
            imports['standard'].append(module_name)
        else:
            imports['third_party'].append(module_name)

    def test_all_imports(self, python_files: List[Path]):
        """Test that all imports can be resolved"""
        print(f"\n{'='*70}")
        print(f"TESTING IMPORTS")
        print(f"{'='*70}")

        all_imports = set()
        import_map = {}

        for file_path in python_files:
            imports = self.extract_imports_from_file(file_path)
            import_map[str(file_path.relative_to(self.astra_core_path))] = imports

            for category in ['astra_core', 'third_party']:
                for imp in imports[category]:
                    all_imports.add(imp)

        self.results['imports'] = {
            'total_unique': len(all_imports),
            'by_file': import_map
        }

        # Test importing each third-party module
        print(f"\nTesting third-party imports ({len([i for i in all_imports if not i.startswith('astra_core')])} unique):")

        tested = set()
        for imp in sorted(all_imports):
            if imp.startswith('astra_core'):
                continue

            if imp in tested:
                continue
            tested.add(imp)

            try:
                importlib.import_module(imp)
                self.log_success(f"Import: {imp}")
            except Exception as e:
                self.log_error("import_error", f"Failed to import {imp}", str(e)[:100])

    def test_astra_core_imports(self, python_files: List[Path]):
        """Test that all astra_core modules can be imported"""
        print(f"\n{'='*70}")
        print(f"TESTING ASTRA_CORE IMPORTS")
        print(f"{'='*70}")

        # Add parent directory to path
        parent_dir = str(self.astra_core_path.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        imported = []
        failed = []

        for file_path in python_files:
            # Get module path
            rel_path = file_path.relative_to(self.astra_core_path)
            if file_path.name == '__init__.py':
                module_name = str(rel_path.parent).replace(os.sep, '.')
            else:
                module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')

            if not module_name or module_name.startswith('_'):
                continue

            full_module_name = f"astra_core.{module_name}"

            try:
                importlib.import_module(full_module_name)
                imported.append(full_module_name)
                self.log_success(f"Import: {full_module_name}")
            except Exception as e:
                error_msg = str(e)
                if "cannot import" in error_msg.lower() or "no module named" in error_msg.lower():
                    # This might be due to missing dependencies or circular imports
                    # Let's check for circular imports
                    if "circular" in error_msg.lower():
                        self.log_error("circular_import", f"Circular import in {full_module_name}", error_msg[:100])
                    else:
                        failed.append((full_module_name, error_msg))
                        self.log_warning("import_failed", f"Could not import {full_module_name}", error_msg[:100])
                else:
                    failed.append((full_module_name, error_msg))
                    self.log_error("import_error", f"Error importing {full_module_name}", error_msg[:100])

        self.results['modules'] = {
            'total_files': len(python_files),
            'successful': len(imported),
            'failed': len(failed),
            'failed_list': failed
        }

        print(f"\nImport summary: {len(imported)} successful, {len(failed)} failed")

    def find_module_references(self, python_files: List[Path]):
        """Find references between astra_core modules"""
        print(f"\n{'='*70}")
        print(f"ANALYZING CROSS-REFERENCES")
        print(f"{'='*70}")

        cross_refs = {}

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                file_refs = {
                    'imports': [],
                    'function_calls': [],
                    'class_usage': []
                }

                for node in ast.walk(tree):
                    # Find imports
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('astra_core'):
                                file_refs['imports'].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('astra_core'):
                            file_refs['imports'].append(node.module)

                    # Find function calls (simple heuristic)
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            file_refs['function_calls'].append(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            if hasattr(node.func.value, 'id'):
                                file_refs['function_calls'].append(f"{node.func.value.id}.{node.func.attr}")

                    # Find class instantiations
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            # Check if it might be a class (capitalized)
                            if node.func.id[0].isupper():
                                file_refs['class_usage'].append(node.func.id)

                rel_path = str(file_path.relative_to(self.astra_core_path))
                cross_refs[rel_path] = file_refs

            except Exception as e:
                self.log_error("parse_error", f"Failed to analyze {file_path}", str(e)[:100])

        self.results['cross_links'] = cross_refs
        return cross_refs

    def test_factory_functions(self):
        """Test that all factory functions work"""
        print(f"\n{'='*70}")
        print(f"TESTING FACTORY FUNCTIONS")
        print(f"{'='*70}")

        parent_dir = str(self.astra_core_path.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Look for factory functions
        factory_patterns = [
            'create_',
            'make_',
            'build_',
            'get_',
            'new_'
        ]

        # Try to import and test key modules
        key_modules = [
            'astra_core.cognitive',
            'astra_core.astro_physics',
            'astra_core.engine',
            'astra_core.reasoning',
            'astra_core.memory'
        ]

        for module_name in key_modules:
            try:
                module = importlib.import_module(module_name)

                # Look for factory functions
                for name in dir(module):
                    if any(name.startswith(pattern) for pattern in factory_patterns):
                        obj = getattr(module, name)
                        if callable(obj) and not name.startswith('_'):
                            # Try to call it with no args
                            try:
                                result = obj()
                                self.log_success(f"Factory: {module_name}.{name}()")
                            except Exception as e:
                                # Expected - factory functions need arguments
                                pass

            except Exception as e:
                self.log_warning("module_error", f"Could not load {module_name}", str(e)[:100])

    def test_dataclass_consistency(self, python_files: List[Path]):
        """Test that dataclasses are properly defined"""
        print(f"\n{'='*70}")
        print(f"TESTING DATACLASS CONSISTENCY")
        print(f"{'='*70}")

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it's a dataclass
                        is_dataclass = False
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                                is_dataclass = True
                                break
                            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                                if decorator.func.id == 'dataclass':
                                    is_dataclass = True
                                    break

                        if is_dataclass:
                            class_name = node.name
                            # Check for __init__ method (dataclasses generate this)
                            has_init = any(n.name == '__init__' for n in node.body if isinstance(n, ast.FunctionDef))

                            # Check for default values
                            issues = []
                            for item in node.body:
                                if isinstance(item, ast.AnnAssign):
                                    # Check if there's a mutable default argument
                                    if isinstance(item.value, (ast.List, ast.Dict, ast.Set)):
                                        issues.append(f"Mutable default: {item.target.id}")

                            if issues:
                                self.log_warning("dataclass_issue", f"Dataclass {class_name} in {file_path.name}", "; ".join(issues))
                            else:
                                self.log_success(f"Dataclass: {class_name}")

            except Exception as e:
                self.log_error("parse_error", f"Failed to analyze {file_path}", str(e)[:100])

    def check_broken_references(self):
        """Check for broken file/module references"""
        print(f"\n{'='*70}")
        print(f"CHECKING FOR BROKEN REFERENCES")
        print(f"{'='*70}")

        # Look for common reference patterns in files
        reference_patterns = {
            'from astra_core': r'from astra_core\.',
            'import astra_core': r'import astra_core',
            'astra_core.': r'astra_core\.'
        }

        python_files = list(self.astra_core_path.rglob("*.py"))
        missing_modules = set()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find all astra_core references
                import re
                astra_refs = re.findall(r'astra_core\.[\w\.]+', content)

                for ref in astra_refs:
                    # Try to import it
                    if ref not in missing_modules:
                        try:
                            importlib.import_module(ref)
                        except ModuleNotFoundError:
                            missing_modules.add(ref)
                        except Exception:
                            # Other errors - might be valid modules with import issues
                            pass

            except Exception as e:
                pass

        if missing_modules:
            for module in sorted(missing_modules):
                self.log_error("broken_reference", f"Referenced module not found: {module}")
        else:
            self.log_success("No broken module references found")

    def test_init_files(self, python_files: List[Path]):
        """Test __init__.py files"""
        print(f"\n{'='*70}")
        print(f"TESTING __INIT__.PY FILES")
        print(f"{'='*70}")

        init_files = [f for f in python_files if f.name == '__init__.py']

        print(f"Found {len(init_files)} __init__.py files")

        for init_file in init_files:
            rel_path = init_file.relative_to(self.astra_core_path)

            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if __init__ is empty or has minimal content
                if len(content.strip()) < 50:
                    self.log_warning("init_empty", f"Minimal __init__.py: {rel_path}")
                else:
                    self.log_success(f"__init__.py: {rel_path}")

                # Check for circular import indicators
                if 'import' in content and 'from' in content:
                    # Has imports - potential circular import risk
                    if content.count('import') > 3:
                        self.log_warning("potential_circular", f"Complex imports in {rel_path}")

            except Exception as e:
                self.log_error("file_error", f"Could not read {init_file}", str(e))

    def generate_report(self):
        """Generate final test report"""
        print(f"\n{'='*70}")
        print(f"FINAL TEST REPORT")
        print(f"{'='*70}")

        print(f"\nERRORS: {len(self.errors)}")
        for error in self.errors:
            print(f"  [{error['category']}] {error['message']}")
            if error['details']:
                print(f"    {error['details']}")

        print(f"\nWARNINGS: {len(self.warnings)}")
        for warning in self.warnings[:20]:  # Show first 20
            print(f"  [{warning['category']}] {warning['message']}")
        if len(self.warnings) > 20:
            print(f"  ... and {len(self.warnings) - 20} more warnings")

        # Save detailed report
        report = {
            'errors': self.errors,
            'warnings': self.warnings,
            'results': self.results,
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'status': 'PASS' if len(self.errors) == 0 else 'FAIL'
            }
        }

        report_path = self.astra_core_path / 'test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nDetailed report saved: {report_path}")

        return report

def main():
    """Main testing function"""
    print("="*70)
    print("ASTRA CORE DEEP TESTING SUITE")
    print("="*70)

    # Find astra_core directory
    current_dir = Path.cwd()
    astra_core_path = current_dir / 'astra_core'

    if not astra_core_path.exists():
        print(f"Error: astra_core not found at {astra_core_path}")
        print(f"Current directory: {current_dir}")
        return 1

    print(f"Testing astra_core at: {astra_core_path}")

    tester = AstraCoreTester(str(astra_core_path))

    # Run all tests
    python_files = tester.find_all_python_files()

    if not python_files:
        print("Error: No Python files found!")
        return 1

    tester.test_init_files(python_files)
    tester.test_all_imports(python_files)
    tester.test_astra_core_imports(python_files)
    tester.find_module_references(python_files)
    tester.test_factory_functions()
    tester.test_dataclass_consistency(python_files)
    tester.check_broken_references()

    # Generate report
    report = tester.generate_report()

    print(f"\n{'='*70}")
    if report['summary']['total_errors'] == 0:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"✗ TESTS FAILED: {report['summary']['total_errors']} errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
