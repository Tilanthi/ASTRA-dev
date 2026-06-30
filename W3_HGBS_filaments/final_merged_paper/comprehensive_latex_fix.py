#!/usr/bin/env python3
"""
Fix all LaTeX math mode errors in filament_spacing_streamlined_mnras.tex
"""
import re

with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    content = f.read()

# List of fixes to apply
fixes = [
    # Fix $\sim$NUMBER\% -> $\simNUMBER\%
    (r'\$\\sim\$([0-9.]+)\\%', r'$\\sim\1\\%'),

    # Fix $NUMBER--$NUMBER\% -> $NUMBER--NUMBER\%
    (r'\$([0-9.]+)--\$([0-9.]+)\\%', r'$\1--\2\\%'),

    # Fix $\sim$NUMBER at end of sentence/punctuation
    (r'\$\\sim\$([0-9.]+)([.,:\)])', r'$\\sim\1\2'),

    # Fix $NUMBER$--NUMBER\% pattern where the % is outside
    (r'\$([0-9.]+)\$--([0-9.]+)\\%', r'$\1--\2\\%'),
]

for pattern, replacement in fixes:
    content = re.sub(pattern, replacement, content)

with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(content)

print("Applied all LaTeX fixes")
