// ============================================================
// Athena++ Problem Generator: filament_ic_sensitivity
// IC Sensitivity Test — Referee Response May 2026
//
// Extends filament_spacing_pr.cpp with ic_type parameter:
//   "gaussian"  — Gaussian profile (default, same as all prior campaigns)
//   "king"      — King (modified Lorentzian) profile: centrally concentrated
//   "uniform"   — Top-hat uniform density: flat profile within W_core
//
// For all IC types the integrated line mass is matched to f*M_crit so
// fragmentation times are directly comparable.
//
// Geometry:  Filament axis = x1 (periodic, fragmentation direction)
//            Transverse plane = x2-x3 (periodic, density profile)
//            B-field: longitudinal (along x1) — consistent with campaign baseline
//
// Code units: four_pi_G = 39.4784 → G = π/4 → λ_J = 1, cs = 1, ρ_bg = 1
//
// Parameters (<problem> block):
//   four_pi_G       [=39.4784176044]  4πG code value
//   f_line_mass     [=1.0]        Line-mass fraction
//   plasma_beta     [=1.0]        β = 2ρ_bg·cs²/B₀²
//   mach_number     [=1.0]        Turbulent Mach number
//   W_core          [=0.3]        Filament half-width in λ_J
//   perturb_ampl    [=1e-4]       Perturbation amplitude
//   random_seed     [=42]         RNG seed
//   ic_type         [="gaussian"] IC density profile ("gaussian","king","uniform")
//
// Author: ASTRA automated system | Date: 2026-05-12
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

// ── Mesh-level init: register 4πG for self-gravity solver ───────────────────
void Mesh::InitUserMeshData(ParameterInput *pin) {
    if (SELF_GRAVITY_ENABLED) {
        Real four_pi_G = pin->GetOrAddReal("problem", "four_pi_G",
                                           39.4784176044);
        SetFourPiG(four_pi_G);
    }
}

// ── Problem generator ────────────────────────────────────────────────────────
void MeshBlock::ProblemGenerator(ParameterInput *pin) {

    // ── Parameters ──────────────────────────────────────────────────────────
    Real four_pi_G  = pin->GetOrAddReal("problem", "four_pi_G",
                                        39.4784176044);
    Real f_line     = pin->GetOrAddReal("problem", "f_line_mass",  1.0);
    Real beta       = pin->GetOrAddReal("problem", "plasma_beta",  1.0);
    Real mach       = pin->GetOrAddReal("problem", "mach_number",  1.0);
    Real W_core     = pin->GetOrAddReal("problem", "W_core",       0.3);
    Real perturb_a  = pin->GetOrAddReal("problem", "perturb_ampl", 1.0e-4);
    int  seed       = pin->GetOrAddInteger("problem", "random_seed", 42);
    Real cs         = pin->GetOrAddReal("hydro", "iso_sound_speed", 1.0);
    std::string ic_type = pin->GetOrAddString("problem", "ic_type",
                                              "gaussian");

    // ── Derived quantities ───────────────────────────────────────────────────
    Real rho_bg  = 1.0;
    Real G_code  = four_pi_G / (4.0 * M_PI);
    Real M_crit  = 2.0 * cs * cs / G_code;

    // For each IC type, set rho_amp so that integrated line mass = f*M_crit:
    //   Gaussian: integral_2D exp(-r²/2W²) dA = 2πW²  → rho_amp = f*M_crit/(2πW²)
    //   King:     integral_2D (W²/(r²+W²))²  dA = πW²  → rho_amp = f*M_crit/(πW²) = 2× Gaussian
    //   Uniform:  integral_2D [r<W] dA = πW²           → rho_amp = f*M_crit/(πW²) = 2× Gaussian
    Real rho_amp;
    if (ic_type == "king" || ic_type == "uniform") {
        rho_amp = f_line * M_crit / (M_PI * W_core * W_core);
    } else {
        // gaussian (default)
        rho_amp = f_line * M_crit / (2.0 * M_PI * W_core * W_core);
    }

    // Magnetic field magnitude from β (defined w.r.t. background density)
    Real B0 = (beta > 0.0) ? cs * std::sqrt(2.0 * rho_bg / beta) : 0.0;
    // Longitudinal: B along x1 (parallel to filament axis)
    Real Bx1 = B0, Bx2 = 0.0, Bx3 = 0.0;

    // ── Kolmogorov velocity perturbation along x1 only ───────────────────────
    const int Nm = 12;
    Real Lx1 = pmy_mesh->mesh_size.x1max - pmy_mesh->mesh_size.x1min;

    std::vector<Real> kx(Nm), ph(Nm), amp_k(Nm);
    std::mt19937 rng(static_cast<unsigned int>(seed));
    std::uniform_real_distribution<Real> U_phase(0.0, 2.0 * M_PI);

    for (int n = 0; n < Nm; ++n) {
        kx[n]    = 2.0 * M_PI * (n + 1) / Lx1;
        ph[n]    = U_phase(rng);
        amp_k[n] = std::pow(kx[n], -11.0 / 6.0);
    }

    // Normalise to target RMS v1 = mach · perturb_a · cs
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

        Real r2 = x2 * x2 + x3 * x3;
        Real rho;

        if (ic_type == "king") {
            // King (modified Lorentzian): ρ = ρ_bg + ρ_amp·(W²/(r²+W²))²
            Real W2 = W_core * W_core;
            rho = rho_bg + rho_amp * (W2 * W2) / ((r2 + W2) * (r2 + W2));
        } else if (ic_type == "uniform") {
            // Top-hat: uniform within r < W_core, background outside
            rho = (r2 < W_core * W_core) ? (rho_bg + rho_amp) : rho_bg;
        } else {
            // Gaussian (default — identical to filament_spacing_pr)
            rho = rho_bg + rho_amp * std::exp(-r2 / (2.0 * W_core * W_core));
        }

        Real v1 = 0.0;
        for (int n = 0; n < Nm; ++n)
            v1 += vnorm * amp_k[n] * std::cos(kx[n] * x1 + ph[n]);

        phydro->u(IDN, k, j, i) = rho;
        phydro->u(IM1, k, j, i) = rho * v1;
        phydro->u(IM2, k, j, i) = 0.0;
        phydro->u(IM3, k, j, i) = 0.0;
    }

    // ── Magnetic field (face-centred) ────────────────────────────────────────
    if (MAGNETIC_FIELDS_ENABLED) {
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
