// PROBLEM GENERATOR: King Profile IC for IC Sensitivity Test
// Athena++ problem generator for self-gravitating magnetized filaments
// Uses King profile density distribution: rho(x,y) = rho0 / [1 + (r/rc)^2]^2
//
// Parameter space: f = 1.0-1.3, beta = 0.3-1.0, M = 1.0-2.0
// Purpose: Test IC sensitivity in near-critical regime

#include "../athena.hpp"
#include "../mesh/mesh.hpp"
#include "../hydro/hydro.hpp"
#include "../field/field.hpp"
#include "../gravity/gravity.hpp"
#include "../coordinates/coordinates.hpp"
#include "../eos/eos.hpp"
#include "../utils/utils.hpp"

// ============================================================================
// Configuration: Read from input file
// ============================================================================

namespace {
  Real f_line = 1.5;              // Mass-to-line-mass ratio (f = M_line/M_line,crit)
  Real beta = 1.0;                // Plasma beta (ratio of thermal to magnetic pressure)
  Real mach_number = 1.0;         // Mach number for turbulence amplitude
  int seed = 1;                   // Random seed for perturbations
  Real turb_amplitude = 1.0e-4;   // Turbulence amplitude (fraction of cs)
  int turb_modes = 8;             // Number of Kolmogorov modes
  Real rc = 0.3;                  // Core radius (in units of lambda_J)
  Real rho0 = 1.5;                // Central density
}

// ============================================================================
// Helper functions: King profile density distribution
// ============================================================================

Real king_profile(Real x, Real y, Real rc) {
  Real r2 = x*x + y*y;
  Real rt = std::sqrt(r2 + rc*rc);
  return std::pow(rc / rt, 2.0);
}

// ============================================================================
// Problem generator initialization
// ============================================================================

void Mesh::InitUserMeshData(ParameterInput *pin) {
  // Read parameters from input file

  // Mass-to-line-mass ratio
  if (pin->DoesParameterExist("problem", "f")) {
    f_line = pin->GetReal("problem", "f");
  }

  // Plasma beta
  if (pin->DoesParameterExist("problem", "beta")) {
    beta = pin->GetReal("problem", "beta");
  }

  // Mach number
  if (pin->DoesParameterExist("problem", "mach")) {
    mach_number = pin->GetReal("problem", "mach");
  }

  // Random seed
  if (pin->DoesParameterExist("problem", "seed")) {
    seed = pin->GetInteger("problem", "seed");
  }

  // Turbulence amplitude
  if (pin->DoesParameterExist("problem", "turb_ampl")) {
    turb_amplitude = pin->GetReal("problem", "turb_ampl");
  }

  // Turbulence modes
  if (pin->DoesParameterExist("problem", "turb_modes")) {
    turb_modes = pin->GetInteger("problem", "turb_modes");
  }

  // Core radius
  if (pin->DoesParameterExist("problem", "rc")) {
    rc = pin->GetReal("problem", "rc");
  }

  // Central density (for near-critical filaments, rho0 ≈ f)
  rho0 = f_line;

  // Initialize random number generator
  std::srand(seed);
}

void Mesh::InitUserMeshProperties(ParameterInput *pin) {
  // Nothing to do
}

void Fluid::InitFluid(ParameterInput *pin) {
  // Initialize King profile filament with PRR perturbations

  auto pcoord = pmy_block->pcoord;

  // Sound speed (isothermal EOS with cs = 1.0)
  Real cs = 1.0;

  // Magnetic field strength from plasma beta
  // beta = P_thermal / P_magnetic = rho*cs^2 / (B^2 / 8pi)
  // B = sqrt(8*pi*rho*cs^2 / beta)
  Real Bz0 = std::sqrt(8.0 * M_PI * rho0 * cs * cs / beta);

  for (int k = pmy_block->ks; k <= pmy_block->ke; ++k) {
    for (int j = pmy_block->js; j <= pmy_block->je; ++j) {
      for (int i = pmy_block->is; i <= pmy_block->ie; ++i) {

        // Get coordinates (filament axis along x1)
        Real x1 = pcoord->x1v(i);
        Real x2 = pcoord->x2v(j);
        Real x3 = pcoord->x3v(k);

        // Compute King profile density
        Real rho = rho0 * king_profile(x2, x3, rc);

        // Set density
        fluid[IDN].density(IDN, k, j, i) = rho;

        // Zero velocity initially (turbulence added below)
        fluid[IVX].velocity(IDN, k, j, i) = 0.0;
        fluid[IVY].velocity(IDN, k, j, i) = 0.0;
        fluid[IVZ].velocity(IDN, k, j, i) = 0.0;

        // Add PRR turbulent perturbations along x1 (filament axis)
        // Kolmogorov spectrum with specified amplitude
        Real dvx = 0.0;
        for (int mode = 1; mode <= turb_modes; ++mode) {
          Real k_mode = 2.0 * M_PI * mode / 8.0;  // Domain length = 8
          Real amplitude = turb_amplitude * cs / std::pow(mode, 5.0/3.0);
          Real phase1 = 2.0 * M_PI * std::rand() / RAND_MAX;
          Real phase2 = 2.0 * M_PI * std::rand() / RAND_MAX;
          dvx += amplitude * std::cos(k_mode * x1 + phase1) * std::cos(phase2);
        }
        dvx *= mach_number;  // Scale by Mach number
        fluid[IVX].velocity(IDN, k, j, i) = dvx;

        // Set pressure (isothermal EOS with cs = 1.0)
        fluid[IPR].pressure(IDN, k, j, i) = rho * cs * cs;
      }
    }
  }
}

void Field::InitField(ParameterInput *pin) {
  // Initialize uniform magnetic field along filament axis (z-direction)

  auto pcoord = pmy_block->pcoord;

  // Sound speed (isothermal EOS with cs = 1.0)
  Real cs = 1.0;

  // Magnetic field strength from plasma beta
  Real Bz0 = std::sqrt(8.0 * M_PI * rho0 * cs * cs / beta);

  for (int k = pmy_block->ks; k <= pmy_block->ke; ++k) {
    for (int j = pmy_block->js; j <= pmy_block->je; ++j) {
      for (int i = pmy_block->is; i <= pmy_block->ie; ++i) {

        // Uniform Bz field
        b.x1f(k, j, i) = 0.0;
        b.x2f(k, j, i) = 0.0;
        b.x3f(k, j, i) = Bz0;
      }
    }
  }
}

void Mesh::UserWorkAfterLoop(ParameterInput *pin, int nstep) {
  // Nothing to do after each loop
}
