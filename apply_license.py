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
Apply Apache 2.0 license header to all Python source files in the ASTRA project.
"""

import os
import glob
from pathlib import Path

# Apache 2.0 license header for Python files
APACHE_HEADER = """# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
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

def has_license_header(filepath):
    """Check if a file already has the Apache license header."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_lines = ''.join([f.readline() for _ in range(15)])
            return 'Copyright 2024-2026 Glenn J. White' in first_lines
    except Exception:
        return False

def apply_license_header(filepath):
    """Apply the license header to a Python file."""
    if has_license_header(filepath):
        print(f"✓ Already has license: {filepath}")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file starts with shebang
        if content.startswith('#!'):
            lines = content.split('\n', 1)
            shebang = lines[0] + '\n'
            rest = lines[1] if len(lines) > 1 else ''
            new_content = shebang + '\n' + APACHE_HEADER + rest
        else:
            new_content = APACHE_HEADER + content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✓ Applied license: {filepath}")
    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}")

def main():
    """Apply license headers to all Python files in the project."""
    root_dir = Path(__file__).parent

    # Find all Python files
    python_files = []
    for pattern in ['**/*.py', '*.py']:
        python_files.extend(root_dir.glob(pattern))

    # Sort files for consistent processing
    python_files = sorted(set(python_files))

    print(f"Found {len(python_files)} Python files")
    print(f"Applying Apache 2.0 license header...\n")

    for filepath in python_files:
        # Skip this script itself
        if filepath.name == 'apply_license.py':
            continue
        apply_license_header(filepath)

    print(f"\nDone! Processed {len(python_files)} files.")

if __name__ == '__main__':
    main()
