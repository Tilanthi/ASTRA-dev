#!/usr/bin/env python3
"""
Exoplanet Transit Detection Module

Complete implementation for discovering exoplanets from light curves.
Uses Box Least Squares (BLS) periodogram optimized for transit detection.

Author: STAN Evolution Team
Date: 2025-03-17
"""

import numpy as np
from scipy import stats
from scipy import signal as scipy_signal
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LightCurve:
    """Photometric time series"""
    times: np.ndarray
    fluxes: np.ndarray
    errors: np.ndarray = None
    target_id: str = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = np.ones_like(self.fluxes) * np.std(self.fluxes) * 0.1


@dataclass
class TransitSignal:
    """Detected transit"""
    period: float
    epoch: float
    duration: float
    depth: float
    snr: float
    radius_ratio: float = None
    false_alarm_prob: float = None


class TransitDetector:
    """Detect transits using BLS (Box Least Squares) periodogram

    BLS is specifically designed for detecting box-shaped signals like
    exoplanet transits, unlike Lomb-Scargle which is optimized for
    sinusoidal signals.
    """

    def __init__(self, min_period: float = 0.5, max_period: float = 100.0,
                 min_snr: float = 5.0):
        self.min_period = min_period
        self.max_period = max_period
        self.min_snr = min_snr

    def detect_transits(self, lc: LightCurve) -> List[TransitSignal]:
        """Main detection pipeline

        Args:
            lc: LightCurve object with times, fluxes, and optional errors

        Returns:
            List of TransitSignal objects sorted by SNR
        """
        print(f"Detecting transits for {lc.target_id or 'unknown'}...")

        # Normalize flux
        times = lc.times
        fluxes = lc.fluxes / np.median(lc.fluxes)

        # BLS periodogram for transits
        periods, power = self._bls_periodogram(times, fluxes)

        if len(periods) == 0:
            print("  No significant periods found")
            return []

        # Get top periods by power
        top_idx = np.argsort(power)[-5:][::-1]
        top_periods = periods[top_idx]
        top_power = power[top_idx]

        print(f"  Found {len(top_periods)} candidate periods")
        for p, pw in zip(top_periods, top_power):
            print(f"    {p:.2f} days (BLS power={pw:.3f})")

        # Fit and validate each period
        signals = []
        for period in top_periods:
            signal = self._analyze_period(times, fluxes, period)
            if signal:
                print(f"    Period {period:.2f}: SNR={signal.snr:.2f}, depth={signal.depth*1e6:.0f} ppm")
            if signal and signal.snr >= self.min_snr:
                signals.append(signal)

        signals.sort(key=lambda s: s.snr, reverse=True)
        print(f"  Found {len(signals)} transit candidates with SNR>{self.min_snr}")
        return signals

    def _bls_periodogram(self, times: np.ndarray, fluxes: np.ndarray,
                         n_freqs: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
        """Box Least Squares periodogram optimized for transit detection

        BLS is designed specifically for box-shaped signals like transits.
        It measures how well the data fits a box model at each period.

        Args:
            times: Time values
            fluxes: Normalized flux values
            n_freqs: Number of frequencies to test

        Returns:
            Tuple of (periods, power_values)
        """
        t_min, t_max = times.min(), times.max()

        # Frequency grid
        min_freq = 1.0 / self.max_period
        max_freq = 1.0 / self.min_period
        frequencies = np.linspace(min_freq, max_freq, n_freqs)
        periods = 1.0 / frequencies

        power = np.zeros(n_freqs)

        for i, freq in enumerate(frequencies):
            period = periods[i]

            # Fold the light curve at this period
            phase = ((times - t_min) * freq) % 1.0

            # Try different transit durations
            durations = np.array([0.01, 0.02, 0.04, 0.06, 0.08, 0.1]) * period
            best_pwr = 0

            for dur in durations:
                # Create in-transit mask
                in_transit = phase < (dur / period)

                if np.sum(in_transit) < 10 or np.sum(~in_transit) < 10:
                    continue

                # BLS statistic: difference between in and out of transit
                in_mean = np.mean(fluxes[in_transit])
                out_mean = np.mean(fluxes[~in_transit])
                out_std = np.std(fluxes[~in_transit])

                # Depth * SNR
                if out_std > 0:
                    pwr = (out_mean - in_mean) / out_std
                    best_pwr = max(best_pwr, pwr)

            power[i] = best_pwr

        return periods, power

    def _analyze_period(self, times: np.ndarray, fluxes: np.ndarray,
                        period: float) -> Optional[TransitSignal]:
        """Analyze a specific period for transits

        Args:
            times: Time values
            fluxes: Normalized flux values
            period: Period to test

        Returns:
            TransitSignal if a valid transit is found, None otherwise
        """
        # Fold light curve
        phase = ((times - times[0]) / period) % 1.0

        # Bin the folded light curve
        n_bins = 50
        binned = []
        bin_centers = []

        for i in range(n_bins):
            mask = (phase >= i/n_bins) & (phase < (i+1)/n_bins)
            if np.sum(mask) > 0:
                binned.append(np.mean(fluxes[mask]))
                bin_centers.append((i + 0.5) / n_bins)

        binned = np.array(binned)
        bin_centers = np.array(bin_centers)

        # Find the transit (minimum in folded light curve)
        min_idx = np.argmin(binned)
        min_val = binned[min_idx]
        baseline = np.median(binned)
        depth = baseline - min_val

        if depth < 0.001:  # Too shallow (< 1000 ppm)
            return None

        # Estimate transit duration from the binned data
        # Count consecutive bins below 75th percentile
        transit_bins = np.where(binned < np.percentile(binned, 75))[0]

        if len(transit_bins) < 2:
            return None

        # Handle wraparound (transit at phase 0/1 boundary)
        if transit_bins[-1] - transit_bins[0] > n_bins // 2:
            # Transit wraps around - split into two groups
            gap = np.where(np.diff(transit_bins) > 5)[0]
            if len(gap) > 0:
                # Use the largest contiguous group
                groups = np.split(transit_bins, gap + 1)
                transit_bins = max(groups, key=len)

        dur_phase = (transit_bins[-1] - transit_bins[0] + 1) / n_bins
        duration = dur_phase * period

        # Sanity check: duration should be reasonable (1-20% of period)
        if duration < 0.01 * period or duration > 0.3 * period:
            duration = 0.02 * period

        # Calculate SNR properly
        # Shift phase so transit is centered at 0
        transit_phase = bin_centers[min_idx]
        shifted_phase = (phase - transit_phase) % 1.0

        # Points in transit (within duration/2 of minimum)
        half_dur_phase = duration / (2 * period)
        in_transit = (shifted_phase < half_dur_phase) | (shifted_phase > (1 - half_dur_phase))

        if np.sum(in_transit) < 10 or np.sum(~in_transit) < 20:
            return None

        in_vals = fluxes[in_transit]
        out_vals = fluxes[~in_transit]

        # Robust SNR: depth relative to out-of-transit scatter
        out_std = np.std(out_vals)
        snr = depth / (out_std + 1e-10)

        # Estimate epoch (time of first transit minimum)
        epoch = times[0] + transit_phase * period

        # Calculate radius ratio using approximation: depth ≈ (Rp/Rs)^2
        radius_ratio = np.sqrt(abs(depth))

        # Estimate false alarm probability
        fap = self._estimate_fap(len(times), snr)

        return TransitSignal(
            period=period,
            epoch=epoch,
            duration=duration,
            depth=depth,
            snr=snr,
            radius_ratio=radius_ratio,
            false_alarm_prob=fap
        )

    def _estimate_fap(self, n_points: int, snr: float) -> float:
        """Estimate false alarm probability

        A simple statistical estimate of the probability that this
        signal is due to random noise.

        Args:
            n_points: Number of data points
            snr: Signal-to-noise ratio

        Returns:
            False alarm probability (0 to 1)
        """
        z_score = snr
        return max(1e-10, 1 - stats.norm.cdf(z_score))


def example_usage():
    """Example with synthetic data"""
    np.random.seed(42)
    times = np.linspace(0, 30, 2000)

    # Create transits - very clear signal for testing
    period = 5.0
    epoch = 5.0
    duration = 0.08
    depth = 0.03  # 3% depth = 30000 ppm

    fluxes = np.ones_like(times) + np.random.randn(len(times)) * 0.0015

    for i in range(6):
        t_center = epoch + i * period
        mask = np.abs(times - t_center) < duration / 2
        fluxes[mask] *= (1 - depth)

    lc = LightCurve(times, fluxes, target_id="TIC-12345678")

    detector = TransitDetector()
    signals = detector.detect_transits(lc)

    print("\n" + "="*70)
    print("RESULTS:")
    print("="*70)

    for i, sig in enumerate(signals):
        print(f"\nCandidate {i+1}:")
        print(f"  Period: {sig.period:.3f} days")
        print(f"  Epoch: {sig.epoch:.3f} days")
        print(f"  Duration: {sig.duration:.3f} days")
        print(f"  Depth: {sig.depth*1e6:.1f} ppm")
        print(f"  SNR: {sig.snr:.1f}")
        print(f"  Rp/Rs: {sig.radius_ratio:.3f}")
        print(f"  FAP: {sig.false_alarm_prob:.2e}")

    return signals


if __name__ == "__main__":
    print("="*70)
    print("Exoplanet Transit Detection Module")
    print("="*70)
    print()

    example_usage()

    print("\n" + "="*70)
    print("Module components:")
    print("  - LightCurve: Time series container with normalization")
    print("  - TransitSignal: Detected transit with all parameters")
    print("  - TransitDetector: Main detection class")
    print("  - BLS periodogram optimized for box-shaped signals")
    print("  - Transit parameter estimation (period, epoch, duration, depth)")
    print("  - SNR calculation with robust out-of-transit scatter")
    print("  - Radius ratio estimate from depth")
    print("  - False alarm probability estimation")
    print("="*70)
