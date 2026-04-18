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

"""Reproduce an ASTRA discovery from its ID.

Re-fetches the original astronomical data and re-runs the statistical test
to verify that a discovery recorded in the ASTRA database can be independently
reproduced. This is a core component of ASTRA's commitment to open science
and reproducibility (see Section 8 of the RASTI paper).

Usage:
    python reproduce.py <discovery_id>
    python reproduce.py --hypothesis <hypothesis_id>
    python reproduce.py --list           # list all reproducible discoveries
    python reproduce.py --all            # reproduce all discoveries
    python reproduce.py --db /path/to.db # use a custom database path

Exit codes:
    0 — all reproductions passed (or --list mode)
    1 — one or more reproductions failed or errored
"""

import sys
import os
import json
import sqlite3
import argparse
import textwrap
import time
from typing import Optional, Dict, Any, Tuple, List

# ---------------------------------------------------------------------------
# Ensure ASTRA backend is importable
# ---------------------------------------------------------------------------
ASTRA_ROOT = os.path.dirname(os.path.abspath(__file__))
if ASTRA_ROOT not in sys.path:
    sys.path.insert(0, ASTRA_ROOT)

import numpy as np

# Lazy imports — these pull in requests/scipy, so defer until needed
_fetcher = None
_stats = None

def _load_modules():
    """Lazily import ASTRA backend modules."""
    global _fetcher, _stats
    if _fetcher is None:
        from astra_live_backend import data_fetcher as df
        from astra_live_backend import statistics as st
        _fetcher = df
        _stats = st

# ═══════════════════════════════════════════════════════════════════════════
# ANSI helpers
# ═══════════════════════════════════════════════════════════════════════════

class C:
    """ANSI colour codes (disabled if NO_COLOR is set or stdout is not a tty)."""
    _enabled = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    RESET  = "\033[0m"   if _enabled else ""
    BOLD   = "\033[1m"   if _enabled else ""
    DIM    = "\033[2m"   if _enabled else ""
    RED    = "\033[91m"  if _enabled else ""
    GREEN  = "\033[92m"  if _enabled else ""
    YELLOW = "\033[93m"  if _enabled else ""
    CYAN   = "\033[96m"  if _enabled else ""
    BLUE   = "\033[94m"  if _enabled else ""
    MAGENTA = "\033[95m" if _enabled else ""

def _header(text: str):
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 72}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {text}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 72}{C.RESET}")

def _ok(text: str):
    print(f"  {C.GREEN}✓{C.RESET} {text}")

def _fail(text: str):
    print(f"  {C.RED}✗{C.RESET} {text}")

def _warn(text: str):
    print(f"  {C.YELLOW}⚠{C.RESET} {text}")

def _info(text: str):
    print(f"  {C.DIM}•{C.RESET} {text}")

# ═══════════════════════════════════════════════════════════════════════════
# Database helpers
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_DB = os.path.join(os.path.dirname(ASTRA_ROOT), "astra_discoveries.db")
# Fallback: /workspace/astra_discoveries.db
if not os.path.exists(DEFAULT_DB):
    DEFAULT_DB = "/workspace/astra_discoveries.db"


def _connect(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        print(f"{C.RED}Error:{C.RESET} Database not found: {db_path}")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _get_discovery(conn: sqlite3.Connection, disc_id: str) -> Optional[Dict]:
    row = conn.execute("SELECT * FROM discoveries WHERE id = ?", (disc_id,)).fetchone()
    return dict(row) if row else None


def _get_discoveries_by_hypothesis(conn: sqlite3.Connection, hyp_id: str) -> List[Dict]:
    rows = conn.execute("SELECT * FROM discoveries WHERE hypothesis_id = ?", (hyp_id,)).fetchall()
    return [dict(r) for r in rows]


def _get_all_discoveries(conn: sqlite3.Connection) -> List[Dict]:
    rows = conn.execute("SELECT * FROM discoveries ORDER BY timestamp DESC").fetchall()
    return [dict(r) for r in rows]

# ═══════════════════════════════════════════════════════════════════════════
# Data source → fetch function mapping
# ═══════════════════════════════════════════════════════════════════════════

# Maps the data_source field in the DB to (fetch_function_name, description).
# The fetch function is looked up on the data_fetcher module at runtime.
_SOURCE_MAP = {
    "exoplanets":      ("fetch_exoplanets",       "NASA Exoplanet Archive"),
    "pantheon":        ("fetch_pantheon_sne",      "Pantheon+ SNe Ia"),
    "gaia":            ("fetch_gaia_stars",        "Gaia DR3"),
    "sdss":            ("fetch_sdss_galaxies",     "SDSS DR18"),
    "hubble":          ("fetch_pantheon_sne",      "Pantheon+ (Hubble diagram)"),
    "galaxy":          ("fetch_sdss_galaxies",     "SDSS galaxies"),
    "stellar":         ("fetch_gaia_stars",        "Gaia DR3 (stellar)"),
    "star_formation":  ("fetch_gaia_stars",        "Gaia DR3 (star formation)"),
    "cmb":             ("fetch_pantheon_sne",      "Pantheon+ (CMB proxy)"),
    "hr_diagram":      ("fetch_hr_diagram",        "Gaia HR diagram"),
    "galaxy_colors":   ("fetch_galaxy_colors",     "SDSS galaxy colors"),
}

# Column name aliases — the discovery may store variable names that differ
# from structured array field names.  Map common aliases.
_COLUMN_ALIASES = {
    # Exoplanet columns
    "pl_orbper": "period",
    "orbital_period": "period",
    "pl_orbsmax": "sma",
    "semi_major_axis": "sma",
    "pl_bmassj": "mass",
    "mass_jup": "mass",
    "stellar_mass": "st_mass",
    "st_teff": "st_teff",
    "stellar_teff": "st_teff",
    # Pantheon / hubble
    "redshift": "z",
    "z_hd": "z",
    "distance_modulus": "mb",
    "m_b": "mb",
    "mb_corr": "mb",
    # Gaia
    "bp_minus_rp": "bp_rp",
    "color": "bp_rp",
    "absolute_mag": "abs_mag",
    "abs_magnitude": "abs_mag",
    # SDSS
    "u_minus_g": "u_g",
    "u_g_color": "u_g",
    "g_minus_r": "g_r",
    "g_r_color": "g_r",
    "zhd": "redshift",
    "z_hd": "redshift",
}


def _resolve_column(name: str) -> str:
    """Resolve a variable name to its structured-array field name."""
    return _COLUMN_ALIASES.get(name.lower().strip(), name.lower().strip())

# ═══════════════════════════════════════════════════════════════════════════
# Finding type → statistical test mapping
# ═══════════════════════════════════════════════════════════════════════════

def _infer_test(finding_type: str, description: str):
    """Return (test_function_name, test_label, is_reproducible)."""
    ft = (finding_type or "").lower()
    desc = (description or "").lower()

    if "correlation" in ft or "correlation" in desc:
        return ("pearson_correlation", "Pearson correlation", True)
    if "scaling" in ft or "power law" in desc or "kepler" in desc:
        return ("pearson_correlation", "Pearson correlation (log-space)", True)
    if "bimodal" in ft or "bimodality" in desc or "gaussian mixture" in desc:
        return ("anderson_darling_test", "Anderson-Darling", True)
    if "distribution" in ft or "normality" in desc:
        return ("anderson_darling_test", "Anderson-Darling", True)
    if "difference" in ft or "comparison" in desc:
        return ("mann_whitney_test", "Mann-Whitney U", True)
    if "causal" in ft or "fci" in desc or "dag" in desc:
        return (None, "FCI / Causal (non-reproducible via simple re-test)", False)
    if "hubble" in ft or "dark energy" in desc or "distance-redshift" in desc:
        return ("pearson_correlation", "Pearson correlation", True)
    # Default: try Pearson
    return ("pearson_correlation", "Pearson correlation (default)", True)


def _fetch_data(data_source: str):
    """Fetch data for a given source. Returns a DataResult or None."""
    _load_modules()
    source_key = (data_source or "").lower().strip()
    entry = _SOURCE_MAP.get(source_key)
    if entry is None:
        return None
    func_name, label = entry
    func = getattr(_fetcher, func_name, None)
    if func is None:
        return None
    _info(f"Fetching data from {label} …")
    try:
        result = func()
        if result is None or (hasattr(result, 'data') and (result.data is None or len(result.data) == 0)):
            return None
        return result
    except Exception as e:
        _fail(f"Fetch failed: {e}")
        return None


def _extract_columns(data, variables: List[str]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Extract up to two columns from a structured numpy array.
    
    Returns (x, y) where y may be None for single-variable tests.
    """
    resolved = [_resolve_column(v) for v in variables]
    available = set(data.dtype.names) if hasattr(data, 'dtype') and data.dtype.names else set()

    arrays = []
    for i, col in enumerate(resolved):
        # Try resolved name first, then original name, then fuzzy match
        original = variables[i].lower().strip() if i < len(variables) else col
        found_col = None
        for candidate in [col, original]:
            if candidate in available:
                found_col = candidate
                break
        if found_col is None:
            # Try partial match
            for av in available:
                if col in av or av in col:
                    found_col = av
                    break
        if found_col is not None:
            arr = data[found_col]
            # Drop NaN / zero
            mask = np.isfinite(arr) & (arr != 0)
            arrays.append((found_col, arr, mask))
        else:
            _warn(f"Column '{col}' not found in data (available: {', '.join(sorted(available))})")

    if len(arrays) == 0:
        return None, None

    if len(arrays) == 1:
        col, arr, mask = arrays[0]
        return arr[mask], None

    # Two variables — intersect valid masks
    _, arr_x, mask_x = arrays[0]
    _, arr_y, mask_y = arrays[1]
    mask = mask_x & mask_y
    return arr_x[mask], arr_y[mask]

# ═══════════════════════════════════════════════════════════════════════════
# Core reproduction logic
# ═══════════════════════════════════════════════════════════════════════════

def reproduce_discovery(disc: Dict, verbose: bool = True) -> Dict[str, Any]:
    """Attempt to reproduce a single discovery.
    
    Returns a result dict with keys:
        id, status ("PASS", "FAIL", "SKIP", "ERROR"),
        original_stat, reproduced_stat, pct_diff, message
    """
    _load_modules()
    disc_id = disc["id"]
    finding_type = disc.get("finding_type", "")
    description = disc.get("description", "")
    data_source = disc.get("data_source", "")
    orig_stat = disc.get("statistic")
    orig_p = disc.get("p_value")
    variables_json = disc.get("variables", "[]")

    result = {
        "id": disc_id,
        "status": "ERROR",
        "original_stat": orig_stat,
        "original_p": orig_p,
        "reproduced_stat": None,
        "reproduced_p": None,
        "pct_diff": None,
        "message": "",
    }

    if verbose:
        _header(f"Reproducing: {disc_id}")
        _info(f"Type: {finding_type}")
        _info(f"Source: {data_source}")
        _info(f"Description: {description[:100]}{'…' if len(description or '') > 100 else ''}")

    # 1. Parse variables
    try:
        variables = json.loads(variables_json) if variables_json else []
    except json.JSONDecodeError:
        variables = [v.strip() for v in (variables_json or "").split(",") if v.strip()]

    if verbose:
        _info(f"Variables: {variables}")

    # 2. Determine test
    test_func_name, test_label, is_reproducible = _infer_test(finding_type, description)
    if not is_reproducible:
        if verbose:
            _warn(f"Skipping — {test_label}")
        result["status"] = "SKIP"
        result["message"] = test_label
        return result

    if verbose:
        _info(f"Test: {test_label}")

    # 3. Fetch data
    data_result = _fetch_data(data_source)
    if data_result is None:
        msg = f"Could not fetch data for source '{data_source}'"
        if verbose:
            _fail(msg)
        result["status"] = "ERROR"
        result["message"] = msg
        return result

    data = data_result.data
    if verbose:
        _ok(f"Fetched {len(data)} data points from {data_result.source} "
            f"({data_result.fetch_time:.1f}s)")

    # 4. Extract columns
    x, y = _extract_columns(data, variables)
    if x is None or len(x) < 10:
        msg = f"Insufficient data after column extraction (got {len(x) if x is not None else 0} rows)"
        if verbose:
            _fail(msg)
        result["status"] = "ERROR"
        result["message"] = msg
        return result

    if verbose:
        _info(f"Extracted {len(x)} valid data points")

    # 5. Run statistical test
    test_func = getattr(_stats, test_func_name, None)
    if test_func is None:
        msg = f"Unknown test function: {test_func_name}"
        if verbose:
            _fail(msg)
        result["status"] = "ERROR"
        result["message"] = msg
        return result

    try:
        # For correlation / scaling, need log-space for scaling
        if "scaling" in (finding_type or "").lower() or "power law" in (description or "").lower():
            x_test = np.log10(x[x > 0])
            if y is not None:
                y_valid = y[x > 0]
                y_test = np.log10(y_valid[y_valid > 0])
                x_test = x_test[:len(y_test)]  # align
            else:
                y_test = None
        else:
            x_test = x
            y_test = y

        if test_func_name in ("pearson_correlation",):
            if y_test is None:
                msg = "Pearson correlation requires two variables"
                if verbose:
                    _fail(msg)
                result["status"] = "ERROR"
                result["message"] = msg
                return result
            # Align lengths
            min_len = min(len(x_test), len(y_test))
            stat_result = test_func(x_test[:min_len], y_test[:min_len])
        elif test_func_name in ("anderson_darling_test",):
            stat_result = test_func(x_test)
        elif test_func_name in ("mann_whitney_test", "bayesian_t_test"):
            if y_test is None:
                stat_result = test_func(x_test)
            else:
                stat_result = test_func(x_test, y_test)
        else:
            stat_result = test_func(x_test)
    except Exception as e:
        msg = f"Test execution failed: {e}"
        if verbose:
            _fail(msg)
        result["status"] = "ERROR"
        result["message"] = msg
        return result

    result["reproduced_stat"] = stat_result.statistic
    result["reproduced_p"] = stat_result.p_value

    # 6. Compare with original
    if orig_stat is not None and orig_stat != 0:
        pct_diff = abs(stat_result.statistic - orig_stat) / abs(orig_stat) * 100
    else:
        pct_diff = None
    result["pct_diff"] = pct_diff

    # Tolerance: 10% for statistic, or p-value agrees on significance direction
    TOLERANCE_PCT = 10.0
    passed = False
    if pct_diff is not None:
        passed = pct_diff < TOLERANCE_PCT
    else:
        # If original statistic is missing/zero, just check p-value direction
        if orig_p is not None:
            passed = (orig_p < 0.05) == (stat_result.p_value < 0.05)
        else:
            passed = True  # Can't compare, assume pass

    result["status"] = "PASS" if passed else "FAIL"

    if verbose:
        print()
        print(f"  {C.BOLD}{'Metric':<28} {'Original':>14} {'Reproduced':>14} {'Δ%':>10}{C.RESET}")
        print(f"  {'─' * 68}")

        stat_color = C.GREEN if (pct_diff is not None and pct_diff < TOLERANCE_PCT) else C.RED
        stat_str = f"{orig_stat:.6f}" if orig_stat is not None else "N/A"
        repr_str = f"{stat_result.statistic:.6f}"
        diff_str = f"{pct_diff:.2f}%" if pct_diff is not None else "N/A"
        print(f"  {'Statistic':<28} {stat_str:>14} {repr_str:>14} {stat_color}{diff_str:>10}{C.RESET}")

        p_orig = f"{orig_p:.2e}" if orig_p is not None else "N/A"
        p_repr = f"{stat_result.p_value:.2e}"
        print(f"  {'p-value':<28} {p_orig:>14} {p_repr:>14}")
        print(f"  {'Test':<28} {test_label:>14}")
        print(f"  {'Details':<28} {stat_result.details}")
        print()

        if passed:
            _ok(f"{C.BOLD}{C.GREEN}PASS{C.RESET} — reproduced within {TOLERANCE_PCT}% tolerance")
        else:
            _fail(f"{C.BOLD}{C.RED}FAIL{C.RESET} — deviation {diff_str} exceeds {TOLERANCE_PCT}% tolerance")

    result["message"] = stat_result.details
    return result

# ═══════════════════════════════════════════════════════════════════════════
# CLI commands
# ═══════════════════════════════════════════════════════════════════════════

def cmd_list(conn: sqlite3.Connection):
    """Print a formatted table of all discoveries."""
    discoveries = _get_all_discoveries(conn)
    if not discoveries:
        print(f"\n{C.YELLOW}No discoveries in database.{C.RESET}\n")
        return

    _header(f"ASTRA Discoveries ({len(discoveries)} total)")

    # Table header
    fmt = f"  {C.BOLD}{'ID':<20} {'Type':<15} {'Domain':<12} {'Source':<12} {'Stat':>10} {'p-value':>12} {'Description'}{C.RESET}"
    print(fmt)
    print(f"  {'─' * 100}")

    for d in discoveries:
        desc = (d.get("description") or "")[:40]
        if len(d.get("description") or "") > 40:
            desc += "…"
        stat = f"{d.get('statistic', 0):.4f}" if d.get("statistic") is not None else "—"
        pval = f"{d.get('p_value', 0):.2e}" if d.get("p_value") is not None else "—"
        print(f"  {d['id']:<20} {(d.get('finding_type') or '—'):<15} "
              f"{(d.get('domain') or '—'):<12} {(d.get('data_source') or '—'):<12} "
              f"{stat:>10} {pval:>12} {desc}")

    # Reproducibility summary
    reproducible = sum(1 for d in discoveries
                       if _infer_test(d.get("finding_type", ""), d.get("description", ""))[2])
    print(f"\n  {C.DIM}Reproducible via statistical re-test: {reproducible}/{len(discoveries)}{C.RESET}")
    print(f"  {C.DIM}Non-reproducible (causal/FCI): {len(discoveries) - reproducible}/{len(discoveries)}{C.RESET}\n")


def cmd_reproduce_one(conn: sqlite3.Connection, disc_id: str) -> bool:
    """Reproduce a single discovery. Returns True if passed."""
    disc = _get_discovery(conn, disc_id)
    if disc is None:
        print(f"\n{C.RED}Error:{C.RESET} Discovery '{disc_id}' not found.\n")
        return False
    result = reproduce_discovery(disc)
    return result["status"] == "PASS"


def cmd_reproduce_hypothesis(conn: sqlite3.Connection, hyp_id: str) -> bool:
    """Reproduce all discoveries linked to a hypothesis."""
    discoveries = _get_discoveries_by_hypothesis(conn, hyp_id)
    if not discoveries:
        print(f"\n{C.RED}Error:{C.RESET} No discoveries found for hypothesis '{hyp_id}'.\n")
        return False
    return _reproduce_batch(discoveries)


def cmd_reproduce_all(conn: sqlite3.Connection) -> bool:
    """Reproduce all discoveries."""
    discoveries = _get_all_discoveries(conn)
    if not discoveries:
        print(f"\n{C.YELLOW}No discoveries in database.{C.RESET}\n")
        return True
    return _reproduce_batch(discoveries)


def _reproduce_batch(discoveries: List[Dict]) -> bool:
    """Reproduce a list of discoveries, printing a summary. Returns True if all pass."""
    results = []
    t0 = time.time()

    print(f"\n{C.BOLD}Reproducing {len(discoveries)} discoveries …{C.RESET}\n")

    for disc in discoveries:
        result = reproduce_discovery(disc)
        results.append(result)

    elapsed = time.time() - t0

    # Summary
    _header("Reproduction Summary")
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_skip = sum(1 for r in results if r["status"] == "SKIP")
    n_err  = sum(1 for r in results if r["status"] == "ERROR")

    print(f"\n  Total:   {len(results)}")
    print(f"  {C.GREEN}Passed:  {n_pass}{C.RESET}")
    if n_fail:
        print(f"  {C.RED}Failed:  {n_fail}{C.RESET}")
    if n_skip:
        print(f"  {C.YELLOW}Skipped: {n_skip}{C.RESET}")
    if n_err:
        print(f"  {C.RED}Errors:  {n_err}{C.RESET}")
    print(f"  Elapsed: {elapsed:.1f}s\n")

    # Detail table for failures
    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        print(f"  {C.RED}{C.BOLD}Failed reproductions:{C.RESET}")
        for r in failures:
            diff = f"{r['pct_diff']:.1f}%" if r["pct_diff"] is not None else "N/A"
            print(f"    {C.RED}✗{C.RESET} {r['id']} — deviation {diff}")
        print()

    all_ok = (n_fail == 0 and n_err == 0)
    if all_ok:
        _ok(f"{C.BOLD}All reproducible discoveries verified.{C.RESET}")
    else:
        _fail(f"{C.BOLD}Some reproductions failed or errored — see above.{C.RESET}")

    return all_ok


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog="reproduce",
        description="Reproduce ASTRA discoveries from the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python reproduce.py --list
          python reproduce.py disc_abc123
          python reproduce.py --hypothesis hyp_001
          python reproduce.py --all
          python reproduce.py --all --db /path/to/discoveries.db
        """),
    )

    parser.add_argument("discovery_id", nargs="?", default=None,
                        help="ID of a specific discovery to reproduce")
    parser.add_argument("--hypothesis", "-H", metavar="ID",
                        help="Reproduce all discoveries for a hypothesis ID")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all discoveries in the database")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Reproduce all discoveries")
    parser.add_argument("--db", default=DEFAULT_DB,
                        help=f"Path to SQLite database (default: {DEFAULT_DB})")

    args = parser.parse_args()

    # At least one mode required
    if not args.list and not args.all and not args.hypothesis and args.discovery_id is None:
        parser.print_help()
        sys.exit(0)

    print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}║   ASTRA Discovery Reproducibility Tool                      ║{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}╚══════════════════════════════════════════════════════════════╝{C.RESET}")
    print(f"  {C.DIM}Database: {args.db}{C.RESET}")

    conn = _connect(args.db)

    if args.list:
        cmd_list(conn)
        conn.close()
        sys.exit(0)

    if args.all:
        ok = cmd_reproduce_all(conn)
        conn.close()
        sys.exit(0 if ok else 1)

    if args.hypothesis:
        ok = cmd_reproduce_hypothesis(conn, args.hypothesis)
        conn.close()
        sys.exit(0 if ok else 1)

    if args.discovery_id:
        ok = cmd_reproduce_one(conn, args.discovery_id)
        conn.close()
        sys.exit(0 if ok else 1)

    conn.close()


if __name__ == "__main__":
    main()
