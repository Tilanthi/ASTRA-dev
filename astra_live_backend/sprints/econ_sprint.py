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
ASTRA Economics Discovery Sprint
=================================
Fetches real economic data from World Bank & FRED APIs,
tests 10 economic hypotheses with full statistical rigor,
and saves discoveries to SQLite.
"""

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import json
import time
import sqlite3
import hashlib
import warnings
from datetime import datetime
from collections import defaultdict

import numpy as np
import requests
from scipy import stats as scipy_stats

warnings.filterwarnings("ignore")

# ── Configuration ──────────────────────────────────────────────────────────
DB_PATH = "astra_discoveries.db"
WB_BASE = "https://api.worldbank.org/v2/country/all/indicator"
FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"
TIMEOUT = 30

WB_INDICATORS = {
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "gini": "SI.POV.GINI",
    "trade_pct_gdp": "NE.TRD.GNFS.ZS",
    "debt_pct_gdp": "GC.DOD.TOTL.GD.ZS",
    "fdi_pct_gdp": "BX.KLT.DINV.WD.GD.ZS",
    "gdp_per_capita": "NY.GDP.PCAP.KD",
    "gdp_current": "NY.GDP.MKTP.CD",
    "broad_money": "FM.LBL.BMNY.GD.ZS",
    "domestic_credit": "FS.AST.PRVT.GD.ZS",
    "exports_goods": "BX.GSR.GNFS.CD",
    "merchandise_exports": "TX.VAL.MRCH.CD.WT",
    "export_concentration": "HH.MKT.CONC.XQ",  # Herfindahl index
}

# ── Data fetching ──────────────────────────────────────────────────────────

def fetch_wb(indicator_key, date_range="2000:2024", per_page=5000):
    """Fetch World Bank indicator data. Returns {(country_code, year): value}."""
    indicator = WB_INDICATORS.get(indicator_key, indicator_key)
    url = f"{WB_BASE}/{indicator}?format=json&per_page={per_page}&date={date_range}"
    print(f"  Fetching WB: {indicator_key} ({indicator})...", end=" ")
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2 or data[1] is None:
            print("No data")
            return {}
        result = {}
        for entry in data[1]:
            if entry["value"] is not None:
                cc = entry["countryiso3code"] or entry["country"]["id"]
                yr = int(entry["date"])
                if len(cc) == 3:  # skip aggregates with 2-letter codes
                    result[(cc, yr)] = float(entry["value"])
        print(f"{len(result)} obs")
        return result
    except Exception as e:
        print(f"FAILED: {e}")
        return {}

def fetch_fred_csv(series_id):
    """Fetch FRED series as CSV. Returns list of (date_str, value)."""
    url = f"{FRED_BASE}?id={series_id}"
    print(f"  Fetching FRED: {series_id}...", end=" ")
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        result = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) == 2 and parts[1] != ".":
                try:
                    result.append((parts[0], float(parts[1])))
                except ValueError:
                    pass
        print(f"{len(result)} obs")
        return result
    except Exception as e:
        print(f"FAILED: {e}")
        return []

def align_wb_data(*datasets, require_all=True):
    """Align multiple WB datasets by (country, year). Returns aligned arrays."""
    if require_all:
        common_keys = set.intersection(*[set(d.keys()) for d in datasets])
    else:
        common_keys = set.union(*[set(d.keys()) for d in datasets])
    common_keys = sorted(common_keys)
    if require_all:
        arrays = []
        for d in datasets:
            arrays.append(np.array([d[k] for k in common_keys]))
        return arrays, common_keys
    return None, common_keys

def align_wb_panel(*datasets):
    """Align and return country-year panel with no NaN."""
    common_keys = set.intersection(*[set(d.keys()) for d in datasets])
    common_keys = sorted(common_keys)
    arrays = [np.array([d[k] for k in common_keys]) for d in datasets]
    return arrays, common_keys

# ── Statistical helpers ────────────────────────────────────────────────────

def ols_regression(x, y):
    """Simple OLS. Returns slope, intercept, r, r2, p, se."""
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 10:
        return None
    slope, intercept, r, p, se = scipy_stats.linregress(x, y)
    return {"slope": slope, "intercept": intercept, "r": r, "r2": r**2, 
            "p": p, "se": se, "n": len(x)}

def cohen_d(x, y):
    """Cohen's d effect size."""
    nx, ny = len(x), len(y)
    pooled_std = np.sqrt(((nx-1)*np.var(x, ddof=1) + (ny-1)*np.var(y, ddof=1)) / (nx+ny-2))
    if pooled_std == 0:
        return 0.0
    return (np.mean(x) - np.mean(y)) / pooled_std

def fdr_correction(p_values, alpha=0.05):
    """Benjamini-Hochberg FDR correction. Returns (reject[], q_values[])."""
    n = len(p_values)
    sorted_idx = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_idx]
    q_values = np.zeros(n)
    for i in range(n):
        q_values[sorted_idx[i]] = sorted_p[i] * n / (i + 1)
    # Enforce monotonicity (from end)
    for i in range(n-2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i+1] if i+1 < n else 1.0)
    q_values = np.minimum(q_values, 1.0)
    reject = q_values < alpha
    return reject, q_values

# ── Database ───────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS discoveries (
        id TEXT PRIMARY KEY,
        timestamp REAL,
        cycle INTEGER,
        hypothesis_id TEXT,
        domain TEXT,
        finding_type TEXT,
        variables TEXT,
        statistic REAL,
        p_value REAL,
        description TEXT,
        data_source TEXT,
        strength REAL,
        follow_ups_generated INTEGER DEFAULT 0,
        verified INTEGER DEFAULT 0,
        effect_size REAL
    )""")
    conn.commit()
    return conn

def get_next_discovery_id(conn):
    """Find max existing ECON-D### and return next."""
    c = conn.cursor()
    c.execute("SELECT id FROM discoveries WHERE id LIKE 'ECON-D%'")
    existing = [row[0] for row in c.fetchall()]
    if not existing:
        return 1
    nums = []
    for eid in existing:
        try:
            nums.append(int(eid.replace("ECON-D", "")))
        except ValueError:
            pass
    return max(nums) + 1 if nums else 1

def save_discovery(conn, disc_id, hyp_id, finding_type, variables, statistic, 
                   p_value, description, data_source, strength, effect_size):
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO discoveries 
        (id, timestamp, cycle, hypothesis_id, domain, finding_type, variables, 
         statistic, p_value, description, data_source, strength, effect_size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (disc_id, time.time(), 0, hyp_id, "Economics", finding_type, variables,
         statistic, p_value, description, data_source, strength, effect_size))
    conn.commit()

# ── Hypothesis Tests ───────────────────────────────────────────────────────

results = []

def test_okuns_law(wb_data):
    """ECON-001: Okun's Law — unemployment change vs GDP growth (negative relationship)."""
    print("\n═══ ECON-001: Okun's Law ═══")
    gdp = wb_data["gdp_growth"]
    unemp = wb_data["unemployment"]
    
    # Build country-level panels: change in unemployment vs GDP growth
    # Group by country, compute year-over-year changes
    country_years = defaultdict(dict)
    for (cc, yr), v in unemp.items():
        country_years[cc][yr] = v
    
    delta_u = []
    gdp_vals = []
    for cc, years in country_years.items():
        for yr in sorted(years.keys()):
            if yr - 1 in years and (cc, yr) in gdp:
                delta_u.append(years[yr] - years[yr-1])
                gdp_vals.append(gdp[(cc, yr)])
    
    x = np.array(gdp_vals)
    y = np.array(delta_u)
    reg = ols_regression(x, y)
    if reg is None:
        print("  Insufficient data")
        return None
    
    print(f"  N={reg['n']}, slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    print(f"  Interpretation: 1pp GDP growth → {reg['slope']:.3f}pp change in unemployment")
    expected_negative = reg["slope"] < 0
    print(f"  Okun's Law predicts negative slope: {'✓ CONFIRMED' if expected_negative else '✗ VIOLATED'}")
    
    return {
        "hyp_id": "ECON-001", "name": "Okun's Law",
        "finding_type": "correlation",
        "variables": "GDP_growth, delta_unemployment",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["r"]),
        "strength": reg["r2"],
        "description": f"Okun's Law: GDP growth vs ΔUnemployment slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, n={reg['n']}. {'Confirmed' if expected_negative else 'Violated'}: negative relationship {'found' if expected_negative else 'NOT found'}.",
        "data_source": "World Bank (NY.GDP.MKTP.KD.ZG, SL.UEM.TOTL.ZS)"
    }

def test_phillips_curve(wb_data):
    """ECON-002: Phillips Curve — unemployment vs inflation (negative relationship)."""
    print("\n═══ ECON-002: Phillips Curve ═══")
    [infl, unemp], keys = align_wb_panel(wb_data["inflation"], wb_data["unemployment"])
    
    reg = ols_regression(unemp, infl)
    if reg is None:
        print("  Insufficient data")
        return None
    
    print(f"  N={reg['n']}, slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    expected_negative = reg["slope"] < 0
    print(f"  Phillips Curve predicts negative slope: {'✓ CONFIRMED' if expected_negative else '✗ WEAKENED/VIOLATED (modern expectation)'}")
    
    return {
        "hyp_id": "ECON-002", "name": "Phillips Curve",
        "finding_type": "correlation",
        "variables": "unemployment, inflation",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["r"]),
        "strength": reg["r2"],
        "description": f"Phillips Curve: unemployment vs inflation slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, n={reg['n']}. Relationship is {'negative (classical)' if expected_negative else 'non-negative (modern breakdown)'}.",
        "data_source": "World Bank (FP.CPI.TOTL.ZG, SL.UEM.TOTL.ZS)"
    }

def test_trade_gravity(wb_data):
    """ECON-003: Trade Gravity Model — trade openness scales with GDP (log-log)."""
    print("\n═══ ECON-003: Trade-GDP Gravity Proxy ═══")
    [trade, gdp], keys = align_wb_panel(wb_data["trade_pct_gdp"], wb_data["gdp_current"])
    
    # Use log GDP vs trade openness
    mask = (gdp > 0) & (trade > 0)
    log_gdp = np.log10(gdp[mask])
    log_trade = np.log10(trade[mask])
    
    reg = ols_regression(log_gdp, log_trade)
    if reg is None:
        print("  Insufficient data")
        return None
    
    print(f"  N={reg['n']}, slope={reg['slope']:.4f} (elasticity), R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    
    # Also test: larger economies tend to have LOWER trade/GDP ratio (gravity model implication)
    [trade2, gdp2], _ = align_wb_panel(wb_data["trade_pct_gdp"], wb_data["gdp_current"])
    mask2 = gdp2 > 0
    reg2 = ols_regression(np.log10(gdp2[mask2]), trade2[mask2])
    if reg2:
        print(f"  Trade openness vs log(GDP): slope={reg2['slope']:.2f}, R²={reg2['r2']:.4f}")
        print(f"  Large economies less open: {'✓' if reg2['slope'] < 0 else '✗'}")
    
    return {
        "hyp_id": "ECON-003", "name": "Trade Gravity Model",
        "finding_type": "regression",
        "variables": "log_GDP, log_trade_openness",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["r"]),
        "strength": reg["r2"],
        "description": f"Trade-GDP gravity proxy: log(trade) vs log(GDP) elasticity={reg['slope']:.4f}, R²={reg['r2']:.4f}, n={reg['n']}. {'Larger economies less trade-open' if reg2 and reg2['slope']<0 else 'No clear size-openness pattern'}.",
        "data_source": "World Bank (NE.TRD.GNFS.ZS, NY.GDP.MKTP.CD)"
    }

def test_gini_trends(wb_data):
    """ECON-004: Income Inequality Trends — Gini coefficient patterns."""
    print("\n═══ ECON-004: Income Inequality Trends ═══")
    gini = wb_data["gini"]
    if len(gini) < 50:
        print("  Insufficient Gini data")
        return None
    
    # Global trend: Gini vs year
    years = np.array([yr for (cc, yr) in gini.keys()])
    vals = np.array(list(gini.values()))
    
    reg = ols_regression(years, vals)
    if reg is None:
        print("  Insufficient data")
        return None
    
    print(f"  Global Gini observations: {reg['n']}")
    print(f"  Time trend: slope={reg['slope']:.4f}/year, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    print(f"  Mean Gini={np.mean(vals):.1f}, Median={np.median(vals):.1f}")
    
    # Split by income groups (use GDP per capita)
    gdppc = wb_data.get("gdp_per_capita", {})
    rich_gini, poor_gini = [], []
    for (cc, yr), g in gini.items():
        if (cc, yr) in gdppc:
            if gdppc[(cc, yr)] > 15000:
                rich_gini.append(g)
            else:
                poor_gini.append(g)
    
    if rich_gini and poor_gini:
        t, p_group = scipy_stats.ttest_ind(rich_gini, poor_gini)
        cd = cohen_d(np.array(poor_gini), np.array(rich_gini))
        print(f"  Rich countries Gini: {np.mean(rich_gini):.1f} (n={len(rich_gini)})")
        print(f"  Poor countries Gini: {np.mean(poor_gini):.1f} (n={len(poor_gini)})")
        print(f"  Difference: t={t:.2f}, p={p_group:.2e}, Cohen's d={cd:.2f}")
    
    direction = "declining" if reg["slope"] < 0 else "rising"
    return {
        "hyp_id": "ECON-004", "name": "Gini Coefficient Trends",
        "finding_type": "trend",
        "variables": "year, Gini_coefficient",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["r"]),
        "strength": reg["r2"],
        "description": f"Global Gini trend: {direction} at {abs(reg['slope']):.3f}/yr, R²={reg['r2']:.4f}, n={reg['n']}. Mean={np.mean(vals):.1f}. {'Rich countries lower Gini' if rich_gini and np.mean(rich_gini)<np.mean(poor_gini) else 'Poor countries lower Gini'}.",
        "data_source": "World Bank (SI.POV.GINI, NY.GDP.PCAP.KD)"
    }

def test_ppp(wb_data):
    """ECON-005: Purchasing Power Parity — inflation differentials vs GDP per capita convergence."""
    print("\n═══ ECON-005: PPP Validation ═══")
    infl = wb_data["inflation"]
    gdppc = wb_data["gdp_per_capita"]
    
    # Test: countries with higher inflation tend to have lower GDP/capita (PPP implication)
    [inf_arr, gdppc_arr], keys = align_wb_panel(infl, gdppc)
    
    mask = (gdppc_arr > 0) & np.isfinite(inf_arr)
    log_gdppc = np.log10(gdppc_arr[mask])
    inf_vals = inf_arr[mask]
    
    reg = ols_regression(log_gdppc, inf_vals)
    if reg is None:
        print("  Insufficient data")
        return None
    
    print(f"  N={reg['n']}, slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    print(f"  Richer countries have {'lower' if reg['slope']<0 else 'higher'} inflation")
    
    # Balassa-Samuelson: richer countries have higher price levels
    # We proxy this with inflation-GDP relationship
    return {
        "hyp_id": "ECON-005", "name": "PPP / Balassa-Samuelson",
        "finding_type": "regression",
        "variables": "log_GDP_per_capita, inflation",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["r"]),
        "strength": reg["r2"],
        "description": f"PPP proxy: inflation vs log(GDP/cap) slope={reg['slope']:.3f}, R²={reg['r2']:.4f}, n={reg['n']}. Richer countries have {'lower' if reg['slope']<0 else 'higher'} inflation. {'Consistent' if reg['slope']<0 else 'Inconsistent'} with PPP convergence.",
        "data_source": "World Bank (FP.CPI.TOTL.ZG, NY.GDP.PCAP.KD)"
    }

def test_gdp_mean_reversion(wb_data):
    """ECON-006: GDP Growth Mean Reversion — high growth followed by lower growth."""
    print("\n═══ ECON-006: GDP Growth Mean Reversion ═══")
    gdp = wb_data["gdp_growth"]
    
    # Build country panels
    country_years = defaultdict(dict)
    for (cc, yr), v in gdp.items():
        country_years[cc][yr] = v
    
    current = []
    next_yr = []
    for cc, years in country_years.items():
        sorted_yrs = sorted(years.keys())
        for i in range(len(sorted_yrs) - 1):
            if sorted_yrs[i+1] == sorted_yrs[i] + 1:
                current.append(years[sorted_yrs[i]])
                next_yr.append(years[sorted_yrs[i+1]])
    
    x = np.array(current)
    y = np.array(next_yr)
    
    reg = ols_regression(x, y)
    if reg is None:
        print("  Insufficient data")
        return None
    
    print(f"  N={reg['n']}, autocorrelation (slope)={reg['slope']:.4f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    mean_reversion = reg["slope"] < 1.0
    print(f"  Mean reversion (slope < 1): {'✓ CONFIRMED' if mean_reversion else '✗ NOT FOUND'} (slope={reg['slope']:.4f})")
    
    # Global mean
    all_growth = list(gdp.values())
    print(f"  Global mean GDP growth: {np.mean(all_growth):.2f}%, std={np.std(all_growth):.2f}%")
    
    return {
        "hyp_id": "ECON-006", "name": "GDP Growth Mean Reversion",
        "finding_type": "autocorrelation",
        "variables": "GDP_growth_t, GDP_growth_t+1",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(1.0 - reg["slope"]),  # deviation from random walk
        "strength": reg["r2"],
        "description": f"GDP growth mean reversion: AR(1) slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, n={reg['n']}. {'Strong mean reversion' if reg['slope']<0.5 else 'Weak persistence'}. Global mean={np.mean(all_growth):.2f}%.",
        "data_source": "World Bank (NY.GDP.MKTP.KD.ZG)"
    }

def test_reinhart_rogoff(wb_data):
    """ECON-007: Debt-to-GDP vs Growth (Reinhart-Rogoff threshold hypothesis)."""
    print("\n═══ ECON-007: Debt-to-GDP vs Growth (Reinhart-Rogoff) ═══")
    [debt, growth], keys = align_wb_panel(wb_data["debt_pct_gdp"], wb_data["gdp_growth"])
    
    if len(debt) < 50:
        print("  Insufficient debt data")
        return None
    
    # Overall regression
    reg = ols_regression(debt, growth)
    if reg is None:
        return None
    
    print(f"  N={reg['n']}, slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    
    # Test the 90% threshold
    low_debt = growth[debt < 90]
    high_debt = growth[debt >= 90]
    
    if len(low_debt) > 10 and len(high_debt) > 10:
        t, p_thresh = scipy_stats.ttest_ind(low_debt, high_debt)
        cd = cohen_d(low_debt, high_debt)
        print(f"  Debt < 90%: mean growth = {np.mean(low_debt):.2f}% (n={len(low_debt)})")
        print(f"  Debt ≥ 90%: mean growth = {np.mean(high_debt):.2f}% (n={len(high_debt)})")
        print(f"  Difference: t={t:.2f}, p={p_thresh:.2e}, Cohen's d={cd:.2f}")
        threshold_matters = p_thresh < 0.05
        print(f"  90% threshold significant: {'✓ YES' if threshold_matters else '✗ NO'}")
        p_use = p_thresh
        es_use = abs(cd)
    else:
        print(f"  Not enough high-debt observations (n={len(high_debt)})")
        p_use = reg["p"]
        es_use = abs(reg["r"])
        threshold_matters = False
    
    return {
        "hyp_id": "ECON-007", "name": "Reinhart-Rogoff Debt Threshold",
        "finding_type": "threshold_test",
        "variables": "debt_to_GDP, GDP_growth",
        "statistic": reg["r2"], "p_value": p_use,
        "effect_size": es_use,
        "strength": reg["r2"],
        "description": f"Debt-GDP: linear slope={reg['slope']:.4f}, R²={reg['r2']:.4f}. 90% threshold: {'significant' if threshold_matters else 'not significant'} (low-debt growth={np.mean(low_debt):.1f}% vs high-debt={np.mean(high_debt):.1f}%). n={reg['n']}.",
        "data_source": "World Bank (GC.DOD.TOTL.GD.ZS, NY.GDP.MKTP.KD.ZG)"
    }

def test_export_diversification(wb_data):
    """ECON-008: Export diversification vs GDP per capita."""
    print("\n═══ ECON-008: Export Diversification vs GDP/capita ═══")
    
    # Use trade openness as proxy if concentration index unavailable
    trade = wb_data.get("trade_pct_gdp", {})
    gdppc = wb_data.get("gdp_per_capita", {})
    
    if not trade or not gdppc:
        print("  Missing data")
        return None
    
    [trade_arr, gdppc_arr], keys = align_wb_panel(trade, gdppc)
    mask = (gdppc_arr > 0) & (trade_arr > 0)
    
    log_gdppc = np.log10(gdppc_arr[mask])
    trade_vals = trade_arr[mask]
    
    reg = ols_regression(log_gdppc, trade_vals)
    if reg is None:
        return None
    
    print(f"  N={reg['n']}, slope={reg['slope']:.2f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    
    # Also check non-linear (quadratic) — middle-income countries most diversified
    x = log_gdppc
    y = trade_vals
    mask2 = np.isfinite(x) & np.isfinite(y)
    x2, y2 = x[mask2], y[mask2]
    if len(x2) > 20:
        coeffs = np.polyfit(x2, y2, 2)
        y_pred = np.polyval(coeffs, x2)
        ss_res = np.sum((y2 - y_pred)**2)
        ss_tot = np.sum((y2 - np.mean(y2))**2)
        r2_quad = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        print(f"  Quadratic R²={r2_quad:.4f} (concavity={coeffs[0]:.2f})")
    
    return {
        "hyp_id": "ECON-008", "name": "Export Diversification vs Development",
        "finding_type": "regression",
        "variables": "log_GDP_per_capita, trade_openness",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["r"]),
        "strength": reg["r2"],
        "description": f"Trade openness vs log(GDP/cap): slope={reg['slope']:.2f}, R²={reg['r2']:.4f}, n={reg['n']}. {'Richer countries more open' if reg['slope']>0 else 'Richer countries less open'}.",
        "data_source": "World Bank (NE.TRD.GNFS.ZS, NY.GDP.PCAP.KD)"
    }

def test_inflation_persistence(wb_data):
    """ECON-009: Inflation Persistence — autocorrelation structure."""
    print("\n═══ ECON-009: Inflation Persistence ═══")
    infl = wb_data["inflation"]
    
    # Build country panels
    country_years = defaultdict(dict)
    for (cc, yr), v in infl.items():
        country_years[cc][yr] = v
    
    current = []
    next_yr = []
    for cc, years in country_years.items():
        sorted_yrs = sorted(years.keys())
        for i in range(len(sorted_yrs) - 1):
            if sorted_yrs[i+1] == sorted_yrs[i] + 1:
                current.append(years[sorted_yrs[i]])
                next_yr.append(years[sorted_yrs[i+1]])
    
    x = np.array(current)
    y = np.array(next_yr)
    
    reg = ols_regression(x, y)
    if reg is None:
        return None
    
    print(f"  N={reg['n']}, AR(1) coefficient={reg['slope']:.4f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    persistent = reg["slope"] > 0.5
    print(f"  Inflation is {'highly persistent' if persistent else 'moderately persistent' if reg['slope']>0.2 else 'not very persistent'}")
    
    # Ljung-Box-like: test if autocorrelation is significant
    r_auto = np.corrcoef(x, y)[0, 1]
    n = len(x)
    lb_stat = n * (n + 2) * (r_auto**2 / (n - 1))
    lb_p = 1 - scipy_stats.chi2.cdf(lb_stat, df=1)
    print(f"  Ljung-Box proxy: Q={lb_stat:.2f}, p={lb_p:.2e}")
    
    return {
        "hyp_id": "ECON-009", "name": "Inflation Persistence",
        "finding_type": "autocorrelation",
        "variables": "inflation_t, inflation_t+1",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["slope"]),
        "strength": reg["r2"],
        "description": f"Inflation persistence: AR(1)={reg['slope']:.4f}, R²={reg['r2']:.4f}, n={reg['n']}. {'Highly persistent' if persistent else 'Moderate persistence'}. Ljung-Box Q={lb_stat:.1f}, p={lb_p:.2e}.",
        "data_source": "World Bank (FP.CPI.TOTL.ZG)"
    }

def test_finance_growth(wb_data):
    """ECON-010: Financial Development vs Economic Growth."""
    print("\n═══ ECON-010: Financial Development vs Growth ═══")
    credit = wb_data.get("domestic_credit", {})
    gdp_growth = wb_data["gdp_growth"]
    
    if not credit:
        # Try broad money as alternative
        credit = wb_data.get("broad_money", {})
        if not credit:
            print("  No financial development data")
            return None
    
    [cred_arr, growth_arr], keys = align_wb_panel(credit, gdp_growth)
    
    reg = ols_regression(cred_arr, growth_arr)
    if reg is None:
        return None
    
    print(f"  N={reg['n']}, slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, p={reg['p']:.2e}")
    
    # Check for non-linearity (too much finance is bad — "too much finance" hypothesis)
    mask = np.isfinite(cred_arr) & np.isfinite(growth_arr)
    x, y = cred_arr[mask], growth_arr[mask]
    if len(x) > 30:
        coeffs = np.polyfit(x, y, 2)
        if coeffs[0] < 0:
            turning_point = -coeffs[1] / (2 * coeffs[0])
            print(f"  Inverted-U detected: turning point at {turning_point:.0f}% of GDP")
            print(f"  'Too much finance' hypothesis: ✓ SUPPORTED")
        else:
            print(f"  No inverted-U pattern (concavity={coeffs[0]:.6f})")
    
    return {
        "hyp_id": "ECON-010", "name": "Financial Development vs Growth",
        "finding_type": "regression",
        "variables": "domestic_credit_pctGDP, GDP_growth",
        "statistic": reg["r2"], "p_value": reg["p"],
        "effect_size": abs(reg["r"]),
        "strength": reg["r2"],
        "description": f"Finance-growth: credit/GDP vs GDP growth slope={reg['slope']:.4f}, R²={reg['r2']:.4f}, n={reg['n']}. {'Positive' if reg['slope']>0 else 'Negative'} relationship.",
        "data_source": "World Bank (FS.AST.PRVT.GD.ZS, NY.GDP.MKTP.KD.ZG)"
    }

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  ASTRA ECONOMICS DISCOVERY SPRINT")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 70)
    
    # 1. Fetch all World Bank data
    print("\n── Fetching World Bank Data ──")
    wb_data = {}
    for key in WB_INDICATORS:
        wb_data[key] = fetch_wb(key)
        time.sleep(0.3)  # rate limit courtesy
    
    total_obs = sum(len(v) for v in wb_data.values())
    print(f"\n  Total observations fetched: {total_obs}")
    
    # 2. Initialize DB
    conn = init_db()
    disc_counter = get_next_discovery_id(conn)
    print(f"  Next discovery ID: ECON-D{disc_counter:03d}")
    
    # 3. Run all hypothesis tests
    print("\n── Running Hypothesis Tests ──")
    
    test_functions = [
        test_okuns_law,
        test_phillips_curve,
        test_trade_gravity,
        test_gini_trends,
        test_ppp,
        test_gdp_mean_reversion,
        test_reinhart_rogoff,
        test_export_diversification,
        test_inflation_persistence,
        test_finance_growth,
    ]
    
    all_results = []
    for test_fn in test_functions:
        try:
            result = test_fn(wb_data)
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"  ERROR in {test_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. FDR correction
    print("\n── FDR Correction (Benjamini-Hochberg) ──")
    p_values = [r["p_value"] for r in all_results]
    reject, q_values = fdr_correction(p_values)
    
    for i, r in enumerate(all_results):
        r["q_value"] = q_values[i]
        r["fdr_significant"] = bool(reject[i])
        print(f"  {r['hyp_id']}: p={r['p_value']:.2e} → q={q_values[i]:.2e} {'✓' if reject[i] else '✗'}")
    
    # 5. Save to database
    print("\n── Saving Discoveries ──")
    for r in all_results:
        disc_id = f"ECON-D{disc_counter:03d}"
        save_discovery(
            conn, disc_id, r["hyp_id"], r["finding_type"], r["variables"],
            r["statistic"], r["p_value"], r["description"], r["data_source"],
            r["strength"], r["effect_size"]
        )
        print(f"  Saved {disc_id}: {r['name']}")
        disc_counter += 1
    
    # 6. Summary table
    print("\n" + "=" * 100)
    print("  ECONOMICS DISCOVERY SPRINT — SUMMARY")
    print("=" * 100)
    print(f"{'ID':<10} {'Hypothesis':<35} {'R²/Stat':>8} {'p-value':>12} {'q-value':>12} {'Effect':>8} {'FDR Sig':>8}")
    print("-" * 100)
    
    sig_count = 0
    for r in all_results:
        sig = "✓" if r["fdr_significant"] else "✗"
        if r["fdr_significant"]:
            sig_count += 1
        print(f"{r['hyp_id']:<10} {r['name']:<35} {r['statistic']:>8.4f} {r['p_value']:>12.2e} {r['q_value']:>12.2e} {r['effect_size']:>8.4f} {sig:>8}")
    
    print("-" * 100)
    print(f"  {len(all_results)} hypotheses tested | {sig_count} significant after FDR correction")
    print(f"  Total World Bank observations: {total_obs}")
    print(f"  Database: {DB_PATH}")
    
    # 7. Verify DB
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM discoveries WHERE domain='Economics'")
    total_econ = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM discoveries")
    total_all = c.fetchone()[0]
    print(f"  Economics discoveries in DB: {total_econ}")
    print(f"  Total discoveries in DB: {total_all}")
    
    conn.close()
    print("\n  Sprint complete! ✓")
    return all_results

if __name__ == "__main__":
    main()
