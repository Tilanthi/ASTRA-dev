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

import numpy as np
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
    # Lever (b): the 2026-07-14 pilots showed some object types are textbook-
    # saturated (stars -> HR diagram, 100% "known"). Mark them so the rotation
    # miner skips them by default and effort goes to novelty-yielding niches.
    textbook_risk: str = "low"   # "low" (mine by default) | "high" (skip by default)
    niche_hint: str = ""         # appended to the proposer prompt for this dataset

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


def productive_datasets() -> List[Dataset]:
    """Datasets worth mining by default — i.e. NOT textbook-saturated.

    The 2026-07-14 pilots found stars (SDSS + Gaia) are ~100% 'known' (HR diagram,
    reduced proper motion), so scaling them burns compute for no novelty. The
    rotation miner mines only these by default; pass --include-high-risk to opt in."""
    return [ds for ds in DATASET_REGISTRY.values() if ds.textbook_risk != "high"]


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


def _cone_match_merge(sdss_df: "pd.DataFrame", wise_df: "pd.DataFrame",
                      max_sep_arcsec: float = 2.0) -> "pd.DataFrame":
    """Phase 4a — positional (cone) cross-match of SDSS optical rows to an AllWISE
    IR table. For each SDSS object, find the nearest WISE source and keep it if it
    lies within ``max_sep_arcsec``; merge the WISE photometry onto the matched SDSS
    rows and compute optical-IR colours. Unmatched SDSS rows are dropped. Returns an
    empty DataFrame if either input is empty or lacks ra/dec (defensive -- the fetcher
    raises on an empty result; this never fabricates rows)."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord

    if (sdss_df is None or wise_df is None or len(sdss_df) == 0 or len(wise_df) == 0
            or not {"ra", "dec"}.issubset(sdss_df.columns)
            or not {"ra", "dec"}.issubset(wise_df.columns)):
        return pd.DataFrame()
    s = SkyCoord(sdss_df["ra"].to_numpy(), sdss_df["dec"].to_numpy(), unit="deg")
    w = SkyCoord(wise_df["ra"].to_numpy(), wise_df["dec"].to_numpy(), unit="deg")
    idx, d2d, _ = s.match_to_catalog_sky(w)
    good = np.asarray(d2d < max_sep_arcsec * u.arcsec)
    if not good.any():
        return pd.DataFrame()
    out = sdss_df[good].reset_index(drop=True).copy()
    wise_cols = [c for c in wise_df.columns
                 if c not in ("ra", "dec") and c not in out.columns]
    if wise_cols:
        wise_matched = (wise_df.iloc[idx[good]][wise_cols].reset_index(drop=True))
        out = pd.concat([out, wise_matched], axis=1)
    if "r" in out and "w1" in out:
        out["r-w1"] = out["r"] - out["w1"]
    if "r" in out and "w2" in out:
        out["r-w2"] = out["r"] - out["w2"]
    if "w1" in out and "w2" in out:
        out["w1w2"] = out["w1"] - out["w2"]
    return out


def _fetch_wise_midir() -> "pd.DataFrame":
    """AllWISE mid-IR (W1-W4) sources — opens the mid-IR colour space (AGN/dust
    diagnostics like W1-W2, stellar-class W1-W2 vs W3-W4) entirely OUTSIDE optical
    photometry. Primary source IRSA AllWISE; VizieR II/328 fallback. Column names
    are normalised (IRSA/VizieR differ in case)."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    field = SkyCoord("150.0 2.0", unit="deg")
    rows = None
    try:
        from astroquery.irsa import Irsa
        for cat in ("allwise_p3as_psd", "allwise"):
            try:
                t = Irsa.query_region(field, radius=0.6 * u.deg, catalog=cat)
                if t is not None and len(t) > 0:
                    rows = t
                    break
            except Exception:
                continue
    except Exception:
        pass
    if rows is None:
        from astroquery.vizier import Vizier
        Vizier.ROW_LIMIT = 5000
        res = Vizier.query_region(field, radius=0.6 * u.deg, catalog="II/328/allwise")
        if res and len(res):
            rows = res[0]
    if rows is None or len(rows) == 0:
        raise RuntimeError("WISE query returned no rows (IRSA + VizieR).")
    df = rows.to_pandas()
    lc = {str(c).lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n in df.columns:
                return n
            if n.lower() in lc:
                return lc[n.lower()]
        return None

    rename = {}
    for key, cand in (("w1", "w1mpro"), ("w2", "w2mpro"),
                      ("w3", "w3mpro"), ("w4", "w4mpro")):
        c = pick(cand, cand.upper())
        if c:
            rename[c] = key
    df = df.rename(columns=rename)
    if "w1" in df and "w2" in df:
        df = df[df["w1"].notna() & df["w2"].notna()].reset_index(drop=True)
    if len(df) == 0:
        raise RuntimeError("WISE: no rows with W1+W2 after normalisation.")
    df["w1w2"] = df["w1"] - df["w2"]
    if "w3" in df.columns and "w4" in df.columns:
        df["w3w4"] = df["w3"] - df["w4"]
    return df


def _fetch_allwise_cone(ra: float, dec: float, radius_deg: float) -> "pd.DataFrame":
    """AllWISE W1-W4 sources + positions in a sky cone (IRSA allwise_p3as_psd, VizieR
    II/328/allwise fallback), normalised to columns ra, dec, w1..w4. Shared by the
    cross-match fetcher so the optical and IR pulls cover the same patch."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord

    field = SkyCoord(float(ra) * u.deg, float(dec) * u.deg)
    rows = None
    try:
        from astroquery.irsa import Irsa
        for cat in ("allwise_p3as_psd", "allwise"):
            try:
                t = Irsa.query_region(field, radius=radius_deg * u.deg, catalog=cat)
                if t is not None and len(t) > 0:
                    rows = t
                    break
            except Exception:
                continue
    except Exception:
        pass
    if rows is None:
        from astroquery.vizier import Vizier
        Vizier.ROW_LIMIT = 50000
        res = Vizier.query_region(field, radius=radius_deg * u.deg,
                                  catalog="II/328/allwise")
        if res and len(res):
            rows = res[0]
    if rows is None or len(rows) == 0:
        raise RuntimeError("AllWISE cone query returned no rows (IRSA + VizieR).")
    df = rows.to_pandas()
    lc = {str(c).lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n in df.columns:
                return n
            if n.lower() in lc:
                return lc[n.lower()]
        return None

    rename = {}
    for key, cand in (("ra", "ra"), ("dec", "dec"),
                      ("w1", "w1mpro"), ("w2", "w2mpro"),
                      ("w3", "w3mpro"), ("w4", "w4mpro")):
        c = pick(cand, cand.upper())
        if c and c != key:
            rename[c] = key
    df = df.rename(columns=rename)
    keep = [c for c in ("ra", "dec", "w1", "w2", "w3", "w4") if c in df.columns]
    df = df[keep]
    if "ra" in df and "dec" in df and "w1" in df:
        df = df[df["ra"].notna() & df["dec"].notna() & df["w1"].notna()]
    return df.reset_index(drop=True)


def _fetch_sdss_wise_xmatch() -> "pd.DataFrame":
    """Phase 4a -- cross-matched SDSS optical galaxies x AllWISE mid-IR for the SAME
    objects (a genuinely new cross-modal axis: optical-IR colours tracing dust / stellar
    mass / AGN). Region-bounded so both catalogs cover one patch, then cone-matched
    locally via _cone_match_merge. Real archival data only; raises on empty."""
    from astroquery.sdss import SDSS

    # ~9 deg^2 box around (150, 2) -> a few thousand galaxies, enough statistical
    # power to clear the Bonferroni gate (116 rows needed |rho|>=~0.5; a few
    # thousand need only |rho|>=~0.16). Circumscribed by the AllWISE cone below.
    sql = """
    SELECT TOP 6000
           p.objid, p.ra, p.dec,
           p.dered_u AS u, p.dered_g AS g, p.dered_r AS r,
           p.dered_i AS i, p.dered_z AS z,
           p.extinction_r, p.petror50_r, p.petror90_r,
           s.z AS z_spec
    FROM PhotoObj AS p
    JOIN SpecObj  AS s ON s.bestobjid = p.objid
    WHERE s.class = 'GALAXY' AND s.z BETWEEN 0.01 AND 0.4 AND s.zwarning = 0
      AND p.petror50_r > 0 AND p.petror90_r > 0
      AND p.dered_r BETWEEN 14 AND 19.5
      AND p.ra  BETWEEN 148.5 AND 151.5
      AND p.dec BETWEEN 0.5 AND 3.5
    """
    res = SDSS.query_sql(" ".join(sql.split()))
    if res is None or len(res) == 0:
        raise RuntimeError("SDSS galaxy region query returned no rows.")
    sdss = res.to_pandas()
    sdss["concentration_r"] = sdss["petror90_r"] / sdss["petror50_r"]
    wise = _fetch_allwise_cone(150.0, 2.0, 2.2)
    out = _cone_match_merge(sdss, wise, max_sep_arcsec=2.0)
    if len(out) == 0:
        raise RuntimeError("SDSS x AllWISE cross-match produced 0 matched galaxies.")
    return out


def _fetch_gaia_variables() -> "pd.DataFrame":
    """Gaia DR3 photometrically VARIABLE stars — a time-domain/variability sample
    (objects confirmed to vary), opening variability-related relations outside
    static photometry. (Optical wavelength but a new modality; period is not in
    gaia_source, so relations are colour/astrometry-of-variables, not PL.)"""
    from astroquery.gaia import Gaia
    adql = """
    SELECT TOP 4000 source_id, ra, dec, phot_g_mean_mag, phot_bp_mean_mag,
           phot_rp_mean_mag, bp_rp, ruwe, phot_variable_flag, parallax
    FROM gaiadr3.gaia_source
    WHERE phot_variable_flag='VARIABLE' AND bp_rp BETWEEN 0 AND 4
      AND ruwe < 1.4 AND phot_g_mean_mag BETWEEN 10 AND 16
    """
    job = Gaia.launch_job(" ".join(adql.split()))
    table = job.get_results()
    if table is None or len(table) == 0:
        raise RuntimeError("Gaia variable-star query returned no rows.")
    return table.to_pandas()


# --------------------------------------------------------------------------- #
# registry (extensible — add Dataset(...) + a fetcher to grow the lake)        #
# --------------------------------------------------------------------------- #
register_dataset(Dataset(
    name="sdss_stars",
    description="SDSS spectroscopic STARS with u,g,r,i,z model mags and z (radial velocity proxy). Stellar populations — different relationship space from galaxies.",
    columns=["u", "g", "r", "i", "z", "z_spec", "ra", "dec"],
    source="SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
    fetcher=_fetch_sdss_stars,
    textbook_risk="high",  # pilots: stellar colour relations are ~100% textbook (HR locus)
    niche_hint="Stars are HR-diagram-dominated and ~100% textbook in pilots; only "
               "pursue a genuinely non-obvious higher-order relation if one exists.",
))
register_dataset(Dataset(
    name="sdss_qso",
    description="SDSS QSOs (quasars) with u,g,r,i,z mags and spectroscopic redshift z_spec out to z~3.5. Quasar colour-redshift is distinct from the galaxy locus.",
    columns=["u", "g", "r", "i", "z", "z_spec", "ra", "dec"],
    source="SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
    fetcher=_fetch_sdss_qso,
    textbook_risk="low",
    niche_hint="Productive directions (have yielded novelty): colour×redshift "
               "interaction terms (e.g. z × (u−g)), non-linear colour space, "
               "colour–colour curvature for QSOs.",
))
register_dataset(Dataset(
    name="sdss_galaxy_extended",
    description="SDSS galaxies with dereddened u,g,r,i,z, extinction_r, Petrosian radii (r50, r90) and a derived concentration index. Opens size/morphology relationships beyond colour.",
    columns=["u", "g", "r", "i", "z", "extinction_r", "petror50_r", "petror90_r", "concentration_r", "z_spec"],
    source="SDSS DR CAS (https://skyserver.sdss.org) via astroquery.sdss",
    fetcher=_fetch_sdss_galaxy_extended,
    textbook_risk="low",
    niche_hint="Productive directions (have yielded novelty): concentration-index "
               "(morphology) effects, colour–colour curvature, residuals after "
               "removing the colour–redshift trend, size×colour interactions.",
))
register_dataset(Dataset(
    name="gaia_nearby",
    description="Gaia DR3 nearby stars (<100 pc): parallax, proper motions (pmra, pmdec), G/BP/RP mags, BP-RP colour, RUWE, and derived absolute G magnitude. Astrometric relationship space (HR diagram, kinematics).",
    columns=["parallax", "pmra", "pmdec", "phot_g_mean_mag", "phot_bp_mean_mag", "phot_rp_mean_mag", "bp_rp", "ruwe", "abs_g"],
    source="Gaia DR3 (https://gea.esac.esa.int/archive) via astroquery.gaia",
    fetcher=_fetch_gaia_nearby,
    textbook_risk="high",  # pilots: 100% known (HR diagram, reduced proper motion)
    niche_hint="Stellar astrometry is HR-diagram / reduced-proper-motion dominated "
               "and ~100% textbook in pilots; only pursue a non-obvious higher-order "
               "relation if one exists.",
))
register_dataset(Dataset(
    name="wise_midir",
    description="AllWISE mid-IR sources (W1,W2,W3,W4 + W1-W2 and W3-W4 colours). The "
                "mid-IR colour space — AGN/dust/stellar-class diagnostics — is a NEW "
                "wavelength, distinct from the optical samples.",
    columns=["w1", "w2", "w1w2", "w3", "w4", "ra", "dec"],
    source="AllWISE via astroquery.irsa (fallback VizieR II/328)",
    fetcher=_fetch_wise_midir,
    textbook_risk="low",
    niche_hint="Mid-IR is a NEW wavelength for this search. Productive: higher-order "
               "mid-IR colour relations — but AVOID restating the standard W1-W2 > 0.5 "
               "AGN selection cut (textbook).",
))
register_dataset(Dataset(
    name="sdss_wise_xmatch",
    description=("SDSS optical galaxies CROSS-MATCHED to AllWISE mid-IR for the SAME "
                 "objects: dereddened u,g,r,i,z + Petrosian radii/concentration + "
                 "redshift AND WISE W1-W4 per galaxy, plus optical-IR colours (r-w1, "
                 "r-w2, w1w2). Opens the cross-modal optical-IR axis (dust, stellar "
                 "mass, AGN content) that no single-wavelength sample has."),
    columns=["u", "g", "r", "i", "z", "extinction_r", "petror50_r", "petror90_r",
             "concentration_r", "z_spec", "w1", "w2", "w3", "w4", "w1w2", "r-w1", "r-w2"],
    source="SDSS DR CAS x AllWISE (IRSA) via astroquery + astropy cone-match",
    fetcher=_fetch_sdss_wise_xmatch,
    textbook_risk="low",
    niche_hint=("Cross-modal optical+mid-IR per galaxy. Productive: optical-IR colours "
                "(r-w1, r-w2) vs morphology/concentration/redshift -- these trace dust, "
                "stellar mass and AGN content. PREFER residuals/conditionals (e.g. the "
                "r-w1 residual after removing z). AVOID textbook: the W1-W2>0.5 AGN "
                "wedge and plain colour-redshift."),
    cache_basename="sdss_wise_xmatch.csv",
))
register_dataset(Dataset(
    name="gaia_variables",
    description="Gaia DR3 photometrically VARIABLE stars (confirmed variables): G/BP/RP "
                "mags, BP-RP colour, RUWE, parallax. A time-domain / variability sample.",
    columns=["phot_g_mean_mag", "phot_bp_mean_mag", "phot_rp_mean_mag", "bp_rp",
             "ruwe", "parallax", "ra", "dec"],
    source="Gaia DR3 (https://gea.esac.esa.int/archive) via astroquery.gaia",
    fetcher=_fetch_gaia_variables,
    textbook_risk="low",
    niche_hint="Confirmed variables — a time-domain sample. No period here, so AVOID "
               "textbook period-luminosity claims; pursue non-obvious colour/astrometry "
               "relations specific to the variable population.",
))


# Band-like columns for which pairwise differences (colour indices) are meaningful
# derived features when mining correlation structure.
_BAND_COLUMNS = {"u", "g", "r", "i", "z", "w1", "w2", "w3", "w4",
                 "j", "h", "k", "phot_g_mean_mag", "phot_bp_mean_mag",
                 "phot_rp_mean_mag"}


def correlation_seeds(name: str, top_k: int = 8, sample: int = 2000,
                      rmin: float = 0.30, rmax: float = 0.85) -> List[tuple]:
    """Phase 1a — the dataset's strongest real, NON-TRIVIAL correlations, to seed the
    proposer with genuine signals instead of letting it guess (74% of blind proposals
    fail Gate-1 significance).

    Computes over the dataset's ADVERTISED columns only (proposer-visible; avoids the
    ~200-column export garbage in caches like AllWISE), derives colour indices for
    band-like columns, and returns the top-K off-diagonal Spearman pairs with
    rmin <= |r| <= rmax. Raw-band-vs-raw-band pairs (trivially correlated fluxes) are
    excluded, so only meaningful colour<->physical-quantity / colour<->colour pairs
    survive. Defensive: [] on any error / missing cache."""
    try:
        ds = DATASET_REGISTRY.get(name)
        if ds is None:
            return []
        df = load_dataframe(name)
        cols = [c for c in ds.columns
                if c not in ("ra", "dec") and c in df.columns
                and pd.api.types.is_numeric_dtype(df[c])]
        if len(cols) < 2:
            return []
        if len(df) > sample:
            df = df.sample(n=sample, random_state=42)
        feats = df[cols].copy()
        bands = [c for c in cols if c.lower() in _BAND_COLUMNS]
        for ia, a in enumerate(bands):
            for b in bands[ia + 1:]:
                feats[f"{a}-{b}"] = df[a] - df[b]
        corr = feats.corr(method="spearman")
        pairs = []
        cs = list(corr.columns)

        def _concatenated_bands(tok):
            """True if tok is >=2 band names concatenated with no separator, e.g.
            'w1w2' / 'w1w2w3' (AllWISE) or 'ugriz' -- these are pre-computed
            colours, NOT science columns. Without this they were misclassified as
            science (the name has no '-'), leaking algebraically-coupled
            colour<->colour pairs into the seeds."""
            t = tok.lower()
            bs = sorted({str(b).lower() for b in bands}, key=len, reverse=True)
            i = 0
            n = 0
            while i < len(t):
                for b in bs:
                    if t[i:i + len(b)] == b:
                        i += len(b)
                        n += 1
                        break
                else:
                    return False  # a char no band covers -> not a pure concatenation
            return n >= 2

        def _is_science(f):
            # a "science" column: not a derived colour (no '-'), not a raw band,
            # and not a concatenated-band colour like 'w1w2'.
            return ("-" not in f) and (f not in bands) and (not _concatenated_bands(f))

        for ia, a in enumerate(cs):
            for b in cs[ia + 1:]:
                r = corr.loc[a, b]
                if not (pd.notna(r) and rmin <= abs(r) <= rmax):
                    continue
                # keep only pairs with at least one science column (colour<->quantity
                # or quantity<->quantity); drop mag<->mag and colour<->colour, which
                # are algebraically coupled / trivially correlated.
                if not (_is_science(a) or _is_science(b)):
                    continue
                pairs.append((a, b, round(float(r), 3)))
        pairs.sort(key=lambda x: -abs(x[2]))

        # RESIDUAL seeds (Phase-1 fix): the strongest PAIRWISE correlations are the
        # textbook ones (band<->redshift, mag<->size, the HR diagram). Surface what
        # only appears AFTER removing each science column's dominant predictor -- a
        # non-obvious, mid-strength partial signal the proposer can build on. These
        # are NOT subject to `rmax`: a high residual correlation is a strong
        # *partial* signal (the trivial dominant axis is already gone), not a
        # near-deterministic pairwise identity.
        RESID_RMIN = 0.20
        resid = []
        science_cols = [c for c in cs if _is_science(c)]
        for s in science_cols[:3]:
            preds = [c for c in cs if c != s and not _is_science(c)]
            if not preds:
                continue
            best_p, best_abs = None, 0.0
            for p in preds:
                r = corr.loc[s, p]
                if pd.notna(r) and abs(r) > best_abs:
                    best_p, best_abs = p, abs(r)
            if best_p is None or best_abs < rmin:
                continue
            x = feats[best_p].to_numpy(dtype=float)
            y = feats[s].to_numpy(dtype=float)
            m = np.isfinite(x) & np.isfinite(y)
            if int(m.sum()) < 30:
                continue
            slope, intercept = np.polyfit(x[m], y[m], 1)
            r_series = pd.Series(y - (slope * x + intercept), index=feats.index)
            for c in cs:
                if c in (s, best_p):
                    continue
                r = r_series.corr(feats[c], method="spearman")
                if pd.notna(r) and RESID_RMIN <= abs(r) < 0.99:
                    resid.append((f"resid({s}~{best_p})", c, round(float(r), 3)))
        resid.sort(key=lambda x: -abs(x[2]))

        # Lead with the non-obvious residual seeds; fill the remainder with the
        # strongest direct (pairwise) seeds.
        out = resid[:top_k]
        for a, b, r in pairs:
            if len(out) >= top_k:
                break
            out.append((a, b, r))
        return out[:top_k]
    except Exception:
        return []


def explored_themes(name: str, n: int = 6) -> List[tuple]:
    """Phases 1b/1c — recent claims already tried on this dataset, for novelty-
    steering (avoid the known/textbook families) and coverage awareness (avoid
    re-deriving what's been explored). Returns [(claim_snippet, verdict_label)]
    most-recent first. Defensive: [] on any error / missing log."""
    try:
        vl = LAKE_DIR.parent / "claim_verdicts.jsonl"
        if not vl.exists():
            return []
        rows = [json.loads(l) for l in vl.read_text().splitlines() if l.strip()]
        rows = [r for r in rows if r.get("dataset") == name and r.get("claim")]
        rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
        out = []
        for r in rows[:n]:
            st = (r.get("gate2") or {}).get("status") or ""
            if r.get("both_pass"):
                label = "novel"
            elif st == "known":
                label = "KNOWN/textbook"
            elif st == "retrieval-failed":
                label = "unverified"
            elif (r.get("gate1") or {}).get("pass") is not True:
                label = "not-significant"
            else:
                label = "rejected"
            out.append((str(r["claim"])[:90], label))
        return out
    except Exception:
        return []


def task_system_for(name: str) -> Optional[str]:
    """Return a proposer TASK_SYSTEM prompt describing this dataset's columns,
    or None for the legacy/unknown case (caller uses the default TASK_SYSTEM)."""
    ds = DATASET_REGISTRY.get(name)
    if ds is None:
        return None
    cols = ", ".join(ds.columns)
    prompt = (
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
        "textbook basics and the dominant pairwise relations for this kind of "
        "object (e.g. colour-redshift for galaxies; the HR diagram / reduced "
        "proper motion for stars) — they will be rejected as known.\n"
        "- PREFER higher-order / non-obvious relations: a relation holding in a "
        "SUBSET ('among high-concentration galaxies, ...'), NON-LINEAR or "
        "curvature effects, RESIDUALS after removing a dominant trend, or "
        "INTERACTIONS of 3+ of the columns above. Reach past simple pairwise "
        "correlations.\n"
        "- No file I/O, no network, no plotting. Correct and self-contained.\n"
        "RESPOND WITH EITHER:\n"
        "  (a) one or more diff blocks (<<<SEARCH>>>...<<<REPLACE>>>...<<<END>>>)\n"
        "  (b) one complete ```python``` module (CLAIM + run_claim).\n"
        "Output ONLY the diff or code, no explanation."
    )
    if ds.niche_hint:
        prompt += "\nDataset-specific guidance: " + ds.niche_hint + "\n"
    seeds = correlation_seeds(name)
    if seeds:
        joined = "; ".join(f"{a} vs {b} (Spearman r={r:+.2f})" for a, b, r in seeds)
        prompt += ("\nStrong relations ALREADY present in this data (grounded starting "
                   "points — extrapolate toward non-obvious HIGHER-ORDER forms such as "
                   "residuals, interactions, or conditional subsets; do NOT just restate "
                   "these pairwise correlations): " + joined + "\n")
    explored = explored_themes(name)
    if explored:
        joined = "; ".join(f'"{c}" [{lab}]' for c, lab in explored)
        prompt += ("\nClaims ALREADY explored on this dataset (go in a DISTINCT direction; "
                   "those marked KNOWN are textbook and will be rejected again): "
                   + joined + "\n")
    return prompt


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
            risk = "TEXTBOOK-saturated" if ds.textbook_risk == "high" else "mine"
            print(f"  {ds.name:24s} [{cached}/{wired}/{risk}]  {ds.source}")
            print(f"  {' ':26s} cols: {', '.join(ds.columns)}")
    elif args.command == "fetch":
        if not args.name:
            ap.error("fetch requires a dataset name")
        p = fetch_and_cache(args.name, force=args.force)
        print(f"OK -> {p}")
