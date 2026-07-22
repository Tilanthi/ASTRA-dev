#!/usr/bin/env python3
"""Referee-v34 arbitration campaign config generator (Jul 2026).

Campaigns (all with the single filament_ambient binary unless noted):
  P0_smoke    : 4 tiny validation runs (profiles x BCs)
  P1_controls : d=0.5 paper-box controls, gaussian+ostriker x user/reflecting
  P2a_t1x     : T1 calibration expansion (OLD rce binary, paper config)
  P2b_am_d1   : main arbitration grid at d=1.0 (gaussian + ostriker)
  P3_heavy    : d=2.0 far-boundary pair
  P3_tr       : physical-turbulence (perturb_ampl=1.0) supercritical runs
"""
import json
from pathlib import Path

FOUR_PI_G = 39.4784176044
W_CORE = 0.3


def make_cfg(pid, f, beta, d, ny, bc, profile='gaussian', bgeom='longitudinal',
             seed=42, perturb=1e-2, tlim=1.5, odt=0.05, nx=512, Lx=8,
             nproc=16, mb=(32, 64, 64), hdt=0.001, maxrt=43200):
    return f"""<comment>
problem   = {pid}
f={f} beta={beta} bgeom={bgeom} profile={profile} d={d} bc={bc} seed={seed} ampl={perturb}

<job>
problem_id      = {pid}
max_runtime     = {maxrt}
num_cores       = {nproc}
restart_file    =

<output1>
file_type   = hdf5
variable    = prim
dt          = {odt}
id          = prim

<output2>
file_type   = hst
dt          = {hdt}
id          = hst

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
x2min       = -{d}
x2max       = {d}
ix2_bc      = {bc}
ox2_bc      = {bc}
nx3         = {ny}
x3min       = -{d}
x3max       = {d}
ix3_bc      = {bc}
ox3_bc      = {bc}

<meshblock>
nx1 = {mb[0]}
nx2 = {mb[1]}
nx3 = {mb[2]}

<hydro>
gamma           = 1.0
iso_sound_speed  = 1.0

<gravity>
grav_mean_rho   = 1.0

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f}
plasma_beta     = {beta}
bfield_geometry = {bgeom}
mach_number     = 1.0
perturb_ampl    = {perturb}
random_seed     = {seed}
W_core          = {W_CORE}
profile         = {profile}
p_ext_ratio     = 0.0
"""


OUT = Path('configs_v34')
manifest = {'suites': {}}


def add(suite, pid, **kw):
    d = OUT / suite
    d.mkdir(parents=True, exist_ok=True)
    (d / f'{pid}.athinput').write_text(make_cfg(pid, **kw))
    manifest['suites'].setdefault(suite, []).append({'pid': pid, **kw})


# geometry -> (ny, nproc, meshblock)
GEOM = {0.5: (64, 16, (32, 64, 64)),
        1.0: (128, 32, (32, 64, 128)),
        2.0: (256, 64, (32, 64, 128))}


def geo(d):
    ny, npr, mb = GEOM[d]
    return dict(d=d, ny=ny, nproc=npr, mb=mb)


# ── P0 smoke: tiny runs ──────────────────────────────────────────────────────
for prof in ('gaussian', 'ostriker'):
    for bc in ('user', 'reflecting'):
        pid = f'SMK_{prof[:4]}_{bc[:4]}'
        add('P0_smoke', pid, f=2.0, beta=1.0, d=0.5, ny=32, bc=bc,
            profile=prof, nx=64, nproc=2, mb=(32, 32, 32),
            tlim=0.02, odt=0.01)

# ── P1 controls: paper box d=0.5 ─────────────────────────────────────────────
for prof in ('gaussian', 'ostriker'):
    for bc in ('user', 'reflecting'):
        pid = f'AM_{prof[:4]}_f2.0_b1.0_th0_d0.5_{bc[:4]}_s42'
        add('P1_controls', pid, f=2.0, beta=1.0, bc=bc, profile=prof,
            **geo(0.5))

# ── P2b main arbitration at d=1.0 ────────────────────────────────────────────
# gaussian
for bc in ('user', 'reflecting', 'periodic'):
    add('P2b_am_d1', f'AM_gaus_f2.0_b1.0_th0_d1.0_{bc[:4]}_s42',
        f=2.0, beta=1.0, bc=bc, profile='gaussian', **geo(1.0))
for bc in ('user', 'reflecting'):
    add('P2b_am_d1', f'AM_gaus_f1.5_b1.0_th0_d1.0_{bc[:4]}_s42',
        f=1.5, beta=1.0, bc=bc, profile='gaussian', **geo(1.0))
    add('P2b_am_d1', f'AM_gaus_f2.0_b1.0_th0_d1.0_{bc[:4]}_s137',
        f=2.0, beta=1.0, bc=bc, seed=137, profile='gaussian', **geo(1.0))
    add('P2b_am_d1', f'AM_gaus_f2.0_b1.0_th90_d1.0_{bc[:4]}_s42',
        f=2.0, beta=1.0, bc=bc, bgeom='perpendicular', profile='gaussian',
        **geo(1.0))
add('P2b_am_d1', 'AM_gaus_f2.0_b1.0_th0_d1.0_user_s42_a4',
    f=2.0, beta=1.0, bc='user', perturb=1e-4, profile='gaussian', **geo(1.0))
# ostriker
for bc in ('user', 'reflecting'):
    for f in (1.5, 2.0):
        add('P2b_am_d1', f'EQ_ostr_f{f}_b1.0_th0_d1.0_{bc[:4]}_s42',
            f=f, beta=1.0, bc=bc, profile='ostriker', **geo(1.0))
    add('P2b_am_d1', f'EQ_ostr_f2.0_b1.0_th0_d1.0_{bc[:4]}_s137',
        f=2.0, beta=1.0, bc=bc, seed=137, profile='ostriker', **geo(1.0))

# ── P3 heavy: d=2.0 far boundary ─────────────────────────────────────────────
for bc in ('user', 'reflecting'):
    add('P3_heavy', f'AM_gaus_f2.0_b1.0_th0_d2.0_{bc[:4]}_s42',
        f=2.0, beta=1.0, bc=bc, profile='gaussian', **geo(2.0))

# ── P3 turbulence race: physical turbulence, paper config ────────────────────
for f in (1.5, 2.0):
    for seed in (42, 137):
        add('P3_tr', f'TR_gaus_f{f}_b1.0_th0_d0.5_user_s{seed}_aP',
            f=f, beta=1.0, bc='user', seed=seed, perturb=1.0,
            profile='gaussian', **geo(0.5))
    add('P3_tr', f'TR_gaus_f{f}_b1.0_th0_d1.0_user_s42_aP',
        f=f, beta=1.0, bc='user', perturb=1.0, profile='gaussian',
        **geo(1.0))

OUT.mkdir(exist_ok=True)
(OUT / 'manifest_v34.json').write_text(json.dumps(manifest, indent=2))
tot = sum(len(v) for v in manifest['suites'].values())
print(f'total {tot}')
for k, v in manifest['suites'].items():
    print(' ', k, len(v))
