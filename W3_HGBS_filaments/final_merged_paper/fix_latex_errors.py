#!/usr/bin/env python3
"""
Fix LaTeX math mode errors with percent signs and tilde symbols.
"""

import re

# Read the file
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    content = f.read()

# Fix pattern 1: $\sim$NUMBER\% -> $\simNUMBER\%$
content = re.sub(r'\$\\sim\$([\d.]+)\\\\%', r'$\sim\1\\\\%', content)

# Fix pattern 2: $NUMBER--$NUMBER\% -> $NUMBER--NUMBER\%
content = re.sub(r'\$([\d.]+)--\$([\d.]+)\\\\%', r'$\1--\2\\\\%', content)

# Fix pattern 3: $\sim$NUMBER--NUMBER -> $\simNUMBER--NUMBER$
content = re.sub(r'\$\\sim\$([\d.]+)--([\d.]+)', r'$\sim\1--\2', content)

# Fix pattern 4: $\sim$NUMBER\% where the % is at end of parenthetical
content = re.sub(r'\$\\sim\$([\d.]+)\\\\%\\)', r'$\sim\1\\\\%)', content)

# Write the fixed file
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(content)

print("Fixed LaTeX math mode errors")
