"""
Automated Archive Exploration Agent (AAEA)
=========================================

Autonomously explores astronomical data archives:
- NASA archives (IRSA, HEASARC, MAST)
- ESO archives
- ALMA data archive
- Virtual Observatory (VO) services

Capabilities:
- Semantic query ("all molecular cloud observations with CO and dust")
- Cross-archive correlation
- Automated download and preprocessing
- Intelligent caching

Author: STAN-XI ASTRO V100 Development Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum, auto
import os
import json
import hashlib
import time
from pathlib import Path
import numpy as np
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET


# =============================================================================
# Enumerations
# =============================================================================

class ArchiveSource(Enum):
    """Available astronomical archives"""
    IRSA = "irsa"  # NASA/IPAC Infrared Science Archive
    HEASARC = "heasarc"  # High Energy Astrophysics Science Archive
    MAST = "mast"  # Barbara A. Mikulski Archive for Space Telescopes
    ESO = "eso"  # European Southern Observatory
    ALMA = "alma"  # Atacama Large Millimeter Array
    VAO = "vao"  # Virtual Astronomical Observatory
    SIMBAD = "simbad"  # SIMBAD astronomical database
    NED = "ned"  # NASA/IPAC Extragalactic Database
    GAIA = "gaia"  # Gaia archive
    PLANCK = "planck"  # Planck legacy archive
    HERSCHEL = "herschel"  # Herschel Science Archive


class DataType(Enum):
    """Types of astronomical data"""
    IMAGE = "image"
    CATALOG = "catalog"
    SPECTRUM = "spectrum"
    TIME_SERIES = "time_series"
    SPECTRAL_CUBE = "spectral_cube"
    POLARIZATION = "polarization"
    TABLE = "table"
    VISIBILITY = "visibility"


class DataFormat(Enum):
    """File formats"""
    FITS = "fits"
    VOTABLE = "votable"
    JSON = "json"
    CSV = "csv"
    HDF5 = "hdf5"


# =============================================================================
# Core Data Structures
# =============================================================================

@dataclass
class ArchiveQuery:
    """A query to an astronomical archive"""
    id: str
    source: ArchiveSource
    query_type: str  # 'semantic', 'adql', 'cone_search', 'cross_match'
    parameters: Dict[str, Any] = field(default_factory=dict)

    # For cone search
    ra_deg: Optional[float] = None
    dec_deg: Optional[float] = None
    radius_deg: Optional[float] = None

    # For ADQL
    adql_query: Optional[str] = None

    # For semantic query
    natural_language: Optional[str] = None
    interpreted_keywords: List[str] = field(default_factory=list)


@dataclass
class DataProduct:
    """A single data product (file or table)"""
    id: str
    archive: ArchiveSource
    title: str
    data_type: DataType
    format: DataFormat

    # Access information
    url: Optional[str] = None
    file_size_bytes: Optional[int] = None

    # Metadata
    obs_id: Optional[str] = None
    instrument: Optional[str] = None
    wavelength_range: Optional[Tuple[float, float]] = None  # microns
    coverage: Optional[Dict[str, float]] = None  # ra_min, ra_max, dec_min, dec_max
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    # Preview
    preview_url: Optional[str] = None

    # Local cache
    local_path: Optional[str] = None
    downloaded: bool = False


@dataclass
class DatasetCollection:
    """A collection of related data products"""
    id: str
    name: str
    description: str
    data_products: List[DataProduct] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_product(self, product: DataProduct):
        """Add a data product to the collection"""
        self.data_products.append(product)

    def get_summary(self) -> Dict[str, Any]:
        """Get collection summary"""
        return {
            'id': self.id,
            'name': self.name,
            'n_products': len(self.data_products),
            'archives': list(set(p.archive.value for p in self.data_products)),
            'types': list(set(p.data_type.value for p in self.data_products)),
            'total_size_gb': sum(p.file_size_bytes or 0 for p in self.data_products) / 1e9,
        }


# =============================================================================
# Archive Explorer
# =============================================================================

class ArchiveExplorer:
    """
    Explores astronomical data archives autonomously.

    Features:
    - Semantic query parsing
    - Multi-archive search
    - Intelligent caching
    - Cross-archive correlation
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/data/cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        self.cached_queries: Dict[str, DatasetCollection] = {}
        self.downloaded_files: Dict[str, str] = {}

        # Archive endpoints
        self.endpoints = {
            ArchiveSource.IRSA: "https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query",
            ArchiveSource.MAST: "https://archive.stsci.edu/search.php",
            ArchiveSource.ESO: "http://archive.eso.org/wdb/wdb/eso/eso_archive_main/query",
            ArchiveSource.ALMA: "https://almascience.eso.org/aq/",
            ArchiveSource.SIMBAD: "http://simbad.u-strasbg.fr/simbad/sim-script",
            ArchiveSource.VAO: "http://vao.stsci.edu/keyword-search",
        }

        # Domain keywords for semantic parsing
        self.domain_keywords = {
            'ism': ['filament', 'molecular_cloud', 'ism', 'interstellar', 'dust',
                    'hii_region', 'bok_globule', 'dark_cloud'],
            'star_formation': ['protostar', 'yso', 'prestellar_core', 'star_formation',
                             'young_stellar_object', 'outflow', 'jet'],
            'galaxies': ['galaxy', 'spiral', 'elliptical', 'irregular', 'merger'],
            'agn': ['quasar', 'active_galactic', 'agn', 'seyfert', 'blazar'],
            'cosmology': ['cosmic_microwave', 'cmb', 'supernova', 'ia_supernova',
                         'galaxy_cluster'],
        }

    def explore(
        self,
        science_question: str,
        hypothesis: Optional[Any] = None,  # TheoryFramework when integrated
        max_data_volume_tb: float = 10.0,
        target_archives: Optional[List[ArchiveSource]] = None
    ) -> DatasetCollection:
        """
        Autonomous data discovery and collection.

        Parameters
        ----------
        science_question : str
            Natural language science question
        hypothesis : TheoryFramework, optional
            Hypothesis to test
        max_data_volume_tb : float
            Maximum data to download
        target_archives : list, optional
            Specific archives to query

        Returns
        -------
        DatasetCollection with relevant data
        """
        print(f"AAEA: Exploring archives for: {science_question}")

        # Parse science question into observables
        observables = self._parse_science_question(science_question)
        print(f"  Identified observables: {observables}")

        # Select relevant archives
        if target_archives:
            archives = target_archives
        else:
            archives = self._select_archives(observables)
        print(f"  Selected archives: {[a.value for a in archives]}")

        # Query each archive
        all_products = []
        for archive in archives:
            print(f"  Querying {archive.value}...")
            products = self._query_archive(archive, observables)
            all_products.extend(products)
            print(f"    Found {len(products)} products")

        # Create collection
        collection = DatasetCollection(
            id=f"collection_{int(time.time())}",
            name=f"Data for: {science_question[:50]}",
            description=science_question,
            data_products=all_products
        )

        # Rank by relevance
        collection.data_products = self._rank_products(
            collection.data_products,
            observables
        )

        print(f"  Total: {len(collection.data_products)} products")
        return collection

    def _parse_science_question(self, question: str) -> Dict[str, Any]:
        """Parse natural language science question"""
        observables = {
            'objects': [],
            'wavelengths': [],
            'instruments': [],
            'regions': [],
            'data_types': [],
        }

        question_lower = question.lower()

        # Parse objects
        for domain, keywords in self.domain_keywords.items():
            if any(kw in question_lower for kw in keywords):
                observables['objects'].extend([kw for kw in keywords if kw in question_lower])

        # Parse wavelengths
        wavelength_map = {
            'radio': ['radio', 'cm', 'ghz'],
            'mm': ['mm', 'submm', 'millimeter'],
            'far_ir': ['far_ir', 'fir', '250µm', '350µm', '500µm', 'spire'],
            'mid_ir': ['mid_ir', 'mir', 'wise', 'spitzer'],
            'near_ir': ['near_ir', 'nir', '2mass'],
            'optical': ['optical', 'visible'],
            'uv': ['uv', 'ultraviolet'],
            'xray': ['xray', 'x-ray', 'chandra'],
        }

        for wave_name, keywords in wavelength_map.items():
            if any(kw in question_lower for kw in keywords):
                observables['wavelengths'].append(wave_name)

        # Parse instruments
        instruments = ['alma', 'vla', 'jwst', 'hst', 'herschel', 'planck',
                      'chandra', 'xmm', 'spitzer', 'wise', 'gaia', 'vlt']
        for inst in instruments:
            if inst in question_lower:
                observables['instruments'].append(inst)

        # Parse regions
        if 'cygnus' in question_lower:
            observables['regions'].append('cygnus')
        if 'orion' in question_lower:
            observables['regions'].append('orion')
        if 'taurus' in question_lower:
            observables['regions'].append('taurus')

        return observables

    def _select_archives(self, observables: Dict[str, Any]) -> List[ArchiveSource]:
        """Select relevant archives based on observables"""
        archives = []

        # IRSA for infrared data
        if any(w in observables['wavelengths'] for w in ['far_ir', 'mid_ir']):
            archives.append(ArchiveSource.IRSA)

        # HEASARC for high energy
        if 'xray' in observables['wavelengths']:
            archives.append(ArchiveSource.HEASARC)

        # ALMA for mm/submm
        if 'mm' in observables['wavelengths']:
            archives.append(ArchiveSource.ALMA)

        # MAST for space telescopes
        if any(inst in observables['instruments'] for inst in ['hst', 'jwst', 'spitzer']):
            archives.append(ArchiveSource.MAST)

        # ESO for ground-based
        if 'vlt' in observables['instruments']:
            archives.append(ArchiveSource.ESO)

        # Planck for CMB
        if 'planck' in observables['instruments']:
            archives.append(ArchiveSource.PLANCK)

        # Default to IRSA and MAST if nothing specific
        if not archives:
            archives = [ArchiveSource.IRSA, ArchiveSource.MAST]

        return archives

    def _query_archive(
        self,
        archive: ArchiveSource,
        observables: Dict[str, Any]
    ) -> List[DataProduct]:
        """Query a specific archive"""
        products = []

        # Simulate query results for demonstration
        # In production, would use actual API calls

        if archive == ArchiveSource.IRSA:
            # IRSA has Herschel, Spitzer, WISE data
            if 'cygnus' in observables['regions']:
                products.append(DataProduct(
                    id=f"hirgel_cygnus_{archive.value}",
                    archive=archive,
                    title="HIGAL Cygnus Field",
                    data_type=DataType.IMAGE,
                    format=DataFormat.FITS,
                    url="https://irsa.ipac.caltech.edu/data/Herschel/HIGAL/",
                    file_size_bytes=500_000_000,
                    instrument='Herschel/SPIRE',
                    wavelength_range=(250, 500),
                ))
                products.append(DataProduct(
                    id=f"planck_cygnus_{archive.value}",
                    archive=archive,
                    title="Planck Polarization Cygnus",
                    data_type=DataType.POLARIZATION,
                    format=DataFormat.FITS,
                    url="https://irsa.ipac.caltech.edu/data/Planck/",
                    file_size_bytes=200_000_000,
                    instrument='Planck',
                    wavelength_range=(850, 850),
                ))

        elif archive == ArchiveSource.ALMA:
            if 'cygnus' in observables['regions']:
                products.append(DataProduct(
                    id=f"alma_cygnus_{archive.value}",
                    archive=archive,
                    title="ALMA Cygnus X Survey",
                    data_type=DataType.SPECTRAL_CUBE,
                    format=DataFormat.FITS,
                    url="https://almascience.eso.org/",
                    file_size_bytes=1_000_000_000,
                    instrument='ALMA',
                    wavelength_range=(3000, 3000),
                ))

        # Add generic products for demonstration
        products.append(DataProduct(
            id=f"generic_{archive.value}_{int(time.time())}",
            archive=archive,
            title=f"Data from {archive.value}",
            data_type=DataType.CATALOG,
            format=DataFormat.VOTABLE,
            url=f"https://{archive.value}.edu/",
        ))

        return products

    def _rank_products(
        self,
        products: List[DataProduct],
        observables: Dict[str, Any]
    ) -> List[DataProduct]:
        """Rank products by relevance"""
        scored_products = []

        for product in products:
            score = 0.0

            # Match wavelength preference
            if product.wavelength_range:
                for wave in observables['wavelengths']:
                    if wave == 'mm' and 300 < product.wavelength_range[0] < 10000:
                        score += 0.3
                    elif wave == 'far_ir' and 60 < product.wavelength_range[0] < 500:
                        score += 0.3

            # Match instrument preference
            if product.instrument:
                for inst in observables['instruments']:
                    if inst.lower() in product.instrument.lower():
                        score += 0.4

            # Prefer FITS format
            if product.format == DataFormat.FITS:
                score += 0.1

            # Prefer polarization data for magnetic questions
            if product.data_type == DataType.POLARIZATION:
                score += 0.2

            product.metadata['relevance_score'] = score
            scored_products.append((product, score))

        # Sort by score
        scored_products.sort(key=lambda x: x[1], reverse=True)

        return [p for p, s in scored_products]

    def download_product(
        self,
        product: DataProduct,
        local_dir: Optional[str] = None
    ) -> str:
        """Download a data product to local cache"""
        if product.local_path:
            return product.local_path

        if local_dir is None:
            local_dir = os.path.join(self.cache_dir, product.archive.value)

        os.makedirs(local_dir, exist_ok=True)

        # Simulate download (in production, would use actual HTTP request)
        filename = f"{product.id}.{product.format.value}"
        local_path = os.path.join(local_dir, filename)

        # Create dummy file
        with open(local_path, 'w') as f:
            f.write(f"# Simulated download from {product.url}\n")

        product.local_path = local_path
        product.downloaded = True

        print(f"  Downloaded {product.id} to {local_path}")
        return local_path

    def create_observation_query(
        self,
        ra_deg: float,
        dec_deg: float,
        radius_deg: float,
        source: ArchiveSource = ArchiveSource.IRSA
    ) -> ArchiveQuery:
        """Create a cone search query"""
        return ArchiveQuery(
            id=f"cone_search_{int(time.time())}",
            source=source,
            query_type="cone_search",
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            radius_deg=radius_deg
        )

    def create_adql_query(
        self,
        adql: str,
        source: ArchiveSource = ArchiveSource.IRSA
    ) -> ArchiveQuery:
        """Create an ADQL query"""
        return ArchiveQuery(
            id=f"adql_{int(time.time())}",
            source=source,
            query_type="adql",
            adql_query=adql
        )


# =============================================================================
# Factory Functions
# =============================================================================

def create_archive_explorer(cache_dir: Optional[str] = None) -> ArchiveExplorer:
    """Create an archive explorer"""
    return ArchiveExplorer(cache_dir=cache_dir)


# =============================================================================
# Convenience Functions
# =============================================================================

def explore_archives(
    science_question: str,
    max_data_tb: float = 10.0
) -> DatasetCollection:
    """
    Convenience function to explore archives.

    Parameters
    ----------
    science_question : str
        Natural language question
    max_data_tb : float
        Maximum data to download

    Returns
    -------
    DatasetCollection with relevant data
    """
    explorer = create_archive_explorer()
    return explorer.explore(science_question, max_data_volume_tb=max_data_tb)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'ArchiveSource',
    'DataType',
    'DataFormat',
    'ArchiveQuery',
    'DataProduct',
    'DatasetCollection',
    'ArchiveExplorer',
    'create_archive_explorer',
    'explore_archives',
]
