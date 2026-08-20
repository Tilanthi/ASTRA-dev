"""IOAA-derived gate rules: narration precision, geometry narration, and the
pinned reference sheet.

Sources (arXiv 2510.05016): models lose most points to conceptual+geometric
errors; unreasonable significant figures earn half credit; a pinned reference
sheet eliminates constant drift. ASTRA's translation: hallucinated precision in
a narrated magnitude is a narration-data mismatch; geometric quantities are
never LLM-narrated unless the code measured them; proposer-authored code sees
pinned constants.

Run: python3 astra_core/tests/test_claim_gate_rules.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis.claim_gates import (  # noqa: E402
    precision_check, geometry_narration_check,
)
from astra_core.scientific_discovery.evolved_analysis import reference_sheet  # noqa: E402


def test_precision_three_decimals_pass():
    ok, reason = precision_check("galaxies with rho = 0.85 are redder", {})
    assert ok, reason


def test_precision_four_to_six_decimals_flagged_but_pass():
    ok, reason = precision_check("correlation of 0.851247 in SDSS", {})
    assert ok and "flag" in reason


def test_precision_seven_plus_decimals_rejected():
    ok, reason = precision_check("rho = 0.8512473 in SDSS", {})
    assert not ok and "reject" in reason


def test_precision_pvalue_three_sigfig_flagged():
    ok, reason = precision_check("significant at p = 1.23e-12", {})
    assert ok and "flag" in reason


def test_precision_pvalue_nine_sigfig_rejected():
    ok, reason = precision_check("significant at p = 1.23456789e-12", {})
    assert not ok and "reject" in reason


def test_precision_pvalue_normal_form_passes():
    ok, reason = precision_check("significant at p = 1e-12", {})
    assert ok


def test_geometry_number_present_in_summary_passes():
    m = {"summary": "sep = 12.5 arcsec, n = 400"}
    ok, reason = geometry_narration_check(
        "the pair is separated by 12.5 arcsec", m)
    assert ok, reason


def test_geometry_number_absent_from_summary_rejected():
    ok, reason = geometry_narration_check(
        "the pair is separated by 30 arcsec", {"summary": "sep = 12.5 arcsec"})
    assert not ok and "geometry" in reason


def test_no_geometry_claim_passes():
    ok, reason = geometry_narration_check(
        "redder galaxies have higher redshift", {"summary": "rho = 0.4"})
    assert ok


def test_reference_sheet_pins_core_constants():
    text = reference_sheet.REFERENCE_SHEET
    for token in ("c = ", "G = ", "k_B = ", "AU = ", "pc = ", "M_sun = "):
        assert token in text, token
    # every value is a literal number (unit annotation allowed after it) —
    # nothing resolved at runtime
    import re
    for line in text.strip().splitlines():
        if " = " in line and not line.startswith("#"):
            value = line.split(" = ")[1].split("(")[0].strip()
            assert re.match(r"^-?\d+\.?\d*(e-?\d+)?($|\s)", value), line


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
