"""
ASTRA Live — FITS File Reader
Reads and processes FITS files from the data/fits directory.
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np

try:
    from astropy.io import fits
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False


# FITS data directory
FITS_DATA_DIR = Path(__file__).parent.parent / "data" / "fits"


def list_fits_files() -> List[Dict[str, Any]]:
    """
    List all FITS files in the data directory.

    Returns:
        List of dicts with file information
    """
    if not FITS_DATA_DIR.exists():
        return []

    fits_files = []
    for ext in ['*.fits', '*.fit', '*.fts']:
        for filepath in FITS_DATA_DIR.glob(ext):
            stat = filepath.stat()
            fits_files.append({
                'name': filepath.name,
                'path': str(filepath),
                'size_mb': stat.st_size / (1024 * 1024),
                'modified': stat.st_mtime
            })

    return sorted(fits_files, key=lambda x: x['name'])


def read_fits_file(filename: str, hdu: int = 0) -> Optional[Dict[str, Any]]:
    """
    Read a FITS file and return the data and header.

    Args:
        filename: Name of FITS file in data/fits directory
        hdu: Header Data Unit to read (default: 0)

    Returns:
        Dict with 'data' (numpy array) and 'header' (FITS header)
        or None if file not found or astropy not available
    """
    if not ASTROPY_AVAILABLE:
        return {
            'error': 'astropy not installed. Install with: pip install astropy',
            'data': None,
            'header': None
        }

    filepath = FITS_DATA_DIR / filename
    if not filepath.exists():
        return {
            'error': f'File not found: {filename}',
            'data': None,
            'header': None
        }

    try:
        with fits.open(filepath) as hdul:
            data = hdul[hdu].data
            header = hdul[hdu].header

            return {
                'filename': filename,
                'data': data,
                'header': dict(header),
                'shape': data.shape if data is not None else None,
                'dtype': str(data.dtype) if data is not None else None,
                'hdu_count': len(hdul)
            }
    except Exception as e:
        return {
            'error': str(e),
            'data': None,
            'header': None
        }


def get_fits_summary(filename: str) -> Optional[Dict[str, Any]]:
    """
    Get a summary of a FITS file without loading all data.

    Args:
        filename: Name of FITS file

    Returns:
        Dict with file summary information
    """
    if not ASTROPY_AVAILABLE:
        return {'error': 'astropy not installed'}

    filepath = FITS_DATA_DIR / filename
    if not filepath.exists():
        return {'error': f'File not found: {filename}'}

    try:
        with fits.open(filepath) as hdul:
            summaries = []
            for i, hdu in enumerate(hdul):
                summary = {
                    'hdu': i,
                    'type': type(hdu).__name__,
                    'shape': hdu.data.shape if hdu.data is not None else None,
                    'dtype': str(hdu.data.dtype) if hdu.data is not None else None
                }

                # Add header info
                if hasattr(hdu, 'header'):
                    header_keys = list(hdu.header.keys())[:10]  # First 10 keys
                    summary['header_keys'] = header_keys
                    summary['header_count'] = len(hdu.header)

                summaries.append(summary)

            return {
                'filename': filename,
                'hdu_summaries': summaries,
                'total_hdus': len(hdul)
            }
    except Exception as e:
        return {'error': str(e)}


def fits_to_numpy(filename: str, hdu: int = 0) -> Optional[np.ndarray]:
    """
    Quick helper to get numpy array from FITS file.

    Args:
        filename: Name of FITS file
        hdu: HDU to read

    Returns:
        Numpy array or None if error
    """
    result = read_fits_file(filename, hdu=hdu)
    if result and 'data' in result and result['data'] is not None:
        return result['data']
    return None


# Data source registration helper
def register_local_fits_sources():
    """
    Register FITS files from data/fits as data sources.
    This can be called during engine initialization.
    """
    from .data_registry import DataSource, SourceSchema, Domain, ColumnSchema

    sources = []

    for fits_file in list_fits_files():
        # Get basic info
        summary = get_fits_summary(fits_file['name'])
        if summary and 'hdu_summaries' in summary:
            # Create a data source for each FITS file
            def make_fetcher(fname):
                def fetch(**kwargs):
                    result = read_fits_file(fname)
                    if result and result['data'] is not None:
                        from .data_registry import DataResult
                        return DataResult(
                            source=fname,
                            query=f"local_fits:{fname}",
                            data=result['data'],
                            metadata={'header': result.get('header', {})}
                        )
                    else:
                        from .data_registry import DataResult
                        return DataResult(
                            source=fname,
                            query=f"local_fits:{fname}",
                            data=None,
                            metadata={'error': result.get('error', 'Unknown error')}
                        )
                return fetch

            sources.append({
                'id': f"fits_{fits_file['name']}",
                'filename': fits_file['name'],
                'size_mb': fits_file['size_mb'],
                'fetcher': make_fetcher(fits_file['name'])
            })

    return sources
