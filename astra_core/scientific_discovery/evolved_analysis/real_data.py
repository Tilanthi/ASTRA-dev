"""
real_data.py — Fetch and cache GENUINELY REAL astronomical data for the prototype.

Task: photometric redshift (photo-z) estimation.
  - Inputs : SDSS u,g,r,i,z model mags (real broadband photometry).
  - Target : spectroscopic redshift z_spec (an INDEPENDENT real measurement).
  - Why real / non-circular: z_spec comes from spectra, NOT from the broadband
    photometry used to predict it. Nothing here is simulated.

Data source: SDSS DR CAS via astroquery.sdss (the live public archive). We fetch
once, then cache to disk so every later run is offline and reproducible. A
manifest records the exact SQL, fetch time, and row count so the data is auditable
as real.

IMPORTANT (project rule): NO MOCK DATA. This module fetches from the real SDSS
archive or fails loudly. It never fabricates rows.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CACHE_CSV = DATA_DIR / "photoz_sdss_cache.csv"
MANIFEST = DATA_DIR / "photoz_sdss_manifest.json"

# Real, hand-written SQL against the public SDSS CAS. Returned rows are real
# measured quantities for real objects. Kept in the manifest for auditability.
SQL = """
SELECT TOP 4000
       p.objid, p.ra, p.dec,
       p.u, p.g, p.r, p.i, p.z AS z_mag,
       s.z  AS z_spec, s.plate, s.mjd, s.fiberid
FROM PhotoObj AS p
JOIN SpecObj  AS s ON s.bestobjid = p.objid
WHERE s.class = 'GALAXY'
  AND s.z BETWEEN 0.01 AND 0.4
  AND p.u BETWEEN 10 AND 25 AND p.g BETWEEN 10 AND 25
  AND p.r BETWEEN 10 AND 25 AND p.i BETWEEN 10 AND 25 AND p.z BETWEEN 10 AND 25
  AND s.zwarning = 0
"""

BANDS = ["u", "g", "r", "i", "z"]


def _write_manifest(rows: int) -> None:
    MANIFEST.write_text(json.dumps({
        "source": "SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
        "fetch_epoch": int(time.time()),
        "fetch_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sql": " ".join(SQL.split()),
        "n_rows": rows,
        "sql_sha256": hashlib.sha256(SQL.encode()).hexdigest()[:16],
        "columns": ["objid", "ra", "dec", "u", "g", "r", "i", "z",
                    "z_spec", "plate", "mjd", "fiberid"],
        "note": "REAL archival data. z_spec is spectroscopic (independent of "
                "the ugriz photometry used as predictor inputs). No mock rows.",
    }, indent=2))


def fetch(force_refetch: bool = False) -> pd.DataFrame:
    """Return the cached real SDSS photo-z sample, fetching from the archive
    on first call (or when force_refetch=True). Raises on any fetch failure —
    it never falls back to synthetic data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CACHE_CSV.exists() and not force_refetch:
        return pd.read_csv(CACHE_CSV).rename(columns={"z_mag": "z"})

    from astroquery.sdss import SDSS  # imported lazily so offline runs need nothing
    print("[real_data] fetching REAL data from SDSS CAS ...")
    res = SDSS.query_sql(SQL)
    if res is None or len(res) == 0:
        raise RuntimeError("SDSS query returned no rows — refusing to continue "
                           "with empty/fake data.")
    df = res.to_pandas().rename(columns={"z_mag": "z"})  # band -> uniform 'z'
    df.to_csv(CACHE_CSV, index=False)
    _write_manifest(len(df))
    print(f"[real_data] cached {len(df)} real galaxies -> {CACHE_CSV}")
    print(f"[real_data] manifest -> {MANIFEST}")
    return df


def load_split(seed: int = 42,
               train_frac: float = 0.6,
               eval_frac: float = 0.2):
    """Load cached data and split into TRAIN / EVAL / TEST.

    - TRAIN : used to fit the regression model inside EVALUATE.
    - EVAL  : used to compute the selection fitness (what evolution sees).
    - TEST  : held out completely; reported ONCE at the end as the honest number.

    All three are real; none overlap.
    """
    df = fetch()
    # Sanity: confirm we have the real independent target and sane ranges.
    assert "z_spec" in df.columns and df["z_spec"].between(0, 0.4).all()
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df))
    df = df.iloc[perm].reset_index(drop=True)
    n = len(df)
    n_tr = int(n * train_frac)
    n_ev = int(n * eval_frac)
    tr = df.iloc[:n_tr].reset_index(drop=True)
    ev = df.iloc[n_tr:n_tr + n_ev].reset_index(drop=True)
    te = df.iloc[n_tr + n_ev:].reset_index(drop=True)
    return {"train": tr, "eval": ev, "test": te}


if __name__ == "__main__":
    df = fetch(force_refetch="--refetch" in os.sys.argv)
    print(df[["u", "g", "r", "i", "z", "z_spec"]].describe().round(3).to_string())
    print("\nManifest written at:", MANIFEST)
    print("Inspect it to confirm the data source is the real SDSS archive.")
