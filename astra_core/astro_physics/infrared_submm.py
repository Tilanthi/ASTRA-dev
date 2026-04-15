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
Infrared and Submillimeter Astronomy Module

Comprehensive analysis of infrared and submillimeter observations.
Supports data from Spitzer, Herschel, JWST, SOFIA, ALMA, NOEMA, JCMT.

Key capabilities:
- Dust emission modeling (modified blackbody)
- SED fitting across IR/submm
- PAH feature analysis
- Spectral energy distributions
- Color-color diagrams
- Redshift estimation from submm
- Cold dust temperature
- Gas mass from dust emission
- Line cooling calculations

Date: 2025-12-22
Version: 1.0
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from scipy import constants
from scipy.optimize import curve_fit
import warnings

# Physical constants (CGS)
H_PLANCK = 6.626e-27  # erg s
K_BOLTZMANN = 1.381e-16  # erg/K
C_LIGHT = 2.998e10  # cm/s
M_H = 1.673e-24  # g
PC = 3.086e18  # cm
JANSKY = 1e-23  # erg/s/cm^2/Hz
L_SUN = 3.828e33  # erg/s
M_SUN = 1.989e33  # g


class IRBand(Enum):
    """Infrared and submillimeter bands"""
    # Near-IR
    IRAC_3_6 = "irac_3_6"  # 3.6 microns
    IRAC_4_5 = "irac_4_5"  # 4.5 microns
    IRAC_5_8 = "irac_5_8"  # 5.8 microns
    IRAC_8_0 = "irac_8_0"  # 8.0 microns
    # Mid-IR
    WISE_12 = "wise_12"  # 12 microns
    WISE_22 = "wise_22"  # 22 microns
    WISE_24 = "wise_24"  # 24 microns
    MIPS_24 = "mips_24"  # 24 microns
    # Far-IR
    PACS_70 = "pacs_70"  # 70 microns
    PACS_100 = "pacs_100"  # 100 microns
    PACS_160 = "pacs_160"  # 160 microns
    SPIRE_250 = "spire_250"  # 250 microns
    SPIRE_350 = "spire_350"  # 350 microns
    SPIRE_500 = "spire_500"  # 500 microns
    # Submillimeter
    SCUBA_450 = "scuba_450"  # 450 microns
    SCUBA_850 = "scuba_850"  # 850 microns
    # ALMA bands
    ALMA_BAND3 = "alma_band3"  # 3 mm (100 GHz)
    ALMA_BAND6 = "alma_band6"  # 1 mm (230 GHz)
    ALMA_BAND7 = "alma_band7"  # 0.87 mm (345 GHz)


class PAHFeature(Enum):
    """Polycyclic Aromatic Hydrocarbon features"""
    PAH_3_3 = "pah_3_3"  # 3.3 microns
    PAH_6_2 = "pah_6_2"  # 6.2 microns
    PAH_7_7 = "pah_7_7"  # 7.7 microns
    PAH_8_6 = "pah_8_6"  # 8.6 microns
    PAH_11_3 = "pah_11_3"  # 11.3 microns
    PAH_12_7 = "pah_12_7"  # 12.7 microns


@dataclass
class IRPhotometry:
    """Infrared/submillimeter photometry point"""
    band: Union[IRBand, str]
    wavelength: float  # microns
    flux: float  # Jy
    flux_err: float = 0.0
    frequency: float = 0.0  # Hz (calculated from wavelength)
    facility: str = ""

    def __post_init__(self):
        if self.frequency == 0:
            # Convert wavelength to frequency
            lam_cm = self.wavelength * 1e-4  # microns to cm
            self.frequency = C_LIGHT / lam_cm


@dataclass
class PAHSpectrum:
    """PAH emission spectrum"""
    features: Dict[PAHFeature, float] = field(default_factory=dict)
    continuum: Dict[str, float] = field(default_factory=dict)
    feature_ratios: Dict[str, float] = field(default_factory=dict)


@dataclass
class DustProperties:
    """Dust properties from SED fitting"""
    temperature: float  # K
    mass: float  # Msun
    beta: float = 1.5  # Emissivity index
    luminosity: float = 0.0  # Lsun
    power: float = 0.0  # erg/s


class ModifiedBlackbody:
    """
    Modified blackbody dust emission model.

    I_nu = tau_nu * B_nu(T)
    tau_nu = kappa_nu * (M_dust / D^2)
    kappa_nu = kappa_0 * (nu/nu_0)^beta

    Where:
    - B_nu is Planck function
    - kappa_nu is dust opacity
    - beta is emissivity index (1.5-2.0 typical)
    """

    def __init__(self, kappa_0: float = 10.0, beta: float = 1.5):
        """
        Initialize modified blackbody.

        Args:
            kappa_0: Reference opacity at lambda_0 (cm^2/g)
            beta: Emissivity index
        """
        self.kappa_0 = kappa_0  # at 350 microns
        self.lambda_0 = 350.0  # microns
        self.beta = beta

    def planck_function(self, wavelength: float, temperature: float) -> float:
        """
        Planck function B_lambda(T).

        Args:
            wavelength: Wavelength (microns)
            temperature: Temperature (K)

        Returns:
            Specific intensity (erg/s/cm^2/cm/sr)
        """
        # Convert to CGS
        lam_cm = wavelength * 1e-4  # microns to cm

        h_nu_over_kt = (H_PLANCK * C_LIGHT) / (lam_cm * K_BOLTZMANN * temperature)

        # Avoid overflow
        if h_nu_over_kt > 100:
            return 0.0

        b_lambda = (2 * H_PLANCK * C_LIGHT**2 / lam_cm**5 /
                   (np.expm1(h_nu_over_kt)))

        return b_lambda

    def opacity(self, wavelength: float) -> float:
        """
        Dust opacity kappa_lambda.

        Args:
            wavelength: Wavelength (microns)

        Returns:
            Opacity (cm^2/g)
        """
        kappa = self.kappa_0 * (wavelength / self.lambda_0)**(-self.beta)
        return kappa

    def flux_density(self, wavelength: float, temperature: float,
                    dust_mass: float, distance: float = 1.0) -> float:
        """
        Predicted flux density from dust emission.

        Args:
            wavelength: Wavelength (microns)
            temperature: Dust temperature (K)
            dust_mass: Dust mass (Msun)
            distance: Distance (Mpc)

        Returns:
            Flux density (Jy)
        """
        # Planck function
        b_lambda = self.planck_function(wavelength, temperature)

        # Opacity
        kappa = self.opacity(wavelength)

        # Convert to flux density
        # F_nu = (1/D^2) * M_dust * kappa_nu * B_nu(T)
        dist_cm = distance * 1e6 * PC  # Mpc to cm
        mass_g = dust_mass * M_SUN

        # Flux in erg/s/cm^2/cm
        flux_cm = mass_g * kappa * b_lambda / dist_cm**2

        # Convert to Jy
        flux_jy = flux_cm / JANSKY

        return flux_jy

    def fit(self, wavelengths: np.ndarray, fluxes: np.ndarray,
           flux_errs: np.ndarray = None) -> Dict[str, Any]:
        """
        Fit modified blackbody to photometry.

        Args:
            wavelengths: Wavelengths (microns)
            fluxes: Flux densities (Jy)
            flux_errs: Flux uncertainties (Jy)

        Returns:
            Fit results (temperature, mass, beta)
        """
        if flux_errs is None:
            flux_errs = np.ones_like(fluxes) * 0.1 * np.mean(fluxes)
