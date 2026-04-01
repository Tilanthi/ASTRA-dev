#!/usr/bin/env python3
"""
ASTRA Paper PDF Builder
Uses the new stan_core PDF generator module
"""

import os
import sys
import re

# Add stan_core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import reportlab units for default arguments
try:
    from reportlab.lib.units import inch
except ImportError:
    inch = 72  # 72 points = 1 inch

from stan_core.utils.pdf_generator import ASTRAPDFGenerator

def parse_markdown_paper(md_path, pdf):
    """Parse markdown paper and add to PDF"""

    with open(md_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    i = 0
    in_abstract = False
    in_list = False
    list_items = []

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            if in_list and list_items:
                pdf.add_bullet_list(list_items)
                list_items = []
                in_list = False
            i += 1
            continue

        # Main title
        if line.startswith('# ') and not line.startswith('##'):
            title = line[2:].strip()
            # Check for subtitle on next line
            subtitle = None
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('##') is False:
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('#'):
                    subtitle = next_line
                    i += 1
            pdf.add_title(title, subtitle)
            i += 1

        # Section headers
        elif line.startswith('##'):
            level = min(len(line) - len(line.lstrip('#')), 3)
            header_text = line.lstrip('#').strip()
            pdf.add_heading(header_text, level)
            i += 1

        # Abstract section
        elif line.lower() == '## abstract' or (i == 0 and 'abstract' in line.lower()):
            in_abstract = True
            pdf.add_heading('Abstract', 2)
            i += 1
            # Collect abstract content
            abstract_lines = []
            while i < len(lines):
                if lines[i].strip().startswith('##') or lines[i].strip().startswith('**Keywords**'):
                    break
                if lines[i].strip():
                    abstract_lines.append(lines[i].strip())
                i += 1
            if abstract_lines:
                abstract_text = ' '.join(abstract_lines)
                # Remove Keywords section
                if '**Keywords**' in abstract_text:
                    abstract_text = abstract_text.split('**Keywords**')[0].strip()
                pdf.add_abstract(abstract_text)
            # Check for keywords
            if i < len(lines) and '**Keywords**' in lines[i]:
                keywords_line = lines[i].split('**Keywords**')[-1].strip()
                keywords = [k.strip() for k in keywords_line.split(':')[-1].split(',')]
                pdf.add_keywords(keywords)
                i += 1
            continue

        # Keywords section
        elif line.startswith('**Keywords**') or line.startswith('**Keywords:'):
            keywords_text = line.split(':', 1)[-1].strip()
            keywords = [k.strip() for k in keywords_text.split(',')]
            pdf.add_keywords(keywords)
            i += 1

        # Figure references
        elif line.startswith('!['):
            match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match:
                caption = match.group(1)
                img_path = match.group(2)
                # Get caption from next line if available
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('*Figure'):
                    caption = lines[i + 1].strip().strip('*')
                    i += 1
                pdf.add_figure(img_path, caption)
            i += 1

        # Tables
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            headers = [h.strip() for h in line.split('|')[1:-1]]
            i += 2  # Skip separator line
            rows = []
            while i < len(lines) and '|' in lines[i] and not lines[i].strip().startswith(('#', '!', '-')):
                row = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                if row:
                    rows.append(row)
                i += 1
            if headers and rows:
                pdf.add_table(headers, rows)

        # Bullet lists
        elif line.startswith('- ') or line.startswith('* '):
            item = line[2:].strip()
            list_items.append(item)
            in_list = True
            i += 1

        # Numbered lists
        elif re.match(r'^\d+\.\s', line):
            item = re.sub(r'^\d+\.\s', '', line)
            list_items.append(item)
            in_list = True
            i += 1

        # Check for list end
        elif in_list and not (line.startswith(('-', '*', '  ')) or re.match(r'^\d+\.\s', line)):
            pdf.add_bullet_list(list_items)
            list_items = []
            in_list = False

        # Horizontal rule
        elif line.startswith('---'):
            pdf.add_spacer(0.1)
            i += 1

        # Regular paragraph
        else:
            if in_list and list_items:
                pdf.add_bullet_list(list_items)
                list_items = []
                in_list = False

            para_text = line
            # Collect multi-line paragraph
            while i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or next_line.startswith(('#', '-', '*', '|', '!', '##', '---')):
                    break
                # Check if it's a numbered list item
                if re.match(r'^\d+\.\s', next_line):
                    break
                para_text += ' ' + next_line
                i += 1

            pdf.add_paragraph(para_text)
            i += 1

    # Finalize any remaining list
    if in_list and list_items:
        pdf.add_bullet_list(list_items)


# Main execution
if __name__ == '__main__':
    print("="*70)
    print("ASTRA PAPER PDF BUILDER")
    print("Using stan_core.utils.pdf_generator")
    print("="*70)

    md_path = 'draft_paper_complete_v9.md'
    output_path = 'ASTRA_paper_complete.pdf'

    if not os.path.exists(md_path):
        print(f"Error: {md_path} not found")
        exit(1)

    print(f"\nReading: {md_path}")
    print(f"Output: {output_path}")

    # Create PDF generator
    pdf = ASTRAPDFGenerator(
        output_path=output_path,
        pagesize='A4',
        margin=0.75 * inch
    )

    # Parse and build
    parse_markdown_paper(md_path, pdf)

    # Build PDF
    print("\nBuilding PDF...")
    pdf.build()

    print("\n" + "="*70)
    print("PDF BUILD COMPLETE")
    print("="*70)
    print(f"\nOutput file: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")
