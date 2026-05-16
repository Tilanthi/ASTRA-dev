/*
 * Athena++ Problem Generator Template
 * Filament with Non-Ideal MHD (Ambipolar Diffusion)
 *
 * This is a template for modifying Athena++ to simulate filament
 * fragmentation with ambipolar diffusion enabled.
 *
 * To use this file:
 * 1. Copy to athena++/src/prob/filament_ambipolar.cpp
 * 2. Modify as needed for your specific setup
 * 3. Rebuild Athena++ with non-ideal MHD support
 */

//======================================================================================
// File Description
//======================================================================================
// This problem generator initializes a self-gravitating, magnetized filament
// with non-ideal MHD effects (ambipolar diffusion) enabled.
//
// Key modifications needed:
// 1. Enable NON_BAROTROPIC_EOS in configure
// 2. Enable MHD with ambipolar diffusion
// 3. Implement filament initial conditions
// 4. Add gravity source terms
// 5. Add turbulence driving (optional)

//======================================================================================
// Initial Condition Parameters (read from input file)
//======================================================================================

// Problem parameters (set in <problem> block of athena_pp.in)
// filament_line_mass: Line mass fraction f = M_line/M_line_crit
// filament_beta: Plasma beta = 8*pi*P_gas / P_mag
// filament_mach: Turbulent Mach number M = sigma_turb / c_s
// random_seed: Random seed for turbulence generation

// Derived parameters:
// Critical line mass: M_line_crit = 2*c_s^2 / G (in code units)
// Filament width: W = 0.3 * lambda_J
// Central density: rho_c = f * rho_crit

//======================================================================================
// Implementation Outline
//======================================================================================

/*
1. INCLUDE HEADERS
   - athena.hpp
   - mesh.hpp
   - hydro/hydro.hpp
   - field/field.hpp
   - gravity/gravity.hpp

2. DEFINE PROBLEM CLASS
   - Inherits from MeshBlock
   - Overrides ProblemGenerator()
   - Implements:

3. INITIALIZE DENSITY PROFILE
   - Gaussian or Ostriker cylinder profile
   - rho(r) = rho_c * exp(-r^2 / (2*W^2))
   - Normalize to desired line mass fraction

4. INITIALIZE MAGNETIC FIELD
   - Uniform longitudinal field B_0 along x-axis
   - B_0 = sqrt(8*pi*rho_0*c_s^2 / beta)

5. ADD TURBULENCE
   - Kolmogorov spectrum along filament axis
   - Only longitudinal velocity perturbations
   - Amplitude: delta_v = M * c_s * amplitude_factor

6. ENABLE AMBIPOLAR DIFFUSION
   - Set eta_A from input file
   - eta_A = Am * c_s * lambda_J / (2*pi)
   - Athena++ handles non-ideal MHD terms automatically

7. GRAVITY SOURCE TERMS
   - Self-gravity via FFT Poisson solver
   - four_pi_G = 39.47841760435743 (sets lambda_J = 1)

8. OUTPUT
   - HST files every 0.05 t_J
   - HDF5 snapshots at key timestamps
   - Track fragmentation via timestep watchdog
*/

//======================================================================================
// Template Code Structure
//======================================================================================

/*
// Pseudo-code for ProblemGenerator function:

void MeshBlock::ProblemGenerator(ParameterInput *pin) {
  // 1. Read problem parameters
  Real f = pin->GetReal("problem", "filament_line_mass");
  Real beta = pin->GetReal("problem", "filament_beta");
  Real mach = pin->GetReal("problem", "filament_mach");
  int seed = pin->GetInteger("problem", "random_seed");

  // 2. Calculate derived quantities
  Real W = 0.3;  // Filament core width in lambda_J units
  Real rho_c = f * 1.0;  // Central density (normalized)
  Real B0 = sqrt(8.0 * M_PI * rho_c / beta);

  // 3. Initialize density field
  for (int k=ks; k<=ke; ++k) {
    for (int j=js; j<=je; ++j) {
      for (int i=is; i<=ie; ++i) {
        Real x1 = pcoord->x1v(i);
        Real x2 = pcoord->x2v(j);
        Real x3 = pcoord->x3v(i);
        Real r = sqrt(x2*x2 + x3*x3);

        // Gaussian density profile
        phydro->u(IDN, k, j, i) = rho_c * exp(-r*r / (2.0*W*W));

        // Initial velocities (zero + turbulence)
        phydro->u(IM1, k, j, i) = 0.0;
        phydro->u(IM2, k, j, i) = 0.0;
        phydro->u(IM3, k, j, i) = 0.0;

        // Longitudinal magnetic field
        pfield->b.x1f(k, j, i) = B0;
        pfield->b.x2f(k, j, i) = 0.0;
        pfield->b.x3f(k, j, i) = 0.0;
      }
    }
  }

  // 4. Add turbulence (only longitudinal)
  // Use seeded random number generator with specified seed
  // Generate Kolmogorov spectrum modes
  // Apply to IM1 (x1-velocity) only

  // 5. Set ambipolar diffusion coefficient
  // This is read from input file: eta_A_0
  // Athena++ applies it automatically in MHD evolution

  return;
}
*/

//======================================================================================
// Notes on Non-Ideal MHD in Athena++
//======================================================================================

/*
1. AMBIPOLAR DIFFUSION COEFFICIENT
   - Set via: eta_A_0 in <mhd> block
   - Units: [length]^2 / [time]
   - Typical values: 0.001 - 0.1 in code units
   - Converts from Am using: eta_A = Am * c_s * L / (2*pi)

2. OHMIC RESISTIVITY (not used in this campaign)
   - Set via: eta_O_0
   - Can be set to 0.0 for pure ambipolar diffusion

3. HALL EFFECT (not used in this campaign)
   - Set via: eta_H_0
   - Can be set to 0.0 for pure ambipolar diffusion

4. STABILITY CONSIDERATIONS
   - Ambipolar diffusion adds stiff terms
   - May require reduced CFL number (0.3 instead of 0.4)
   - If simulations crash, try: cfl_number = 0.2

5. VERIFICATION
   - Test with Am = 0.0 (should recover ideal MHD results)
   - Compare to main campaign results at identical parameters
   - Verify that eta_A > 0 slows radial collapse

6. FRAGMENTATION DETECTION
   - Monitor timestep for rapid drops (dt < 1e-8)
   - This indicates radial collapse fragmentation
   - For longitudinal fragmentation, analyze HDF5 snapshots
*/

//======================================================================================
// Modifying Existing Problem Generator
//======================================================================================

/*
The easiest approach is to start from an existing problem generator:

1. Copy athena++/src/prob/fountain_ambipolar.cpp to filament_ambipolar.cpp

2. Modify the initial conditions to use cylindrical filament geometry
   instead of the fountain cloud geometry

3. Remove any source terms specific to the fountain problem

4. Add gravity (if not already present)

5. Test with Am = 0 to verify ideal MHD matches existing results

6. Then enable Am > 0 for non-ideal MHD runs

Key files to modify:
- src/prob/filament_ambipolar.cpp: Problem generator
- src/Makefile: Add new problem to build
- configure: Re-run after adding new problem
*/

//======================================================================================
// Example Input File
//======================================================================================

/*
<job>
problem_id = filament_ambipolar

<time>
tlim = 3.0              # Run time in code units (t_J)
nlim = 1000000          # Maximum timestep
dt_parabolic_reduce = 0.5

<mesh>
nx1 = 256
nx2 = 64
nx3 = 64
x1min = -4.0
x1max = 4.0
x2min = -1.0
x2max = 1.0
x3min = -1.0
x3max = 1.0

<hydro>
iso_sound_speed = 1.0

<mhd>
ambipolar_diffusion = true
eta_A_0 = 0.159        # Am = 1.0: 1.0 * 1.0 * 1.0 / (2*pi)
eta_O_0 = 0.0          # No Ohmic resistivity
eta_H_0 = 0.0          # No Hall effect

<gravity>
grav_field_type = fft
four_pi_G = 39.47841760435743

<problem>
filament_line_mass = 1.5    # f = 1.5 (supercritical)
filament_beta = 1.0          # Plasma beta = 1.0
filament_mach = 1.0          # Mach = 1.0
random_seed = 42

<output>
file_type = hst
dt = 0.05                  # Output every 0.05 t_J
variable = u, b1, b2, b3, rho
file_type = hdf5
variable = prim
dt = 0.05
include_ghost_zones = false

<time>
cfl_number = 0.35
*/

//======================================================================================
// END OF TEMPLATE
//======================================================================================

/*
For complete Athena++ documentation, see:
https://github.com/PrincetonUniversity/athena-public-version

For non-ideal MHD implementation details, see:
Bai, X.-N. 2014, ApJ, 789, 102 (Ambipolar Diffusion in Athena++)

Good luck with your simulations!
*/
