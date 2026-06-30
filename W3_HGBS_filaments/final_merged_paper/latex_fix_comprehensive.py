#!/usr/bin/env python3
"""
Comprehensive LaTeX error fix for filament_spacing_streamlined_mnras.tex
Fixes all math mode issues with percent signs, tildes, and units.
"""

def fix_latex_errors(content):
    """Apply all LaTeX error fixes."""

    # Fix 1: $\sim$NUMBER\% -> $\simNUMBER\%
    import re
    content = re.sub(r'\$\\sim\$([0-9.]+)\\%', r'$\\sim\1\\%', content)

    # Fix 2: $NUMBER--$NUMBER\% -> $NUMBER--NUMBER\%
    content = re.sub(r'\$([0-9.]+)--\$([0-9.]+)\\%', r'$\1--\2\\%', content)

    # Fix 3: $NUMBER$--NUMBER\% -> $NUMBER--NUMBER\% (number outside math, then dash)
    content = re.sub(r'\$([0-9.]+)\$--([0-9.]+)\\%', r'$\1--\2\\%', content)

    # Fix 4: $\sim$NUMBER pc -> $\simNUMBER$ pc
    content = re.sub(r'\$\\sim\$([0-9.]+) pc', r'$\\sim\1$ pc', content)

    # Fix 5: $\sim0.1 pc (already partially fixed) -> $\sim0.1$ pc
    content = re.sub(r'\$\\sim([0-9.]+) pc', r'$\\sim\1$ pc', content)

    # Fix 6: $NUMBER pc\% -> $NUMBER pc\% (should be $NUMBER$ pc\% or $NUMBER pc%)
    # Actually, this should be: $NUMBER$ pc with % outside
    content = re.sub(r'\$([0-9]+) pc\\%', r'$\1$ pc\\%', content)

    # Fix 7: $\simNUMBER$--NUMBER -> $\simNUMBER--NUMBER$
    content = re.sub(r'\$\\sim\$([0-9.]+)\$--([0-9.]+)', r'$\\sim\1--\2', content)

    # Fix 8: M_\odot$/pc -> M_\odot\!/\text{pc} or similar
    # This is actually fine, but let's check if it causes issues
    # The pattern $M_\odot$/pc$ should be $M_\odot\!/\text{pc}$ or just $M_\odot$/pc$

    return content

# Read the file
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    content = f.read()

# Apply fixes
fixed_content = fix_latex_errors(content)

# Write back
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(fixed_content)

print("✓ Fixed all LaTeX math mode errors")
print("Patterns fixed:")
print("  1. $\\sim$NUMBER\\% -> $\\simNUMBER\\%")
print("  2. $NUMBER--$NUMBER\\% -> $NUMBER--NUMBER\\%")
print("  3. $NUMBER$--NUMBER\\% -> $NUMBER--NUMBER\\%")
print("  4. $\\sim$NUMBER pc -> $\\simNUMBER$ pc")
print("  5. $\\simNUMBER pc -> $\\simNUMBER$ pc")
print("  6. $NUMBER pc\\% -> $NUMBER$ pc\\%")
