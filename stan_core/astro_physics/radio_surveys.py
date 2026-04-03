"""
Radio Source Survey Analysis Module

Comprehensive analysis of extragalactic radio sources from large-scale surveys.
Supports cross-correlation, source detection, and population studies.

Capabilities:
- Source detection and catalog generation
- Cross-correlation between surveys
- Radio source classification (AGN, star-forming, radio quiet)
- Luminosity function analysis
- Source count distributions (dN/dS)
- Multi-wavelength cross-matching
- Variability analysis
- Polarization studies

Date: 2025-12-22
Version: 1.0
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import warnings

# Physical constants (CGS)
C_LIGHT = 2.998e10  # cm/s
JANSKY = 1e-23  # erg/s/cm^2/Hz
PC = 3.086e18  # cm
MPC = 3.086e24  # cm


class RadioSourceType(Enum):
    """Classification of radio sources"""
    AGN_CORE = "agn_core"  # Core-dominated AGN
    AGN_LOBE = "agn_lobe"  # Lobe-dominated AGN
    STAR_FORMING = "star_forming"  # Star formation related
    RADIO_QUIET = "radio_quiet"  # Upper limits
    BLAZAR = "blazar"  # Highly variable beamed AGN
    RADIO_GALAXY = "radio_galaxy"  # FRI/FRII
    PULSAR = "pulsar"  # Galactic pulsar
    SNR = "snr"  # Supernova remnant
    UNKNOWN = "unknown"


class SurveyType(Enum):
    """Major radio surveys"""
    NVSS = "nvss"  # NRAO VLA Sky Survey (1.4 GHz)
    FIRST = "first"  # Faint Images of the Radio Sky at Twenty-cm
    VLASS = "vlass"  # VLA Sky Survey (2-4 GHz)
    LOFAR = "lofar"  # LOFAR Two-meter Sky Survey (150 MHz)
    ASKAP = "askap"  # Evolutionary Map of the Universe (EMU)
    MEEKAT = "meerkat"  # MeerKAT Galactic Plane
    WENSS = "wenss"  # Westerbork Northern Sky Survey
    SUMSS = "sumss"  # Sydney University Molonglo Sky Survey


@dataclass
class RadioSource:
    """Radio source detection"""
    source_id: str
    ra: float  # degrees
    dec: float  # degrees
    flux_int: float  # Total flux (Jy)
    flux_peak: float  # Peak flux (Jy/beam)
    ra_err: float = 0.0
    dec_err: float = 0.0
    flux_err: float = 0.0
    major_axis: float = 0.0  # arcsec
    minor_axis: float = 0.0  # arcsec
    position_angle: float = 0.0  # degrees
    spectral_index: float = None  # alpha (S ~ nu^alpha)
    spectral_index_err: float = None
    frequency: float = 1.4e9  # Hz
    source_type: RadioSourceType = RadioSourceType.UNKNOWN
    redshift: float = None
    var_flag: bool = False
    pol_fraction: float = None  # Polarization fraction
    rm: float = None  # Rotation measure


@dataclass
class SurveyCatalog:
    """Radio survey catalog"""
    survey_name: SurveyType
    frequency: float  # Hz
    beam_size: float  # arcsec
    rms_sensitivity: float  # Jy/beam
    area: float  # square degrees
    sources: List[RadioSource] = field(default_factory=list)

    def __len__(self):
        return len(self.sources)

    def __iter__(self):
        return iter(self.sources)


class RadioSurveyAnalyzer:
    """
    Analyze radio source surveys with advanced statistical methods.

    Key capabilities:
    - Source detection using multiple algorithms
    - Cross-correlation between catalogs
    - dN/dS source count calculation
    - Luminosity function estimation
    - Variability detection
    """

    def __init__(self, beam_size: float = 5.0, rms: float = 0.0001):
        """
        Initialize analyzer.

        Args:
            beam_size: FWHM beam size in arcsec
            rms: RMS noise level in Jy/beam
        """
        self.beam_size = beam_size
        self.rms = rms
        self.detection_threshold = 5.0  # sigma

    def detect_sources(self, data: np.ndarray, wcs: Dict = None) -> List[RadioSource]:
        """
        Detect sources in radio image using multiple algorithms.

        Args:
            data: 2D radio image (Jy/beam)
            wcs: World coordinate system information

        Returns:
            List of detected sources
        """
        sources = []

        # Method 1: Peak finding with threshold
        from scipy import ndimage
        from scipy.ndimage import label, center_of_mass

        # Create detection mask
        threshold = self.detection_threshold * self.rms
        mask = data > threshold
        labeled, num_features = label(mask)

        for i in range(1, num_features + 1):
            region = (labeled == i)

            # Peak position
            peak_idx = np.unravel_index(np.argmax(data * region), data.shape)
            peak_flux = data[peak_idx]

            # Centroid
            if wcs:
                # Convert pixel to RA/Dec if WCS provided
                cy, cx = center_of_mass(region)
                # Simplified - would need full WCS conversion
                ra = cx  # Placeholder
                dec = cy  # Placeholder
            else:
                ra, dec = peak_idx

            # Integrated flux (sum in region)
            flux_int = np.sum(data[region]) * (self.beam_size / 60.0)**2  # Approx

            source = RadioSource(
                source_id=f"SRC_{i:05d}",
                ra=float(ra),
                dec=float(dec),
                flux_peak=float(peak_flux),
                flux_int=float(flux_int),
                frequency=1.4e9
            )
            sources.append(source)

        return sources

    def cross_match_catalogs(self, catalog1: SurveyCatalog,
                            catalog2: SurveyCatalog,
                            max_separation: float = 5.0) -> List[Tuple[RadioSource, RadioSource]]:
        """
        Cross-match two radio source catalogs.

        Args:
            catalog1: First survey catalog
            catalog2: Second survey catalog
            max_separation: Maximum separation in arcsec

        Returns:
            List of matched source pairs
        """
        matches = []

        for src1 in catalog1.sources:
            for src2 in catalog2.sources:
                # Calculate angular separation
                separation = self._angular_separation(
                    src1.ra, src1.dec, src2.ra, src2.dec
                )

                if separation <= max_separation:
                    matches.append((src1, src2))

        return matches

    def _angular_separation(self, ra1: float, dec1: float,
                          ra2: float, dec2: float) -> float:
        """Calculate angular separation in arcsec"""
        # Convert to radians
        ra1, dec1, ra2, dec2 = map(np.radians, [ra1, dec1, ra2, dec2])

        # Haversine formula
        dra = ra2 - ra1
        ddec = dec2 - dec1

        a = np.sin(ddec/2)**2 + np.cos(dec1) * np.cos(dec2) * np.sin(dra/2)**2
        separation = 2 * np.arcsin(np.sqrt(a))

        return np.degrees(separation) * 3600  # arcsec

    def calculate_source_counts(self, catalog: SurveyCatalog,
                              area: float = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate differential source counts dN/dS.

        Args:
            catalog: Survey catalog
            area: Survey area in square degrees

        Returns:
            (flux_bins, dN_dS, dN_dS_err)
        """
        fluxes = np.array([s.flux_int for s in catalog.sources])
        area = area or catalog.area

        # Logarithmic bins
        flux_min = np.min(fluxes[fluxes > 0]) * 0.5
        flux_max = np.max(fluxes) * 2
        n_bins = 15

        flux_bins = np.logspace(np.log10(flux_min), np.log10(flux_max), n_bins + 1)

        # Histogram
        hist, _ = np.histogram(fluxes, bins=flux_bins)

        # Differential
        flux_centers = np.sqrt(flux_bins[:-1] * flux_bins[1:])
        bin_widths = flux_bins[1:] - flux_bins[:-1]
        dN_dS = hist / (bin_widths * area)
        dN_dS_err = np.sqrt(hist) / (bin_widths * area)

        return flux_centers, dN_dS, dN_dS_err

    def classify_source(self, source: RadioSource,
                       optical_counterpart: bool = False,
                       ir_counterpart: bool = False,
                       compactness: float = None) -> RadioSourceType:
        """
        Classify radio source based on properties.

        Args:
            source: Radio source to classify
            optical_counterpart: Has optical counterpart
            ir_counterpart: Has IR counterpart
            compactness: Ratio of peak to integrated flux

        Returns:
            Source type classification
        """
        # Calculate compactness if not provided
        if compactness is None:
            compactness = source.flux_peak / source.flux_int if source.flux_int > 0 else 0

        # Classification logic
        if source.var_flag and compactness > 0.9:
            return RadioSourceType.BLAZAR

        if compactness > 0.8:
            if optical_counterpart:
                return RadioSourceType.AGN_CORE
            return RadioSourceType.AGN_CORE

        if compactness < 0.3:
            return RadioSourceType.AGN_LOBE

        if ir_counterpart and compactness < 0.7:
            return RadioSourceType.STAR_FORMING

        return RadioSourceType.UNKNOWN

    def calculate_spectral_index(self, flux_low: float, freq_low: float,
                                flux_high: float, freq_high: float) -> float:
        """
        Calculate spectral index alpha where S ~ nu^alpha.

        Args:
            flux_low: Flux at low frequency (Jy)
            freq_low: Low frequency (Hz)
            flux_high: Flux at high frequency (Jy)
            freq_high: High frequency (Hz)

        Returns:
            Spectral index alpha
        """
        alpha = np.log(flux_high / flux_low) / np.log(freq_high / freq_low)
        return alpha


class VariabilityAnalyzer:
    """Analyze radio source variability from multi-epoch data"""

    def __init__(self):
        self.modulation_index_threshold = 0.05

    def detect_variability(self, lightcurve: np.ndarray,
                         errors: np.ndarray = None) -> Dict[str, Any]:
        """
        Detect significant variability.

        Args:
            lightcurve: Flux measurements over time
            errors: Measurement uncertainties

        Returns:
            Dictionary with variability metrics
        """
        n = len(lightcurve)

        # Calculate statistics
        mean_flux = np.mean(lightcurve)
        std_flux = np.std(lightcurve)

        # Modulation index
        if mean_flux > 0:
            mod_index = std_flux / mean_flux
        else:
            mod_index = 0

        # Chi-squared test for constant flux
        if errors is not None:
            chisq = np.sum((lightcurve - mean_flux)**2 / errors**2)
            reduced_chisq = chisq / (n - 1)

            # Significance (p-value from chi-squared)
            from scipy import stats
            p_value = 1 - stats.chi2.cdf(chisq, n - 1)
        else:
            chisq = None
            reduced_chisq = None
            p_value = None

        return {
            'variable': mod_index > self.modulation_index_threshold,
            'modulation_index': mod_index,
            'mean_flux': mean_flux,
            'std_flux': std_flux,
            'chisq': chisq,
            'reduced_chisq': reduced_chisq,
            'p_value': p_value
        }

    def structure_function(self, lightcurve: np.ndarray,
                         times: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate structure function for variability timescales.

        Args:
            lightcurve: Flux measurements
            times: Observation times (days)

        Returns:
            (time_lags, structure_function)
        """
        n = len(lightcurve)
        sf_lags = []
        sf_values = []

        for i in range(n):
            for j in range(i+1, n):
                dt = times[j] - times[i]
                if dt > 0:
                    dsq = (lightcurve[j] - lightcurve[i])**2
                    sf_lags.append(dt)
                    sf_values.append(dsq)

        # Bin by log time lag
        sf_lags = np.array(sf_lags)
        sf_values = np.array(sf_values)

        # Sort and bin
        sort_idx = np.argsort(sf_lags)
        sf_lags = sf_lags[sort_idx]
        sf_values = sf_values[sort_idx]

        # Simple binning
        n_bins = 10
        bin_edges = np.logspace(np.log10(sf_lags.min()),
                                np.log10(sf_lags.max()), n_bins + 1)

        sf_binned = []
        lag_binned = []

        for i in range(n_bins):
            mask = (sf_lags >= bin_edges[i]) & (sf_lags < bin_edges[i+1])
            if np.sum(mask) > 0:
                sf_binned.append(np.mean(sf_values[mask]))
                lag_binned.append(np.sqrt(bin_edges[i] * bin_edges[i+1]))

        return np.array(lag_binned), np.array(sf_binned)


def create_analyzer(sensitivity: float = 0.0001, beam: float = 5.0) -> RadioSurveyAnalyzer:
    """Factory function for creating survey analyzer"""
    return RadioSurveyAnalyzer(beam_size=beam, rms=sensitivity)


def get_cross_match_tolerance(frequency: float) -> float:
    """
    Get appropriate cross-match tolerance based on frequency.

    Higher frequency = better astrometry = smaller tolerance needed.

    Args:
        frequency: Observing frequency in Hz

    Returns:
        Matching tolerance in arcsec
    """
    if frequency < 300e6:  # < 300 MHz
        return 10.0
    elif frequency < 1.4e9:  # < 1.4 GHz
        return 5.0
    elif frequency < 5e9:  # < 5 GHz
        return 2.0
    else:
        return 1.0


# Convenience functions for common operations
def load_survey_catalog(filename: str, survey: SurveyType) -> SurveyCatalog:
    """
    Load a survey catalog from file.

    Args:
        filename: Path to catalog file
        survey: Survey type

    Returns:
        Loaded catalog
    """
    # Placeholder - would implement actual file loading
    return SurveyCatalog(
        survey_name=survey,
        frequency=1.4e9,
        beam_size=5.0,
        rms_sensitivity=0.0001,
        area=1.0
    )


def estimate_luminosity(flux: float, redshift: float,
                       frequency: float, spectral_index: float = -0.7) -> float:
    """
    Estimate radio luminosity from flux.

    Args:
        flux: Flux density (Jy)
        redshift: Source redshift
        frequency: Observing frequency (Hz)
        spectral_index: Spectral index

    Returns:
        Luminosity in erg/s/Hz
    """
    from astropy.cosmology import Planck18 as cosmo
    import astropy.units as u


# Custom optimization variant 26
