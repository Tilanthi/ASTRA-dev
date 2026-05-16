// Athena++ Problem Generator for Critical Transition Zone Mapping (CTZM) Campaign
// Purpose: Model isothermal self-gravitating filament with longitudinal magnetic field
// Key feature: Fine HDF5 output (dt = 0.02 tJ) to capture transient beading in transition zone

#include <cmath>
#include <sstream>
#include <stdexcept>

#include "../athena.hpp"
#include "../athena_arrays.hpp"
#include "../coordinates/coordinates.hpp"
#include "../field/field.hpp"
#include "../hydro/hydro.hpp"
#include "../mesh/mesh.hpp"
#include "../parameter_input.hpp"

// External physics headers
#include "../gravity/gravity.hpp"
#include "../hydro/eos/eos.hpp"
#include "../utils/utils.hpp"

// ======================================================================
// CTZM-specific configuration
// ======================================================================

// Physical constants (CGS units, but normalized in simulation)
namespace CTZMConfig {
  // Filament parameters (will be overridden by input parameters)
  static Real f_ratio = 1.0;           // Mass-to-line-mass ratio (M_line/M_line_crit)
  static Real beta_thermal = 1.0;      // Plasma beta (thermal pressure / magnetic pressure)
  static Real mach_number = 1.0;       // Turbulent Mach number
  static int random_seed = 42;         // Random seed for turbulence

  // Domain parameters
  static constexpr Real Lx = 8.0;      // Longitudinal domain length (in units of lambda_J)
  static constexpr Real Ly = 2.0;      // Transverse domain size y
  static constexpr Real Lz = 2.0;      // Transverse domain size z

  // Filament profile parameters
  static constexpr Real W_core = 0.3;  // Core half-width (in units of lambda_J)
  static constexpr Real rho_0 = 1.0;   // Background density

  // Turbulence parameters
  static constexpr int n_modes = 8;    // Number of turbulent modes
  static constexpr Real perturb_scale = 1e-4;  // Base perturbation amplitude

  // Physical constants (normalized so that lambda_J = 1.0)
  // This requires: 4 * PI * G = 4 * PI^2, so G = PI
  static constexpr Real G_norm = M_PI;
}

// ======================================================================
// Helper functions
// ======================================================================

// Calculate critical line mass for isothermal filament
// M_line,crit = 2 * c_s^2 / G
static Real CriticalLineMass(Real cs) {
  return 2.0 * cs * cs / CTZMConfig::G_norm;
}

// Calculate Alfvén velocity from plasma beta
// beta = c_s^2 / v_A^2  =>  v_A = c_s / sqrt(beta)
static Real AlfvénVelocity(Real cs, Real beta) {
  return cs / std::sqrt(beta);
}

// Gaussian filament profile
// rho(r) = rho_c * exp(-r^2 / (2 * W_core^2))
static Real GaussianFilament(Real r, Real W_core, Real rho_c) {
  return rho_c * std::exp(-r * r / (2.0 * W_core * W_core));
}

// ======================================================================
// Mesh initialization
// ======================================================================

void Mesh::InitUserMeshData(ParameterInput *pin) {
  // Read CTZM-specific parameters from input file
  CTZMConfig::f_ratio = pin->GetOrAddReal("problem", "f_ratio", 1.0);
  CTZMConfig::beta_thermal = pin->GetOrAddReal("problem", "beta", 1.0);
  CTZMConfig::mach_number = pin->GetOrAddReal("problem", "mach", 1.0);
  CTZMConfig::random_seed = pin->GetOrAddInteger("problem", "seed", 42);

  // Enroll source term for self-gravity
  if (SELF_GRAVITY_ENABLED) {
    EnrollGravitySourceTerm();
  }

  // Output configuration info
  if (Globals::my_rank == 0) {
    std::cout << "==================================================" << std::endl;
    std::cout << "CTZM Campaign: Filament Simulation" << std::endl;
    std::cout << "==================================================" << std::endl;
    std::cout << "Line-mass ratio f = " << CTZMConfig::f_ratio << std::endl;
    std::cout << "Plasma beta = " << CTZMConfig::beta_thermal << std::endl;
    std::cout << "Mach number = " << CTZMConfig::mach_number << std::endl;
    std::cout << "Random seed = " << CTZMConfig::random_seed << std::endl;
    std::cout << "==================================================" << std::endl;
  }
}

// ======================================================================
// Problem generator
// ======================================================================

void Mesh::ProblemGenerator(ParameterInput *pin) {
  // Get physics constants
  const Real gamma_adi = pin->GetReal("hydro", "gamma");
  const Real iso_cs = pin->GetOrAddReal("hydro", "iso_sound_speed", 1.0);

  // Calculate filament properties from input parameters
  const Real M_line_crit = CriticalLineMass(iso_cs);
  const Real M_line_target = CTZMConfig::f_ratio * M_line_crit;

  // For Gaussian filament: M_line = pi * W_core^2 * rho_c
  // Solve for central density: rho_c = M_line / (pi * W_core^2)
  const Real rho_c = M_line_target / (M_PI * CTZMConfig::W_core * CTZMConfig::W_core);

  // Calculate magnetic field strength
  const Real v_A = AlfvénVelocity(iso_cs, CTZMConfig::beta_thermal);
  const Real B_0 = v_A * std::sqrt(CTZMConfig::rho_0);  // B = v_A * sqrt(rho) in normalized units

  // Initialize random seed for turbulence
  srand(CTZMConfig::random_seed);

  // Loop over MeshBlocks
  for (auto it = meshblock.pmb->begin(); it != meshblock.pmb->end(); ++it) {
    MeshBlock *pmb = &(*it);

    // Get coordinates
    Coordinates *pcoord = pmb->pcoord;

    // Initialize conserved variables
    for (int k = pmb->ks; k <= pmb->ke; ++k) {
      for (int j = pmb->js; j <= pmb->je; ++j) {
        for (int i = pmb->is; i <= pmb->ie; ++i) {
          // Get cell coordinates
          Real x1 = pcoord->x1v(i);
          Real x2 = pcoord->x2v(j);
          Real x3 = pcoord->x3v(k);

          // Calculate radial distance from filament axis
          Real r = std::sqrt(x2 * x2 + x3 * x3);

          // Base density from Gaussian filament profile
          Real rho = GaussianFilament(r, CTZMConfig::W_core, rho_c);

          // Add longitudinal turbulent perturbations
          // v_x_pert = sum_{modes} A_n * sin(2*pi*n*x/Lx + phi_n)
          Real delta_vx = 0.0;
          for (int m = 1; m <= CTZMConfig::n_modes; ++m) {
            Real k = 2.0 * M_PI * m / CTZMConfig::Lx;
            Real phi = 2.0 * M_PI * (rand() % 1000) / 1000.0;  // Random phase
            Real amplitude = CTZMConfig::mach_number * iso_cs * CTZMConfig::perturb_scale;
            delta_vx += amplitude * std::sin(k * x1 + phi);
          }

          // Add small density perturbations (correlated with velocity)
          Real delta_rho = 0.01 * rho * delta_vx / iso_cs;

          // Total density
          rho += delta_rho;

          // Pressure (isothermal EOS)
          Real P = rho * iso_cs * iso_cs;

          // Velocity (only longitudinal component with turbulence)
          Real vx = delta_vx;
          Real vy = 0.0;
          Real vz = 0.0;

          // Magnetic field (purely longitudinal: B = (B_0, 0, 0))
          Real B1 = B_0;
          Real B2 = 0.0;
          Real B3 = 0.0;

          // Set conserved variables in Hydro
          // density
          pmb->phydro->u(IDN, k, j, i) = rho;

          // momentum
          pmb->phydro->u(IM1, k, j, i) = rho * vx;
          pmb->phydro->u(IM2, k, j, i) = rho * vy;
          pmb->phydro->u(IM3, k, j, i) = rho * vz;

          // total energy (isothermal: no internal energy)
          pmb->phydro->u(IEN, k, j, i) = P + 0.5 * rho * (vx * vx + vy * vy + vz * vz);

          // Set magnetic field in FaceField
          if (MAGNETIC_FIELDS_ENABLED) {
            pmb->pfield->b.x1f(k, j, i) = B1;
            pmb->pfield->b.x2f(k, j, i) = B2;
            pmb->pfield->b.x3f(k, j, i) = B3;

            // Add magnetic energy to total energy
            Real B_mag_sq = B1 * B1 + B2 * B2 + B3 * B3;
            pmb->phydro->u(IEN, k, j, i) += 0.5 * B_mag_sq;
          }
        }
      }
    }

    // Initialize gravitational potential if needed
    if (SELF_GRAVITY_ENABLED) {
      // The FFT-based solver will handle this automatically
      // Just ensure the potential is zero-initialized
      for (int k = pmb->ks; k <= pmb->ke; ++k) {
        for (int j = pmb->js; j <= pmb->je; ++j) {
          for (int i = pmb->is; i <= pmb->ie; ++i) {
            pmb->pgrav->phi[k][j][i] = 0.0;
          }
        }
      }
    }
  }

  // Output initial conditions summary
  if (Globals::my_rank == 0) {
    std::cout << "Initial Conditions Summary:" << std::endl;
    std::cout << "  Central density rho_c = " << rho_c << std::endl;
    std::cout << "  Magnetic field B_0 = " << B_0 << std::endl;
    std::cout << "  Alfvén velocity v_A = " << v_A << std::endl;
    std::cout << "  Sound speed c_s = " << iso_cs << std::endl;
    std::cout << "  Target line mass = " << M_line_target << std::endl;
    std::cout << "  Critical line mass = " << M_line_crit << std::endl;
    std::cout << "  f ratio = " << CTZMConfig::f_ratio << std::endl;
  }
}

// ======================================================================
// Analysis functions for CTZM campaign
// ======================================================================

// User work function to detect fragmentation
// Called at each output to analyze whether longitudinal beading has developed
void Mesh::UserWorkInLoop(ParameterInput *pin) {
  // Only analyze on root process
  if (Globals::my_rank != 0) return;

  // Get current simulation time
  Real time = pmb->pmy_mesh->time;

  // Analyze every 0.1 tJ to detect fragmentation
  static Real last_analysis_time = -1.0;
  if (time - last_analysis_time < 0.1) return;
  last_analysis_time = time;

  // Log simulation progress
  std::cout << "CTZM Analysis: t = " << time << " tJ" << std::endl;

  // TODO: Add peak detection logic here if needed for runtime analysis
  // For now, we do post-processing on HDF5 outputs
}

// ======================================================================
// Boundary conditions
// ======================================================================

void Mesh::UserWorkAfterOutput(ParameterInput *pin, int output_count) {
  // This function is called after each output
  // Can be used for additional analysis or logging

  if (Globals::my_rank == 0) {
    std::cout << "Output " << output_count << " written at t = "
              << pmb->pmy_mesh->time << " tJ" << std::endl;
  }
}
