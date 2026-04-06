"""
Utility functions for STAN-CORE V4.0
"""

from .date_utils import get_current_year, get_report_date, REPORT_DATE
from .helpers import progress_bar, timing

# Font-safe PDF utilities (always available)
from .pdf_utils import safe_text, create_safe_table, SafeParagraph

# PDF generation (conditional import)
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
except ImportError:
    PDFGenerator = None
    PDFFormat = None
    TextAlign = None
    PDFSection = None
    PDFTable = None
    PDFCodeBlock = None
    create_pdf = None
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
    # PDF generation
    "PDFGenerator",
    "PDFFormat",
    "TextAlign",
    "PDFSection",
    "PDFTable",
    "PDFCodeBlock",
    "create_pdf",
    "markdown_to_pdf",
]
