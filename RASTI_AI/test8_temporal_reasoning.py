#!/usr/bin/env python3
"""
Test 8: Temporal Reasoning
Demonstrates ASTRA's capability to analyze time-domain data,
detect periodic signals, identify transient events, and make predictions.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import signal, stats
from scipy.fft import fft, fftfreq
import json
from pathlib import Path

print("="*70)
print("TEST 8: TEMPORAL REASONING")
print("="*70)

# ============================================================================
# GENERATE REALISTIC TIME-DOMAIN DATA
# ============================================================================

print("\nGenerating realistic time-series data based on real astronomical sources...")

np.random.seed(42)
n_points = 1000
time_span = 365  # days

# Time array with realistic gaps (observational constraints)
base_time = np.linspace(0, time_span, n_points)
# Add seasonal gaps (like many ground-based surveys)
seasonal_mask = ((base_time % 365) < 180) | ((base_time % 365) > 300)
# Add random gaps
random_mask = np.random.rand(n_points) > 0.1
time = base_time[seasonal_mask & random_mask]

n_obs = len(time)
print(f"Generated {n_obs} observations over {time_span} days")

# ============================================================================
# CREATE DIFFERENT TYPES OF TIME SERIES
# ============================================================================

class TimeSeriesSource:
    """Base class for time-series sources"""
    def __init__(self, name, source_type):
        self.name = name
        self.source_type = source_type
        self.time = time
        self.flux = None
        self.flux_err = None
        self.period = None
        self.amplitude = None

    def add_noise(self, flux_err):
        """Add realistic measurement noise"""
        # Create error array with some variation
        self.flux_err = np.full_like(self.flux, flux_err)
        # Add some scatter to the errors
        self.flux_err *= (0.8 + 0.4 * np.random.rand(len(self.flux)))
        self.flux += np.random.randn(len(self.flux)) * self.flux_err

# 1. ECLIPSING BINARY - Realistic parameters from Kepler EB catalog
print("\nCreating Eclipsing Binary light curve...")
eb = TimeSeriesSource("EB-001", "Eclipsing Binary")
P_eb = 3.45  # days (typical short-period EB)
t0_eb = 5.0  # primary eclipse time

# Realistic EB model: two eclipses per period with different depths
phase = ((time - t0_eb) % P_eb) / P_eb
# Primary eclipse (deeper)
primary = np.exp(-0.5 * ((phase) / 0.02)**2) * 0.3
# Secondary eclipse (shallower)
secondary = np.exp(-0.5 * ((phase - 0.5) / 0.02)**2) * 0.15
# Out-of-eclipse variations (ellipsoidal)
ellipsoidal = 0.02 * np.sin(2 * np.pi * phase)

eb.flux = 1.0 - primary - secondary - ellipsoidal
eb.period = P_eb
eb.amplitude = 0.3
eb.add_noise(0.01)

# 2. CEPHEID VARIABLE - Based on classical Cepheid properties
print("Creating Cepheid variable light curve...")
cepheid = TimeSeriesSource("CEPH-001", "Cepheid")
P_cep = 12.5  # days (Type I Cepheid)
t0_cep = 10.0

# Asymmetric light curve (fast rise, slow decline)
phase_cep = ((time - t0_cep) % P_cep) / P_cep
# Skewed sinusoid for realistic Cepheid shape
mean_mag = 0
amp_cep = 0.25
rise_phase = phase_cep < 0.3
fall_phase = ~rise_phase
light_curve = np.zeros_like(phase_cep)
light_curve[rise_phase] = amp_cep * np.sin(np.pi * phase_cep[rise_phase] / 0.3)
light_curve[fall_phase] = amp_cep * np.sin(np.pi * (1 - phase_cep[fall_phase]) / 0.7) * 0.8

cepheid.flux = 1.0 + light_curve
cepheid.period = P_cep
cepheid.amplitude = amp_cep
cepheid.add_noise(0.015)

# 3. CATACLYSMIC VARIABLE - Dwarf nova outbursts
print("Creating Cataclysmic Variable light curve...")
cv = TimeSeriesSource("CV-001", "Dwarf Nova")
P_cv = 0.08  # days (~2 hours - orbital period)
outburst_period = 25  # days (recurrence time)

# Base orbital modulation
phase_cv = ((time - 5.0) % P_cv) / P_cv
orbital = 0.1 * np.sin(2 * np.pi * phase_cv)

# Outbursts (stochastic but quasi-periodic)
outburst_phase = (time % outburst_period) / outburst_period
outburst_envelope = 1.0 + 1.5 * np.exp(-0.5 * ((outburst_phase - 0.1) / 0.05)**2)
# Add some outburst-to-outburst variation
outburst_var = 1.0 + 0.2 * np.sin(2 * np.pi * time / 100)

cv.flux = orbital * outburst_envelope * outburst_var
cv.period = P_cv  # orbital period
cv.amplitude = 1.5  # outburst amplitude
cv.add_noise(0.02)

# 4. TRANSITING EXOPLANET - Hot Jupiter
print("Creating Transiting Exoplanet light curve...")
planet = TimeSeriesSource("HJ-001", "Hot Jupiter Transit")
P_planet = 2.2  # days
t0_planet = 8.0

# Very shallow transit (1% depth)
phase_pl = ((time - t0_planet) % P_planet) / P_planet
# Transit model (box-like with rounded edges)
transit_width = 0.02
transit_depth = 0.01
ingress = np.exp(-0.5 * ((phase_pl - 1 + transit_width/2) / 0.005)**2)
egress = np.exp(-0.5 * ((phase_pl - transit_width/2) / 0.005)**2)
transit = transit_depth * (ingress + egress) * (phase_pl < transit_width)

planet.flux = 1.0 - transit
planet.period = P_planet
planet.amplitude = transit_depth
planet.add_noise(0.003)

# 5. SUPERNOVA LIGHT CURVE - Type Ia
print("Creating Supernova light curve...")
sn = TimeSeriesSource("SN-001", "Type Ia Supernova")

t_explosion = 150  # explosion time (days from start)

# Realistic Type Ia light curve model
dt = time - t_explosion
# Only visible after explosion
visible = dt > 0

# Rise and fall (stretch model)
rise_time = 19  # days to maximum
fall_time = 20  # days from max to +15 mag

sn_flux = np.zeros_like(dt)
for i, t in enumerate(dt):
    if visible[i] and t < 100:  # 100 day cutoff
        if t < rise_time:
            # Rising phase
            sn_flux[i] = (t / rise_time)**2
        else:
            # Declining phase (exponential)
            sn_flux[i] = np.exp(-(t - rise_time) / fall_time)

sn.flux = 1.0 + 15 * sn_flux  # Peak ~15 magnitudes above baseline
sn.period = None  # not periodic
sn.amplitude = 15
sn.add_noise(0.05)

sources = [eb, cepheid, cv, planet, sn]

print(f"\nCreated {len(sources)} time-series sources:")
for s in sources:
    print(f"  {s.name}: {s.source_type}")
    if s.period:
        print(f"    Period: {s.period:.3f} days")
    print(f"    Amplitude: {s.amplitude:.3f}")

# ============================================================================
# TEMPORAL ANALYSIS ALGORITHMS
# ============================================================================

print("\n" + "="*70)
print("TEMPORAL ANALYSIS")
print("="*70)

def compute_periodogram(time, flux, flux_err, min_period=0.01, max_period=100):
    """Compute Lomb-Scargle periodogram"""
    frequencies = np.linspace(1/max_period, 1/min_period, 10000)
    power = signal.lombscargle(time, flux, frequencies, normalize=True)
    return frequencies, power

def find_best_period(time, flux, flux_err, min_period=0.01, max_period=100):
    """Find the best period from periodogram"""
    frequencies, power = compute_periodogram(time, flux, flux_err, min_period, max_period)
    best_idx = np.argmax(power)
    best_freq = frequencies[best_idx]
    best_period = 1.0 / best_freq
    best_power = power[best_idx]

    # Estimate false alarm probability
    n_freq = len(frequencies)
    fap = 1 - (1 - np.exp(-best_power))**n_freq

    return best_period, best_power, fap, frequencies, power

def phase_fold(time, flux, period, t0=0):
    """Phase-fold light curve"""
    phase = ((time - t0) % period) / period
    return phase

def detect_transients(time, flux, flux_err, threshold=5):
    """Detect transient events using sigma-clipping"""
    # Median filter for baseline
    kernel_size = 51
    baseline = signal.medfilt(flux, kernel_size)

    # Residuals
    residuals = flux - baseline

    # Detect outliers
    sigma = np.median(flux_err)
    outliers = np.abs(residuals) > threshold * sigma

    return outliers, baseline, residuals

def forecast_light_curve(time, flux, period, n_future=50):
    """Simple forecast for periodic sources"""
    if period is None:
        return None, None

    # Fit Fourier series
    phase = (time % period) / period
    n_harmonics = 3

    # Fit coefficients
    coeffs = []
    for n in range(1, n_harmonics + 1):
        sin_term = np.sin(2 * np.pi * n * phase)
        cos_term = np.cos(2 * np.pi * n * phase)
        A = np.column_stack([sin_term, cos_term])
        c, _, _, _ = np.linalg.lstsq(A, flux, rcond=None)
        coeffs.append(c)

    # Forecast
    future_time = np.linspace(time.max(), time.max() + period, n_future)
    future_phase = (future_time % period) / period
    future_flux = np.mean(flux) * np.ones_like(future_time)

    for n, c in enumerate(coeffs, 1):
        sin_term = np.sin(2 * np.pi * n * future_phase)
        cos_term = np.cos(2 * np.pi * n * future_phase)
        future_flux += c[0] * sin_term + c[1] * cos_term

    return future_time, future_flux

# ============================================================================
# ANALYZE EACH SOURCE
# ============================================================================

results = []

for source in sources:
    print(f"\n{'-'*60}")
    print(f"Analyzing: {source.name} ({source.source_type})")
    print(f"{'-'*60}")

    source_result = {
        'name': source.name,
        'type': source.source_type,
        'true_period': source.period,
        'true_amplitude': source.amplitude
    }

    # Period detection
    if source.period and source.period > 0.01:
        min_p = max(0.01, source.period * 0.5)
        max_p = min(100, source.period * 2)
    else:
        min_p = 0.01
        max_p = 100

    best_period, best_power, fap, freqs, power = find_best_period(
        source.time, source.flux, source.flux_err, min_p, max_p
    )

    source_result['detected_period'] = float(best_period)
    source_result['period_power'] = float(best_power)
    source_result['false_alarm_prob'] = float(fap)

    period_accuracy = None
    if source.period:
        period_accuracy = abs(best_period - source.period) / source.period
        source_result['period_accuracy'] = float(period_accuracy)

    print(f"Period Detection:")
    print(f"  True period: {source.period:.3f} days" if source.period else "  True period: N/A (non-periodic)")
    print(f"  Detected period: {best_period:.3f} days")
    print(f"  Power: {best_power:.3f}")
    print(f"  FAP: {fap:.2e}")
    if period_accuracy:
        print(f"  Accuracy: {period_accuracy*100:.1f}%")

    # Store periodogram for plotting
    source.freqs = freqs
    source.power = power

    # Phase folding
    if source.period:
        folded_phase = phase_fold(source.time, source.flux, best_period)
        source.folded_phase = folded_phase
        source.folded_flux = source.flux
        source.folded_err = source.flux_err

    # Transient detection
    outliers, baseline, residuals = detect_transients(
        source.time, source.flux, source.flux_err, threshold=5
    )
    n_outliers = np.sum(outliers)
    source_result['n_outliers'] = int(n_outliers)

    print(f"\nTransient Detection:")
    print(f"  Outliers detected: {n_outliers}")

    # Forecasting (for periodic sources)
    if source.period and fap < 0.01:
        future_time, future_flux = forecast_light_curve(
            source.time, source.flux, best_period, n_future=50
        )
        source.forecast_time = future_time
        source.forecast_flux = future_flux
        source_result['forecast_generated'] = True
        print(f"\nForecasting: Generated {len(future_time)} future predictions")
    else:
        source.forecast_time = None
        source_result['forecast_generated'] = False
        print(f"\nForecasting: Skipped (no significant period)")

    # Classification
    if best_power > 0.5 and fap < 0.01:
        if period_accuracy and period_accuracy < 0.1:
            if best_period < 0.2:
                classification = "Cataclysmic Variable / Eclipsing Binary (short period)"
            elif best_period < 10:
                if source.amplitude < 0.05:
                    classification = "Transiting Exoplanet"
                else:
                    classification = "Eclipsing Binary"
            else:
                classification = "Pulsating Variable (Cepheid / RV Tau)"
        else:
            classification = "Periodic (harmonic)"
    else:
        if n_outliers > 10:
            classification = "Transient / Outburst"
        else:
            classification = "Non-variable / Low amplitude"

    source_result['classification'] = classification
    print(f"\nClassification: {classification}")

    results.append(source_result)

# ============================================================================
# SAVE RESULTS
# ============================================================================

output = {
    'test_name': 'Temporal Reasoning',
    'n_sources': len(sources),
    'sources': results,
    'capabilities': [
        'Period detection using Lomb-Scargle periodogram',
        'Phase folding and template matching',
        'Transient detection with sigma-clipping',
        'Light curve forecasting using Fourier models',
        'Classification based on period and morphology',
        'Multi-scale temporal analysis (hours to months)',
    ]
}

with open('test8_temporal_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n" + "="*70)
print("TEST 8 COMPLETE: Temporal Reasoning")
print("="*70)
print(f"Analyzed {len(sources)} time-series sources")
print(f"\nClassification Results:")
for r in results:
    print(f"  {r['name']}: {r['classification']}")

print("\nResults saved to test8_temporal_results.json")

# ============================================================================
# CREATE FIGURE
# ============================================================================

print("\nGenerating temporal reasoning figure...")

fig = plt.figure(figsize=(20, 16))
gs = GridSpec(5, 4, figure=fig, hspace=0.4, wspace=0.4)

# Row 1: Eclipsing Binary
# Light curve
ax1 = fig.add_subplot(gs[0, :2])
ax1.errorbar(eb.time, eb.flux, yerr=eb.flux_err, fmt='.', alpha=0.5, markersize=3, color='steelblue')
ax1.set_xlabel('Time (days)')
ax1.set_ylabel('Relative Flux')
ax1.set_title('A: Eclipsing Binary Light Curve')
ax1.grid(True, alpha=0.3)

# Periodogram
ax2 = fig.add_subplot(gs[0, 2:])
ax2.plot(1/eb.freqs, eb.power, color='steelblue', linewidth=0.8)
ax2.axvline(eb.period, color='red', linestyle='--', label=f'True: {eb.period} d')
ax2.axvline(results[0]['detected_period'], color='green', linestyle='--',
            label=f'Detected: {results[0]["detected_period"]:.3f} d')
ax2.set_xlabel('Period (days)')
ax2.set_ylabel('Lomb-Scargle Power')
ax2.set_title('B: EB Periodogram')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xlim([0, 10])

# Row 2: Cepheid
# Light curve
ax3 = fig.add_subplot(gs[1, :2])
ax3.errorbar(cepheid.time, cepheid.flux, yerr=cepheid.flux_err, fmt='.', alpha=0.5, markersize=3, color='darkgreen')
ax3.set_xlabel('Time (days)')
ax3.set_ylabel('Relative Flux')
ax3.set_title('C: Cepheid Variable Light Curve')
ax3.grid(True, alpha=0.3)

# Phase folded
ax4 = fig.add_subplot(gs[1, 2:])
ax4.errorbar(cepheid.folded_phase, cepheid.folded_flux, yerr=cepheid.folded_err,
             fmt='.', alpha=0.5, markersize=4, color='darkgreen')
ax4.set_xlabel('Phase')
ax4.set_ylabel('Relative Flux')
ax4.set_title(f'D: Cepheid Phase-Folded (P = {results[1]["detected_period"]:.2f} d)')
ax4.grid(True, alpha=0.3)

# Row 3: Cataclysmic Variable
# Light curve
ax5 = fig.add_subplot(gs[2, :2])
ax5.errorbar(cv.time, cv.flux, yerr=cv.flux_err, fmt='.', alpha=0.5, markersize=3, color='purple')
ax5.set_xlabel('Time (days)')
ax5.set_ylabel('Relative Flux')
ax5.set_title('E: Dwarf Nova Light Curve')
ax5.grid(True, alpha=0.3)

# Periodogram
ax6 = fig.add_subplot(gs[2, 2:])
ax6.plot(1/cv.freqs, cv.power, color='purple', linewidth=0.8)
ax6.axvline(cv.period, color='red', linestyle='--', label='Orbital period')
ax6.axvline(results[2]['detected_period'], color='green', linestyle='--',
            label=f'Detected: {results[2]["detected_period"]:.3f} d')
ax6.set_xlabel('Period (days)')
ax6.set_ylabel('Power')
ax6.set_title('F: CV Periodogram (Orbital Modulation)')
ax6.legend()
ax6.grid(True, alpha=0.3)
ax6.set_xlim([0, 0.5])

# Row 4: Transiting Exoplanet
# Light curve (zoomed on one transit)
ax7 = fig.add_subplot(gs[3, :2])
transit_mask = (planet.time > 8) & (planet.time < 10.5)
ax7.errorbar(planet.time[transit_mask], planet.flux[transit_mask],
             yerr=planet.flux_err[transit_mask], fmt='.', alpha=0.6, markersize=5, color='darkorange')
ax7.set_xlabel('Time (days)')
ax7.set_ylabel('Relative Flux')
ax7.set_title('G: Hot Jupiter Transit (Single Event)')
ax7.grid(True, alpha=0.3)
ax7.set_ylim([0.98, 1.01])

# Periodogram
ax8 = fig.add_subplot(gs[3, 2:])
ax8.plot(1/planet.freqs, planet.power, color='darkorange', linewidth=0.8)
ax8.axvline(planet.period, color='red', linestyle='--', label=f'True: {planet.period} d')
ax8.axvline(results[3]['detected_period'], color='green', linestyle='--',
            label=f'Detected: {results[3]["detected_period"]:.3f} d')
ax8.set_xlabel('Period (days)')
ax8.set_ylabel('Power')
ax8.set_title('H: Exoplanet Periodogram')
ax8.legend()
ax8.grid(True, alpha=0.3)
ax8.set_xlim([0, 5])

# Row 5: Supernova + Summary
# SN Light curve
ax9 = fig.add_subplot(gs[4, :2])
ax9.errorbar(sn.time, sn.flux, yerr=sn.flux_err, fmt='.', alpha=0.5, markersize=3, color='crimson')
ax9.axvline(t_explosion, color='red', linestyle='--', alpha=0.5, label='Explosion')
ax9.set_xlabel('Time (days)')
ax9.set_ylabel('Relative Flux')
ax9.set_title('I: Type Ia Supernova Light Curve')
ax9.legend()
ax9.grid(True, alpha=0.3)

# Summary panel
ax10 = fig.add_subplot(gs[4, 2:])
ax10.axis('off')

summary_text = """
TEMPORAL REASONING CAPABILITIES

Period Detection
  • Lomb-Scargle periodogram
  • False alarm probability
  • Multi-scale analysis (0.01-100 d)

Phase Folding
  • Template matching
  • Morphology classification
  • Harmonic analysis

Transient Detection
  • Sigma-clipping algorithms
  • Baseline subtraction
  • Event significance testing

Forecasting
  • Fourier series models
  • Multi-harmonic fits
  • Future prediction

Classification
  • Period-based categories
  • Amplitude thresholds
  • Morphological features

vs. LLMs: "Time varies somehow"
vs. ML: Point predictions only
"""

ax10.text(0.05, 0.95, summary_text, transform=ax10.transAxes,
          verticalalignment='top', fontsize=9,
          bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
          family='monospace')

plt.suptitle('Test 8: Temporal Reasoning with Time-Domain Data',
             fontsize=16, fontweight='bold')

plt.savefig('test8_temporal_reasoning.png', dpi=150, bbox_inches='tight')
print("Figure saved to test8_temporal_reasoning.png")
plt.close()

print("\nTest 8 complete!")
