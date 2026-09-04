"""Truncation-vs-structure test for zeta2_A at Delta=7, m2's t=84.4669 zero.
Hypothesis: the z>160 break and TRUNC_REL k-stop assume K_nu(z) ~ e^{-z}
decay in z, valid only for z >> |nu|^2 ~ t^2. At t=84.5 all K terms are
~e^{-pi t/2}-scale (flat in z), so the coded truncation drops O(1)-after-
prefactor terms => dps-independent O(1) error (the observed signature).
Widen ZCUT and force the k-loop; if |F| drops toward m3's ~2e-28-scale
(|zeta2(s0,1/7)| = |49^{-s}| * |F_1/7| ~ 49^{-0.6} * 1.4e-26), the death
line is a truncation bug, not structural."""
import ast, time
from mpmath import (mp, mpf, mpc, sqrt, zeta, gamma, besselk, pi)

mp.dps = 80
PATH = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat68_epstein_rect_zeros.py"
tree = ast.parse(open(PATH).read())
fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "zeta2_A"][0]
ns = dict(mpf=mpf, mp=mp, zeta=zeta, sqrt=sqrt, pi=pi, gamma=gamma,
          besselk=besselk, TRUNC_REL=mpf("1e-45"))
exec(compile(ast.Module(body=[fn], type_ignores=[]), "<z>", "exec"), ns)

def zeta2_wide(s, D, zcut, kmax):
    nu = s - mpf("0.5")
    t1 = zeta(2 * s)
    t2 = sqrt(pi) * gamma(s - mpf("0.5")) * D ** (1 - 2 * s) * zeta(2 * s - 1) / gamma(s)
    total = mpf(0); n = 0
    for k in range(1, kmax + 1):
        for m in range(1, kmax + 1):
            z = 2 * pi * D * k * m
            if z > zcut:
                break
            total += (mpf(m) / k) ** nu * besselk(nu, z)
            n += 1
    t3 = (4 * pi ** s / gamma(s)) * D ** (mpf("0.5") - s) * total
    return t1 + t2 + t3, n

s0 = mpc(mpf("0.6046656812518528366431236261"), mpf("84.46688428178119162005426882"))
D7 = mpf(7)
for zcut, kmax in ((160, 10), (500, 30), (1500, 60), (4000, 120)):
    t0 = time.time()
    v, n = zeta2_wide(s0, D7, zcut, kmax)
    print(f"zcut={zcut:5d}: |F| = {mp.nstr(abs(v), 6)}  terms={n}  ({time.time()-t0:.0f}s)", flush=True)
