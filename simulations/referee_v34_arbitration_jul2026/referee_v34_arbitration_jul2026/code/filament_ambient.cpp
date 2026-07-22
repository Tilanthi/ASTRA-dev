// ============================================================
// Athena++ Problem Generator: filament_ambient
// Referee-v34 boundary-condition arbitration campaigns (Jul 2026)
//
// Purpose: resolve the configuration dependence of the supercritical
// fragmentation result (paper Section 4.6.6 / referee major point 1) with a
// SINGLE binary in which the transverse boundary condition (user
// external-pressure, reflecting, or periodic) is selected purely from the
// input file, the transverse domain size is a free parameter (so the
// boundary can be moved away from the filament while the pressurized
// ambient medium inside the domain provides the confinement), and the
// initial radial profile can be either the paper's Gaussian or a
// scaled-Ostriker near-equilibrium profile (equilibration test).
//
// Profiles (profile parameter):
//   gaussian : rho(r) = rho_bg + rho_amp * exp(-r^2/(2 W_core^2))
//              rho_amp = f * M_crit / (2 pi W_core^2)      [paper standard]
//   ostriker : rho(r) = rho_bg + f * rho_c / (1 + (r/W_core)^2)^2
//              rho_c   = 2 cs^2 / (pi G W_core^2)
//              (exact unmagnetized hydrostatic equilibrium at f=1 in
//               isolation; radial force imbalance ~ (f-1), vs O(1) for the
//               Gaussian.  Both profiles carry filament line mass f*M_crit.)
//
// B-field geometries (bfield_geometry): longitudinal | perpendicular | oblique
//
// Boundary conditions: if <mesh> ix2_bc = user, the four transverse faces
// are enrolled with the external-pressure zero-gradient BCs (identical
// implementation to filament_rce.cpp; p_ext_ratio=0 -> standard outflow).
// If ix2_bc = reflecting or periodic, Athena++ built-ins are used and no
// user functions are enrolled.
//
// Author: ASTRA automated system (astra-pa) | Date: 2026-07-21
// ============================================================

#include "../athena.hpp"
#include "../athena_arrays.hpp"
#include "../parameter_input.hpp"
#include "../mesh/mesh.hpp"
#include "../hydro/hydro.hpp"
#include "../field/field.hpp"
#include "../coordinates/coordinates.hpp"
#include <cmath>
#include <random>
#include <vector>
#include <string>
#include <algorithm>

// ── Global external pressure ratio (shared across all BC functions) ──────────
static Real g_p_ext = 0.0;

void InnerX2_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b, Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh);
void OuterX2_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b, Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh);
void InnerX3_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b, Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh);
void OuterX3_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b, Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh);

// ── Mesh-level init ──────────────────────────────────────────────────────────
void Mesh::InitUserMeshData(ParameterInput *pin) {
    if (SELF_GRAVITY_ENABLED) {
        Real four_pi_G = pin->GetOrAddReal("problem", "four_pi_G",
                                           4.0 * M_PI * M_PI);
        SetFourPiG(four_pi_G);
    }
    g_p_ext = pin->GetOrAddReal("problem", "p_ext_ratio", 0.0);

    // Enroll external-pressure user BCs only when requested in <mesh>
    std::string bc2 = pin->GetOrAddString("mesh", "ix2_bc", "periodic");
    if (bc2 == "user") {
        EnrollUserBoundaryFunction(BoundaryFace::inner_x2, InnerX2_ExtPressure);
        EnrollUserBoundaryFunction(BoundaryFace::outer_x2, OuterX2_ExtPressure);
        EnrollUserBoundaryFunction(BoundaryFace::inner_x3, InnerX3_ExtPressure);
        EnrollUserBoundaryFunction(BoundaryFace::outer_x3, OuterX3_ExtPressure);
    }
}

// ── Problem generator ────────────────────────────────────────────────────────
void MeshBlock::ProblemGenerator(ParameterInput *pin) {

    Real four_pi_G  = pin->GetOrAddReal("problem", "four_pi_G",
                                        4.0 * M_PI * M_PI);
    Real f_line     = pin->GetOrAddReal("problem", "f_line_mass",  1.0);
    Real beta       = pin->GetOrAddReal("problem", "plasma_beta",  1.0);
    Real mach       = pin->GetOrAddReal("problem", "mach_number",  1.0);
    Real W_core     = pin->GetOrAddReal("problem", "W_core",       0.3);
    Real perturb_a  = pin->GetOrAddReal("problem", "perturb_ampl", 1.0e-4);
    int  seed       = pin->GetOrAddInteger("problem", "random_seed", 42);
    Real cs         = pin->GetOrAddReal("hydro", "iso_sound_speed", 1.0);
    Real theta_deg  = pin->GetOrAddReal("problem", "theta_deg",    0.0);
    std::string bgeom = pin->GetOrAddString("problem", "bfield_geometry",
                                             "longitudinal");
    std::string prof  = pin->GetOrAddString("problem", "profile", "gaussian");

    // ── Derived quantities ───────────────────────────────────────────────────
    Real rho_bg  = 1.0;
    Real G_code  = four_pi_G / (4.0 * M_PI);
    Real M_crit  = 2.0 * cs * cs / G_code;
    // Gaussian amplitude (paper standard): line mass f*M_crit
    Real rho_amp = f_line * M_crit / (2.0 * M_PI * W_core * W_core);
    // Ostriker central density: equilibrium value for core radius W_core
    Real rho_c_ost = 2.0 * cs * cs / (M_PI * G_code * W_core * W_core);
    Real B0      = (beta > 0.0) ? cs * std::sqrt(2.0 * rho_bg / beta) : 0.0;

    // ── Kolmogorov velocity perturbation along x1 (identical to
    //    filament_supercritical.cpp: 12 modes, k^-11/6 amplitudes) ────────────
    const int Nm = 12;
    Real Lx1 = pmy_mesh->mesh_size.x1max - pmy_mesh->mesh_size.x1min;

    std::vector<Real> kx_v(Nm), ph(Nm), amp_k(Nm);
    std::mt19937 rng(static_cast<unsigned int>(seed));
    std::uniform_real_distribution<Real> U_phase(0.0, 2.0 * M_PI);

    for (int n = 0; n < Nm; ++n) {
        kx_v[n]  = 2.0 * M_PI * (n + 1) / Lx1;
        ph[n]    = U_phase(rng);
        amp_k[n] = std::pow(kx_v[n], -11.0 / 6.0);
    }
    Real sumsq = 0.0;
    for (int n = 0; n < Nm; ++n)
        sumsq += 0.5 * amp_k[n] * amp_k[n];
    Real vtgt  = mach * perturb_a * cs;
    Real vnorm = (sumsq > 0.0) ? vtgt / std::sqrt(sumsq) : 0.0;

    // ── Fill conserved arrays ────────────────────────────────────────────────
    for (int k = ks; k <= ke; ++k)
    for (int j = js; j <= je; ++j)
    for (int i = is; i <= ie; ++i) {
        Real x1 = pcoord->x1v(i);
        Real x2 = pcoord->x2v(j);
        Real x3 = pcoord->x3v(k);

        Real r2  = x2 * x2 + x3 * x3;
        Real rho;
        if (prof == "ostriker") {
            Real q = 1.0 + r2 / (W_core * W_core);
            rho = rho_bg + f_line * rho_c_ost / (q * q);
        } else {  // gaussian (default)
            rho = rho_bg + rho_amp * std::exp(-r2 / (2.0 * W_core * W_core));
        }

        Real v1 = 0.0;
        for (int n = 0; n < Nm; ++n)
            v1 += vnorm * amp_k[n] * std::cos(kx_v[n] * x1 + ph[n]);

        phydro->u(IDN, k, j, i) = rho;
        phydro->u(IM1, k, j, i) = rho * v1;
        phydro->u(IM2, k, j, i) = 0.0;
        phydro->u(IM3, k, j, i) = 0.0;
    }

    // ── Magnetic field (uniform geometries) ──────────────────────────────────
    if (MAGNETIC_FIELDS_ENABLED) {
        Real Bx1 = 0.0, Bx2 = 0.0, Bx3 = 0.0;
        if (bgeom == "perpendicular") {
            Bx2 = B0;
        } else if (bgeom == "oblique") {
            Real theta_rad = theta_deg * M_PI / 180.0;
            Bx1 = B0 * std::cos(theta_rad);
            Bx2 = B0 * std::sin(theta_rad);
        } else {
            Bx1 = B0;  // longitudinal (default)
        }

        for (int k = ks; k <= ke; ++k)
        for (int j = js; j <= je; ++j)
        for (int i = is; i <= ie + 1; ++i)
            pfield->b.x1f(k, j, i) = Bx1;

        for (int k = ks; k <= ke; ++k)
        for (int j = js; j <= je + 1; ++j)
        for (int i = is; i <= ie; ++i)
            pfield->b.x2f(k, j, i) = Bx2;

        for (int k = ks; k <= ke + 1; ++k)
        for (int j = js; j <= je; ++j)
        for (int i = is; i <= ie; ++i)
            pfield->b.x3f(k, j, i) = Bx3;

        pfield->CalculateCellCenteredField(
            pfield->b, pfield->bcc, pcoord,
            is, ie, js, je, ks, ke);
    }
}
// ── inner_x2: ghost cells at j = js-1, js-2, ..., js-ngh ───────────────────
void InnerX2_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int k = ks; k <= ke; ++k) {
        for (int n = 1; n <= ngh; ++n) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, k, js-n, i) = std::max(prim(IDN, k, js, i), g_p_ext);
                prim(IVX, k, js-n, i) = prim(IVX, k, js, i);
                prim(IVY, k, js-n, i) = prim(IVY, k, js, i);
                prim(IVZ, k, js-n, i) = prim(IVZ, k, js, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f: face-centered in x1 (i has extra +1 face)
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(k, js-n, i) = b.x1f(k, js, i);

        // x2f: face-centered in x2; ghost faces at js-n (boundary face = js)
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x2f(k, js-n, i) = b.x2f(k, js, i);

        // x3f: face-centered in x3 (k has extra +1 face)
        for (int k = ks; k <= ke + 1; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x3f(k, js-n, i) = b.x3f(k, js, i);
    }
}

// ── outer_x2: ghost cells at j = je+1, je+2, ..., je+ngh ───────────────────
void OuterX2_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int k = ks; k <= ke; ++k) {
        for (int n = 1; n <= ngh; ++n) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, k, je+n, i) = std::max(prim(IDN, k, je, i), g_p_ext);
                prim(IVX, k, je+n, i) = prim(IVX, k, je, i);
                prim(IVY, k, je+n, i) = prim(IVY, k, je, i);
                prim(IVZ, k, je+n, i) = prim(IVZ, k, je, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(k, je+n, i) = b.x1f(k, je, i);

        // x2f: last active face = je+1; ghost faces at je+1+n
        for (int k = ks; k <= ke; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x2f(k, je+1+n, i) = b.x2f(k, je+1, i);

        // x3f
        for (int k = ks; k <= ke + 1; ++k)
            for (int n = 1; n <= ngh; ++n)
                for (int i = is; i <= ie; ++i)
                    b.x3f(k, je+n, i) = b.x3f(k, je, i);
    }
}

// ── inner_x3: ghost cells at k = ks-1, ks-2, ..., ks-ngh ───────────────────
void InnerX3_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int n = 1; n <= ngh; ++n) {
        for (int j = js; j <= je; ++j) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, ks-n, j, i) = std::max(prim(IDN, ks, j, i), g_p_ext);
                prim(IVX, ks-n, j, i) = prim(IVX, ks, j, i);
                prim(IVY, ks-n, j, i) = prim(IVY, ks, j, i);
                prim(IVZ, ks-n, j, i) = prim(IVZ, ks, j, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(ks-n, j, i) = b.x1f(ks, j, i);

        // x2f: face-centered in x2 (j has extra +1 face)
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je + 1; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x2f(ks-n, j, i) = b.x2f(ks, j, i);

        // x3f: ghost faces at ks-n (boundary face = ks)
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x3f(ks-n, j, i) = b.x3f(ks, j, i);
    }
}

// ── outer_x3: ghost cells at k = ke+1, ke+2, ..., ke+ngh ───────────────────
void OuterX3_ExtPressure(MeshBlock *pmb, Coordinates *pco,
    AthenaArray<Real> &prim, FaceField &b,
    Real time, Real dt,
    int is, int ie, int js, int je, int ks, int ke, int ngh) {

    // Primitives: zero-gradient with density floor
    for (int n = 1; n <= ngh; ++n) {
        for (int j = js; j <= je; ++j) {
            for (int i = is; i <= ie; ++i) {
                prim(IDN, ke+n, j, i) = std::max(prim(IDN, ke, j, i), g_p_ext);
                prim(IVX, ke+n, j, i) = prim(IVX, ke, j, i);
                prim(IVY, ke+n, j, i) = prim(IVY, ke, j, i);
                prim(IVZ, ke+n, j, i) = prim(IVZ, ke, j, i);
            }
        }
    }

    if (MAGNETIC_FIELDS_ENABLED) {
        // x1f
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie + 1; ++i)
                    b.x1f(ke+n, j, i) = b.x1f(ke, j, i);

        // x2f
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je + 1; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x2f(ke+n, j, i) = b.x2f(ke, j, i);

        // x3f: last active face = ke+1; ghost faces at ke+1+n
        for (int n = 1; n <= ngh; ++n)
            for (int j = js; j <= je; ++j)
                for (int i = is; i <= ie; ++i)
                    b.x3f(ke+1+n, j, i) = b.x3f(ke+1, j, i);
    }
}
