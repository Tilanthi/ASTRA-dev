#!/usr/bin/env python3
"""Shared Athena++ filament config builder for the referee follow-up campaigns.

Produces .athinput files for the validated configuration used by the Jul 2026
audit (transverse ``user`` boundary conditions, required by the current
Athena++ binary). The problem-generator block matches the filament generator
used throughout the paper (four_pi_G, f_line_mass, plasma_beta, theta_deg,
mach_number, perturb_ampl, random_seed, W_core), with lambda_J = 1 by
construction.
"""
FOUR_PI_G = 39.4784176044  # 4 pi^2  -> lambda_J = 1 in code units
W_CORE = 0.3               # Gaussian half-width in lambda_J (paper W_core)


def make_cfg(pid, f, beta, theta, Lx, seed, perturb=1e-2,
             cells_per_lambda=64, nproc=16, tlim=0.5, hdt=0.001, odt=0.005):
    """Return an Athena++ .athinput string for one filament simulation."""
    nx = int(Lx * cells_per_lambda)
    ny = 64
    nz = 64
    # choose an x1 meshblock size (multiple of 32) so that nx/mbx == nproc
    mbx = 32
    while mbx < nx and (nx % mbx or nx // mbx != nproc):
        mbx += 32
    if nx // mbx != nproc:
        # fall back to a single serial-safe block
        mbx = nx
        nproc = 1
    return f"""<comment>
problem   = {pid}
f={f} beta={beta} theta={theta} Lx={Lx} seed={seed} perturb_ampl={perturb} cells_per_lambda={cells_per_lambda} nproc={nproc} odt={odt}

<job>
problem_id      = {pid}
max_runtime     = 21600
num_cores       = {nproc}
restart_file    =

<output1>
file_type   = hdf5
variable    = prim
dt          = {odt}
id          = prim
data_dir    = ./{pid}/

<output2>
file_type   = hst
dt          = {hdt}
id          = hst
data_dir    = ./{pid}/

<time>
cfl_number  = 0.3
tlim        = {tlim}
nlim        = -1

<mesh>
nx1         = {nx}
x1min       = 0.0
x1max       = {Lx}
ix1_bc      = periodic
ox1_bc      = periodic
nx2         = {ny}
x2min       = -0.5
x2max       = 0.5
ix2_bc      = user
ox2_bc      = user
nx3         = {nz}
x3min       = -0.5
x3max       = 0.5
ix3_bc      = user
ox3_bc      = user

<meshblock>
nx1 = {mbx}
nx2 = {ny}
nx3 = {nz}

<hydro>
gamma           = 1.0
iso_sound_speed  = 1.0

<gravity>
grav_mean_rho   = 1.0

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f}
plasma_beta     = {beta}
theta_deg       = {theta}
mach_number     = 1.0
perturb_ampl    = {perturb}
random_seed     = {seed}
W_core          = {W_CORE}
"""


def add(manifest, suite, pid, outdir, **kw):
    """Write one config and register it in the manifest under ``suite``."""
    from pathlib import Path
    d = Path(outdir) / suite
    d.mkdir(parents=True, exist_ok=True)
    p = d / (pid + '.athinput')
    p.write_text(make_cfg(pid, **kw))
    manifest['suites'].setdefault(suite, []).append(
        {'pid': pid, 'config': str(p), **kw})
