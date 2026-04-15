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
ASTRA Core Syntax Error Fixer
Automatically fixes common syntax errors in Python files
"""

import ast
import re
from pathlib import Path

class SyntaxErrorFixer:
    """Fixes common syntax errors in Python files"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.fixes_applied = []

    def fix_file(self, file_path: Path) -> bool:
        """Try to fix syntax errors in a file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            original_content = content
            content = self._apply_fixes(content, str(file_path))

            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                return True
            return False

        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False

    def _apply_fixes(self, content: str, file_path: str) -> str:
        """Apply all fixes to content"""

        # Fix 1: Unclosed strings/brackets at end of file
        content = self._fix_truncated_file(content)

        # Fix 2: Unclosed triple-quoted strings
        content = self._fix_triple_quotes(content)

        # Fix 3: Missing function bodies
        content = self._fix_function_bodies(content)

        return content

    def _fix_truncated_file(self, content: str) -> str:
        """Fix files that end mid-statement"""

        lines = content.split('\n')

        # Check if file ends with an incomplete statement
        while lines:
            last_line = lines[-1].rstrip()

            # Check for incomplete patterns
            incomplete = [
                last_line.endswith(':'),
                last_line.endswith('(') and not last_line.endswith('()'),
                last_line.endswith('[') and not last_line.endswith('[]'),
                last_line.endswith('{') and not last_line.endswith('}'),
            ]

            if any(incomplete):
                # Add appropriate completion
                if last_line.endswith(':'):
                    lines.append('    pass')  # Add pass for incomplete block
                else:
                    lines.append('')  # Just add newline for other cases
            else:
                break

        return '\n'.join(lines)

    def _fix_triple_quotes(self, content: str) -> str:
        """Fix unclosed triple-quoted strings"""

        # Count triple quotes
        single_quotes = content.count("'''")
        double_quotes = content.count('"""')

        # If odd number of triple quotes, add closing
        if single_quotes % 2 == 1:
            content += "\n'''"
        elif double_quotes % 2 == 1:
            content += '\n"""'

        return content

    def _fix_function_bodies(self, content: str) -> str:
        """Fix missing function bodies"""

        lines = content.split('\n')
        result = []

        for i, line in enumerate(lines):
            result.append(line)

            # Check if this is an incomplete function/for/if definition
            stripped = line.strip()
            if (stripped.endswith(':') and
                i + 1 < len(lines) and
                not lines[i + 1].strip().startswith('#') and
                not lines[i + 1].strip()):

                # Check if next line is indented
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                if next_line and not next_line.startswith(' '):
                    # Need to add a body
                    indent = '    '  # 4 spaces
                    result.append(f'{indent}pass')

        return '\n'.join(result)

def fix_all_syntax_errors(astra_core_path: str):
    """Fix all syntax errors in astra_core"""

    print("="*70)
    print("FIXING SYNTAX ERRORS")
    print("="*70)

    fixer = SyntaxErrorFixer(astra_core_path)

    # Find files with syntax errors
    python_files = list(Path(astra_core_path).rglob("*.py"))

    errors_fixed = []
    still_errors = []

    for file_path in python_files:
        try:
            # Try to compile
            compile(str(file_path), 'string', 'exec')
        except SyntaxError as e:
            error_msg = str(e)
            print(f"\nFixing: {file_path.relative_to(astra_core_path)}")
            print(f"  Error: {error_msg[:100]}...")

            # Try to fix
            if fixer.fix_file(file_path):
                errors_fixed.append(str(file_path.relative_to(astra_core_path)))
                print(f"  ✓ Fixed")

                # Verify fix
                try:
                    compile(str(file_path), 'string', 'exec')
                except SyntaxError:
                    still_errors.append(str(file_path.relative_to(astra_core_path)))
                    print(f"  ⚠ Still has errors")
            else:
                still_errors.append(str(file_path.relative_to(astra_core_path)))

    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Errors fixed: {len(errors_fixed)}")
    print(f"Still has errors: {len(still_errors)}")

    if still_errors:
        print(f"\nFiles still with errors:")
        for f in still_errors[:10]:
            print(f"  - {f}")

    return errors_fixed, still_errors

if __name__ == "__main__":
    import sys
    sys.exit(0)
