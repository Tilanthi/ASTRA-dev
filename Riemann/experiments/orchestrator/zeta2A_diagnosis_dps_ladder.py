"""Test whether my cycle-16 'instrument death above t~84' is structural or a
dps-crossover artifact of m2's 0.6822*t law: at t=84 the law demands 57.6
digits, and my death-line anchor ran dps 50/60 -- both rungs BELOW the
crossover, so 'dps-stable' measured nothing. Route B (zeta2_A at Delta=7,
the scaling-identity side with no small-argument cancellation) evaluated at
m2's five high-t zero coordinates across dps {120, 100, 75, 60}.
Prediction if the law governs: |F|(dps) ~ max(10^-(dps-0.6822*t), ~1e-26
print-rounding floor), matching m3's dps-40 third-implementation values
(1.43e-26 ... 9.19e-25) at the plateau. Control: the t=47.3 best zero
(should sit at its 5.6e-27 floor at every dps >= 60)."""
import ast, time
from mpmath import (mp, mpf, mpc, sqrt, zeta, gamma, besselk, pi)

mp.dps = 130                      # parse precision FIRST (dps-15 trap)
PATH = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat68_epstein_rect_zeros.py"
tree = ast.parse(open(PATH).read())
fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "zeta2_A"][0]
ns = dict(mpf=mpf, mp=mp, zeta=zeta, sqrt=sqrt, pi=pi, gamma=gamma,
          besselk=besselk, TRUNC_REL=mpf("1e-45"))
exec(compile(ast.Module(body=[fn], type_ignores=[]), "<z>", "exec"), ns)
_z = ns["zeta2_A"]

ZEROS = [  # (sigma, t, m3's |F| at dps 40)
    (mpf("0.6046656812518528366431236261"), mpf("84.46688428178119162005426882"), "1.43e-26"),
    (mpf("0.6310301952784749425929755304"), mpf("91.06135680391329435771957746"), "7.56e-26"),
    (mpf("0.6608607494128433009276473937"), mpf("92.40067261379804243385567371"), "1.11e-25"),
    (mpf("0.6852853131833004632846554526"), mpf("98.61599811620170433773193031"), "2.49e-25"),
    (mpf("0.6203387601752353028098032884"), mpf("110.2778479937533731781573067"), "9.19e-25"),
    (mpf("0.7159014103823531018264718067"), mpf("47.29775881721048753252892984"), "9.06e-26"),  # control
]
D7 = mpf(7)
print(f"{'t':>8} {'law 0.6822t':>11} | m3 ref | " + " | ".join(f"|F| @dps{d}" for d in (120, 100, 75, 60)), flush=True)
for sig, tim, ref in ZEROS:
    s = mpc(sig, tim)
    row = []
    for dps in (120, 100, 75, 60):
        t0 = time.time()
        mp.dps = dps
        val = _z(s, D7)[0]
        row.append(f"{mp.nstr(abs(val), 3)} ({time.time()-t0:.1f}s)")
        mp.dps = 130
    print(f"{mp.nstr(tim, 6):>8} {0.6822*float(tim):>11.1f} | {ref} | " + " | ".join(row), flush=True)
