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
Multi-Scale Coupling Framework for Astrophysical Simulations

Provides tools for connecting simulations across different scales:
- Zoom-in simulation techniques
- Sub-grid physics models
- Feedback prescriptions (stellar, AGN)
- Scale bridging and interpolation
- Hierarchical refinement

Applications:
- Galaxy formation with ISM physics
- Star formation in molecular clouds
- Protoplanetary disk structure
- AGN feedback and outflows
- Cosmological zoom simulations
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod
import json


# Physical constants (CGS)
G_GRAV = 6.67430e-8  # cm^3/g/s^2
C_LIGHT = 2.99792458e10  # cm/s
K_BOLTZMANN = 1.380649e-16  # erg/K
M_PROTON = 1.6726219e-24  # g
M_SUN = 1.989e33  # g
PC = 3.086e18  # cm
KPC = 3.086e21  # cm
MPC = 3.086e24  # cm
YR = 3.156e7  # s
MYR = 3.156e13  # s
GYR = 3.156e16  # s


class ScaleLevel(Enum):
    """Hierarchical scale levels."""
    COSMOLOGICAL = "cosmological"  # > 10 Mpc
    CLUSTER = "cluster"  # 1-10 Mpc
    GALAXY = "galaxy"  # 10-100 kpc
    CGM = "cgm"  # 10-300 kpc
    DISK = "disk"  # 1-30 kpc
    GMC = "gmc"  # 1-100 pc
    CLUMP = "clump"  # 0.1-1 pc
    CORE = "core"  # 0.01-0.1 pc
    PROTOSTELLAR = "protostellar"  # < 0.01 pc


@dataclass
class ScaleBoundary:
    """Defines the interface between simulation scales."""
    upper_scale: ScaleLevel
    lower_scale: ScaleLevel
    resolution_ratio: float  # Refinement factor
    overlap_fraction: float  # Fractional overlap region
    coupling_vars: List[str]  # Variables to transfer
    interpolation_order: int = 2
    conservation_enforced: bool = True


@dataclass
class SubGridModel(ABC):
    """Abstract base class for sub-grid physics models."""
    name: str
    scale_below: float  # pc, resolution below which model applies
    parameters: Dict[str, float] = field(default_factory=dict)

    @abstractmethod
    def compute(self, local_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Compute sub-grid physics contribution."""
        pass


class TurbulentPressureModel(SubGridModel):
    """
    Sub-grid turbulent pressure support.

    Adds effective pressure from unresolved turbulent motions.
    """

    def __init__(self, sigma_turb: float = 1.0, scale_below: float = 1.0):
        """
        Parameters
        ----------
        sigma_turb : float
            Turbulent velocity dispersion at reference scale (km/s)
        scale_below : float
            Scale below which model applies (pc)
        """
        self.name = "turbulent_pressure"
        self.scale_below = scale_below
        self.parameters = {
            "sigma_turb": sigma_turb,
            "reference_scale": 1.0,  # pc
            "power_law_index": 0.5  # Larson relation
        }

    def compute(self, local_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute turbulent pressure contribution.

        Parameters
        ----------
        local_properties : dict
            Must contain 'density' (g/cm^3) and 'cell_size' (pc)

        Returns
        -------
        dict
            Contains 'P_turb' (erg/cm^3), 'sigma_eff' (km/s)
        """
        rho = local_properties['density']
        cell_size = local_properties.get('cell_size', self.scale_below)

        # Turbulent velocity from Larson relation
        sigma_ref = self.parameters['sigma_turb'] * 1e5  # cm/s
        l_ref = self.parameters['reference_scale'] * PC
        alpha = self.parameters['power_law_index']

        sigma_turb = sigma_ref * (cell_size * PC / l_ref)**alpha

        # Turbulent pressure
        P_turb = rho * sigma_turb**2

        return {
            'P_turb': P_turb,
            'sigma_eff': sigma_turb / 1e5,  # km/s
            'turbulent_energy': 0.5 * rho * sigma_turb**2
        }


class StarFormationModel(SubGridModel):
    """
    Sub-grid star formation prescription.

    Implements various star formation recipes.
    """

    def __init__(self, efficiency: float = 0.01, density_threshold: float = 100.0,
                 scale_below: float = 10.0, recipe: str = "schmidt"):
        """
        Parameters
        ----------
        efficiency : float
            Star formation efficiency per free-fall time
        density_threshold : float
            Density threshold in H/cm^3
        scale_below : float
            Scale below which model applies (pc)
        recipe : str
            Star formation recipe ("schmidt", "krumholz", "hopkins")
        """
        self.name = "star_formation"
        self.scale_below = scale_below
        self.recipe = recipe
        self.parameters = {
            "efficiency": efficiency,
            "n_threshold": density_threshold,
            "schmidt_index": 1.5,
            "virial_parameter_crit": 2.0
        }

    def compute(self, local_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute star formation rate.

        Parameters
        ----------
        local_properties : dict
            Must contain 'density', 'temperature', optional 'velocity_dispersion'

        Returns
        -------
        dict
            Contains 'sfr_density' (M_sun/yr/pc^3), 'stellar_mass_formed'
        """
        rho = local_properties['density']
        T = local_properties.get('temperature', 10.0)

        # Number density
        n_H = rho / (1.4 * M_PROTON)
        n_threshold = self.parameters['n_threshold']

        if n_H < n_threshold:
            return {'sfr_density': 0.0, 'stellar_mass_formed': 0.0}

        # Free-fall time
        t_ff = np.sqrt(3 * np.pi / (32 * G_GRAV * rho))

        if self.recipe == "schmidt":
            # Simple Schmidt law
            epsilon = self.parameters['efficiency']
            sfr_vol = epsilon * rho / t_ff

        elif self.recipe == "krumholz":
            # Krumholz & McKee (2005) turbulence-regulated SF
            sigma = local_properties.get('velocity_dispersion', 1.0) * 1e5  # cm/s
            alpha_vir = self.parameters['virial_parameter_crit']

            # Virial parameter
            cell_size = local_properties.get('cell_size', 1.0) * PC
            alpha = 5 * sigma**2 * cell_size / (G_GRAV * rho * cell_size**3)

            # Efficiency depends on virial state
            epsilon = self.parameters['efficiency'] * np.exp(-alpha_vir / alpha)
            sfr_vol = epsilon * rho / t_ff

        elif self.recipe == "hopkins":
            # Hopkins (2013) multi-freefall
            sigma = local_properties.get('velocity_dispersion', 1.0) * 1e5
            mach = sigma / np.sqrt(K_BOLTZMANN * T / M_PROTON)

            # Multi-freefall model
            s_crit = np.log(1 + 0.5 * mach**2)
            epsilon = 0.5 * (1 + np.tanh((np.log(n_H / n_threshold) - s_crit) / 0.5))
            sfr_vol = epsilon * rho / t_ff

        else:
            sfr_vol = 0.0

        # Convert to M_sun/yr/pc^3
        sfr_density = sfr_vol / M_SUN * YR * PC**3

        # Mass formed in timestep
        dt = local_properties.get('timestep', 1e4 * YR)
        mass_formed = sfr_vol * local_properties.get('cell_volume', PC**3) * dt / M_SUN

        return {
            'sfr_density': sfr_density,
            'stellar_mass_formed': mass_formed,
            'free_fall_time': t_ff / YR  # years
        }


class StellarFeedbackModel(SubGridModel):
    """
    Sub-grid stellar feedback prescription.

    Includes:
    - Supernova energy/momentum injection
    - Stellar winds
    - Radiation pressure
    - Photoionization heating
    """

    def __init__(self, scale_below: float = 100.0,
                 sn_energy: float = 1e51,
                 coupling_efficiency: float = 0.1):
        """
        Parameters
        ----------
        scale_below : float
            Scale below which feedback is sub-grid (pc)
        sn_energy : float
            Energy per supernova (erg)
        coupling_efficiency : float
            Fraction of energy coupled to ISM
        """
        self.name = "stellar_feedback"
        self.scale_below = scale_below
        self.parameters = {
            "E_sn": sn_energy,
            "eta_couple": coupling_efficiency,
            "sn_rate_per_100msun": 1.0,  # per 100 M_sun of SF
            "wind_mass_loading": 0.3,
            "wind_velocity": 30.0,  # km/s
            "ionizing_photon_rate": 1e49,  # per M_sun of young stars
            "radiation_pressure_boost": 2.0
        }

    def compute(self, local_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute stellar feedback.

        Parameters
        ----------
        local_properties : dict
            Must contain 'stellar_mass' or 'sfr', 'density'

        Returns
        -------
        dict
            Energy, momentum, and mass injection rates
        """
        # Star formation rate or recent stellar mass
        sfr = local_properties.get('sfr', 0.0)  # M_sun/yr
        young_stars = local_properties.get('young_stellar_mass', sfr * 10e6)  # M_sun
        rho = local_properties['density']

        # Supernova feedback
        sn_rate = self.parameters['sn_rate_per_100msun'] * sfr / 100.0  # per year
        E_sn = self.parameters['E_sn']
        eta = self.parameters['eta_couple']

        # Energy injection rate
        E_dot_sn = eta * sn_rate * E_sn / YR  # erg/s

        # Momentum injection (Sedov-Taylor terminal momentum)
        n_H = rho / (1.4 * M_PROTON)
        p_terminal = 3e5 * M_SUN * 1e5 * (E_sn / 1e51)**0.93 * (n_H / 1.0)**(-0.13)
        p_dot_sn = sn_rate * p_terminal  # g cm/s /yr

        # Stellar winds
        wind_mass_rate = self.parameters['wind_mass_loading'] * sfr * M_SUN / YR  # g/s
        wind_velocity = self.parameters['wind_velocity'] * 1e5  # cm/s
        p_dot_wind = wind_mass_rate * wind_velocity

        # Radiation pressure
        L_young = 1e3 * young_stars * 3.83e33  # erg/s, young stellar luminosity
        boost = self.parameters['radiation_pressure_boost']
        p_dot_rad = boost * L_young / C_LIGHT

        # Photoionization heating
        Q_ion = self.parameters['ionizing_photon_rate'] * young_stars  # photons/s
        heating_rate = 1e-13 * n_H * Q_ion * 2e-11  # erg/s (approximate)

        return {
            'energy_injection_rate': E_dot_sn + 0.5 * wind_mass_rate * wind_velocity**2,
            'momentum_injection_rate': p_dot_sn + p_dot_wind + p_dot_rad,
            'mass_injection_rate': wind_mass_rate,
            'heating_rate': heating_rate,
            'supernova_rate': sn_rate,
            'ionizing_luminosity': Q_ion
        }


class AGNFeedbackModel(SubGridModel):
    """
    Sub-grid AGN feedback prescription.

    Implements:
    - Quasar/radiative mode
    - Kinetic/jet mode
    - Radiation pressure on dust
    """

    def __init__(self, scale_below: float = 1000.0,
                 radiative_efficiency: float = 0.1,
                 coupling_efficiency: float = 0.05):
        """
        Parameters
        ----------
        scale_below : float
            Scale below which AGN is sub-grid (pc)
        radiative_efficiency : float
            Radiative efficiency of accretion
        coupling_efficiency : float
            Fraction of energy coupled to surrounding gas
        """
        self.name = "agn_feedback"
        self.scale_below = scale_below
        self.parameters = {
            "epsilon_r": radiative_efficiency,
            "epsilon_f": coupling_efficiency,
            "eddington_factor_crit": 0.01,  # Below this, jet mode
            "jet_efficiency": 0.1,
            "jet_velocity": 10000.0,  # km/s
            "momentum_boost": 20.0  # IR momentum boost
        }

    def compute(self, local_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute AGN feedback.

        Parameters
        ----------
        local_properties : dict
            Must contain 'bh_mass' (M_sun), 'accretion_rate' (M_sun/yr)

        Returns
        -------
        dict
            Energy and momentum injection rates
        """
        M_bh = local_properties.get('bh_mass', 1e6) * M_SUN  # g
        Mdot = local_properties.get('accretion_rate', 0.01) * M_SUN / YR  # g/s

        # Eddington luminosity and rate
        L_edd = 4 * np.pi * G_GRAV * M_bh * M_PROTON * C_LIGHT / 6.65e-25
        Mdot_edd = L_edd / (self.parameters['epsilon_r'] * C_LIGHT**2)

        f_edd = Mdot / Mdot_edd

        # Bolometric luminosity
        L_bol = self.parameters['epsilon_r'] * Mdot * C_LIGHT**2

        if f_edd > self.parameters['eddington_factor_crit']:
            # Quasar/radiative mode
            E_dot = self.parameters['epsilon_f'] * L_bol

            # Radiation pressure on dust (momentum boost)
            boost = self.parameters['momentum_boost']
            p_dot = boost * L_bol / C_LIGHT

            mode = "quasar"

        else:
            # Jet/kinetic mode
            E_dot = self.parameters['jet_efficiency'] * Mdot * C_LIGHT**2
            v_jet = self.parameters['jet_velocity'] * 1e5  # cm/s
            p_dot = E_dot / v_jet

            mode = "jet"

        return {
            'energy_injection_rate': E_dot,
            'momentum_injection_rate': p_dot,
            'luminosity': L_bol,
            'eddington_ratio': f_edd,
            'feedback_mode': mode
        }


class CoolingFunction:
    """
    Gas cooling function for ISM/CGM physics.

    Includes:
    - Atomic line cooling
    - Metal cooling
    - Molecular cooling
    - Dust cooling
    """

    def __init__(self, metallicity: float = 1.0, redshift: float = 0.0):
        """
        Parameters
        ----------
        metallicity : float
            Metallicity in solar units
        redshift : float
            Redshift for CMB floor
        """
        self.metallicity = metallicity
        self.redshift = redshift
        self.T_cmb = 2.725 * (1 + redshift)

        # Cooling table temperatures
        self._T_table = np.logspace(1, 9, 100)
        self._build_cooling_table()

    def _build_cooling_table(self):
        """Build interpolation table for cooling function."""
        T = self._T_table

        # Primordial cooling (H, He)
        Lambda_prim = np.zeros_like(T)

        # Collisional ionization
        Lambda_prim += 1.27e-21 * np.sqrt(T) * np.exp(-157809 / T) / (1 + np.sqrt(T / 1e5))

        # Recombination
        Lambda_prim += 8.7e-27 * np.sqrt(T) * (T / 1e3)**(-0.2) / (1 + (T / 1e6)**0.7)

        # Collisional excitation
        Lambda_prim += 7.5e-19 * np.exp(-118348 / T) / (1 + np.sqrt(T / 1e5))

        # Bremsstrahlung
        Lambda_prim += 1.42e-27 * np.sqrt(T)

        # Metal cooling (approximate CIE)
        Lambda_metal = np.zeros_like(T)

        # Low-T metal lines (OI, CII, etc.)
        Lambda_metal += 2e-26 * (T / 1e4)**0.5 * np.exp(-92 / T)

        # High-T metal lines
        Lambda_metal += 1e-22 * np.exp(-(np.log10(T) - 5.25)**2 / 0.5)

        self._Lambda_prim = Lambda_prim
        self._Lambda_metal = Lambda_metal

    def cooling_rate(self, temperature: float, density: float) -> float:
        """
        Compute cooling rate.

        Parameters
        ----------
        temperature : float
            Gas temperature in K
        density : float
            Gas density in g/cm^3

        Returns
        -------
        float
            Cooling rate in erg/cm^3/s
        """
        # Clamp temperature
        T = np.clip(temperature, 10, 1e9)

        # Interpolate cooling function
        Lambda_prim = np.interp(T, self._T_table, self._Lambda_prim)
        Lambda_metal = np.interp(T, self._T_table, self._Lambda_metal)

        Lambda_total = Lambda_prim + self.metallicity * Lambda_metal

        # Number density
        n_H = density / (1.4 * M_PROTON)

        # Cooling rate
        cool_rate = n_H**2 * Lambda_total

        # CMB floor
        if T < self.T_cmb:
            cool_rate = 0.0

        return cool_rate

    def cooling_time(self, temperature: float, density: float) -> float:
        """
        Compute cooling time.

        Parameters
        ----------
        temperature : float
            Gas temperature in K
        density : float
            Gas density in g/cm^3

        Returns
        -------
        float
            Cooling time in years
        """
        cool_rate = self.cooling_rate(temperature, density)

        if cool_rate <= 0:
            return np.inf

        # Thermal energy
        n_H = density / (1.4 * M_PROTON)
        E_thermal = 1.5 * n_H * K_BOLTZMANN * temperature

        t_cool = E_thermal / cool_rate

        return t_cool / YR


class ZoomRegion:
    """
    Defines a zoom-in simulation region.

    Handles:
    - Lagrangian region selection
    - Boundary conditions
    - Resolution hierarchy
    """

    def __init__(self, center: np.ndarray, radius: float,
                 base_resolution: float, max_refinement: int = 5):
        """
        Parameters
        ----------
        center : ndarray
            Center coordinates (kpc)
        radius : float
            Region radius (kpc)
        base_resolution : float
            Base resolution (pc)
        max_refinement : int
            Maximum refinement levels
        """
        self.center = center
        self.radius = radius
        self.base_resolution = base_resolution
        self.max_refinement = max_refinement

        self.refinement_levels = []
        self._setup_refinement_hierarchy()

    def _setup_refinement_hierarchy(self):
        """Set up nested refinement regions."""
        current_radius = self.radius
        current_res = self.base_resolution

        for level in range(self.max_refinement + 1):
            self.refinement_levels.append({
                'level': level,
                'radius': current_radius,
                'resolution': current_res,
                'cell_mass': None  # Set based on density
            })
            current_radius /= 2
            current_res /= 2

    def get_refinement_level(self, position: np.ndarray) -> int:
        """
        Determine refinement level at position.

        Parameters
        ----------
        position : ndarray
            Position coordinates (kpc)

        Returns
        -------
        int
            Refinement level (0 = coarsest)
        """
        r = np.linalg.norm(position - self.center)

        for level_info in reversed(self.refinement_levels):
            if r <= level_info['radius']:
                return level_info['level']

        return 0

    def get_resolution(self, position: np.ndarray) -> float:
        """Get spatial resolution at position."""
        level = self.get_refinement_level(position)
        return self.refinement_levels[level]['resolution']


class BoundaryConditionHandler:
    """
    Handles boundary conditions between simulation scales.

    Supports:
    - Fixed boundary
    - Periodic boundary
    - Outflow boundary
    - Inflowing boundary from larger scale
    """

    def __init__(self, boundary_type: str = "outflow"):
        """
        Parameters
        ----------
        boundary_type : str
            Type of boundary ("fixed", "periodic", "outflow", "inflow")
        """
        self.boundary_type = boundary_type
        self.inflow_conditions: Dict[str, Any] = {}

    def set_inflow_conditions(self, density: float, velocity: np.ndarray,
                              temperature: float, metallicity: float = 1.0):
        """
        Set inflow boundary conditions from larger scale.

        Parameters
        ----------
        density : float
            Inflow density (g/cm^3)
        velocity : ndarray
            Inflow velocity vector (cm/s)
        temperature : float
            Inflow temperature (K)
        metallicity : float
            Inflow metallicity (solar)
        """
        self.inflow_conditions = {
            'density': density,
            'velocity': velocity,
            'temperature': temperature,
            'metallicity': metallicity
        }

    def apply_boundary(self, field: np.ndarray, axis: int,
                       side: str) -> np.ndarray:
        """
        Apply boundary conditions to field.

        Parameters
        ----------
        field : ndarray
            Field values
        axis : int
            Axis for boundary (0, 1, or 2)
        side : str
            Side of boundary ("lower" or "upper")

        Returns
        -------
        ndarray
            Field with boundary applied
        """
        if self.boundary_type == "periodic":
            # Wrap around
            if side == "lower":
                field = np.roll(field, 1, axis=axis)
            else:
                field = np.roll(field, -1, axis=axis)

        elif self.boundary_type == "outflow":
            # Zero gradient
            slices = [slice(None)] * field.ndim
            if side == "lower":
                slices[axis] = 0
                field[tuple(slices)] = field[tuple([slice(None) if i != axis else 1
                                                    for i in range(field.ndim)])]
            else:
                slices[axis] = -1
                field[tuple(slices)] = field[tuple([slice(None) if i != axis else -2
                                                    for i in range(field.ndim)])]

        elif self.boundary_type == "fixed":
            # Keep boundary values fixed
            pass

        return field


class ScaleCoupler:
    """
    Couples simulations at different scales.

    Handles:
    - Downsampling from large to small scale
    - Upsampling/feedback from small to large scale
    - Conservation enforcement
    """

    def __init__(self, upper_scale: ScaleLevel, lower_scale: ScaleLevel,
                 refinement_factor: int = 4):
        """
        Parameters
        ----------
        upper_scale : ScaleLevel
            Coarser scale level
        lower_scale : ScaleLevel
            Finer scale level
        refinement_factor : int
            Resolution ratio between scales
        """
        self.upper_scale = upper_scale
        self.lower_scale = lower_scale
        self.refinement_factor = refinement_factor

        self.conserved_quantities = ['mass', 'momentum', 'energy']

    def downsample(self, coarse_field: np.ndarray,
                   interpolation: str = "linear") -> np.ndarray:
        """
        Interpolate from coarse to fine grid.

        Parameters
        ----------
        coarse_field : ndarray
            Field on coarse grid
        interpolation : str
            Interpolation method ("nearest", "linear", "cubic")

        Returns
        -------
        ndarray
            Field interpolated to fine grid
        """
        from scipy import ndimage

        factor = self.refinement_factor

        if interpolation == "nearest":
            fine_field = np.repeat(np.repeat(np.repeat(
                coarse_field, factor, axis=0), factor, axis=1), factor, axis=2)

        elif interpolation == "linear":
            fine_field = ndimage.zoom(coarse_field, factor, order=1)

        elif interpolation == "cubic":
            fine_field = ndimage.zoom(coarse_field, factor, order=3)

        else:
            fine_field = ndimage.zoom(coarse_field, factor, order=1)

        return fine_field

    def upsample(self, fine_field: np.ndarray,
                 operation: str = "average") -> np.ndarray:
        """
        Coarsen from fine to coarse grid.

        Parameters
        ----------
        fine_field : ndarray
            Field on fine grid
        operation : str
            Coarsening operation ("average", "sum", "max")

        Returns
        -------
        ndarray
            Field on coarse grid
        """
        factor = self.refinement_factor
        shape = fine_field.shape

        # Reshape for block reduction
        new_shape = (shape[0] // factor, factor,
                     shape[1] // factor, factor,
                     shape[2] // factor, factor)

        reshaped = fine_field.reshape(new_shape)

        if operation == "average":
            coarse_field = reshaped.mean(axis=(1, 3, 5))
        elif operation == "sum":
            coarse_field = reshaped.sum(axis=(1, 3, 5))
        elif operation == "max":
            coarse_field = reshaped.max(axis=(1, 3, 5))
        else:
            coarse_field = reshaped.mean(axis=(1, 3, 5))

        return coarse_field

    def enforce_conservation(self, fine_field: np.ndarray,
                             coarse_total: float) -> np.ndarray:
        """
        Enforce conservation between scales.

        Parameters
        ----------
        fine_field : ndarray
            Field on fine grid
        coarse_total : float
            Total value that must be conserved

        Returns
        -------
        ndarray
            Adjusted fine field
        """
        fine_total = fine_field.sum()

        if fine_total > 0:
            fine_field *= coarse_total / fine_total

        return fine_field


class MultiScaleSimulation:
    """
    Framework for multi-scale astrophysical simulations.

    Coordinates:
    - Multiple zoom regions
    - Sub-grid physics models
    - Scale coupling
    - Feedback prescriptions
    """

    def __init__(self, box_size: float, base_resolution: float):
        """
        Parameters
        ----------
        box_size : float
            Simulation box size (kpc)
        base_resolution : float
            Base resolution (pc)
        """
        self.box_size = box_size
        self.base_resolution = base_resolution

        self.zoom_regions: List[ZoomRegion] = []
        self.subgrid_models: List[SubGridModel] = []
        self.scale_couplers: List[ScaleCoupler] = []
        self.cooling = CoolingFunction()

        # Fields
        self.density: Optional[np.ndarray] = None
        self.velocity: Optional[np.ndarray] = None
        self.temperature: Optional[np.ndarray] = None
        self.metallicity: Optional[np.ndarray] = None

    def add_zoom_region(self, center: np.ndarray, radius: float,
                        max_refinement: int = 5):
        """Add a zoom-in region."""
        zoom = ZoomRegion(center, radius, self.base_resolution, max_refinement)
        self.zoom_regions.append(zoom)

    def add_subgrid_model(self, model: SubGridModel):
        """Add a sub-grid physics model."""
        self.subgrid_models.append(model)

    def add_scale_coupler(self, upper: ScaleLevel, lower: ScaleLevel,
                          factor: int = 4):
        """Add scale coupling."""
        coupler = ScaleCoupler(upper, lower, factor)
        self.scale_couplers.append(coupler)

    def initialize_fields(self, n_cells: int):
        """Initialize simulation fields."""
        self.density = np.ones((n_cells, n_cells, n_cells)) * 1e-24  # g/cm^3
        self.velocity = np.zeros((3, n_cells, n_cells, n_cells))  # cm/s
        self.temperature = np.ones((n_cells, n_cells, n_cells)) * 1e4  # K
        self.metallicity = np.ones((n_cells, n_cells, n_cells))  # solar

    def get_local_properties(self, i: int, j: int, k: int) -> Dict[str, Any]:
        """Get local gas properties at cell."""
        cell_size = self.base_resolution  # Will be refined based on zoom

        # Check zoom regions
        position = np.array([i, j, k]) * cell_size / 1000  # kpc
        for zoom in self.zoom_regions:
            cell_size = min(cell_size, zoom.get_resolution(position))

        return {
            'density': self.density[i, j, k],
            'temperature': self.temperature[i, j, k],
            'metallicity': self.metallicity[i, j, k],
            'velocity': self.velocity[:, i, j, k],
            'cell_size': cell_size,
            'cell_volume': (cell_size * PC)**3
        }

    def apply_subgrid_physics(self, dt: float) -> Dict[str, np.ndarray]:
        """
        Apply all sub-grid models.

        Parameters
        ----------
        dt : float
            Timestep in seconds

        Returns
        -------
        dict
            Source terms from sub-grid physics
        """
        source_terms = {
            'mass': np.zeros_like(self.density),
            'energy': np.zeros_like(self.density),
            'momentum': np.zeros_like(self.velocity)
        }

        if self.density is None:
            return source_terms

        nx, ny, nz = self.density.shape

        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    props = self.get_local_properties(i, j, k)
                    props['timestep'] = dt

                    for model in self.subgrid_models:
                        if props['cell_size'] > model.scale_below:
                            continue

                        result = model.compute(props)

                        # Accumulate source terms
                        if 'stellar_mass_formed' in result:
                            source_terms['mass'][i, j, k] -= result['stellar_mass_formed'] * M_SUN
                        if 'energy_injection_rate' in result:
                            source_terms['energy'][i, j, k] += result['energy_injection_rate'] * dt
                        if 'momentum_injection_rate' in result:
                            # Distribute isotropically
                            source_terms['momentum'][:, i, j, k] += result['momentum_injection_rate'] * dt / 3

        return source_terms

    def compute_cooling(self, dt: float) -> np.ndarray:
        """
        Compute radiative cooling.

        Parameters
        ----------
        dt : float
            Timestep in seconds

        Returns
        -------
        ndarray
            Energy loss per cell
        """
        if self.density is None or self.temperature is None:
            return np.zeros((1, 1, 1))

        energy_loss = np.zeros_like(self.density)

        nx, ny, nz = self.density.shape
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    self.cooling.metallicity = self.metallicity[i, j, k]
                    cool_rate = self.cooling.cooling_rate(
                        self.temperature[i, j, k],
                        self.density[i, j, k]
                    )
                    props = self.get_local_properties(i, j, k)
                    energy_loss[i, j, k] = cool_rate * props['cell_volume'] * dt

        return energy_loss


class HierarchicalRefinement:
    """
    Adaptive mesh refinement criteria and implementation.

    Supports:
    - Density-based refinement
    - Gradient-based refinement
    - Geometry-based refinement
    """

    def __init__(self, max_level: int = 8):
        """
        Parameters
        ----------
        max_level : int
            Maximum refinement level
        """
        self.max_level = max_level
        self.refinement_criteria: List[Callable] = []

    def add_density_criterion(self, threshold: float, levels: int = 1):
        """Add density-based refinement criterion."""

        def criterion(density: np.ndarray, level: int) -> np.ndarray:
            if level >= levels:
                return np.zeros_like(density, dtype=bool)
            return density > threshold

        self.refinement_criteria.append(criterion)

    def add_gradient_criterion(self, threshold: float, levels: int = 1):
        """Add gradient-based refinement criterion."""

        def criterion(field: np.ndarray, level: int) -> np.ndarray:
            if level >= levels:
                return np.zeros_like(field, dtype=bool)

            grad_x = np.abs(np.diff(field, axis=0, prepend=field[:1]))
            grad_y = np.abs(np.diff(field, axis=1, prepend=field[:, :1]))
            grad_z = np.abs(np.diff(field, axis=2, prepend=field[:, :, :1]))

            grad_mag = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
            return grad_mag / (np.abs(field) + 1e-10) > threshold

        self.refinement_criteria.append(criterion)

    def add_jeans_criterion(self, n_jeans: int = 4):
        """Add Jeans length resolution criterion."""

        def criterion(density: np.ndarray, temperature: np.ndarray,
                      cell_size: float, level: int) -> np.ndarray:
            # Jeans length
            cs = np.sqrt(K_BOLTZMANN * temperature / M_PROTON)
            lambda_j = cs * np.sqrt(np.pi / (G_GRAV * density))

            # Require n_jeans cells per Jeans length
            return lambda_j < n_jeans * cell_size

        self.refinement_criteria.append(criterion)

    def check_refinement(self, fields: Dict[str, np.ndarray],
                        current_level: int) -> np.ndarray:
        """
        Check which cells need refinement.

        Parameters
        ----------
        fields : dict
            Dictionary of field arrays
        current_level : int
            Current refinement level

        Returns
        -------
        ndarray
            Boolean array indicating cells to refine
        """
        if current_level >= self.max_level:
            return np.array([], dtype=bool)
