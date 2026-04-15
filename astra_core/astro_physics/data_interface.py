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
Observational Data Interface Layer for ASTRO-SWARM
===================================================

Comprehensive interfaces for reading, writing, and manipulating
astronomical data formats.

Capabilities:
1. FITS file I/O (images, tables, cubes)
2. Spectral cube handling (position-position-velocity)
3. VOTable and Virtual Observatory support
4. CASA measurement set interface
5. Automatic unit handling
6. Region file support
7. World Coordinate System (WCS) transformations

Key Dependencies:
- astropy (FITS, WCS, units, tables)
- spectral-cube (optional, for advanced cube handling)
- regions (optional, for region file support)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from pathlib import Path
import warnings
import json

# Try to import optional dependencies
try:
    from astropy.io import fits
    from astropy import units as u
    from astropy.wcs import WCS
    from astropy.table import Table
    from astropy.coordinates import SkyCoord
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False
    warnings.warn("astropy not available - some functionality will be limited")

try:
    from spectral_cube import SpectralCube
    SPECTRAL_CUBE_AVAILABLE = True
except ImportError:
    SPECTRAL_CUBE_AVAILABLE = False

try:
    from regions import Regions
    REGIONS_AVAILABLE = True
except ImportError:
    REGIONS_AVAILABLE = False

# Starlink NDF support (for JCMT, UKIRT data)
try:
    from starlink import Ndf
    from starlink import Ast
    NDF_AVAILABLE = True
except ImportError:
    NDF_AVAILABLE = False


# =============================================================================
# UNIT HANDLING
# =============================================================================

class AstroUnits:
    """
    Astronomical unit handling and conversions.

    Provides standardized unit conversions for common astronomical quantities.
    """

    # Common unit conversions
    CONVERSIONS = {
        # Length
        'pc_to_cm': 3.0857e18,
        'kpc_to_cm': 3.0857e21,
        'Mpc_to_cm': 3.0857e24,
        'AU_to_cm': 1.496e13,
        'ly_to_cm': 9.461e17,

        # Mass
        'Msun_to_g': 1.989e33,
        'Mjup_to_g': 1.898e30,
        'Mearth_to_g': 5.972e27,

        # Luminosity
        'Lsun_to_erg_s': 3.828e33,

        # Flux
        'Jy_to_cgs': 1e-23,  # erg/s/cm²/Hz
        'mJy_to_cgs': 1e-26,
        'uJy_to_cgs': 1e-29,

        # Angle
        'arcsec_to_rad': np.pi / 180 / 3600,
        'arcmin_to_rad': np.pi / 180 / 60,
        'deg_to_rad': np.pi / 180,

        # Frequency/wavelength
        'GHz_to_Hz': 1e9,
        'MHz_to_Hz': 1e6,
        'um_to_cm': 1e-4,
        'nm_to_cm': 1e-7,
        'Angstrom_to_cm': 1e-8,

        # Temperature
        'K_to_K': 1.0,  # Identity

        # Column density
        'cm-2_to_cm-2': 1.0,

        # Velocity
        'km_s_to_cm_s': 1e5,
    }

    @classmethod
    def convert(cls, value: float, from_unit: str, to_unit: str) -> float:
        """
        Convert between units.

        Parameters
        ----------
        value : float
            Value to convert
        from_unit : str
            Source unit
        to_unit : str
            Target unit

        Returns
        -------
        float : Converted value
        """
        key = f"{from_unit}_to_{to_unit}"
        if key in cls.CONVERSIONS:
            return value * cls.CONVERSIONS[key]

        # Try reverse
        key_rev = f"{to_unit}_to_{from_unit}"
