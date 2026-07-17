"""
Astronomical time-series analysis: periodicity search, variability character,
wavelet and structure-function analysis, and burst detection.

  * Lomb-Scargle periodogram (Lomb 1976; Scargle 1982) for uneven sampling.
  * Continuous wavelet transform with a Morlet mother wavelet (Torrence &
    Compo 1998).
  * First-order structure function SF(tau) = < |m(t+tau) - m(t)|^2 > (Simonetti
    et al. 1985; Hughes et al. 1992).
  * Discrete correlation function (Edelson & Krolik 1988) for two series.
  * Variability metrics: fractional variability and excess variance
    (Vaughan et al. 2003).
  * Burst detection by threshold crossing.

Implemented with numpy / scipy.signal where possible.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum
from scipy import signal as sps


class SignalType(Enum):
    PERIODIC = "periodic"
    STOCHASTIC = "stochastic"
    TRANSIENT = "transient"
    WHITE_NOISE = "white_noise"


@dataclass
class TimeSeries:
    time: np.ndarray
    flux: np.ndarray
    error: Optional[np.ndarray] = None

    def __post_init__(self):
        self.time = np.asarray(self.time, float)
        self.flux = np.asarray(self.flux, float)
        if self.error is not None:
            self.error = np.asarray(self.error, float)


@dataclass
class PeriodogramResult:
    frequency: np.ndarray     # 1/day (or whatever unit `time` is in)
    power: np.ndarray
    best_frequency: float
    best_period: float
    false_alarm_prob: Optional[float] = None


class PowerSpectrumAnalyzer:
    """Lomb-Scargle periodogram for unevenly sampled series."""

    def periodogram(self, ts: TimeSeries,
                    freq=None, nyquist_factor: float = 3.0) -> PeriodogramResult:
        t = ts.time - ts.time.mean()
        if freq is None:
            span = ts.time.max() - ts.time.min()
            f_min = 1.0 / span if span > 0 else 1.0
            f_max = nyquist_factor * 0.5 * len(ts.time) / span if span > 0 else 1.0
            freq = np.linspace(f_min, f_max, max(1000, 5 * len(ts.time)))
        # angular frequency for scipy.signal.lombscargle
        omega = 2 * np.pi * freq
        p = sps.lombscargle(t, ts.flux - ts.flux.mean(), omega, normalize=True)
        i = int(np.argmax(p))
        return PeriodogramResult(frequency=freq, power=p,
                                 best_frequency=float(freq[i]),
                                 best_period=float(1.0 / freq[i]) if freq[i] > 0 else np.inf)


class VariabilityDetector:
    """Fractional variability and excess (Poisson) variance."""

    def fractional_variability(self, ts: TimeSeries) -> Tuple[float, float]:
        f, e = ts.flux, (ts.error if ts.error is not None else np.zeros_like(ts.flux))
        mean = f.mean()
        var = f.var(ddof=1)
        mean_err2 = (e ** 2).mean()
        Fvar2 = (var - mean_err2) / mean ** 2
        Fvar = np.sqrt(Fvar2) if Fvar2 > 0 else 0.0
        return float(Fvar), float(np.sqrt(2 / len(f)) * var / mean ** 2 / (2 * Fvar)
                                  if Fvar > 0 else 0.0)

    def excess_variance(self, ts: TimeSeries) -> float:
        f, e = ts.flux, (ts.error if ts.error is not None else np.zeros_like(ts.flux))
        return float((f.var(ddof=1) - (e ** 2).mean()) / f.mean() ** 2)


class WaveletAnalyzer:
    """Continuous wavelet transform (Morlet, scipy.signal.cwt)."""

    def transform(self, ts: TimeSeries, widths=None) -> Tuple[np.ndarray, np.ndarray]:
        n = len(ts.time)
        if widths is None:
            widths = np.arange(1, max(2, n // 4))
        cwt = sps.cwt(ts.flux - ts.flux.mean(), sps.morlet2, widths, w=5.0)
        power = np.abs(cwt) ** 2
        return power, widths


class CrossCorrelationAnalyzer:
    """Discrete correlation function (Edelson & Krolik 1988)."""

    def dcf(self, ts1: TimeSeries, ts2: TimeSeries,
            lags=None, bin_width: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
        if lags is None:
            span = max(ts1.time.max(), ts2.time.max()) - min(ts1.time.min(), ts2.time.min())
            lags = np.linspace(-span / 2, span / 2, 50)
        if bin_width is None:
            bin_width = (lags[1] - lags[0]) if len(lags) > 1 else 1.0
        m1, m2 = ts1.flux - ts1.flux.mean(), ts2.flux - ts2.flux.mean()
        s1, s2 = ts1.flux.std(), ts2.flux.std()
        dcf = np.zeros_like(lags)
        for k, lag in enumerate(lags):
            pairs = []
            for i, ti in enumerate(ts1.time):
                for j, tj in enumerate(ts2.time):
                    if abs((tj - ti) - lag) <= bin_width:
                        pairs.append(m1[i] * m2[j])
            dcf[k] = np.mean(pairs) / (s1 * s2) if pairs else 0.0
        return dcf, lags


class BurstDetector:
    """Threshold-based transient/burst detection."""

    def detect(self, ts: TimeSeries, sigma: float = 5.0,
               min_duration: int = 1) -> list:
        med, mad = np.median(ts.flux), 1.4826 * np.median(np.abs(ts.flux - np.median(ts.flux)))
        if mad <= 0:
            mad = ts.flux.std()
        threshold = med + sigma * mad
        mask = ts.flux > threshold
        bursts = []
        i = 0
        while i < len(mask):
            if mask[i]:
                j = i
                while j < len(mask) and mask[j]:
                    j += 1
                if (j - i) >= min_duration:
                    bursts.append((int(ts.time[i]), int(ts.time[j - 1]), float(ts.flux[i:j].max())))
                i = j
            else:
                i += 1
        return bursts


def analyze_power_spectrum(ts: TimeSeries, freq=None) -> PeriodogramResult:
    return PowerSpectrumAnalyzer().periodogram(ts, freq)


def detect_periodicity(ts: TimeSeries, freq=None) -> Tuple[float, float]:
    """Return (best_period, peak_power)."""
    res = PowerSpectrumAnalyzer().periodogram(ts, freq)
    return res.best_period, float(res.power.max())


def compute_structure_function(ts: TimeSeries, n_bins: int = 20) -> Tuple[np.ndarray, np.ndarray]:
    """First-order structure function SF(tau) = <|m(t+tau)-m(t)|^2>."""
    t, f = ts.time, ts.flux
    dts, dsf = [], []
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            dts.append(t[j] - t[i])
            dsf.append((f[j] - f[i]) ** 2)
    dts, dsf = np.array(dts), np.array(dsf)
    edges = np.linspace(dts.min(), dts.max(), n_bins + 1)
    tau, sf = [], []
    for k in range(n_bins):
        m = (dts >= edges[k]) & (dts < edges[k + 1])
        if m.sum() > 0:
            tau.append(0.5 * (edges[k] + edges[k + 1]))
            sf.append(dsf[m].mean())
    return np.array(sf), np.array(tau)


def cross_correlate_series(ts1: TimeSeries, ts2: TimeSeries, lags=None):
    return CrossCorrelationAnalyzer().dcf(ts1, ts2, lags)


__all__ = [
    'SignalType', 'TimeSeries', 'PeriodogramResult', 'PowerSpectrumAnalyzer',
    'VariabilityDetector', 'WaveletAnalyzer', 'CrossCorrelationAnalyzer',
    'BurstDetector', 'analyze_power_spectrum', 'detect_periodicity',
    'compute_structure_function', 'cross_correlate_series',
]
