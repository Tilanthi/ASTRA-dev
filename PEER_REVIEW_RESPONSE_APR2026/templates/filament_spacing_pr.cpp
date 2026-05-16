# PROBLEM GENERATOR: Filament Spacing for Peer Review Campaign
# Athena++ problem generator for self-gravitating magnetized filaments
# Addresses peer review concerns T1-T10

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
  // Physical parameters
  Real f_line = 1.5;              // Line mass fraction
  Real rho0 = 1.5;               // Mean density
  Real rc = 0.3;                 // Core radius (in units of lambda_J)
  Real Bx0 = 0.0, By0 = 0.0, Bz0 = 0.0;  // Magnetic field components
  Real mach_number = 1.0;        // Mach number for turbulence
  int seed = 1;                   // Random seed
  Real turb_amplitude = 1.0e-4;   // Turbulence amplitude

  // Configuration flags
  std::string density_profile = "king";  // king or uniform
  std::string eos_type = "isothermal";   // isothermal or adiabatic
  std::string bfield_config = "longitudinal";  // longitudinal, perpendicular, or oblique
}

// ============================================================================
// Helper functions
// ============================================================================

Real gaussian_profile(Real x, Real y, Real z, Real rc) {
  Real r2 = x*x + y*y;
  return std::exp(-r2 / (2.0 * rc * rc));
}

Real king_profile(Real x, Real y, Real z, Real rc) {
  Real r2 = x*x + y*y;
  Real r = std::sqrt(r2);
  Real rt = std::sqrt(r2 + rc*rc);
  return std::pow(rt / (1.0 + rt), 2.0);
}

// ============================================================================
// Problem generator
// ============================================================================

void Mesh::UserWorkAfterLoop(ParameterInput *pin, int nstep) {
  // Nothing to do after each loop
}

void Mesh::InitUserMeshData(ParameterInput *pin) {
  // Read parameters from input file

  // Line mass fraction
  if (pin->DoesParameterExist("problem", "f")) {
    f_line = pin->GetReal("problem", "f");
  }

  // Mean density (for supercritical filaments, rho0 = f)
  rho0 = f_line;

  // Core radius
  if (pin->DoesParameterExist("problem", "rc")) {
    rc = pin->GetReal("problem", "rc");
  }

  // Magnetic field
  if (pin->DoesParameterExist("problem", "Bx0")) {
    Bx0 = pin->GetReal("problem", "Bx0");
  }
  if (pin->DoesParameterExist("problem", "By0")) {
    By0 = pin->GetReal("problem", "By0");
  }
  if (pin->DoesParameterExist("problem", "Bz0")) {
    Bz0 = pin->GetReal("problem", "Bz0");
  }

  // Turbulence parameters
  if (pin->DoesParameterExist("problem", "mach_number")) {
    mach_number = pin->GetReal("problem", "mach_number");
  }
  if (pin->DoesParameterExist("problem", "seed")) {
    seed = pin->GetInteger("problem", "seed");
  }
  if (pin->DoesParameterExist("problem", "turb_amplitude")) {
    turb_amplitude = pin->GetReal("problem", "turb_amplitude");
  }

  // Configuration flags
  if (pin->DoesParameterExist("problem", "density_profile")) {
    density_profile = pin->GetString("problem", "density_profile");
  }
  if (pin->DoesParameterExist("problem", "eos")) {
    eos_type = pin->GetString("problem", "eos");
  }
  if (pin->DoesParameterExist("problem", "bfield")) {
    bfield_config = pin->GetString("problem", "bfield");
  }

  // Initialize random number generator
  std::srand(seed);
}

void Mesh::InitUserMeshProperties(ParameterInput *pin) {
  // Nothing to do
}

void Fluid::InitFluid(ParameterInput *pin) {
  // Set up initial hydrostatic equilibrium for self-gravitating filament

  // Get coordinate system
  auto pcoord = pmy_block->pcoord;

  // Initialize density profile
  for (int k = pmy_block->ks; k <= pmy_block->ke; ++k) {
    for (int j = pmy_block->js; j <= pmy_block->je; ++j) {
      for (int i = pmy_block->is; i <= pmy_block->ie; ++i) {

        // Get coordinates
        Real x1 = pcoord->x1v(i);
        Real x2 = pcoord->x2v(j);
        Real x3 = pcoord->x3v(k);

        // Compute density profile
        Real rho;
        if (density_profile == "uniform") {
          rho = rho0;
        } else if (density_profile == "king") {
          rho = rho0 * king_profile(x1 - 4.0, x2, x3, rc);  // Center filament at x1=4
        } else {
          rho = rho0 * gaussian_profile(x1 - 4.0, x2, x3, rc);
        }

        // Set density
        fluid[IDN].density(IDN, k, j, i) = rho;

        // Zero velocity initially
        fluid[IVX].velocity(IDN, k, j, i) = 0.0;
        fluid[IVY].velocity(IDN, k, j, i) = 0.0;
        fluid[IVZ].velocity(IDN, k, j, i) = 0.0;

        // Add small turbulent perturbations along x1 (filament axis)
        // Use 8 Kolmogorov modes along x1
        for (int mode = 1; mode <= 8; ++mode) {
          Real k = 2.0 * 3.14159 * mode / 8.0;  // Wavenumber
          Real phase = 2.0 * 3.14159 * (std::rand() / (Real)RAND_MAX);
          Real amplitude = turb_amplitude * mach_number * std::exp(-(mode - 1) / 4.0);
          fluid[IVX].velocity(IDN, k, j, i) += amplitude * std::cos(k * (x1 - 4.0) + phase);
        }

        // Uniform pressure (isothermal)
        fluid[IPR].pressure(IDN, k, j, i) = rho;  // P = rho for isothermal (c_s = 1)
      }
    }
  }
}

void Field::InitField(ParameterInput *pin) {
  // Initialize uniform magnetic field

  for (int k = pmy_block->ks; k <= pmy_block->ke; ++k) {
    for (int j = pmy_block->js; j <= pmy_block->je; ++j) {
      for (int i = pmy_block->is; i <= pmy_block->ie; ++i) {
        bfield.x1f(k, j, i) = Bx0;
        bfield.x2f(k, j, i) = By0;
        bfield.x3f(k, j, i) = Bz0;
      }
    }
  }
}

void Gravity::InitGravity(ParameterInput *pin) {
  // Set mean density for FFT Poisson solver
  grav_mean_rho = rho0;

  // four_pi_G should be set in input file: 4*pi^2
  // This gives lambda_J = 1 in code units
}

void Mesh::UserWorkInLoop(ParameterInput *pin) {
  // Nothing to do during main loop
}

// History output for watchdog monitoring
void Mesh::UserWorkBeforeOutput(ParameterInput *pin, int nstep) {
  // Nothing special before output
}

// Output additional diagnostic information
void Fluid::UserWorkBeforeOutput(ParameterInput *pin, int nstep) {
  // Nothing special
}

// ============================================================================
// EOS modification for adiabatic case
// ============================================================================

// Note: For adiabatic simulations, gamma is set in the input file
// The problem generator doesn't need to modify EOS here
