// filament_tgrad.cpp
// Referee B1: illustrative MHD filament with an imposed LONGITUDINAL temperature
// gradient of the observed (~12% in lambda_J) magnitude, to measure the actual
// shift in the fragmentation wavelength lambda/W (cf. the analytic +-0.3 estimate
// of Section 6.5, which uses lambda_J proportional to sqrt(T) at fixed density).
//
// Design:
//  - Adiabatic EOS with gamma ~ 1.0001 (quasi-isothermal): the local sound speed
//    cs_loc(x1) is imposed via the initial pressure P = rho * cs_loc^2.
//  - cs_loc^2(x1) = cs0^2 * [1 + A*sin(2*pi*(x1-x1min)/Lx1)], A = tgrad_amp.
//    Sinusoidal so the profile is periodic-BC compatible (no boundary jump) and
//    carries no NET pressure imbalance; warm half (sin>0) vs cool half (sin<0).
//  - Density profile is FIXED along x1 (Gaussian core, amplitude set by the GLOBAL
//    cs0), so lambda_J,loc ~ cs_loc/sqrt(G rho) ~ sqrt(1 + A sin) -> +-6% (fixed-rho
//    sqrt(T) scaling, matching Section 6.5).
//  - Broadband per-cell white-noise velocity seed (spatial-hash RNG) so each region
//    selects its LOCAL preferred wavelength rather than a global imposed mode.
#include <algorithm>
#include <cmath>
#include <random>
#include "../athena.hpp"
#include "../athena_arrays.hpp"
#include "../coordinates/coordinates.hpp"
#include "../eos/eos.hpp"
#include "../field/field.hpp"
#include "../hydro/hydro.hpp"
#include "../mesh/mesh.hpp"
#include "../parameter_input.hpp"

// spatial-hash white noise in [-1,1], reproducible & MPI-decorrelated
static inline Real HashNoise(int i1, int i2, int i3, unsigned int base) {
  unsigned int h = base;
  h ^= (unsigned int)(i1) * 73856093u;
  h ^= (unsigned int)(i2) * 19349663u;
  h ^= (unsigned int)(i3) * 83492791u;
  h ^= h >> 13; h *= 0x5bd1e995u; h ^= h >> 15;
  return 2.0 * (Real)(h & 0xFFFFFFu) / (Real)0xFFFFFF - 1.0;
}

void Mesh::InitUserMeshData(ParameterInput *pin) {
  if (SELF_GRAVITY_ENABLED) {
    Real four_pi_G = pin->GetOrAddReal("problem", "four_pi_G", 4.0 * M_PI * M_PI);
    SetFourPiG(four_pi_G);
  }
}

void MeshBlock::ProblemGenerator(ParameterInput *pin) {
  Real four_pi_G = pin->GetOrAddReal("problem", "four_pi_G", 4.0 * M_PI * M_PI);
  Real f_line    = pin->GetOrAddReal("problem", "f_line_mass", 1.1);
  Real beta      = pin->GetOrAddReal("problem", "plasma_beta", 1.0);
  Real mach      = pin->GetOrAddReal("problem", "mach_number", 1.0);
  Real W_core    = pin->GetOrAddReal("problem", "W_core", 0.3);
  Real perturb_a = pin->GetOrAddReal("problem", "perturb_ampl", 1.0e-3);
  int  seed      = pin->GetOrAddInteger("problem", "random_seed", 42);
  Real cs0       = pin->GetOrAddReal("hydro", "iso_sound_speed", 1.0);
  Real tgrad     = pin->GetOrAddReal("problem", "tgrad_amp", 0.125);
  std::string bgeom = pin->GetOrAddString("problem", "bfield_geometry", "longitudinal");
  Real gamma     = peos->GetGamma();

  Real rho_bg  = 1.0;
  Real G_code  = four_pi_G / (4.0 * M_PI);
  Real M_crit  = 2.0 * cs0 * cs0 / G_code;                 // global critical line mass
  Real rho_amp = f_line * M_crit / (2.0 * M_PI * W_core * W_core);
  Real B0      = (beta > 0.0) ? cs0 * std::sqrt(2.0 * rho_bg / beta) : 0.0;

  Real x1min = pmy_mesh->mesh_size.x1min;
  Real Lx1   = pmy_mesh->mesh_size.x1max - x1min;
  Real dx1   = pcoord->dx1v(is);
  Real dx2   = pcoord->dx2v(js);
  Real dx3   = pcoord->dx3v(ks);
  Real vamp  = mach * perturb_a * cs0;
  unsigned int base = (unsigned int)(seed) * 2654435761u + 12345u;

  for (int k = ks; k <= ke; ++k)
  for (int j = js; j <= je; ++j)
  for (int i = is; i <= ie; ++i) {
    Real x1 = pcoord->x1v(i);
    Real x2 = pcoord->x2v(j);
    Real x3 = pcoord->x3v(k);
    Real r2 = x2 * x2 + x3 * x3;
    Real rho = rho_bg + rho_amp * std::exp(-r2 / (2.0 * W_core * W_core));

    // local (imposed) temperature / sound speed
    Real cs2loc = cs0 * cs0 * (1.0 + tgrad * std::sin(2.0 * M_PI * (x1 - x1min) / Lx1));

    // global cell indices for reproducible white noise
    int i1 = (int)std::floor((x1 - x1min) / dx1 + 0.5);
    int i2 = (int)std::floor((x2 - pmy_mesh->mesh_size.x2min) / dx2 + 0.5);
    int i3 = (int)std::floor((x3 - pmy_mesh->mesh_size.x3min) / dx3 + 0.5);
    Real v1 = vamp * HashNoise(i1, i2, i3, base);

    phydro->u(IDN, k, j, i) = rho;
    phydro->u(IM1, k, j, i) = rho * v1;
    phydro->u(IM2, k, j, i) = 0.0;
    phydro->u(IM3, k, j, i) = 0.0;
    if (NON_BAROTROPIC_EOS) {
      Real pres = rho * cs2loc;                 // P = rho * cs_loc^2
      phydro->u(IEN, k, j, i) = pres / (gamma - 1.0) + 0.5 * rho * v1 * v1;
    }
  }

  if (MAGNETIC_FIELDS_ENABLED) {
    Real Bx1 = 0.0, Bx2 = 0.0, Bx3 = 0.0;
    if (bgeom == "perpendicular") Bx2 = B0; else Bx1 = B0;  // default longitudinal
    for (int k = ks; k <= ke; ++k)
    for (int j = js; j <= je; ++j)
    for (int i = is; i <= ie + 1; ++i) pfield->b.x1f(k, j, i) = Bx1;
    for (int k = ks; k <= ke; ++k)
    for (int j = js; j <= je + 1; ++j)
    for (int i = is; i <= ie; ++i) pfield->b.x2f(k, j, i) = Bx2;
    for (int k = ks; k <= ke + 1; ++k)
    for (int j = js; j <= je; ++j)
    for (int i = is; i <= ie; ++i) pfield->b.x3f(k, j, i) = Bx3;
    pfield->CalculateCellCenteredField(pfield->b, pfield->bcc, pcoord,
                                       is, ie, js, je, ks, ke);
    if (NON_BAROTROPIC_EOS) {
      for (int k = ks; k <= ke; ++k)
      for (int j = js; j <= je; ++j)
      for (int i = is; i <= ie; ++i)
        phydro->u(IEN, k, j, i) += 0.5 * (SQR(pfield->bcc(IB1, k, j, i))
                                        + SQR(pfield->bcc(IB2, k, j, i))
                                        + SQR(pfield->bcc(IB3, k, j, i)));
    }
  }
}
