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
Interferometric Imaging Support for ASTRO-SWARM
================================================

Tools for radio/mm interferometric data analysis.

Capabilities:
1. UV-plane sampling and simulation
2. Visibility modeling and prediction
3. CLEAN/MEM deconvolution interfaces
4. Primary beam correction
5. Self-calibration support
6. Visibility model comparison
7. Baseline-dependent analysis

Key References:
- Thompson, Moran & Swenson (Interferometry and Synthesis)
- Cornwell et al. 2008 (W-projection)
- Briggs 1995 (Robust weighting)
- Rau & Cornwell 2011 (Multi-scale CLEAN)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
from scipy.fft import fft2, ifft2, fftshift, ifftshift, fftfreq
from scipy.ndimage import gaussian_filter
from scipy.interpolate import griddata
from scipy.optimize import minimize
import warnings

# Physical Constants
c_light = 2.998e10      # cm/s


# =============================================================================
# VISIBILITY DATA STRUCTURES
# =============================================================================

@dataclass
class Visibility:
    """Visibility data container"""
    u: np.ndarray               # U coordinates (wavelengths)
    v: np.ndarray               # V coordinates (wavelengths)
    w: np.ndarray               # W coordinates (wavelengths)
    real: np.ndarray            # Real part of visibility
    imag: np.ndarray            # Imaginary part of visibility
    weight: np.ndarray          # Visibility weights
    freq: float                 # Frequency (Hz)
    time: Optional[np.ndarray] = None  # Time stamps

    @property
    def vis(self) -> np.ndarray:
        """Complex visibility"""
        return self.real + 1j * self.imag

    @property
    def amplitude(self) -> np.ndarray:
        """Visibility amplitude"""
        return np.abs(self.vis)

    @property
    def phase(self) -> np.ndarray:
        """Visibility phase (radians)"""
        return np.angle(self.vis)

    @property
    def uvdist(self) -> np.ndarray:
        """UV distance (wavelengths)"""
        return np.sqrt(self.u**2 + self.v**2)

    def __len__(self):
        return len(self.u)


@dataclass
class UVCoverage:
    """UV plane coverage pattern"""
    u: np.ndarray
    v: np.ndarray
    w: np.ndarray
    weight: np.ndarray
    antenna1: np.ndarray
    antenna2: np.ndarray
    time: np.ndarray


# =============================================================================
# ARRAY CONFIGURATION
# =============================================================================

@dataclass
class Antenna:
    """Antenna position"""
    name: str
    x: float        # East coordinate (m)
    y: float        # North coordinate (m)
    z: float        # Up coordinate (m)
    diameter: float  # Dish diameter (m)


class ArrayConfiguration:
    """
    Interferometer array configuration.
    """

    def __init__(self, name: str, latitude: float = 0.0):
        """
        Parameters
        ----------
        name : str
            Array name
        latitude : float
            Array latitude (degrees)
        """
        self.name = name
        self.latitude = np.radians(latitude)
        self.antennas: List[Antenna] = []

    def add_antenna(self, antenna: Antenna):
        """Add antenna to array"""
        self.antennas.append(antenna)

    @property
    def n_antennas(self) -> int:
        return len(self.antennas)

    @property
    def n_baselines(self) -> int:
        n = self.n_antennas
        return n * (n - 1) // 2

    def get_baselines(self) -> List[Tuple[int, int, np.ndarray]]:
        """
        Get all baselines.

        Returns
        -------
        list : (i, j, baseline_vector) tuples
        """
        baselines = []
        for i, ant1 in enumerate(self.antennas):
            for j, ant2 in enumerate(self.antennas):
                if j > i:
                    baseline = np.array([
                        ant2.x - ant1.x,
                        ant2.y - ant1.y,
                        ant2.z - ant1.z
                    ])
                    baselines.append((i, j, baseline))
        return baselines

    def max_baseline(self) -> float:
        """Maximum baseline length (m)"""
        max_b = 0.0
        for i, j, b in self.get_baselines():
            max_b = max(max_b, np.linalg.norm(b))
        return max_b

    def min_baseline(self) -> float:
        """Minimum baseline length (m)"""
        min_b = np.inf
        for i, j, b in self.get_baselines():
            blen = np.linalg.norm(b)
            if blen > 0:
                min_b = min(min_b, blen)
        return min_b

    def angular_resolution(self, freq_Hz: float) -> float:
        """
        Angular resolution (arcsec).

        θ ≈ λ / B_max
        """
        wavelength = c_light / freq_Hz
        b_max = self.max_baseline() * 100  # m to cm
        theta_rad = wavelength / b_max
        return theta_rad * 206265  # radians to arcsec

    def largest_angular_scale(self, freq_Hz: float) -> float:
        """
        Largest recoverable angular scale (arcsec).

        θ_LAS ≈ λ / B_min
        """
        wavelength = c_light / freq_Hz
        b_min = self.min_baseline() * 100
        if b_min > 0:
            theta_rad = wavelength / b_min
            return theta_rad * 206265
        return np.inf


class StandardArrays:
    """
    Standard interferometer array configurations.
    """

    @staticmethod
    def vla_a() -> ArrayConfiguration:
        """VLA A-configuration (approximate)"""
        array = ArrayConfiguration("VLA_A", latitude=34.08)

        # Simplified Y-shaped array
        arm_length = 21000  # meters (max baseline ~36 km)
        n_per_arm = 9

        for arm, angle in enumerate([0, 120, 240]):
            angle_rad = np.radians(angle - 90)  # North arm at 0
            for i in range(n_per_arm):
                r = arm_length * (i / n_per_arm)**1.7  # Non-uniform spacing
                x = r * np.cos(angle_rad)
                y = r * np.sin(angle_rad)
                array.add_antenna(Antenna(
                    name=f"Ant{arm*n_per_arm + i}",
                    x=x, y=y, z=0, diameter=25
                ))

        return array

    @staticmethod
    def alma_compact() -> ArrayConfiguration:
        """ALMA compact configuration (approximate)"""
        array = ArrayConfiguration("ALMA_C1", latitude=-23.02)

        # Random compact distribution
        np.random.seed(42)
        n_antennas = 50
        max_radius = 150  # meters

        for i in range(n_antennas):
            r = max_radius * np.sqrt(np.random.random())
            theta = np.random.random() * 2 * np.pi
            array.add_antenna(Antenna(
                name=f"DA{i:02d}",
                x=r * np.cos(theta),
                y=r * np.sin(theta),
                z=0,
                diameter=12
            ))

        return array

    @staticmethod
    def alma_extended() -> ArrayConfiguration:
        """ALMA extended configuration (approximate)"""
        array = ArrayConfiguration("ALMA_C6", latitude=-23.02)

        np.random.seed(43)
        n_antennas = 50
        max_radius = 8000  # meters

        for i in range(n_antennas):
            r = max_radius * np.sqrt(np.random.random())
            theta = np.random.random() * 2 * np.pi
            array.add_antenna(Antenna(
                name=f"DA{i:02d}",
                x=r * np.cos(theta),
                y=r * np.sin(theta),
                z=0,
                diameter=12
            ))

        return array


# =============================================================================
# UV PLANE SIMULATION
# =============================================================================

class UVSimulator:
    """
    Simulate UV coverage for observations.
    """

    def __init__(self, array: ArrayConfiguration):
        self.array = array

    def generate_coverage(self,
                         source_dec: float,
                         freq_Hz: float,
                         hour_angles: np.ndarray,
                         integration_time: float = 10.0) -> UVCoverage:
        """
        Generate UV coverage for an observation.

        Parameters
        ----------
        source_dec : float
            Source declination (degrees)
        freq_Hz : float
            Observing frequency (Hz)
        hour_angles : np.ndarray
            Hour angles to observe (degrees)
        integration_time : float
            Integration time per sample (seconds)

        Returns
        -------
        UVCoverage
        """
        dec_rad = np.radians(source_dec)
        lat_rad = self.array.latitude
        wavelength = c_light / freq_Hz * 1e-2  # wavelengths (m -> cm, then to wavelengths)
        wavelength_m = c_light / freq_Hz  # in meters

        baselines = self.array.get_baselines()

        all_u = []
        all_v = []
        all_w = []
        all_ant1 = []
        all_ant2 = []
        all_time = []

        for ha in hour_angles:
            ha_rad = np.radians(ha)

            # Rotation matrix from antenna coords to UV coords
            sin_ha = np.sin(ha_rad)
            cos_ha = np.cos(ha_rad)
            sin_dec = np.sin(dec_rad)
            cos_dec = np.cos(dec_rad)
            sin_lat = np.sin(lat_rad)
            cos_lat = np.cos(lat_rad)

            for i, j, b in baselines:
                # Transform baseline to UV coordinates
                # b = (East, North, Up) in meters

                # Convert to (X, Y, Z) in wavelengths
                # where X points to HA=0, Y to HA=6h, Z to NCP
                u = (sin_ha * b[0] + cos_ha * b[1]) / wavelength_m
                v = (-sin_dec * cos_ha * b[0] + sin_dec * sin_ha * b[1] +
                     cos_dec * b[2]) / wavelength_m
                w = (cos_dec * cos_ha * b[0] - cos_dec * sin_ha * b[1] +
                     sin_dec * b[2]) / wavelength_m

                all_u.append(u)
                all_v.append(v)
                all_w.append(w)
                all_ant1.append(i)
                all_ant2.append(j)
                all_time.append(ha)

                # Add conjugate
                all_u.append(-u)
                all_v.append(-v)
                all_w.append(-w)
                all_ant1.append(j)
                all_ant2.append(i)
                all_time.append(ha)

        return UVCoverage(
            u=np.array(all_u),
            v=np.array(all_v),
            w=np.array(all_w),
            weight=np.ones(len(all_u)),
            antenna1=np.array(all_ant1),
            antenna2=np.array(all_ant2),
            time=np.array(all_time)
        )

    def observe_model(self,
                     model_image: np.ndarray,
                     pixel_size_arcsec: float,
                     uv_coverage: UVCoverage,
                     freq_Hz: float,
                     add_noise: bool = True,
                     noise_Jy: float = 1e-3) -> Visibility:
        """
        Simulate visibilities from a model image.

        Parameters
        ----------
        model_image : np.ndarray
            Sky model (Jy/pixel)
        pixel_size_arcsec : float
            Pixel size (arcsec)
        uv_coverage : UVCoverage
            UV coverage pattern
        freq_Hz : float
            Observing frequency (Hz)
        add_noise : bool
            Add thermal noise
        noise_Jy : float
            RMS noise per visibility (Jy)

        Returns
        -------
        Visibility
        """
        ny, nx = model_image.shape

        # FFT of model (visibility function)
        model_ft = fftshift(fft2(ifftshift(model_image)))

        # UV pixel scale
        du = 1.0 / (nx * pixel_size_arcsec / 206265)
        dv = 1.0 / (ny * pixel_size_arcsec / 206265)

        # UV grid coordinates
        u_grid = fftfreq(nx, d=pixel_size_arcsec / 206265)
        v_grid = fftfreq(ny, d=pixel_size_arcsec / 206265)

        # Sample visibilities at UV coverage points
        real_parts = []
        imag_parts = []

        for u, v in zip(uv_coverage.u, uv_coverage.v):
            # Find nearest grid point (simple nearest-neighbor)
            iu = int(np.round(u / du)) + nx // 2
            iv = int(np.round(v / dv)) + ny // 2

            if 0 <= iu < nx and 0 <= iv < ny:
                vis = model_ft[iv, iu]
            else:
                vis = 0.0

            real_parts.append(np.real(vis))
            imag_parts.append(np.imag(vis))

        real_parts = np.array(real_parts)
        imag_parts = np.array(imag_parts)

        if add_noise:
            real_parts += np.random.normal(0, noise_Jy, len(real_parts))
            imag_parts += np.random.normal(0, noise_Jy, len(imag_parts))

        weights = np.ones(len(uv_coverage.u)) / noise_Jy**2

        return Visibility(
            u=uv_coverage.u,
            v=uv_coverage.v,
            w=uv_coverage.w,
            real=real_parts,
            imag=imag_parts,
            weight=weights,
            freq=freq_Hz,
            time=uv_coverage.time
        )


# =============================================================================
# IMAGING
# =============================================================================

class WeightingScheme(Enum):
    """Visibility weighting schemes"""
    NATURAL = "natural"
    UNIFORM = "uniform"
    BRIGGS = "briggs"


@dataclass
class DirtyImage:
    """Dirty image and beam"""
    image: np.ndarray           # Dirty image
    beam: np.ndarray            # Dirty beam (PSF)
    pixel_size: float           # Pixel size (arcsec)
    beam_params: Dict[str, float]  # Fitted beam parameters


class Imager:
    """
    Interferometric imaging.
    """

    def __init__(self):
        pass

    def make_dirty_image(self,
                        vis: Visibility,
                        image_size: int = 256,
                        pixel_size: float = 0.1,
                        weighting: WeightingScheme = WeightingScheme.NATURAL,
                        robust: float = 0.5) -> DirtyImage:
        """
        Make dirty image from visibilities.

        Parameters
        ----------
        vis : Visibility
            Visibility data
        image_size : int
            Image size in pixels
        pixel_size : float
            Pixel size (arcsec)
        weighting : WeightingScheme
            Weighting scheme
        robust : float
            Briggs robust parameter (-2 to 2)

        Returns
        -------
        DirtyImage
        """
        # Grid size
        nx = ny = image_size

        # UV pixel scale (wavelengths per pixel in UV plane)
        du = 1.0 / (nx * pixel_size / 206265)
        dv = 1.0 / (ny * pixel_size / 206265)

        # Create grids
        vis_grid = np.zeros((ny, nx), dtype=complex)
        weight_grid = np.zeros((ny, nx))
        sampling_grid = np.zeros((ny, nx))

        # Apply weighting
        weights = self._compute_weights(vis, weighting, robust, du, dv, nx, ny)

        # Grid visibilities
        for i in range(len(vis.u)):
            iu = int(np.round(vis.u[i] / du)) + nx // 2
            iv = int(np.round(vis.v[i] / dv)) + ny // 2

            if 0 <= iu < nx and 0 <= iv < ny:
                vis_grid[iv, iu] += vis.vis[i] * weights[i]
                weight_grid[iv, iu] += weights[i]
                sampling_grid[iv, iu] += 1

        # Normalize
        with np.errstate(invalid='ignore', divide='ignore'):
            vis_grid = np.where(weight_grid > 0, vis_grid / weight_grid, 0)

        # FFT to image
        dirty_image = np.real(fftshift(ifft2(ifftshift(vis_grid))))

        # Dirty beam (PSF)
        beam_grid = np.where(sampling_grid > 0, 1.0, 0.0)
        dirty_beam = np.real(fftshift(ifft2(ifftshift(beam_grid))))
        dirty_beam /= np.max(dirty_beam)

        # Fit beam
        beam_params = self._fit_beam(dirty_beam, pixel_size)

        return DirtyImage(
            image=dirty_image,
            beam=dirty_beam,
            pixel_size=pixel_size,
            beam_params=beam_params
        )

    def _compute_weights(self, vis: Visibility,
                        weighting: WeightingScheme,
                        robust: float,
                        du: float, dv: float,
                        nx: int, ny: int) -> np.ndarray:
        """Compute visibility weights"""
        if weighting == WeightingScheme.NATURAL:
            return vis.weight

        elif weighting == WeightingScheme.UNIFORM:
            # Count visibilities per UV cell
            cell_counts = {}
            for i in range(len(vis.u)):
                iu = int(np.round(vis.u[i] / du)) + nx // 2
                iv = int(np.round(vis.v[i] / dv)) + ny // 2
                key = (iu, iv)
                cell_counts[key] = cell_counts.get(key, 0) + 1

            weights = np.zeros(len(vis.u))
            for i in range(len(vis.u)):
                iu = int(np.round(vis.u[i] / du)) + nx // 2
                iv = int(np.round(vis.v[i] / dv)) + ny // 2
                key = (iu, iv)
                weights[i] = 1.0 / cell_counts.get(key, 1)

            return weights

        elif weighting == WeightingScheme.BRIGGS:
            # Briggs robust weighting
            # First compute uniform weights
            uniform = self._compute_weights(vis, WeightingScheme.UNIFORM,
                                           robust, du, dv, nx, ny)
            natural = vis.weight

            # Robust factor
            f2 = (5 * 10**(-robust))**2 * np.sum(uniform) / np.sum(natural)

            return natural / (1 + natural * f2)

        return vis.weight

    def _fit_beam(self, beam: np.ndarray, pixel_size: float) -> Dict[str, float]:
        """Fit 2D Gaussian to beam"""
        ny, nx = beam.shape
        y, x = np.mgrid[0:ny, 0:nx]
        y = (y - ny//2) * pixel_size
        x = (x - nx//2) * pixel_size
