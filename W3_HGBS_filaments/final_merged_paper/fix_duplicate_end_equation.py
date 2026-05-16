#!/usr/bin/env python3
"""
Fix duplicate \end{equation} on line 680
"""

# Read the paper
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    lines = f.readlines()

# Fix the duplicate \end{equation} on line 680 (index 679)
if len(lines) > 680 and lines[679].strip() == '\\end{equation}':
    # Remove this duplicate line
    del lines[679]
    print("Removed duplicate \\end{equation} at line 680")

# Write the updated content
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.writelines(lines)

print("Fixed duplicate end equation")
