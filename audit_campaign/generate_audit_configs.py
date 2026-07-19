#!/usr/bin/env python3
"""
COMPREHENSIVE AUDIT CONFIG GENERATOR — Standard Athena++ format.
Generates .athinput files for: extended-domain supercritical audit,
domain-size convergence map, and field-geometry spot-check.
Total: ~70 sims. On 220 CPUs at 16 cores/sim (~13 concurrent), ~10 hrs.
Usage: python3 generate_audit_configs.py
"""
import numpy as np, json
from pathlib import Path

SEEDS = [42, 137, 251]
NY, NZ = 64, 64  # transverse resolution
W_CORE = 0.3     # filament half-width in lambda_J
FOUR_PI_G = 39.4784176044  # code units: G = pi/4 -> lambda_J = 1

def make_athinput(f_line_mass, plasma_beta, mach_number, theta_deg,
                  Lx_lambdaJ, Nx, seed, problem_id,
                  tlim=2.0, wall_timeout=21600, output_dt=0.1):
    """Generate a standard-format Athena++ .athinput file."""
    x1min, x1max = 0.0, Lx_lambdaJ
    y1min, y1max = -0.5, 0.5
    z1min, z1max = -0.5, 0.5
    B0 = np.sqrt(2.0 / plasma_beta) if plasma_beta > 0 else 0.0
    return f"""<comment>
problem   = {problem_id}
f={f_line_mass} beta={plasma_beta} M={mach_number} theta={theta_deg} Lx={Lx_lambdaJ}

<job>
problem_id      = {problem_id}
max_runtime     = {wall_timeout}
num_cores       = 16
restart_file    =

<output1>
file_type   = hdf5
variable    = prim
dt          = {output_dt}
id          = prim
data_dir    = ./outputs/{problem_id}/

<output2>
file_type   = hst
dt          = 0.005
id          = hst
data_dir    = ./outputs/{problem_id}/

<time>
cfl_number  = 0.3
tlim        = {tlim}
nlim        = -1

<mesh>
nx1         = {Nx}
x1min       = {x1min}
x1max       = {x1max}
ix1_bc      = periodic
ox1_bc      = periodic
nx2         = {NY}
x2min       = {y1min}
x2max       = {y1max}
ix2_bc      = periodic
ox2_bc      = periodic
nx3         = {NZ}
x3min       = {z1min}
x3max       = {z1max}
ix3_bc      = periodic
ox3_bc      = periodic

<meshblock>
nx1 = 32
nx2 = 64
nx3 = 64

<hydro>
gamma           = 1.0
iso_sound_speed  = 1.0

<gravity>
grav_mean_rho   = 1.0

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f_line_mass}
plasma_beta     = {plasma_beta}
theta_deg       = {theta_deg}
mach_number     = {mach_number}
perturb_ampl    = 1.0
random_seed     = {seed}
W_core          = {W_CORE}
"""

def generate_all(output_dir="configs"):
    out = Path(output_dir); out.mkdir(exist_ok=True)
    manifest = {"campaigns": {}, "total_sims": 0}
    all_configs = []

    def add(camp, f, beta, theta, Lx, Nx, seed, subdir, **kw):
        pid = f"AUDIT_{subdir}_f{f:.1f}_b{beta:.1f}_th{theta:.0f}_Lx{int(Lx)}_s{seed}"
        cfg = make_athinput(f, beta, 1.0, theta, Lx, Nx, seed, pid, **kw)
        p = out / camp / f"{pid}.athinput"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(cfg)
        all_configs.append(str(p))
        return str(p)

    # 1. Extended-domain supercritical audit (24 lambda_J)
    camp = "supercritical_extended"; n = 0
    for f in [1.5, 2.0, 2.5, 3.0]:
        for beta in [0.3, 1.0, 2.0]:
            if f in [2.5, 3.0] and beta != 1.0: continue  # reduce grid
            for s in SEEDS:
                add(camp, f, beta, 0.0, 24.0, 1536, s, f"f{f:.0f}b{beta:.0f}"); n += 1
    manifest["campaigns"][camp] = {"n_sims": n, "desc": "Extended-domain (24Lj) supercritical audit"}
    manifest["total_sims"] += n

    # 2. Domain-size convergence map (f=2.0, beta=1.0)
    camp = "domain_convergence"; n = 0
    for Lx in [8, 16, 24, 32, 48]:
        Nx = {8:512, 16:1024, 24:1536, 32:2048, 48:3072}[Lx]
        for s in SEEDS:
            add(camp, 2.0, 1.0, 0.0, float(Lx), Nx, s, f"Lx{Lx}"); n += 1
    manifest["campaigns"][camp] = {"n_sims": n, "desc": "Domain-size convergence map at f=2.0"}
    manifest["total_sims"] += n

    # 3. Field Geometry spot-check (extended domain)
    camp = "field_geometry"; n = 0
    for f in [1.5, 2.0]:
        for theta in [0.0, 45.0, 90.0]:
            for s in SEEDS:
                add(camp, f, 1.0, theta, 24.0, 1536, s, f"f{f:.0f}th{theta:.0f}"); n += 1
    manifest["campaigns"][camp] = {"n_sims": n, "desc": "FG spot-check at extended domain"}
    manifest["total_sims"] += n

    # 4. Near-critical validation
    camp = "near_critical"; n = 0
    for f in [1.0, 1.1, 1.2]:
        for s in SEEDS:
            add(camp, f, 1.0, 0.0, 24.0, 1536, s, f"f{f:.1f}"); n += 1
    manifest["campaigns"][camp] = {"n_sims": n, "desc": "Near-critical validation at 24Lj"}
    manifest["total_sims"] += n

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    for c, info in manifest["campaigns"].items():
        print(f"  {c}: {info['n_sims']} configs")
    print(f"\nTotal: {manifest['total_sims']} configs")
    return all_configs

if __name__ == "__main__":
    print("="*60); print("AUDIT CAMPAIGN CONFIG GENERATION"); print("="*60)
    generate_all()
