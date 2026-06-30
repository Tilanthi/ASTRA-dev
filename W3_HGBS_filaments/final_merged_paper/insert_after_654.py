#!/usr/bin/env python3
"""Insert content after line 654."""

with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    lines = f.readlines()

# Insert after line 654 (0-indexed, so after line 654)
insertion = """
\noindent\\textbf{Implications}. This $\\pm31$\\%$ systematic dominates the error budget and is comparable to the theory-observation discrepancy (factor of 1.4 in $\\lambda/W$). The RTC null result (overshoot by factors of 1.9--3.5) exceeds this uncertainty and is therefore robust. However, the rigid cylinder match ($\\lambda/W = 2.65 \\pm 0.57$) cannot be definitively confirmed without reducing this systematic.\\
"""

# Find line 654 and insert after it
for i, line in enumerate(lines):
    if i == 653:  # Line 654 (0-indexed)
        lines.insert(i+1, insertion)
        break

with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.writelines(lines)

print("✓ Added width normalisation implications")
