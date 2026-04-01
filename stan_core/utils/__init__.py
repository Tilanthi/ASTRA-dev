"""
Utility functions for STAN-CORE V4.0
"""

from .date_utils import get_current_year, get_report_date, REPORT_DATE
from .helpers import progress_bar, timing

# Font-safe PDF utilities (always available)
from .pdf_utils import safe_text, create_safe_table, SafeParagraph

# PDF generation (NEW ASTRA PDF Generator - March 2026)
# Try new ASTRA PDF generator first, fall back to old one
_pdf_available = False
_pdf_generator_type = None

try:
    # New ASTRA PDF generator with improved formatting
    from .pdf_generator import (
        ASTRAPDFGenerator,
        ASTRAPDFStyles,
        MarkdownConverter,
        WrappedTableCell,
        create_pdf_from_markdown
    )
    _pdf_available = True
    _pdf_generator_type = 'new'

    # Export new classes
    PDFGenerator = ASTRAPDFGenerator
    PDFStyles = ASTRAPDFStyles
    MarkdownConverter = MarkdownConverter
    WrappedTableCell = WrappedTableCell
    create_pdf = create_pdf_from_markdown
    markdown_to_pdf = create_pdf_from_markdown

    # Old API compatibility (aliases)
    PDFFormat = None  # Not needed in new version
    TextAlign = None  # Not needed in new version
    PDFSection = None  # Not needed in new version
    PDFTable = None  # Not needed in new version
    PDFCodeBlock = None  # Not needed in new version

except ImportError:
    # Fall back to old PDF generator
    try:
        from .pdf_generator import (
            PDFGenerator,
            PDFFormat,
            TextAlign,
            PDFSection,
            PDFTable,
            PDFCodeBlock,
            create_pdf,
            markdown_to_pdf
        )
        _pdf_available = True
        _pdf_generator_type = 'old'

        # New API compatibility (placeholders)
        ASTRAPDFGenerator = PDFGenerator
        ASTRAPDFStyles = None
        MarkdownConverter = None
        WrappedTableCell = None

    except ImportError:
        # No PDF generator available
        PDFGenerator = None
        ASTRAPDFGenerator = None
        ASTRAPDFStyles = None
        MarkdownConverter = None
        WrappedTableCell = None
        PDFFormat = None
        TextAlign = None
        PDFSection = None
        PDFTable = None
        PDFCodeBlock = None
        create_pdf = None
        create_pdf_from_markdown = None
        markdown_to_pdf = None
        _pdf_available = False

__all__ = [
    "get_current_year",
    "get_report_date",
    "REPORT_DATE",
    "progress_bar",
    "timing",
    # Font-safe PDF utilities
    "safe_text",
    "create_safe_table",
    "SafeParagraph",
    # PDF generation (both old and new APIs)
    "PDFGenerator",
    "ASTRAPDFGenerator",
    "ASTRAPDFStyles",
    "MarkdownConverter",
    "WrappedTableCell",
    "PDFFormat",
    "TextAlign",
    "PDFSection",
    "PDFTable",
    "PDFCodeBlock",
    "create_pdf",
    "create_pdf_from_markdown",
    "markdown_to_pdf",
    "_pdf_available",
    "_pdf_generator_type",
]
