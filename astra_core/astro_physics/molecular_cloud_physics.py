
"""
Documentation for multi_scale_inference module.

This module provides multi_scale_inference capabilities for STAN.
Enhanced through self-evolution cycle 84.
"""

#!/usr/bin/env python3
"""
Molecular Cloud and Dust Physics Module for ASTRO-SWARM
========================================================

Comprehensive physics for analyzing galactic molecular clouds and
interstellar dust, integrated with stigmergic swarm intelligence.

Physical Models:
1. Molecular Line Spectroscopy (CO, HCN, N2H+, NH3, CS, etc.)
2. Dust Emission and Extinction
3. Column Density and Mass Estimation
4. Temperature and Density Structure
5. Turbulence and Kinematics
6. Magnetic Field Tracers
7. Chemical Abundances

Key References:
- Hildebrand 1983 (dust opacity)
- Ossenkopf & Henning 1994 (dust models)
- Kauffmann et al. 2008 (mass-size relation)
- Lada et al. 2010 (star formation thresholds)
- Planck Collaboration (dust properties)

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from abc import ABC, abstractmethod

# Physical Constants (CGS)
k_B = 1.38e-16          # Boltzmann constant (erg/K)
h_planck = 6.626e-27    # Planck constant (erg s)
c_light = 2.998e10      # Speed of light (cm/s)
m_H = 1.67e-24          # Hydrogen mass (g)
m_H2 = 2 * m_H          # H2 mass (g)
G_cgs = 6.67e-8         # Gravitational constant
pc_to_cm = 3.086e18     # parsec to cm
Msun_to_g = 1.989e33    # Solar mass to grams
AU_to_cm = 1.496e13     # AU to cm
Jy_to_cgs = 1e-23       # Jansky to erg/s/cm²/Hz


# =============================================================================
# MOLECULAR LINE DATABASE
# =============================================================================

@dataclass
class MolecularTransition:
    """Properties of a molecular line transition"""
    molecule: str
    transition: str          # e.g., "J=1-0", "J=2-1"
    rest_frequency: float    # GHz
    upper_energy: float      # K (E_u/k_B)
    einstein_A: float        # s⁻¹
    critical_density: float  # cm⁻³
    abundance_typical: float # X = n(mol)/n(H2)
    tracer_of: str          # What physical condition it traces
    optical_depth_typical: str  # "thin", "moderate", "thick"


class MolecularLineDatabase:
    """
    Database of molecular transitions for ISM spectroscopy

    Organized by molecule with key transitions for cloud analysis.
    """

    TRANSITIONS = {
        # Carbon Monoxide - most common tracer
        "12CO_1-0": MolecularTransition(
            molecule="12CO", transition="J=1-0",
            rest_frequency=115.271, upper_energy=5.53,
            einstein_A=7.203e-8, critical_density=2.2e3,
            abundance_typical=1e-4, tracer_of="total_molecular_gas",
            optical_depth_typical="thick"
        ),
        "12CO_2-1": MolecularTransition(
            molecule="12CO", transition="J=2-1",
            rest_frequency=230.538, upper_energy=16.60,
            einstein_A=6.910e-7, critical_density=1.1e4,
            abundance_typical=1e-4, tracer_of="warm_molecular_gas",
            optical_depth_typical="thick"
        ),
        "13CO_1-0": MolecularTransition(
            molecule="13CO", transition="J=1-0",
            rest_frequency=110.201, upper_energy=5.29,
            einstein_A=6.294e-8, critical_density=2.0e3,
            abundance_typical=1.4e-6, tracer_of="column_density",
            optical_depth_typical="moderate"
        ),
        "C18O_1-0": MolecularTransition(
            molecule="C18O", transition="J=1-0",
            rest_frequency=109.782, upper_energy=5.27,
            einstein_A=6.266e-8, critical_density=2.0e3,
            abundance_typical=1.7e-7, tracer_of="column_density_optically_thin",
            optical_depth_typical="thin"
        ),

        # Dense gas tracers
        "HCN_1-0": MolecularTransition(
            molecule="HCN", transition="J=1-0",
            rest_frequency=88.632, upper_energy=4.25,
            einstein_A=2.407e-5, critical_density=2.6e6,
            abundance_typical=2e-8, tracer_of="dense_gas",
            optical_depth_typical="moderate"
        ),
        "HCO+_1-0": MolecularTransition(
            molecule="HCO+", transition="J=1-0",
            rest_frequency=89.189, upper_energy=4.28,
            einstein_A=4.187e-5, critical_density=1.6e5,
            abundance_typical=1e-9, tracer_of="dense_ionized_gas",
            optical_depth_typical="moderate"
        ),
        "N2H+_1-0": MolecularTransition(
            molecule="N2H+", transition="J=1-0",
            rest_frequency=93.173, upper_energy=4.47,
            einstein_A=3.628e-5, critical_density=1.4e5,
            abundance_typical=5e-10, tracer_of="cold_dense_cores",
            optical_depth_typical="thin"
        ),
        "CS_2-1": MolecularTransition(
            molecule="CS", transition="J=2-1",
            rest_frequency=97.981, upper_energy=7.05,
            einstein_A=1.679e-5, critical_density=4.3e5,
            abundance_typical=1e-9, tracer_of="dense_gas",
            optical_depth_typical="moderate"
        ),

        # Temperature tracers
        "NH3_1,1": MolecularTransition(
            molecule="NH3", transition="(1,1)",
            rest_frequency=23.694, upper_energy=23.4,
            einstein_A=1.712e-7, critical_density=1.8e3,
            abundance_typical=3e-8, tracer_of="kinetic_temperature",
            optical_depth_typical="moderate"
        ),
        "NH3_2,2": MolecularTransition(
            molecule="NH3", transition="(2,2)",
            rest_frequency=23.723, upper_energy=64.9,
            einstein_A=2.239e-7, critical_density=2.1e3,
            abundance_typical=3e-8, tracer_of="kinetic_temperature",
            optical_depth_typical="moderate"
        ),

        # Shock/outflow tracers
        "SiO_2-1": MolecularTransition(
            molecule="SiO", transition="J=2-1",
            rest_frequency=86.847, upper_energy=6.25,
            einstein_A=2.927e-5, critical_density=3.4e5,
            abundance_typical=1e-12, tracer_of="shocks_outflows",
            optical_depth_typical="thin"
        ),
        "CH3OH_2-1": MolecularTransition(
            molecule="CH3OH", transition="2(0)-1(0)A+",
            rest_frequency=96.741, upper_energy=12.5,
            einstein_A=3.407e-6, critical_density=1.1e5,
            abundance_typical=1e-9, tracer_of="hot_cores_shocks",
            optical_depth_typical="thin"
        ),

        # Atomic fine structure
        "CI_1-0": MolecularTransition(
            molecule="CI", transition="3P1-3P0",
            rest_frequency=492.161, upper_energy=23.6,
            einstein_A=7.880e-8, critical_density=5e2,
            abundance_typical=1e-5, tracer_of="PDR_interface",
            optical_depth_typical="moderate"
        ),
        "CII_158um": MolecularTransition(
            molecule="CII", transition="2P3/2-2P1/2",
            rest_frequency=1900.537, upper_energy=91.2,
            einstein_A=2.300e-6, critical_density=2.8e3,
            abundance_typical=1.4e-4, tracer_of="PDR_ionized_carbon",
            optical_depth_typical="thick"
        ),
    }

    @classmethod
    def get_transition(cls, name: str) -> MolecularTransition:
        """Get transition by name"""
        return cls.TRANSITIONS.get(name)

    @classmethod
    def get_dense_gas_tracers(cls) -> List[MolecularTransition]:
        """Get transitions that trace dense gas (n > 10⁴ cm⁻³)"""
        return [t for t in cls.TRANSITIONS.values()
                if t.critical_density > 1e4]

    @classmethod
    def get_temperature_tracers(cls) -> List[MolecularTransition]:
        """Get transitions useful for temperature measurement"""
        return [t for t in cls.TRANSITIONS.values()
                if t.tracer_of == "kinetic_temperature"]


# =============================================================================
# DUST MODELS
# =============================================================================

class DustModel(Enum):
    """Standard dust models for the ISM"""
    MRN = "mrn"                    # Mathis, Rumpl, Nordsieck 1977
    WD01 = "wd01"                  # Weingartner & Draine 2001
    OSSENKOPF_THIN = "oh94_thin"   # Ossenkopf & Henning 1994 (thin ice)
    OSSENKOPF_THICK = "oh94_thick" # Ossenkopf & Henning 1994 (thick ice)
    PLANCK = "planck"              # Planck all-sky dust model


@dataclass
class DustProperties:
    """
    Physical properties of interstellar dust

    Key quantities:
    - κ_ν: Dust opacity (cm²/g of dust)
    - β: Spectral index of dust emissivity
    - Gas-to-dust ratio
    - Size distribution parameters
    """
    model: str

    # Opacity at reference wavelength
    kappa_ref: float        # cm²/g at reference λ
    lambda_ref: float       # Reference wavelength (μm)

    # Spectral index
    beta: float             # κ_ν ∝ ν^β
    beta_uncertainty: float

    # Gas-to-dust ratio
    gas_to_dust: float      # M_gas / M_dust

    # Temperature range of applicability
    T_min: float            # K
    T_max: float            # K

    # Size distribution (MRN: dn/da ∝ a^(-3.5))
    a_min: float            # Minimum grain size (μm)
    a_max: float            # Maximum grain size (μm)
    size_index: float       # Power law index

    # Composition
    silicate_fraction: float  # Mass fraction silicates
    carbon_fraction: float    # Mass fraction carbonaceous

    def kappa_nu(self, wavelength_um: float) -> float:
        """
        Dust opacity at given wavelength

        κ_ν = κ_ref × (λ_ref / λ)^β
        """
        return self.kappa_ref * (self.lambda_ref / wavelength_um) ** self.beta

    def kappa_nu_frequency(self, freq_GHz: float) -> float:
        """Dust opacity at given frequency"""
        wavelength_um = c_light / (freq_GHz * 1e9) * 1e4  # cm to μm
        return self.kappa_nu(wavelength_um)


class DustModelLibrary:
    """
    Library of standard dust models for different environments
    """

    MODELS = {
        DustModel.MRN: DustProperties(
            model="MRN (Mathis+ 1977)",
            kappa_ref=10.0, lambda_ref=250.0,
            beta=2.0, beta_uncertainty=0.2,
            gas_to_dust=100.0,
            T_min=10, T_max=50,
            a_min=0.005, a_max=0.25, size_index=-3.5,
            silicate_fraction=0.53, carbon_fraction=0.47
        ),
        DustModel.WD01: DustProperties(
            model="Weingartner & Draine 2001",
            kappa_ref=4.0, lambda_ref=250.0,
            beta=1.8, beta_uncertainty=0.15,
            gas_to_dust=124.0,
            T_min=15, T_max=100,
            a_min=0.00035, a_max=0.25, size_index=-3.5,
            silicate_fraction=0.55, carbon_fraction=0.45
        ),
        DustModel.OSSENKOPF_THIN: DustProperties(
            model="Ossenkopf & Henning 1994 (thin ice)",
            kappa_ref=5.0, lambda_ref=250.0,
            beta=1.8, beta_uncertainty=0.1,
            gas_to_dust=100.0,
            T_min=10, T_max=30,
            a_min=0.005, a_max=0.25, size_index=-3.5,
            silicate_fraction=0.50, carbon_fraction=0.30
        ),
        DustModel.OSSENKOPF_THICK: DustProperties(
            model="Ossenkopf & Henning 1994 (thick ice)",
            kappa_ref=1.85, lambda_ref=1300.0,  # 1.3mm reference
            beta=1.5, beta_uncertainty=0.1,
            gas_to_dust=100.0,
            T_min=10, T_max=25,
            a_min=0.01, a_max=1.0, size_index=-3.0,  # Grain growth
            silicate_fraction=0.40, carbon_fraction=0.25
        ),
        DustModel.PLANCK: DustProperties(
            model="Planck Collaboration",
            kappa_ref=0.92, lambda_ref=353.0,  # 353 GHz = 850 μm
            beta=1.62, beta_uncertainty=0.10,
            gas_to_dust=136.0,
            T_min=14, T_max=30,
            a_min=0.001, a_max=0.5, size_index=-3.5,
            silicate_fraction=0.50, carbon_fraction=0.50
        ),
    }

    @classmethod
    def get_model(cls, model: DustModel) -> DustProperties:
        return cls.MODELS[model]

    @classmethod
    def get_dense_cloud_model(cls) -> DustProperties:
        """Get model appropriate for dense molecular clouds"""
        return cls.MODELS[DustModel.OSSENKOPF_THICK]

    @classmethod
    def get_diffuse_ism_model(cls) -> DustProperties:
        """Get model appropriate for diffuse ISM"""
        return cls.MODELS[DustModel.WD01]


# =============================================================================
# MOLECULAR CLOUD PHYSICS ENGINE
# =============================================================================

@dataclass
class CloudSpectralLine:
    """Observed spectral line properties"""
    transition: str
    peak_temperature: float      # K (T_mb or T_A*)
    velocity_centroid: float     # km/s (LSR)
    line_width: float            # km/s (FWHM)
    integrated_intensity: float  # K km/s
    rms_noise: float            # K
    optical_depth: Optional[float] = None
    excitation_temp: Optional[float] = None


@dataclass
class DustSED:
    """Observed dust spectral energy distribution"""
    wavelengths: np.ndarray      # μm
    fluxes: np.ndarray           # Jy
    flux_errors: np.ndarray      # Jy
    beam_sizes: np.ndarray       # arcsec (FWHM)
    distance_pc: float           # Distance to source


@dataclass
class MolecularCloudProperties:
    """Derived physical properties of a molecular cloud"""
    # Basic properties
    name: str
    distance_pc: float

    # Size and structure
    angular_size_arcmin: float
    physical_size_pc: float
    aspect_ratio: float

    # Mass estimates
    mass_dust_msun: float
    mass_virial_msun: float
    mass_lte_msun: float
    mass_uncertainty_factor: float

    # Column density
    N_H2_peak: float             # cm⁻²
    N_H2_mean: float             # cm⁻²
    A_V_peak: float              # mag

    # Temperature
    T_dust: float                # K
    T_dust_uncertainty: float    # K
    T_kinetic: float             # K (from NH3 or other)
    T_excitation: float          # K (from CO)

    # Density
    n_H2_mean: float             # cm⁻³
    n_H2_peak: float             # cm⁻³
    volume_filling_factor: float

    # Kinematics
    v_lsr: float                 # km/s
    sigma_v: float               # km/s (1D velocity dispersion)
    sigma_nt: float              # km/s (non-thermal)
    mach_number: float           # σ_nt / c_s

    # Stability
    virial_parameter: float      # α_vir = 2K/|W|
    jeans_mass: float            # M_J in M_sun
    bonnor_ebert_mass: float     # M_BE in M_sun
    is_gravitationally_bound: bool

    # Chemistry
    CO_abundance: float          # X_CO = N(CO)/N(H2)
    depletion_factor: float      # CO depletion onto grains
    ionization_fraction: float   # n(e)/n(H2)

    # Star formation
    dense_gas_fraction: float    # M(n>10⁴)/M_total
    star_formation_rate: float   # M_sun/yr
    star_formation_efficiency: float

    # Magnetic field (if measured)
    B_field_strength: Optional[float] = None  # μG
    mass_to_flux_ratio: Optional[float] = None

    # Metadata
    analysis_method: str = ""
    references: List[str] = field(default_factory=list)


class MolecularCloudPhysicsEngine:
    """
    Physics engine for molecular cloud analysis

    Provides forward models and inference methods for:
    1. Spectral line analysis
    2. Dust continuum analysis
    3. Mass estimation
    4. Stability analysis
    5. Star formation diagnostics
    """

    # Standard conversion factors
    X_CO = 2.0e20  # cm⁻² / (K km/s) - Milky Way average
    N_H2_to_AV = 9.4e20  # cm⁻² per mag (Bohlin+ 1978)

    def __init__(self, dust_model: DustModel = DustModel.OSSENKOPF_THICK):
        self.dust = DustModelLibrary.get_model(dust_model)
        self.lines = MolecularLineDatabase()

    # =========================================================================
    # SPECTRAL LINE ANALYSIS
    # =========================================================================

    def analyze_co_isotopologues(self,
                                  co12: CloudSpectralLine,
                                  co13: CloudSpectralLine,
                                  c18o: Optional[CloudSpectralLine] = None
                                  ) -> Dict[str, float]:
        """
        Analyze CO isotopologue ratios to get optical depth and column density

        Method: Use 12CO/13CO ratio to estimate τ(12CO), then derive N(H2)

        Returns:
            Dictionary with optical depth, excitation temp, column density
        """
        # Standard isotope ratios (Galactocentric gradient)
        R_12_13 = 77.0  # 12C/13C ratio (local ISM)
        R_16_18 = 560.0  # 16O/18O ratio

        # Estimate optical depth from line ratio
        # T_12 / T_13 = (1 - exp(-τ_12)) / (1 - exp(-τ_13))
        # With τ_13 = τ_12 / R

        T_ratio = co12.peak_temperature / (co13.peak_temperature + 1e-10)

        # Iterative solution for τ_12
        tau_12 = self._solve_optical_depth(T_ratio, R_12_13)

        # Excitation temperature from 12CO (assuming fills beam)
        T_ex = self._brightness_to_tex(co12.peak_temperature,
                                        self.lines.get_transition("12CO_1-0").rest_frequency)

        # Column density from 13CO (optically thinner)
        tau_13 = tau_12 / R_12_13
        N_13CO = self._column_density_lte(
            co13.integrated_intensity,
            T_ex,
            self.lines.get_transition("13CO_1-0"),
            tau_13
        )

        # Convert to H2 column density
        X_13CO = 1.4e-6  # 13CO/H2 abundance
        N_H2 = N_13CO / X_13CO

        # If C18O available, use for better constraint
        if c18o is not None:
            N_C18O = self._column_density_lte(
                c18o.integrated_intensity,
                T_ex,
                self.lines.get_transition("C18O_1-0"),
                optical_depth=0.1  # Assume optically thin
            )
            X_C18O = 1.7e-7
            N_H2_c18o = N_C18O / X_C18O
            # Average the two estimates
            N_H2 = (N_H2 + N_H2_c18o) / 2

        return {
            'tau_12CO': tau_12,
            'tau_13CO': tau_13,
            'T_ex': T_ex,
            'N_13CO': N_13CO,
            'N_H2': N_H2,
            'A_V': N_H2 / self.N_H2_to_AV
        }

    def analyze_nh3_temperature(self,
                                nh3_11: CloudSpectralLine,
                                nh3_22: CloudSpectralLine) -> Dict[str, float]:
        """
        Derive kinetic temperature from NH3 (1,1) and (2,2) lines

        The rotational temperature is derived from the line ratio,
        then converted to kinetic temperature.

        Returns:
            Dictionary with T_rot, T_kin, optical depth, column density
        """
        # Energy difference between (2,2) and (1,1) levels
        Delta_E = 41.5  # K

        # Line ratio gives rotational temperature
        # Assuming both lines optically thin
        ratio = nh3_22.integrated_intensity / (nh3_11.integrated_intensity + 1e-10)

        # T_rot from Boltzmann equation
        # Includes statistical weights g(2,2)/g(1,1) = 5/3
        T_rot = -Delta_E / np.log(ratio * 3/5 + 1e-10)
        T_rot = max(T_rot, 8.0)  # Physical minimum

        # Convert to kinetic temperature (Ho & Townes 1983)
        # T_kin = T_rot / (1 - (T_rot/42) * ln(1 + 1.1*exp(-16/T_rot)))
        T_kin = T_rot / (1 - (T_rot/42) * np.log(1 + 1.1*np.exp(-16/T_rot)))

        # Optical depth from hyperfine structure (if resolved)
        # Simplified: assume τ ~ 1 for typical clouds
        tau_11 = 1.0

        # Column density
        N_NH3 = 1.6e13 * T_rot * nh3_11.integrated_intensity / (1 - np.exp(-tau_11))

        return {
            'T_rot': T_rot,
            'T_kin': T_kin,
            'tau_11': tau_11,
            'N_NH3': N_NH3,
            'N_H2': N_NH3 / 3e-8  # Assuming standard abundance
        }

    def analyze_dense_gas(self,
                          hcn: CloudSpectralLine,
                          hcop: Optional[CloudSpectralLine] = None,
                          n2hp: Optional[CloudSpectralLine] = None) -> Dict[str, float]:
        """
        Analyze dense gas tracers (HCN, HCO+, N2H+)

        These molecules have high critical densities and trace
        gas suitable for star formation (n > 10⁴ cm⁻³).
        """
        results = {}

        # HCN analysis
        hcn_trans = self.lines.get_transition("HCN_1-0")

        # Integrated intensity gives dense gas mass proxy
        # L_HCN ∝ M_dense (Gao & Solomon 2004)
        results['I_HCN'] = hcn.integrated_intensity
        results['n_crit_HCN'] = hcn_trans.critical_density

        if hcop is not None:
            # HCN/HCO+ ratio sensitive to ionization and chemistry
            ratio_hcn_hcop = hcn.integrated_intensity / (hcop.integrated_intensity + 1e-10)
            results['HCN_HCO+_ratio'] = ratio_hcn_hcop

            # High ratio (>1) suggests XDR or high CR ionization
            # Low ratio (<1) suggests PDR or high ionization fraction
            if ratio_hcn_hcop > 2:
                results['chemistry_indicator'] = "XDR_or_high_CR"
            elif ratio_hcn_hcop < 0.5:
                results['chemistry_indicator'] = "PDR_dominated"
            else:
                results['chemistry_indicator'] = "normal"

        if n2hp is not None:
            # N2H+ survives in cold, CO-depleted cores
            results['I_N2H+'] = n2hp.integrated_intensity

            # N2H+/HCN ratio traces CO depletion
            ratio_n2hp_hcn = n2hp.integrated_intensity / (hcn.integrated_intensity + 1e-10)
            results['N2H+_HCN_ratio'] = ratio_n2hp_hcn

            if ratio_n2hp_hcn > 1:
                results['CO_depletion'] = "significant"
            else:
                results['CO_depletion'] = "moderate"

        return results

    # =========================================================================
    # DUST CONTINUUM ANALYSIS
    # =========================================================================

    def fit_dust_sed(self, sed: DustSED,
                     T_range: Tuple[float, float] = (8, 50),
                     beta_range: Tuple[float, float] = (1.0, 2.5)
                     ) -> Dict[str, float]:
        """
        Fit modified blackbody to dust SED

        S_ν = Ω × B_ν(T_d) × (1 - exp(-τ_ν))

        For optically thin: S_ν ∝ ν^β × B_ν(T_d)

        Returns:
            T_dust, beta, column density, mass
        """
        from scipy.optimize import curve_fit

        # Convert to frequency
        freq_hz = c_light / (sed.wavelengths * 1e-4)  # μm to cm to Hz

        # Modified blackbody model (optically thin)
        def mod_bb(nu, T_d, beta, amp):
            B_nu = self._planck_function(nu, T_d)
            return amp * (nu / 1e12)**beta * B_nu
