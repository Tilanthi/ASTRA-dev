#!/usr/bin/env python3
"""A5: Magnetic-subcriticality stability test.
Longitudinal-B, ambient-confined, thermally-SUPERCRITICAL filaments across plasma-beta.
Tests whether strong longitudinal field (low beta = magnetically subcritical) STABILISES
a filament that is ABOVE the critical line mass (f>1), integrated to t=40 tJ.
If low-beta stays C~1 to t=40 -> genuine magnetic stability boundary (not merely slow).
Resolution 256x64x64 matches the Fig-2 base grid; periodic (matches Fig-2 base grid)."""
import os
TEMPLATE = """<comment>
problem   = {pid}
A5 magnetic-subcriticality stability test: f={f} beta={beta} longitudinal th0 M={M} tlim40

<job>
problem_id      = {pid}
max_runtime     = 36000
num_cores       = 16

<output1>
file_type   = hdf5
variable    = prim
dt          = 2.0
id          = prim

<output2>
file_type   = hst
dt          = 0.05
id          = hst

<time>
cfl_number  = 0.3
tlim        = 40.0
nlim        = -1

<mesh>
nx1         = 256
x1min       = 0.0
x1max       = 8
ix1_bc      = periodic
ox1_bc      = periodic
nx2         = 64
x2min       = -1.0
x2max       = 1.0
ix2_bc      = periodic
ox2_bc      = periodic
nx3         = 64
x3min       = -1.0
x3max       = 1.0
ix3_bc      = periodic
ox3_bc      = periodic

<meshblock>
nx1 = 16
nx2 = 64
nx3 = 64

<hydro>
gamma           = 1.0
iso_sound_speed  = 1.0

<gravity>
grav_mean_rho   = 1.0

<problem>
four_pi_G       = 39.4784176044
f_line_mass     = {f}
plasma_beta     = {beta}
bfield_geometry = longitudinal
bfield_angle    = 0
mach_number     = {M}
perturb_ampl    = 0.01
random_seed     = 42
W_core          = 0.3
profile         = gaussian
p_ext_ratio     = 0.0
dt_kill         = 1e-09
eta_ohm         = 0.0
eta_hall        = 0.0
eta_ad          = 0.0
"""
outdir="/data/referee_v42_campaigns_jul2026/configs_A5"
betas=[0.05,0.10,0.15,0.30,1.0]
fs=[1.5,2.0]
M=2.0
n=0
for f in fs:
    for beta in betas:
        pid=f"A5_f{f}_b{beta}_th0_M{M}_s42"
        with open(os.path.join(outdir,pid+".athinput"),"w") as fh:
            fh.write(TEMPLATE.format(pid=pid,f=f,beta=beta,M=M))
        n+=1
print("wrote",n,"A5 configs to",outdir)
