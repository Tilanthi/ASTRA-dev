#!/usr/bin/env python3
"""
Generate PDF from ASTRA User Manual V8.0

This script converts the User Manual markdown file to a professionally formatted PDF.
"""

import sys
import re
from pathlib import Path

# Add astra_core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from astra_core.utils.pdf_generator import (
    ASTRAPDFGenerator,
    MarkdownConverter,
    ASTRAPDFStyles
)
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4


def parse_user_manual(md_file: str) -> dict:
    """
    Parse the user manual markdown file into structured data

    Returns:
        dict with: title, subtitle, sections, toc_entries
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # Extract title and metadata
    title = "ASTRA User Manual"
    subtitle = "Autonomous Scientific Discovery in Astrophysics"
    version = "8.0"
    date = "June 27, 2026"
    authors = "Glenn J. White, Open University and Rutherford Appleton Laboratory, England"

    # Parse content into sections
    sections = []
    current_section = None
    current_subsection = None
    current_content = []

    for line in lines:
        # Main heading (level 1)
        if line.startswith('# ') and not line.startswith('##'):
            if current_section:
                sections.append({
                    'level': 1,
                    'title': current_section,
                    'content': current_content
                })
            current_section = line[2:].strip()
            current_content = []

        # Subsection (level 2)
        elif line.startswith('## ') and not line.startswith('###'):
            if current_section:
                sections.append({
                    'level': 1,
                    'title': current_section,
                    'content': current_content
                })
            current_section = line[3:].strip()
            current_content = []

        # Sub-subsection (level 3)
        elif line.startswith('### '):
            if current_section:
                sections.append({
                    'level': 1,
                    'title': current_section,
                    'content': current_content
                })
            current_section = line[4:].strip()
            current_content = []

        # Code block
        elif line.strip().startswith('```'):
            current_content.append(line)

        # Empty line
        elif not line.strip():
            current_content.append('')

        # Regular content
        else:
            current_content.append(line)

    # Add last section
    if current_section:
        sections.append({
            'level': 1,
            'title': current_section,
            'content': current_content
        })

    return {
        'title': title,
        'subtitle': subtitle,
        'version': version,
        'date': date,
        'authors': authors,
        'sections': sections
    }


def generate_pdf(md_file: str, output_file: str):
    """Generate PDF from markdown file"""

    print(f"Reading markdown file: {md_file}")
    manual_data = parse_user_manual(md_file)

    print(f"Creating PDF generator: {output_file}")
    pdf = ASTRAPDFGenerator(
        output_file,
        pagesize=A4,
        margin=0.75 * inch
    )

    # Add title page
    pdf.add_title(manual_data['title'])
    pdf.add_paragraph(
        f"<b>Version:</b> {manual_data['version']} | "
        f"<b>Date:</b> {manual_data['date']}<br/>"
        f"<b>Authors:</b> {manual_data['authors']}"
    )
    pdf.add_paragraph(
        f"<b>Repository:</b> https://github.com/Tilanthi/ASTRA"
    )

    pdf.add_page_break()

    # Add table of contents
    pdf.add_heading("Table of Contents", level=1)
    pdf.add_paragraph(
        "1. Introduction<br/>"
        "2. System Architecture<br/>"
        "3. Installation and Setup<br/>"
        "4. Getting Started<br/>"
        "5. New in Version 8.0<br/>"
        "6. Core Capabilities Overview<br/>"
        "7. V4.0 Revolutionary Capabilities<br/>"
        "8. V5.0 Discovery Enhancement System<br/>"
        "9. V7.0 Autonomous Research Scientist<br/>"
        "10. Automatic Startup Discovery<br/>"
        "11. Use Case Examples<br/>"
        "12. Advanced Features<br/>"
        "13. Domain Modules<br/>"
        "14. API Reference<br/>"
        "15. Best Practices<br/>"
        "16. Troubleshooting<br/>"
        "17. Performance Optimization<br/>"
        "18. Development Workflow<br/>"
        "19. Testing and Verification<br/>"
        "20. Appendices"
    )
    pdf.add_page_break()

    # Now process the actual markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    in_code_block = False
    code_content = []
    code_language = ""
    in_list = False
    list_items = []
    list_type = None  # 'bullet' or 'numbered'
    list_number = 1

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip title and metadata (already added)
        if i < 20:  # Skip header
            i += 1
            continue

        # Code block handling
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_content)
                pdf.add_paragraph(code_text, style='Code')
                code_content = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
                code_language = line.strip()[3:]
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # Empty line
        if not line.strip():
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False
                list_number = 1
            i += 1
            continue

        # Main heading (level 1)
        if line.startswith('# ') and not line.startswith('##'):
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False
            heading_text = line[2:].strip()
            pdf.add_heading(heading_text, level=1)
            i += 1

        # Subsection (level 2)
        elif line.startswith('## ') and not line.startswith('###'):
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False
            heading_text = line[3:].strip()
            pdf.add_heading(heading_text, level=2)
            i += 1

        # Sub-subsection (level 3)
        elif line.startswith('### '):
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False
            heading_text = line[4:].strip()
            pdf.add_heading(heading_text, level=3)
            i += 1

        # Bullet list item
        elif re.match(r'^\s*[-*]\s+', line):
            if not in_list:
                in_list = True
                list_type = 'bullet'
            list_items.append(re.sub(r'^\s*[-*]\s+', '', line))
            i += 1

        # Numbered list item
        elif re.match(r'^\s*\d+\.\s+', line):
            if not in_list:
                in_list = True
                list_type = 'numbered'
            list_items.append(re.sub(r'^\s*\d+\.\s+', '', line))
            i += 1

        # Table
        elif '|' in line and i + 1 < len(lines) and '|---' in lines[i + 1]:
            # Close any open list
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False

            # Parse table
            headers = [h.strip() for h in line.split('|')[1:-1]]
            i += 2  # Skip separator
            rows = []
            while i < len(lines) and '|' in lines[i]:
                row = [c.strip() for c in lines[i].split('|')[1:-1]]
                if row:
                    rows.append(row)
                i += 1
            if rows:
                pdf.add_table(headers, rows)

        # Horizontal rule
        elif line.strip() == '---':
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False
            pdf.add_horizontal_rule()
            i += 1

        # Image
        elif line.strip().startswith('!['):
            # Close any open list
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False

            match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match:
                caption = match.group(1)
                img_path = match.group(2)
                pdf.add_figure(img_path, caption)
            i += 1

        # Regular paragraph
        else:
            # Close any open list first
            if in_list and list_items:
                if list_type == 'bullet':
                    pdf.add_bullet_list(list_items)
                else:
                    pdf.add_numbered_list(list_items)
                list_items = []
                in_list = False

            # Collect paragraph lines
            para_text = line
            i += 1
            while i < len(lines):
                next_line = lines[i].rstrip()
                # Stop if empty or special marker
                if not next_line.strip():
                    break
                if next_line.startswith('#') or next_line.startswith('```') or \
                   next_line.startswith('---') or next_line.strip().startswith('![') or \
                   ('|' in next_line and i + 1 < len(lines) and '|---' in lines[i + 1]):
                    break
                if re.match(r'^\s*[-*]\s+', next_line) or re.match(r'^\s*\d+\.\s+', next_line):
                    break
                para_text += ' ' + next_line
                i += 1

            if para_text.strip():
                pdf.add_paragraph(para_text)

    # Build PDF
    print("Building PDF...")
    pdf.build()
    print(f"PDF generated successfully: {output_file}")

    return output_file


if __name__ == '__main__':
    # Paths
    md_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/User_Manual/User_Manual_V8.md'
    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/User_Manual/ASTRA_User_Manual_V8.0.pdf'

    # Generate PDF
    try:
        generate_pdf(md_file, output_file)
        print("\n✓ PDF generation complete!")
        print(f"  Output: {output_file}")
    except Exception as e:
        print(f"\n✗ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
