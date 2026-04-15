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

"""ASTRA Cross-Domain Discovery Sprint — World Bank correlations (2019)."""

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import json
import sqlite3
import time
import urllib.request
from datetime import datetime, timezone

import numpy as np
from scipy import stats

# ── World Bank data fetch ──────────────────────────────────────────────

INDICATORS = {
    "gdp_pc":       ("NY.GDP.PCAP.CD",        2019),
    "gdp_growth":   ("NY.GDP.MKTP.KD.ZG",     2019),
    "co2_pc":       ("EN.GHG.CO2.PC.CE.AR5",  2019),  # Updated indicator
    "co2_mt":       ("EN.GHG.CO2.MT.CE.AR5",  2019),  # Updated indicator
    "life_exp":     ("SP.DYN.LE00.IN",         2019),
    "infant_mort":  ("SP.DYN.IMRT.IN",         2019),
    "trade_pct":    ("NE.TRD.GNFS.ZS",        2019),
    "unemployment": ("SL.UEM.TOTL.ZS",        2019),
    "forest_pct":   ("AG.LND.FRST.ZS",        2020),
    "renewable_pct":("EG.FEC.RNEW.ZS",        2015),
    "urban_pct":    ("SP.URB.TOTL.IN.ZS",     2019),
}

BASE = "https://api.worldbank.org/v2/country/all/indicator/{ind}?format=json&per_page=1000&date={yr}"

def fetch_indicator(name, ind, year):
    url = BASE.format(ind=ind, yr=year)
    print(f"  Fetching {name} ({ind}, {year})...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ASTRA/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        if not isinstance(data, list) or len(data) < 2 or data[1] is None:
            print(f"    ⚠ Unexpected response for {name}")
            return {}
        result = {}
        for item in data[1]:
            cid = item.get("country", {}).get("id")
            val = item.get("value")
            if cid and val is not None:
                result[cid] = float(val)
        print(f"    ✓ {len(result)} countries")
        return result
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return {}

print("=" * 70)
print("ASTRA Cross-Domain Discovery Sprint")
print("=" * 70)

print("\n📡 Fetching World Bank data...")
datasets = {}
for name, (ind, year) in INDICATORS.items():
    datasets[name] = fetch_indicator(name, ind, year)
    time.sleep(0.3)

# ── Hypothesis definitions ─────────────────────────────────────────────

HYPOTHESES = [
    ("CD-001", "GDP per capita vs CO2 per capita",     "gdp_pc",       "co2_pc",   True,  True,  "Economics↔Climate"),
    ("CD-002", "Life expectancy vs CO2 per capita",     "life_exp",     "co2_pc",   False, True,  "Epi↔Climate"),
    ("CD-003", "GDP per capita vs Life expectancy",     "gdp_pc",       "life_exp", True,  False, "Economics↔Epi"),
    ("CD-004", "Urbanization vs CO2 per capita",        "urban_pct",    "co2_pc",   False, True,  "Demographics↔Climate"),
    ("CD-005", "Trade openness vs CO2 per capita",      "trade_pct",    "co2_pc",   False, True,  "Economics↔Climate"),
    ("CD-006", "Renewable energy % vs GDP per capita",  "renewable_pct","gdp_pc",   False, True,  "Climate↔Economics"),
    ("CD-007", "Forest area vs CO2 per capita",         "forest_pct",   "co2_pc",   False, True,  "Climate↔Climate"),
    ("CD-008", "Unemployment vs Life expectancy",       "unemployment", "life_exp", False, False, "Economics↔Epi"),
]

# ── Analysis ───────────────────────────────────────────────────────────

def merge(d1, d2):
    keys = set(d1) & set(d2)
    pairs = [(d1[k], d2[k]) for k in keys if d1[k] > 0 and d2[k] > 0]
    if not pairs:
        return np.array([]), np.array([])
    x, y = zip(*pairs)
    return np.array(x), np.array(y)

def fdr_correction(pvals):
    """Benjamini-Hochberg FDR correction."""
    n = len(pvals)
    indexed = sorted(enumerate(pvals), key=lambda t: t[1])
    corrected = [0.0] * n
    prev = 1.0
    for rank_idx in range(n - 1, -1, -1):
        orig_idx, p = indexed[rank_idx]
        rank = rank_idx + 1
        adj = min(prev, p * n / rank)
        corrected[orig_idx] = adj
        prev = adj
    return corrected

print("\n🔬 Running cross-domain analyses...")
results = []
all_pvals = []

for hid, desc, xvar, yvar, log_x, log_y, domains in HYPOTHESES:
    x_raw, y_raw = merge(datasets[xvar], datasets[yvar])
    n = len(x_raw)
    if n < 10:
        print(f"  {hid}: ⚠ Only {n} pairs, skipping")
        results.append((hid, desc, domains, n, None))
        all_pvals.extend([1.0, 1.0])
        continue

    x = np.log10(x_raw) if log_x else x_raw
    y = np.log10(y_raw) if log_y else y_raw

    # Correlations
    r_pearson, p_pearson = stats.pearsonr(x, y)
    r_spearman, p_spearman = stats.spearmanr(x, y)

    # Linear regression
    slope, intercept, r_val, p_reg, se = stats.linregress(x, y)
    r_sq = r_val ** 2

    # Effect size (Cohen's f² from R²)
    f_sq = r_sq / (1 - r_sq) if r_sq < 1 else float('inf')
    if f_sq >= 0.35:
        effect = "large"
    elif f_sq >= 0.15:
        effect = "medium"
    elif f_sq >= 0.02:
        effect = "small"
    else:
        effect = "negligible"

    res = {
        "hid": hid, "desc": desc, "domains": domains, "n": n,
        "xvar": xvar, "yvar": yvar, "log_x": log_x, "log_y": log_y,
        "r_pearson": r_pearson, "p_pearson": p_pearson,
        "r_spearman": r_spearman, "p_spearman": p_spearman,
        "slope": slope, "intercept": intercept,
        "r_sq": r_sq, "p_reg": p_reg, "se": se,
        "f_sq": f_sq, "effect": effect,
    }
    results.append((hid, desc, domains, n, res))
    all_pvals.extend([p_pearson, p_reg])
    print(f"  {hid}: N={n}, r={r_pearson:.3f}, R²={r_sq:.3f} ({effect})")

# FDR correction
adj_pvals = fdr_correction(all_pvals)
idx = 0
for i, (hid, desc, domains, n, res) in enumerate(results):
    if res is not None:
        res["p_pearson_fdr"] = adj_pvals[idx]
        res["p_reg_fdr"] = adj_pvals[idx + 1]
    idx += 2

# ── Print summary ──────────────────────────────────────────────────────

print("\n" + "=" * 105)
print(f"{'HID':<8} {'Description':<42} {'N':>4} {'r_P':>7} {'r_S':>7} {'R²':>7} {'Effect':>10} {'p(FDR)':>10} {'Sig':>4}")
print("-" * 105)
for hid, desc, domains, n, res in results:
    if res is None:
        print(f"{hid:<8} {desc:<42} {n:>4}   — insufficient data —")
        continue
    sig = "✓" if res["p_pearson_fdr"] < 0.05 else "✗"
    print(f"{hid:<8} {desc:<42} {n:>4} {res['r_pearson']:>7.3f} {res['r_spearman']:>7.3f} "
          f"{res['r_sq']:>7.3f} {res['effect']:>10} {res['p_pearson_fdr']:>10.2e} {sig:>4}")
print("=" * 105)

# ── Save to DB ─────────────────────────────────────────────────────────

DB_PATH = "astra_discoveries.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Use existing schema: discoveries(id, timestamp, cycle, hypothesis_id, domain, finding_type,
#   variables, statistic, p_value, description, data_source, strength, follow_ups_generated, verified, effect_size)
# outcomes(id, hypothesis_id, test_type, result, p_value, effect_size, timestamp)

now_ts = time.time()
now_iso = datetime.now(timezone.utc).isoformat()
inserted_d = 0
inserted_o = 0

for i, (hid, desc, domains, n, res) in enumerate(results):
    if res is None:
        continue

    d_corr_id = f"CD-D{(i*2+1):03d}"
    d_reg_id = f"CD-D{(i*2+2):03d}"

    x_label = f"log10({res['xvar']})" if res['log_x'] else res['xvar']
    y_label = f"log10({res['yvar']})" if res['log_y'] else res['yvar']

    # Correlation discovery
    cur.execute("SELECT id FROM discoveries WHERE id=?", (d_corr_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO discoveries (id, timestamp, cycle, hypothesis_id, domain, finding_type, "
            "variables, statistic, p_value, description, data_source, strength, follow_ups_generated, verified, effect_size) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d_corr_id, now_ts, 0, hid, "Cross-Domain", "correlation",
             json.dumps([res["xvar"], res["yvar"]]),
             res["r_pearson"], res["p_pearson_fdr"],
             f"{hid} Correlation [{domains}]: {desc} (r={res['r_pearson']:.3f}, ρ={res['r_spearman']:.3f}, N={n})",
             "World Bank 2019", abs(res["r_pearson"]), 0, 0, abs(res["r_pearson"])))
        inserted_d += 1

    # Regression discovery
    cur.execute("SELECT id FROM discoveries WHERE id=?", (d_reg_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO discoveries (id, timestamp, cycle, hypothesis_id, domain, finding_type, "
            "variables, statistic, p_value, description, data_source, strength, follow_ups_generated, verified, effect_size) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d_reg_id, now_ts, 0, hid, "Cross-Domain", "regression",
             json.dumps([x_label, y_label]),
             res["r_sq"], res["p_reg_fdr"],
             f"{hid} Regression [{domains}]: {y_label} ~ {x_label} (R²={res['r_sq']:.3f}, slope={res['slope']:.3f}, {res['effect']})",
             "World Bank 2019", res["r_sq"], 0, 0, res["f_sq"]))
        inserted_d += 1

    # Outcomes
    o_corr_id = f"CD-O{(i*2+1):03d}"
    o_reg_id = f"CD-O{(i*2+2):03d}"

    cur.execute("SELECT id FROM outcomes WHERE id=?", (o_corr_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO outcomes VALUES (?,?,?,?,?,?,?)",
                    (o_corr_id, hid, "correlation",
                     json.dumps({"pearson_r": round(res["r_pearson"], 4),
                                 "spearman_r": round(res["r_spearman"], 4),
                                 "n": n, "significant_fdr": bool(res["p_pearson_fdr"] < 0.05)}),
                     float(res["p_pearson_fdr"]), float(abs(res["r_pearson"])), now_iso))
        inserted_o += 1

    cur.execute("SELECT id FROM outcomes WHERE id=?", (o_reg_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO outcomes VALUES (?,?,?,?,?,?,?)",
                    (o_reg_id, hid, "regression",
                     json.dumps({"R_squared": round(res["r_sq"], 4),
                                 "slope": round(res["slope"], 4),
                                 "effect": res["effect"], "n": n,
                                 "significant_fdr": bool(res["p_reg_fdr"] < 0.05)}),
                     float(res["p_reg_fdr"]), float(res["f_sq"]), now_iso))
        inserted_o += 1

conn.commit()

# Count totals
cur.execute("SELECT COUNT(*) FROM discoveries")
total_d = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM outcomes")
total_o = cur.fetchone()[0]
conn.close()

print(f"\n💾 Database: {inserted_d} discoveries + {inserted_o} outcomes inserted")
print(f"   Totals: {total_d} discoveries, {total_o} outcomes in {DB_PATH}")

# Summary of significant findings
print("\n🔑 Key Findings (FDR < 0.05):")
for hid, desc, domains, n, res in results:
    if res and res["p_pearson_fdr"] < 0.05:
        direction = "positive" if res["r_pearson"] > 0 else "negative"
        print(f"  {hid} [{domains}]: {desc}")
        print(f"      r={res['r_pearson']:.3f} ({direction}), R²={res['r_sq']:.3f}, "
              f"effect={res['effect']}, N={n}")

print("\n✅ Cross-domain sprint complete.")
