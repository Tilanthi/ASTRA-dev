"""zeta2_C: the fixed Chowla-Selberg evaluator for zeta2 at high t.
Defect in zeta2_A (heat68): the k-shell stop `abs(shell) < TRUNC_REL *
max(abs(total), 1)` is an ABSOLUTE floor. Each shell carries the K-envelope
e^{-pi*t/2}; above t ~ 66-70 the shells fall below the floor and the loop
halts after k=1, dropping k=2,3 terms that are O(1) after the e^{+pi*t/2}
prefactor (measured: 0.186 wrong vs 1.357e-27 right at m2's t=84.4669 zero).
Fix: explicit summation of ALL (m,k) with 2*pi*D*m*k <= zcut, with
t-adaptive zcut = 160 + 0.08*t^2 (empirically zcut>=500 converges at t=84.5:
29/127/425-term sums agree to all printed digits), dps per the 0.6822*t law
+ margin.

Validation battery:
  V1  all seven m2 zeros: |zeta2_C(s0, 7)| vs 49^{-sigma0} * m3's |F| table
  V2  low-t regression: zeta2_C vs certified zeta2_A at the fold region
      (s = 1/2 +- 1e-12, D = Delta*) and at the best zero -- must reproduce
      the certified values (extra z>160 terms are e^{-z}-tiny at low t)
"""
import ast, time
from mpmath import (mp, mpf, mpc, sqrt, zeta, gamma, besselk, pi, im)

mp.dps = 130
PATH = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat68_epstein_rect_zeros.py"
tree = ast.parse(open(PATH).read())
fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "zeta2_A"][0]
ns = dict(mpf=mpf, mp=mp, zeta=zeta, sqrt=sqrt, pi=pi, gamma=gamma,
          besselk=besselk, TRUNC_REL=mpf("1e-45"))
exec(compile(ast.Module(body=[fn], type_ignores=[]), "<z>", "exec"), ns)
zeta2_A = ns["zeta2_A"]

def zeta2_C(s, D, zcut=None):
    """Explicit double sum; returns (value, nterms). zcut None -> adaptive."""
    nu = s - mpf("0.5")
    if zcut is None:
        zcut = mpf(160) + mpf("0.08") * (mpf(float(abs(im(s)))) ** 2)
    t1 = zeta(2 * s)
    t2 = sqrt(pi) * gamma(s - mpf("0.5")) * D ** (1 - 2 * s) * zeta(2 * s - 1) / gamma(s)
    total = mpf(0)
    n = 0
    k = 1
    while True:
        z = 2 * pi * D * k
        if z > zcut:
            break
        m = 1
        while z * m <= zcut:
            total += (mpf(m) / k) ** nu * besselk(nu, z * m)
            n += 1
            m += 1
        k += 1
    t3 = (4 * pi ** s / gamma(s)) * D ** (mpf("0.5") - s) * total
    return t1 + t2 + t3, n

ZEROS = [  # (sigma, t, m3 |F(zeta2(s,1/7))| at dps 40)
    (mpf("0.5246770865109702460561581364"), mpf("44.41100379785915585775068919"), "2.56e-26"),
    (mpf("0.7159014103823531018264718067"), mpf("47.29775881721048753252892984"), "9.06e-26"),
    (mpf("0.6046656812518528366431236261"), mpf("84.46688428178119162005426882"), "1.43e-26"),
    (mpf("0.6310301952784749425929755304"), mpf("91.06135680391329435771957746"), "7.56e-26"),
    (mpf("0.6608607494128433009276473937"), mpf("92.40067261379804243385567371"), "1.11e-25"),
    (mpf("0.6852853131833004632846554526"), mpf("98.61599811620170433773193031"), "2.49e-25"),
    (mpf("0.6203387601752353028098032884"), mpf("110.2778479937533731781573067"), "9.19e-25"),
]
D7 = mpf(7)

print("=== V1: seven zeros, zeta2_C at dps per 0.6822*t + 45 margin ===", flush=True)
print("ratio = |F_C(s0,7)| / (49^{-sig0} * m3_ref); zconv = rel diff zcut vs 1.5*zcut", flush=True)
print(f"{'t':>8} {'dps':>4} {'|F(s0,7)|':>12} {'49^-sig*m3':>12} {'ratio':>7} {'zconv':>8} terms", flush=True)
for sig, tim, ref in ZEROS:
    dps = int(0.6822 * float(tim)) + 45
    mp.dps = dps
    s = mpc(sig, tim)
    zcut = mpf(160) + mpf("0.08") * (mpf(float(tim)) ** 2)
    t0 = time.time()
    v1, n1 = zeta2_C(s, D7, zcut=zcut)
    v2, n2 = zeta2_C(s, D7, zcut=mpf("1.5") * zcut)
    zconv = abs(v2 - v1) / abs(v1)
    pred = mpf(49) ** (-sig) * mpf(ref)
    print(f"{mp.nstr(tim, 6):>8} {dps:>4} {mp.nstr(abs(v1), 6):>12} {mp.nstr(pred, 6):>12} "
          f"{mp.nstr(abs(v1) / pred, 5):>7} {mp.nstr(zconv, 3):>8} {n1}/{n2} ({time.time()-t0:.0f}s)",
          flush=True)
    mp.dps = 130

print("\n=== V2: low-t regression vs certified zeta2_A (dps 55) ===", flush=True)
mp.dps = 55
DST = mpf("0.141733239663887191395415685084185024")
for s_lbl, s in [("1/2+1e-12, D=Dstar", mpc(mpf("0.5") + mpf("1e-12"), 0)),
                 ("1/2-1e-12, D=Dstar", mpc(mpf("0.5") - mpf("1e-12"), 0)),
                 ("0.7159+47.30i, D=7", mpc(ZEROS[1][0], ZEROS[1][1]))]:
    D = DST if "Dstar" in s_lbl else D7
    va, _ = zeta2_A(s, D)
    vc, nc = zeta2_C(s, D)
    print(f"{s_lbl:>22}: A={mp.nstr(va, 12)}  C={mp.nstr(vc, 12)}  "
          f"|A-C|={mp.nstr(abs(va - vc), 4)}  (C terms {nc})", flush=True)
