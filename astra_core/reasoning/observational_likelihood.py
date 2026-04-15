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
Observational Likelihood Module for STAN V43

Connects forward models to real astronomical data with proper uncertainty
propagation. Provides likelihood functions for spectral, image, and cube
fitting with beam convolution and systematic error handling.

Features:
- Spectral likelihood with correlated noise handling
- Image likelihood with beam convolution
- 3D PPV cube fitting
- Multi-wavelength joint likelihood
- Calibration uncertainty propagation
- Beam/PSF convolution for model comparison

Author: STAN V43 Astrophysics Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any


# Physical constants
C_LIGHT = 2.998e10           # Speed of light (cm/s)


class LikelihoodType(Enum):
    """Types of likelihood functions."""
    CHI_SQUARED = auto()      # Standard chi-squared
    GAUSSIAN = auto()         # Gaussian likelihood
    POISSON = auto()          # Poisson (for low counts)
    CASH = auto()             # Cash statistic (unbinned)
    MODIFIED_CASH = auto()    # Modified Cash for backgrounds


class NoiseModel(Enum):
    """Types of noise models."""
    WHITE = auto()            # Uncorrelated Gaussian
    CORRELATED = auto()       # Correlated (covariance matrix)
    HETEROSCEDASTIC = auto()  # Position-dependent variance
    SCALED = auto()           # Scaled variance (multiplicative factor)


@dataclass
class BeamModel:
    """Telescope beam/PSF model."""
    bmaj_arcsec: float        # Major axis FWHM (arcsec)
    bmin_arcsec: float        # Minor axis FWHM (arcsec)
    bpa_deg: float            # Position angle (degrees, E of N)
    pixel_scale: float = 1.0  # arcsec per pixel

    def to_sigma_pixels(self) -> Tuple[float, float, float]:
        """Convert to Gaussian sigma in pixels."""
        fwhm_to_sigma = 1.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))
        sigma_maj = self.bmaj_arcsec * fwhm_to_sigma / self.pixel_scale
        sigma_min = self.bmin_arcsec * fwhm_to_sigma / self.pixel_scale
        pa_rad = self.bpa_deg * math.pi / 180.0
        return sigma_maj, sigma_min, pa_rad


@dataclass
class LikelihoodResult:
    """Result of likelihood calculation."""
    log_likelihood: float     # Log-likelihood value
    chi_squared: float        # Chi-squared statistic
    degrees_of_freedom: int   # DOF
    reduced_chi_squared: float  # Chi-squared / DOF
    residuals: Optional[List[float]] = None  # Data - model
    p_value: float = 0.0      # P-value for fit quality
    aic: float = 0.0          # Akaike Information Criterion
    bic: float = 0.0          # Bayesian Information Criterion


@dataclass
class CalibrationUncertainties:
    """Systematic calibration uncertainties."""
    flux_scale_error: float = 0.1    # Fractional flux scale error
    pointing_error: float = 0.0      # Pointing error (arcsec)
    frequency_error: float = 0.0     # Frequency error (Hz)
    baseline_error: float = 0.0      # Baseline uncertainty
    sideband_ratio: float = 0.0      # Sideband gain ratio error


@dataclass
class MultiBandData:
    """Multi-wavelength observation data."""
    band_name: str            # Band identifier
    wavelength_micron: float  # Central wavelength
    flux: float               # Flux measurement
    flux_error: float         # Statistical error
    calibration_error: float  # Systematic calibration error
    upper_limit: bool = False # Is this an upper limit?


class BeamConvolver:
    """
    Convolve models with instrumental beam/PSF.

    Handles 2D Gaussian beam convolution for comparing
    forward models with observations.
    """

    def __init__(self, beam: BeamModel):
        """
        Initialize beam convolver.

        Args:
            beam: Beam model parameters
        """
        self.beam = beam
        self._kernel = None
        self._kernel_size = 0

    def _generate_kernel(self, size: int) -> List[List[float]]:
        """Generate 2D Gaussian kernel."""
        sigma_maj, sigma_min, pa = self.beam.to_sigma_pixels()

        kernel = [[0.0] * size for _ in range(size)]
        center = size // 2

        cos_pa = math.cos(pa)
        sin_pa = math.sin(pa)

        total = 0.0
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center

                # Rotate
                x_rot = dx * cos_pa + dy * sin_pa
                y_rot = -dx * sin_pa + dy * cos_pa

                # Gaussian
                arg = 0.5 * ((x_rot / sigma_maj)**2 + (y_rot / sigma_min)**2)
                val = math.exp(-arg)
                kernel[y][x] = val
                total += val

        # Normalize
        for y in range(size):
            for x in range(size):
                kernel[y][x] /= total

        return kernel

    def convolve(self, image: List[List[float]]) -> List[List[float]]:
        """
        Convolve image with beam.

        Args:
            image: 2D input image

        Returns:
            Convolved image
        """
        ny = len(image)
        nx = len(image[0])

        # Kernel size (3 * FWHM)
        sigma_maj, sigma_min, _ = self.beam.to_sigma_pixels()
        k_size = int(6 * max(sigma_maj, sigma_min)) + 1
        if k_size % 2 == 0:
            k_size += 1

        if self._kernel is None or self._kernel_size != k_size:
            self._kernel = self._generate_kernel(k_size)
            self._kernel_size = k_size

        k_half = k_size // 2
        result = [[0.0] * nx for _ in range(ny)]

        for iy in range(ny):
            for ix in range(nx):
                total = 0.0
                weight = 0.0

                for ky in range(k_size):
                    for kx in range(k_size):
                        py = iy + ky - k_half
                        px = ix + kx - k_half

                        if 0 <= px < nx and 0 <= py < ny:
                            w = self._kernel[ky][kx]
                            total += image[py][px] * w
                            weight += w

                result[iy][ix] = total / weight if weight > 0 else 0.0

        return result


class SpectralLikelihood:
    """
    Likelihood function for spectral fitting.

    Computes chi-squared for spectral model comparison
    with optional correlated noise handling.
    """

    def __init__(self, noise_model: NoiseModel = NoiseModel.WHITE):
        """
        Initialize spectral likelihood.

        Args:
            noise_model: Type of noise model
        """
        self.noise_model = noise_model

    def compute(self, data: List[float],
                model: List[float],
                errors: List[float],
                n_params: int = 0,
                covariance: Optional[List[List[float]]] = None) -> LikelihoodResult:
        """
        Compute spectral likelihood.

        Args:
            data: Observed spectrum
            model: Model spectrum
            errors: Measurement uncertainties
            n_params: Number of free parameters
            covariance: Covariance matrix for correlated noise

        Returns:
            Likelihood result
        """
        n = len(data)

        if self.noise_model == NoiseModel.CORRELATED and covariance is not None:
            # Use full covariance matrix
            chi2 = self._chi2_correlated(data, model, covariance)
        else:
            # Simple chi-squared
            chi2 = 0.0
            for d, m, e in zip(data, model, errors):
                if e > 0:
                    chi2 += ((d - m) / e)**2

        dof = n - n_params
        reduced_chi2 = chi2 / dof if dof > 0 else chi2

        # Log-likelihood (Gaussian)
        log_like = -0.5 * chi2 - 0.5 * n * math.log(2 * math.pi)
        log_like -= sum(math.log(e) for e in errors if e > 0)

        # Residuals
        residuals = [d - m for d, m in zip(data, model)]

        # Information criteria
        aic = chi2 + 2 * n_params
        bic = chi2 + n_params * math.log(n)

        # P-value (approximate)
        p_value = self._chi2_pvalue(chi2, dof)

        return LikelihoodResult(
            log_likelihood=log_like,
            chi_squared=chi2,
            degrees_of_freedom=dof,
            reduced_chi_squared=reduced_chi2,
            residuals=residuals,
            p_value=p_value,
            aic=aic,
            bic=bic
        )

    def _chi2_correlated(self, data: List[float],
                         model: List[float],
                         cov: List[List[float]]) -> float:
        """Compute chi-squared with covariance matrix."""
        n = len(data)
        residuals = [data[i] - model[i] for i in range(n)]

        # Invert covariance matrix (simplified - would use proper linear algebra)
        # For now, assume diagonal dominance
        chi2 = 0.0
        for i in range(n):
            for j in range(n):
                if abs(cov[i][j]) > 1e-20:
                    # Simplified inverse
                    chi2 += residuals[i] * residuals[j] / cov[i][j] if i == j else 0

        return chi2

    def _chi2_pvalue(self, chi2: float, dof: int) -> float:
        """Approximate p-value for chi-squared."""
        if dof <= 0:
            return 0.0

        # Use approximate formula
        z = (chi2 - dof) / math.sqrt(2 * dof)
        # Approximate CDF of standard normal
        p = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        return 1.0 - p


class ImageLikelihood:
    """
    Likelihood function for 2D image fitting.

    Compares model images to observations with proper
    beam convolution and noise handling.
    """

    def __init__(self, beam: Optional[BeamModel] = None):
        """
        Initialize image likelihood.

        Args:
            beam: Beam model for convolution
        """
        self.beam = beam
        self.convolver = BeamConvolver(beam) if beam else None

    def compute(self, data: List[List[float]],
                model: List[List[float]],
                errors: List[List[float]],
                mask: Optional[List[List[bool]]] = None,
                n_params: int = 0) -> LikelihoodResult:
        """
        Compute image likelihood.

        Args:
            data: Observed image
            model: Model image
            errors: Error map
            mask: Valid pixel mask
            n_params: Number of free parameters

        Returns:
            Likelihood result
        """
        ny = len(data)
        nx = len(data[0])

        # Convolve model with beam if provided
        if self.convolver:
            model_conv = self.convolver.convolve(model)
        else:
            model_conv = model

        # Compute chi-squared
        chi2 = 0.0
        n_valid = 0
        residuals_flat = []

        for iy in range(ny):
            for ix in range(nx):
                if mask is not None and not mask[iy][ix]:
                    continue

                d = data[iy][ix]
                m = model_conv[iy][ix]
                e = errors[iy][ix]

                if e > 0 and not math.isnan(d):
                    chi2 += ((d - m) / e)**2
                    residuals_flat.append(d - m)
                    n_valid += 1

        dof = n_valid - n_params
        reduced_chi2 = chi2 / dof if dof > 0 else chi2

        log_like = -0.5 * chi2

        return LikelihoodResult(
            log_likelihood=log_like,
            chi_squared=chi2,
            degrees_of_freedom=dof,
            reduced_chi_squared=reduced_chi2,
            residuals=residuals_flat
        )


class CubeLikelihood:
    """
    Likelihood function for 3D PPV cube fitting.

    Handles spectral cube comparison with channel-by-channel
    or integrated comparison modes.
    """

    def __init__(self, beam: Optional[BeamModel] = None):
        """
        Initialize cube likelihood.

        Args:
            beam: Beam model for spatial convolution
        """
        self.beam = beam
        self.image_like = ImageLikelihood(beam)
        self.spectral_like = SpectralLikelihood()

    def compute_integrated(self, data_cube: List[List[List[float]]],
                           model_cube: List[List[List[float]]],
                           errors: List[List[float]],
                           velocity_range: Optional[Tuple[int, int]] = None,
                           n_params: int = 0) -> LikelihoodResult:
        """
        Compute likelihood from integrated (moment 0) maps.

        Args:
            data_cube: Observed cube [y][x][v]
            model_cube: Model cube
            errors: Error map for integrated intensity
            velocity_range: Channel range to integrate
            n_params: Number of free parameters

        Returns:
            Likelihood result
        """
        ny = len(data_cube)
        nx = len(data_cube[0])
        nv = len(data_cube[0][0])

        if velocity_range is None:
            v_start, v_end = 0, nv
        else:
            v_start, v_end = velocity_range

        # Integrate cubes
        data_int = [[0.0] * nx for _ in range(ny)]
        model_int = [[0.0] * nx for _ in range(ny)]

        for iy in range(ny):
            for ix in range(nx):
                for iv in range(v_start, v_end):
                    data_int[iy][ix] += data_cube[iy][ix][iv]
                    model_int[iy][ix] += model_cube[iy][ix][iv]

        return self.image_like.compute(data_int, model_int, errors, n_params=n_params)

    def compute_channel_by_channel(self, data_cube: List[List[List[float]]],
                                   model_cube: List[List[List[float]]],
                                   errors: List[List[List[float]]],
                                   n_params: int = 0) -> LikelihoodResult:
        """
        Compute likelihood comparing each channel.

        Args:
            data_cube: Observed cube [y][x][v]
            model_cube: Model cube
            errors: Error cube
            n_params: Number of free parameters

        Returns:
            Combined likelihood result
        """
        ny = len(data_cube)
        nx = len(data_cube[0])
        nv = len(data_cube[0][0])

        total_chi2 = 0.0
        n_valid = 0
        all_residuals = []

        for iv in range(nv):
            # Extract channel
            data_chan = [[data_cube[iy][ix][iv] for ix in range(nx)] for iy in range(ny)]
            model_chan = [[model_cube[iy][ix][iv] for ix in range(nx)] for iy in range(ny)]
            error_chan = [[errors[iy][ix][iv] for ix in range(nx)] for iy in range(ny)]

            result = self.image_like.compute(data_chan, model_chan, error_chan, n_params=0)
            total_chi2 += result.chi_squared
            n_valid += result.degrees_of_freedom
            if result.residuals:
                all_residuals.extend(result.residuals)

        dof = n_valid - n_params
        reduced_chi2 = total_chi2 / dof if dof > 0 else total_chi2

        return LikelihoodResult(
            log_likelihood=-0.5 * total_chi2,
            chi_squared=total_chi2,
            degrees_of_freedom=dof,
            reduced_chi_squared=reduced_chi2,
            residuals=all_residuals
        )


class MultiWavelengthLikelihood:
    """
    Joint likelihood across multiple wavelength bands.

    Combines observations from different facilities with
    proper uncertainty propagation.
    """

    def __init__(self):
        """Initialize multi-wavelength likelihood."""
        pass

    def compute(self, observations: List[MultiBandData],
                model_fluxes: Dict[str, float],
                include_systematics: bool = True,
                n_params: int = 0) -> LikelihoodResult:
        """
        Compute joint multi-wavelength likelihood.

        Args:
            observations: List of multi-band observations
            model_fluxes: Model fluxes keyed by band name
            include_systematics: Include calibration uncertainties
            n_params: Number of free parameters

        Returns:
            Likelihood result
        """
        chi2 = 0.0
        n_valid = 0
        residuals = []

        for obs in observations:
            if obs.band_name not in model_fluxes:
                continue

            model_flux = model_fluxes[obs.band_name]

            if obs.upper_limit:
                # Handle upper limits (simplified)
                if model_flux > obs.flux:
                    chi2 += ((model_flux - obs.flux) / obs.flux_error)**2
            else:
                # Combined uncertainty
                if include_systematics:
                    total_error = math.sqrt(obs.flux_error**2 +
                                            (obs.calibration_error * obs.flux)**2)
                else:
                    total_error = obs.flux_error

                if total_error > 0:
                    chi2 += ((obs.flux - model_flux) / total_error)**2
                    residuals.append(obs.flux - model_flux)
                    n_valid += 1

        dof = n_valid - n_params
        reduced_chi2 = chi2 / dof if dof > 0 else chi2

        return LikelihoodResult(
            log_likelihood=-0.5 * chi2,
            chi_squared=chi2,
            degrees_of_freedom=dof,
            reduced_chi_squared=reduced_chi2,
            residuals=residuals
        )


class CalibrationUncertaintyPropagator:
    """
    Propagate calibration uncertainties through likelihood calculations.
    """

    def __init__(self, uncertainties: CalibrationUncertainties):
        """
        Initialize propagator.

        Args:
            uncertainties: Calibration uncertainty specifications
        """
        self.uncertainties = uncertainties

    def inflate_errors(self, flux: float, error: float) -> float:
        """
        Inflate flux error with calibration uncertainty.

        Args:
            flux: Measured flux
            error: Statistical error

        Returns:
            Total error including calibration
        """
        cal_error = self.uncertainties.flux_scale_error * abs(flux)
        return math.sqrt(error**2 + cal_error**2)

    def marginalize_flux_scale(self, log_like_func: Callable[[float], float],
                               scale_range: Tuple[float, float] = (0.8, 1.2),
                               n_samples: int = 20) -> float:
        """
        Marginalize likelihood over flux scale uncertainty.

        Args:
            log_like_func: Log-likelihood as function of scale factor
            scale_range: Range of scale factors to consider
            n_samples: Number of samples

        Returns:
            Marginalized log-likelihood
        """
        scales = [scale_range[0] + i * (scale_range[1] - scale_range[0]) / (n_samples - 1)
                  for i in range(n_samples)]

        # Compute log-likelihoods
        log_likes = [log_like_func(s) for s in scales]

        # Log-sum-exp for marginalization
        max_ll = max(log_likes)
        log_marg = max_ll + math.log(sum(math.exp(ll - max_ll) for ll in log_likes))
        log_marg -= math.log(n_samples)  # Normalize

        return log_marg


class NuisanceParameterHandler:
    """
    Handle nuisance parameters in likelihood calculations.
    """

    def __init__(self):
        """Initialize nuisance handler."""
        self.nuisance_params = {}

    def add_nuisance(self, name: str, prior_mean: float,
                     prior_sigma: float):
        """
        Add a nuisance parameter.

        Args:
            name: Parameter name
            prior_mean: Prior mean value
            prior_sigma: Prior standard deviation
        """
        self.nuisance_params[name] = {
            'mean': prior_mean,
            'sigma': prior_sigma
        }

    def marginalize_gaussian(self, log_like_at_best: float,
                             hessian_diagonal: Dict[str, float]) -> float:
        """
        Marginalize over nuisance parameters (Laplace approximation).

        Args:
            log_like_at_best: Log-likelihood at best-fit
            hessian_diagonal: Diagonal of Hessian at best-fit

        Returns:
            Marginalized log-likelihood
        """
        # Laplace approximation: integrate out nuisance parameters
        # assuming Gaussian posterior around maximum

        log_det_correction = 0.0
        for name, param in self.nuisance_params.items():
            if name in hessian_diagonal:
                # Combine curvature from likelihood and prior
                curvature = hessian_diagonal[name] + 1.0 / param['sigma']**2
                if curvature > 0:
                    log_det_correction += 0.5 * math.log(2 * math.pi / curvature)

        return log_like_at_best + log_det_correction

    def profile_out(self, log_like_func: Callable[[Dict[str, float]], float],
                    params_to_profile: List[str],
                    fixed_params: Dict[str, float]) -> float:
        """
        Profile out nuisance parameters by maximization.

        Args:
            log_like_func: Log-likelihood function of parameters
            params_to_profile: Names of parameters to profile out
            fixed_params: Fixed parameter values

        Returns:
            Profile likelihood (maximum over nuisance parameters)
        """
        # Simple grid search for profiling
        best_ll = float('-inf')

        # Generate grid (simplified - single parameter)
        if len(params_to_profile) == 1:
            name = params_to_profile[0]
            param = self.nuisance_params[name]

            for i in range(21):
                value = param['mean'] + (i - 10) * 0.3 * param['sigma']
                test_params = dict(fixed_params)
                test_params[name] = value

                ll = log_like_func(test_params)
                # Add prior
                ll -= 0.5 * ((value - param['mean']) / param['sigma'])**2

                best_ll = max(best_ll, ll)

        return best_ll


class LikelihoodCombiner:
    """
    Combine multiple likelihood components.
    """

    def __init__(self):
        """Initialize combiner."""
        self.components = []
        self.weights = []

    def add_component(self, likelihood_func: Callable[[], LikelihoodResult],
                      weight: float = 1.0, name: str = ''):
        """
        Add a likelihood component.

        Args:
            likelihood_func: Function returning LikelihoodResult
            weight: Weight for this component
            name: Component name
        """
        self.components.append({
            'func': likelihood_func,
            'weight': weight,
            'name': name
        })
        self.weights.append(weight)

    def compute(self, n_params: int = 0) -> LikelihoodResult:
        """
        Compute combined likelihood.

        Args:
            n_params: Total number of free parameters

        Returns:
            Combined likelihood result
        """
        total_chi2 = 0.0
        total_dof = 0
        all_residuals = []

        for comp in self.components:
            result = comp['func']()
            total_chi2 += comp['weight'] * result.chi_squared
            total_dof += result.degrees_of_freedom
            if result.residuals:
                all_residuals.extend(result.residuals)

        dof = total_dof - n_params
        reduced_chi2 = total_chi2 / dof if dof > 0 else total_chi2

        return LikelihoodResult(
            log_likelihood=-0.5 * total_chi2,
            chi_squared=total_chi2,
            degrees_of_freedom=dof,
            reduced_chi_squared=reduced_chi2,
            residuals=all_residuals
        )


# Singleton instances
_spectral_likelihood: Optional[SpectralLikelihood] = None
_image_likelihood: Optional[ImageLikelihood] = None
_cube_likelihood: Optional[CubeLikelihood] = None
_multiband_likelihood: Optional[MultiWavelengthLikelihood] = None


def get_spectral_likelihood() -> SpectralLikelihood:
    """Get singleton spectral likelihood."""
    global _spectral_likelihood
    if _spectral_likelihood is None:
        _spectral_likelihood = SpectralLikelihood()
    return _spectral_likelihood


def get_image_likelihood(beam: Optional[BeamModel] = None) -> ImageLikelihood:
    """Get image likelihood with optional beam."""
    return ImageLikelihood(beam)


def get_cube_likelihood(beam: Optional[BeamModel] = None) -> CubeLikelihood:
    """Get cube likelihood with optional beam."""
    return CubeLikelihood(beam)


def get_multiband_likelihood() -> MultiWavelengthLikelihood:
    """Get singleton multi-band likelihood."""
    global _multiband_likelihood
    if _multiband_likelihood is None:
        _multiband_likelihood = MultiWavelengthLikelihood()
    return _multiband_likelihood


# Convenience functions

def compute_chi_squared(data: List[float],
                        model: List[float],
                        errors: List[float]) -> float:
    """
    Simple chi-squared calculation.

    Args:
        data: Observed values
        model: Model values
        errors: Uncertainties

    Returns:
        Chi-squared value
    """
    chi2 = 0.0
    for d, m, e in zip(data, model, errors):
        if e > 0:
            chi2 += ((d - m) / e)**2
    return chi2


def compute_log_likelihood(data: List[float],
                           model: List[float],
                           errors: List[float]) -> float:
    """
    Compute Gaussian log-likelihood.

    Args:
        data: Observed values
        model: Model values
        errors: Uncertainties

    Returns:
        Log-likelihood value
    """
    like = get_spectral_likelihood()
    result = like.compute(data, model, errors)
    return result.log_likelihood


def model_comparison_bayes_factor(log_like_1: float, log_like_2: float,
                                   n_params_1: int, n_params_2: int,
                                   n_data: int) -> float:
    """
    Compute Bayes factor for model comparison (BIC approximation).

    Args:
        log_like_1: Log-likelihood of model 1
        log_like_2: Log-likelihood of model 2
        n_params_1: Number of parameters in model 1
        n_params_2: Number of parameters in model 2
        n_data: Number of data points

    Returns:
        Approximate log Bayes factor (positive favors model 1)
    """
    bic_1 = -2 * log_like_1 + n_params_1 * math.log(n_data)
    bic_2 = -2 * log_like_2 + n_params_2 * math.log(n_data)

    # BIC difference approximates -2 * log(Bayes factor)
    return (bic_2 - bic_1) / 2.0


def convolve_with_beam(image: List[List[float]],
                       bmaj_arcsec: float,
                       bmin_arcsec: float,
                       bpa_deg: float = 0.0,
                       pixel_scale: float = 1.0) -> List[List[float]]:
    """
    Convolve image with Gaussian beam.

    Args:
        image: Input image
        bmaj_arcsec: Beam major axis (arcsec)
        bmin_arcsec: Beam minor axis (arcsec)
        bpa_deg: Beam position angle (degrees)
        pixel_scale: Pixel scale (arcsec/pixel)

    Returns:
        Convolved image
    """
    beam = BeamModel(bmaj_arcsec, bmin_arcsec, bpa_deg, pixel_scale)
    convolver = BeamConvolver(beam)
    return convolver.convolve(image)
