"""data_lake.py — Sub-project C: a registry of REAL astronomy datasets for the
Phase-2 claim search.

Motivation (2026-07-14 diagnostic): the autonomous search was drawing from a
single narrow sample (SDSS u,g,r,i,z + z_spec on ~4000 galaxies). 148/157 Gate-2
"known" rejections were foundational/textbook, 129/157 were colour–redshift —
the only strong relationships in that space ARE the textbook ones. Broadening
the data is the lever that targets the real bottleneck; a smarter selector is
not (Sub-project A, dropped).

Design (mirrors the trusted ``real_data.photoz_sdss_cache.csv`` pattern):
  * Fetchers run OUTSIDE the sandbox (network available) and write a cache CSV
    + JSON manifest to ~/.astra_persistent/evolved_programs/data_lake/.
  * The sandboxed claim_eval_worker reads the cache FILE only (no network) —
    exactly as it already reads photoz_sdss_cache.csv today. The sandbox
    network-denial profile (astra_worker.sb) is unchanged.
  * The Phase-2 search draws splits from the lake via ``--data-source NAME``.
    Default behaviour is unchanged (legacy sdss_photoz via real_data.py); the
    lake is strictly opt-in.

Project rule: NO MOCK DATA. Every fetcher pulls from a real public archive
(SDSS CAS, Gaia DR3, ...) or raises loudly. Nothing here fabricates rows.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

import pandas as pd

LAKE_DIR = (Path.home() / ".astra_persistent" / "evolved_programs" / "data_lake")
LEGACY = "legacy"  # sentinel: use real_data.py (sdss_photoz), unchanged behaviour


@dataclass
class Dataset:
    """One real dataset the claim search can mine."""
    name: str
    description: str          # human-readable, injected into the proposer prompt
    columns: List[str]        # column names shown to the proposer
    source: str               # archive provenance, e.g. "SDSS DR CAS", "Gaia DR3"
    fetcher: Optional[Callable[[], "pd.DataFrame"]] = None  # None = not wired yet
    cache_basename: str = ""

    def cache_path(self) -> Path:
        return LAKE_DIR / (self.cache_basename or f"{self.name}.csv")

    def manifest_path(self) -> Path:
        return self.cache_path().with_suffix(".manifest.json")


DATASET_REGISTRY: Dict[str, Dataset] = {}


def register_dataset(ds: Dataset) -> Dataset:
    DATASET_REGISTRY[ds.name] = ds
    return ds


def get_dataset(name: str) -> Optional[Dataset]:
    return DATASET_REGISTRY.get(name)


def list_datasets() -> List[Dataset]:
    return list(DATASET_REGISTRY.values())


# --------------------------------------------------------------------------- #
# cache + fetch (run OUTSIDE the sandbox)                                      #
# --------------------------------------------------------------------------- #
def _write_manifest(ds: Dataset, df: "pd.DataFrame", cache: Path) -> None:
    ds.manifest_path().write_text(json.dumps({
        "name": ds.name,
        "source": ds.source,
        "fetch_epoch": int(time.time()),
        "fetch_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_rows": int(len(df)),
        "columns": list(df.columns),
        "csv_sha1": hashlib.sha1(cache.read_bytes()).hexdigest()[:16],
        "note": "REAL archival data fetched via astroquery. No mock rows.",
    }, indent=2))


def fetch_and_cache(name: str, force: bool = False) -> Path:
    """Ensure the cache for ``name`` exists. Fetches from the real archive
    (network required — call this OUTSIDE the sandbox) on first use or when
    ``force``. Returns the cache path. Raises on unknown name, missing fetcher,
    or empty result — it never fabricates data."""
    ds = DATASET_REGISTRY.get(name)
    if ds is None:
        raise KeyError(f"unknown data-lake dataset: {name!r}; "
                       f"known: {sorted(DATASET_REGISTRY)}")
    if ds.fetcher is None:
        raise RuntimeError(f"dataset {name!r} has no fetcher wired yet "
                           f"(extensibility placeholder)")
    cache = ds.cache_path()
    if cache.exists() and not force:
        return cache
    LAKE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[data_lake] fetching REAL data for {name!r} from {ds.source} ...")
    df = ds.fetcher()
    if df is None or len(df) == 0:
        raise RuntimeError(f"fetcher for {name!r} returned empty — "
                           f"refusing to cache fake/empty data.")
    df = df.reset_index(drop=True)
    df.to_csv(cache, index=False)
    _write_manifest(ds, df, cache)
    print(f"[data_lake] cached {len(df)} real rows -> {cache}")
    return cache


def load_dataframe(name: str) -> "pd.DataFrame":
    """Read the cached dataframe. Sandbox-safe: file read only, no network."""
    ds = DATASET_REGISTRY.get(name)
    if ds is None:
        raise KeyError(f"unknown data-lake dataset: {name!r}")
    cache = ds.cache_path()
    if not cache.exists():
        raise FileNotFoundError(
            f"cache missing for {name!r} — run data_lake.fetch_and_cache("
            f"{name!r}) first (outside the sandbox).")
    return pd.read_csv(cache)


def load_split(name: str, seed: int = 42,
               train_frac: float = 0.6, eval_frac: float = 0.2):
    """train/eval/test split of a lake dataset (mirrors real_data.load_split)."""
    import numpy as np
    df = load_dataframe(name)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(df))
    df = df.iloc[perm].reset_index(drop=True)
    n = len(df)
    n_tr = int(n * train_frac)
    n_ev = int(n * eval_frac)
    return {
        "train": df.iloc[:n_tr].reset_index(drop=True),
        "eval": df.iloc[n_tr:n_tr + n_ev].reset_index(drop=True),
        "test": df.iloc[n_tr + n_ev:].reset_index(drop=True),
    }


# --------------------------------------------------------------------------- #
# concrete fetchers (real public archives)                                     #
# --------------------------------------------------------------------------- #
def _fetch_sdss_stars() -> "pd.DataFrame":
    """SDSS photometric STARS (class='STAR') with spectroscopy — stellar colour
    loci and metallicity tracers, a different population from the galaxy sample."""
    from astroquery.sdss import SDSS
    sql = """
    SELECT TOP 4000
           p.objid, p.ra, p.dec,
           p.u, p.g, p.r, p.i, p.z AS z_mag,
           s.z AS z_spec
    FROM PhotoObj AS p
    JOIN SpecObj  AS s ON s.bestobjid = p.objid
    WHERE s.class = 'STAR'
      AND p.u BETWEEN 10 AND 25 AND p.g BETWEEN 10 AND 25
      AND p.r BETWEEN 10 AND 25 AND p.i BETWEEN 10 AND 25 AND p.z BETWEEN 10 AND 25
      AND s.zwarning = 0 AND s.snMedian_g > 10
    """
    res = SDSS.query_sql(" ".join(sql.split()))
    if res is None or len(res) == 0:
        raise RuntimeError("SDSS STAR query returned no rows.")
    return res.to_pandas().rename(columns={"z_mag": "z"})


def _fetch_sdss_qso() -> "pd.DataFrame":
    """SDSS QSOs (class='QSO') — quasar colour–redshift occupies a distinct
    region from galaxy colour–redshift; a separate relationship space."""
    from astroquery.sdss import SDSS
    sql = """
    SELECT TOP 4000
           p.objid, p.ra, p.dec,
           p.u, p.g, p.r, p.i, p.z AS z_mag,
           s.z AS z_spec
    FROM PhotoObj AS p
    JOIN SpecObj  AS s ON s.bestobjid = p.objid
    WHERE s.class = 'QSO'
      AND p.u BETWEEN 10 AND 25 AND p.g BETWEEN 10 AND 25
      AND p.r BETWEEN 10 AND 25 AND p.i BETWEEN 10 AND 25 AND p.z BETWEEN 10 AND 25
      AND s.zwarning = 0 AND s.z BETWEEN 0.01 AND 3.5
    """
    res = SDSS.query_sql(" ".join(sql.split()))
    if res is None or len(res) == 0:
        raise RuntimeError("SDSS QSO query returned no rows.")
    return res.to_pandas().rename(columns={"z_mag": "z"})


def _fetch_sdss_galaxy_extended() -> "pd.DataFrame":
    """SDSS galaxies with morphology/size columns (Petrosian radii -> concentration
    index) and dereddened mags — opens size/morphology relationships beyond colour."""
    from astroquery.sdss import SDSS
    sql = """
    SELECT TOP 4000
           p.objid, p.ra, p.dec,
           p.dered_u AS u, p.dered_g AS g, p.dered_r AS r,
           p.dered_i AS i, p.dered_z AS z,
           p.extinction_r, p.petror50_r, p.petror90_r,
           s.z AS z_spec
    FROM PhotoObj AS p
    JOIN SpecObj  AS s ON s.bestobjid = p.objid
    WHERE s.class = 'GALAXY' AND s.z BETWEEN 0.01 AND 0.4 AND s.zwarning = 0
      AND p.petror50_r > 0 AND p.petror90_r > 0
      AND p.dered_r BETWEEN 12 AND 20
    """
    res = SDSS.query_sql(" ".join(sql.split()))
    if res is None or len(res) == 0:
        raise RuntimeError("SDSS galaxy-extended query returned no rows.")
    df = res.to_pandas()
    # concentration index (morphology) — a real derived feature the proposer can use
    df["concentration_r"] = df["petror90_r"] / df["petror50_r"]
    return df


def _fetch_gaia_nearby() -> "pd.DataFrame":
    """Gaia DR3 nearby stars (parallax > 10 mas => within ~100 pc) with quality
    astrometry + BP/RP colour — opens astrometric relationships (HR diagram,
    absolute magnitude from parallax) entirely outside the SDSS photometric space."""
    from astroquery.gaia import Gaia
    adql = """
    SELECT TOP 4000 source_id, ra, dec, parallax, pmra, pmdec,
           phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag, bp_rp, ruwe
    FROM gaiadr3.gaia_source
    WHERE parallax > 10 AND parallax_over_error > 20
      AND ruwe < 1.4 AND bp_rp BETWEEN -0.5 AND 4
      AND phot_g_mean_mag BETWEEN 5 AND 18
    """
    job = Gaia.launch_job(" ".join(adql.split()))
    table = job.get_results()
    if table is None or len(table) == 0:
        raise RuntimeError("Gaia DR3 query returned no rows.")
    df = table.to_pandas()
    # absolute G magnitude from parallax (in mas) — a real derived quantity
    import numpy as np
    df["abs_g"] = df["phot_g_mean_mag"] - 5 * (np.log10(1000.0 / df["parallax"]) - 1)
    return df


# --------------------------------------------------------------------------- #
# registry (extensible — add Dataset(...) + a fetcher to grow the lake)        #
# --------------------------------------------------------------------------- #
register_dataset(Dataset(
    name="sdss_stars",
    description="SDSS spectroscopic STARS with u,g,r,i,z model mags and z (radial velocity proxy). Stellar populations — different relationship space from galaxies.",
    columns=["u", "g", "r", "i", "z", "z_spec", "ra", "dec"],
    source="SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
    fetcher=_fetch_sdss_stars,
))
register_dataset(Dataset(
    name="sdss_qso",
    description="SDSS QSOs (quasars) with u,g,r,i,z mags and spectroscopic redshift z_spec out to z~3.5. Quasar colour-redshift is distinct from the galaxy locus.",
    columns=["u", "g", "r", "i", "z", "z_spec", "ra", "dec"],
    source="SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
    fetcher=_fetch_sdss_qso,
))
register_dataset(Dataset(
    name="sdss_galaxy_extended",
    description="SDSS galaxies with dereddened u,g,r,i,z, extinction_r, Petrosian radii (r50, r90) and a derived concentration index. Opens size/morphology relationships beyond colour.",
    columns=["u", "g", "r", "i", "z", "extinction_r", "petror50_r", "petror90_r", "concentration_r", "z_spec"],
    source="SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
    fetcher=_fetch_sdss_galaxy_extended,
))
register_dataset(Dataset(
    name="gaia_nearby",
    description="Gaia DR3 nearby stars (<100 pc): parallax, proper motions (pmra, pmdec), G/BP/RP mags, BP-RP colour, RUWE, and derived absolute G magnitude. Astrometric relationship space (HR diagram, kinematics).",
    columns=["parallax", "pmra", "pmdec", "phot_g_mean_mag", "phot_bp_mean_mag", "phot_rp_mean_mag", "bp_rp", "ruwe", "abs_g"],
    source="Gaia DR3 (https://gea.esac.esa.int/archive) via astroquery.gaia",
    fetcher=_fetch_gaia_nearby,
))


def task_system_for(name: str) -> Optional[str]:
    """Return a proposer TASK_SYSTEM prompt describing this dataset's columns,
    or None for the legacy/unknown case (caller uses the default TASK_SYSTEM)."""
    ds = DATASET_REGISTRY.get(name)
    if ds is None:
        return None
    cols = ", ".join(ds.columns)
    return (
        "You are an expert astronomer searching for a NOVEL, real statistical "
        "relationship in this dataset that is NOT already a well-known textbook "
        "result. You are given the current candidate (a natural-language CLAIM "
        "plus a `run_claim(df_train, df_eval)` function that tests it on real "
        "data and returns {effect, pvalue, effect_type, summary}).\n"
        f"Dataset: {ds.description}\n"
        f"The available REAL data columns are: {cols}.\n"
        "You may use numpy/scipy/pandas/sklearn only.\n"
        "HARD RULES:\n"
        "- Keep the EXACT signature: def run_claim(df_train, df_eval)\n"
        "- Compute on df_train (the FIRST argument): the body MUST reference "
        "df_train (e.g. start with `df = df_train`). NEVER set `df = df_eval` or "
        "compute on df_eval alone — computing on df_eval makes the result "
        "identical on the train/test splits and the candidate is rejected.\n"
        "- Set a module-level CLAIM = \"...\" string: a specific, quantitative claim.\n"
        "- Return a dict with keys effect (a correlation/contrast magnitude in "
        "[-1,1] or a normalized contrast), pvalue (a real significance), "
        "effect_type, summary.\n"
        "- Pick a relationship genuinely significant on the data but AVOID "
        "textbook basics and AVOID restating a colour-redshift relation. Prefer "
        "specific, non-obvious combinations of the columns above.\n"
        "- No file I/O, no network, no plotting. Correct and self-contained.\n"
        "RESPOND WITH EITHER:\n"
        "  (a) one or more diff blocks (<<<SEARCH>>>...<<<REPLACE>>>...<<<END>>>)\n"
        "  (b) one complete ```python``` module (CLAIM + run_claim).\n"
        "Output ONLY the diff or code, no explanation."
    )


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="ASTRA data lake (Sub-project C)")
    ap.add_argument("command", choices=["list", "fetch"])
    ap.add_argument("name", nargs="?", help="dataset name (for 'fetch')")
    ap.add_argument("--force", action="store_true", help="re-fetch even if cached")
    args = ap.parse_args()
    if args.command == "list":
        for ds in list_datasets():
            cached = "cached" if ds.cache_path().exists() else "NOT-cached"
            wired = "ok" if ds.fetcher else "no-fetcher"
            print(f"  {ds.name:24s} [{cached}/{wired}]  {ds.source}")
            print(f"  {' ':26s} cols: {', '.join(ds.columns)}")
    elif args.command == "fetch":
        if not args.name:
            ap.error("fetch requires a dataset name")
        p = fetch_and_cache(args.name, force=args.force)
        print(f"OK -> {p}")
