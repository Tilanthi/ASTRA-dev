#!/usr/bin/env python3

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
Radial Velocity Planet Detection Module

Complete implementation for discovering exoplanets from radial velocity data.
Uses Keplerian orbit fitting and periodogram analysis.

Author: STAN Evolution Team
Date: 2025-03-17
"""

import numpy as np
from scipy import optimize, stats
from scipy.signal import lombscargle
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class RVData:
    """Radial velocity time series"""
    times: np.ndarray
    velocities: np.ndarray
    errors: np.ndarray = None
    target_id: str = None

    def __post_init__(self):
        if self.errors is None:
            # Default error estimate based on scatter
            self.errors = np.ones_like(self.velocities) * np.std(self.velocities) * 0.1


@dataclass
class RVSignal:
    """Detected radial velocity signal"""
    period: float
    K: float  # Semi-amplitude (m/s)
    eccentricity: float
    omega: float  # Argument of periastron (rad)
    T0: float  # Time of periastron passage
    mass_minimum: float  # M sin i (in Jupiter masses, assuming M_star = 1 Msun)
    snr: float
    false_alarm_prob: float = None


class RVPeriodogram:
    """Periodogram analysis for radial velocity data"""

    def __init__(self, min_period: float = 0.5, max_period: float = 1000.0):
        self.min_period = min_period
        self.max_period = max_period

    def compute_lombscargle(self, times: np.ndarray, velocities: np.ndarray,
                            n_freqs: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute Lomb-Scargle periodogram

        Args:
            times: Observation times
            velocities: Radial velocity measurements
            n_freqs: Number of frequencies to test

        Returns:
            Tuple of (periods, power)
        """
        t_span = times.max() - times.min()

        # Frequency grid - use regular frequencies (cycles/day)
        # Lomb-Scargle expects angular frequencies (rad/day), so multiply by 2π
        min_f = 1.0 / (self.max_period * 1.1)
        max_f = 1.0 / (self.min_period * 0.9)
        frequencies = np.linspace(min_f, max_f, n_freqs)

        # Normalize velocities
        v_norm = velocities - np.mean(velocities)

        # Convert to angular frequencies for lombscargle
        angular_freqs = 2 * np.pi * frequencies

        # Compute Lomb-Scargle periodogram
        power = lombscargle(times, v_norm, angular_freqs, precenter=True)

        # Normalize power to [0, 1]
        power = power / (np.max(power) + 1e-10)

        periods = 1.0 / frequencies

        return periods, power

    def find_peaks(self, periods: np.ndarray, power: np.ndarray,
                   n_peaks: int = 5, min_prominence: float = 0.1) -> List[Tuple[int, float, float]]:
        """
        Find significant peaks in periodogram

        Args:
            periods: Period values
            power: Power values
            n_peaks: Number of peaks to return
            min_prominence: Minimum peak prominence

        Returns:
            List of (index, period, power) tuples
        """
        from scipy.signal import find_peaks

        peaks, properties = find_peaks(power, prominence=min_prominence, distance=10)

        if len(peaks) == 0:
            return []

        # Sort by prominence
        prominences = properties['prominences']
        sorted_idx = np.argsort(prominences)[::-1]

        top_peaks = []
        for i in sorted_idx[:n_peaks]:
            peak_idx = peaks[i]
            top_peaks.append((peak_idx, periods[peak_idx], power[peak_idx]))

        return top_peaks


class KeplerianFitter:
    """Fit Keplerian orbits to radial velocity data"""

    def __init__(self):
        pass

    def rv_model(self, t: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """
        Compute radial velocity for a Keplerian orbit

        Args:
            t: Time values
            params: Dictionary with orbit parameters:
                - period: Orbital period (days)
                - K: Semi-amplitude (m/s)
                - ecc: Eccentricity
                - omega: Argument of periastron (rad)
                - T0: Time of periastron passage
                - gamma: Systemic velocity (m/s)

        Returns:
            Radial velocity at each time
        """
        period = params['period']
        K = params['K']
        ecc = params['ecc']
        omega = params['omega']
        T0 = params['T0']
        gamma = params.get('gamma', 0.0)

        # Mean anomaly
        M = 2 * np.pi * (t - T0) / period

        # Solve Kepler's equation for eccentric anomaly E
        # M = E - e * sin(E)
        E = self._solve_kepler(M, ecc)

        # True anomaly
        cos_f = (np.cos(E) - ecc) / (1 - ecc * np.cos(E))
        sin_f = (np.sqrt(1 - ecc**2) * np.sin(E)) / (1 - ecc * np.cos(E))

        # Radial velocity
        rv = K * (cos_f * np.cos(omega) + sin_f * np.sin(omega)) + gamma

        return rv

    def _solve_kepler(self, M: np.ndarray, ecc: float, tol: float = 1e-10,
                     max_iter: int = 100) -> np.ndarray:
        """Solve Kepler's equation using Newton-Raphson"""
        E = M.copy()  # Initial guess

        for _ in range(max_iter):
            f = E - ecc * np.sin(E) - M
            df = 1 - ecc * np.cos(E)

            delta = f / df
            E = E - delta

            if np.max(np.abs(delta)) < tol:
                break

        return E

    def fit(self, times: np.ndarray, velocities: np.ndarray, errors: np.ndarray,
            period_guess: float) -> Tuple[Dict[str, float], float]:
        """
        Fit Keplerian orbit to RV data

        Args:
            times: Observation times
            velocities: RV measurements
            errors: Measurement errors
            period_guess: Initial period estimate

        Returns:
            Tuple of (fitted_parameters, chi_squared)
        """
        # Initial parameters
        v_mean = np.mean(velocities)
        v_std = np.std(velocities)

        def objective(params):
            """Objective function for optimization"""
            period, K, ecc, omega_rad, T0 = params

            # Constrain parameters
            K = abs(K)
            ecc = np.clip(ecc, 0, 0.99)  # Keep eccentricity < 1

            model_params = {
                'period': period,
                'K': K,
                'ecc': ecc,
                'omega': omega_rad,
                'T0': T0,
                'gamma': v_mean
            }

            model = self.rv_model(times, model_params)

            # Weighted chi-squared
            if errors is not None and np.any(errors > 0):
                chi2 = np.sum(((velocities - model) / errors)**2)
            else:
                chi2 = np.sum((velocities - model)**2) / v_std**2

            return chi2

        # Initial guess
        x0 = [
            period_guess,
            v_std,  # K
            0.1,  # ecc
            0.0,  # omega
            times[0]  # T0
        ]

        try:
            # Simple optimization without bounds for compatibility
            result = optimize.minimize(objective, x0, method='Nelder-Mead')

            fitted_params = {
                'period': abs(result.x[0]),
                'K': abs(result.x[1]),
                'ecc': np.clip(result.x[2], 0, 0.99),
                'omega': result.x[3] % (2 * np.pi),
                'T0': result.x[4],
                'gamma': v_mean
            }

            chi2 = result.fun

        except Exception as e:
            # Fallback to simple circular orbit
            fitted_params = {
                'period': period_guess,
                'K': v_std,
                'ecc': 0.0,
                'omega': 0.0,
                'T0': times[0],
                'gamma': v_mean
            }
            chi2 = objective([period_guess, v_std, 0, 0, times[0]])

        return fitted_params, chi2


class RVDetector:
    """
    Detect exoplanets from radial velocity data.

    Uses periodogram analysis and Keplerian orbit fitting.
    """

    def __init__(self, min_period: float = 0.5, max_period: float = 1000.0,
                 min_snr: float = 5.0):
        """
        Initialize RV detector

        Args:
            min_period: Minimum orbital period (days)
            max_period: Maximum orbital period (days)
            min_snr: Minimum SNR for detection
        """
        self.min_period = min_period
        self.max_period = max_period
        self.min_snr = min_snr

        self.periodogram = RVPeriodogram(min_period, max_period)
        self.fitter = KeplerianFitter()

    def detect_planets(self, rv_data: RVData) -> List[RVSignal]:
        """
        Detect planets from radial velocity data

        Args:
            rv_data: RVData object with times, velocities, errors

        Returns:
            List of detected RVSignals
        """
        print(f"Detecting planets from RV data for {rv_data.target_id or 'unknown'}...")

        # Preprocess
        times = rv_data.times
        velocities = rv_data.velocities
        errors = rv_data.errors

        # Remove outliers
        mask = np.abs(velocities - np.mean(velocities)) < 5 * np.std(velocities)
        times = times[mask]
        velocities = velocities[mask]
        if errors is not None:
            errors = errors[mask]

        # Compute periodogram
        periods, power = self.periodogram.compute_lombscargle(times, velocities)

        # Find peaks
        peaks = self.periodogram.find_peaks(periods, power, n_peaks=10)

        if len(peaks) == 0:
            print("  No significant periods found")
            return []

        print(f"  Found {len(peaks)} candidate periods")

        # Fit Keplerian orbits to top candidates
        signals = []
        for idx, period, pwr in peaks[:5]:
            print(f"    Period: {period:.2f} days (power={pwr:.3f})")

            # Fit orbit
            params, chi2 = self.fitter.fit(times, velocities, errors, period)

            # Calculate SNR
            model = self.fitter.rv_model(times, params)
            residuals = velocities - model

            # For RV, SNR is typically K / error where error is the RV measurement error
            if errors is not None and np.any(errors > 0):
                rms_error = np.sqrt(np.mean(errors**2))
                snr = params['K'] / rms_error
            else:
                rms_error = np.std(residuals)
                snr = params['K'] / (rms_error + 1e-10)

            print(f"      Fitted K={params['K']:.1f} m/s, SNR={snr:.1f}, chi2={chi2:.1f}")

            # Calculate minimum mass
            # M sin i (in Jupiter masses) = K * sqrt(1 - e^2) * (P/1yr)^(1/3) * (M_star/1Msun)^(2/3) / 28.4
            # Assuming M_star = 1 Msun
            P_yr = params['period'] / 365.25
            mass_min = (params['K'] * np.sqrt(1 - params['ecc']**2) *
                       (P_yr**(1/3)) / 28.4)

            # Estimate false alarm probability
            fap = self._estimate_fap(len(times), snr, pwr)

            if snr >= self.min_snr:
                print(f"      ** DETECTED: M sin i={mass_min:.2f} Mjup")

                signal = RVSignal(
                    period=params['period'],
                    K=params['K'],
                    eccentricity=params['ecc'],
                    omega=params['omega'],
                    T0=params['T0'],
                    mass_minimum=mass_min,
                    snr=snr,
                    false_alarm_prob=fap
                )
                signals.append(signal)

        # Sort by SNR
        signals.sort(key=lambda s: s.snr, reverse=True)

        print(f"  Found {len(signals)} planet candidates with SNR>{self.min_snr}")

        return signals

    def _estimate_fap(self, n_points: int, snr: float, power: float) -> float:
        """
        Estimate false alarm probability

        Args:
            n_points: Number of data points
            snr: Signal-to-noise ratio
            power: Periodogram power

        Returns:
            False alarm probability
        """
        # Simplified FAP estimation
        # In practice, would use bootstrap or analytic methods

        z_score = snr
        return max(1e-10, 1 - stats.norm.cdf(z_score))


def example_usage():
    """Example with synthetic RV data"""
    np.random.seed(42)

    # Create synthetic RV observations with more data
    n_obs = 100
    times = np.sort(np.random.uniform(0, 300, n_obs))  # 300 days, random sampling

    # Planet parameters
    period = 10.0  # days
    K = 50.0  # m/s (semi-amplitude)
    ecc = 0.3  # eccentricity
    omega = np.pi / 4  # argument of periastron
    T0 = 5.0  # time of periastron
    gamma = 0.0  # systemic velocity

    # Generate RV curve
    fitter = KeplerianFitter()
    true_rv = fitter.rv_model(times, {
        'period': period,
        'K': K,
        'ecc': ecc,
        'omega': omega,
        'T0': T0,
        'gamma': gamma
    })

    # Add noise
    error = 5.0  # m/s
    noisy_rv = true_rv + np.random.randn(len(times)) * error

    # Create RVData object
    rv_data = RVData(
        times=times,
        velocities=noisy_rv,
        errors=np.ones_like(times) * error,
        target_id="HD-123456"
    )

    # Detect planets
    detector = RVDetector(min_snr=3.0, max_period=50.0)
    signals = detector.detect_planets(rv_data)

    print("\n" + "="*70)
    print("RESULTS:")
    print("="*70)

    for i, sig in enumerate(signals):
        print(f"\nPlanet Candidate {i+1}:")
        print(f"  Period: {sig.period:.3f} days (true: {period:.1f})")
        print(f"  K: {sig.K:.2f} m/s (true: {K:.1f})")
        print(f"  Eccentricity: {sig.eccentricity:.3f} (true: {ecc:.1f})")
        print(f"  omega: {sig.omega:.3f} rad (true: {omega:.3f})")
        print(f"  T0: {sig.T0:.3f} (true: {T0:.1f})")
        print(f"  M sin i: {sig.mass_minimum:.3f} M_Jup")
        print(f"  SNR: {sig.snr:.1f}")

    return signals


if __name__ == "__main__":
    print("="*70)
    print("Radial Velocity Planet Detection")
    print("="*70)
    print()

    example_usage()

    print("\n" + "="*70)
    print("Module components:")
    print("  - RVData: Radial velocity time series container")
    print("  - RVSignal: Detected planet signal")
    print("  - RVPeriodogram: Lomb-Scargle periodogram analysis")
    print("  - KeplerianFitter: Keplerian orbit fitting")
    print("  - RVDetector: Main detection class")
    print("  - Minimum mass estimation")
    print("="*70)
