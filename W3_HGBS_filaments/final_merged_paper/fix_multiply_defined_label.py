#!/usr/bin/env python3
"""
Fix multiply-defined label for fig:pfpi_beta_transition
"""

# Read the paper
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    content = f.read()

# The label is defined at lines 607 and 880
# The second occurrence should have a unique label since it's a different section
# We'll rename the second one (around line 880 in Supercritical section)

# Find the second occurrence (in Supercritical Filament Campaign section)
# and replace it with a unique label
old_label = r'\label{fig:pfpi_beta_transition}'
# We need to replace only the second occurrence after the Supercritical section starts

# Split by the Supercritical section marker
parts = content.split('\\subsection{Supercritical Filament Campaign}', 1)
if len(parts) == 2:
    # Replace the label in the second part (Supercritical section)
    parts[1] = parts[1].replace(old_label, '\\label{fig:pfpi_beta_transition_supercrit}', 1)
    content = parts[0] + '\\subsection{Supercritical Filament Campaign}' + parts[1]

# Write the updated content
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(content)

print("Fixed multiply-defined label")
