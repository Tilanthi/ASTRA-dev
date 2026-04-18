// ============================================================
// Athena++ Problem Generator: Filament Spacing Campaign
//
// Key fix (v2): Added Mesh::InitUserMeshData() to call
//   SetFourPiG() — required for FFT self-gravity activation.
//   Athena++ does NOT auto-read four_pi_G from <gravity> block;
//   the pgen must call SetFourPiG() explicitly.
//
// Initial conditions:
//   - Uniform density slab (rho0 = 1)
//   - Isothermal MHD (cs = 1, code units)
//   - Magnetic field along x3-axis (filament axis)
//   - Sinusoidal density + velocity perturbation along x1
//
// Reference: Glenn J. White (Open University)
// ============================================================

#include "../athena.hpp"
#include "../athena_arrays.hpp"
#include "../parameter_input.hpp"
#include "../mesh/mesh.hpp"
#include "../hydro/hydro.hpp"
#include "../field/field.hpp"
#include "../coordinates/coordinates.hpp"
#include <cmath>

// ============================================================
// InitUserMeshData — REQUIRED for FFT self-gravity
// SetFourPiG() must be called here; Athena++ does not read
// four_pi_G from the <gravity> input block automatically.
// ============================================================
void Mesh::InitUserMeshData(ParameterInput *pin) {
    if (SELF_GRAVITY_ENABLED) {
        Real four_pi_G = pin->GetReal("problem", "four_pi_G");
        SetFourPiG(four_pi_G);
    }
    return;
}

// ============================================================
// Problem Generator
// ============================================================
void MeshBlock::ProblemGenerator(ParameterInput *pin) {
    // Read parameters from <problem> block
    Real mach_number  = pin->GetOrAddReal("problem", "mach_number",  3.0);
    Real plasma_beta  = pin->GetOrAddReal("problem", "plasma_beta",  1.0);
    Real wavelength   = pin->GetOrAddReal("problem", "wavelength",   4.443);
    Real perturb_ampl = pin->GetOrAddReal("problem", "perturb_ampl", 0.01);

    // Isothermal sound speed (from <hydro> block, default 1.0)
    Real cs = pin->GetOrAddReal("hydro", "iso_sound_speed", 1.0);

    // Uniform initial density (code units)
    Real rho0 = 1.0;

    // Magnetic field strength from plasma beta:
    //   beta = 2 * rho0 * cs^2 / B0^2  =>  B0 = cs * sqrt(2*rho0/beta)
    Real B0 = cs * std::sqrt(2.0 * rho0 / plasma_beta);

    // Perturbation wavenumber along x1 (the long axis)
    Real kx = 2.0 * M_PI / wavelength;

    // -------------------------------------------------------
    // Set conserved hydro variables
    // For isothermal MHD: IDN, IM1, IM2, IM3 (no energy)
    // -------------------------------------------------------
    for (int k = ks; k <= ke; ++k) {
        for (int j = js; j <= je; ++j) {
            for (int i = is; i <= ie; ++i) {
                Real x1 = pcoord->x1v(i);

                // Density: mean + sinusoidal perturbation
                Real rho = rho0 * (1.0 + perturb_ampl * std::cos(kx * x1));

                // Velocity: compressional mode along x1
                Real vx1 = mach_number * cs * perturb_ampl * std::sin(kx * x1);

                phydro->u(IDN, k, j, i) = rho;
                phydro->u(IM1, k, j, i) = rho * vx1;  // x1-momentum
                phydro->u(IM2, k, j, i) = 0.0;          // x2-momentum
                phydro->u(IM3, k, j, i) = 0.0;          // x3-momentum
                // Note: no IEN for isothermal EOS
            }
        }
    }

    // -------------------------------------------------------
    // Set face-centred magnetic field (if MHD enabled)
    // B0 along x3-axis (filament axis / out-of-perturbation-plane)
    // -------------------------------------------------------
    if (MAGNETIC_FIELDS_ENABLED) {
        // x1-face: B1 = 0
        for (int k = ks; k <= ke; ++k) {
            for (int j = js; j <= je; ++j) {
                for (int i = is; i <= ie + 1; ++i) {
                    pfield->b.x1f(k, j, i) = 0.0;
                }
            }
        }
        // x2-face: B2 = 0
        for (int k = ks; k <= ke; ++k) {
            for (int j = js; j <= je + 1; ++j) {
                for (int i = is; i <= ie; ++i) {
                    pfield->b.x2f(k, j, i) = 0.0;
                }
            }
        }
        // x3-face: B3 = B0 (uniform, along filament axis)
        for (int k = ks; k <= ke + 1; ++k) {
            for (int j = js; j <= je; ++j) {
                for (int i = is; i <= ie; ++i) {
                    pfield->b.x3f(k, j, i) = B0;
                }
            }
        }
        // Derive cell-centred B from face-centred values
        pfield->CalculateCellCenteredField(
            pfield->b, pfield->bcc, pcoord,
            is, ie, js, je, ks, ke);
    }
}
