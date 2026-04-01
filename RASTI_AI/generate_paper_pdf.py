#!/usr/bin/env python3
"""
Generate PDF from ASTRA paper markdown
"""

import sys
import os

# Add parent directory to path to import stan_core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from stan_core.utils.pdf_generator import create_pdf_from_markdown

# Paths
markdown_file = os.path.join(os.path.dirname(__file__), 'draft_paper_complete_v9.md')
output_file = os.path.join(os.path.dirname(__file__), 'ASTRA_paper_complete_v9.pdf')

print(f"Converting {markdown_file} to PDF...")
print(f"Output: {output_file}")

# Generate PDF
try:
    result = create_pdf_from_markdown(
        markdown_file=markdown_file,
        output_file=output_file,
        title="ASTRA: A Physics-Aware AI System for Scientific Discovery in Astrophysics"
    )
    print(f"\n✓ PDF generated successfully: {result}")
except Exception as e:
    print(f"\n✗ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
