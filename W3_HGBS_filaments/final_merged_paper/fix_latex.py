#!/usr/bin/env python3
import re

with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    lines = f.readlines()

fixed_lines = []
for line in lines:
    # Fix $\sim$NUMBER\% -> $\simNUMBER\%
    line = re.sub(r'\$\\sim\$([0-9.]+)\\%', r'$\sim\1\\%', line)
    # Fix $NUMBER--$NUMBER\% -> $NUMBER--NUMBER\%
    line = re.sub(r'\$([0-9.]+)--\$([0-9.]+)\\%', r'$\1--\2\\%', line)
    # Fix $\sim$NUMBER--NUMBER -> $\simNUMBER--NUMBER
    line = re.sub(r'\$\\sim\$([0-9.]+)--([0-9.]+)', r'$\sim\1--\2', line)
    fixed_lines.append(line)

with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed LaTeX errors")
