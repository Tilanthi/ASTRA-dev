#!/usr/bin/env python3
"""
Fix broken cross-references and formatting issues
"""

import re

# Read the paper
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    lines = f.readlines()

# Fix 1: Add label to MHD SIMULATIONS section (line 463)
# Find the section and add label after it
for i, line in enumerate(lines):
    if i == 462 and '\\section{MHD SIMULATIONS}' in line:  # 0-indexed, so line 463 is index 462
        # Add label after the section
        lines[i] = line.rstrip() + '\n\\label{sec:mhd_simulations}\n'
        print(f"Fixed line 463: Added label to MHD SIMULATIONS section")
        break

# Fix 2: Replace sec:mhd_results with sec:mhd_simulations
content = ''.join(lines)
content = content.replace('sec:mhd_results}', 'sec:mhd_simulations}')

# Fix 3: Fix DLIT reference - replace sec:extended_validation with sec:additional_validation
content = content.replace('sec:extended_validation}', 'sec:additional_validation}')

# Fix 4: Fix the mixed prose with unicode characters in Section 5.1
# Replace "—" with proper LaTeX en-dash
content = content.replace('—', '--')

# Fix 5: Fix the feff notation
content = content.replace('f_{\\rm eff} ≈ 0.7', '$f_{\\rm eff} \\approx 0.7$')
content = content.replace('f_{\\rm eff} \\approx 0.7', '$f_{\\rm eff} \\approx 0.7$')

# Fix 6: Fix any raw text that should be in math mode
content = re.sub(r'f_{\\rm eff}\s+≈\s+0\.7', r'$f_{\\rm eff} \approx 0.7$', content)

# Fix 7: Check for other broken section references that might have "??"
# Look for patterns like "Section ??)" or similar
content = re.sub(r'Section\s+\?\?', r'Section~\\ref{FIXME}', content)

# Write the updated content
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(content)

print("Fixed cross-references and formatting issues")
