"""heat58b — convergence-corrected zero-sum Li/Keiper cross-check (extends
heat58, same instruction: two-instrument check of machine 3's contour
instrument, Letter 20).

heat58's raw truncation to 2700 zeros sat ~1.5% below published lambda_1 and
~1.6% below m3's lambda_15 — deficit growing with n, the signature of a TAIL,
not an instrument error. heat58's in-script tail estimate n^2 log(T)/T was
sloppy (no 2pi from the density); the FIRST draft of this script then
overcorrected to n(n+1)/2 — caught by hand-check before results: on the line
w = 1-1/rho = exp(i theta) EXACTLY (|w|=1), so term_n = 2-2cos(n theta) with
theta ~ 1/gamma, i.e. term ~ n^2/gamma^2 — and the 1/rho expansion agrees:
2Re[n/rho - C(n,2)/rho^2] ~ n/gamma^2 + n(n-1)/gamma^2 = n^2/gamma^2. With
N(T) ~ T log T /(2 pi):
    tail_n(T) ~ n^2 * (log T + 1)/(2 pi T),   k_n^theory = n^2/(2 pi).
Hand pre-check at n=1, T=3234: predicted deficit 4.47e-4 vs heat58 observed
3.57e-4 — agreement at the ~20% level expected of the asymptotic at low gamma.

Method (one enumeration, three cutoffs at zero-index 900/1800/2700): fit the
observed deficit against (log T + 1)/T per n from consecutive cutoff pairs,
report k_n vs theory, the extrapolated lambda_n(T=inf), and the convergence
ratio test. Comparisons only to values already on record: m3 contour lambda_1
~= 0.023096, lambda_15 ~= 5.045 (their Letter 20), published lambda_1 =
0.0230957089661 (on record since heat58). No other published values cited from
memory (trap #51/#63: nothing hand-typed).
"""
import mpmath as mp

mp.mp.dps = 40
CUTS = [900, 1800, 2700]
NZ = max(CUTS)
print(f"== heat58b: lambda_n zero-sum, cutoffs at zero-index {CUTS} ==", flush=True)

gammas = [mp.im(mp.zetazero(k)) for k in range(1, NZ + 1)]
for c in CUTS:
    print(f"  T(idx {c}) = gamma_{c} = {mp.nstr(gammas[c-1], 10)}", flush=True)

# accumulate partial pair sums at each cutoff in ONE pass
part = {c: [mp.mpf(0)] * 16 for c in CUTS}
idx = 0
for g in gammas:
    idx += 1
    rho = mp.mpc(mp.mpf("0.5"), g)
    w = 1 - 1 / rho
    wn = mp.mpf(1)
    for n in range(1, 16):
        wn = wn * w
        t = 2 - 2 * mp.re(wn)
        for c in CUTS:
            if idx <= c:
                part[c][n] += t

print("\n  n | lam(T1)      lam(T2)      lam(T3)   | deficit12   deficit23 | ratio12/23")
T = {c: gammas[c - 1] for c in CUTS}
for n in range(1, 16):
    a, b, cq = (part[c][n] for c in CUTS)
    d12, d23 = b - a, cq - b
    r = d12 / d23 if d23 != 0 else mp.inf
    print(f" {n:2d} | {mp.nstr(a,8):>12} {mp.nstr(b,8):>12} {mp.nstr(cq,8):>12} | "
          f"{mp.nstr(d12,3):>10} {mp.nstr(d23,3):>10} | {mp.nstr(r,4):>8}", flush=True)

# deficit-law fit: deficit_n(T) = k_n * (log T + 1)/T, two cutoffs -> k from each pair
print("\n  n | k_n(1,2)     k_n(2,3)     theory n^2/(2 pi) | extrap lam_n(T=inf)")
for n in range(1, 16):
    a, b, cq = (part[c][n] for c in CUTS)
    f1, f2, f3 = ((mp.log(T[c]) + 1) / T[c] for c in CUTS)
    k12, k23 = (b - a) / (f1 - f2), (cq - b) / (f2 - f3)
    lam_inf = cq + k23 * f3          # extrapolate the remaining tail at T3
    theory = n**2 / (2 * mp.pi)
    print(f" {n:2d} | {mp.nstr(k12,5):>12} {mp.nstr(k23,5):>12} {mp.nstr(theory,6):>15} | "
          f"{mp.nstr(lam_inf, 10)}", flush=True)

print("\nchecks:", flush=True)
a1 = part[CUTS[2]][1]
_, _, cq15 = None, None, part[CUTS[2]][15]
print(f"  raw lam_1(T3)      = {mp.nstr(a1, 8)}", flush=True)
print(f"  published lam_1    = 0.0230957089661 (on record)", flush=True)
print(f"  raw lam_15(T3)     = {mp.nstr(cq15, 8)}   (m3 contour: 5.045)", flush=True)
print("  extrapolated values in the table above are the cross-check numbers", flush=True)
