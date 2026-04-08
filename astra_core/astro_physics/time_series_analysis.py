"""
Multi-Scale Inference Module
=============================

This module combines information across multiple temporal and spatial
scales for robust inference.

Key Functions:
- multi_scale_fusion: Combine evidence from multiple scales
- scale_voting: Ensemble inference across scales
"""


"""
Time Series and Power Spectrum Analysis Module

Comprehensive time series analysis for astrophysical signals.
Supports analysis of variable stars, AGN, transients, and periodic signals.

Key capabilities:
- Power spectral density estimation
- Period detection (Lomb-Scargle, phase dispersion)
- Autocorrelation analysis
- Wavelet analysis
- Quasi-periodic oscillations (QPOs)
- Time-domain filtering
- Cross-correlation and coherence
- Burst detection
- State space modeling

Date: 2025-12-22
Version: 1.0
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from scipy import signal, fft, stats
from scipy.interpolate import interp1d
import warnings

# Physical constants
DAY = 86400  # seconds
YEAR = 3.154e7  # seconds


class SignalType(Enum):
    """Types of astrophysical signals"""
    PERIODIC = "periodic"
    QUASI_PERIODIC = "quasi_periodic"
    STOCHASTIC = "stochastic"
    TRANSIENT = "transient"
    BURST = "burst"
    WHITE_NOISE = "white_noise"
    RED_NOISE = "red_noise"


@dataclass
class TimeSeries:
    """Time series data container"""
    times: np.ndarray  # Time values (days)
    values: np.ndarray  # Measured values
    errors: np.ndarray = None  # Measurement errors
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __len__(self):
        return len(self.times)

    def __post_init__(self):
        if self.errors is None:
            self.errors = np.ones_like(self.values)


@dataclass
class PeriodogramResult:
    """Result from periodogram analysis"""
    frequencies: np.ndarray  # Hz or cycles/day
    power: np.ndarray  # Power spectral density
    periods: np.ndarray = None  # Periods (days)
    peaks: List[Dict] = field(default_factory=list)
    false_alarm_prob: np.ndarray = None
    confidence: Dict[str, Any] = field(default_factory=dict)


class PowerSpectrumAnalyzer:
    """
    Power spectrum and frequency analysis.

    Methods:
    - Lomb-Scargle periodogram
    - Welch's method
    - Multi-taper method
    - Wavelet power spectrum
    """

    def __init__(self):
        self.nyquist_mult = 2.0  # Frequency multiplier for Nyquist

    def lomb_scargle(self, times: np.ndarray, values: np.ndarray,
                     errors: np.ndarray = None,
                     min_freq: float = None,
                     max_freq: float = None,
                     n_freqs: int = 10000) -> PeriodogramResult:
        """
        Lomb-Scargle periodogram for unevenly spaced data.

        Args:
            times: Time values (days)
            values: Measurement values
            errors: Measurement uncertainties
            min_freq: Minimum frequency (cycles/day)
            max_freq: Maximum frequency (cycles/day)
            n_freqs: Number of frequency points

        Returns:
            Periodogram result
        """
        # Frequency range
        t_span = times.max() - times.min()
        avg_dt = np.mean(np.diff(times))

        if min_freq is None:
            min_freq = 1.0 / t_span
        if max_freq is None:
            max_freq = 1.0 / (2 * avg_dt)  # Nyquist

        frequencies = np.linspace(min_freq, max_freq, n_freqs)

        # Use scipy's lombscargle
        from scipy.signal import lombscargle
        power = lombscargle(times, values, frequencies)

        # Periods
        periods = 1.0 / frequencies

        # False alarm probability
        n = len(times)
        false_alarm_prob = 1 - (1 - np.exp(-power))**(n-1)

        result = PeriodogramResult(
            frequencies=frequencies,
            power=power,
            periods=periods,
            false_alarm_prob=false_alarm_prob
        )

        return result

    def welch_method(self, times: np.ndarray, values: np.ndarray,
                    nperseg: int = 256,
                    overlap: int = None) -> PeriodogramResult:
        """
        Welch's method for evenly spaced data.

        Args:
            times: Time values (should be evenly spaced)
            values: Measurement values
            nperseg: Length of each segment
            overlap: Overlap between segments

        Returns:
            Periodogram result
        """
        # Check if evenly spaced
        dt = np.mean(np.diff(times))
        if np.std(np.diff(times)) / dt > 0.01:
            warnings.warn("Data not evenly spaced, consider interpolation")

        fs = 1.0 / dt  # Sampling frequency (1/day)

        frequencies, power = signal.welch(values, fs=fs,
                                             nperseg=nperseg,
                                             noverlap=overlap)

        # Convert to cycles/day
        result = PeriodogramResult(
            frequencies=frequencies,  # cycles/day
            power=power,
            periods=1.0 / frequencies
        )

        return result

    def find_peaks(self, result: PeriodogramResult,
                   threshold: float = 0.1,
                   min_distance: int = 10) -> List[Dict]:
        """
        Find peaks in periodogram.

        Args:
            result: Periodogram result
            threshold: Minimum peak height (relative)
            min_distance: Minimum distance between peaks (indices)

        Returns:
            List of peak properties
        """
        from scipy.signal import find_peaks

        # Normalize power
        power_norm = result.power / np.max(result.power)

        peaks, properties = find_peaks(power_norm,
                                        height=threshold,
                                        distance=min_distance)

        peak_list = []
        for peak_idx in peaks:
            peak_list.append({
                'period': result.periods[peak_idx],
                'frequency': result.frequencies[peak_idx],
                'power': result.power[peak_idx],
                'power_norm': power_norm[peak_idx],
                'fap': result.false_alarm_prob[peak_idx] if result.false_alarm_prob is not None else None
            })

        return peak_list


class VariabilityDetector:
    """
    Detect and characterize variability.

    Methods:
    - Stetson index
    - Chi-squared test against constancy
    - Structure function
    - Autocorrelation
    """

    def __init__(self):
        pass

    def stetson_index(self, times: np.ndarray, values: np.ndarray) -> float:
        """
        Calculate Stetson's variability index.

        Measures autocorrelation of variability.

        Args:
            times: Time values
            values: Measurement values

        Returns:
            Stetson's J index
        """
        # Normalize to unit variance
        mean_val = np.mean(values)
        std_val = np.std(values)
        if std_val == 0:
            return 0.0

        normalized = (values - mean_val) / std_val

        # Calculate Stetson's J
        J = 0
        n = len(times)

        for i in range(n):
            for j in range(n):
                if i != j:
                    delta_i = normalized[i]
                    delta_j = normalized[j]
                    J += np.sign(delta_i) * np.sign(delta_j) * min(abs(delta_i), abs(delta_j))

        J = J / (n * (n - 1))

        return J

    def chi2_constancy(self, values: np.ndarray, errors: np.ndarray) -> Tuple[float, float]:
        """
        Chi-squared test against constant flux.

        Args:
            values: Measured values
            errors: Measurement uncertainties

        Returns:
            (chi_squared, p_value)
        """
        mean_val = np.mean(values)

        chi2 = np.sum(((values - mean_val) / errors)**2)
        dof = len(values) - 1

        # P-value from chi-squared distribution
        p_value = 1 - stats.chi2.cdf(chi2, dof)

        return chi2, p_value

    def structure_function(self, times: np.ndarray, values: np.ndarray,
                         max_lag: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate structure function.

        SF(dt) = <(x(t) - x(t+dt))^2>

        Args:
            times: Time values
            values: Measured values
            max_lag: Maximum lag to compute

        Returns:
            (lags, structure_function)
        """
        n = len(times)

        if max_lag is None:
            max_lag = n // 2

        lags = []
        sf_values = []

        for lag in range(1, max_lag + 1):
            sf_pairs = []

            for i in range(n - lag):
                diff = values[i] - values[i + lag]
                sf_pairs.append(diff**2)

            if sf_pairs:
                lags.append(lag)
                sf_values.append(np.mean(sf_pairs))

        return np.array(lags), np.array(sf_values)


class WaveletAnalyzer:
    """
    Wavelet analysis for time-frequency decomposition.

    Useful for:
    - Time-varying periodicities
    - Quasi-periodic oscillations
    - Burst detection
    """

    def __init__(self):
        pass

    def continuous_wavelet_transform(self, times: np.ndarray,
                                     values: np.ndarray,
                                     frequencies: np.ndarray) -> np.ndarray:
        """
        Compute continuous wavelet transform.

        Args:
            times: Time values
            values: Measurement values
            frequencies: Analysis frequencies (cycles/day)

        Returns:
            Wavelet power [n_freqs, n_times]
        """
        import pywt

        # Interpolate to evenly spaced grid
        dt = np.mean(np.diff(times))
        time_grid = np.arange(times.min(), times.max(), dt)

        # Linear interpolation
        interp = interp1d(times, values, kind='linear', fill_value='extrapolate')
        values_grid = interp(time_grid)

        # CWT
        # Use Morlet wavelet
        scales = 1.0 / frequencies  # Approximate scaling
        cwt_coeffs, scales_result = pywt.cwt(values_grid, scales, 'morlet')

        # Power
        power = np.abs(cwt_coeffs)**2

        return power

    def global_wavelet_spectrum(self, times: np.ndarray,
                                values: np.ndarray,
                                frequencies: np.ndarray) -> np.ndarray:
        """
        Calculate global wavelet spectrum (time-averaged).

        Args:
            times: Time values
            values: Measurement values
            frequencies: Analysis frequencies

        Returns:
            Global wavelet power spectrum
        """
        power_2d = self.continuous_wavelet_transform(times, values, frequencies)
        global_power = np.mean(power_2d, axis=1)

        return global_power


class CrossCorrelationAnalyzer:
    """
    Cross-correlation and coherence analysis.

    Useful for:
    - Time delays
    - Reverberation mapping
    - Multi-wavelength correlations
    """

    def __init__(self):
        pass

    def cross_correlate(self, times1: np.ndarray, values1: np.ndarray,
                        times2: np.ndarray, values2: np.ndarray,
                        max_lag: int = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cross-correlate two time series.

        Args:
            times1: Time values for series 1
            values1: Measurement values for series 1
            times2: Time values for series 2
            values2: Measurement values for series 2
            max_lag: Maximum lag to compute

        Returns:
            (lags, correlation)
        """
        # Interpolate to common time grid
        t_min = max(times1.min(), times2.min())
        t_max = min(times1.max(), times2.max())

        dt = min(np.mean(np.diff(times1)), np.mean(np.diff(times2)))
        t_grid = np.arange(t_min, t_max, dt)

        interp1 = interp1d(times1, values1, kind='linear', fill_value='extrapolate')
        interp2 = interp1d(times2, values2, kind='linear', fill_value='extrapolate')

        v1 = interp1(t_grid)
        v2 = interp2(t_grid)

        # Cross-correlation
        correlation = signal.correlate(v1 - np.mean(v1),
                                        v2 - np.mean(v2),
                                        mode='same')

        # Normalize
        norm = np.sqrt(np.sum(v1**2) * np.sum(v2**2))
        correlation = correlation / norm

        # Lags
        lags = t_grid - t_grid[len(t_grid)//2]

        return lags, correlation

    def coherence(self, times1: np.ndarray, values1: np.ndarray,
                 times2: np.ndarray, values2: np.ndarray,
                 nperseg: int = 256) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate magnitude-squared coherence.

        Args:
            times1: Time values for series 1
            values1: Measurement values for series 1
            times2: Time values for series 2
            values2: Measurement values for series 2
            nperseg: Segment length

        Returns:
            (frequencies, coherence)
        """
        # Interpolate to common grid
        t_min = max(times1.min(), times2.min())
        t_max = min(times1.max(), times2.max())

        dt = min(np.mean(np.diff(times1)), np.mean(np.diff(times2)))
        t_grid = np.arange(t_min, t_max, dt)
        fs = 1.0 / dt

        interp1 = interp1d(times1, values1, kind='linear', fill_value='extrapolate')
        interp2 = interp1d(times2, values2, kind='linear', fill_value='extrapolate')

        v1 = interp1(t_grid)
        v2 = interp2(t_grid)

        # Coherence
        frequencies, coherence = signal.coherence(v1, v2, fs=fs,
                                                     nperseg=nperseg)

        return frequencies, coherence


class BurstDetector:
    """
    Detect transients and bursts in time series.

    Methods:
    - Sigma clipping
    - Bayesian blocks
    - Peak finding
    - Change point detection
    """

    def __init__(self, threshold: float = 5.0):
        """
        Initialize burst detector.

        Args:
            threshold: Detection threshold in sigma
        """
        self.threshold = threshold

    def sigma_clip(self, values: np.ndarray, errors: np.ndarray = None,
                  n_sigma: float = 5.0) -> List[Dict]:
        """
        Detect bursts using sigma clipping.

        Args:
            values: Measurement values
            errors: Measurement uncertainties
            n_sigma: Detection threshold

        Returns:
            List of burst detections
        """
        if errors is None:
            errors = np.std(values) * np.ones_like(values)

        # Compute significance
        mean_val = np.mean(values)
        significance = (values - mean_val) / errors

        # Find detections
        detections = np.where(significance > n_sigma)[0]

        bursts = []
        for idx in detections:
            bursts.append({
                'index': idx,
                'value': values[idx],
                'significance': significance[idx],
                'time': idx  # Placeholder
            })

        return bursts

    def bayesian_blocks(self, times: np.ndarray, values: np.ndarray,
                       errors: np.ndarray = None) -> List[Tuple[int, int]]:
        """
        Detect change points using Bayesian Blocks algorithm.

        Args:
            times: Time values
            values: Measurement values
            errors: Measurement uncertainties

        Returns:
            List of change point (start_idx, end_idx)
        """
        # Simplified Bayesian Blocks
        # Full implementation would be more complex

        n = len(values)
        edges = [0]

        # Simple variance-based change detection
        window = 10
        for i in range(window, n - window):
            before = values[i-window:i]
            after = values[i:i+window]

            # Kolmogorov-Smirnov test
            ks_stat, ks_p = stats.ks_2samp(before, after)

            if ks_p < 0.01:  # Significant change
                edges.append(i)

        edges.append(n)

        # Create edge pairs
        change_points = [(edges[i], edges[i+1]) for i in range(len(edges)-1)]

        return change_points


# Factory functions
def analyze_power_spectrum(times: np.ndarray, values: np.ndarray,
                          method: str = 'lomb_scargle') -> PeriodogramResult:
    """
    Analyze power spectrum of time series.

    Args:
        times: Time values (days)
        values: Measurement values
        method: Analysis method ('lomb_scargle', 'welch')

    Returns:
        Periodogram result
    """
    analyzer = PowerSpectrumAnalyzer()

    if method == 'lomb_scargle':
        return analyzer.lomb_scargle(times, values)
    elif method == 'welch':
        return analyzer.welch_method(times, values)
    else:
        raise ValueError(f"Unknown method: {method}")


def detect_periodicity(times: np.ndarray, values: np.ndarray,
                      min_period: float = None,
                      max_period: float = None) -> Dict[str, Any]:
    """
    Detect significant periods in time series.

    Args:
        times: Time values (days)
        values: Measurement values
        min_period: Minimum period to search (days)
        max_period: Maximum period to search (days)

    Returns:
        Detection results with period, significance, etc.
    """
    analyzer = PowerSpectrumAnalyzer()
    result = analyzer.lomb_scargle(times, values)

    # Find peaks
    peaks = analyzer.find_peaks(result, threshold=0.05)

    # Filter by period range
    if min_period is not None or max_period is not None:
        filtered_peaks = []
        for peak in peaks:
            period = peak['period']
            if min_period and period < min_period:
                continue
            if max_period and period > max_period:
                continue
            filtered_peaks.append(peak)
        peaks = filtered_peaks

    return {
        'peaks': peaks,
        'periodogram': result,
        'best_period': peaks[0]['period'] if peaks else None,
        'best_significance': peaks[0]['fap'] if peaks else None
    }


def compute_structure_function(times: np.ndarray, values: np.ndarray,
                             max_lag: int = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute structure function for variability analysis.

    Args:
        times: Time values (days)
        values: Measurement values
        max_lag: Maximum lag

    Returns:
        (lags, structure_function)
    """
    detector = VariabilityDetector()
    return detector.structure_function(times, values, max_lag)


def cross_correlate_series(times1: np.ndarray, values1: np.ndarray,
                           times2: np.ndarray, values2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Cross-correlate two time series.

    Args:
        times1: Time values for series 1
        values1: Measurement values for series 1
        times2: Time values for series 2
        values2: Measurement values for series 2

    Returns:
        (lags, correlation)
    """
    analyzer = CrossCorrelationAnalyzer()
    return analyzer.cross_correlate(times1, values1, times2, values2)



def check_temporal_constraints(events: List[Dict[str, Any]],
                             constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check if temporal sequence satisfies temporal logic constraints.

    Supports:
    - Before (A before B)
    - After (A after B)
    - Between (A between B and C)
    - Within (A within time_delta of B)

    Args:
        events: List of events with 'type' and 'timestamp'
        constraints: List of temporal constraints

    Returns:
        Dictionary with constraint satisfaction results
    """
    import numpy as np

    event_times = {e['type']: e['timestamp'] for e in events}

    results = {
        'all_satisfied': True,
        'constraint_results': [],
        'violations': []
    }

    for constraint in constraints:
        ctype = constraint['type']
        satisfied = True
        details = {}

        if ctype == 'before':
            # A must occur before B
            time_a = event_times.get(constraint['A'])
            time_b = event_times.get(constraint['B'])

            if time_a is None or time_b is None:
                satisfied = False
            else:
                satisfied = time_a < time_b
                details = {'time_difference': time_b - time_a}

        elif ctype == 'within':
            # A must occur within delta of B
            time_a = event_times.get(constraint['A'])
            time_b = event_times.get(constraint['B'])
            delta = constraint['delta']

            if time_a is None or time_b is None:
                satisfied = False
            else:
                satisfied = abs(time_a - time_b) <= delta
                details = {'actual_difference': abs(time_a - time_b), 'allowed': delta}

        elif ctype == 'between':
            # A must occur between B and C
            time_a = event_times.get(constraint['A'])
            time_b = event_times.get(constraint['B'])
            time_c = event_times.get(constraint['C'])

            if time_a is None or time_b is None or time_c is None:
                satisfied = False
            else:
                satisfied = min(time_b, time_c) <= time_a <= max(time_b, time_c)
                details = {'in_range': satisfied}

        results['constraint_results'].append({
            'constraint': constraint,
            'satisfied': satisfied,
            'details': details
        })

        if not satisfied:
            results['all_satisfied'] = False
            results['violations'].append(constraint)

    return results


def temporal_sequence_inference(observed: List[Dict[str, Any]],
                                knowledge_base: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Infer likely sequence completion based on temporal patterns.

    Args:
        observed: Observed events in sequence
        knowledge_base: Known temporal patterns

    Returns:
        Predicted next events with probabilities
    """
    import numpy as np

    # Extract observed sequence
    sequence_types = [e['type'] for e in observed]

    # Find matching patterns
    pattern_scores = []

    for pattern in knowledge_base:
        pattern_seq = pattern.get('sequence', [])

        # Check if observed matches pattern prefix
        matches_prefix = True
        match_length = 0

        for i, (obs, pat) in enumerate(zip(sequence_types, pattern_seq)):
            if obs == pat:
                match_length += 1
            else:
                matches_prefix = False
                break

        if matches_prefix and match_length > 0:
            # Score by match length and pattern confidence
            score = match_length * pattern.get('confidence', 0.5)
            pattern_scores.append({
                'pattern': pattern,
                'match_length': match_length,
                'score': score,
                'next_event': pattern_seq[match_length] if match_length < len(pattern_seq) else None
            })

    if not pattern_scores:
        return {'predictions': [], 'confidence': 0.0}

    # Sort by score
    pattern_scores.sort(key=lambda x: x['score'], reverse=True)

    # Get top predictions
    predictions = []
    for ps in pattern_scores[:5]:
        if ps['next_event']:
            predictions.append({
                'event_type': ps['next_event'],
                'confidence': ps['score'] / len(observed),
                'matched_pattern': ps['pattern'].get('name', 'unknown')
            })

    overall_confidence = max([p['confidence'] for p in predictions]) if predictions else 0.0

    return {
        'predictions': predictions,
        'confidence': overall_confidence,
        'num_patterns_matched': len(pattern_scores)
    }



def integrate_cross_scale_predictions(predictions: Dict[str, np.ndarray],
                                    scale_weights: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Integrate predictions from multiple scales with learned weights.

    Args:
        predictions: Dictionary mapping scale names to predictions
        scale_weights: Optional weights for each scale

    Returns:
        Integrated prediction with confidence
    """
    import numpy as np

    scales = list(predictions.keys())

    if not scales:
        return {'prediction': None, 'confidence': 0.0}
