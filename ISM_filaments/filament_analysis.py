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
Filament Width Analysis - Numerical Simulations
Investigating the characteristic width of interstellar filaments

Four competing mechanisms:
1. Turbulent dissipation / accretion-driven turbulence (sonic scale)
2. Ambipolar diffusion scale
3. Ion-neutral friction damping scale
4. Projection artefacts
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy.optimize import fsolve
from scipy.constants import k, m_p, sigma, hbar
import matplotlib
matplotlib.use('Agg')

# Physical constants (CGS units)
KB = 1.380649e-16  # Boltzmann constant [erg/K]
MP = 1.6726219e-24  # Proton mass [g]
G = 6.67430e-8      # Gravitational constant [cm^3/g/s^2]
PC = 3.086e18       # Parsec [cm]
MSUN = 1.989e33     # Solar mass [g]
YEAR = 3.156e7      # Year [s]

class FilamentPhysics:
    """Physics of interstellar filaments"""

    def __init__(self, T=10.0, n_H2=1e4, B=30.0):
        """
        Initialize filament parameters

        Parameters:
        T: Temperature [K]
        n_H2: Molecular hydrogen number density [cm^-3]
        B: Magnetic field strength [microG]
        """
        self.T = T
        self.n_H2 = n_H2
        self.B = B * 1e-6  # Convert to G

        # Derived quantities
        self.rho = n_H2 * 2.8 * MP  # Mass density [g/cm^3]
        self.cs = np.sqrt(KB * T / (2.33 * MP))  # Sound speed [cm/s]
        self.va = self.B / np.sqrt(4 * np.pi * self.rho)  # Alfvén speed [cm/s]

    def sonic_scale(self, mach=5.0, l_drive=10.0):
        """
        Calculate the sonic scale (turbulent dissipation scale)

        The sonic scale λ_sonic is where turbulent velocity equals sound speed
        v_turb(λ) = cs at λ = λ_sonic

        For Kolmogorov turbulence: v(l) ∝ l^(1/3)
        λ_sonic = l_drive * M^(-3/(1+2q)) where q is the power spectral index

        Parameters:
        mach: Mach number at driving scale
        l_drive: Driving scale [pc]

        Returns:
        Sonic scale [pc]
        """
        # For supersonic turbulence with Mach >> 1
        # λ_sonic ≈ l_drive * M^(-3) for Burgers turbulence
        # λ_sonic ≈ l_drive * M^(-3/(4/3)) = l_drive * M^(-9/4) for Kolmogorov

        # Using the relation from Padoan et al. (2006)
        # λ_sonic ≈ l_drive * (cs / v_drive)^3 = l_drive * M^(-3)
        l_sonic = l_drive * mach**(-3)

        return l_sonic

    def turbulent_jeans_length(self):
        """
        Calculate the turbulent Jeans length

        λ_J,turb = cs,turb * sqrt(pi / (G * rho))
        where cs,turb includes turbulent pressure support

        Returns:
        Turbulent Jeans length [pc]
        """
        # Effective sound speed including turbulence
        # For M=5 turbulence, effective pressure increases by factor ~(1 + M^2)/3
        mach_eff = 3.0  # Typical internal Mach number in filaments
        cs_eff = self.cs * np.sqrt(1 + mach_eff**2)

        lambda_j = cs_eff * np.sqrt(np.pi / (G * self.rho))

        return lambda_j / PC

    def ambipolar_diffusion_scale(self, ionization_fraction=1e-6):
        """
        Calculate the ambipolar diffusion scale

        In weakly ionized gas, magnetic fluctuations decay at scales where
        the ion-neutral coupling becomes ineffective

        L_AD ≈ v_A * t_ni where t_ni is the neutral-ion collision time

        Returns:
        Ambipolar diffusion scale [pc]
        """
        # Ion-neutral coupling time
        # t_ni = 1/(γ ρ_i) where γ is the drag coefficient

        # Drag coefficient (approximately)
        gamma_ni = 3.5e-13  # [cm^3/s] for H-H+ collisions

        # Ion density
        n_i = self.n_H2 * ionization_fraction
        rho_i = n_i * 30 * MP  # Ion mass (assume heavier species)

        # Coupling time
        t_ni = 1.0 / (gamma_ni * rho_i)

        # Ambipolar diffusion scale
        l_ad = self.va * t_ni

        return l_ad / PC

    def ion_neutral_damping_scale(self):
        """
        Calculate the MHD wave damping scale from ion-neutral friction

        Damping occurs where wave frequency ~ ion-neutral collision rate

        Returns:
        Damping scale [pc]
        """
        # Ion-neutral collision frequency
        gamma_ni = 3.5e-13  # [cm^3/s]
        n_i = self.n_H2 * 1e-6  # Ion density

        nu_in = gamma_ni * n_i  # [s^-1]

        # For Alfvén waves: damping when ω ~ ν_in
        # k_max ~ ν_in / v_A
        k_max = nu_in / self.va
        l_min = 2 * np.pi / k_max

        return l_min / PC

    def thermal_jeans_length(self):
        """
        Calculate the thermal Jeans length

        Returns:
        Thermal Jeans length [pc]
        """
        lambda_j = self.cs * np.sqrt(np.pi / (G * self.rho))
        return lambda_j / PC

    def critical_mass_per_length(self):
        """
        Calculate the critical mass per unit length

        For an isothermal cylinder: M_line,crit = 2 cs^2 / G

        Returns:
        Critical mass per unit length [M_sun/pc]
        """
        m_line_crit = 2 * self.cs**2 / G  # [g/cm]
        return m_line_crit * PC / MSUN

    def ohc_parameter(self):
        """
        Calculate the Ostriker (1964) characteristic length scale

        λ_OHC ≈ H * sqrt(2) where H is the scale height

        Returns:
        OHC scale [pc]
        """
        # For an isothermal cylinder in hydrostatic equilibrium
        # The radial scale height is H = cs^2 / (π G ρ_central)
        # But this depends on central density

        # Using the relation: λ_width ≈ σ / sqrt(π G ρ)
        # where σ is the velocity dispersion
        lambda_width = self.cs / np.sqrt(np.pi * G * self.rho)

        return lambda_width / PC

def run_parameter_sweep():
    """Run simulations across parameter space"""

    print("="*70)
    print("FILAMENT WIDTH ANALYSIS - PARAMETER SWEEP")
    print("="*70)

    # Parameter ranges
    temperatures = np.array([8, 10, 12, 15, 20])  # K
    densities = np.array([1e3, 5e3, 1e4, 5e4, 1e5])  # cm^-3
    magnetic_fields = np.array([10, 30, 50, 100])  # microG

    results = {
        'T': [],
        'n': [],
        'B': [],
        'sonic_scale': [],
        'turbulent_jeans': [],
        'ambipolar_diff': [],
        'ion_neutral_damp': [],
        'thermal_jeans': [],
        'ohc_scale': []
    }

    print("\nRunning parameter sweep...")
    print(f"Grid: {len(temperatures)} T × {len(densities)} n × {len(magnetic_fields)} B")
    print(f"Total: {len(temperatures) * len(densities) * len(magnetic_fields)} models\n")

    for T in temperatures:
        for n in densities:
            for B in magnetic_fields:
                fil = FilamentPhysics(T=T, n_H2=n, B=B)

                results['T'].append(T)
                results['n'].append(n)
                results['B'].append(B)
                results['sonic_scale'].append(fil.sonic_scale(mach=5.0, l_drive=10.0))
                results['turbulent_jeans'].append(fil.turbulent_jeans_length())
                results['ambipolar_diff'].append(fil.ambipolar_diffusion_scale())
                results['ion_neutral_damp'].append(fil.ion_neutral_damping_scale())
                results['thermal_jeans'].append(fil.thermal_jeans_length())
                results['ohc_scale'].append(fil.ohc_parameter())

    print("Parameter sweep complete!")
    return results

def analyze_results(results):
    """Analyze simulation results"""

    print("\n" + "="*70)
    print("ANALYSIS OF RESULTS")
    print("="*70)

    # Convert to arrays
    sonic = np.array(results['sonic_scale'])
    turb_jeans = np.array(results['turbulent_jeans'])
    ambipolar = np.array(results['ambipolar_diff'])
    damping = np.array(results['ion_neutral_damp'])
    thermal = np.array(results['thermal_jeans'])
    ohc = np.array(results['ohc_scale'])

    print(f"\nCharacteristic scales across parameter space:")
    print(f"  Sonic scale (turbulence):      {np.mean(sonic):.3f} ± {np.std(sonic):.3f} pc")
    print(f"  Turbulent Jeans length:         {np.mean(turb_jeans):.3f} ± {np.std(turb_jeans):.3f} pc")
    print(f"  Ambipolar diffusion scale:      {np.mean(ambipolar):.3f} ± {np.std(ambipolar):.3f} pc")
    print(f"  Ion-neutral damping scale:      {np.mean(damping):.3f} ± {np.std(damping):.3f} pc")
    print(f"  Thermal Jeans length:           {np.mean(thermal):.3f} ± {np.std(thermal):.3f} pc")
    print(f"  OHC scale:                      {np.mean(ohc):.3f} ± {np.std(ohc):.3f} pc")

    print(f"\nComparison with observed value (~0.1 pc):")
    observed = 0.1

    mechanisms = {
        'Sonic scale': sonic,
        'Turbulent Jeans': turb_jeans,
        'Ambipolar diffusion': ambipolar,
        'Ion-neutral damping': damping,
        'Thermal Jeans': thermal,
        'OHC scale': ohc
    }

    print(f"\n{'Mechanism':<25} {'Mean [pc]':<12} {'Δ from obs':<15} {'Variance'}")
    print("-"*70)

    for name, values in mechanisms.items():
        mean_val = np.mean(values)
        delta = abs(mean_val - observed) / observed * 100
        var = np.std(values) / np.mean(values) * 100
        indicator = "✓" if 0.05 < mean_val < 0.2 else "✗"
        print(f"{name:<25} {mean_val:<12.4f} {delta:<15.1f}% {var:.1f}% {indicator}")

    # Calculate which mechanism best matches observations
    print(f"\nMECHANISM RANKING (closeness to 0.1 pc):")
    rankings = sorted(mechanisms.items(),
                     key=lambda x: abs(np.mean(x[1]) - observed))

    for i, (name, values) in enumerate(rankings, 1):
        diff = abs(np.mean(values) - observed)
        var = np.std(values) / np.mean(values) * 100
        print(f"  {i}. {name:<25} Δ={diff:.4f} pc, scatter={var:.1f}%")

    return results, mechanisms

def create_filament_profile_figure(results, mechanisms):
    """Create figure comparing filament profiles from different mechanisms"""

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Filament Width Predictions Across Parameter Space',
                 fontsize=14, fontweight='bold')

    # Extract unique values for plotting
    temps = np.unique(results['T'])
    densities = np.unique(results['n'])

    # Plot 1: Temperature dependence
    ax = axes[0, 0]
    for T in temps:
        mask = np.array(results['T']) == T
        n_vals = np.array(results['n'])[mask]
        sonic = np.array(results['sonic_scale'])[mask]

        # Group by density and average
        unique_n = np.unique(n_vals)
        mean_sonic = [np.mean(sonic[n_vals == n]) for n in unique_n]

        ax.plot(unique_n, mean_sonic, 'o-', label=f'T = {T} K', linewidth=2)

    ax.set_xscale('log')
    ax.set_xlabel('Density n$_{{H_2}}$ [cm$^{-3}$]', fontsize=11)
    ax.set_ylabel('Sonic Scale [pc]', fontsize=11)
    ax.set_title('Turbulent Dissipation Scale', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.1, color='r', linestyle='--', linewidth=2, label='Observed')

    # Plot 2: Density dependence of all mechanisms
    ax = axes[0, 1]
    colors = ['#00e5ff', '#ffab00', '#00e676', '#ff5252', '#7c4dff']

    for i, (name, values) in enumerate(mechanisms.items()):
        # Bin by density
        densities = np.array(results['n'])
        unique_n = np.unique(densities)

        # For each density, calculate mean scale
        mean_vals = []
        for n in unique_n:
            mask = densities == n
            mean_vals.append(np.mean(np.array(values)[mask]))

        ax.plot(unique_n, mean_vals, 'o-', color=colors[i % len(colors)],
                label=name, linewidth=2, markersize=6)

    ax.set_xscale('log')
    ax.set_xlabel('Density n$_{{H_2}}$ [cm$^{-3}$]', fontsize=11)
    ax.set_ylabel('Characteristic Scale [pc]', fontsize=11)
    ax.set_title('All Mechanisms', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.1, color='r', linestyle='--', linewidth=2)

    # Plot 3: Magnetic field dependence
    ax = axes[1, 0]
    for B in [10, 30, 50, 100]:
        mask = np.array(results['B']) == B
        n_vals = np.array(results['n'])[mask]
        ambipolar = np.array(results['ambipolar_diff'])[mask]

        unique_n = np.unique(n_vals)
        mean_ad = [np.mean(ambipolar[n_vals == n]) for n in unique_n]

        ax.plot(unique_n, mean_ad, 'o-', label=f'B = {B} μG', linewidth=2)

    ax.set_xscale('log')
    ax.set_xlabel('Density n$_{{H_2}}$ [cm$^{-3}$]', fontsize=11)
    ax.set_ylabel('Ambipolar Diffusion Scale [pc]', fontsize=11)
    ax.set_title('Magnetic Field Dependence', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.1, color='r', linestyle='--', linewidth=2)

    # Plot 4: Comparison with observations
    ax = axes[1, 1]

    mechanism_names = list(mechanisms.keys())
    mean_scales = [np.mean(v) for v in mechanisms.values()]
    std_scales = [np.std(v) for v in mechanisms.values()]

    x_pos = np.arange(len(mechanism_names))
    colors_bars = ['#00e5ff', '#ffab00', '#00e676', '#ff5252', '#7c4dff', '#ff9800']

    bars = ax.bar(x_pos, mean_scales, yerr=std_scales, color=colors_bars,
                  alpha=0.7, capsize=5, edgecolor='white', linewidth=1.5)

    ax.axhline(y=0.1, color='r', linestyle='--', linewidth=3, label='Observed')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([m.replace(' ', '\n') for m in mechanism_names],
                       rotation=0, ha='center', fontsize=8)
    ax.set_ylabel('Characteristic Scale [pc]', fontsize=11)
    ax.set_title('Comparison with Observations', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, max(mean_scales) * 1.3)

    plt.tight_layout()

    # Save high-resolution figure
    output_path = 'ISM_filaments/figures/filament_width_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nSaved: {output_path}")

    return output_path

def create_density_profile_figure():
    """Create figure showing filament density profiles for different mechanisms"""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Parameters for typical filament
    n_central = 1e5  # cm^-3
    width = 0.1  # pc
    width_cm = width * PC

    r = np.linspace(0, 0.5, 200) * PC  # cm

    # Plot 1: Different density profiles
    ax = axes[0]

    # Plummer-like profile (often used for filaments)
    # ρ(r) = ρ_c / [1 + (r/R_flat)^2]^(p/2)
    # where p is the power-law index at large radii

    rho_c = n_central * 2.8 * MP
    R_flat = width_cm / 2.4  # Flat radius related to FWHM

    profiles = {
        'Plummer (p=2)': 1.0 / (1 + (r/R_flat)**2),
        'Plummer (p=3)': 1.0 / (1 + (r/R_flat)**2)**1.5,
        'Plummer (p=4)': 1.0 / (1 + (r/R_flat)**2)**2,
        'Ostriker (cylinder)': np.exp(-0.5 * (r/R_flat)**2)
    }

    for name, profile in profiles.items():
        n_profile = n_central * profile
        ax.plot(r/PC, n_profile, linewidth=2.5, label=name, alpha=0.8)

    ax.set_xlabel('Radius [pc]', fontsize=12)
    ax.set_ylabel('Density n$_{{H_2}}$ [cm$^{-3}$]', fontsize=12)
    ax.set_title('Filament Density Profiles', fontsize=13, fontweight='bold')
    ax.set_yscale('log')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 0.3)

    # Plot 2: Column density map simulation
    ax = axes[1]

    # Create 2D column density map
    extent = 0.5  # pc
    nx, ny = 200, 200
    x = np.linspace(-extent, extent, nx)
    y = np.linspace(-extent, extent, ny)
    X, Y = np.meshgrid(x, y)

    # cylindrical radius
    R = np.sqrt(X**2 + Y**2)

    # Column density for Plummer profile
    sigma_c = n_central * R_flat * 2.8 * MP / MSUN * PC  # M_sun/pc^2
    N_2D = sigma_c / np.sqrt(1 + (R*PC/(R_flat))**2)

    im = ax.imshow(N_2D, extent=[-extent, extent, -extent, extent],
                   origin='lower', cmap='magma', aspect='equal')

    # Add contour at FWHM
    ax.contour(X, Y, N_2D, levels=[N_2D.max()/2], colors='cyan',
               linewidths=2, linestyles='--')

    ax.set_xlabel('x [pc]', fontsize=12)
    ax.set_ylabel('y [pc]', fontsize=12)
    ax.set_title('Synthetic Column Density Map', fontsize=13, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Column Density [M$_\\odot$/pc$^2]', fontsize=11)

    # Add scale bar
    ax.plot([-0.4, -0.3], [-0.4, -0.4], 'w-', linewidth=3)
    ax.text(-0.35, -0.38, '0.1 pc', color='white', ha='center',
            fontsize=10, fontweight='bold')

    plt.tight_layout()

    output_path = 'ISM_filaments/figures/filament_profiles.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")

    return output_path

def create_imf_figure():
    """Create figure showing connection between filament width and IMF"""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Filament fragmentation
    ax = axes[0]

    # Simulate filament with periodic density perturbations
    L = 2.0  # pc, filament length
    n_points = 500
    x = np.linspace(0, L, n_points)

    # Background density
    n_0 = 1e4  # cm^-3

    # Add perturbations with wavelength ~ 4 × filament width
    wavelength = 4 * 0.1  # pc (typical fragmentation scale)
    perturbation = 0.3 * np.sin(2 * np.pi * x / wavelength)

    # Add random noise
    noise = 0.1 * np.random.randn(n_points)

    n_x = n_0 * (1 + perturbation + noise)

    ax.plot(x, n_x, color='#00e5ff', linewidth=1.5, alpha=0.7)
    ax.fill_between(x, n_0 * 0.5, n_x, color='#00e5ff', alpha=0.2)

    # Mark cores (local maxima above threshold)
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(n_x, height=n_0*1.2, distance=20)

    ax.plot(x[peaks], n_x[peaks], 'o', color='#ffab00', markersize=10,
            markeredgecolor='white', markeredgewidth=2, label='Pre-stellar cores')

    ax.set_xlabel('Position along filament [pc]', fontsize=12)
    ax.set_ylabel('Density n$_{{H_2}}$ [cm$^{-3}$]', fontsize=12)
    ax.set_title('Filament Fragmentation', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(n_0*0.5, n_0*2)

    # Annotate fragmentation scale
    ax.annotate('', xy=(0, n_0*1.8), xytext=(wavelength, n_0*1.8),
                arrowprops=dict(arrowstyle='<->', color='white', lw=2))
    ax.text(wavelength/2, n_0*1.85, f'λ ≈ {wavelength:.2f} pc\n(~4 × width)',
            color='white', ha='center', fontsize=10, fontweight='bold')

    # Plot 2: Connection to IMF
    ax = axes[1]

    # Theoretical core mass from Jeans fragmentation
    # M_core ≈ λ_J × M_line

    width_pc = 0.1
    T = 10  # K
    n = 1e4  # cm^-3
    cs = np.sqrt(KB * T / (2.33 * MP))
    rho = n * 2.8 * MP

    lambda_J = cs * np.sqrt(np.pi / (G * rho)) / PC
    M_line = 2 * cs**2 / G * PC / MSUN  # M_sun/pc
    M_core = lambda_J * M_line

    # Typical IMF (Chabrier 2003)
    m_imf = np.logspace(-2, 2, 1000)
    # Chabrier system IMF
    imf_chabrier = np.exp(-(np.log10(m_imf) - np.log10(0.08))**2 / (2 * 0.69**2))

    ax.plot(m_imf, imf_chabrier / imf_chabrier.max(),
            color='#ff5252', linewidth=2.5, label='Observed IMF (Chabrier 2003)')

    # Mark predicted core mass
    ax.axvline(M_core, color='#00e5ff', linestyle='--', linewidth=2.5,
               label=f'Predicted from width: {M_core:.2f} M$_\\odot$')
    ax.axvline(0.2, color='#ffab00', linestyle=':', linewidth=2.5,
               label='IMF peak: 0.2 M$_\\odot$')

    ax.fill_betweenx([0, 1.2], M_core*0.5, M_core*1.5,
                      color='#00e5ff', alpha=0.2, label='±50% range')

    ax.set_xscale('log')
    ax.set_xlabel('Stellar Mass [M$_\\odot$]', fontsize=12)
    ax.set_ylabel('Normalized PDF', fontsize=12)
    ax.set_title('Connection to Stellar IMF', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.1)

    plt.tight_layout()

    output_path = 'ISM_filaments/figures/imf_connection.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")

    return output_path

def create_magnetic_field_figure():
    """Create figure showing magnetic field effects"""

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Magnetic critical mass
    ax = axes[0]

    B_range = np.linspace(0, 100, 100)  # microG
    T = 10  # K
    n = 1e4  # cm^-3

    # Thermal critical mass
    cs = np.sqrt(KB * T / (2.33 * MP))
    M_thermal = 2 * cs**2 / G * PC / MSUN  # M_sun/pc

    # Magnetic critical mass
    # M_mag ≈ M_thermal × (1 + (B/B_0)^2)^(1/2)
    # where B_0 is the critical field

    rho = n * 2.8 * MP
    B_crit = np.sqrt(4 * np.pi * rho) * cs  # G

    M_mag = []
    for B in B_range:
        B_gauss = B * 1e-6
        ratio = B_gauss / B_crit
        M = M_thermal * np.sqrt(1 + ratio**2)
        M_mag.append(M)

    ax.plot(B_range, M_mag, color='#7c4dff', linewidth=3,
            label='M$_{line,crit}$')
    ax.axhline(M_thermal, color='#00e5ff', linestyle='--', linewidth=2,
               label=f'Thermal only: {M_thermal:.1f} M$_\\odot$/pc')

    # Shade regions
    ax.fill_between(B_range, 0, M_thermal,
                     where=np.array(B_range) < 30,
                     color='#00e676', alpha=0.3, label='Sub-critical')

    ax.set_xlabel('Magnetic Field Strength [μG]', fontsize=12)
    ax.set_ylabel('Critical Mass per Unit Length [M$_\\odot$/pc]', fontsize=12)
    ax.set_title('Magnetic Critical Mass', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Plot 2: Filament morphology with B-fields
    ax = axes[1]

    # Create synthetic observation
    extent = 1.0  # pc
    nx, ny = 150, 150
    x = np.linspace(-extent, extent, nx)
    y = np.linspace(-extent, extent, ny)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)

    # Column density
    R_flat = 0.04
    sigma_c = 50  # M_sun/pc^2
    N_2D = sigma_c / np.sqrt(1 + (R/R_flat)**2)

    im = ax.imshow(N_2D, extent=[-extent, extent, -extent, extent],
                   origin='lower', cmap='magma', aspect='equal', alpha=0.8)

    # Add magnetic field lines
    # Field lines follow the filament (parallel case)
    for y_line in np.linspace(-0.3, 0.3, 7):
        ax.plot([-0.8, 0.8], [y_line, y_line], 'c-',
                linewidth=1.5, alpha=0.7)

    # Add perpendicular field lines (perpendicular case)
    for x_line in np.linspace(-0.3, 0.3, 7):
        ax.plot([x_line, x_line], [-0.8, 0.8], 'r--',
                linewidth=1.5, alpha=0.5)

    ax.set_xlabel('x [pc]', fontsize=12)
    ax.set_ylabel('y [pc]', fontsize=12)
    ax.set_title('Magnetic Field Geometry', fontsize=13, fontweight='bold')

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='c', lw=2, label='B-field (parallel)'),
        Line2D([0], [0], color='r', lw=2, linestyle='--', label='B-field (perpendicular)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Column Density [M$_\\odot$/pc$^2]', fontsize=11)

    plt.tight_layout()

    output_path = 'ISM_filaments/figures/magnetic_effects.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")

    return output_path

def main():
    """Main analysis function"""

    print("\n" + "="*70)
    print("INTERSTELLAR FILAMENT WIDTH ANALYSIS")
    print("="*70)

    # Run parameter sweep
    results = run_parameter_sweep()

    # Analyze results
    results, mechanisms = analyze_results(results)

    # Create figures
    print("\n" + "="*70)
    print("GENERATING FIGURES")
    print("="*70)

    create_filament_profile_figure(results, mechanisms)
    create_density_profile_figure()
    create_imf_figure()
    create_magnetic_field_figure()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)

    # Save results to file
    import json
    with open('ISM_filaments/analysis/simulation_results.json', 'w') as f:
        # Convert numpy arrays to lists for JSON serialization
        results_serializable = {}
        for key, values in results.items():
            if isinstance(values, list):
                results_serializable[key] = [float(v) if not isinstance(v, str) else v for v in values]
            else:
                results_serializable[key] = values

        json.dump(results_serializable, f, indent=2)
    print("Results saved: ISM_filaments/analysis/simulation_results.json")

if __name__ == "__main__":
    main()
