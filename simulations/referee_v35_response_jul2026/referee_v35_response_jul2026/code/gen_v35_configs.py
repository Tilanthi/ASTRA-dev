#!/usr/bin/env python3
import os, itertools

BASE = "/data/referee_v35_campaigns_jul2026"

def write_athinput(outdir, pid, params):
    os.makedirs(outdir, exist_ok=True)
    p = params
    bc2 = p.get('bc','reflecting')
    d = p.get('d', 1.0)
    nx_t = 64
    eta_str = ""
    if p.get('eta_ad', 0.0) > 0:
        eta_str = f"\neta_ohm         = 0.0\neta_hall        = 0.0\neta_ad          = {p['eta_ad']}"
    content = f"""<comment>
problem   = {pid}
f={p['f']} beta={p['beta']} bgeom={p.get('bgeom','longitudinal')} d={d} bc={bc2} seed={p['seed']} ampl={p.get('ampl',0.01)} theta={p.get('theta',0)}

<job>
problem_id      = {pid}
max_runtime     = 43200
num_cores       = 32

<output1>
file_type   = hdf5
variable    = prim
dt          = 0.05
id          = prim

<output2>
file_type   = hst
dt          = 0.001
id          = hst

<time>
cfl_number  = 0.3
tlim        = 1.5
nlim        = -1

<mesh>
nx1         = 512
x1min       = 0.0
x1max       = 8
ix1_bc      = periodic
ox1_bc      = periodic
nx2         = {nx_t}
x2min       = -{d}
x2max       = {d}
ix2_bc      = {bc2}
ox2_bc      = {bc2}
nx3         = {nx_t}
x3min       = -{d}
x3max       = {d}
ix3_bc      = {bc2}
ox3_bc      = {bc2}

<meshblock>
nx1 = 32
nx2 = {nx_t}
nx3 = {nx_t}

<hydro>
gamma           = 1.0
iso_sound_speed  = 1.0

<gravity>
grav_mean_rho   = 1.0

<problem>
four_pi_G       = 39.4784176044
f_line_mass     = {p['f']}
plasma_beta     = {p['beta']}
bfield_geometry = {p.get('bgeom','longitudinal')}
bfield_angle    = {p.get('theta',0)}
mach_number     = 1.0
perturb_ampl    = {p.get('ampl',0.01)}
random_seed     = {p['seed']}
W_core          = 0.3
profile         = gaussian
p_ext_ratio     = 0.0{eta_str}
"""
    with open(os.path.join(outdir, pid+'.athinput'), 'w') as fh:
        fh.write(content)

# RC1: periodic d=1.0 — reconciliation (does main-grid geometry actually bead?)
rc1_dir = f"{BASE}/configs_v35/RC1_periodic_d1"
rc1_runs = []
for f,b,s in itertools.product([1.5,2.0],[0.5,1.0,2.0],[42,137]):
    pid = f"RC1_per_f{f}_b{b}_th0_d1.0_s{s}"
    write_athinput(rc1_dir, pid, dict(f=f,beta=b,seed=s,bc='periodic',d=1.0,ampl=0.01))
    rc1_runs.append(pid)
print(f"RC1: {len(rc1_runs)} runs")

# RC2: expanded reflecting d=1.0 ensemble (14->36+)
rc2_dir = f"{BASE}/configs_v35/RC2_refl_d1_expanded"
rc2_runs = []
for f,b,s in itertools.product([1.5,1.7,2.0],[0.5,1.0,2.0],[42,137,251]):
    pid = f"RC2_refl_f{f}_b{b}_th0_d1.0_s{s}"
    write_athinput(rc2_dir, pid, dict(f=f,beta=b,seed=s,bc='reflecting',d=1.0,ampl=0.01))
    rc2_runs.append(pid)
print(f"RC2: {len(rc2_runs)} runs")

# RC3: perpendicular θ=90 at d=1.0 reflecting
rc3_dir = f"{BASE}/configs_v35/RC3_perp_d1"
rc3_runs = []
for f,b,s in itertools.product([1.2,1.5,2.0],[0.5,1.0,2.0],[42,137]):
    pid = f"RC3_perp_f{f}_b{b}_th90_d1.0_s{s}"
    write_athinput(rc3_dir, pid, dict(f=f,beta=b,seed=s,bc='reflecting',d=1.0,ampl=0.01,theta=90,bgeom='perpendicular'))
    rc3_runs.append(pid)
print(f"RC3: {len(rc3_runs)} runs")

# RC4: non-ideal ambipolar θ=90 via athena-sc
rc4_dir = f"{BASE}/configs_v35/RC4_ambipolar_perp"
rc4_runs = []
for f,b,eta in itertools.product([1.0,1.2,1.5],[0.5,1.0],[0.01,0.05]):
    pid = f"RC4_ad_f{f}_b{b}_th90_eta{eta}_s42"
    write_athinput(rc4_dir, pid, dict(f=f,beta=b,seed=42,bc='reflecting',d=1.0,ampl=0.01,theta=90,bgeom='perpendicular',eta_ad=eta))
    rc4_runs.append(pid)
print(f"RC4: {len(rc4_runs)} runs")

total = len(rc1_runs)+len(rc2_runs)+len(rc3_runs)+len(rc4_runs)
print(f"TOTAL: {total} runs")
