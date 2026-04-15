#!/usr/bin/env python3

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
Font-safe PDF generation utilities for reportlab.
Fixes black square issues caused by Unicode characters not in standard fonts.
"""

def safe_text(text):
    """
    Convert special Unicode characters to ASCII-safe alternatives for reportlab.
    This prevents black squares/splodges in PDFs when using standard fonts like Helvetica.

    Args:
        text: String with potential Unicode characters

    Returns:
        String with Unicode replaced by ASCII equivalents
    """
    replacements = {
        # Superscripts and subscripts
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
        '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁺': '+', '⁻': '-',
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5',
        '₆': '6', '₇': '7', '₈': '8', '₉': '9',

        # Common symbols
        '°': ' deg',
        '±': '+/-',
        '∓': '-/+',
        '×': 'x',
        '÷': '/',
        '−': '-',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '⇒': '=>',
        '⇐': '<=',

        # Greek letters (common in astronomy/physics)
        'Α': 'A', 'Β': 'B', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'E',
        'Ζ': 'Z', 'Η': 'H', 'Θ': 'Theta', 'Ι': 'I', 'Κ': 'K',
        'Λ': 'Lambda', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'Xi', 'Ο': 'O',
        'Π': 'Pi', 'Ρ': 'R', 'Σ': 'Sigma', 'Τ': 'T', 'Υ': 'U',
        'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega',
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
        'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa',
        'λ': 'lambda', 'μ': 'u', 'ν': 'nu', 'ξ': 'xi', 'ο': 'o',
        'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
        'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',

        # Special astronomy symbols
        '☉': 'Sun',
        '☊': 'asc',
        '☋': 'desc',
        '☌': 'conj',
        '☍': 'opp',

        # Math symbols
        '∞': 'inf',
        '∂': 'd',
        '∇': 'grad',
        'δ': 'delta',
        'Δ': 'Delta',
        '∑': 'sum',
        '∏': 'prod',
        '∫': 'integral',
        '√': 'sqrt',

        # Common units
        'μ': 'u',  # micro
        'Ω': 'Ohm',  # Ohm
        'Å': 'A',   # Angstrom

        # Other problematic characters
        '…': '...',
        '—': '--',
        '–': '-',
        ''': "'",
        ''': "'",
        '"': '"',
        '"': '"',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# Table styling helper with safe text handling
def create_safe_table(data, colWidths, style_kwargs=None):
    """
    Create a reportlab Table with safe text handling.

    Args:
        data: 2D list of table content
        colWidths: List of column widths
        style_kwargs: Optional dict of TableStyle keyword arguments

    Returns:
        reportlab Table object
    """
    from reportlab.platypus import Table
    from reportlab.lib import colors

    # Apply safe_text to all string cells
    safe_data = []
    for row in data:
        safe_row = [safe_text(str(cell)) if isinstance(cell, str) else cell for cell in row]
        safe_data.append(safe_row)

    # Default style
    default_style = {
        'FONTSIZE': 10,
        'ALIGN': 'LEFT',
        'GRID': True,
        'VALIGN': 'MIDDLE',
    }

    if style_kwargs:
        default_style.update(style_kwargs)

    return Table(safe_data, colWidths=colWidths)


# Paragraph wrapper with safe text
class SafeParagraph:
    """Wrapper for reportlab Paragraph that automatically handles Unicode characters."""

    def __init__(self, text, style):
        """
        Args:
            text: The text content (may contain Unicode)
            style: reportlab ParagraphStyle
        """
        from reportlab.platypus import Paragraph
        self.text = safe_text(text)
        self.style = style
        self._paragraph = Paragraph(self.text, style)

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped Paragraph."""
        return getattr(self._paragraph, name)

    def wrap(self, *args, **kwargs):
        return self._paragraph.wrap(*args, **kwargs)

    def draw(self, *args, **kwargs):
        return self._paragraph.draw(*args, **kwargs)


# Test function
def test_safe_text():
    """Test the safe_text function with common problematic characters."""
    test_cases = [
        ("μJy", "uJy"),
        ("rad m⁻²", "rad m-2"),
        ("10⁵ years", "105 years"),
        ("± 0.5", "+/- 0.5"),
        ("α, β, γ", "alpha, beta, gamma"),
        ("Δv = 5 km/s", "Deltav = 5 km/s"),  # Note: 'Δ' replaced directly, 'v' remains attached
        ("°C", " degC"),  # Note: space not auto-added
        ("→", "->"),
    ]

    print("Testing safe_text conversion:")
    all_passed = True
    for input_text, expected_output in test_cases:
        result = safe_text(input_text)
        passed = result == expected_output
        all_passed &= passed
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: '{input_text}' -> '{result}'")
        if not passed:
            print(f"         Expected: '{expected_output}'")

    return all_passed


if __name__ == "__main__":
    import sys
    success = test_safe_text()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
