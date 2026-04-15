# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
