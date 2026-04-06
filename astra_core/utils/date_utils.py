"""
Date utilities for STAN-CORE V4.0

Centralized date handling to ensure all content shows correct current date.
"""

from datetime import datetime

# Current date constants - updated for deployment
REPORT_DATE = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR = str(datetime.now().year)


def get_current_year() -> str:
    """Get current year as string."""
    return CURRENT_YEAR


def get_report_date() -> str:
    """Get formatted report date."""
    return REPORT_DATE
