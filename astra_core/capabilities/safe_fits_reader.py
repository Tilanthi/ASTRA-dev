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
Enhanced FITS Data Reader with Comprehensive Bounds Checking

This module provides safe access to FITS astronomical data cubes with
built-in boundary validation and error handling.

Features:
- Automatic bounds checking for all array access
- Clear error messages for invalid operations
- Graceful handling of edge cases
- Coordinate system validation

Date: 2026-03-19
Version: 1.0
"""

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class DataCubeInfo:
    """Information about a FITS data cube"""
    n_freq: int
    n_dec: int
    n_ra: int
    shape: Tuple[int, int, int]
    freq_range: Tuple[float, float]  # GHz
    vel_range: Tuple[float, float]   # km/s
    ra_range: Tuple[float, float]    # degrees
    dec_range: Tuple[float, float]   # degrees
    pixel_scale: Tuple[float, float] # arcsec/pixel (RA, Dec)
    header: Dict[str, Any]


class SafeFITSReader:
    """
    Safe FITS file reader with comprehensive bounds checking.
    """

    def __init__(self, filepath: str):
        """
        Initialize the reader and load the FITS file.

        Args:
            filepath: Path to the FITS file

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
            ValueError: If file format is invalid
        """
        self.filepath = filepath

        try:
            with fits.open(filepath) as hdul:
                self.data = hdul[0].data
                # Store header as dict to avoid issues with non-ASCII characters
                self.header = dict(hdul[0].header)
        except FileNotFoundError:
            raise FileNotFoundError(f"FITS file not found: {filepath}")
        except Exception as e:
            raise IOError(f"Error reading FITS file {filepath}: {e}")

        # Validate data shape
        if self.data.ndim != 3:
            raise ValueError(f"Expected 3D data cube, got shape {self.data.shape}")

        # Get dimensions
        self._n_freq, self._n_dec, self._n_ra = self.data.shape

        # Initialize WCS - create from the file directly to avoid header issues
        try:
            with fits.open(filepath) as hdul:
                self.wcs = WCS(hdul[0].header)
                self.wcs_2d = self.wcs.celestial
        except Exception as e:
            # Fallback: manually construct WCS from keywords
            try:
                self.wcs = WCS(naxis=3)
                self.wcs.wcs.ctype = [self.header.get('CTYPE1', 'RA---TAN'),
                                        self.header.get('CTYPE2', 'DEC--TAN'),
                                        self.header.get('CTYPE3', 'FREQ')]
                self.wcs.wcs.crval = [self.header.get('CRVAL1', 0),
                                        self.header.get('CRVAL2', 0),
                                        self.header.get('CRVAL3', 0)]
                self.wcs.wcs.crpix = [self.header.get('CRPIX1', 1),
                                        self.header.get('CRPIX2', 1),
                                        self.header.get('CRPIX3', 1)]
                self.wcs.wcs.cdelt = [self.header.get('CDELT1', 1),
                                        self.header.get('CDELT2', 1),
                                        self.header.get('CDELT3', 1)]
                self.wcs_2d = self.wcs.celestial
            except Exception as e2:
                raise ValueError(f"Error creating WCS from header: {e}")

        # Pre-compute coordinate information
        self._setup_coordinate_info()

        # Cache for spectra
        self._spectrum_cache: Dict[Tuple[int, int], np.ndarray] = {}

    def _setup_coordinate_info(self):
        """Set up coordinate system information."""
        # Frequency/velocity axis
        try:
            wcs_freq = self.wcs.sub([3])
            self.frequencies = wcs_freq.array_index_to_world(np.arange(self._n_freq)).value
            if np.max(np.abs(self.frequencies)) > 1000:
                self.frequencies *= 1e-9  # Convert to GHz
        except:
            f0 = self.header.get('CRVAL3', 22235.08)
            df = self.header.get('CDELT3', 0.005)
            if abs(f0) > 1000:
                f0, df = f0/1e9, df/1e9
            self.frequencies = f0 + df * np.arange(self._n_freq)

        # Convert to LSR velocity
        C_LIGHT = 299792.458
        F0_WATER = 22.23508
        self.velocities = C_LIGHT * (F0_WATER - self.frequencies) / F0_WATER

        # Get spatial coordinate ranges
        corners = [
            (0, 0),
            (self._n_ra - 1, 0),
            (0, self._n_dec - 1),
            (self._n_ra - 1, self._n_dec - 1)
        ]
        coords = [self.wcs_2d.pixel_to_world(x, y) for x, y in corners]
        ra_vals = [c.ra.deg for c in coords]
        dec_vals = [c.dec.deg for c in coords]

        # Determine pixel scale (degrees per pixel)
        ra_scale = abs(ra_vals[1] - ra_vals[0]) / max(1, self._n_ra - 1)
        dec_scale = abs(dec_vals[2] - dec_vals[0]) / max(1, self._n_dec - 1)

        self.info = DataCubeInfo(
            n_freq=self._n_freq,
            n_dec=self._n_dec,
            n_ra=self._n_ra,
            shape=self.data.shape,
            freq_range=(self.frequencies[0], self.frequencies[-1]),
            vel_range=(self.velocities[0], self.velocities[-1]),
            ra_range=(min(ra_vals), max(ra_vals)),
            dec_range=(min(dec_vals), max(dec_vals)),
            pixel_scale=(ra_scale * 3600, dec_scale * 3600),  # arcsec
            header=self.header
        )

    # =======================================================================
    # BOUNDS CHECKING METHODS
    # =======================================================================

    def _check_freq_bounds(self, channel: int, name: str = "channel") -> None:
        """Check if frequency channel is within bounds."""
        if not 0 <= channel < self._n_freq:
            raise IndexError(
                f"{name} {channel} out of bounds [0, {self._n_freq-1}]"
            )

    def _check_spatial_bounds(self, x: int, y: int) -> None:
        """Check if spatial pixel coordinates are within bounds."""
        if x < 0 or x >= self._n_ra:
            raise IndexError(
                f"RA pixel x={x} out of bounds [0, {self._n_ra-1}]"
            )
        if y < 0 or y >= self._n_dec:
            raise IndexError(
                f"Dec pixel y={y} out of bounds [0, {self._n_dec-1}]"
            )

    def _check_coord_bounds(self, ra_deg: float, dec_deg: float) -> bool:
        """Check if sky coordinates are within the field of view."""
        ra_min, ra_max = self.info.ra_range
        dec_min, dec_max = self.info.dec_range

        # Handle RA wrapping
        if ra_min > ra_max:  # Crosses 0/360 boundary
            in_ra = ra_deg >= ra_min or ra_deg <= ra_max
        else:
            in_ra = ra_min <= ra_deg <= ra_max

        in_dec = dec_min <= dec_deg <= dec_max

        return in_ra and in_dec

    def _check_spectrum_bounds(self, spectrum: np.ndarray) -> bool:
        """Check if spectrum has valid data."""
        return len(spectrum) == self._n_freq and np.sum(~np.isnan(spectrum)) > 0

    # =======================================================================
    # SAFE DATA ACCESS METHODS
    # =======================================================================

    def get_spectrum_at_pixel(self, x: int, y: int,
                              check_bounds: bool = True) -> np.ndarray:
        """
        Get spectrum at pixel coordinates with bounds checking.

        Args:
            x: RA pixel coordinate
            y: Dec pixel coordinate
            check_bounds: Whether to validate bounds (default True)

        Returns:
            Spectrum array (n_freq,)

        Raises:
            IndexError: If coordinates out of bounds
        """
        if check_bounds:
            self._check_spatial_bounds(x, y)

        spectrum = self.data[:, y, x].astype(float)
        return spectrum

    def get_spectrum_at_coords(self, ra_deg: float, dec_deg: float,
                                check_coords: bool = True,
                                check_bounds: bool = True) -> Tuple[np.ndarray, int, int]:
        """
        Get spectrum at sky coordinates with validation.

        Args:
            ra_deg: Right ascension in degrees
            dec_deg: Declination in degrees
            check_coords: Validate coordinates within FOV
            check_bounds: Validate pixel bounds after conversion

        Returns:
            (spectrum, x_pixel, y_pixel)

        Raises:
            ValueError: If coordinates outside field of view
            IndexError: If converted pixels out of bounds
        """
        coord = SkyCoord(ra=ra_deg*u.degree, dec=dec_deg*u.degree)

        if check_coords and not self._check_coord_bounds(ra_deg, dec_deg):
            ra_str = coord.ra.to_string(unit='hour', sep='hms')
            dec_str = coord.dec.to_string(unit='deg', sep='dms')
            raise ValueError(
                f"Coordinates ({ra_str}, {dec_str}) outside field of view:\n"
                f"  FOV: RA [{self.info.ra_range[0]:.4f}, {self.info.ra_range[1]:.4f}] deg, "
                f"Dec [{self.info.dec_range[0]:.4f}, {self.info.dec_range[1]:.4f}] deg"
            )

        result = self.wcs_2d.world_to_pixel(coord)
        x_int = int(round(float(result[0])))
        y_int = int(round(float(result[1])))

        if check_bounds:
            self._check_spatial_bounds(x_int, y_int)

        spectrum = self.data[:, y_int, x_int].astype(float)
        return spectrum, x_int, y_int

    def get_spectrum_safe(self, ra_deg: float, dec_deg: float) -> Optional[np.ndarray]:
        """
        Get spectrum safely, returning None if out of bounds.

        Args:
            ra_deg: Right ascension in degrees
            dec_deg: Declination in degrees

        Returns:
            Spectrum array or None if out of bounds/invalid
        """
        try:
            spectrum, x, y = self.get_spectrum_at_coords(
                ra_deg, dec_deg, check_coords=True, check_bounds=True
            )
            if self._check_spectrum_bounds(spectrum):
                return spectrum
        except (ValueError, IndexError):
            pass
        return None

    def get_valid_pixel_near(self, ra_deg: float, dec_deg: float,
                            max_radius: int = 50,
                            min_valid_channels: int = 10) -> Optional[Tuple[np.ndarray, int, int]]:
        """
        Find nearest valid pixel to given coordinates.

        Args:
            ra_deg: Target RA in degrees
            dec_deg: Target Dec in degrees
            max_radius: Maximum search radius in pixels
            min_valid_channels: Minimum non-NaN channels required

        Returns:
            (spectrum, x, y) of nearest valid pixel, or None
        """
        coord = SkyCoord(ra=ra_deg*u.degree, dec=dec_deg*u.degree)
        result = self.wcs_2d.world_to_pixel(coord)
        x0, y0 = int(round(float(result[0]))), int(round(float(result[1])))

        # Check if target is already valid
        if (0 <= x0 < self._n_ra and 0 <= y0 < self._n_dec):
            spec = self.data[:, y0, x0]
            if np.sum(~np.isnan(spec)) >= min_valid_channels:
                return spec.astype(float), x0, y0

        # Search outward
        for radius in range(1, max_radius + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    x, y = x0 + dx, y0 + dy
                    if 0 <= x < self._n_ra and 0 <= y < self._n_dec:
                        spec = self.data[:, y, x]
                        if np.sum(~np.isnan(spec)) >= min_valid_channels:
                            return spec.astype(float), x, y

        return None

    # =======================================================================
    # BULK OPERATIONS WITH BOUNDS CHECKING
    # =======================================================================

    def find_sources(self,
                    threshold: float,
                    min_channels: int,
                    max_sources: int = None) -> List[Dict[str, Any]]:
        """
        Find all maser sources with specified criteria.

        Args:
            threshold: Intensity threshold in Jy
            min_channels: Minimum consecutive channels above threshold
            max_sources: Maximum number of sources to return

        Returns:
            List of source dictionaries with coordinates and spectra
        """
        sources = []

        for y in range(self._n_dec):
            for x in range(self._n_ra):
                spectrum = self.data[:, y, x]

                # Skip if mostly NaN
                if np.sum(~np.isnan(spectrum)) < min_channels:
                    continue

                # Check for consecutive channels above threshold
                max_consecutive = 0
                current_consecutive = 0
                for val in spectrum:
                    if not np.isnan(val) and val > threshold:
                        current_consecutive += 1
                        max_consecutive = max(max_consecutive, current_consecutive)
                    else:
                        current_consecutive = 0

                if max_consecutive >= min_channels:
                    peak = np.nanmax(spectrum)
                    peak_idx = np.argmax(spectrum)
                    peak_vel = self.velocities[peak_idx]

                    coord = self.wcs_2d.pixel_to_world(x, y)

                    sources.append({
                        'x': x,
                        'y': y,
                        'ra': coord.ra.deg,
                        'dec': coord.dec.deg,
                        'ra_str': coord.ra.to_string(unit='hour', sep='hms', precision=1),
                        'dec_str': coord.dec.to_string(unit='deg', sep='dms', precision=0),
                        'peak': peak,
                        'peak_vel': peak_vel,
                        'n_channels': max_consecutive,
                        'spectrum': spectrum.copy()
                    })

                    if max_sources and len(sources) >= max_sources:
                        return sources

        return sources

    def filter_by_separation(self,
                            sources: List[Dict[str, Any]],
                            separation_arcsec: float) -> List[Dict[str, Any]]:
        """
        Filter sources to keep only brightest within separation radius.

        Args:
            sources: List of source dictionaries
            separation_arcsec: Minimum separation in arcseconds

        Returns:
            Filtered list of sources
        """
        if not sources:
            return []

        # Create coordinate arrays
        sky_coords = SkyCoord(
            ra=[s['ra'] for s in sources]*u.degree,
            dec=[s['dec'] for s in sources]*u.degree
        )
        peaks = np.array([s['peak'] for s in sources])

        # Calculate separation matrix
        separations = sky_coords.separation(sky_coords[:, np.newaxis]).arcsec

        # Filter: keep only brightest within separation radius
        keep_mask = np.ones(len(sources), dtype=bool)

        for i in range(len(sources)):
            if not keep_mask[i]:
                continue

            nearby = np.where((separations[i] < separation_arcsec) &
                             (separations[i] > 0))[0]

            for j in nearby:
                if peaks[j] <= peaks[i]:
                    keep_mask[j] = False

        return [sources[i] for i in range(len(sources)) if keep_mask[i]]

    # =======================================================================
    # UTILITY METHODS
    # =======================================================================

    def pixel_to_sky(self, x: int, y: int) -> Tuple[float, float]:
        """Convert pixel coordinates to sky coordinates."""
        self._check_spatial_bounds(x, y)
        coord = self.wcs_2d.pixel_to_world(x, y)
        return coord.ra.deg, coord.dec.deg

    def sky_to_pixel(self, ra_deg: float, dec_deg: float) -> Tuple[int, int]:
        """Convert sky coordinates to pixel coordinates."""
        coord = SkyCoord(ra=ra_deg*u.degree, dec=dec_deg*u.degree)
        result = self.wcs_2d.world_to_pixel(coord)
        x_int = int(round(float(result[0])))
        y_int = int(round(float(result[1])))
        return x_int, y_int

    def print_info(self) -> None:
        """Print information about the data cube."""
        print("="*70)
        print("FITS DATA CUBE INFORMATION")
        print("="*70)
        print(f"File: {self.filepath}")
        print(f"\nShape: {self.info.shape}")
        print(f"  Frequency channels: {self.info.n_freq}")
        print(f"  Dec pixels: {self.info.n_dec}")
        print(f"  RA pixels: {self.info.n_ra}")
        print(f"\nCoordinate ranges:")
        print(f"  Frequency: {self.info.freq_range[0]:.6f} - {self.info.freq_range[1]:.6f} GHz")
        print(f"  Velocity: {self.info.vel_range[0]:.2f} - {self.info.vel_range[1]:.2f} km/s")
        print(f"  RA: {self.info.ra_range[0]:.6f} - {self.info.ra_range[1]:.6f} deg")
        print(f"  Dec: {self.info.dec_range[0]:.6f} - {self.info.dec_range[1]:.6f} deg")
        print(f"  Pixel scale: {self.info.pixel_scale[0]:.2f}\" x {self.info.pixel_scale[1]:.2f}\"")
        print("="*70)


# Convenience function
def load_fits(filepath: str) -> SafeFITSReader:
    """
    Load a FITS file with safe bounds checking.

    Args:
        filepath: Path to FITS file

    Returns:
        SafeFITSReader instance

    Raises:
        FileNotFoundError, IOError, ValueError for invalid files
    """
    return SafeFITSReader(filepath)


__all__ = [
    'SafeFITSReader',
    'DataCubeInfo',
    'load_fits'
]
