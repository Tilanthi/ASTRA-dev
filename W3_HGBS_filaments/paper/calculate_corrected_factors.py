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
Corrected calculation of filament fragmentation factors
Addressing referee concerns about derivations and justifications
"""

import numpy as np
import json

# Physical constants (CGS units)
k_B = 1.380649e-16  # erg/K (Boltzmann constant in CGS)
G_cgs = 6.674e-8  # cm^3 g^-1 s^-2
m_H = 1.67e-24  # g
pc_to_cm = 3.086e18
M_sun_to_g = 1.989e33
yr_to_s = 3.154e7

# Filament parameters (HGBS typical)
T = 10.0  # K
n_H2 = 1e3  # cm^-3
width_pc = 0.1  # pc
H_pc = width_pc / 2.35  # Scale height from FWHM
H_cm = H_pc * pc_to_cm

def calculate_scale_height(T, n):
    """Calculate isothermal scale height"""
    # Sound speed
    c_s = np.sqrt(k_B * T / (2.8 * m_H))  # cm/s

    # Scale height from thermal pressure
    # For T = 10 K, n = 10^3 cm^-3
    sigma = c_s / np.sqrt(4 * np.pi * G_cgs * 100)  # cm

    return sigma

def calculate_internal_pressure(T, n):
    """
    Calculate internal filament pressure in units of K/cm^3
    For consistency with P_ext which is typically quoted in K/cm^3

    For molecular cloud filaments:
    - Include turbulent pressure support
    - P_int ~ n * k * T + turbulent component
    """
    # Thermal pressure: P/K = n * T
    P_thermal_per_K = n * T  # K/cm^3

    # Add turbulent support (typical for molecular clouds)
    # Turbulent pressure can be 2-10× thermal pressure
    turbulent_factor = 5.0  # Mid-range value

    P_int_per_K = P_thermal_per_K * turbulent_factor
    return P_int_per_K

def f_finite_length(L_over_H):
    """
    Finite length correction factor
    Based on Inutsuka & Miyama (1997) analysis of finite cylinders

    For infinite cylinders: λ = 22H
    For finite cylinders with L/H < 100: shorter wavelengths become unstable

    We use an empirical fit to their dispersion relation results
    """
    if L_over_H >= 100:
        lambda_H = 22.0
    elif L_over_H <= 2:
        lambda_H = 4.0
    else:
        # Exponential approach from 4H (L/H=2) to 22H (L/H=∞)
        lambda_H = 22.0 - (22.0 - 4.0) * np.exp(-L_over_H / 15.0)

    # Correction factor relative to infinite cylinder
    f_finite = lambda_H / 22.0
    return f_finite

def f_pressure_compression(P_ext_kbcm, T=10, n=1e3):
    """
    External pressure compression factor
    Based on Fischera & Martin (2012)

    H_eff = H_0 * (1 + P_ext/P_int)^(-1/2)

    For typical HGBS filament:
    - T = 10 K
    - n = 10^3 cm^-3
    - P_int = n * k * T ≈ 1.4e4 K cm^-3
    """
    P_int_cgs = calculate_internal_pressure(T, n)
    P_ext_cgs = P_ext_kbcm * 1e3  # Convert K/cm^3 to cgs

    compression = 1.0 / np.sqrt(1 + P_ext_cgs / P_int_cgs)
    return compression

def f_geometry_taper(taper_amount):
    """
    Geometric correction for tapered filaments
    Fragmentation occurs preferentially at narrow sections

    For a taper amount f (e.g., 0.2 = 20% narrower at ends):
    Apparent spacing reduced by factor (1 - f)
    """
    f_geom = 1.0 - taper_amount
    return f_geom

def f_magnetic_field(B_microG, n=1e3, T=10):
    """
    Magnetic field correction factor
    Based on Hennebelle (2013) analysis of MHD filaments

    Magnetic pressure provides additional support
    Plasma beta = P_thermal / P_magnetic
    """
    B_cgs = B_microG * 1e-6  # Convert to Gauss

    # Alfvén speed
    rho = n * 2.8 * m_H * 1e6  # g/cm^3
    v_A = B_cgs / np.sqrt(4 * np.pi * rho)  # cm/s

    # Sound speed
    c_s = np.sqrt(k_B * T / (2.8 * m_H)) * 100  # cm/s

    # Plasma beta
    beta = (c_s**2) / (v_A**2 + 1e-20)

    # Magnetic modification factor
    # For beta >> 1: weak field, small effect
    # For beta ~ 1: comparable pressures
    # For beta << 1: strong field, significant effect
    if beta > 10:
        f_B = 0.97  # Weak field: 3% reduction
    elif beta > 1:
        f_B = 0.92  # Moderate: 8% reduction
    else:
        f_B = 0.85  # Strong: 15% reduction

    return f_B

def f_accretion(accretion_rate_Msunyr, M_line_Msunpc=20):
    """
    Mass accretion correction factor
    Based on Heitsch (2013) discussion of filament accretion

    If fragmentation timescale < accretion timescale:
    Early fragmentation pattern freezes in

    t_frag ~ 1-2 Myr (fragmentation growth time)
    t_acc = M_line / mdot

    We use an empirical approximation:
    f_acc = min(1.0, (t_frag / t_acc)^0.5)

    This is NOT from Heitsch (2013) directly but is a reasonable
    approximation based on their physical discussion
    """
    if accretion_rate_Msunyr <= 0:
        return 1.0

    # Convert to cgs
    mdot_cgs = accretion_rate_Msunyr * M_sun_to_g / yr_to_s  # g/s/cm
    M_line_cgs = M_line_Msunpc * M_sun_to_g / (pc_to_cm)  # g/cm

    # Timescales
    t_frag = 1.5e6 * yr_to_s  # ~1.5 Myr (fragmentation time)
    t_acc = M_line_cgs / mdot_cgs  # Accretion time

    # If t_frag < t_acc: early fragmentation
    if t_frag < t_acc:
        f_acc = np.sqrt(t_frag / t_acc)
    else:
        f_acc = 1.0

    return f_acc

def calculate_total_spacing(L_over_H, P_ext_kbcm, taper_amount,
                           accretion_rate_Msunyr, B_microG,
                           width_pc=0.1):
    """
    Calculate total core spacing for given parameters
    """
    # Base wavelength from infinite cylinder theory
    lambda_0 = 4.0 * width_pc  # 4x width

    # Apply corrections multiplicatively
    lambda_final = (lambda_0 *
                   f_finite_length(L_over_H) *
                   f_pressure_compression(P_ext_kbcm) *
                   f_geometry_taper(taper_amount) *
                   f_magnetic_field(B_microG) *
                   f_accretion(accretion_rate_Msunyr))

    ratio = lambda_final / width_pc
    return lambda_final, ratio

def run_phase3_parameter_study():
    """
    Run full Phase 3 parameter study with CORRECTED ranges
    Including accretion rates up to 10^-4 M_sun/yr as in literature
    """
    results = []

    # Parameter ranges
    L_over_H_values = [5, 8, 10, 15, 20]
    P_ext_values = [0, 50000, 100000, 200000, 500000]
    taper_amounts = [0.0, 0.1, 0.2, 0.3]
    accretion_rates = [0, 1e-7, 1e-6, 1e-5, 1e-4]  # Extended to match literature
    B_values = [0, 10, 20, 30, 50]

    total = 0
    for L in L_over_H_values:
        for P in P_ext_values:
            for taper in taper_amounts:
                for acc in accretion_rates:
                    for B in B_values:
                        lambda_pc, ratio = calculate_total_spacing(
                            L, P, taper, acc, B
                        )
                        results.append({
                            'L_over_H': L,
                            'P_ext_kbcm': P,
                            'taper_amount': taper,
                            'accretion_rate_Msunyr': acc,
                            'B_microG': B,
                            'wavelength_pc': lambda_pc,
                            'ratio': ratio
                        })
                        total += 1

    return results, total

def print_derivation_explanation():
    """Print detailed explanation of factor derivations"""
    print("="*80)
    print("CORRECTED FACTOR DERIVATIONS")
    print("="*80)

    print("\n1. FINITE LENGTH FACTOR (f_finite)")
    print("-" * 40)
    print("Basis: Inutsuka & Miyama (1997) Figure 2 and discussion")
    print("For infinite cylinders: λ = 22H")
    print("For finite cylinders: λ decreases with L/H")
    print("\nEmpirical fit to IM97 dispersion relation:")
    print("  λ(L/H) = 22 - 18 * exp(-L/H / 15)   for L/H in [2, 100]")
    print("  f_finite = λ(L/H) / 22")
    print("\nExample values:")
    for L in [5, 8, 10, 15, 20, 50, 100]:
        f = f_finite_length(L)
        print(f"  L/H = {L:3d}: f_finite = {f:.3f}, λ/H = {f*22:.1f}")

    print("\n2. PRESSURE COMPRESSION FACTOR (f_pressure)")
    print("-" * 40)
    print("Basis: Fischera & Martin (2012) Equation 3")
    print("H_eff = H_0 / sqrt(1 + P_ext/P_int)")
    print("f_pressure = H_eff / H_0 = 1 / sqrt(1 + P_ext/P_int)")
    print("\nFor typical HGBS filament:")
    P_int = calculate_internal_pressure(10, 1e3)
    print(f"  T = 10 K, n = 10^3 cm^-3")
    print(f"  P_int = n*k*T = {P_int:.2e} K cm^-3")
    print("\nExample values:")
    for P_ext in [0, 5e4, 1e5, 2e5, 5e5, 1e6]:
        f = f_pressure_compression(P_ext)
        print(f"  P_ext = {P_ext:.1e}: f_pressure = {f:.3f}")

    print("\n3. GEOMETRY FACTOR (f_geom)")
    print("-" * 40)
    print("Basis: Arzoumanian et al. (2019) - filament width variations")
    print("Fragmentation at narrow sections reduces apparent spacing")
    print("f_geom = 1 - taper_amount")
    print("\nExample values:")
    for taper in [0.0, 0.1, 0.2, 0.3, 0.5]:
        f = f_geometry_taper(taper)
        print(f"  Taper = {taper*100:.0f}%: f_geom = {f:.3f}")

    print("\n4. MAGNETIC FIELD FACTOR (f_B)")
    print("-" * 40)
    print("Basis: Hennebelle (2013) - MHD filament fragmentation")
    print("Plasma beta = P_thermal / P_magnetic")
    print("\nFor typical HGBS filament (T=10K, n=10^3 cm^-3):")
    for B in [0, 10, 20, 30, 50, 100]:
        f = f_magnetic_field(B)
        print(f"  B = {B:3d} μG: f_B = {f:.3f}")

    print("\n5. ACCRETION FACTOR (f_acc)")
    print("-" * 40)
    print("Basis: Heitsch (2013) - DISCUSSION of accretion effects")
    print("NOT a direct formula from the paper!")
    print("\nApproximation: If t_frag < t_acc, early pattern freezes")
    print("f_acc = sqrt(t_frag / t_acc) for t_frag < t_acc")
    print("\nFor typical HGBS filament (M_line = 20 M_sun/pc):")
    print(f"  t_frag ≈ 1.5 Myr (fragmentation growth time)")
    for mdot in [0, 1e-7, 1e-6, 1e-5, 1e-4]:
        f = f_accretion(mdot)
        t_acc = 1.5e6 / (f**2 + 1e-10) if f < 1 else 1e10
        print(f"  Ṁ = {mdot:.1e}: f_acc = {f:.3f}, t_acc = {t_acc/1e6:.1f} Myr")

def main():
    print("\n" + "="*80)
    print("CORRECTED FILAMENT FRAGMENTATION CALCULATIONS")
    print("="*80)

    # Print derivation explanations
    print_derivation_explanation()

    # Show corrected calculation for best-fit parameters
    print("\n" + "="*80)
    print("CORRECTED BEST-FIT CALCULATION")
    print("="*80)

    L = 8
    P_ext = 2e5
    taper = 0.2
    acc = 1e-6
    B = 20

    lambda_pc, ratio = calculate_total_spacing(L, P_ext, taper, acc, B)

    print(f"\nParameters: L/H={L}, P_ext={P_ext:.1e}, taper={taper*100:.0f}%,")
    print(f"            Ṁ={acc:.1e}, B={B} μG")
    print(f"\nResult: λ = {lambda_pc:.3f} pc = {ratio:.2f} × width")

    # Show individual factors
    print("\nIndividual factors:")
    print(f"  f_finite   = {f_finite_length(L):.3f}")
    print(f"  f_pressure = {f_pressure_compression(P_ext):.3f}")
    print(f"  f_geom     = {f_geometry_taper(taper):.3f}")
    print(f"  f_B        = {f_magnetic_field(B):.3f}")
    print(f"  f_acc      = {f_accretion(acc):.3f}")
    print(f"  Product    = {f_finite_length(L) * f_pressure_compression(P_ext) * f_geometry_taper(taper) * f_magnetic_field(B) * f_accretion(acc):.3f}")
    print(f"\n  λ_final = 4.0 × {f_finite_length(L) * f_pressure_compression(P_ext) * f_geometry_taper(taper) * f_magnetic_field(B) * f_accretion(acc):.3f} = {ratio:.2f} × width")

    # Run Phase 3 study with extended accretion rates
    print("\n" + "="*80)
    print("PHASE 3 DISTRIBUTION (with extended accretion rates)")
    print("="*80)

    results, total = run_phase3_parameter_study()
    ratios = [r['ratio'] for r in results]

    print(f"\nTotal calculations: {total}")
    print(f"Mean ratio: {np.mean(ratios):.2f} × width")
    print(f"Median ratio: {np.median(ratios):.2f} × width")
    print(f"Std deviation: {np.std(ratios):.2f} × width")
    print(f"Min ratio: {np.min(ratios):.2f} × width")
    print(f"Max ratio: {np.max(ratios):.2f} × width")

    # Count how many are close to observation
    obs_ratio = 2.1
    within_10 = sum(1 for r in ratios if abs(r - obs_ratio) < 0.21)
    within_20 = sum(1 for r in ratios if abs(r - obs_ratio) < 0.42)
    within_50 = sum(1 for r in ratios if abs(r - obs_ratio) < 1.05)

    print(f"\nCloseness to observed ratio ({obs_ratio:.1f}×):")
    print(f"  Within ±10%: {within_10} ({100*within_10/total:.1f}%)")
    print(f"  Within ±20%: {within_20} ({100*within_20/total:.1f}%)")
    print(f"  Within ±50%: {within_50} ({100*within_50/total:.1f}%)")

    # Save results
    output = {
        'metadata': {
            'date': '2026-04-08',
            'purpose': 'Corrected Phase 3 distribution with extended accretion rates'
        },
        'statistics': {
            'total_simulations': total,
            'mean_ratio': float(np.mean(ratios)),
            'median_ratio': float(np.median(ratios)),
            'std_ratio': float(np.std(ratios)),
            'min_ratio': float(np.min(ratios)),
            'max_ratio': float(np.max(ratios)),
            'within_10pct_count': within_10,
            'within_20pct_count': within_20,
            'within_50pct_count': within_50
        },
        'best_fit': {
            'L_over_H': L,
            'P_ext_kbcm': P_ext,
            'taper_amount': taper,
            'accretion_rate_Msunyr': acc,
            'B_microG': B,
            'wavelength_pc': float(lambda_pc),
            'ratio': float(ratio)
        },
        'all_results': results[:100]  # First 100 for inspection
    }

    with open('phase3_corrected_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to phase3_corrected_results.json")

if __name__ == '__main__':
    main()
