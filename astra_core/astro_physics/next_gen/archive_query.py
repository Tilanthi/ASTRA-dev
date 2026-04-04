"""
Archive Query Interfaces

Provides unified access to major astronomical archives via VO/TAP protocols
and astroquery interfaces.

Supported Archives:
- MAST (HST, JWST, TESS, Kepler)
- ESO Archive (VLT, ALMA, VISTA)
- IRSA (Spitzer, WISE, 2MASS, Herschel)
- CDS/VizieR (catalogs, cross-matching)
- Gaia Archive (astrometry, photometry, RVS)
- CADC (CFHT, JCMT, Gemini)
- NRAO Archive (VLA, ALMA, GBT)
- NED (extragalactic cross-IDs)
- Simbad (object queries)

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

try:
    from astropy.coordinates import SkyCoord
    from astropy import units as u
    from astropy.table import Table, vstack
    from astropy.time import Time
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False

try:
    from astroquery.vizier import Vizier
    from astroquery.simbad import Simbad
    from astroquery.ned import Ned
    from astroquery.gaia import Gaia
    from astroquery.mast import Observations as MASTObs
    from astroquery.ipac.irsa import Irsa
    from astroquery.eso import Eso
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False


class ArchiveType(Enum):
    """Supported astronomical archives"""
    VIZIER = "vizier"
    SIMBAD = "simbad"
    NED = "ned"
    GAIA = "gaia"
    MAST = "mast"
    IRSA = "irsa"
    ESO = "eso"
    CADC = "cadc"
    NRAO = "nrao"


@dataclass
class QueryResult:
    """Container for archive query results"""
    archive: str
    query_type: str
    n_results: int
    table: Any  # astropy Table
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def __repr__(self):
        return f"QueryResult({self.archive}, {self.n_results} results)"


@dataclass
class ConeSearchParams:
    """Parameters for cone search queries"""
    ra: float  # degrees
    dec: float  # degrees
    radius: float  # arcmin
    catalog: Optional[str] = None
    columns: Optional[List[str]] = None
    row_limit: int = 10000


@dataclass
class CrossMatchParams:
    """Parameters for cross-matching queries"""
    ra_col: str = "ra"
    dec_col: str = "dec"
    radius: float = 1.0  # arcsec
    join_type: str = "best"  # 'best', 'all', or distance threshold


class TAP_Client:
    """
    Table Access Protocol (TAP) client for VO-compliant archives.

    Supports ADQL queries to any TAP endpoint.
    """

    # Standard TAP endpoints
    TAP_ENDPOINTS = {
        'gaia': 'https://gea.esac.esa.int/tap-server/tap',
        'vizier': 'http://tapvizier.u-strasbg.fr/TAPVizieR/tap',
        'cadc': 'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/tap',
        'eso': 'http://archive.eso.org/tap_obs',
        'mast': 'https://mast.stsci.edu/vo-tap/api/v0.1',
        'ned': 'https://ned.ipac.caltech.edu/tap',
    }

    def __init__(self, endpoint: str = None, archive: str = None):
        """
        Initialize TAP client.

        Args:
            endpoint: Direct TAP endpoint URL
            archive: Archive name (uses predefined endpoint)
        """
        if endpoint:
            self.endpoint = endpoint
        elif archive and archive.lower() in self.TAP_ENDPOINTS:
            self.endpoint = self.TAP_ENDPOINTS[archive.lower()]
        else:
            raise ValueError(f"Specify endpoint URL or archive from: {list(self.TAP_ENDPOINTS.keys())}")

        self.archive = archive or "custom"

    def query(self, adql: str, maxrec: int = 10000) -> QueryResult:
        """
        Execute ADQL query.

        Args:
            adql: ADQL query string
            maxrec: Maximum records to return

        Returns:
            QueryResult with table
        """
        if not ASTROQUERY_AVAILABLE:
            raise ImportError("astroquery required for TAP queries")

        from astroquery.utils.tap.core import TapPlus

        tap = TapPlus(url=self.endpoint)
        job = tap.launch_job(adql, maxrec=maxrec)
        result_table = job.get_results()

        return QueryResult(
            archive=self.archive,
            query_type="TAP/ADQL",
            n_results=len(result_table),
            table=result_table,
            metadata={'adql': adql, 'endpoint': self.endpoint}
        )

    def cone_search(self, ra: float, dec: float, radius: float,
                    table: str, columns: str = "*") -> QueryResult:
        """
        Cone search via TAP.

        Args:
            ra, dec: Center coordinates (degrees)
            radius: Search radius (arcmin)
            table: Table name to query
            columns: Columns to return

        Returns:
            QueryResult
        """
        adql = f"""
        SELECT {columns}
        FROM {table}
        WHERE 1=CONTAINS(
            POINT('ICRS', ra, dec),
            CIRCLE('ICRS', {ra}, {dec}, {radius/60.0})
        )
        """
        return self.query(adql)


class VOQueryEngine:
    """
    High-level Virtual Observatory query engine.

    Provides unified interface to multiple archives with automatic
    protocol selection.
    """

    def __init__(self):
        """Initialize VO query engine with available services"""
        self.available_services = []

        if ASTROQUERY_AVAILABLE:
            self.available_services.extend([
                'vizier', 'simbad', 'ned', 'gaia', 'mast', 'irsa'
            ])

        self._cache = {}

    def resolve_name(self, name: str) -> Tuple[float, float]:
        """
        Resolve object name to coordinates.

        Args:
            name: Object name (e.g., "M31", "NGC 1068")

        Returns:
            (ra, dec) in degrees
        """
        if not ASTROQUERY_AVAILABLE:
            raise ImportError("astroquery required for name resolution")

        result = Simbad.query_object(name)
        if result is None:
            # Try NED
            result = Ned.query_object(name)
            if result is None:
                raise ValueError(f"Could not resolve: {name}")
            ra = result['RA'][0]
            dec = result['DEC'][0]
        else:
            coord = SkyCoord(
                result['RA'][0], result['DEC'][0],
                unit=(u.hourangle, u.deg)
            )
            ra, dec = coord.ra.deg, coord.dec.deg

        return ra, dec

    def query_region(self, ra: float, dec: float, radius: float,
                     archives: List[str] = None,
                     catalogs: Dict[str, List[str]] = None) -> Dict[str, QueryResult]:
        """
        Query multiple archives for a sky region.

        Args:
            ra, dec: Center coordinates (degrees)
            radius: Search radius (arcmin)
            archives: List of archives to query (default: all available)
            catalogs: Dict mapping archive to specific catalogs

        Returns:
            Dict mapping archive name to QueryResult
        """
        if not ASTROPY_AVAILABLE:
            raise ImportError("astropy required")

        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
