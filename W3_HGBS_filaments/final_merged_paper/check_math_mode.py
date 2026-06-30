#!/usr/bin/env python3
"""
Check for math mode issues in specific lines.
"""
import re

with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    lines = f.readlines()

# Check line 153 specifically
line = lines[152]  # 0-indexed, so 152 = line 153
print(f"Line 153 length: {len(line)} chars")
print(f"Line 153: {line[:200]}...")

# Count math mode delimiters
dollar_count = line.count('$')
print(f"$ count: {dollar_count}")

# Find all $...$ patterns
math_modes = re.findall(r'\$[^$]+\$', line)
print(f"Math mode sections found: {len(math_modes)}")
for i, mm in enumerate(math_modes[:10]):
    print(f"  {i+1}. {mm[:80]}")

# Check if there's a pattern like $...$...$ (odd number)
if dollar_count % 2 == 1:
    print("ERROR: Odd number of $ signs - unclosed math mode!")
