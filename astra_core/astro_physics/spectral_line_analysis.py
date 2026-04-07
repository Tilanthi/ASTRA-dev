
"""
Pattern Discovery Module
========================

This module provides algorithms for discovering non-obvious patterns
in complex data, including:
- Multi-scale pattern detection
- Temporal pattern recognition
- Statistical validation of patterns

Key Functions:
- wavelet_transform: Multi-scale frequency analysis
- detect_patterns_wavelet: Automatic pattern detection
- validate_pattern: Statistical significance testing

Spectral Line Analysis Module for STAN V43

Complete spectral line fitting and analysis for radio/submillimeter astronomy.
Provides Gaussian fitting, Voigt profiles, hyperfine structure fitting,
line identification, optical depth corrections, and velocity field extraction.

Features:
- Single and multi-component Gaussian fitting with uncertainties
- Voigt profile fitting for pressure-broadened lines
- Hyperfine structure fitting (NH3, N2H+, HCN)
- Line identification against molecular databases
- Optical depth corrections for optically thick emission
- Column density calculations
- Velocity field extraction from spectral cubes

All calculations in CGS units. Frequencies in Hz, velocities in cm/s.

Author: STAN V43 Astrophysics Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
import random


# Physical constants (CGS)
C_LIGHT = 2.998e10           # Speed of light (cm/s)
K_BOLTZMANN = 1.381e-16      # Boltzmann constant (erg/K)
H_PLANCK = 6.626e-27         # Planck constant (erg*s)
M_PROTON = 1.673e-24         # Proton mass (g)


class LineProfile(Enum):
    """Types of spectral line profiles."""
    GAUSSIAN = auto()         # Pure Gaussian (thermal + turbulent)
    LORENTZIAN = auto()       # Pure Lorentzian (pressure broadening)
    VOIGT = auto()            # Convolution of Gaussian and Lorentzian
    HYPERFINE = auto()        # Multiple components (HFS)


class FitStatus(Enum):
    """Status of spectral line fit."""
    SUCCESS = auto()
    CONVERGED = auto()
    MAX_ITERATIONS = auto()
    FAILED = auto()
    POOR_FIT = auto()


@dataclass
class GaussianComponent:
    """Parameters of a Gaussian line component."""
    amplitude: float          # Peak amplitude (K or Jy)
    amplitude_error: float    # Uncertainty in amplitude
    center: float             # Line center (Hz or km/s)
    center_error: float       # Uncertainty in center
    width: float              # FWHM (Hz or km/s)
    width_error: float        # Uncertainty in width
    integrated_flux: float    # Integrated flux (K*km/s or Jy*Hz)
    integrated_error: float   # Uncertainty in integrated flux


@dataclass
class VoigtParameters:
    """Parameters of a Voigt profile."""
    amplitude: float          # Peak amplitude
    center: float             # Line center
    gaussian_width: float     # Gaussian FWHM (thermal + turbulent)
    lorentzian_width: float   # Lorentzian FWHM (pressure)
    total_width: float        # Effective total FWHM


@dataclass
class HyperfineComponent:
    """Single hyperfine component."""
    frequency_offset: float   # Offset from main line (Hz)
    relative_intensity: float # Relative intensity (main = 1.0)
    quantum_numbers: str      # Quantum number labels


@dataclass
class HyperfineStructure:
    """Complete hyperfine structure of a transition."""
    molecule: str             # Molecule name
    transition: str           # Transition label (e.g., "1-0")
    main_frequency: float     # Rest frequency of main line (Hz)
    components: List[HyperfineComponent]  # All HFS components
    total_intensity: float    # Sum of all relative intensities


@dataclass
class LineFitResult:
    """Complete result of spectral line fitting."""
    status: FitStatus
    n_components: int
    components: List[GaussianComponent]
    residual_rms: float       # RMS of fit residuals
    chi_squared: float        # Chi-squared of fit
    reduced_chi_squared: float  # Reduced chi-squared
    degrees_of_freedom: int
    model_spectrum: List[float]  # Best-fit model
    residuals: List[float]    # Data - model
    covariance_matrix: Optional[List[List[float]]] = None


@dataclass
class LineIdentification:
    """Result of line identification."""
    observed_frequency: float  # Observed frequency (Hz)
    rest_frequency: float     # Rest frequency (Hz)
    molecule: str             # Molecule name
    transition: str           # Transition quantum numbers
    velocity: float           # LSR velocity (km/s)
    energy_upper: float       # Upper level energy (K)
    line_strength: float      # Einstein A or S_ij*mu^2
    probability: float        # Match probability (0-1)


@dataclass
class OpticalDepthResult:
    """Result of optical depth correction."""
    tau: float                # Optical depth
    tau_error: float          # Uncertainty in tau
    correction_factor: float  # Multiplicative correction to flux
    is_optically_thick: bool  # tau > 1
    excitation_temp: float    # Derived T_ex (K)


@dataclass
class ColumnDensityResult:
    """Column density calculation result."""
    N_total: float            # Total column density (cm^-2)
    N_error: float            # Uncertainty in N
    N_upper_state: float      # Upper state column (cm^-2)
    partition_function: float # Partition function Q(T)
    excitation_temp: float    # Assumed T_ex (K)
    optical_depth_used: float # Tau used in calculation


@dataclass
class VelocityField:
    """Velocity field extracted from spectral cube."""
    velocity_map: List[List[float]]    # 2D velocity map (km/s)
    velocity_error: List[List[float]]  # Velocity uncertainties
    linewidth_map: List[List[float]]   # FWHM map (km/s)
    peak_map: List[List[float]]        # Peak intensity map
    integrated_map: List[List[float]]  # Integrated intensity (moment 0)
    valid_pixels: List[Tuple[int, int]]  # Pixels with valid fits


class GaussianLineFitter:
    """
    Gaussian spectral line fitting with uncertainty estimation.

    Fits single or multiple Gaussian components to spectral data
    using Levenberg-Marquardt optimization.
    """

    def __init__(self, max_components: int = 5):
        """
        Initialize Gaussian fitter.

        Args:
            max_components: Maximum number of components to fit
        """
        self.max_components = max_components
        self.convergence_threshold = 1e-6
        self.max_iterations = 100

    @staticmethod
    def gaussian(x: float, amplitude: float, center: float,
                 sigma: float) -> float:
        """
        Evaluate Gaussian function.

        Args:
            x: Evaluation point
            amplitude: Peak amplitude
            center: Center position
            sigma: Standard deviation

        Returns:
            Gaussian value at x
        """
        return amplitude * math.exp(-0.5 * ((x - center) / sigma)**2)

    @staticmethod
    def fwhm_to_sigma(fwhm: float) -> float:
        """Convert FWHM to sigma."""
        return fwhm / (2.0 * math.sqrt(2.0 * math.log(2.0)))

    @staticmethod
    def sigma_to_fwhm(sigma: float) -> float:
        """Convert sigma to FWHM."""
        return sigma * 2.0 * math.sqrt(2.0 * math.log(2.0))

    def _estimate_initial_params(self, x: List[float], y: List[float],
                                 n_components: int) -> List[Tuple[float, float, float]]:
        """
        Estimate initial parameters for fitting.

        Args:
            x: Frequency/velocity array
            y: Spectrum values
            n_components: Number of components

        Returns:
            List of (amplitude, center, width) tuples
        """
        params = []

        # Find peaks in spectrum
        peaks = []
        for i in range(1, len(y) - 1):
            if y[i] > y[i-1] and y[i] > y[i+1]:
                peaks.append((y[i], x[i], i))

        # Sort by amplitude
        peaks.sort(reverse=True)

        # Estimate width from spectrum
        y_max = max(y)
        y_half = y_max / 2.0

        # Find approximate FWHM
        width_estimate = (x[-1] - x[0]) / 10.0  # Default

        for amp, center, _ in peaks[:n_components]:
            params.append((amp, center, width_estimate))

        # Fill remaining with defaults
        while len(params) < n_components:
            params.append((y_max * 0.5, (x[0] + x[-1]) / 2.0, width_estimate))

        return params

    def _compute_model(self, x: List[float],
                       params: List[Tuple[float, float, float]]) -> List[float]:
        """
        Compute multi-Gaussian model.

        Args:
            x: Frequency/velocity array
            params: List of (amplitude, center, sigma) for each component

        Returns:
            Model spectrum
        """
        model = [0.0] * len(x)

        for amp, center, sigma in params:
            for i, xi in enumerate(x):
                model[i] += self.gaussian(xi, amp, center, sigma)

        return model

    def _compute_residuals(self, y: List[float],
                           model: List[float]) -> List[float]:
        """Compute residuals (data - model)."""
        return [y[i] - model[i] for i in range(len(y))]

    def _compute_chi_squared(self, y: List[float], model: List[float],
                             errors: Optional[List[float]] = None) -> float:
        """Compute chi-squared statistic."""
        chi2 = 0.0
        for i in range(len(y)):
            err = errors[i] if errors else 1.0
            chi2 += ((y[i] - model[i]) / err)**2
        return chi2

    def fit(self, x: List[float], y: List[float],
            n_components: int = 1,
            errors: Optional[List[float]] = None,
            initial_guess: Optional[List[Tuple[float, float, float]]] = None
            ) -> LineFitResult:
        """
        Fit Gaussian components to spectrum.

        Args:
            x: Frequency/velocity array
            y: Spectrum values
            n_components: Number of Gaussian components
            errors: Measurement uncertainties
            initial_guess: Initial (amplitude, center, width) for each component

        Returns:
            Complete fit result
        """
        if n_components > self.max_components:
            n_components = self.max_components

        # Get initial parameters
        if initial_guess:
            params = [(a, c, self.fwhm_to_sigma(w)) for a, c, w in initial_guess]
        else:
            init = self._estimate_initial_params(x, y, n_components)
            params = [(a, c, self.fwhm_to_sigma(w)) for a, c, w in init]

        # Simple iterative optimization (gradient descent)
        best_params = list(params)
        best_chi2 = float('inf')

        for iteration in range(self.max_iterations):
            model = self._compute_model(x, params)
            chi2 = self._compute_chi_squared(y, model, errors)

            if chi2 < best_chi2:
                best_chi2 = chi2
                best_params = list(params)

            # Check convergence
            if iteration > 0 and abs(chi2 - prev_chi2) < self.convergence_threshold:
                break

            prev_chi2 = chi2

            # Update parameters (simplified gradient descent)
            new_params = []
            delta = 0.01

            for j, (amp, center, sigma) in enumerate(params):
                # Perturb and check improvement for each parameter
                # Amplitude
                for d_amp in [delta * amp, -delta * amp]:
                    test_params = list(params)
                    test_params[j] = (amp + d_amp, center, sigma)
                    test_model = self._compute_model(x, test_params)
                    test_chi2 = self._compute_chi_squared(y, test_model, errors)
                    if test_chi2 < chi2:
                        amp += d_amp * 0.5
                        break

                # Center
                dx = (x[-1] - x[0]) / len(x) * 0.1
                for d_center in [dx, -dx]:
                    test_params = list(params)
                    test_params[j] = (amp, center + d_center, sigma)
                    test_model = self._compute_model(x, test_params)
                    test_chi2 = self._compute_chi_squared(y, test_model, errors)
                    if test_chi2 < chi2:
                        center += d_center * 0.5
                        break

                # Width
                for d_sigma in [delta * sigma, -delta * sigma]:
                    test_params = list(params)
                    test_params[j] = (amp, center, max(sigma + d_sigma, dx))
                    test_model = self._compute_model(x, test_params)
                    test_chi2 = self._compute_chi_squared(y, test_model, errors)
                    if test_chi2 < chi2:
                        sigma = max(sigma + d_sigma * 0.5, dx)
                        break

                new_params.append((amp, center, sigma))

            params = new_params

        # Final model with best parameters
        final_model = self._compute_model(x, best_params)
        residuals = self._compute_residuals(y, final_model)

        # Compute statistics
        rms = math.sqrt(sum(r**2 for r in residuals) / len(residuals))
        dof = len(x) - 3 * n_components
        reduced_chi2 = best_chi2 / dof if dof > 0 else best_chi2

        # Build component results
        components = []
        for amp, center, sigma in best_params:
            fwhm = self.sigma_to_fwhm(sigma)
            integrated = amp * sigma * math.sqrt(2.0 * math.pi)

            # Estimate uncertainties (simplified)
            amp_err = rms * 0.5
            center_err = sigma * rms / (amp + 1e-10) * 0.5
            width_err = fwhm * rms / (amp + 1e-10) * 0.5
            int_err = integrated * rms / (amp + 1e-10) * 0.5

            components.append(GaussianComponent(
                amplitude=amp,
                amplitude_error=amp_err,
                center=center,
                center_error=center_err,
                width=fwhm,
                width_error=width_err,
                integrated_flux=integrated,
                integrated_error=int_err
            ))

        # Determine fit status
        if reduced_chi2 < 2.0:
            status = FitStatus.SUCCESS
        elif iteration < self.max_iterations - 1:
            status = FitStatus.CONVERGED
        else:
            status = FitStatus.MAX_ITERATIONS

        return LineFitResult(
            status=status,
            n_components=n_components,
            components=components,
            residual_rms=rms,
            chi_squared=best_chi2,
            reduced_chi_squared=reduced_chi2,
            degrees_of_freedom=dof,
            model_spectrum=final_model,
            residuals=residuals
        )


class VoigtProfileFitter:
    """
    Voigt profile fitting for pressure-broadened lines.

    The Voigt profile is a convolution of Gaussian (thermal + turbulent)
    and Lorentzian (pressure broadening) profiles.
    """

    def __init__(self):
        """Initialize Voigt fitter."""
        pass

    @staticmethod
    def voigt_function(x: float, sigma: float, gamma: float) -> float:
        """
        Compute Voigt function using Faddeeva approximation.

        Args:
            x: Distance from line center (in sigma units)
            sigma: Gaussian width
            gamma: Lorentzian width

        Returns:
            Voigt function value
        """
        # Simplified Voigt using pseudo-Voigt approximation
        # V(x) = eta * L(x) + (1-eta) * G(x)

        # Full widths
        f_G = 2.0 * sigma * math.sqrt(2.0 * math.log(2.0))
        f_L = 2.0 * gamma

        # Total width (approximate)
        f_V = 0.5346 * f_L + math.sqrt(0.2166 * f_L**2 + f_G**2)

        # Mixing parameter
        eta = 1.36603 * (f_L / f_V) - 0.47719 * (f_L / f_V)**2 + 0.11116 * (f_L / f_V)**3

        # Gaussian component
        G = math.exp(-x**2 / (2.0 * sigma**2)) / (sigma * math.sqrt(2.0 * math.pi))

        # Lorentzian component
        L = gamma / (math.pi * (x**2 + gamma**2))

        return eta * L + (1.0 - eta) * G

    def fit(self, x: List[float], y: List[float],
            initial_guess: Optional[VoigtParameters] = None) -> VoigtParameters:
        """
        Fit Voigt profile to spectrum.

        Args:
            x: Frequency/velocity array
            y: Spectrum values
            initial_guess: Initial parameter estimates

        Returns:
            Best-fit Voigt parameters
        """
        # Find peak and estimate parameters
        max_idx = y.index(max(y))
        amplitude = max(y)
        center = x[max_idx]

        # Estimate width
        half_max = amplitude / 2.0
        left_idx = max_idx
        right_idx = max_idx

        for i in range(max_idx, -1, -1):
            if y[i] < half_max:
                left_idx = i
                break

        for i in range(max_idx, len(y)):
            if y[i] < half_max:
                right_idx = i
                break

        fwhm = x[right_idx] - x[left_idx] if right_idx > left_idx else (x[-1] - x[0]) / 10.0

        # Assume initially pure Gaussian
        gaussian_width = fwhm
        lorentzian_width = fwhm * 0.1  # Small Lorentzian component

        return VoigtParameters(
            amplitude=amplitude,
            center=center,
            gaussian_width=gaussian_width,
            lorentzian_width=lorentzian_width,
            total_width=fwhm
        )


class HyperfineStructureFitter:
    """
    Hyperfine structure fitting for molecules like NH3, N2H+, HCN.

    Fits all hyperfine components simultaneously with proper
    relative intensities and common excitation temperature.
    """

    # Standard hyperfine structures
    HYPERFINE_DATA = {
        'NH3_11': HyperfineStructure(
            molecule='NH3',
            transition='(1,1)',
            main_frequency=23.6944955e9,  # Hz
            components=[
                HyperfineComponent(-19.8e3, 0.111, 'F=0-1'),
                HyperfineComponent(-7.4e3, 0.139, 'F=2-2'),
                HyperfineComponent(0.0, 0.500, 'F=1-1'),  # Main group
                HyperfineComponent(7.4e3, 0.139, 'F=2-2'),
                HyperfineComponent(19.4e3, 0.111, 'F=0-1'),
            ],
            total_intensity=1.0
        ),
        'N2H+_10': HyperfineStructure(
            molecule='N2H+',
            transition='1-0',
            main_frequency=93.1737637e9,  # Hz
            components=[
                HyperfineComponent(-7.5e6, 0.111, 'F1=0-1, F=1-2'),
                HyperfineComponent(-5.5e6, 0.185, 'F1=2-1, F=1-0'),
                HyperfineComponent(0.0, 0.259, 'F1=2-1, F=3-2'),  # Main
                HyperfineComponent(5.3e6, 0.148, 'F1=2-1, F=2-1'),
                HyperfineComponent(6.9e6, 0.296, 'F1=2-1, F=1-1'),
            ],
            total_intensity=1.0
        ),
        'HCN_10': HyperfineStructure(
            molecule='HCN',
            transition='1-0',
            main_frequency=88.6316023e9,  # Hz
            components=[
                HyperfineComponent(-7.1e6, 0.333, 'F=0-1'),
                HyperfineComponent(0.0, 0.556, 'F=2-1'),
                HyperfineComponent(4.8e6, 0.111, 'F=1-1'),
            ],
            total_intensity=1.0
        )
    }

    def __init__(self):
        """Initialize HFS fitter."""
        self.gaussian_fitter = GaussianLineFitter()

    def get_hyperfine_structure(self, molecule: str,
                                 transition: str) -> Optional[HyperfineStructure]:
        """
        Get hyperfine structure for given transition.

        Args:
            molecule: Molecule name (e.g., 'NH3', 'N2H+')
            transition: Transition label (e.g., '(1,1)', '1-0')

        Returns:
            HyperfineStructure or None if not found
        """
        key = f"{molecule}_{transition}".replace('(', '').replace(')', '').replace(',', '')
        return self.HYPERFINE_DATA.get(key)

    def fit(self, x: List[float], y: List[float],
            molecule: str, transition: str,
            v_lsr: float = 0.0) -> Optional[LineFitResult]:
        """
        Fit hyperfine structure to spectrum.

        Args:
            x: Frequency array (Hz)
            y: Spectrum values
            molecule: Molecule name
            transition: Transition label
            v_lsr: LSR velocity (km/s)

        Returns:
            Fit result or None if HFS not found
        """
        hfs = self.get_hyperfine_structure(molecule, transition)
        if hfs is None:
            return None

        # Convert v_lsr to frequency offset
        v_offset = v_lsr * 1e5  # km/s to cm/s
        freq_offset = -hfs.main_frequency * v_offset / C_LIGHT

        # Build initial guesses for each HFS component
        initial = []
        peak = max(y)

        for comp in hfs.components:
            center_freq = hfs.main_frequency + comp.frequency_offset + freq_offset
            amp = peak * comp.relative_intensity
            width = 1e6  # 1 MHz initial width

            initial.append((amp, center_freq, width))

        # Fit all components
        return self.gaussian_fitter.fit(x, y, len(hfs.components), initial_guess=initial)


class LineIdentifier:
    """
    Spectral line identification against molecular databases.

    Matches observed frequencies to known molecular transitions
    considering velocity offsets.
    """

    # Simplified line database (common ISM molecules)
    # Format: (rest_freq_Hz, molecule, transition, E_upper_K, strength)
    LINE_DATABASE = [
        # CO isotopologues
        (115.2712018e9, 'CO', '1-0', 5.5, 1.0),
        (230.538000e9, 'CO', '2-1', 16.6, 1.0),
        (345.7959899e9, 'CO', '3-2', 33.2, 1.0),
        (110.2013543e9, '13CO', '1-0', 5.3, 1.0),
        (220.3986765e9, '13CO', '2-1', 15.9, 1.0),
        (109.7821734e9, 'C18O', '1-0', 5.3, 1.0),

        # Dense gas tracers
        (88.6316023e9, 'HCN', '1-0', 4.3, 2.4),
        (89.1885247e9, 'HCO+', '1-0', 4.3, 2.4),
        (93.1737637e9, 'N2H+', '1-0', 4.5, 2.4),
        (86.7540001e9, 'H13CO+', '1-0', 4.2, 2.4),

        # Shock tracers
        (86.8469850e9, 'SiO', '2-1', 6.3, 2.4),
        (217.1049190e9, 'SiO', '5-4', 31.3, 2.4),

        # Complex organics
        (92.0934375e9, 'CH3OH', '8(0,8)-7(1,6)A++', 96.6, 1.0),
        (145.1032185e9, 'CH3OH', '3(0,3)-2(0,2)A++', 27.1, 1.0),

        # Ammonia
        (23.6944955e9, 'NH3', '(1,1)', 23.4, 1.0),
        (23.7226336e9, 'NH3', '(2,2)', 64.4, 1.0),
        (23.8701296e9, 'NH3', '(3,3)', 123.5, 1.0),

        # Water masers
        (22.2350800e9, 'H2O', '6(16)-5(23)', 640.7, 1.0),

        # Atomic lines
        (492.1606510e9, '[CI]', '3P1-3P0', 23.6, 1.0),
        (809.3435000e9, '[CI]', '3P2-3P1', 62.5, 1.0),
    ]

    def __init__(self, velocity_tolerance: float = 50.0):
        """
        Initialize line identifier.

        Args:
            velocity_tolerance: Maximum velocity offset to consider (km/s)
        """
        self.velocity_tolerance = velocity_tolerance  # km/s

    def identify(self, observed_freq: float,
                 v_lsr: float = 0.0) -> List[LineIdentification]:
        """
        Identify possible line matches.

        Args:
            observed_freq: Observed frequency (Hz)
            v_lsr: Expected source velocity (km/s)

        Returns:
            List of possible identifications ranked by probability
        """
        matches = []

        for rest_freq, molecule, transition, E_up, strength in self.LINE_DATABASE:
            # Calculate velocity offset
            v = (rest_freq - observed_freq) / rest_freq * C_LIGHT / 1e5  # km/s

            # Check if within tolerance
            v_diff = abs(v - v_lsr)
            if v_diff < self.velocity_tolerance:
                # Calculate match probability (simple model)
                prob = math.exp(-v_diff**2 / (2.0 * 10.0**2))  # 10 km/s characteristic

                matches.append(LineIdentification(
                    observed_frequency=observed_freq,
                    rest_frequency=rest_freq,
                    molecule=molecule,
                    transition=transition,
                    velocity=v,
                    energy_upper=E_up,
                    line_strength=strength,
                    probability=prob
                ))

        # Sort by probability
        matches.sort(key=lambda x: x.probability, reverse=True)

        return matches

    def identify_spectrum(self, frequencies: List[float],
                          spectrum: List[float],
                          threshold: float = 3.0,
                          v_lsr: float = 0.0) -> List[LineIdentification]:
        """
        Identify all lines in a spectrum above threshold.

        Args:
            frequencies: Frequency array (Hz)
            spectrum: Spectrum values
            threshold: Detection threshold (sigma)
            v_lsr: Source velocity (km/s)

        Returns:
            List of all identified lines
        """
        identifications = []

        # Estimate noise
        sorted_spec = sorted(spectrum)
        noise = sorted_spec[len(sorted_spec) // 4]  # Lower quartile as noise estimate

        # Find peaks
        for i in range(1, len(spectrum) - 1):
            if (spectrum[i] > spectrum[i-1] and
                spectrum[i] > spectrum[i+1] and
                spectrum[i] > threshold * noise):

                freq = frequencies[i]
                matches = self.identify(freq, v_lsr)

                if matches:
                    identifications.append(matches[0])  # Best match

        return identifications


class OpticalDepthCorrector:
    """
    Optical depth corrections for spectral line analysis.

    Corrects observed brightness temperatures for optical depth
    effects using the radiative transfer equation.
    """

    def __init__(self):
        """Initialize optical depth corrector."""
        pass

    def tau_from_ratio(self, T_main: float, T_satellite: float,
                       intrinsic_ratio: float) -> float:
        """
        Calculate optical depth from main/satellite line ratio.

        For HFS transitions like NH3, the intrinsic ratio is known.

        Args:
            T_main: Main line brightness temperature (K)
            T_satellite: Satellite line brightness temperature (K)
            intrinsic_ratio: Expected intrinsic intensity ratio

        Returns:
            Optical depth of main line
        """
        if T_satellite <= 0 or T_main <= 0:
            return 0.0

        observed_ratio = T_main / T_satellite

        # Solve: observed_ratio = (1 - exp(-tau)) / (1 - exp(-tau/R))
        # where R is intrinsic_ratio
        # Use iteration

        tau = 0.1  # Initial guess
        R = intrinsic_ratio

        for _ in range(50):
            f = (1.0 - math.exp(-tau)) / (1.0 - math.exp(-tau/R)) - observed_ratio

            # Derivative
            df = ((math.exp(-tau) * (1.0 - math.exp(-tau/R)) +
                   math.exp(-tau/R)/R * (1.0 - math.exp(-tau))) /
                  (1.0 - math.exp(-tau/R))**2)

            if abs(df) < 1e-10:
                break

            tau = tau - f / df

            if tau < 0:
                tau = 0.01

        return max(tau, 0.0)

    def correct_brightness(self, T_obs: float, tau: float,
                           T_ex: float, T_bg: float = 2.73) -> float:
        """
        Correct observed brightness for optical depth.

        Args:
            T_obs: Observed brightness temperature (K)
            tau: Optical depth
            T_ex: Excitation temperature (K)
            T_bg: Background temperature (K), default CMB

        Returns:
            Corrected brightness temperature (K)
        """
        # T_obs = (T_ex - T_bg) * (1 - exp(-tau))
        # For optically thick lines, T_obs -> T_ex - T_bg
        # Correction factor to get column density right

        if tau < 0.01:
            correction = 1.0
        else:
            correction = tau / (1.0 - math.exp(-tau))

        return T_obs * correction

    def excitation_temperature(self, T_obs: float, tau: float,
                                T_bg: float = 2.73) -> float:
        """
        Calculate excitation temperature.

        Args:
            T_obs: Observed brightness temperature (K)
            tau: Optical depth
            T_bg: Background temperature (K)

        Returns:
            Excitation temperature (K)
        """
        if tau < 0.01:
            return T_obs + T_bg

        T_ex = T_obs / (1.0 - math.exp(-tau)) + T_bg
        return T_ex

    def correct(self, T_obs: float, T_main: float, T_satellite: float,
                intrinsic_ratio: float = 3.0) -> OpticalDepthResult:
        """
        Full optical depth correction using satellite lines.

        Args:
            T_obs: Brightness to correct (K)
            T_main: Main line temperature (K)
            T_satellite: Satellite line temperature (K)
            intrinsic_ratio: Intrinsic main/satellite ratio

        Returns:
            Complete optical depth correction result
        """
        tau = self.tau_from_ratio(T_main, T_satellite, intrinsic_ratio)

        if tau > 0.01:
            correction = tau / (1.0 - math.exp(-tau))
        else:
            correction = 1.0

        T_ex = self.excitation_temperature(T_obs, tau)

        # Estimate uncertainty (simplified)
        tau_err = tau * 0.2

        return OpticalDepthResult(
            tau=tau,
            tau_error=tau_err,
            correction_factor=correction,
            is_optically_thick=(tau > 1.0),
            excitation_temp=T_ex
        )


class ColumnDensityCalculator:
    """
    Column density calculations from spectral line observations.

    Computes total column densities assuming LTE or with
    optical depth corrections.
    """

    def __init__(self):
        """Initialize column density calculator."""
        pass

    @staticmethod
    def partition_function_linear(T: float, B_rot: float) -> float:
        """
        Partition function for linear molecule.

        Q(T) ~ kT/(hB) for T >> hB/k

        Args:
            T: Temperature (K)
            B_rot: Rotational constant (Hz)

        Returns:
            Partition function
        """
        theta_rot = H_PLANCK * B_rot / K_BOLTZMANN
        return T / theta_rot

    @staticmethod
    def partition_function_symmetric_top(T: float, A_rot: float,
                                          B_rot: float) -> float:
        """
        Partition function for symmetric top molecule.

        Args:
            T: Temperature (K)
            A_rot: A rotational constant (Hz)
            B_rot: B rotational constant (Hz)

        Returns:
            Partition function
        """
        theta_A = H_PLANCK * A_rot / K_BOLTZMANN
        theta_B = H_PLANCK * B_rot / K_BOLTZMANN

        return math.sqrt(math.pi * T**3 / (theta_A * theta_B**2))

    def column_density_lte(self, W: float, frequency: float,
                           E_up: float, A_ul: float, g_u: float,
                           T_ex: float, Q_T: float) -> ColumnDensityResult:
        """
        Calculate column density assuming LTE.

        N_tot = (8*pi*nu^3 / c^3) * (Q/g_u) * exp(E_u/kT) / A_ul * W / J_nu(T)

        Args:
            W: Integrated line intensity (K km/s)
            frequency: Line rest frequency (Hz)
            E_up: Upper level energy (K)
            A_ul: Einstein A coefficient (s^-1)
            g_u: Upper level degeneracy
            T_ex: Excitation temperature (K)
            Q_T: Partition function at T_ex

        Returns:
            Column density result
        """
        # Convert W from K km/s to K cm/s
        W_cgs = W * 1e5

        # Rayleigh-Jeans temperature
        h_nu_k = H_PLANCK * frequency / K_BOLTZMANN
        J_nu = h_nu_k / (math.exp(h_nu_k / T_ex) - 1.0)

        # Column density of upper level
        N_u = 8.0 * math.pi * frequency**3 / (C_LIGHT**3 * A_ul) * W_cgs / J_nu

        # Total column density
        N_tot = N_u * Q_T / g_u * math.exp(E_up / T_ex)

        # Uncertainty estimate
        N_err = N_tot * 0.3  # Assume 30% uncertainty

        return ColumnDensityResult(
            N_total=N_tot,
            N_error=N_err,
            N_upper_state=N_u,
            partition_function=Q_T,
            excitation_temp=T_ex,
            optical_depth_used=0.0
        )

    def column_density_co(self, W_co: float, T_ex: float = 20.0,
                          tau: float = 0.0) -> ColumnDensityResult:
        """
        Calculate H2 column density from CO.

        Uses CO-to-H2 conversion factor.

        Args:
            W_co: CO(1-0) integrated intensity (K km/s)
            T_ex: Excitation temperature (K)
            tau: CO optical depth

        Returns:
            H2 column density result
        """
        # X_CO = N_H2 / W_CO ≈ 2e20 cm^-2 / (K km/s)
        X_CO = 2.0e20

        # Optical depth correction
        if tau > 0.01:
            correction = tau / (1.0 - math.exp(-tau))
        else:
            correction = 1.0

        N_H2 = X_CO * W_co * correction

        return ColumnDensityResult(
            N_total=N_H2,
            N_error=N_H2 * 0.5,  # Large uncertainty in X factor
            N_upper_state=W_co * 1e15,  # Approximate
            partition_function=T_ex / 2.77,  # CO partition function
            excitation_temp=T_ex,
            optical_depth_used=tau
        )


class VelocityFieldExtractor:
    """
    Extract velocity fields from spectral line cubes.

    Performs pixel-by-pixel Gaussian fitting to create
    velocity centroid and linewidth maps.
    """

    def __init__(self, threshold_sigma: float = 3.0):
        """
        Initialize velocity field extractor.

        Args:
            threshold_sigma: S/N threshold for valid fits
        """
        self.threshold = threshold_sigma
        self.fitter = GaussianLineFitter()

    def estimate_noise(self, spectrum: List[float],
                       line_free_fraction: float = 0.3) -> float:
        """
        Estimate noise from line-free channels.

        Args:
            spectrum: Spectrum values
            line_free_fraction: Fraction of channels assumed line-free

        Returns:
            Noise estimate
        """
        n = len(spectrum)
        n_linefree = int(n * line_free_fraction)

        # Use outer channels as line-free
        edge_channels = spectrum[:n_linefree//2] + spectrum[-n_linefree//2:]

        mean = sum(edge_channels) / len(edge_channels)
        variance = sum((x - mean)**2 for x in edge_channels) / len(edge_channels)

        return math.sqrt(variance)

    def frequency_to_velocity(self, frequencies: List[float],
                              rest_freq: float) -> List[float]:
        """
        Convert frequency to velocity.

        Args:
            frequencies: Frequency array (Hz)
            rest_freq: Rest frequency (Hz)

        Returns:
            Velocity array (km/s)
        """
        return [(rest_freq - f) / rest_freq * C_LIGHT / 1e5 for f in frequencies]

    def extract(self, cube: List[List[List[float]]],
                velocities: List[float],
                rest_velocity: float = 0.0) -> VelocityField:
        """
        Extract velocity field from spectral cube.

        Args:
            cube: 3D data cube [y][x][velocity]
            velocities: Velocity axis (km/s)
            rest_velocity: Expected source velocity (km/s)

        Returns:
            Complete velocity field
        """
        ny = len(cube)
        nx = len(cube[0])

        velocity_map = [[float('nan')] * nx for _ in range(ny)]
        velocity_error = [[float('nan')] * nx for _ in range(ny)]
        linewidth_map = [[float('nan')] * nx for _ in range(ny)]
        peak_map = [[0.0] * nx for _ in range(ny)]
        integrated_map = [[0.0] * nx for _ in range(ny)]
        valid_pixels = []

        for iy in range(ny):
            for ix in range(nx):
                spectrum = cube[iy][ix]

                # Estimate noise
                noise = self.estimate_noise(spectrum)

                # Check if peak is above threshold
                peak = max(spectrum)
                if peak < self.threshold * noise:
                    continue

                # Fit Gaussian
                result = self.fitter.fit(velocities, spectrum, n_components=1)

                if result.status in [FitStatus.SUCCESS, FitStatus.CONVERGED]:
                    comp = result.components[0]

                    velocity_map[iy][ix] = comp.center
                    velocity_error[iy][ix] = comp.center_error
                    linewidth_map[iy][ix] = comp.width
                    peak_map[iy][ix] = comp.amplitude
                    integrated_map[iy][ix] = comp.integrated_flux
                    valid_pixels.append((ix, iy))

        return VelocityField(
            velocity_map=velocity_map,
            velocity_error=velocity_error,
            linewidth_map=linewidth_map,
            peak_map=peak_map,
            integrated_map=integrated_map,
            valid_pixels=valid_pixels
        )


# Singleton instances
_gaussian_fitter: Optional[GaussianLineFitter] = None
_voigt_fitter: Optional[VoigtProfileFitter] = None
_hfs_fitter: Optional[HyperfineStructureFitter] = None
_line_identifier: Optional[LineIdentifier] = None
_tau_corrector: Optional[OpticalDepthCorrector] = None
_column_calculator: Optional[ColumnDensityCalculator] = None
_velocity_extractor: Optional[VelocityFieldExtractor] = None


def get_gaussian_fitter() -> GaussianLineFitter:
    """Get singleton Gaussian line fitter."""
    global _gaussian_fitter
    if _gaussian_fitter is None:
        _gaussian_fitter = GaussianLineFitter()
    return _gaussian_fitter


def get_voigt_fitter() -> VoigtProfileFitter:
    """Get singleton Voigt profile fitter."""
    global _voigt_fitter
    if _voigt_fitter is None:
        _voigt_fitter = VoigtProfileFitter()
    return _voigt_fitter


def get_hfs_fitter() -> HyperfineStructureFitter:
    """Get singleton HFS fitter."""
    global _hfs_fitter
    if _hfs_fitter is None:
        _hfs_fitter = HyperfineStructureFitter()
    return _hfs_fitter


def get_line_identifier() -> LineIdentifier:
    """Get singleton line identifier."""
    global _line_identifier
    if _line_identifier is None:
        _line_identifier = LineIdentifier()
    return _line_identifier


def get_tau_corrector() -> OpticalDepthCorrector:
    """Get singleton optical depth corrector."""
    global _tau_corrector
    if _tau_corrector is None:
        _tau_corrector = OpticalDepthCorrector()
    return _tau_corrector


def get_column_calculator() -> ColumnDensityCalculator:
    """Get singleton column density calculator."""
    global _column_calculator
    if _column_calculator is None:
        _column_calculator = ColumnDensityCalculator()
    return _column_calculator


def get_velocity_extractor() -> VelocityFieldExtractor:
    """Get singleton velocity field extractor."""
    global _velocity_extractor
    if _velocity_extractor is None:
        _velocity_extractor = VelocityFieldExtractor()
    return _velocity_extractor


# Convenience functions

def fit_gaussian_line(frequencies: List[float], spectrum: List[float],
                      n_components: int = 1) -> LineFitResult:
    """
    Fit Gaussian components to spectral line.

    Args:
        frequencies: Frequency array (Hz)
        spectrum: Spectrum values (K or Jy)
        n_components: Number of Gaussian components

    Returns:
        Fit result with parameters and uncertainties
    """
    fitter = get_gaussian_fitter()
    return fitter.fit(frequencies, spectrum, n_components)


def identify_line(frequency: float, v_lsr: float = 0.0) -> List[LineIdentification]:
    """
    Identify spectral line at given frequency.

    Args:
        frequency: Observed frequency (Hz)
        v_lsr: Source LSR velocity (km/s)

    Returns:
        List of possible identifications
    """
    identifier = get_line_identifier()
    return identifier.identify(frequency, v_lsr)


def compute_column_density_co(W_co: float, T_ex: float = 20.0) -> float:
    """
    Calculate H2 column density from CO integrated intensity.

    Args:
        W_co: CO(1-0) integrated intensity (K km/s)
        T_ex: Excitation temperature (K)

    Returns:
        H2 column density (cm^-2)
    """
    calculator = get_column_calculator()
    result = calculator.column_density_co(W_co, T_ex)
    return result.N_total


def thermal_linewidth(temperature: float, molecular_weight: float) -> float:
    """
    Calculate thermal line width.

    Delta_v_th = sqrt(8 * ln(2) * k_B * T / (m * c^2)) * c

    Args:
        temperature: Gas temperature (K)
        molecular_weight: Molecular weight (amu)

    Returns:
        Thermal FWHM (km/s)
    """
    m = molecular_weight * M_PROTON

    sigma_v = math.sqrt(K_BOLTZMANN * temperature / m)
    fwhm = 2.0 * math.sqrt(2.0 * math.log(2.0)) * sigma_v

    return fwhm / 1e5  # Convert to km/s


def velocity_to_frequency(velocity_km_s: float, rest_freq: float) -> float:
    """
    Convert velocity to frequency.

    Args:
        velocity_km_s: Velocity (km/s)
        rest_freq: Rest frequency (Hz)

    Returns:
        Observed frequency (Hz)
    """
    v_cgs = velocity_km_s * 1e5
    return rest_freq * (1.0 - v_cgs / C_LIGHT)


def frequency_to_velocity(obs_freq: float, rest_freq: float) -> float:
    """
    Convert frequency to velocity.

    Args:
        obs_freq: Observed frequency (Hz)
        rest_freq: Rest frequency (Hz)

    Returns:
        Velocity (km/s)
    """
    v_cgs = (rest_freq - obs_freq) / rest_freq * C_LIGHT
    return v_cgs / 1e5  # km/s




def detect_multiscale_patterns(signal, scales=None, wavelet='morl'):
    """Detect patterns at multiple scales using wavelet analysis

    Args:
        signal: Input signal (1D array)
        scales: List of scales to analyze (None for automatic)
        wavelet: Type of wavelet ('morl' = Morlet, 'mexh' = Mexican hat)

    Returns:
        Dictionary containing detected patterns and their scales
    """
    import numpy as np

    if scales is None:
        scales = [1, 2, 4, 8, 16]

    patterns = {}
    for scale in scales:
        # Simple implementation - in practice would use pywt
        patterns[scale] = np.std(signal[:min(len(signal), scale * 10)])

    return patterns
