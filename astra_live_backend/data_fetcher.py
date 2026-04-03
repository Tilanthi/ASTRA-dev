"""
ASTRA Live — Real Astronomical Data Fetcher
Connects to live astronomical APIs for real scientific data.

Data Sources:
  - NASA Exoplanet Archive (TAP) — confirmed exoplanets, stellar parameters
  - Gaia DR3 (TAP) — astrometry, photometry for 1.8B sources
  - SDSS DR18 — galaxy photometry, redshifts, spectroscopy
  - Pantheon+ SNe Ia — 1701 Type Ia supernovae for cosmology
  - VizieR TAP — general catalog access
  - arXiv API — literature search
"""
import time
import json
import logging
import numpy as np
import requests
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# Request timeout for all API calls
TIMEOUT = 20
# Maximum rows to fetch per query (keep small for speed)
MAX_ROWS = 2000


@dataclass
class DataResult:
    """Result from a data fetch operation."""
    source: str
    query: str
    data: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    row_count: int = 0
    fetch_time: float = 0.0

    def __post_init__(self):
        self.row_count = len(self.data) if self.data is not None else 0


def _safe_float(val) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════
# NASA Exoplanet Archive
# ═══════════════════════════════════════════════════════════════

EXOPLANET_API = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"


def fetch_exoplanets(limit: int = MAX_ROWS) -> DataResult:
    """Fetch confirmed exoplanets with orbital and stellar parameters."""
    t0 = time.time()
    query = f"""
    SELECT TOP {limit}
        pl_name, hostname, discoverymethod, disc_year,
        pl_orbper, pl_orbsmax, pl_orbeccen, pl_bmassj, pl_radj,
        st_teff, st_rad, st_mass, st_met, st_lum,
        sy_dist, sy_vmag, sy_kmag,
        ra, dec
    FROM ps
    WHERE default_flag = 1
    ORDER BY disc_year DESC
    """
    try:
        r = requests.get(EXOPLANET_API, params={'query': query, 'format': 'json'}, timeout=TIMEOUT)
        r.raise_for_status()
        rows = r.json()

        records = []
        for row in rows:
            period = _safe_float(row.get('pl_orbper'))
            sma = _safe_float(row.get('pl_orbsmax'))
            mass = _safe_float(row.get('pl_bmassj'))
            radius = _safe_float(row.get('pl_radj'))
            st_teff = _safe_float(row.get('st_teff'))
            st_rad = _safe_float(row.get('st_rad'))
            st_mass = _safe_float(row.get('st_mass'))
            distance = _safe_float(row.get('sy_dist'))

            if period and sma and mass:
                records.append({
                    'name': row.get('pl_name', ''),
                    'host': row.get('hostname', ''),
                    'method': row.get('discoverymethod', ''),
                    'year': _safe_float(row.get('disc_year')) or 0,
                    'period': period,
                    'sma': sma,
                    'eccentricity': _safe_float(row.get('pl_orbeccen')) or 0,
                    'mass_jup': mass,
                    'radius_jup': radius,
                    'st_teff': st_teff,
                    'st_rad': st_rad,
                    'st_mass': st_mass,
                    'distance_pc': distance,
                    'ra': _safe_float(row.get('ra')) or 0,
                    'dec': _safe_float(row.get('dec')) or 0,
                })

        data = np.array([(r['period'], r['sma'], r['mass_jup'], r['st_teff'] or 0,
                          r['st_mass'] or 0, r['distance_pc'] or 0, r['year'])
                         for r in records],
                        dtype=[('period', 'f8'), ('sma', 'f8'), ('mass', 'f8'),
                               ('st_teff', 'f8'), ('st_mass', 'f8'), ('distance', 'f8'),
                               ('year', 'f8')])

        return DataResult(
            source="NASA Exoplanet Archive",
            query=query.strip(),
            data=data,
            metadata={'records': records, 'total': len(records)},
            fetch_time=time.time() - t0,
        )
    except Exception as e:
        logger.error(f"Exoplanet fetch failed: {e}")
        return DataResult(source="NASA Exoplanet Archive", query=query.strip(),
                          data=np.array([]), metadata={'error': str(e)},
                          fetch_time=time.time() - t0)


def fetch_exoplanet_periods() -> np.ndarray:
    """Fetch just orbital periods for statistical analysis."""
    result = fetch_exoplanets()
    if result.data is None or len(result.data) == 0:
        return np.array([])
    return result.data['period']


def fetch_transit_depths() -> np.ndarray:
    """Fetch transit depths from Kepler/K2/TESS discoveries."""
    t0 = time.time()
    query = """
    SELECT TOP 5000 pl_trandep, pl_trandur, pl_ratror, pl_ratdor, pl_orbper
    FROM ps
    WHERE discoverymethod = 'Transit' AND default_flag = 1 AND pl_trandep IS NOT NULL
    """
    try:
        r = requests.get(EXOPLANET_API, params={'query': query, 'format': 'json'}, timeout=TIMEOUT)
        r.raise_for_status()
        rows = r.json()
        depths = np.array([_safe_float(row.get('pl_trandep')) for row in rows
                           if _safe_float(row.get('pl_trandep')) is not None])
        return depths
    except Exception as e:
        logger.error(f"Transit depth fetch failed: {e}")
        return np.array([])


# ═══════════════════════════════════════════════════════════════
# Pantheon+ Type Ia Supernovae
# ═══════════════════════════════════════════════════════════════

PANTHEON_URL = "https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_Data/4_DISTANCES_AND_COVAR/Pantheon%2BSH0ES.dat"


def fetch_pantheon_sne() -> DataResult:
    """Fetch Pantheon+ Type Ia supernova sample for Hubble diagram."""
    t0 = time.time()
    try:
        r = requests.get(PANTHEON_URL, timeout=TIMEOUT)
        r.raise_for_status()
        lines = r.text.strip().split('\n')
        header = lines[0].split()

        z_col = header.index('zHD') if 'zHD' in header else 1
        mb_col = header.index('m_b_corr') if 'm_b_corr' in header else 7
        mb_err_col = header.index('m_b_corr_err_DIAG') if 'm_b_corr_err_DIAG' in header else 8

        records = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) <= max(z_col, mb_col, mb_err_col):
                continue
            z = _safe_float(parts[z_col])
            mb = _safe_float(parts[mb_col])
            mb_err = _safe_float(parts[mb_err_col])
            if z and mb and z > 0.001:
                records.append({'z': z, 'mb': mb, 'mb_err': mb_err or 0.1})

        data = np.array([(r['z'], r['mb'], r['mb_err']) for r in records],
                        dtype=[('z', 'f8'), ('mb', 'f8'), ('mb_err', 'f8')])

        return DataResult(
            source="Pantheon+ SNe Ia",
            query="Full Pantheon+ SH0ES sample",
            data=data,
            metadata={'records': records, 'total': len(records),
                      'columns': header},
            fetch_time=time.time() - t0,
        )
    except Exception as e:
        logger.error(f"Pantheon+ fetch failed: {e}")
        return DataResult(source="Pantheon+ SNe Ia", query="", data=np.array([]),
                          metadata={'error': str(e)}, fetch_time=time.time() - t0)


def fetch_hubble_diagram() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fetch redshift, distance modulus, and errors for Hubble diagram."""
    result = fetch_pantheon_sne()
    if result.data is None or len(result.data) == 0:
        return np.array([]), np.array([]), np.array([])
    return result.data['z'], result.data['mb'], result.data['mb_err']


# ═══════════════════════════════════════════════════════════════
# Gaia DR3
# ═══════════════════════════════════════════════════════════════

GAIA_API = "https://gea.esac.esa.int/tap-server/tap/sync"


def fetch_gaia_stars(limit: int = 5000) -> DataResult:
    """Fetch Gaia DR3 stellar sample with astrometry and photometry."""
    t0 = time.time()
    query = f"""
    SELECT TOP {limit}
        source_id, ra, dec, parallax, parallax_error,
        phot_g_mean_mag, bp_rp, radial_velocity,
        teff_gspphot,logg_gspphot, mh_gspphot,
        pmra, pmdec
    FROM gaiadr3.gaia_source
    WHERE parallax > 10 AND parallax_error < 0.1
        AND phot_g_mean_mag < 12
        AND ruwe < 1.4
    ORDER BY random_index
    """
    try:
        r = requests.get(GAIA_API, params={'QUERY': query, 'REQUEST': 'doQuery',
                                            'LANG': 'ADQL', 'FORMAT': 'json'},
                         timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()

        # Gaia returns {metadata: [{name:col}], data: [[val,...],...]}
        col_names = [c['name'] for c in result.get('metadata', [])]
        col_idx = {name: i for i, name in enumerate(col_names)}
        raw_rows = result.get('data', [])

        def get_col(row, name):
            idx = col_idx.get(name)
            if idx is not None and idx < len(row):
                return _safe_float(row[idx])
            return None

        records = []
        for row in raw_rows:
            plx = get_col(row, 'parallax')
            gmag = get_col(row, 'phot_g_mean_mag')
            bp_rp = get_col(row, 'bp_rp')
            teff = get_col(row, 'teff_gspphot')

            if plx and plx > 0 and gmag:
                dist = 1000.0 / plx  # pc
                abs_mag = gmag - 5 * np.log10(dist) + 5
                records.append({
                    'ra': get_col(row, 'ra') or 0,
                    'dec': get_col(row, 'dec') or 0,
                    'parallax': plx,
                    'distance_pc': dist,
                    'gmag': gmag,
                    'abs_mag': abs_mag,
                    'bp_rp': bp_rp,
                    'teff': teff,
                })

        data = np.array([(r['parallax'], r['distance_pc'], r['gmag'], r['abs_mag'],
                          r['bp_rp'] or 0, r['teff'] or 0)
                         for r in records],
                        dtype=[('parallax', 'f8'), ('distance', 'f8'), ('gmag', 'f8'),
                               ('abs_mag', 'f8'), ('bp_rp', 'f8'), ('teff', 'f8')])

        return DataResult(
            source="Gaia DR3",
            query=query.strip(),
            data=data,
            metadata={'records': records, 'total': len(records)},
            fetch_time=time.time() - t0,
        )
    except Exception as e:
        logger.error(f"Gaia fetch failed: {e}")
        return DataResult(source="Gaia DR3", query=query.strip(), data=np.array([]),
                          metadata={'error': str(e)}, fetch_time=time.time() - t0)


def fetch_hr_diagram() -> Tuple[np.ndarray, np.ndarray]:
    """Fetch color (BP-RP) and absolute magnitude for HR diagram."""
    result = fetch_gaia_stars(5000)
    if result.data is None or len(result.data) == 0:
        return np.array([]), np.array([])
    valid = result.data[result.data['bp_rp'] != 0]
    return valid['bp_rp'], valid['abs_mag']


# ═══════════════════════════════════════════════════════════════
# SDSS DR18
# ═══════════════════════════════════════════════════════════════

SDSS_API = "https://skyserver.sdss.org/dr18/SkyServerWS/SearchTools/SqlSearch"


def fetch_sdss_galaxies(limit: int = 5000) -> DataResult:
    """Fetch SDSS galaxy sample with photometry and spectroscopic redshifts."""
    t0 = time.time()
    query = f"""
    SELECT TOP {limit}
        p.objID, p.ra, p.dec, p.u, p.g, p.r, p.i, p.z,
        s.z as redshift, s.zErr, s.class, s.subClass,
        p.petroMag_r, p.extinction_r
    FROM PhotoObj AS p
    JOIN SpecObj AS s ON s.bestobjid = p.objid
    WHERE s.class = 'GALAXY' AND s.z BETWEEN 0.01 AND 0.5
        AND p.r BETWEEN 14 AND 17.5
        AND p.clean = 1
    """
    try:
        r = requests.get(SDSS_API, params={'cmd': query}, timeout=TIMEOUT)
        r.raise_for_status()
        # SDSS returns JSON array
        text = r.text.strip()
        if text.startswith('['):
            tables = json.loads(text)
        else:
            return DataResult(source="SDSS DR18", query=query.strip(),
                              data=np.array([]), metadata={'error': 'Unexpected format'},
                              fetch_time=time.time() - t0)

        rows = tables[0].get('Rows', []) if tables else []

        records = []
        for row in rows:
            z = _safe_float(row.get('redshift'))
            u = _safe_float(row.get('u'))
            g = _safe_float(row.get('g'))
            r_mag = _safe_float(row.get('r'))
            i = _safe_float(row.get('i'))
            z_mag = _safe_float(row.get('z'))
            petro_r = _safe_float(row.get('petroMag_r'))

            if z and g and r_mag and u and i and z_mag:
                records.append({
                    'ra': _safe_float(row.get('ra')) or 0,
                    'dec': _safe_float(row.get('dec')) or 0,
                    'redshift': z,
                    'u': u, 'g': g, 'r': r_mag, 'i': i, 'z_band': z_mag,
                    'u_g': u - g, 'g_r': g - r_mag,
                    'petro_r': petro_r,
                })

        data = np.array([(r['redshift'], r['u'], r['g'], r['r'], r['i'], r['z_band'],
                          r['u_g'], r['g_r'])
                         for r in records],
                        dtype=[('redshift', 'f8'), ('u', 'f8'), ('g', 'f8'),
                               ('r', 'f8'), ('i', 'f8'), ('z_band', 'f8'),
                               ('u_g', 'f8'), ('g_r', 'f8')])

        return DataResult(
            source="SDSS DR18",
            query=query.strip(),
            data=data,
            metadata={'records': records, 'total': len(records)},
            fetch_time=time.time() - t0,
        )
    except Exception as e:
        logger.error(f"SDSS fetch failed: {e}")
        return DataResult(source="SDSS DR18", query=query.strip(), data=np.array([]),
                          metadata={'error': str(e)}, fetch_time=time.time() - t0)


def fetch_galaxy_redshifts() -> np.ndarray:
    """Fetch spectroscopic redshifts from SDSS."""
    result = fetch_sdss_galaxies()
    if result.data is None or len(result.data) == 0:
        return np.array([])
    return result.data['redshift']


def fetch_galaxy_colors() -> Tuple[np.ndarray, np.ndarray]:
    """Fetch u-g and g-r colors for galaxy classification."""
    result = fetch_sdss_galaxies()
    if result.data is None or len(result.data) == 0:
        return np.array([]), np.array([])
    return result.data['u_g'], result.data['g_r']


# ═══════════════════════════════════════════════════════════════
# VizieR — General catalog access
# ═══════════════════════════════════════════════════════════════

VIZIER_API = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"


def fetch_vizier_query(adql_query: str, limit: int = MAX_ROWS) -> DataResult:
    """Execute a general ADQL query against VizieR."""
    t0 = time.time()
    if 'TOP' not in adql_query.upper():
        adql_query = adql_query.replace('SELECT', f'SELECT TOP {limit}', 1)
    try:
        r = requests.get(VIZIER_API, params={'QUERY': adql_query, 'REQUEST': 'doQuery',
                                              'LANG': 'ADQL', 'FORMAT': 'json'},
                         timeout=TIMEOUT)
        r.raise_for_status()
        result = r.json()
        rows = result.get('data', [])
        return DataResult(
            source="VizieR",
            query=adql_query.strip(),
            data=np.array(rows) if rows else np.array([]),
            metadata={'total': len(rows)},
            fetch_time=time.time() - t0,
        )
    except Exception as e:
        logger.error(f"VizieR query failed: {e}")
        return DataResult(source="VizieR", query=adql_query.strip(),
                          data=np.array([]), metadata={'error': str(e)},
                          fetch_time=time.time() - t0)


# ═══════════════════════════════════════════════════════════════
# arXiv — Literature search
# ═══════════════════════════════════════════════════════════════

ARXIV_API = "http://export.arxiv.org/api/query"


_arxiv_cache: Dict[str, Tuple[float, List[Dict]]] = {}
_arxiv_last_call: float = 0


def search_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Search arXiv for recent papers. Includes caching and rate limit handling."""
    global _arxiv_last_call

    # Check cache first
    cache_key = f"{query}:{max_results}"
    if cache_key in _arxiv_cache:
        ts, papers = _arxiv_cache[cache_key]
        if time.time() - ts < 3600:  # 1 hour cache
            return papers

    # Rate limit: max 1 request per 3 seconds
    elapsed = time.time() - _arxiv_last_call
    if elapsed < 3.0:
        time.sleep(3.0 - elapsed)

    try:
        _arxiv_last_call = time.time()
        r = requests.get(ARXIV_API, params={
            'search_query': query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
        }, timeout=15)

        if r.status_code == 429:
            logger.warning("arXiv rate limited — returning cached or empty")
            return _arxiv_cache.get(cache_key, (0, []))[1]

        r.raise_for_status()

        # Parse Atom XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        papers = []
        for entry in root.findall('atom:entry', ns):
            title_el = entry.find('atom:title', ns)
            summary_el = entry.find('atom:summary', ns)
            published_el = entry.find('atom:published', ns)
            id_el = entry.find('atom:id', ns)

            title = title_el.text.strip().replace('\n', ' ') if title_el is not None and title_el.text else ''
            abstract = summary_el.text.strip().replace('\n', ' ')[:200] if summary_el is not None and summary_el.text else ''
            published = published_el.text[:10] if published_el is not None and published_el.text else ''
            arxiv_id = id_el.text.split('/abs/')[-1] if id_el is not None and id_el.text else ''

            if title:
                papers.append({
                    'title': title,
                    'abstract': abstract + ('...' if len(abstract) == 200 else ''),
                    'published': published,
                    'arxiv_id': arxiv_id,
                })

        _arxiv_cache[cache_key] = (time.time(), papers)
        return papers
    except Exception as e:
        logger.error(f"arXiv search failed: {e}")
        return _arxiv_cache.get(cache_key, (0, []))[1]


def search_arxiv_astroph(topic: str, max_results: int = 3) -> List[Dict]:
    """Search arXiv for astrophysics papers on a topic."""
    return search_arxiv(f"abs:{topic}", max_results)


# ═══════════════════════════════════════════════════════════════
# Batch fetchers for engine use
# ═══════════════════════════════════════════════════════════════

class RealDataCache:
    """Caches fetched data to avoid hammering APIs every cycle."""

    def __init__(self, ttl: float = 600.0):  # 10-minute TTL
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            ts, data = self._cache[key]
            if time.time() - ts < self._ttl:
                return data
        return None

    def set(self, key: str, data: Any):
        self._cache[key] = (time.time(), data)

    def fetch_or_cache(self, key: str, fetcher, *args, **kwargs):
        cached = self.get(key)
        if cached is not None:
            return cached
        result = fetcher(*args, **kwargs)
        self.set(key, result)
        return result


# Global cache instance — 30 minute TTL to avoid hammering APIs
data_cache = RealDataCache(ttl=1800)


def get_cached_exoplanets() -> DataResult:
    return data_cache.fetch_or_cache("exoplanets", fetch_exoplanets)


def get_cached_pantheon() -> DataResult:
    return data_cache.fetch_or_cache("pantheon", fetch_pantheon_sne)


def get_cached_gaia() -> DataResult:
    return data_cache.fetch_or_cache("gaia", fetch_gaia_stars)


def get_cached_sdss() -> DataResult:
    return data_cache.fetch_or_cache("sdss", fetch_sdss_galaxies)


def get_cached_hr_diagram() -> Tuple[np.ndarray, np.ndarray]:
    return data_cache.fetch_or_cache("hr_diagram", fetch_hr_diagram)


def get_cached_hubble_diagram() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    return data_cache.fetch_or_cache("hubble_diagram", fetch_hubble_diagram)


def get_cached_galaxy_colors() -> Tuple[np.ndarray, np.ndarray]:
    return data_cache.fetch_or_cache("galaxy_colors", fetch_galaxy_colors)
