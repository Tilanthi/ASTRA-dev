"""cls_data.py — REAL mixed-class SDSS sample for WP5 (object classification).

Fetches a CLASS-BALANCED real sample of STAR / GALAXY / QSO with ugriz model
mags + the SPECTROSCOPIC class (independent ground truth), caches it with a
provenance manifest. No mock data. This is the second task: a different problem
type (classification) and metric (balanced accuracy) than photo-z, to prove the
engine is task-agnostic.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CACHE = DATA_DIR / "sdss_class_cache.csv"
MANIFEST = DATA_DIR / "sdss_class_manifest.json"

SQL = """
SELECT TOP {n} p.objid, p.ra, p.dec, p.u, p.g, p.r, p.i, p.z AS z_mag,
       s.class AS spec_class, s.z AS z_spec
FROM PhotoObj AS p JOIN SpecObj AS s ON s.bestobjid = p.objid
WHERE s.class = '{cls}' AND s.zwarning = 0
  AND p.u BETWEEN 12 AND 22 AND p.g BETWEEN 12 AND 22
  AND p.r BETWEEN 12 AND 22 AND p.i BETWEEN 12 AND 22 AND p.z BETWEEN 12 AND 22
"""
BANDS = ["u", "g", "r", "i", "z"]
CLASSES = ["STAR", "GALAXY", "QSO"]


def _write_manifest(rows: int, counts: dict) -> None:
    MANIFEST.write_text(json.dumps({
        "source": "SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
        "fetch_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sql_template": " ".join(SQL.split()),
        "n_rows": rows, "class_counts": counts,
        "note": "REAL archival data. spec_class is spectroscopic (independent of "
                "the ugriz photometry used as predictor inputs). Class-balanced.",
    }, indent=2))


def fetch(force_refetch: bool = False) -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CACHE.exists() and not force_refetch:
        return pd.read_csv(CACHE)
    from astroquery.sdss import SDSS
    print("[cls_data] fetching REAL class-balanced SDSS sample ...")
    frames = []
    for cls in CLASSES:
        f = SDSS.query_sql(SQL.format(cls=cls, n=2000)).to_pandas()
        f["spec_class"] = cls
        frames.append(f)
        print(f"  {cls}: {len(f)}")
    df = pd.concat(frames, ignore_index=True).rename(columns={"z_mag": "z"})
    df.to_csv(CACHE, index=False)
    _write_manifest(len(df), df["spec_class"].value_counts().to_dict())
    print(f"[cls_data] cached {len(df)} real objects -> {CACHE}")
    return df


def load_split(seed: int = 42, train_frac: float = 0.6, eval_frac: float = 0.2):
    df = fetch()
    assert "spec_class" in df.columns
    rng = np.random.default_rng(seed)
    df = df.iloc[rng.permutation(len(df))].reset_index(drop=True)
    n = len(df); n_tr = int(n * train_frac); n_ev = int(n * eval_frac)
    return {"train": df.iloc[:n_tr].reset_index(drop=True),
            "eval": df.iloc[n_tr:n_tr + n_ev].reset_index(drop=True),
            "test": df.iloc[n_tr + n_ev:].reset_index(drop=True)}
