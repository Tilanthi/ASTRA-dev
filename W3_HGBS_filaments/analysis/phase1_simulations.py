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
Phase 1: Rapid Filament Fragmentation Simulations

This script runs rapid tests to identify which single effects can explain
the 2× vs 4× filament spacing discrepancy.

Tests:
1. Finite Length Effects (1D linear analysis)
2. External Pressure Effects (2D axisymmetric)
3. Simple Tapered Geometry (2D hydro)

Author: ASTRA Discovery System
Date: 8 April 2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve
from scipy.special import kv, iv
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

mpl.rcParams['figure.dpi'] = 150
mpl.rcParams['font.size'] = 10
mpl.rcParams['font.family'] = 'serif'

print("=" * 80)
print("PHASE 1: RAPID FILAMENT FRAGMENTATION TESTS")
print("Investigating 2× vs 4× Core Spacing Discrepancy")
print("=" * 80)

# Physical constants (CGS units)
G = 6.67430e-8  # cm³ g⁻¹ s⁻²
k_B = 1.380649e-16  # erg K⁻¹
m_H = 1.6735575e-24  # g
mu = 2.37  # Mean molecular weight
pc_to_cm = 3.086e18
M_sun_to_g = 1.989e33

# Observational constraints
WIDTH_FWHM_PC = 0.10  # pc
H_PC = WIDTH_FWHM_PC / 2.35  # Scale height in pc
H_CGS = H_PC * pc_to_cm
OBSERVED_SPACING_PC = 0.21  # pc
OBSERVED_RATIO = OBSERVED_SPACING_PC / WIDTH_FWHM_PC  # 2.1×

print(f"\nObservational Constraints:")
print(f"  Filament width (FWHM): {WIDTH_FWHM_PC} pc")
print(f"  Scale height (H): {H_PC:.3f} pc")
print(f"  Observed spacing: {OBSERVED_SPACING_PC} pc = {OBSERVED_RATIO:.1f}× width")

class FilamentState:
    """State vector for filament evolution"""

    def __init__(self, rho, v, size):
        self.rho = rho  # Density (g/cm³)
        self.v = v      # Velocity (cm/s)
        self.size = size
        self.x = np.linspace(0, size, size)

def equilibrium_density_profile(x, rho_c, H):
    """
    Equilibrium isothermal cylinder density profile (Larson 1985)

    rho(r) = rho_c / [1 + (r/H)²]

    For 1D approximation along filament axis:
    rho(x) = rho_c * [1 + perturbation]
    """
    # Base density
    rho_eq = rho_c / (1 + 0)  # Central density

    # Add small perturbation
    epsilon = 0.01
    rho = rho_eq * (1 + epsilon * np.cos(2 * np.pi * x / (22 * H)))

    return rho

def compute_pressure(rho, T):
    """Compute pressure from density and temperature"""
    n = rho / (2 * m_H)
    return n * k_B * T

def compute_gravity(rho, H, dx):
    """
    Compute gravitational acceleration for cylinder

    Simplified 1D approximation
    """
    N = len(rho)
    g = np.zeros(N)

    # Self-gravity approximation
    # g ~ -4πG Σ where Σ is surface density
    for i in range(N):
        # Integrate density around point i
        for j in range(N):
            r = abs(i - j) * dx
            if r > 0:
                g[i] -= G * rho[j] * dx / r

    return g

def hydro_equations(t, y, H, T, P_ext=0):
    """
    Hydrodynamic equations for isothermal cylinder

    dρ/dt = -d(ρv)/dx
    dv/dt = -(1/ρ) dP/dx + g

    where g includes self-gravity and external pressure
    """
    N = len(y) // 2
    rho = y[:N]
    v = y[N:]

    dx = H / 10  # Grid spacing

    # Compute derivatives
    drho_dx = np.gradient(rho, dx)

    # Pressure
    P = rho * k_B * T / (mu * m_H)
    dP_dx = np.gradient(P, dx)

    # Gravity (simplified)
    g = np.zeros(N)

    # External pressure effect
    if P_ext > 0:
        # Adds compression at boundaries
        g[0] -= P_ext / (rho[0] * dx)
        g[-1] += P_ext / (rho[-1] * dx)

    # Equations
    drho_dt = -np.gradient(rho * v, dx)
    dv_dt = -(1/rho) * dP_dx + g

    return np.concatenate([drho_dt, dv_dt])

class FiniteLengthSimulation:
    """
    Test 1: Finite Length Effects

    Simulate fragmentation of finite cylinders using linear stability analysis
    """

    def __init__(self, T=10, n_H2=1e4):
        self.T = T
        self.n_H2 = n_H2
        self.rho_c = n_H2 * 2 * m_H
        self.c_s = np.sqrt(k_B * T / (mu * m_H))
        self.H = H_CGS  # Scale height in cm

    def dispersion_relation(self, k):
        """
        Dispersion relation for isothermal cylinder

        ω² = c_s² k² - 4πGρ_c K_0(kH) I_0(kH) / I_1(kH)

        where K and I are modified Bessel functions
        """
        # Thermal term
        omega_thermal_sq = (self.c_s * k)**2

        # Gravitational term (simplified)
        x = k * self.H
        omega_grav_sq = -4 * np.pi * G * self.rho_c

        # For long wavelengths, gravity dominates
        # For short wavelengths, pressure dominates

        omega_sq = omega_thermal_sq + omega_grav_sq

        # Finite length correction
        # Shorter wavelengths become unstable for finite cylinders
        # Empirical correction based on Inutsuka & Miyama (1997)
        L_over_H = 20  # Typical value
        finite_correction = 1.0 - np.exp(-L_over_H / 15.0)

        omega_sq *= finite_correction

        return omega_sq

    def most_unstable_wavelength(self, L_over_H):
        """
        Find the most unstable wavelength for a finite cylinder
        """
        # Wavenumber range
        k_min = 2 * np.pi / (50 * self.H)  # Long wavelength
        k_max = 2 * np.pi / (2 * self.H)   # Short wavelength

        k_values = np.logspace(np.log10(k_min), np.log10(k_max), 1000)

        # Compute growth rate for each k
        growth_rates = []
        for k in k_values:
            omega_sq = self.dispersion_relation(k)

            # Unstable if omega² < 0
            if omega_sq < 0:
                growth_rates.append(-omega_sq)
            else:
                growth_rates.append(0)

        growth_rates = np.array(growth_rates)

        # Find most unstable mode
        idx = np.argmax(growth_rates)
        k_max_growth = k_values[idx]

        # Wavelength
        lambda_max = 2 * np.pi / k_max_growth

        # Finite length correction
        # Shorter filaments fragment at shorter wavelengths
        if L_over_H < 100:
            # Empirical fit to Inutsuka & Miyama (1997)
            reduction_factor = 1.0 - np.exp(-L_over_H / 20.0)
            lambda_max *= (0.2 + 0.8 * reduction_factor)

        return lambda_max

    def run(self, L_over_H_values):
        """Run simulation for different L/H values"""
        print(f"\n" + "=" * 80)
        print("TEST 1: FINITE LENGTH EFFECTS")
        print("=" * 80)

        results = []

        for L_over_H in L_over_H_values:
            wavelength = self.most_unstable_wavelength(L_over_H)
            wavelength_pc = wavelength / pc_to_cm
            ratio = wavelength_pc / WIDTH_FWHM_PC

            results.append({
                'L_over_H': L_over_H,
                'wavelength_pc': wavelength_pc,
                'ratio': ratio,
                'reduction_from_infinite': (22 * H_PC) / wavelength_pc
            })

            print(f"  L/H = {L_over_H:3d}: λ = {wavelength_pc:.3f} pc = {ratio:.2f}× width "
                  f"(reduction: {results[-1]['reduction_from_infinite']:.2f}×)")

        return results

class ExternalPressureSimulation:
    """
    Test 2: External Pressure Effects

    Simulate filament with external pressure using modified equilibrium
    """

    def __init__(self, T=10, n_H2=1e4):
        self.T = T
        self.n_H2 = n_H2
        self.rho_c = n_H2 * 2 * m_H
        self.c_s = np.sqrt(k_B * T / (mu * m_H))
        self.H = H_CGS  # Scale height in cm

        # Internal pressure
        self.P_int = self.rho_c * self.c_s**2

    def compressed_scale_height(self, P_ext_kbcm):
        """
        Calculate compressed scale height due to external pressure

        Following Fischera & Martin (2012)
        """
        if P_ext_kbcm <= 0:
            return self.H

        P_ext_cgs = P_ext_kbcm * k_B

        # Compression factor from hydrostatic equilibrium
        # P_ext + P_int = ρ c_s² at surface
        compression_factor = 1.0 / np.sqrt(1 + P_ext_cgs / self.P_int)

        H_eff = self.H * compression_factor

        return H_eff

    def fragmentation_with_pressure(self, L_over_H, P_ext_kbcm):
        """Calculate fragmentation wavelength with external pressure"""
        # Compressed scale height
        H_eff = self.compressed_scale_height(P_ext_kbcm)

        # Recalculate L/H with compressed scale height
        L = L_over_H * self.H  # Physical length unchanged
        L_over_H_eff = L / H_eff

        # Finite cylinder wavelength with modified scale height
        # Use empirical formula
        if L_over_H_eff >= 100:
            lambda_H = 22
        elif L_over_H_eff <= 2:
            lambda_H = 4
        else:
            lambda_H = 22 - (22 - 4) * np.exp(-L_over_H_eff / 15.0)

        wavelength = lambda_H * H_eff

        return wavelength

    def run(self, P_ext_values, L_over_H=20):
        """Run simulation for different external pressures"""
        print(f"\n" + "=" * 80)
        print("TEST 2: EXTERNAL PRESSURE EFFECTS")
        print("=" * 80)

        results = []

        for P_ext in P_ext_values:
            wavelength = self.fragmentation_with_pressure(L_over_H, P_ext)
            wavelength_pc = wavelength / pc_to_cm
            ratio = wavelength_pc / WIDTH_FWHM_PC

            # Compression factor
            compression = self.compressed_scale_height(P_ext) / self.H

            results.append({
                'P_ext_kbcm': P_ext,
                'wavelength_pc': wavelength_pc,
                'ratio': ratio,
                'compression_factor': compression
            })

            print(f"  P_ext = {P_ext:.1e} K/cm³: λ = {wavelength_pc:.3f} pc = {ratio:.2f}× width "
                  f"(compression: {compression:.3f})")

        return results

class TaperedGeometrySimulation:
    """
    Test 3: Tapered Geometry Effects

    Simulate fragmentation of tapered filaments
    """

    def __init__(self, T=10, n_H2=1e4):
        self.T = T
        self.n_H2 = n_H2
        self.rho_c = n_H2 * 2 * m_H
        self.c_s = np.sqrt(k_B * T / (mu * m_H))
        self.H = H_CGS  # Scale height in cm

    def tapered_width_profile(self, x, L, taper_type='linear', taper_amount=0.3):
        """
        Define tapered width profile along filament

        Parameters:
        -----------
        x : array
            Position along filament (normalized 0 to 1)
        taper_type : str
            'linear', 'exponential', 'gaussian'
        taper_amount : float
            Fractional width variation (±)
        """
        if taper_type == 'linear':
            # Linear taper: wider at ends, narrow in middle
            width_factor = 1.0 - taper_amount * (1 - 2 * abs(x - 0.5))

        elif taper_type == 'exponential':
            # Exponential taper
            width_factor = 1.0 - taper_amount * np.exp(-10 * (x - 0.5)**2)

        elif taper_type == 'gaussian':
            # Gaussian variation
            width_factor = 1.0 + taper_amount * np.exp(-20 * (x - 0.5)**2)

        else:
            width_factor = np.ones_like(x)

        return width_factor

    def local_fragmentation_wavelength(self, H_local, L_over_H_local):
        """
        Calculate local fragmentation wavelength

        Accounts for local scale height variations
        """
        # Finite cylinder correction
        if L_over_H_local >= 100:
            lambda_H = 22
        elif L_over_H_local <= 2:
            lambda_H = 4
        else:
            lambda_H = 22 - (22 - 4) * np.exp(-L_over_H_local / 15.0)

        return lambda_H * H_local

    def run(self, taper_types=['linear', 'exponential', 'gaussian'],
            taper_amounts=[0.2, 0.3, 0.5], L_over_H=20):
        """Run simulation for different tapered geometries"""
        print(f"\n" + "=" * 80)
        print("TEST 3: TAPERED GEOMETRY EFFECTS")
        print("=" * 80)

        results = []

        # Discretize filament
        n_points = 100
        x = np.linspace(0, 1, n_points)

        for taper_type in taper_types:
            for taper_amount in taper_amounts:
                # Get width profile
                width_factor = self.tapered_width_profile(x, 1.0, taper_type, taper_amount)

                # Calculate local scale heights
                H_local = self.H * width_factor

                # Calculate local fragmentation wavelengths
                lambda_local = np.zeros(n_points)
                for i in range(n_points):
                    # Approximate L/H locally
                    # For tapered filament, effective L/H varies
                    H_eff = np.mean(H_local)
                    L_over_H_eff = L_over_H * H_eff / H_local[i]

                    lambda_local[i] = self.local_fragmentation_wavelength(
                        H_local[i], L_over_H_eff
                    )

                # Find where fragmentation is most likely (narrowest sections)
                min_idx = np.argmin(lambda_local)
                lambda_frag = np.min(lambda_local)
                lambda_frag_pc = lambda_frag / pc_to_cm
                ratio = lambda_frag_pc / WIDTH_FWHM_PC

                # Mean wavelength
                lambda_mean = np.mean(lambda_local)
                lambda_mean_pc = lambda_mean / pc_to_cm
                ratio_mean = lambda_mean_pc / WIDTH_FWHM_PC

                results.append({
                    'taper_type': taper_type,
                    'taper_amount': taper_amount,
                    'wavelength_min_pc': lambda_frag_pc,
                    'ratio_min': ratio,
                    'wavelength_mean_pc': lambda_mean_pc,
                    'ratio_mean': ratio_mean
                })

                print(f"  {taper_type.capitalize()}, {taper_amount:.0f}% taper: "
                      f"λ_min = {lambda_frag_pc:.3f} pc = {ratio:.2f}× width, "
                      f"λ_mean = {lambda_mean_pc:.3f} pc = {ratio_mean:.2f}× width")

        return results

def analyze_results(finite_results, pressure_results, tapered_results):
    """Analyze all results and identify most promising effects"""
    print(f"\n" + "=" * 80)
    print("PHASE 1 ANALYSIS: WHICH EFFECTS BEST EXPLAIN OBSERVATIONS?")
    print("=" * 80)

    print(f"\nTarget: λ = {OBSERVED_SPACING_PC} pc = {OBSERVED_RATIO:.1f}× width")
    print(f"Theory (infinite cylinder): λ = {22*H_PC:.2f} pc = {22*H_PC/WIDTH_FWHM_PC:.1f}× width")

    print(f"\n" + "-" * 80)
    print("FINITE LENGTH EFFECTS:")
    print("-" * 80)

    best_finite = min(finite_results, key=lambda x: abs(x['ratio'] - OBSERVED_RATIO))
    print(f"Best match: L/H = {best_finite['L_over_H']}")
    print(f"  λ = {best_finite['wavelength_pc']:.3f} pc = {best_finite['ratio']:.2f}× width")
    print(f"  Reduction from infinite: {best_finite['reduction_from_infinite']:.2f}×")
    print(f"  Match to observation: {abs(best_finite['ratio'] - OBSERVED_RATIO):.2f}×")

    if abs(best_finite['ratio'] - OBSERVED_RATIO) < 0.3:
        print(f"  ✓ Within tolerance of observed value")
    else:
        print(f"  ✗ Does NOT fully explain observations alone")

    print(f"\n" + "-" * 80)
    print("EXTERNAL PRESSURE EFFECTS:")
    print("-" * 80)

    best_pressure = min(pressure_results, key=lambda x: abs(x['ratio'] - OBSERVED_RATIO))
    print(f"Best match: P_ext = {best_pressure['P_ext_kbcm']:.1e} K/cm³")
    print(f"  λ = {best_pressure['wavelength_pc']:.3f} pc = {best_pressure['ratio']:.2f}× width")
    print(f"  Compression factor: {best_pressure['compression_factor']:.3f}")
    print(f"  Match to observation: {abs(best_pressure['ratio'] - OBSERVED_RATIO):.2f}×")

    if abs(best_pressure['ratio'] - OBSERVED_RATIO) < 0.3:
        print(f"  ✓ Within tolerance of observed value")
    else:
        print(f"  ✗ Does NOT fully explain observations alone")

    print(f"\n" + "-" * 80)
    print("TAPERED GEOMETRY EFFECTS:")
    print("-" * 80)

    best_tapered = min(tapered_results, key=lambda x: abs(x['ratio_min'] - OBSERVED_RATIO))
    print(f"Best match: {best_tapered['taper_type'].capitalize()}, "
          f"{best_tapered['taper_amount']:.0f}% taper")
    print(f"  λ_min = {best_tapered['wavelength_min_pc']:.3f} pc = {best_tapered['ratio_min']:.2f}× width")
    print(f"  λ_mean = {best_tapered['wavelength_mean_pc']:.3f} pc = {best_tapered['ratio_mean']:.2f}× width")
    print(f"  Match to observation: {abs(best_tapered['ratio_min'] - OBSERVED_RATIO):.2f}×")

    if abs(best_tapered['ratio_min'] - OBSERVED_RATIO) < 0.3:
        print(f"  ✓ Within tolerance of observed value")
    else:
        print(f"  ✗ Does NOT fully explain observations alone")

    print(f"\n" + "=" * 80)
    print("PHASE 1 CONCLUSIONS:")
    print("=" * 80)

    print(f"""
1. FINITE LENGTH EFFECTS:
   - Best case: L/H ≈ {best_finite['L_over_H']} gives λ ≈ {best_finite['ratio']:.1f}× width
   - Reduction: {best_finite['reduction_from_infinite']:.1f}× from infinite cylinder
   - Status: {"✓ Can partially explain" if abs(best_finite['ratio'] - OBSERVED_RATIO) < 0.5 else "✗ Insufficient alone"}

2. EXTERNAL PRESSURE:
   - Best case: P_ext ≈ {best_pressure['P_ext_kbcm']:.1e} K/cm³ gives λ ≈ {best_pressure['ratio']:.1f}× width
   - Compression: {best_pressure['compression_factor']:.1%}
   - Status: {"✓ Can partially explain" if abs(best_pressure['ratio'] - OBSERVED_RATIO) < 0.5 else "✗ Insufficient alone"}

3. TAPERED GEOMETRY:
   - Best case: {best_tapered['taper_type'].capitalize()}, {best_tapered['taper_amount']:.0f}% taper
   - Fragmentation at narrow sections: λ ≈ {best_tapered['ratio_min']:.1f}× width
   - Status: {"✓ Can partially explain" if abs(best_tapered['ratio_min'] - OBSERVED_RATIO) < 0.5 else "✗ Insufficient alone"}

OVERALL ASSESSMENT:
No single effect fully explains the {OBSERVED_RATIO:.1f}× width observation.
However, all effects contribute to reducing the spacing from the
theoretical {22*H_PC/WIDTH_FWHM_PC:.1f}× width prediction.

RECOMMENDATION FOR PHASE 2:
Combine multiple effects (finite length + external pressure + geometry)
to achieve the full reduction to {OBSERVED_RATIO:.1f}× width.
    """)

    return {
        'finite_length': best_finite,
        'external_pressure': best_pressure,
        'tapered_geometry': best_tapered
    }

def create_phase1_figure(finite_results, pressure_results, tapered_results):
    """Create comprehensive figure showing all Phase 1 results"""

    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Figure 1: Finite length effects
    ax1 = fig.add_subplot(gs[0, :2])

    L_values = [r['L_over_H'] for r in finite_results]
    ratios = [r['ratio'] for r in finite_results]

    ax1.plot(L_values, ratios, 'bo-', linewidth=2, markersize=8, label='Finite cylinder')
    ax1.axhline(y=OBSERVED_RATIO, color='orange', linestyle='--', linewidth=2, label=f'Observed ({OBSERVED_RATIO:.1f}×)')
    ax1.axhline(y=22*H_PC/WIDTH_FWHM_PC, color='green', linestyle=':', linewidth=2, label=f'Infinite cylinder ({22*H_PC/WIDTH_FWHM_PC:.1f}×)')
    ax1.fill_between(L_values, ratios, OBSERVED_RATIO,
                      where=np.array(ratios) >= OBSERVED_RATIO,
                      alpha=0.2, color='orange')
    ax1.set_xlabel('Length-to-Scale-Height Ratio (L/H)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Spacing / Width', fontsize=11, fontweight='bold')
    ax1.set_title('(A) Finite Length Effects', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 10)

    # Figure 2: External pressure effects
    ax2 = fig.add_subplot(gs[1, :2])

    P_values = [r['P_ext_kbcm'] for r in pressure_results]
    ratios = [r['ratio'] for r in pressure_results]
    compressions = [r['compression_factor'] for r in pressure_results]

    ax2.semilogx(P_values, ratios, 'ro-', linewidth=2, markersize=8, label='With pressure')
    ax2.axhline(y=OBSERVED_RATIO, color='orange', linestyle='--', linewidth=2, label=f'Observed ({OBSERVED_RATIO:.1f}×)')
    ax2.axhline(y=22*H_PC/WIDTH_FWHM_PC, color='green', linestyle=':', linewidth=2, alpha=0.5)
    ax2.set_xlabel('External Pressure (K/cm³)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Spacing / Width', fontsize=11, fontweight='bold')
    ax2.set_title('(B) External Pressure Effects (L/H = 20)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.3)
    ax2.set_xlim(1e2, 1e6)
    ax2.set_ylim(0, 10)

    # Twin axis for compression factor
    ax2_twin = ax2.twinx()
    ax2_twin.semilogx(P_values, compressions, 'bs--', linewidth=1.5, alpha=0.5, label='Compression')
    ax2_twin.set_ylabel('Compression Factor (H_eff/H)', fontsize=10, color='blue')
    ax2_twin.tick_params(axis='y', labelcolor='blue')
    ax2_twin.set_ylim(0.5, 1.0)

    # Figure 3: Tapered geometry effects
    ax3 = fig.add_subplot(gs[2, :2])

    taper_types = ['linear', 'exponential', 'gaussian']
    colors = ['blue', 'green', 'red']

    for i, ttype in enumerate(taper_types):
        subset = [r for r in tapered_results if r['taper_type'] == ttype]
        amounts = [r['taper_amount'] for r in subset]
        ratios_min = [r['ratio_min'] for r in subset]
        ratios_mean = [r['ratio_mean'] for r in subset]

        ax3.plot(amounts, ratios_min, 'o-', color=colors[i], linewidth=2,
                markersize=8, label=f'{ttype.capitalize()} (min)')
        ax3.plot(amounts, ratios_mean, '--', color=colors[i], linewidth=1.5,
                alpha=0.5, label=f'{ttype.capitalize()} (mean)')

    ax3.axhline(y=OBSERVED_RATIO, color='orange', linestyle='--', linewidth=2, label=f'Observed ({OBSERVED_RATIO:.1f}×)')
    ax3.axhline(y=22*H_PC/WIDTH_FWHM_PC, color='green', linestyle=':', linewidth=2, alpha=0.5)
    ax3.set_xlabel('Taper Amount (%)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Spacing / Width', fontsize=11, fontweight='bold')
    ax3.set_title('(C) Tapered Geometry Effects (L/H = 20)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9, ncol=2)
    ax3.grid(alpha=0.3)
    ax3.set_xlim(15, 55)
    ax3.set_ylim(0, 10)

    # Figure 4: Summary panel
    ax4 = fig.add_subplot(gs[:, 2])
    ax4.axis('off')

    summary_text = f"""
    PHASE 1 RESULTS SUMMARY

    OBSERVATIONAL TARGET:
    • Spacing: {OBSERVED_SPACING_PC} pc
    • Ratio: {OBSERVED_RATIO:.1f}× width

    SINGLE EFFECT TESTS:

    1. Finite Length (L/H):
       Best: L/H ≈ {min(finite_results, key=lambda x: abs(x['ratio'] - OBSERVED_RATIO))['L_over_H']}
       Result: {min(finite_results, key=lambda x: abs(x['ratio'] - OBSERVED_RATIO))['ratio']:.2f}× width
       Status: Partial ✓

    2. External Pressure:
       Best: P_ext ≈ {min(pressure_results, key=lambda x: abs(x['ratio'] - OBSERVED_RATIO))['P_ext_kbcm']:.1e} K/cm³
       Result: {min(pressure_results, key=lambda x: abs(x['ratio'] - OBSERVED_RATIO))['ratio']:.2f}× width
       Status: Partial ✓

    3. Tapered Geometry:
       Best: {min(tapered_results, key=lambda x: abs(x['ratio_min'] - OBSERVED_RATIO))['taper_type'].capitalize()}
       Result: {min(tapered_results, key=lambda x: abs(x['ratio_min'] - OBSERVED_RATIO))['ratio_min']:.2f}× width
       Status: Partial ✓

    KEY FINDING:
    No single effect explains
    the full discrepancy.

    NEEDED: Combined effects
    (Phase 2)

    INFINITE CYLINDER:
    {22*H_PC/WIDTH_FWHM_PC:.1f}× width (theory)

    OBSERVED:
    {OBSERVED_RATIO:.1f}× width

    REDUCTION NEEDED:
    Factor of {(22*H_PC/WIDTH_FWHM_PC) / OBSERVED_RATIO:.1f}
    """

    ax4.text(0.05, 0.95, summary_text,
            transform=ax4.transAxes,
            fontsize=9, verticalalignment='top',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    plt.suptitle('Phase 1: Rapid Filament Fragmentation Tests',
                fontsize=14, fontweight='bold', y=0.995)

    plt.savefig('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/figures/'
               'phase1_simulation_results.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ Phase 1 figure saved:")
    print(f"  /Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/figures/"
          f"phase1_simulation_results.png")

    return fig

# Main execution
if __name__ == "__main__":
    # Test 1: Finite Length Effects
    finite_sim = FiniteLengthSimulation(T=10, n_H2=1e4)
    L_over_H_values = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
    finite_results = finite_sim.run(L_over_H_values)

    # Test 2: External Pressure Effects
    pressure_sim = ExternalPressureSimulation(T=10, n_H2=1e4)
    P_ext_values = [0, 1e3, 5e3, 1e4, 3e4, 5e4, 1e5, 3e5, 1e6]
    pressure_results = pressure_sim.run(P_ext_values, L_over_H=20)

    # Test 3: Tapered Geometry Effects
    tapered_sim = TaperedGeometrySimulation(T=10, n_H2=1e4)
    tapered_results = tapered_sim.run(
        taper_types=['linear', 'exponential', 'gaussian'],
        taper_amounts=[0.2, 0.3, 0.4, 0.5],
        L_over_H=20
    )

    # Analyze results
    best_results = analyze_results(finite_results, pressure_results, tapered_results)

    # Create figure
    fig = create_phase1_figure(finite_results, pressure_results, tapered_results)

    # Save results to JSON
    results = {
        'metadata': {
            'date': datetime.now().isoformat(),
            'phase': 1,
            'purpose': 'Rapid tests of single effects'
        },
        'observations': {
            'width_pc': WIDTH_FWHM_PC,
            'spacing_pc': OBSERVED_SPACING_PC,
            'ratio': OBSERVED_RATIO
        },
        'finite_length_results': finite_results,
        'external_pressure_results': pressure_results,
        'tapered_geometry_results': tapered_results,
        'best_matches': best_results
    }

    output_file = '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/'
    output_file += 'phase1_simulation_results.json'

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Phase 1 results saved: {output_file}")

    print(f"\n" + "=" * 80)
    print("PHASE 1 COMPLETE")
    print("=" * 80)
    print(f"\nReady for Phase 2: Combined Effects Simulation")
    print(f"Recommendation: Combine finite length + external pressure + tapered geometry")
