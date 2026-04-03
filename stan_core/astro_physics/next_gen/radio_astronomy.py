"""
Radio Astronomy Module

Comprehensive radio astronomy data processing, analysis, and interpretation.
Supports data from ALMA, LOFAR, MWA, VLA, JCMT, NOEMA, and other facilities.

Includes:
- Visibility data handling and calibration concepts
- Imaging and deconvolution
- Spectral line analysis
- Continuum source characterization
- Polarization analysis
- Low-frequency specific processing (ionospheric effects)
- Interferometer simulation

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

# Physical constants (CGS)
C_LIGHT = 2.998e10  # cm/s
K_BOLTZMANN = 1.381e-16  # erg/K
H_PLANCK = 6.626e-27  # erg s
M_PROTON = 1.673e-24  # g
JANSKY = 1e-23  # erg/s/cm^2/Hz
PC = 3.086e18  # cm
KPC = 3.086e21  # cm

# Radio-specific constants
MHZ = 1e6  # Hz
GHZ = 1e9  # Hz


class RadioFacility(Enum):
    """Major radio astronomy facilities"""
    ALMA = "alma"  # Atacama Large Millimeter Array
    VLA = "vla"  # Karl G. Jansky Very Large Array
    LOFAR = "lofar"  # Low-Frequency Array
    MWA = "mwa"  # Murchison Widefield Array
    JCMT = "jcmt"  # James Clerk Maxwell Telescope
    NOEMA = "noema"  # Northern Extended Millimeter Array
    GMRT = "gmrt"  # Giant Metrewave Radio Telescope
    ASKAP = "askap"  # Australian SKA Pathfinder
    MEERKAT = "meerkat"  # MeerKAT
    ATCA = "atca"  # Australia Telescope Compact Array
    WSRT = "wsrt"  # Westerbork Synthesis Radio Telescope
    EFFELSBERG = "effelsberg"  # Effelsberg 100m
    GBT = "gbt"  # Green Bank Telescope
    PARKES = "parkes"  # Parkes 64m


class ObservingBand(Enum):
    """Standard radio observing bands"""
    # Low frequency
    VHF = "vhf"  # 30-300 MHz
    P_BAND = "p"  # 230-470 MHz
    L_BAND = "l"  # 1-2 GHz
    S_BAND = "s"  # 2-4 GHz
    C_BAND = "c"  # 4-8 GHz
    X_BAND = "x"  # 8-12 GHz
    KU_BAND = "ku"  # 12-18 GHz
    K_BAND = "k"  # 18-26.5 GHz
    KA_BAND = "ka"  # 26.5-40 GHz
    Q_BAND = "q"  # 33-50 GHz
    W_BAND = "w"  # 75-110 GHz
    # Millimeter/submm
    BAND_3 = "band3"  # 84-116 GHz (ALMA)
    BAND_6 = "band6"  # 211-275 GHz (ALMA)
    BAND_7 = "band7"  # 275-373 GHz (ALMA)
    BAND_9 = "band9"  # 602-720 GHz (ALMA)


@dataclass
class RadioObservation:
    """Container for radio observation metadata"""
    facility: RadioFacility
    band: ObservingBand
    freq_center: float  # Hz
    bandwidth: float  # Hz
    n_channels: int
    integration_time: float  # seconds
    ra: float  # degrees
    dec: float  # degrees
    beam_major: float  # arcsec
    beam_minor: float  # arcsec
    beam_pa: float  # degrees
    rms_noise: float  # Jy/beam
    primary_beam_fwhm: float = None  # arcmin


@dataclass
class Visibility:
    """UV visibility data point"""
    u: float  # wavelengths
    v: float  # wavelengths
    w: float  # wavelengths
    real: float  # Jy
    imag: float  # Jy
    weight: float
    freq: float  # Hz
    time: float  # MJD
    antenna1: int
    antenna2: int


@dataclass
class RadioSource:
    """Radio source characterization"""
    name: str
    ra: float  # degrees
    dec: float  # degrees
    flux_density: float  # Jy
    flux_error: float  # Jy
    freq: float  # Hz
    spectral_index: float = 0.0  # S ~ nu^alpha
    spectral_index_error: float = 0.0
    angular_size: float = 0.0  # arcsec (0 = unresolved)
    integrated_flux: float = None  # Jy (for extended sources)
    peak_flux: float = None  # Jy/beam
    source_type: str = "unknown"


# =============================================================================
# FACILITY SPECIFICATIONS
# =============================================================================

class FacilitySpecs:
    """
    Technical specifications for radio facilities.
    """

    SPECS = {
        RadioFacility.ALMA: {
            'location': 'Atacama, Chile',
            'latitude': -23.0262,
            'longitude': -67.7552,
            'elevation': 5000,  # m
            'n_antennas': 66,
            'dish_diameter': 12.0,  # m (main array)
            'baseline_min': 15,  # m
            'baseline_max': 16000,  # m
            'freq_range': (84e9, 950e9),  # Hz
            'bands': ['band3', 'band4', 'band5', 'band6', 'band7', 'band8', 'band9', 'band10'],
            'tsys_typical': {
                'band3': 70, 'band6': 100, 'band7': 200, 'band9': 500
            },
        },
        RadioFacility.VLA: {
            'location': 'New Mexico, USA',
            'latitude': 34.0784,
            'longitude': -107.6184,
            'elevation': 2124,
            'n_antennas': 27,
            'dish_diameter': 25.0,
            'baseline_min': 35,
            'baseline_max': 36400,  # A-config
            'freq_range': (1e9, 50e9),
            'bands': ['l', 's', 'c', 'x', 'ku', 'k', 'ka', 'q'],
            'configurations': ['A', 'B', 'C', 'D'],
        },
        RadioFacility.LOFAR: {
            'location': 'Netherlands (core)',
            'latitude': 52.9088,
            'longitude': 6.8690,
            'elevation': 10,
            'n_stations': 52,  # core + remote + international
            'freq_range': (10e6, 240e6),
            'bands': ['lba', 'hba'],  # Low-band, High-band antennas
            'baseline_max': 2000000,  # International baselines
            'fov_lba': 10,  # degrees at 60 MHz
            'fov_hba': 5,  # degrees at 150 MHz
        },
        RadioFacility.MWA: {
            'location': 'Western Australia',
            'latitude': -26.7033,
            'longitude': 116.6708,
            'elevation': 377,
            'n_tiles': 256,  # Phase II
            'freq_range': (70e6, 300e6),
            'baseline_max': 6000,
            'fov': 25,  # degrees at 150 MHz
            'freq_resolution': 40e3,  # Hz
        },
        RadioFacility.JCMT: {
            'location': 'Mauna Kea, Hawaii',
            'latitude': 19.8228,
            'longitude': -155.4770,
            'elevation': 4092,
            'dish_diameter': 15.0,
            'freq_range': (211e9, 691e9),
            'instruments': ['SCUBA-2', 'HARP', 'RxA3m'],
        },
    }

    @classmethod
    def get_specs(cls, facility: RadioFacility) -> Dict[str, Any]:
        """Get facility specifications"""
        return cls.SPECS.get(facility, {})

    @classmethod
    def primary_beam_fwhm(cls, facility: RadioFacility, freq: float) -> float:
        """
        Calculate primary beam FWHM.

        Args:
            facility: Radio facility
            freq: Observing frequency (Hz)

        Returns:
            Primary beam FWHM (arcmin)
        """
        specs = cls.SPECS.get(facility, {})
        D = specs.get('dish_diameter', 25)  # Default 25m

        # FWHM = 1.02 * lambda / D (radians)
        wavelength = C_LIGHT / freq
        fwhm_rad = 1.02 * wavelength / (D * 100)  # D in cm

        return np.degrees(fwhm_rad) * 60  # arcmin

    @classmethod
    def synthesized_beam(cls, facility: RadioFacility, freq: float,
                         baseline_km: float = None) -> float:
        """
        Estimate synthesized beam size.

        Args:
            facility: Radio facility
            freq: Frequency (Hz)
            baseline_km: Maximum baseline (km)

        Returns:
            Beam FWHM (arcsec)
        """
        specs = cls.SPECS.get(facility, {})

        if baseline_km is None:
            baseline_km = specs.get('baseline_max', 1000) / 1000

        wavelength = C_LIGHT / freq  # cm
        baseline_cm = baseline_km * 1e5

        # theta ~ lambda / B
        theta_rad = wavelength / baseline_cm

        return np.degrees(theta_rad) * 3600  # arcsec


# =============================================================================
# RADIO CONTINUUM ANALYSIS
# =============================================================================

class RadioContinuumAnalysis:
    """
    Analysis of radio continuum emission.

    Includes spectral index fitting, flux density measurements,
    and source characterization.
    """

    def __init__(self):
        """Initialize continuum analysis"""
        pass

    def spectral_index(self, flux1: float, flux2: float,
                       freq1: float, freq2: float) -> float:
        """
        Calculate spectral index from two-point measurement.

        S_nu ~ nu^alpha

        Args:
            flux1, flux2: Flux densities (Jy)
            freq1, freq2: Frequencies (Hz)

        Returns:
            Spectral index alpha
        """
        if flux1 <= 0 or flux2 <= 0:
            return np.nan

        return np.log(flux1 / flux2) / np.log(freq1 / freq2)

    def spectral_index_fit(self, fluxes: np.ndarray, freqs: np.ndarray,
                           errors: np.ndarray = None) -> Tuple[float, float, float]:
        """
        Fit spectral index to multiple measurements.

        Args:
            fluxes: Flux density array (Jy)
            freqs: Frequency array (Hz)
            errors: Flux density errors (Jy)

        Returns:
            (alpha, alpha_error, S_0) where S = S_0 * (nu/nu_0)^alpha
        """
        log_flux = np.log10(fluxes)
        log_freq = np.log10(freqs)

        if errors is not None:
            # Weighted fit
            weights = fluxes / errors
            log_weights = weights**2
        else:
            log_weights = np.ones_like(fluxes)

        # Linear regression in log space
        coeffs = np.polyfit(log_freq - np.mean(log_freq), log_flux,
                           1, w=np.sqrt(log_weights))

        alpha = coeffs[0]
        S_0 = 10**coeffs[1]

        # Estimate uncertainty (simplified)
        residuals = log_flux - np.polyval(coeffs, log_freq - np.mean(log_freq))
        alpha_err = np.std(residuals) / np.std(log_freq)

        return alpha, alpha_err, S_0

    def brightness_temperature(self, flux_density: float, freq: float,
                               beam_area: float) -> float:
        """
        Calculate brightness temperature from flux density.

        T_B = (c^2 / 2k) * (S / nu^2 / Omega)

        Args:
            flux_density: Flux density (Jy)
            freq: Frequency (Hz)
            beam_area: Beam solid angle (sr)

        Returns:
            Brightness temperature (K)
        """
        S_cgs = flux_density * JANSKY  # erg/s/cm^2/Hz
        T_B = (C_LIGHT**2 / (2 * K_BOLTZMANN)) * S_cgs / (freq**2 * beam_area)
        return T_B

    def beam_solid_angle(self, bmaj: float, bmin: float) -> float:
        """
        Calculate beam solid angle.

        Args:
            bmaj: Beam major axis (arcsec)
            bmin: Beam minor axis (arcsec)

        Returns:
            Solid angle (sr)
        """
        # Convert to radians
        bmaj_rad = np.radians(bmaj / 3600)
        bmin_rad = np.radians(bmin / 3600)

        # Gaussian beam: Omega = pi * a * b / (4 * ln(2))
        return np.pi * bmaj_rad * bmin_rad / (4 * np.log(2))

    def thermal_fraction(self, alpha: float,
                         alpha_thermal: float = -0.1,
                         alpha_nonthermal: float = -0.7) -> float:
        """
        Estimate thermal fraction from spectral index.

        Args:
            alpha: Observed spectral index
            alpha_thermal: Thermal spectral index
            alpha_nonthermal: Non-thermal spectral index

        Returns:
            Thermal fraction (0-1)
        """
        # S = S_th + S_nth
        # alpha = (f_th * alpha_th + (1-f_th) * alpha_nth)
        f_th = (alpha - alpha_nonthermal) / (alpha_thermal - alpha_nonthermal)
        return np.clip(f_th, 0, 1)

    def star_formation_rate(self, L_radio: float, freq: float = 1.4e9,
                            calibration: str = 'condon') -> float:
        """
        Estimate SFR from radio luminosity.

        Args:
            L_radio: Radio luminosity (W/Hz)
            freq: Reference frequency (Hz)
            calibration: 'condon' or 'murphy'

        Returns:
            SFR (M_sun/yr)
        """
        if calibration == 'condon':
            # Condon (1992) for 1.4 GHz
            # SFR = L_1.4 / 4e21
            L_14 = L_radio * (1.4e9 / freq)**0.8  # Scale to 1.4 GHz
            SFR = L_14 / 4e21

        elif calibration == 'murphy':
            # Murphy et al. (2011)
            # More accurate, accounts for thermal/non-thermal
            L_14 = L_radio * (1.4e9 / freq)**0.8
            SFR = L_14 / 6.35e21

        return SFR


# =============================================================================
# SPECTRAL LINE ANALYSIS
# =============================================================================

class RadioSpectralLine:
    """
    Radio spectral line analysis.

    Includes line identification, fitting, and physical parameter extraction.
    """

    # Common radio spectral lines (frequency in Hz)
    LINE_CATALOG = {
        'HI_21cm': 1.420405751e9,
        'OH_1665': 1.6654018e9,
        'OH_1667': 1.6673590e9,
        'OH_1720': 1.7205300e9,
        'H2CO_4830': 4.829660e9,
        'CH3OH_6668': 6.6685192e9,  # Class II methanol maser
        'H2O_22235': 2.2235080e10,  # Water maser
        'NH3_11': 2.3694506e10,  # Ammonia (1,1)
        'NH3_22': 2.3722633e10,  # Ammonia (2,2)
        'NH3_33': 2.3870129e10,  # Ammonia (3,3)
        'SiO_43': 4.3122090e10,  # SiO v=1
        'CS_21': 9.7980953e10,
        'CO_10': 1.15271204e11,
        'CO_21': 2.30538000e11,
        'CO_32': 3.45795991e11,
        '13CO_10': 1.10201354e11,
        '13CO_21': 2.20398684e11,
        'C18O_10': 1.09782176e11,
        'C18O_21': 2.19560358e11,
        'HCN_10': 8.8631602e10,
        'HCO+_10': 8.9188526e10,
        'N2H+_10': 9.3173777e10,
        'CN_10': 1.13490970e11,
        'HNC_10': 9.0663568e10,
    }

    def __init__(self):
        """Initialize spectral line analysis"""
        pass

    def identify_line(self, freq_observed: float, z: float = 0,
                      tolerance: float = 1e-4) -> List[Tuple[str, float]]:
        """
        Identify spectral line from observed frequency.

        Args:
            freq_observed: Observed frequency (Hz)
            z: Source redshift
            tolerance: Fractional frequency tolerance

        Returns:
            List of (line_name, rest_frequency) matches
        """
        freq_rest = freq_observed * (1 + z)

        matches = []
        for name, freq in self.LINE_CATALOG.items():
            if np.abs(freq_rest - freq) / freq < tolerance:
                matches.append((name, freq))

        return matches

    def velocity_from_frequency(self, freq_obs: float, freq_rest: float,
                                convention: str = 'radio') -> float:
        """
        Calculate velocity from frequency shift.

        Args:
            freq_obs: Observed frequency (Hz)
            freq_rest: Rest frequency (Hz)
            convention: 'radio', 'optical', or 'relativistic'

        Returns:
            Velocity (km/s)
        """
        c_kms = C_LIGHT / 1e5  # km/s

        if convention == 'radio':
            # v = c * (f_rest - f_obs) / f_rest
            v = c_kms * (freq_rest - freq_obs) / freq_rest

        elif convention == 'optical':
            # v = c * (f_rest - f_obs) / f_obs
            v = c_kms * (freq_rest - freq_obs) / freq_obs

        elif convention == 'relativistic':
            # Full relativistic formula
            beta = (freq_rest**2 - freq_obs**2) / (freq_rest**2 + freq_obs**2)
            v = c_kms * beta

        return v

    def column_density_optically_thin(self, integral: float, freq: float,
                                      A_ul: float, g_u: float, E_u: float,
                                      T_ex: float, Q: float) -> float:
        """
        Calculate column density assuming optically thin emission.

        N_tot = (8 * pi * k * nu^2 / h * c^3 * A_ul) * Q(T) / g_u * exp(E_u/kT) * integral(T_mb dv)

        Args:
            integral: Integrated intensity (K km/s)
            freq: Line frequency (Hz)
            A_ul: Einstein A coefficient (s^-1)
            g_u: Upper level degeneracy
            E_u: Upper level energy (K)
            T_ex: Excitation temperature (K)
            Q: Partition function at T_ex

        Returns:
            Column density (cm^-2)
        """
        # Convert integral to CGS (K cm/s)
        integral_cgs = integral * 1e5

        factor = (8 * np.pi * K_BOLTZMANN * freq**2) / \
                 (H_PLANCK * C_LIGHT**3 * A_ul)

        N = factor * Q / g_u * np.exp(E_u / T_ex) * integral_cgs

        return N

    def rotation_diagram_analysis(self, transitions: List[Dict],
                                  T_bg: float = 2.73) -> Tuple[float, float]:
        """
        Rotation diagram analysis for temperature and column density.

        Args:
            transitions: List of dicts with 'integral', 'A_ul', 'g_u', 'E_u', 'freq'
            T_bg: Background temperature (K)

        Returns:
            (T_rot, N_tot) rotation temperature (K) and column density (cm^-2)
        """
        # ln(N_u / g_u) = ln(N_tot / Q) - E_u / (k * T_rot)

        x = []  # E_u / k
        y = []  # ln(N_u / g_u)

        for trans in transitions:
            # Calculate N_u from integrated intensity
            # Simplified: assume optically thin
            integral = trans['integral']
            A_ul = trans['A_ul']
            g_u = trans['g_u']
            E_u = trans['E_u']
            freq = trans['freq']

            # N_u ~ integral / A_ul
            N_u = 8 * np.pi * K_BOLTZMANN * freq**2 * integral * 1e5 / \
                  (H_PLANCK * C_LIGHT**3 * A_ul)

            x.append(E_u)
            y.append(np.log(N_u / g_u))

        x = np.array(x)
        y = np.array(y)

        # Linear fit
        coeffs = np.polyfit(x, y, 1)

        T_rot = -1.0 / coeffs[0]
        ln_N_Q = coeffs[1]

        # Estimate N_tot (need partition function)
        # Q ~ sum(g_i * exp(-E_i/kT)) ~ T for linear molecules at high T
        Q = T_rot  # Rough approximation
        N_tot = np.exp(ln_N_Q) * Q

        return T_rot, N_tot

    def optical_depth_from_tau(self, T_on: float, T_off: float,
                               T_sys: float) -> float:
        """
        Calculate optical depth from absorption measurement.

        Args:
            T_on: On-source temperature (K)
            T_off: Off-source temperature (K)
            T_sys: System temperature (K)

        Returns:
            Optical depth tau
        """
        # T_obs = T_cont * exp(-tau) + T_line * (1 - exp(-tau))
        # For absorption: T_on < T_off
        # tau = -ln((T_on - T_line) / (T_off - T_line))

        # Simplified for HI absorption against continuum
        if T_off <= 0:
            return np.nan

        return -np.log(T_on / T_off)


# =============================================================================
# INTERFEROMETRY
# =============================================================================

class RadioInterferometry:
    """
    Radio interferometry calculations and UV-plane analysis.
    """

    def __init__(self):
        """Initialize interferometry module"""
        pass

    def baseline_to_uv(self, baseline_m: np.ndarray, freq: float,
                       ha: float, dec: float, lat: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert baseline to UV coordinates.

        Args:
            baseline_m: Baseline vector (East, North, Up) in meters
            freq: Frequency (Hz)
            ha: Hour angle (radians)
            dec: Declination (radians)
            lat: Latitude (radians)

        Returns:
            (u, v) in wavelengths
        """
        wavelength = C_LIGHT / freq  # cm
        baseline_lambda = baseline_m * 100 / wavelength  # Convert to wavelengths

        # Rotation matrices
        sin_ha = np.sin(ha)
        cos_ha = np.cos(ha)
        sin_dec = np.sin(dec)
        cos_dec = np.cos(dec)
        sin_lat = np.sin(lat)
        cos_lat = np.cos(lat)

        # Transform to UV plane
        # u = sin(ha) * B_x + cos(ha) * B_y
        # v = -sin(dec)*cos(ha)*B_x + sin(dec)*sin(ha)*B_y + cos(dec)*B_z

        u = sin_ha * baseline_lambda[0] + cos_ha * baseline_lambda[1]
        v = -sin_dec * cos_ha * baseline_lambda[0] + \
            sin_dec * sin_ha * baseline_lambda[1] + \
            cos_dec * baseline_lambda[2]

        return u, v

    def uv_coverage(self, n_antennas: int, baseline_max: float, freq: float,
                    dec: float, ha_range: Tuple[float, float] = (-6, 6),
                    lat: float = -23.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate UV coverage for an observation.

        Args:
            n_antennas: Number of antennas
            baseline_max: Maximum baseline (m)
            freq: Frequency (Hz)
            dec: Declination (degrees)
            ha_range: Hour angle range (hours)
            lat: Observatory latitude (degrees)

        Returns:
            (u, v) arrays in kilolambda
        """
        # Generate antenna positions (simplified random distribution)
        np.random.seed(42)
        n_baselines = n_antennas * (n_antennas - 1) // 2

        # Random baseline lengths and orientations
        baseline_lengths = np.random.uniform(0, baseline_max, n_baselines)
        baseline_angles = np.random.uniform(0, 2 * np.pi, n_baselines)

        baselines = np.column_stack([
            baseline_lengths * np.cos(baseline_angles),
            baseline_lengths * np.sin(baseline_angles),
            np.zeros(n_baselines)  # Ignore W for simplicity
        ])

        # Hour angle sampling
        ha_hours = np.linspace(ha_range[0], ha_range[1], 100)
        ha_rad = np.radians(ha_hours * 15)  # Convert to radians

        dec_rad = np.radians(dec)
        lat_rad = np.radians(lat)

        all_u = []
        all_v = []

        for ha in ha_rad:
            for bl in baselines:
                u, v = self.baseline_to_uv(bl, freq, ha, dec_rad, lat_rad)
                all_u.extend([u, -u])  # Hermitian symmetry
                all_v.extend([v, -v])

        return np.array(all_u) / 1000, np.array(all_v) / 1000  # kilolambda

    def dirty_beam(self, u: np.ndarray, v: np.ndarray,
                   n_pixels: int = 256, cell_size: float = 1.0) -> np.ndarray:
        """
        Calculate dirty beam (PSF) from UV coverage.

        Args:
            u, v: UV coordinates (kilolambda)
            n_pixels: Image size
            cell_size: Pixel size (arcsec)

        Returns:
            Dirty beam image
        """
        # Create UV grid
        uv_max = np.max([np.abs(u).max(), np.abs(v).max()])
        uv_cell = 1.0 / (n_pixels * np.radians(cell_size / 3600))

        u_grid = np.zeros((n_pixels, n_pixels), dtype=complex)

        # Grid visibilities (simple nearest neighbor)
        u_idx = ((u * 1000 / uv_cell) + n_pixels // 2).astype(int)
        v_idx = ((v * 1000 / uv_cell) + n_pixels // 2).astype(int)

        valid = (u_idx >= 0) & (u_idx < n_pixels) & \
                (v_idx >= 0) & (v_idx < n_pixels)

        for ui, vi in zip(u_idx[valid], v_idx[valid]):
            u_grid[vi, ui] += 1.0

        # Inverse FFT
        beam = np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(u_grid))).real

        # Normalize
        beam /= beam.max()

        return beam

    def theoretical_rms(self, sefd: float, n_antennas: int,
                        bandwidth: float, t_int: float,
                        n_pol: int = 2) -> float:
        """
        Calculate theoretical image RMS noise.

        sigma = SEFD / (eta * sqrt(n_pol * n_baselines * bandwidth * t_int))

        Args:
            sefd: System Equivalent Flux Density (Jy)
            n_antennas: Number of antennas
            bandwidth: Bandwidth (Hz)
            t_int: Integration time (s)
            n_pol: Number of polarizations

        Returns:
            RMS noise (Jy/beam)
        """
        n_baselines = n_antennas * (n_antennas - 1) / 2
        eta = 0.88  # Correlator efficiency

        sigma = sefd / (eta * np.sqrt(n_pol * n_baselines * bandwidth * t_int))

        return sigma

    def largest_angular_scale(self, baseline_min: float, freq: float) -> float:
        """
        Calculate largest angular scale recoverable.

        theta_LAS ~ lambda / B_min

        Args:
            baseline_min: Minimum baseline (m)
            freq: Frequency (Hz)

        Returns:
            Largest angular scale (arcsec)
        """
        wavelength = C_LIGHT / freq  # cm
        baseline_cm = baseline_min * 100

        theta_rad = wavelength / baseline_cm
        return np.degrees(theta_rad) * 3600


# =============================================================================
# LOW-FREQUENCY SPECIFIC
# =============================================================================

class LowFrequencyRadio:
    """
    Low-frequency radio astronomy specific processing.

    Handles ionospheric effects, RFI, and wide-field imaging.
    """

    def __init__(self):
        """Initialize low-frequency module"""
        pass

    def ionospheric_phase_screen(self, TEC: float, freq: float) -> float:
        """
        Calculate ionospheric phase delay.

        phi = 8.448e9 * TEC / freq

        Args:
            TEC: Total Electron Content (TECU, 10^16 m^-2)
            freq: Frequency (Hz)

        Returns:
            Phase delay (radians)
        """
        return 8.448e9 * TEC / freq

    def ionospheric_refraction(self, TEC: float, freq: float,
                               elevation: float) -> float:
        """
        Calculate ionospheric refraction offset.

        Args:
            TEC: Total Electron Content (TECU)
            freq: Frequency (Hz)
            elevation: Source elevation (degrees)

        Returns:
            Position offset (arcsec)
        """
        # delta_theta ~ 40.3 * TEC / (freq^2 * sin(el))
        freq_mhz = freq / 1e6
        el_rad = np.radians(elevation)

        offset_rad = 40.3 * TEC * 1e16 / (freq**2 * np.sin(el_rad))

        return np.degrees(offset_rad) * 3600

    def faraday_rotation(self, RM: float, wavelength: float) -> float:
        """
        Calculate Faraday rotation angle.

        chi = RM * lambda^2

        Args:
            RM: Rotation Measure (rad/m^2)
            wavelength: Wavelength (m)

        Returns:
            Polarization angle rotation (radians)
        """
        return RM * wavelength**2

    def rotation_measure_synthesis(self, Q: np.ndarray, U: np.ndarray,
                                   lambda_sq: np.ndarray,
                                   phi_range: Tuple[float, float] = (-1000, 1000),
                                   n_phi: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform RM synthesis on polarization data.

        Args:
            Q, U: Stokes Q and U as function of lambda^2
            lambda_sq: lambda^2 values (m^2)
            phi_range: Faraday depth range (rad/m^2)
            n_phi: Number of Faraday depth samples

        Returns:
            (phi, F) Faraday depth and Faraday dispersion function
        """
        phi = np.linspace(phi_range[0], phi_range[1], n_phi)
        P = Q + 1j * U

        F = np.zeros(n_phi, dtype=complex)

        for i, p in enumerate(phi):
            F[i] = np.sum(P * np.exp(-2j * p * lambda_sq)) / len(lambda_sq)

        return phi, np.abs(F)

    def smearing_bandwidth(self, freq: float, channel_width: float,
                           baseline_km: float) -> float:
        """
        Calculate bandwidth smearing (chromatic aberration).

        Args:
            freq: Center frequency (Hz)
            channel_width: Channel width (Hz)
            baseline_km: Baseline length (km)

        Returns:
            Smearing factor (fractional flux loss at edge of field)
        """
        # Smearing becomes significant when delta_nu/nu * B/lambda ~ theta
        wavelength_km = C_LIGHT / freq / 1e5
        theta_synth = wavelength_km / baseline_km  # radians

        # Smearing angle
        delta_theta = (channel_width / freq) * (baseline_km / wavelength_km) * theta_synth

        return delta_theta

    def smearing_time(self, freq: float, t_int: float,
                      baseline_km: float, dec: float) -> float:
        """
        Calculate time-average smearing.

        Args:
            freq: Frequency (Hz)
            t_int: Integration time (s)
            baseline_km: Baseline length (km)
            dec: Declination (degrees)

        Returns:
            Smearing factor
        """
        # Earth rotation rate
        omega_earth = 7.29e-5  # rad/s

        wavelength_km = C_LIGHT / freq / 1e5
        theta_synth = wavelength_km / baseline_km

        # Smearing depends on cos(dec)
        smear = omega_earth * t_int * np.cos(np.radians(dec)) / theta_synth

        return smear


# =============================================================================
# POLARIZATION ANALYSIS
# =============================================================================

class RadioPolarization:
    """
    Radio polarization analysis.

    Handles Stokes parameters, polarization calibration,
    and Faraday rotation.
    """

    def __init__(self):
        """Initialize polarization analysis"""
        pass

    def stokes_from_correlations(self, RR: complex, LL: complex,
                                 RL: complex, LR: complex) -> Tuple[float, float, float, float]:
        """
        Calculate Stokes parameters from circular correlations.

        Args:
            RR, LL, RL, LR: Circular correlation products

        Returns:
            (I, Q, U, V) Stokes parameters
        """
        I = (RR + LL).real / 2
        V = (RR - LL).real / 2
        Q = (RL + LR).real / 2
        U = (RL - LR).imag / 2

        return I, Q, U, V

    def linear_polarization(self, Q: float, U: float) -> Tuple[float, float]:
        """
        Calculate linear polarization intensity and angle.

        Args:
            Q, U: Stokes Q and U

        Returns:
            (P_linear, chi) polarization intensity and angle
        """
        P = np.sqrt(Q**2 + U**2)
        chi = 0.5 * np.arctan2(U, Q)

        return P, chi

    def polarization_fraction(self, I: float, Q: float, U: float,
                              V: float = 0) -> Dict[str, float]:
        """
        Calculate polarization fractions.

        Args:
            I, Q, U, V: Stokes parameters

        Returns:
            Dict with linear, circular, and total polarization fractions
        """
        P_linear = np.sqrt(Q**2 + U**2)
        P_total = np.sqrt(Q**2 + U**2 + V**2)

        return {
            'linear_fraction': P_linear / I if I > 0 else 0,
            'circular_fraction': np.abs(V) / I if I > 0 else 0,
            'total_fraction': P_total / I if I > 0 else 0,
            'P_linear': P_linear,
            'P_circular': V,
            'P_total': P_total,
        }

    def derotate_polarization(self, Q: float, U: float,
                              chi_rot: float) -> Tuple[float, float]:
        """
        De-rotate Stokes Q, U by angle chi_rot.

        Args:
            Q, U: Stokes parameters
            chi_rot: Rotation angle (radians)

        Returns:
            (Q_derot, U_derot)
        """
        cos2chi = np.cos(2 * chi_rot)
        sin2chi = np.sin(2 * chi_rot)

        Q_derot = Q * cos2chi + U * sin2chi
        U_derot = -Q * sin2chi + U * cos2chi

        return Q_derot, U_derot


# =============================================================================
# RADIO SOURCE PHYSICS
# =============================================================================

class RadioSourcePhysics:
    """
    Physical models for radio emission mechanisms.
    """

    def __init__(self):
        """Initialize source physics module"""
        pass

    def synchrotron_spectrum(self, freq: np.ndarray, B: float,
                             gamma_min: float, gamma_max: float,
                             p: float = 2.5, S_0: float = 1.0) -> np.ndarray:
        """
        Calculate synchrotron spectrum from power-law electron distribution.

        N(gamma) ~ gamma^(-p)
        S(nu) ~ nu^(-(p-1)/2)

        Args:
            freq: Frequency array (Hz)
            B: Magnetic field (Gauss)
            gamma_min, gamma_max: Lorentz factor range
            p: Electron power-law index
            S_0: Normalization

        Returns:
            Flux density (Jy)
        """
        alpha = -(p - 1) / 2

        # Characteristic frequency
        nu_c = 4.2e6 * B * gamma_min**2  # Hz

        # Spectrum
        S = S_0 * (freq / nu_c)**alpha

        # Self-absorption turnover at low frequencies
        nu_ssa = nu_c * (gamma_min)**(-2)
        S *= (1 - np.exp(-(freq / nu_ssa)**2.5))

        return S

    def thermal_bremsstrahlung(self, freq: float, T_e: float, EM: float) -> float:
        """
        Calculate thermal (free-free) emission.

        Args:
            freq: Frequency (Hz)
            T_e: Electron temperature (K)
            EM: Emission measure (pc cm^-6)

        Returns:
            Flux density (Jy) per steradian
        """
        # Gaunt factor approximation
        g_ff = np.log(4.955e-2 / (freq / 1e9)) + 1.5 * np.log(T_e)

        # Optical depth
        tau = 3.28e-7 * (T_e / 1e4)**(-1.35) * (freq / 1e9)**(-2.1) * EM

        # Brightness temperature
        T_B = T_e * (1 - np.exp(-tau))

        # Convert to flux density
        S = 2 * K_BOLTZMANN * T_B * (freq / C_LIGHT)**2 / JANSKY

        return S

    def hii_region_flux(self, T_e: float, EM: float, freq: float,
                        distance_kpc: float, angular_size: float) -> Dict[str, float]:
        """
        Calculate HII region radio properties.

        Args:
            T_e: Electron temperature (K)
            EM: Emission measure (pc cm^-6)
            freq: Frequency (Hz)
            distance_kpc: Distance (kpc)
            angular_size: Angular diameter (arcsec)

        Returns:
            Dict with flux density, optical depth, etc.
        """
        # Optical depth
        tau = 3.28e-7 * (T_e / 1e4)**(-1.35) * (freq / 1e9)**(-2.1) * EM

        # Brightness temperature
        T_B = T_e * (1 - np.exp(-tau))

        # Solid angle
        theta_rad = np.radians(angular_size / 3600)
        omega = np.pi * (theta_rad / 2)**2

        # Flux density
        S = 2 * K_BOLTZMANN * T_B * (freq / C_LIGHT)**2 * omega / JANSKY

        # Physical size
        size_pc = distance_kpc * 1000 * theta_rad  # pc

        # Electron density from EM
        n_e = np.sqrt(EM / size_pc)  # cm^-3

        return {
            'flux_density': S,
            'optical_depth': tau,
            'brightness_temperature': T_B,
            'electron_density': n_e,
            'physical_size_pc': size_pc,
        }

    def pulsar_flux(self, S_1400: float, freq: float,
                    spectral_index: float = -1.6) -> float:
        """
        Scale pulsar flux density to different frequency.

        Args:
            S_1400: Flux density at 1.4 GHz (mJy)
            freq: Target frequency (Hz)
            spectral_index: Pulsar spectral index

        Returns:
            Flux density at freq (mJy)
        """
        return S_1400 * (freq / 1.4e9)**spectral_index

    def magnetic_field_equipartition(self, L_synch: float, V: float,
                                     alpha: float = -0.7,
                                     eta: float = 1.0) -> float:
        """
        Estimate magnetic field from equipartition/minimum energy.

        Args:
            L_synch: Synchrotron luminosity (erg/s)
            V: Source volume (cm^3)
            alpha: Spectral index
            eta: Ratio of total to electron energy

        Returns:
            Magnetic field (Gauss)
        """
        # Minimum energy condition
        # B_min ~ (L / V)^(2/7)

        c_12 = 1.06e12  # Constant for synchrotron

        B = (6 * np.pi * eta * c_12 * L_synch / V)**(2 / 7)

        return B


# =============================================================================
# RADIO ARCHIVE INTERFACES
# =============================================================================

class RadioArchiveInterface:
    """
    Interface to radio astronomy data archives.

    Provides access to ALMA, VLA, LOFAR, and other archives.
    """

    # Archive URLs and TAP endpoints
    ARCHIVES = {
        'alma': {
            'tap': 'https://almascience.eso.org/tap',
            'query_url': 'https://almascience.eso.org/aq/',
            'data_url': 'https://almascience.eso.org/dataPortal/',
        },
        'vla': {
            'tap': 'https://archive.nrao.edu/tap',
            'query_url': 'https://archive.nrao.edu/archive/advquery.jsp',
        },
        'lofar': {
            'tap': 'https://lta.lofar.eu/tap',
            'query_url': 'https://lta.lofar.eu/',
        },
        'eso': {
            'tap': 'http://archive.eso.org/tap_obs',
            'query_url': 'http://archive.eso.org/wdb/wdb/eso/eso_archive_main/query',
        },
        'mwa': {
            'query_url': 'https://asvo.mwatelescope.org/',
        },
        'askap': {
            'tap': 'https://casda.csiro.au/casda_vo_tools/tap',
        },
    }

    def __init__(self):
        """Initialize archive interface"""
        pass

    def search_alma(self, ra: float, dec: float, radius: float = 0.1,
                    band: str = None, project_code: str = None) -> List[Dict]:
        """
        Search ALMA archive.

        Args:
            ra, dec: Coordinates (degrees)
            radius: Search radius (degrees)
            band: ALMA band (e.g., 'band6')
            project_code: ALMA project code

        Returns:
            List of matching observations
        """
        # Would use astroquery.alma in practice
        query_params = {
            'ra': ra,
            'dec': dec,
            'radius': radius,
            'band': band,
            'project_code': project_code,
        }

        # Placeholder - actual implementation would query archive
        return [query_params]

    def search_vla(self, ra: float, dec: float, radius: float = 0.1,
                   config: str = None, band: str = None) -> List[Dict]:
        """
        Search VLA archive.

        Args:
            ra, dec: Coordinates (degrees)
            radius: Search radius (degrees)
            config: VLA configuration (A, B, C, D)
            band: Observing band

        Returns:
            List of matching observations
        """
        query_params = {
            'ra': ra,
            'dec': dec,
            'radius': radius,
            'config': config,
            'band': band,
        }
        return [query_params]

    def search_lofar(self, ra: float, dec: float, radius: float = 1.0) -> List[Dict]:
        """
        Search LOFAR Long Term Archive.

        Args:
            ra, dec: Coordinates (degrees)
            radius: Search radius (degrees)

        Returns:
            List of matching observations
        """
        query_params = {
            'ra': ra,
            'dec': dec,
            'radius': radius,
        }
        return [query_params]

    def get_observation_summary(self, archive: str, obs_id: str) -> Dict:
        """
        Get observation summary from archive.

        Args:
            archive: Archive name
            obs_id: Observation ID

        Returns:
            Observation metadata
        """
        return {
            'archive': archive,
            'obs_id': obs_id,
            'status': 'placeholder',
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def jy_to_kelvin(flux_jy: float, freq_hz: float,
                 beam_arcsec: Tuple[float, float]) -> float:
    """
    Convert flux density to brightness temperature.

    Args:
        flux_jy: Flux density (Jy)
        freq_hz: Frequency (Hz)
        beam_arcsec: (bmaj, bmin) in arcsec

    Returns:
        Brightness temperature (K)
    """
    bmaj_rad = np.radians(beam_arcsec[0] / 3600)
    bmin_rad = np.radians(beam_arcsec[1] / 3600)
    omega = np.pi * bmaj_rad * bmin_rad / (4 * np.log(2))

    S_cgs = flux_jy * JANSKY
    T_B = (C_LIGHT**2 / (2 * K_BOLTZMANN * freq_hz**2)) * S_cgs / omega

    return T_B


def kelvin_to_jy(T_K: float, freq_hz: float,
                 beam_arcsec: Tuple[float, float]) -> float:
    """
    Convert brightness temperature to flux density.

    Args:
        T_K: Brightness temperature (K)
        freq_hz: Frequency (Hz)
        beam_arcsec: (bmaj, bmin) in arcsec

    Returns:
        Flux density (Jy)
    """
    bmaj_rad = np.radians(beam_arcsec[0] / 3600)
    bmin_rad = np.radians(beam_arcsec[1] / 3600)
    omega = np.pi * bmaj_rad * bmin_rad / (4 * np.log(2))

    S_cgs = (2 * K_BOLTZMANN * T_K * freq_hz**2 / C_LIGHT**2) * omega

    return S_cgs / JANSKY


def freq_to_wavelength(freq_hz: float) -> float:
    """Convert frequency to wavelength in cm"""
    return C_LIGHT / freq_hz


def wavelength_to_freq(wavelength_cm: float) -> float:
    """Convert wavelength to frequency in Hz"""
    return C_LIGHT / wavelength_cm


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums and data classes
    'RadioFacility',
    'ObservingBand',
    'RadioObservation',
    'Visibility',
    'RadioSource',

    # Core classes
    'FacilitySpecs',
    'RadioContinuumAnalysis',
    'RadioSpectralLine',
    'RadioInterferometry',
    'LowFrequencyRadio',
    'RadioPolarization',
    'RadioSourcePhysics',
    'RadioArchiveInterface',

    # Convenience functions
    'jy_to_kelvin',
    'kelvin_to_jy',
    'freq_to_wavelength',
    'wavelength_to_freq',
]


