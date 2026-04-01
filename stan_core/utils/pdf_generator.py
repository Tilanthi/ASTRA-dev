#!/usr/bin/env python3
"""
ASTRA PDF Generator Module
============================

A robust PDF generator for scientific papers that properly handles:
- Markdown to HTML conversion
- HTML tag rendering (bold, italic, superscript, etc.)
- Table text wrapping without overflow
- Unicode to ASCII conversion
- Complex document structure

Author: ASTRA Project
Version: 1.0
Date: April 2026
"""

import re
import os
from typing import List, Tuple, Optional, Dict
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
        PageBreak, KeepTogether
    )
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        from reportlab.platypus.flowables import Flowable
    except ImportError:
        Flowable = None
    from PIL import Image as PILImage
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Define fallback constants
    inch = 72
    cm = 28.35
    A4 = (595.27, 841.89)
    letter = (612, 792)
    print("WARNING: reportlab not available. PDF generation disabled.")


class ASTRAPDFStyles:
    """Pre-defined styles for ASTRA documents"""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            return

        self._styles = getSampleStyleSheet()
        self._custom_styles = {}
        self._build_styles()

    def _build_styles(self):
        """Build custom styles"""

        # Title style
        self._custom_styles['Title'] = ParagraphStyle(
            'ASTRATitle',
            parent=self._styles['Title'],
            fontSize=18,
            textColor=colors.darkblue,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=22
        )

        # Subtitle style
        self._custom_styles['Subtitle'] = ParagraphStyle(
            'ASTRASubtitle',
            parent=self._styles['Normal'],
            fontSize=12,
            textColor=colors.darkgray,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique',
            leading=16
        )

        # Heading 1 style
        self._custom_styles['Heading1'] = ParagraphStyle(
            'ASTRAHeading1',
            parent=self._styles['Heading1'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            leading=18,
            keepWithNext=True
        )

        # Heading 2 style
        self._custom_styles['Heading2'] = ParagraphStyle(
            'ASTRAHeading2',
            parent=self._styles['Heading2'],
            fontSize=12,
            textColor=colors.darkblue,
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold',
            leading=15,
            keepWithNext=True
        )

        # Heading 3 style
        self._custom_styles['Heading3'] = ParagraphStyle(
            'ASTRAHeading3',
            parent=self._styles['Heading3'],
            fontSize=11,
            textColor=colors.darkblue,
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            leading=14
        )

        # Body text style
        self._custom_styles['Body'] = ParagraphStyle(
            'ASTRABody',
            parent=self._styles['BodyText'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            leading=13
        )

        # Abstract style
        self._custom_styles['Abstract'] = ParagraphStyle(
            'ASTRAAbstract',
            parent=self._styles['Normal'],
            fontSize=9,
            spaceAfter=20,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman',
            leftIndent=20,
            rightIndent=20,
            leading=12
        )

        # Caption style
        self._custom_styles['Caption'] = ParagraphStyle(
            'ASTRACaption',
            parent=self._styles['Normal'],
            fontSize=8,
            spaceAfter=12,
            spaceBefore=6,
            alignment=TA_JUSTIFY,
            fontName='Times-Italic',
            leading=10
        )

        # Table cell style
        self._custom_styles['TableCell'] = ParagraphStyle(
            'ASTRATableCell',
            parent=self._styles['Normal'],
            fontSize=8,
            fontName='Times-Roman',
            leading=10,
            wordWrap='CJK'
        )

        # Code style
        self._custom_styles['Code'] = ParagraphStyle(
            'ASTRACode',
            parent=self._styles['Code'],
            fontSize=8,
            spaceAfter=8,
            fontName='Courier',
            leftIndent=20,
            leading=10
        )

        # Reference style
        self._custom_styles['Reference'] = ParagraphStyle(
            'ASTRAReference',
            parent=self._styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Times-Roman',
            leftIndent=20,
            leading=11
        )

        # Keyword style
        self._custom_styles['Keyword'] = ParagraphStyle(
            'ASTRAKeyword',
            parent=self._styles['Normal'],
            fontSize=9,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Times-Italic',
            leading=11
        )

    def get_style(self, name: str) -> ParagraphStyle:
        """Get a style by name"""
        if name in self._custom_styles:
            return self._custom_styles[name]
        return self._styles.get(name, self._styles['Normal'])


class MarkdownConverter:
    """Converts Markdown to reportlab-compatible HTML"""

    # Unicode to ASCII mappings
    UNICODE_MAP = {
        '±': '+/-',
        '×': ' x ',
        '÷': ' / ',
        '²': '²',
        '³': '³',
        '⁴': '⁴',
        '⁵': '⁵',
        '⁶': '⁶',
        '⁷': '⁷',
        '⁸': '⁸',
        '⁹': '⁹',
        '⁰': '⁰',
        '¹': '¹',
        '⁻': '-',
        'α': 'alpha',
        'β': 'beta',
        'γ': 'gamma',
        'δ': 'delta',
        'ε': 'epsilon',
        'θ': 'theta',
        'κ': 'kappa',
        'λ': 'lambda',
        'μ': 'mu',
        'π': 'pi',
        'σ': 'sigma',
        'τ': 'tau',
        'φ': 'phi',
        'ω': 'omega',
        '°': ' degrees',
        '′': "'",
        '″': '"',
        '—': '&mdash;',
        '–': '&ndash;',
        '≤': '<=',
        '≥': '>=',
        '≈': 'approximately',
        '≠': '!=',
        '∝': 'proportional to',
        '√': 'sqrt',
        '∞': 'infinity',
        '∑': 'sum',
        '∫': 'integral',
        '∂': 'partial',
        'Δ': 'Delta',
        'Σ': 'Sigma',
        'Π': 'Pi',
        'Ω': 'Omega',
        'Γ': 'Gamma',
        'Λ': 'Lambda',
        'Ψ': 'Psi',
        'Φ': 'Phi',
    }

    # Greek letters that should be italicized
    GREEK_ITALIC = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta',
                     'kappa', 'lambda', 'mu', 'pi', 'sigma', 'tau', 'phi', 'omega']

    def __init__(self):
        self._patterns = [
            # Superscript patterns: ^text^ or ^number
            (r'\^([0-9a-zA-Z+-]+)\^', r'<super>\1</super>'),

            # Subscript patterns: _text_ (but not __ for bold)
            (r'(?<!_)_(?!_)([a-zA-Z0-9+-]+)(?!_)_', r'<sub>\1</sub>'),

            # Bold: **text** or __text__
            (r'\*\*([^*]+?)\*\*', r'<b>\1</b>'),
            (r'__([^_]+?)__', r'<b>\1</b>'),

            # Italic: *text* (but not ** or within superscript/subscript)
            (r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>'),

            # Strikethrough: ~~text~~
            (r'~~([^~]+?)~~', r'<strike>\1</strike>'),

            # Underline: __text__ handled by bold, use u-text-u for underline
            (r'~([^~]+)~', r'<u>\1</u>'),
        ]

    def convert(self, text: str, preserve_tags: bool = True) -> str:
        """
        Convert markdown text to reportlab-compatible HTML

        Args:
            text: The markdown text to convert
            preserve_tags: If True, preserve existing HTML tags

        Returns:
            HTML string compatible with reportlab Paragraph
        """
        if not isinstance(text, str):
            text = str(text)

        # First, escape HTML special characters IF we're not preserving tags
        if not preserve_tags:
            text = self._escape_html(text)

        # Convert unicode characters to HTML/ASCII
        text = self._convert_unicode(text)

        # Make Greek letters italic
        for greek in self.GREEK_ITALIC:
            text = re.sub(r'\b' + greek + r'\b', f'<i>{greek}</i>', text)

        # Apply markdown patterns
        for pattern, replacement in self._patterns:
            text = re.sub(pattern, replacement, text)

        # Clean up any double escapes
        text = text.replace('&amp;amp;', '&amp;')

        return text

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        # Only escape if not already part of a tag
        parts = []
        in_tag = False
        i = 0

        while i < len(text):
            if text[i] == '<':
                # Check if this is a valid tag
                if i + 1 < len(text) and text[i+1] in '/bisuBISU':
                    in_tag = True
                    parts.append('<')
                else:
                    parts.append('&lt;')
            elif text[i] == '>':
                if in_tag:
                    parts.append('>')
                    in_tag = False
                else:
                    parts.append('&gt;')
            elif text[i] == '&':
                # Check if already an entity
                if i + 1 < len(text) and text[i+1] in '#aA':
                    # Already an entity, preserve
                    parts.append('&')
                else:
                    parts.append('&amp;')
            else:
                parts.append(text[i])
            i += 1

        return ''.join(parts)

    def _convert_unicode(self, text: str) -> str:
        """Convert unicode characters to ASCII equivalents"""
        for uni, ascii_equiv in self.UNICODE_MAP.items():
            text = text.replace(uni, ascii_equiv)
        return text


class WrappedTableCell:
    """Helper class for creating properly wrapped table cells"""

    def __init__(self, text: str, style: ParagraphStyle, max_width: float):
        """
        Create a wrapped table cell

        Args:
            text: The text content
            style: The Paragraph style to use
            max_width: Maximum width for the cell
        """
        self.text = text
        self.style = style
        self.max_width = max_width

    def wrap_text(self, text: str) -> str:
        """
        Wrap text to fit within max_width

        Args:
            text: The text to wrap

        Returns:
            Wrapped text with <br/> tags for line breaks
        """
        # First, convert any markdown
        converter = MarkdownConverter()
        html_text = converter.convert(text, preserve_tags=True)

        # Split the text into lines that fit
        wrapped_lines = simpleSplit(
            html_text,
            self.style.fontName,
            self.style.fontSize,
            self.max_width - 6  # Account for padding
        )

        # Join with <br/> tags
        if len(wrapped_lines) > 1:
            # Limit to 3 lines maximum
            wrapped_lines = wrapped_lines[:3]
            if len(wrapped_lines) == 3 and wrapped_lines[2] != html_text:
                wrapped_lines[2] = wrapped_lines[2][:max(0, len(wrapped_lines[2])-3)] + '...'

            return '<br/>'.join(wrapped_lines)

        return wrapped_lines[0] if wrapped_lines else ''


class ASTRAPDFGenerator:
    """
    Main PDF generator for ASTRA scientific papers

    Features:
    - Markdown to HTML conversion
    - Proper table text wrapping
    - Figure embedding with captions
    - Automatic page numbering
    - Table of contents generation
    """

    # Page size mappings
    PAGE_SIZES = {
        'A4': A4,
        'LETTER': letter,
        'LETTER': letter,
    }

    def __init__(self,
                 output_path: str,
                 pagesize='A4',
                 margin: float = 0.75 * inch):
        """
        Initialize the PDF generator

        Args:
            output_path: Path to output PDF file
            pagesize: Reportlab pagesize (default: 'A4')
            margin: Page margin in points
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation")

        # Handle string pagesize
        if isinstance(pagesize, str):
            pagesize = self.PAGE_SIZES.get(pagesize.upper(), A4)

        self.output_path = output_path
        self.pagesize = pagesize
        self.margin = margin
        self.content_width = pagesize[0] - 2 * margin

        self.styles = ASTRAPDFStyles()
        self.converter = MarkdownConverter()
        self.story = []

        # Document template
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=pagesize,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin
        )

    def add_title(self, text: str, subtitle: str = None):
        """Add document title and optional subtitle"""
        converted = self.converter.convert(text)
        self.story.append(Paragraph(converted, self.styles.get_style('Title')))

        if subtitle:
            sub_conv = self.converter.convert(subtitle)
            self.story.append(Paragraph(sub_conv, self.styles.get_style('Subtitle')))

        self.story.append(Spacer(1, 0.2*inch))

    def add_heading(self, text: str, level: int = 1):
        """
        Add a section heading

        Args:
            text: Heading text
            level: Heading level (1-3)
        """
        converted = self.converter.convert(text)
        style_name = f'Heading{min(level, 3)}'
        self.story.append(Paragraph(converted, self.styles.get_style(style_name)))

    def add_paragraph(self, text: str, style: str = 'Body'):
        """
        Add a paragraph

        Args:
            text: Paragraph text (can contain markdown)
            style: Style name to use
        """
        converted = self.converter.convert(text)
        self.story.append(Paragraph(converted, self.styles.get_style(style)))

    def add_abstract(self, text: str):
        """Add an abstract paragraph"""
        converted = self.converter.convert(text)
        self.story.append(Paragraph(converted, self.styles.get_style('Abstract')))

    def add_keywords(self, keywords: List[str]):
        """Add keywords list"""
        text = '<b>Keywords:</b> ' + ', '.join(keywords)
        converted = self.converter.convert(text)
        self.story.append(Paragraph(converted, self.styles.get_style('Keyword')))

    def add_figure(self,
                  image_path: str,
                  caption: str = None,
                  max_height: float = 4 * inch,
                  max_width: float = None):
        """
        Add a figure with caption

        Args:
            image_path: Path to image file
            caption: Figure caption text
            max_height: Maximum height for figure
            max_width: Maximum width (default: content_width)
        """
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}")
            return

        try:
            # Get image dimensions
            img = PILImage.open(image_path)
            img_width, img_height = img.size

            # Calculate display size
            if max_width is None:
                max_width = self.content_width

            scale_w = max_width / img_width
            scale_h = max_height / img_height
            scale = min(scale_w, scale_h)

            display_width = img_width * scale
            display_height = img_height * scale

            # Add image
            img_obj = Image(image_path, width=display_width, height=display_height)
            img_obj.hAlign = TA_CENTER
            self.story.append(img_obj)

            # Add caption
            if caption:
                cap_conv = self.converter.convert(caption)
                self.story.append(Paragraph(cap_conv, self.styles.get_style('Caption')))

            self.story.append(Spacer(1, 0.1*inch))

        except Exception as e:
            print(f"Error adding image {image_path}: {e}")

    def add_table(self,
                  headers: List[str],
                  rows: List[List[str]],
                  col_widths: List[float] = None,
                  repeat_header: bool = True):
        """
        Add a table with proper text wrapping

        Args:
            headers: Column headers
            rows: Table data rows
            col_widths: Optional column widths
            repeat_header: Whether to repeat header on new pages
        """
        if not headers or not rows:
            return

        n_cols = len(headers)
        if col_widths is None:
            col_width = self.content_width / n_cols
            col_widths = [col_width] * n_cols

        # Convert cells to Paragraph objects for proper HTML rendering
        cell_style = self.styles.get_style('TableCell')
        header_style = ParagraphStyle(
            'ASTRATableHeader',
            parent=cell_style,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke
        )

        wrapped_data = []

        # Wrap headers as Paragraphs
        wrapped_headers = []
        for h in headers:
            converted = self.converter.convert(h)
            wrapped_headers.append(Paragraph(converted, header_style))
        wrapped_data.append(wrapped_headers)

        # Wrap rows as Paragraphs
        for row in rows:
            wrapped_row = []
            for cell in row:
                converted = self.converter.convert(str(cell))
                wrapped_row.append(Paragraph(converted, cell_style))
            wrapped_data.append(wrapped_row)

        # Create table
        table = Table(wrapped_data, colWidths=col_widths, repeatRows=1 if repeat_header else 0)

        # Build style
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]

        # Add alternating row colors
        for i in range(1, len(wrapped_data)):
            row_color = colors.white if i % 2 == 0 else colors.lightgrey
            style_commands.append(('BACKGROUND', (0, i), (-1, i), row_color))

        table.setStyle(TableStyle(style_commands))
        self.story.append(table)
        self.story.append(Spacer(1, 0.1*inch))

    def add_bullet_list(self, items: List[str], style: str = 'Body'):
        """Add a bullet list"""
        for item in items:
            converted = self.converter.convert(f"&#8226; {item}")
            self.story.append(Paragraph(converted, self.styles.get_style(style)))
        self.story.append(Spacer(1, 0.05*inch))

    def add_numbered_list(self, items: List[str], style: str = 'Body'):
        """Add a numbered list"""
        for i, item in enumerate(items, 1):
            converted = self.converter.convert(f"{i}. {item}")
            self.story.append(Paragraph(converted, self.styles.get_style(style)))
        self.story.append(Spacer(1, 0.05*inch))

    def add_reference(self, text: str):
        """Add a bibliography reference"""
        converted = self.converter.convert(text)
        self.story.append(Paragraph(converted, self.styles.get_style('Reference')))

    def add_page_break(self):
        """Add a page break"""
        self.story.append(PageBreak())

    def add_spacer(self, height: float = 0.2 * inch):
        """Add vertical space"""
        self.story.append(Spacer(1, height))

    def add_horizontal_rule(self):
        """Add a horizontal rule"""
        self.story.append(Paragraph('<hr/>', self.styles.get_style('Body')))

    def build(self):
        """Build the PDF document"""
        self.doc.build(self.story)
        print(f"PDF built successfully: {self.output_path}")
        return self.output_path


# Convenience function for quick PDF generation
def create_pdf_from_markdown(markdown_file: str,
                            output_file: str = None,
                            title: str = None) -> str:
    """
    Create a PDF from a markdown file

    Args:
        markdown_file: Path to markdown file
        output_file: Path to output PDF (optional)
        title: Document title (optional)

    Returns:
        Path to generated PDF file
    """
    if output_file is None:
        output_file = Path(markdown_file).stem + '.pdf'

    # Read markdown file
    with open(markdown_file, 'r') as f:
        content = f.read()

    # Create PDF generator
    pdf = ASTRAPDFGenerator(output_file)

    # Simple parser for basic markdown structure
    lines = content.split('\n')
    i = 0
    in_list = False
    list_items = []

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            if in_list and list_items:
                pdf.add_bullet_list(list_items)
                list_items = []
                in_list = False
            i += 1
            continue

        # Title
        if line.startswith('# ') and not line.startswith('##'):
            if title is None:
                title = line[2:].strip()
            pdf.add_title(title)
            i += 1

        # Headings
        elif line.startswith('##'):
            level = len(line) - len(line.lstrip('#'))
            pdf.add_heading(line.lstrip('#').strip(), level)
            i += 1

        # Images
        elif line.startswith('!['):
            match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match:
                caption = match.group(1)
                img_path = match.group(2)
                pdf.add_figure(img_path, caption)
            i += 1

        # Lists
        elif line.startswith('- ') or line.startswith('* '):
            list_items.append(line[2:].strip())
            in_list = True
            i += 1

        # Tables
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            headers = [h.strip() for h in line.split('|')[1:-1]]
            i += 2  # Skip separator
            rows = []
            while i < len(lines) and '|' in lines[i]:
                row = [c.strip() for c in lines[i].split('|')[1:-1]]
                if row:
                    rows.append(row)
                i += 1
            pdf.add_table(headers, rows)

        # Regular paragraph
        else:
            if in_list and list_items:
                pdf.add_bullet_list(list_items)
                list_items = []
                in_list = False

            para_text = line
            while i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].strip().startswith(('#', '-', '*', '|', '!', '##')):
                para_text += ' ' + lines[i + 1].strip()
                i += 1
            pdf.add_paragraph(para_text)
            i += 1

    # Build PDF
    return pdf.build()


if __name__ == '__main__':
    # Test the PDF generator
    print("ASTRA PDF Generator Module")
    print("="*50)
    print("Available classes:")
    print("  - ASTRAPDFGenerator: Main PDF generator")
    print("  - ASTRAPDFStyles: Style management")
    print("  - MarkdownConverter: Markdown to HTML")
    print("  - WrappedTableCell: Table cell wrapping")
    print()
    print("Usage:")
    print("  from stan_core.utils.pdf_generator import ASTRAPDFGenerator")
    print("  pdf = ASTRAPDFGenerator('output.pdf')")
    print("  pdf.add_title('My Paper')")
    print("  pdf.add_paragraph('This is **bold** and *italic* text.')")
    print("  pdf.build()")
