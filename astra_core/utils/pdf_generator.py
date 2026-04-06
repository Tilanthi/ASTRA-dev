"""
STAN_IX_ASTRO PDF Generator
==========================

Direct PDF generation module for creating PDF documents without intermediate HTML.
This module provides a simple interface for generating professional PDFs with
support for text, tables, code blocks, and structured sections.

Author: STAN_IX_ASTRO
Date: January 10, 2026
Updated: March 19, 2026 - Fixed table widths, font issues, figure placement
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import re
from datetime import datetime

# Conditional imports for PDF generation
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import inch, cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
        KeepTogether, Preformatted
    )
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available, PDF generation disabled")

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    from reportlab.lib.utils import ImageReader
    IMAGEREADER_AVAILABLE = True
except ImportError:
    IMAGEREADER_AVAILABLE = False


class PDFFormat(Enum):
    """PDF page formats."""
    A4 = "A4"
    LETTER = "Letter"
    LEGAL = "Legal"


class TextAlign(Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class PDFSection:
    """A section in the PDF document."""
    title: str
    content: str
    level: int = 1  # 1=h1, 2=h2, 3=h3, etc.
    page_break_before: bool = False


@dataclass
class PDFTable:
    """A table in the PDF document."""
    headers: List[str]
    rows: List[List[str]]
    title: Optional[str] = None
    column_widths: Optional[List[float]] = None


@dataclass
class PDFCodeBlock:
    """A code block in the PDF document."""
    code: str
    language: str = "Python"
    title: Optional[str] = None


class PDFGenerator:
    """
    Direct PDF generator for STAN_IX_ASTRO.

    Creates professional PDF documents with support for:
    - Multi-level headings
    - Paragraphs with various formatting
    - Tables with custom styling and automatic width calculation
    - Code blocks with syntax highlighting
    - Inline figure placement at correct positions
    - Font character compatibility
    """

    def __init__(
        self,
        filename: str,
        format: PDFFormat = PDFFormat.A4,
        title: str = "STAN_IX_ASTRO Document",
        author: str = "STAN_IX_ASTRO",
        subject: str = "",
        keywords: List[str] = None
    ):
        """
        Initialize the PDF generator.

        Args:
            filename: Output PDF filename
            format: Page format (A4, Letter, Legal)
            title: Document title (metadata)
            author: Document author (metadata)
            subject: Document subject (metadata)
            keywords: Document keywords (metadata)
        """
        self.filename = Path(filename)
        self.format = format
        self.title = title
        self.author = author
        self.subject = subject
        self.keywords = keywords or []

        # Document content
        self.sections: List[PDFSection] = []
        self.tables: List[PDFTable] = []
        self.code_blocks: List[PDFCodeBlock] = []
        self.toc_enabled = True
        self.embedded_figures = set()  # Track which figures have been embedded

        # Setup
        self._setup_document()

    def _setup_document(self):
        """Setup the PDF document based on available libraries."""
        if REPORTLAB_AVAILABLE:
            self._setup_reportlab()
        elif FPDF_AVAILABLE:
            self._setup_fpdf()
        else:
            raise ImportError(
                "No PDF generation library available. "
                "Install reportlab: pip install reportlab"
            )

    def _setup_reportlab(self):
        """Setup ReportLab-based document."""
        # Page size
        if self.format == PDFFormat.A4:
            pagesize = A4
        elif self.format == PDFFormat.LETTER:
            pagesize = letter
        else:
            pagesize = A4

        # Create document with proper margins
        self.doc = SimpleDocTemplate(
            str(self.filename),
            pagesize=pagesize,
            rightMargin=1.8*cm,
            leftMargin=1.8*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Set up metadata
        self.doc.title = self.title
        self.doc.author = self.author
        self.doc.subject = self.subject
        self.doc.keywords = ", ".join(self.keywords)

        # Document elements container
        self.elements = []

        # Available page width for content (A4 width - margins)
        self.available_width = pagesize[0] - (1.8*cm * 2)

        # Styles
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=HexColor('#1a1a2e'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Heading 1
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#1a1a2e'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))

        # Heading 2
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=13,
            textColor=HexColor('#2d3436'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Heading 3
        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=self.styles['Heading3'],
            fontSize=11,
            textColor=HexColor('#4a4a4a'),
            spaceAfter=6,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        # Body text - use Times-Roman for better readability
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=HexColor('#2d3436'),
            spaceAfter=8,
            leading=14,
            alignment=TA_JUSTIFY,
            fontName='Times-Roman'
        ))

        # Code block
        self.styles.add(ParagraphStyle(
            name='CustomCode',
            parent=self.styles['Code'],
            fontSize=8,
            textColor=HexColor('#dfe6e9'),
            backColor=HexColor('#2d3436'),
            spaceAfter=10,
            spaceBefore=10,
            leftIndent=8,
            fontName='Courier',
            leading=11
        ))

        # Figure caption
        self.styles.add(ParagraphStyle(
            name='FigureCaption',
            parent=self.styles['Normal'],
            fontSize=9,
            fontStyle='Italic',
            alignment=TA_CENTER,
            textColor=HexColor('#4a4a4a'),
            spaceAfter=15,
            fontName='Helvetica'
        ))

    def _setup_fpdf(self):
        """Setup FPDF-based document (fallback)."""
        self.pdf = FPDF()
        self.pdf.set_title(self.title)
        self.pdf.set_author(self.author)
        self.pdf.set_subject(self.subject)

        if self.format == PDFFormat.A4:
            self.pdf.add_page("A4")
        else:
            self.pdf.add_page("Letter")

    def _clean_text(self, text: str) -> str:
        """
        Clean text to fix font rendering issues while preserving Greek and mathematical symbols.

        CRITICAL: This method must ensure that:
        1. All text is renderable by reportlab's standard fonts
        2. No raw HTML tags appear in output (they will show as literal text)
        3. Unicode characters are either preserved (Greek/math) or converted to ASCII

        This method:
        - Preserves Greek characters (alpha, beta, gamma, etc.) - converted to names for compatibility
        - Preserves mathematical symbols - converted to ASCII equivalents
        - Replaces problematic Unicode characters with safe alternatives
        - Filters out non-ASCII characters that cause font issues
        - Does NOT handle HTML escaping (that's done in _process_inline_formatting)
        """
        # Comprehensive unicode replacements
        replacements = {
            # Punctuation
            '\u2014': '--',      # em dash
            '\u2013': '-',       # en dash
            '\u2018': "'",       # left single quote
            '\u2019': "'",       # right single quote
            '\u201c': '"',       # left double quote
            '\u201d': '"',       # right double quote
            '\u2026': '...',     # ellipsis
            '\u2022': '-',       # bullet
            '\u00b7': '-',       # middle dot

            # Symbols
            '\u2605': '*',       # Star
            '\u2606': '*',       # White star
            '\u2713': '[PASS]',  # Checkmark
            '\u2714': '[PASS]',  # Heavy checkmark
            '\u2717': '[FAIL]',  # Cross mark
            '\u2718': '[FAIL]',  # Heavy cross mark
            '\u25cf': '*',       # Black circle
            '\u25cb': 'o',       # White circle
            '\u25a0': '#',       # Black square
            '\u25a1': '#',       # White square
            '\u25e6': 'o',       # White bullet
            '\u25b2': '^',       # Triangle up
            '\u25bc': 'v',       # Triangle down

            # Math operators
            '\u2212': '-',       # Minus sign
            '\u00b1': '+/-',     # Plus-minus
            '\u00d7': 'x',       # Multiplication
            '\u00f7': '/',       # Division
            '\u2248': '~',       # Approximately
            '\u2264': '<=',      # Less than or equal
            '\u2265': '>=',      # Greater than or equal
            '\u2260': '!=',      # Not equal
            '\u221e': 'infinity', # Infinity
            '\u2202': 'partial',  # Partial derivative
            '\u2206': 'Delta',    # Delta
            '\u2207': 'nabla',    # Nabla

            # Greek letters - convert to names for font compatibility
            '\u03b1': 'alpha',
            '\u03b2': 'beta',
            '\u03b3': 'gamma',
            '\u03b4': 'delta',
            '\u03b5': 'epsilon',
            '\u03b6': 'zeta',
            '\u03b7': 'eta',
            '\u03b8': 'theta',
            '\u03b9': 'iota',
            '\u03ba': 'kappa',
            '\u03bb': 'lambda',
            '\u03bc': 'mu',
            '\u03bd': 'nu',
            '\u03be': 'xi',
            '\u03bf': 'omicron',
            '\u03c0': 'pi',
            '\u03c1': 'rho',
            '\u03c2': 'sigma',
            '\u03c3': 'sigma',
            '\u03c4': 'tau',
            '\u03c5': 'upsilon',
            '\u03c6': 'phi',
            '\u03c7': 'chi',
            '\u03c8': 'psi',
            '\u03c9': 'omega',
            '\u0391': 'Alpha',
            '\u0392': 'Beta',
            '\u0393': 'Gamma',
            '\u0394': 'Delta',
            '\u0395': 'Epsilon',
            '\u0396': 'Zeta',
            '\u0397': 'Eta',
            '\u0398': 'Theta',
            '\u0399': 'Iota',
            '\u039a': 'Kappa',
            '\u039b': 'Lambda',
            '\u039c': 'Mu',
            '\u039d': 'Nu',
            '\u039e': 'Xi',
            '\u039f': 'Omicron',
            '\u03a0': 'Pi',
            '\u03a1': 'Rho',
            '\u03a3': 'Sigma',
            '\u03a4': 'Tau',
            '\u03a5': 'Upsilon',
            '\u03a6': 'Phi',
            '\u03a7': 'Chi',
            '\u03a8': 'Psi',
            '\u03a9': 'Omega',

            # Arrows
            '\u2192': '->',
            '\u2190': '<-',
            '\u2194': '<->',
            '\u21d2': '=>',
            '\u21d0': '<=',

            # Special
            '\u00b0': ' degrees',
            '\u212b': 'Angstrom',
            '\u00a0': ' ',        # Non-breaking space
            '\u200b': '',         # Zero-width space
            '\u200c': '',         # Zero-width non-joiner
            '\u200d': '',         # Zero-width joiner
            '\u27c2': 'perpendicular',
            '\u2225': 'parallel',
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Remove any remaining non-ASCII characters that might cause font issues
        # Keep only ASCII (0-127) and common whitespace
        cleaned_text = ""
        for char in text:
            char_code = ord(char)
            if char_code < 128:
                cleaned_text += char
            elif char in [' ', '\n', '\t', '\r']:
                cleaned_text += char
            # All other non-ASCII characters are removed to prevent font issues

        return cleaned_text

    def add_figure(self, image_path: str, caption: str, width: float = 5.0):
        """Add a figure to the document."""
        if not REPORTLAB_AVAILABLE:
            return

        from reportlab.platypus import Image

        try:
            # Get image dimensions to scale properly
            if IMAGEREADER_AVAILABLE:
                img_reader = ImageReader(image_path)
                img_width, img_height = img_reader.getSize()

                # Max dimensions for A4 page (with margins)
                max_width = self.available_width
                max_height = 14 * cm  # Leave room for caption

                # Calculate scale factor
                width_scale = max_width / img_width
                height_scale = max_height / img_height
                scale = min(width_scale, height_scale)

                # Scaled dimensions
                display_width = img_width * scale
                display_height = img_height * scale

                img = Image(image_path, width=display_width, height=display_height, lazy=1)
            else:
                # Fallback to width-only scaling
                img = Image(image_path, width=min(width, 5.0)*inch, lazy=1)

            self.elements.append(Spacer(1, 0.2*cm))
            self.elements.append(img)

            # Clean caption text
            clean_caption = self._clean_text(caption)
            self.elements.append(Paragraph(clean_caption, self.styles['FigureCaption']))
            self.elements.append(Spacer(1, 0.2*cm))
        except Exception as e:
            self.elements.append(Paragraph(
                f"[Figure: {image_path} - {e}]",
                self.styles['CustomBody']
            ))

    def generate_from_markdown_with_figures(self, markdown_file: str, figures_dir: str = None):
        """Generate PDF from markdown with inline figure placement."""
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        self.figures_dir = figures_dir or Path(markdown_file).parent / "figures"
        self._parse_markdown_with_inline_figures(md_content)

    def _parse_markdown_with_inline_figures(self, md_content: str):
        """Parse markdown with inline figure placement."""
        lines = md_content.split('\n')
        i = 0

        # Track if we're in the references/tables section at the end
        in_end_section = False

        while i < len(lines):
            line = lines[i].rstrip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check if we've reached the end section (tables/figures list)
            if line.startswith('## ') and ('Table' in line or 'Figure' in line or 'References' in line):
                in_end_section = True

            # Skip content in the end section
            if in_end_section:
                i += 1
                continue

            # Check for inline figure references in the text
            # Matches "Figure N" or "Figure N:" patterns within text
            figure_match = re.search(r'Figure (\d+):?', line)
            if figure_match:
                fig_num = int(figure_match.group(1))
                if fig_num not in self.embedded_figures:
                    fig_caption = self._get_figure_caption(fig_num)
                    fig_path = self._get_figure_path(fig_num)
                    if fig_path:
                        self.add_figure(fig_path, f"Figure {fig_num}: {fig_caption}")
                        self.embedded_figures.add(fig_num)

                        # Remove the figure reference from the line
                        line = re.sub(r'Figure \d+:?\s*', '', line).strip()

            # Headings
            if line.startswith('# '):
                heading_text = self._clean_text(line[2:].replace('*', '').strip())
                self.add_section(heading_text, level=1)
            elif line.startswith('## '):
                heading_text = self._clean_text(line[3:].replace('*', '').strip())
                self.add_section(heading_text, level=2)
            elif line.startswith('### '):
                heading_text = self._clean_text(line[4:].replace('*', '').strip())
                self.add_section(heading_text, level=3)
            elif line.startswith('#### '):
                heading_text = self._clean_text(line[5:].replace('*', '').strip())
                self.add_section(heading_text, level=4)

            # Tables
            elif line.startswith('|') and i + 1 < len(lines) and lines[i+1].strip().startswith('|'):
                table_data = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    row = [cell.strip() for cell in lines[i].strip().split('|')[1:-1]]
                    if row:  # Only add non-empty rows
                        table_data.append(row)
                    i += 1

                if len(table_data) >= 1:
                    # Skip separator row if present (contains ---)
                    headers = table_data[0]
                    rows = [r for r in table_data[1:] if r and not all(c.startswith('---') for c in r)]
                    self.add_table_with_auto_width(headers, rows)
                continue

            # Regular text
            elif line and not line.startswith('**'):
                para_text = self._process_inline_formatting(line)
                if para_text:
                    self.add_paragraph(para_text)

            i += 1

    def _get_figure_caption(self, figure_number: int) -> str:
        """Get figure caption by number. Supports both V4.0 and legacy figures."""
        # V4.0 figure captions
        v40_captions = {
            1: "STAN-XI-ASTRO V4.0 System Architecture showing the seven-layer structure: Semantic Grounding, Metacognitive Systems, Multi-Mind Orchestration, Meta-Context Engine, Integration, Memory/Knowledge, and Physical Foundation layers",
            2: "V4.0 Revolutionary Capabilities: (A) Meta-Context Engine with temporal scales and cognitive frames, (B) Autocatalytic Self-Compiler cycle, (C) Cognitive-Relativity Navigator abstraction scale, (D) Multi-Mind Orchestration with seven specialized minds",
            3: "V95 Semantic Grounding Layer anti-hallucination system showing verification pipeline and performance metrics",
            4: "STAN-XI-ASTRO Domain Expansion: Original 9 domains (blue), V1.0 expansion +14 domains (green), V4.0 expansion +48 astrophysics domains (orange). Total: 75 domains, all verified operational (100% pass rate)"
        }
        # Legacy figure captions
        legacy_captions = {
            1: "System architecture showing the four-layer structure: Physical Foundation, Domain, Integration, and Inquiry layers",
            2: "Domain adaptation accuracy versus number of training examples for various source-target domain pairs",
            3: "Causal structure learning example for galaxy evolution variables showing the learned directed acyclic graph",
            4: "Physics curriculum learning stages and mastery progression through fifteen learning stages"
        }

        # Try V4.0 figures first, then fallback to legacy
        if figure_number in v40_captions:
            return v40_captions[figure_number]
        return legacy_captions.get(figure_number, "")

    def _get_figure_path(self, figure_number: int):
        """Get figure path by number. Supports both V4.0 and legacy figures."""
        if not hasattr(self, 'figures_dir'):
            return None
        figures_dir = Path(self.figures_dir)
        if not figures_dir.exists():
            return None

        # V4.0 figure files
        v40_figure_files = {
            1: "figure1_v40_architecture.png",
            2: "figure2_v40_capabilities.png",
            3: "figure3_semantic_grounding.png",
            4: "figure4_domain_expansion_updated.png"
        }
        # Legacy figure files
        legacy_figure_files = {
            1: "figure1_architecture.png",
            2: "figure2_adaptation.png",
            3: "figure3_causal.png",
            4: "figure4_curriculum.png"
        }

        # Try V4.0 figures first, then fallback to legacy
        if figure_number in v40_figure_files:
            path = figures_dir / v40_figure_files[figure_number]
            if path.exists():
                return str(path)

        if figure_number in legacy_figure_files:
            path = figures_dir / legacy_figure_files[figure_number]
            if path.exists():
                return str(path)

        return None

    def add_section(self, title: str, level: int = 1, page_break_before: bool = False):
        """Add a section heading to the document."""
        if page_break_before:
            self.elements.append(PageBreak())

        # Clean title text
        title = self._clean_text(title)

        if level == 1:
            self.elements.append(Paragraph(title, self.styles['CustomHeading1']))
        elif level == 2:
            self.elements.append(Paragraph(title, self.styles['CustomHeading2']))
        elif level == 3:
            self.elements.append(Paragraph(title, self.styles['CustomHeading3']))
        else:
            self.elements.append(Paragraph(title, self.styles['CustomBody']))

    def add_paragraph(self, text: str):
        """Add a paragraph to the document."""
        # Clean text to fix font issues
        text = self._clean_text(text)
        self.elements.append(Paragraph(text, self.styles['CustomBody']))

    def add_table_with_auto_width(self, headers: List[str], rows: List[List[str]], title: str = None):
        """
        Add a table with automatic width calculation and proper text wrapping.

        This method creates tables that:
        - Automatically calculate column widths to fit page
        - Wrap long text within cells
        - Handle multi-line content properly
        - Clean all text to avoid font rendering issues
        """
        # Clean all cell content
        cleaned_headers = [self._clean_text(h) for h in headers]
        cleaned_rows = []
        for row in rows:
            cleaned_rows.append([self._clean_text(cell) for cell in row])

        # Calculate column widths based on content length
        num_cols = len(cleaned_headers)
        available_width = self.available_width

        # Find maximum content length for each column
        col_widths = []
        for col_idx in range(num_cols):
            max_length = len(cleaned_headers[col_idx]) if col_idx < len(cleaned_headers) else 0

            for row in cleaned_rows:
                if col_idx < len(row):
                    # Split by words to find longest word
                    words = row[col_idx].split()
                    if words:
                        max_word_len = max(len(w) for w in words)
                        max_length = max(max_length, max_word_len)

            # Calculate width based on character count (assuming ~3pt per character)
            # Minimum width is at least 1cm for very short columns
            min_width = max(max_length * 2.5, 25)  # Points per character approximation

            # Limit maximum column width
            max_col_width = available_width * 0.6
            col_widths.append(min(min_width, max_col_width))

        # Adjust widths to fit available width
        total_width = sum(col_widths)

        if total_width > available_width:
            # Scale down proportionally
            scale = available_width / total_width
            col_widths = [w * scale for w in col_widths]
        elif total_width < available_width * 0.9:
            # Expand to fill available width (but leave some margin)
            extra_space = (available_width * 0.9 - total_width) / num_cols
            col_widths = [w + extra_space for w in col_widths]

        # Convert cells to Paragraphs for proper text wrapping
        table_data = []
        for col_idx, header in enumerate(cleaned_headers):
            table_data.append([Paragraph(header, ParagraphStyle(
                f'TableHeader_{col_idx}',
                parent=self.styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=7,
                alignment=TA_LEFT,
                leading=9
            ))])

        for row in cleaned_rows:
            table_row = []
            for col_idx, cell in enumerate(row):
                # Create paragraph with wrapping for each cell
                # Use default wordWrap handling
                cell_style = ParagraphStyle(
                    f'TableCell_{col_idx}',
                    parent=self.styles['Normal'],
                    fontName='Times-Roman',
                    fontSize=7,
                    alignment=TA_LEFT,
                    leading=9
                )
                table_row.append(Paragraph(cell, cell_style))
            table_data.append(table_row)

        # Create table with calculated widths
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.black),
            ('LEFTPADDING', (0, 1), (-1, -1), 3),
            ('RIGHTPADDING', (0, 1), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))

        # Add zebra striping for alternating rows
        for i in range(1, len(cleaned_rows) + 1):
            if i % 2 == 0:
                bg_color = colors.Color(0.95, 0.95, 0.95, 1)
                for j in range(num_cols):
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (j, i), (j, i), bg_color),
                    ]))

        if title:
            self.elements.append(Paragraph(f"<b>{self._clean_text(title)}</b>", self.styles['CustomBody']))

        self.elements.append(t)
        self.elements.append(Spacer(1, 0.3*cm))

    def add_table(self, headers: List[str], rows: List[List[str]], title: str = None):
        """Add a table to the document (deprecated - use add_table_with_auto_width)."""
        self.add_table_with_auto_width(headers, rows, title)

    def add_title_page(self, title: str, authors: List[str], affiliations: List[str], date: str):
        """Add a title page."""
        self.elements.append(Spacer(1, 2*cm))

        # Clean title
        title = self._clean_text(title)
        self.elements.append(Paragraph(title, self.styles['CustomTitle']))
        self.elements.append(Spacer(1, 0.8*cm))

        for author in authors:
            self.elements.append(Paragraph(author, ParagraphStyle(
                "AuthorStyle",
                parent=self.styles['Normal'],
                fontSize=11,
                alignment=TA_CENTER,
                fontName='Helvetica'
            )))

        self.elements.append(Spacer(1, 0.2*cm))

        for aff in affiliations:
            self.elements.append(Paragraph(aff, ParagraphStyle(
                "AffiliationStyle",
                parent=self.styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique'
            )))

        self.elements.append(Spacer(1, 0.4*cm))
        self.elements.append(Paragraph(date, ParagraphStyle(
            "DateStyle",
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )))

        self.elements.append(PageBreak())

    def add_abstract(self, abstract: str, keywords: List[str] = None):
        """Add an abstract section."""
        self.elements.append(Paragraph("<b>Abstract</b>", self.styles['CustomHeading1']))

        # Clean abstract text
        abstract = self._clean_text(abstract)
        self.elements.append(Paragraph(abstract, ParagraphStyle(
            "AbstractStyle",
            parent=self.styles['CustomBody'],
            fontName='Times-Italic',
            leftIndent=1*cm,
            rightIndent=1*cm,
            alignment=TA_JUSTIFY
        )))

        if keywords:
            kw_text = "<b>Keywords:</b> " + ", ".join(keywords)
            self.elements.append(Paragraph(kw_text, ParagraphStyle(
                "KeywordsStyle",
                parent=self.styles['CustomBody'],
                fontSize=9,
                fontName='Times-Italic'
            )))

        self.elements.append(Spacer(1, 0.4*cm))

    def _process_inline_formatting(self, text: str) -> str:
        """
        Process inline markdown formatting SAFELY.

        CRITICAL: This method must:
        1. Only convert **bold** to <b>bold</b> - NEVER convert single * to <i>
           because asterisks are used in mathematical expressions (e.g., dyn*cm^2)
        2. Escape all HTML special characters (<, >, &) except our converted tags
        3. Handle code backticks carefully

        This prevents issues like:
        - "dyn*cm^2" becoming "dyn<i>cm^2</i>" (broken formatting)
        - Raw HTML tags appearing in output
        - Unicode characters causing rendering errors
        """
        # Clean text first (handles unicode)
        text = self._clean_text(text)

        # Step 1: Protect our valid HTML tags by using placeholders
        # Bold: **text** -> <b>text</b>
        text = re.sub(r'\*\*([^*]+?)\*\*', r'%%BOLD_START%%\1%%BOLD_END%%', text)

        # Step 2: Escape ALL HTML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        # Step 3: Restore our protected tags
        text = text.replace('%%BOLD_START%%', '<b>')
        text = text.replace('%%BOLD_END%%', '</b>')

        # Step 4: Handle code backticks - escape any remaining special chars inside
        # We don't convert to <font> because it can cause parsing issues
        # Just leave code as-is with escaped HTML
        text = re.sub(r'`([^`]+?)`', r'<font face="Courier">\1</font>', text)

        # DO NOT convert single * to <i> - asterisks are used in math!
        # This was the source of the bug: "dyn*cm^2" became "dyn<i>cm^2</i>"

        return text

    def build(self):
        """Build and save the PDF."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab not available")
        self.doc.build(self.elements)
        return str(self.filename)


def generate_stan_paper_with_figures(
    markdown_file: str,
    output_pdf: str,
    title: str = "STAN Paper",
    authors: List[str] = None,
    abstract: str = None,
    keywords: List[str] = None,
    figures_dir: str = None
) -> str:
    """
    Generate STAN paper with embedded figures.

    Convenience function for creating publication-ready PDFs from markdown
    with embedded figures. Automatically handles figure scaling and placement.

    Args:
        markdown_file: Path to markdown source file
        output_pdf: Path for output PDF
        title: Paper title
        authors: List of author names
        abstract: Abstract text
        keywords: List of keywords
        figures_dir: Directory containing figure images (defaults to markdown_file.parent/figures)

    Returns:
        Path to generated PDF file
    """
    generator = PDFGenerator(
        filename=output_pdf,
        title=title,
        author=", ".join(authors or ["STAN Team"]),
        subject="Astronomical Research",
        keywords=keywords or []
    )

    generator.add_title_page(title, authors or ["STAN Team"], ["STAN-XI-ASTRO"], "March 2026")
    if abstract:
        generator.add_abstract(abstract, keywords)
    generator.generate_from_markdown_with_figures(markdown_file, figures_dir)
    return generator.build()


def create_publication_pdf_from_markdown(
    markdown_file: str,
    output_pdf: str,
    figures_dir: str = None,
    title: str = None,
    **metadata
) -> str:
    """
    Create a publication PDF from markdown.

    Simple interface for converting markdown papers to PDF with embedded figures.
    Detects figures marked with "Figure N" references in the text and embeds them inline.

    Args:
        markdown_file: Path to markdown source file
        output_pdf: Path for output PDF
        figures_dir: Directory containing figure images (defaults to markdown_file.parent/figures)
        title: Paper title (extracted from first # heading if not provided)
        **metadata: Additional metadata (author, subject, keywords)

    Returns:
        Path to generated PDF file
    """
    md_path = Path(markdown_file)
    if not title:
        # Extract title from first heading
        with open(md_path, 'r') as f:
            for line in f:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
        title = title or "Document"

    generator = PDFGenerator(
        filename=output_pdf,
        title=title,
        author=metadata.get('author', 'STAN-XI-ASTRO'),
        subject=metadata.get('subject', ''),
        keywords=metadata.get('keywords', [])
    )

    # Auto-detect figures directory if not specified
    if figures_dir is None:
        figures_dir = str(md_path.parent / "figures")

    generator.generate_from_markdown_with_figures(markdown_file, figures_dir)
    return generator.build()


__all__ = [
    'PDFGenerator',
    'PDFFormat',
    'TextAlign',
    'PDFSection',
    'PDFTable',
    'PDFCodeBlock',
    'generate_stan_paper_with_figures',
    'create_publication_pdf_from_markdown',
    'REPORTLAB_AVAILABLE',
    'FPDF_AVAILABLE'
]
