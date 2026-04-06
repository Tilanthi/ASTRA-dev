"""
Multi-Wavelength Data Fusion for Astrophysical Discovery

This module implements data fusion techniques for combining observations
across radio, mm-wave, sub-mm, and infrared wavelengths.

Key capabilities:
- Cross-wavelength registration and alignment
- Multi-scale data fusion (different angular resolutions)
- Causal inference from combined datasets
- Spectral energy distribution (SED) fitting
- Component separation (different emission mechanisms)
- Automated source detection and classification
- Machine learning for feature extraction

Version: 3.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from scipy import ndimage, optimize
from scipy.interpolate import RegularGridInterpolator
import json


class WavelengthBand(Enum):
    """Astronomical wavelength bands."""
    RADIO = "radio"
    MILLIMETER = "millimeter"
    SUBMILLIMETER = "submillimeter"
    INFRARED = "infrared"
    OPTICAL = "optical"
    UV = "ultraviolet"
    XRAY = "xray"


class EmissionMechanism(Enum):
    """Physical emission mechanisms."""
    FREE_FREE = "free_free"  # Bremsstrahlung
    SYNCHROTRON = "synchrotron"
    DUST_CONTINUUM = "dust_continuum"
    THERMAL_DUST = "thermal_dust"
    ATOM_LINE = "atomic_line"
    MOLECULE_LINE = "molecular_line"
    RECOMBINATION_LINE = "recombination_line"
    PAH = "pah"  # Polycyclic aromatic hydrocarbons


@dataclass
class WavelengthData:
    """Data from a single wavelength observation."""
    band: WavelengthBand
    frequency: float  # Hz
    wavelength: float  # microns
    angular_resolution: float  # arcsec
    data: np.ndarray  # 2D or 3D data array
    uncertainty: Optional[np.ndarray] = None
    beam: Optional[np.ndarray] = None  # Point spread function
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiWavelengthDataset:
    """Combined dataset from multiple wavelengths."""
    datasets: Dict[WavelengthBand, WavelengthData]
    common_coordinates: np.ndarray  # World coordinate system
    common_resolution: float  # Lowest resolution (arcsec)


@dataclass
class SpectralEnergyDistribution:
    """Spectral energy distribution for a source."""
    frequencies: np.ndarray  # Hz
    fluxes: np.ndarray  # Jy
    uncertainties: np.ndarray  # Jy
    components: Dict[EmissionMechanism, np.ndarray] = field(default_factory=dict)


class BeamConvoler:
    """
    Convolution and deconvolution for different beam sizes.

    Used to match resolutions across wavelengths.
    """

    @staticmethod
    def gaussian_beam(fwhm: float, pixel_size: float, size: int = 101) -> np.ndarray:
        """
        Create a Gaussian beam kernel.

        Args:
            fwhm: Full width at half maximum (pixels)
            pixel_size: Pixel scale
            size: Kernel size

        Returns:
            Gaussian beam kernel
        """
        sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))

        x = np.linspace(-size//2, size//2, size) * pixel_size
        y = np.linspace(-size//2, size//2, size) * pixel_size
        X, Y = np.meshgrid(x, y)

        beam = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        beam /= np.sum(beam)  # Normalize

        return beam

    @staticmethod
    def convolve_to_common_beam(
        data: np.ndarray,
        input_beam: float,
        target_beam: float,
        pixel_size: float
    ) -> np.ndarray:
        """
        Convolve data to a larger (coarser) beam.

        Args:
            data: Input data array
            input_beam: Input beam FWHM (pixels)
            target_beam: Target beam FWHM (pixels)
            pixel_size: Pixel size

        Returns:
            Convolved data
        """
        if target_beam <= input_beam:
            return data  # Already higher resolution

        # Convolution beam
        conv_beam = np.sqrt(target_beam**2 - input_beam**2)
        kernel = BeamConvoler.gaussian_beam(conv_beam, pixel_size)

        # Convolve
        convolved = ndimage.convolve(data, kernel, mode='constant')

        return convolved


class MultiScaleFusion:
    """
    Multi-scale data fusion techniques.

    Combines data at different spatial scales/frequencies.
    """

    def __init__(self):
        self.pyramid_levels = 5
        self.fusion_method = "wavelet"  # wavelet, curvelet, pyramid

    def create_laplacian_pyramid(
        self,
        image: np.ndarray,
        levels: int
    ) -> List[np.ndarray]:
        """
        Create Laplacian pyramid for multi-scale analysis.

        Useful for combining data at different resolutions.
        """
        pyramid = []
        current = image.copy()

        for level in range(levels):
            # Smooth
            smoothed = ndimage.gaussian_filter(current, sigma=2**level)

            # Laplacian = current - smoothed
            laplacian = current - smoothed
            pyramid.append(laplacian)

            # Downsample for next level
            current = smoothed[::2, ::2]

        # Add residual low-frequency component
        pyramid.append(current)

        return pyramid

    def reconstruct_from_pyramid(self, pyramid: List[np.ndarray]) -> np.ndarray:
        """Reconstruct image from Laplacian pyramid."""
        current = pyramid[-1]

        for level in reversed(range(len(pyramid) - 1)):
            # Upsample
            upsampled = np.repeat(np.repeat(current, 2, axis=0), 2, axis=1)

            # Crop to match size
            target_shape = pyramid[level].shape
            current = upsampled[:target_shape[0], :target_shape[1]] + pyramid[level]

        return current

    def fuse_images(
        self,
        images: List[np.ndarray],
        weights: Optional[List[float]] = None
    ) -> np.ndarray:
        """
        Fuse multiple images using multi-scale approach.

        Args:
            images: List of images to fuse (same size)
            weights: Optional weights for each image

        Returns:
            Fused image
        """
        if weights is None:
            weights = [1.0] * len(images)

        # Create pyramids for each image
        pyramids = []
        for img in images:
            pyramid = self.create_laplacian_pyramid(img, self.pyramid_levels)
            pyramids.append(pyramid)

        # Combine pyramids
        fused_pyramid = []
        for level in range(self.pyramid_levels + 1):
            combined = np.zeros_like(pyramids[0][level])

            for i, pyramid in enumerate(pyramids):
                # Upsample if necessary
                level_data = pyramid[level]
                if level_data.shape != combined.shape:
                    level_data = ndimage.zoom(level_data,
                                             order=1,
                                             zoom=(combined.shape[0] / level_data.shape[0],
                                                   combined.shape[1] / level_data.shape[1]))
                combined += weights[i] * level_data

            fused_pyramid.append(combined)

        # Reconstruct
        fused = self.reconstruct_from_pyramid(fused_pyramid)

        return fused


class SpectralEnergyDistributionBuilder:
    """
    Build and analyze spectral energy distributions.

    Fits physical models to multi-wavelength photometry.
    """

    def __init__(self):
        self.dust_models = ["modified_blackbody", "power_law"]
        self.synchrotron_models = ["power_law", "curved_power_law"]
        self.free_free_models = ["thermal", "gaunt_factor"]

    def build_sed(
        self,
        fluxes: Dict[float, float],  # frequency -> flux
        uncertainties: Optional[Dict[float, float]] = None
    ) -> SpectralEnergyDistribution:
        """Build SED from flux measurements."""
        frequencies = np.array(sorted(fluxes.keys()))
        flux_array = np.array([fluxes[f] for f in frequencies])

        if uncertainties:
            err_array = np.array([uncertainties.get(f, 0.1 * fluxes[f]) for f in frequencies])
        else:
            err_array = 0.1 * flux_array  # 10% default

        return SpectralEnergyDistribution(
            frequencies=frequencies,
            fluxes=flux_array,
            uncertainties=err_array
        )

    def fit_modified_blackbody(
        self,
        sed: SpectralEnergyDistribution,
        freq_range: Tuple[float, float]
    ) -> Dict[str, float]:
        """
        Fit modified blackbody (dust emission).

        I_ν ∝ κ_ν * B_ν(T_d) with κ_ν ∝ ν^β
        """
        # Select frequency range
        mask = (sed.frequencies >= freq_range[0]) & (sed.frequencies <= freq_range[1])
        freq = sed.frequencies[mask]
        flux = sed.fluxes[mask]
        err = sed.uncertainties[mask]

        def model(params, nu):
            T_d, beta, amplitude = params

            # Planck function
            h = 6.626e-34
            k = 1.381e-23
            c = 3e8

            x = h * nu / (k * T_d)
            if np.any(x > 100):
                return np.inf

            B_nu = (2 * h * nu**3 / c**2) / (np.exp(x) - 1)

            # Modified blackbody
            I_nu = amplitude * (nu / 1e12)**beta * B_nu

            return I_nu

        def chi2(params):
            model_flux = model(params, freq)
            return np.sum((flux - model_flux)**2 / err**2)

        # Initial guess
        p0 = [20.0, 1.5, 1e-20]  # T_d, beta, amplitude

        # Fit
        result = optimize.minimize(chi2, p0, method='Nelder-Mead')

        if result.success:
            T_d, beta, amplitude = result.x

            return {
                'dust_temperature': T_d,
                'dust_emissivity': beta,
                'amplitude': amplitude,
                'chi2': result.fun
            }
        else:
            return {}

    def fit_synchrotron(
        self,
        sed: SpectralEnergyDistribution,
        freq_range: Tuple[float, float]
    ) -> Dict[str, float]:
        """
        Fit synchrotron emission model.

        I_ν ∝ ν^(-α) or curved spectrum
        """
        mask = (sed.frequencies >= freq_range[0]) & (sed.frequencies <= freq_range[1])
        freq = sed.frequencies[mask]
        flux = sed.fluxes[mask]
        err = sed.uncertainties[mask]

        def power_law(params, nu):
            alpha, amplitude = params
            return amplitude * (nu / 1e9)**(-alpha)

        def curved_power_law(params, nu):
            alpha_0, curvature, amplitude = params
            nu_0 = 1e9  # Reference frequency
            return amplitude * (nu / nu_0)**(-alpha_0 + curvature * np.log10(nu / nu_0))

        def chi2_simple(params):
            model_flux = power_law(params, freq)
            return np.sum((flux - model_flux)**2 / err**2)

        def chi2_curved(params):
            model_flux = curved_power_law(params, freq)
            return np.sum((flux - model_flux)**2 / err**2)

        # Try simple power law first
        p0_simple = [0.7, 1e-3]
        result_simple = optimize.minimize(chi2_simple, p0_simple, method='Nelder-Mead')

        # Try curved power law
        p0_curved = [0.7, 0.1, 1e-3]
        result_curved = optimize.minimize(chi2_curved, p0_curved, method='Nelder-Mead')

        if result_curved.fun < result_simple.fun and result_curved.success:
            alpha_0, curvature, amplitude = result_curved.x
            return {
                'spectral_index': alpha_0,
                'curvature': curvature,
                'amplitude': amplitude,
                'model_type': 'curved',
                'chi2': result_curved.fun
            }
        elif result_simple.success:
            alpha, amplitude = result_simple.x
            return {
                'spectral_index': alpha,
                'amplitude': amplitude,
                'model_type': 'power_law',
                'chi2': result_simple.fun
            }
        else:
            return {}

    def decompose_sed(
        self,
        sed: SpectralEnergyDistribution
    ) -> Dict[EmissionMechanism, Dict]:
        """
        Decompose SED into physical components.

        Returns contributions from:
        - Synchrotron (radio)
        - Free-free (radio/mm)
        - Thermal dust (far-IR/sub-mm)
        - PAH (mid-IR)
        """
        components = {}

        # Radio: synchrotron + free-free
        radio_mask = sed.frequencies < 100e9
        if np.any(radio_mask):
            sed_radio = SpectralEnergyDistribution(
                frequencies=sed.frequencies[radio_mask],
                fluxes=sed.fluxes[radio_mask],
                uncertainties=sed.uncertainties[radio_mask]
            )

            synchrotron = self.fit_synchrotron(sed_radio, (1e9, 50e9))
            if synchrotron:
                components[EmissionMechanism.SYNCHROTRON] = synchrotron

        # Sub-mm: thermal dust
        dust_mask = (sed.frequencies > 100e9) & (sed.frequencies < 2e12)
        if np.any(dust_mask):
            sed_dust = SpectralEnergyDistribution(
                frequencies=sed.frequencies[dust_mask],
                fluxes=sed.fluxes[dust_mask],
                uncertainties=sed.uncertainties[dust_mask]
            )

            dust = self.fit_modified_blackbody(sed_dust, (100e9, 2e12))
            if dust:
                components[EmissionMechanism.DUST_CONTINUUM] = dust

        return components


class ComponentSeparation:
    """
    Separate different emission components in multi-wavelength data.

    Techniques:
    - Independent component analysis (ICA)
    - Non-negative matrix factorization (NMF)
    - Bayesian fitting
    """

    def __init__(self):
        self.separation_methods = ["nmf", "ica", "bayesian"]

    def non_negative_matrix_factorization(
        self,
        data_cube: np.ndarray,
        n_components: int,
        max_iter: int = 1000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform NMF to separate components.

        Data ≈ W * H where W >= 0, H >= 0

        Args:
            data_cube: Shape (n_freq, n_x, n_y)
            n_components: Number of components to extract
            max_iter: Maximum iterations

        Returns:
            (W, H) where W is spectral shapes, H is spatial maps
        """
        n_freq, n_x, n_y = data_cube.shape
        n_pixels = n_x * n_y

        # Reshape to (n_freq, n_pixels)
        X = data_cube.reshape(n_freq, n_pixels)

        # Initialize W and H randomly
        W = np.random.rand(n_freq, n_components)
        H = np.random.rand(n_components, n_pixels)

        # Normalize
        W /= np.sum(W, axis=0, keepdims=True)

        # Multiplicative update rules
        for iteration in range(max_iter):
            # Update H
            numerator = W.T @ X
            denominator = W.T @ W @ H + 1e-10
            H *= numerator / denominator

            # Update W
            numerator = X @ H.T
            denominator = W @ H @ H.T + 1e-10
            W *= numerator / denominator

            # Normalize W
            W /= np.sum(W, axis=0, keepdims=True)

            # Renormalize H
            scale = np.sum(W, axis=0)
            H *= scale[np.newaxis, :]

        # Reshape H to (n_components, n_x, n_y)
        H_spatial = H.reshape(n_components, n_x, n_y)

        return W, H_spatial

    def independent_component_analysis(
        self,
        data_cube: np.ndarray,
        n_components: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform ICA to separate statistically independent components.

        Uses FastICA algorithm (simplified).
        """
        from sklearn.decomposition import FastICA

        n_freq, n_x, n_y = data_cube.shape
        n_pixels = n_x * n_y

        # Reshape
        X = data_cube.reshape(n_freq, n_pixels).T

        # Center data
        X -= np.mean(X, axis=0)

        # Whiten
        cov = np.cov(X.T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        D = np.diag(1.0 / np.sqrt(eigvals + 1e-10))
        V = eigvecs @ D @ eigvecs.T
        X_white = X @ V

        # FastICA
        ica = FastICA(n_components=n_components, random_state=42)
        S = ica.fit_transform(X_white)  # Independent components
        A = ica.mixing_  # Mixing matrix

        # Reshape components
        S_spatial = S.T.reshape(n_components, n_x, n_y)

        return A, S_spatial


class SourceDetection:
    """
    Automated source detection in multi-wavelength data.

    Algorithms:
    - Wavelet-based detection
    - Thresholding with noise estimation
    - Multi-wavelength cross-matching
    """

    def __init__(self):
        self.detection_threshold = 5.0  # Sigma
        self.min_pixels = 5

    def wavelet_detection(
        self,
        data: np.ndarray,
        scales: List[int] = [1, 2, 4, 8]
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detect sources using wavelet transform.

        Returns:
            (detection_map, source_catalog)
        """
        # Multi-scale wavelet transform (Mexican hat)
        wavelet_maps = []
        for scale in scales:
            # Mexican hat kernel
            size = 4 * scale + 1
            x = np.linspace(-size//2, size//2, size)
            y = np.linspace(-size//2, size//2, size)
            X, Y = np.meshgrid(x, y)
            r2 = X**2 + Y**2

            # Mexican hat wavelet
            wavelet = (1 - r2 / scale**2) * np.exp(-r2 / (2 * scale**2))
            wavelet /= np.sum(np.abs(wavelet))

            # Convolve
            convolved = ndimage.convolve(data, wavelet, mode='constant')
            wavelet_maps.append(convolved)

        # Combine scales
        combined = np.sqrt(np.mean(np.array(wavelet_maps)**2, axis=0))

        # Estimate noise
        noise = np.median(np.abs(combined)) / 0.6745

        # Threshold
        threshold = self.detection_threshold * noise
        detection_mask = combined > threshold

        # Find connected components
        labeled, num_features = ndimage.label(detection_mask)

        # Extract sources
        sources = []
        for i in range(1, num_features + 1):
            source_pixels = np.where(labeled == i)

            if len(source_pixels[0]) < self.min_pixels:
                continue

            # Source properties
            y_center = np.mean(source_pixels[0])
            x_center = np.mean(source_pixels[1])
            peak_value = np.max(data[source_pixels])
            total_flux = np.sum(data[source_pixels])

            sources.append({
                'id': i,
                'position': (y_center, x_center),
                'peak_flux': peak_value,
                'total_flux': total_flux,
                'num_pixels': len(source_pixels[0]),
                'snr': peak_value / noise
            })

        return combined, sources

    def cross_match_sources(
        self,
        source_catalogs: Dict[WavelengthBand, List[Dict]],
        matching_radius: float = 2.0  # arcsec
    ) -> List[Dict]:
        """
        Cross-match sources across wavelengths.

        Returns a unified catalog with multi-wavelength properties.
        """
        matched_sources = []

        # Use the longest wavelength catalog as reference
        reference_band = min(source_catalogs.keys(), key=lambda x: x.value)

        for ref_source in source_catalogs[reference_band]:
            matched = {
                'position': ref_source['position'],
                'reference_band': reference_band,
                'detections': {reference_band: ref_source}
            }

            # Match in other bands
            for band, catalog in source_catalogs.items():
                if band == reference_band:
                    continue

                for source in catalog:
                    # Calculate separation
                    dy = source['position'][0] - ref_source['position'][0]
                    dx = source['position'][1] - ref_source['position'][1]
                    separation = np.sqrt(dy**2 + dx**2)

                    if separation < matching_radius:
                        matched['detections'][band] = source
                        break

            # Count detections
            matched['n_detections'] = len(matched['detections'])
            matched['multi_wavelength'] = matched['n_detections'] > 1

            matched_sources.append(matched)

        return matched_sources


class CausalInferenceFusion:
    """
    Use causal inference to relate multi-wavelength observations.

    Identifies causal chains:
    - Physical processes causing emission at multiple wavelengths
    - Evolutionary sequences
    - Environmental dependencies
    """

    def __init__(self):
        self.causal_models = {}

    def discover_wavelength_causality(
        self,
        multi_wavelength_data: MultiWavelengthDataset
    ) -> Dict[str, Any]:
        """
        Discover causal relationships between wavelength emissions.

        For example:
        - Synchrotron emission (radio) caused by cosmic rays
        - Dust emission (sub-mm) caused by heating from stars (IR)
        - Free-free (radio) caused by HII regions (also emitting in IR)
        """
        # Extract correlation matrix across wavelengths
        bands = list(multi_wavelength_data.datasets.keys())
        n_bands = len(bands)

        correlation_matrix = np.zeros((n_bands, n_bands))

        for i, band_i in enumerate(bands):
            for j, band_j in enumerate(bands):
                data_i = multi_wavelength_data.datasets[band_i].data.flatten()
                data_j = multi_wavelength_data.datasets[band_j].data.flatten()

                # Correlation coefficient
                corr = np.corrcoef(data_i, data_j)[0, 1]
                correlation_matrix[i, j] = corr

        # Infer causal structure (simplified PC algorithm)
        # In practice, would need temporal or perturbation data
        causal_graph = self._build_causal_graph(correlation_matrix, bands)

        return {
            'correlation_matrix': correlation_matrix,
            'bands': [b.value for b in bands],
            'causal_graph': causal_graph,
            'physical_interpretations': self._interpret_causality(causal_graph)
        }

    def _build_causal_graph(
        self,
        correlation_matrix: np.ndarray,
        bands: List[WavelengthBand]
    ) -> Dict[str, List[str]]:
        """
        Build causal graph from correlations.

        Returns adjacency list: parent -> children
        """
        n = len(bands)
        graph = {band.value: [] for band in bands}

        # Simplified: high correlation implies causal connection
        # In reality, need temporal data or interventions
        threshold = 0.5

        for i in range(n):
            for j in range(n):
                if i != j and abs(correlation_matrix[i, j]) > threshold:
                    # Direction based on physical prior knowledge
                    # (in practice, would learn this)
                    if self._is_causal_parent(bands[i], bands[j]):
                        graph[bands[i].value].append(bands[j].value)

        return graph

    def _is_causal_parent(
        self,
        parent: WavelengthBand,
        child: WavelengthBand
    ) -> bool:
        """
        Determine if parent band causally influences child band.

        Based on astrophysical prior knowledge.
        """
        # Heating (short wavelength) -> dust emission (long wavelength)
        heating_bands = [WavelengthBand.UV, WavelengthBand.OPTICAL, WavelengthBand.INFRARED]
        dust_bands = [WavelengthBand.SUBMILLIMETER, WavelengthBand.MILLIMETER]

        if parent in heating_bands and child in dust_bands:
            return True

        # Cosmic rays -> synchrotron
        if parent == WavelengthBand.XRAY and child == WavelengthBand.RADIO:
            return True

        return False

    def _interpret_causality(
        self,
        causal_graph: Dict[str, List[str]]
    ) -> List[Dict]:
        """Interpret causal graph in physical terms."""
        interpretations = []

        for parent, children in causal_graph.items():
            for child in children:
                interpretations.append({
                    'cause': parent,
                    'effect': child,
                    'physical_mechanism': self._get_physical_mechanism(parent, child),
                    'confidence': 0.7  # Placeholder
                })

        return interpretations

    def _get_physical_mechanism(self, cause: str, effect: str) -> str:
        """Get physical mechanism for causal link."""
        mechanisms = {
            ('infrared', 'submillimeter'): 'Dust heating: IR radiation from stars heats dust grains which emit at sub-mm',
            ('ultraviolet', 'infrared'): 'PAH excitation: UV photons excite PAH molecules which emit in IR',
            ('xray', 'radio'): 'Cosmic ray electrons: X-ray emitting sources produce cosmic rays that emit synchrotron in radio',
            ('optical', 'millimeter'): 'Radiation field: Optical emission traces star formation which also heats dust (mm emission)',
        }

        return mechanisms.get((cause, effect), 'Unknown mechanism')


# =============================================================================
# Factory Functions
# =============================================================================

def create_multi_wavelength_dataset(
    data_dict: Dict[str, np.ndarray],
    frequencies: Dict[str, float],
    resolutions: Dict[str, float]
) -> MultiWavelengthDataset:
    """Create a multi-wavelength dataset from individual arrays."""
    datasets = {}

    for name, data in data_dict.items():
        if name == "radio":
            band = WavelengthBand.RADIO
        elif name == "mm":
            band = WavelengthBand.MILLIMETER
        elif name == "submm":
            band = WavelengthBand.SUBMILLIMETER
        elif name == "ir":
            band = WavelengthBand.INFRARED
        else:
            continue

        wavelength = 3e8 / frequencies[name] * 1e6  # microns

        datasets[band] = WavelengthData(
            band=band,
            frequency=frequencies[name],
            wavelength=wavelength,
            angular_resolution=resolutions[name],
            data=data
        )

    return MultiWavelengthDataset(
        datasets=datasets,
        common_coordinates=np.zeros((100, 100)),  # Placeholder
        common_resolution=max(resolutions.values())
    )


def create_sed_builder() -> SpectralEnergyDistributionBuilder:
    """Create an SED builder."""
    return SpectralEnergyDistributionBuilder()


def create_component_separator() -> ComponentSeparation:
    """Create a component separator."""
    return ComponentSeparation()


def create_source_detector() -> SourceDetection:
    """Create a source detector."""
    return SourceDetection()
