"""heat59 — GUE-side lambda_n ensemble (W-002 prediction generator).

Runs AFTER m4_lambdan_signature_design.md was committed; its outputs become the
hash target committed BEFORE any zeta-side lambda_n beyond published n. See the
design doc for the channel (off-line pair => e^{delta n/gamma^2} cos(n/gamma))
and the three pre-registered statistics.

Ensemble: per draw, CUE(256) eigenangles via Haar QR of complex Ginibre (with
the R-diagonal phase correction), the first K angles unfolded to zero
ordinates on [0, T_max] against the Riemann-von Mangoldt cumulative density
N(T) = (T/2pi) log(T/2pi e) + 7/8, plus the deterministic analytic tail
beyond T_max (no tail randomness: rigidity). lambda_n per draw by the heat58
zero-sum formula for n = 1..60.

Statistics (design doc section 3):
 1. per-n ensemble mean mu_n, std sigma_n;
 2. envelope: distribution of max_{n in [30,60]} |lambda_n - mu_n|/sigma_n;
 3. growing-oscillation detector: amplitude ratio of cos(n theta)-projected
    residual between windows n in [30,45] and [45,60], alpha_hat(theta) =
    (1/15) log(A2/A1) over theta grid; ensemble max over theta;
 4. lag-1 correlation of consecutive residuals (n in [30,60]).
Everything printed + pickled for the hash step. No zeta-side number is
computed here.
"""
import numpy as np
import pickle

rng = np.random.default_rng(20260903)
NCUE = 256
NN = 60            # lambda_n for n = 1..60
M = 2000           # draws
NMIN, NMID, NMAX = 30, 45, 60   # statistic windows (design doc)
THETAS = np.linspace(1.0 / NMAX, 1.0 / 14.0, 200)


def haar_unitary_eigangles(n):
    z = (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))) / np.sqrt(2)
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    q = q * (d / np.abs(d))[None, :]          # phase correction => Haar
    return np.angle(np.linalg.eigvals(q))


def cum_density(T):
    # Riemann-von Mangoldt cumulative zero count (smooth part)
    return (T / (2 * np.pi)) * np.log(T / (2 * np.pi * np.e)) + 7.0 / 8.0


# target window: first K CUE angles mapped to zeros on [0, T_max]
T_max = 240.0
K = int(np.floor(cum_density(T_max)))
print(f"== heat59: CUE({NCUE}) x {M} draws, zeros 1..{K} on [0,{T_max}], n<= {NN} ==")
print(f"   tail beyond T_max: deterministic analytic (rigidity), per design doc")

lam_all = np.zeros((M, NN + 1))
for m in range(M):
    ang = np.sort(haar_unitary_eigangles(NCUE))          # in (-pi, pi]
    u = (ang - ang[0]) / (2 * np.pi)                      # normalized spacing, [0,1)
    u = u[:K] / u[:K][-1]                                 # first K, rescale to [0,1]
    # invert cumulative density: solve N(T) = u * N(T_max) by bisection
    Ntar = u * cum_density(T_max)
    T_lo, T_hi = np.full(K, 1e-6), np.full(K, T_max)
    for _ in range(80):
        T_mid = 0.5 * (T_lo + T_hi)
        hi = cum_density(T_mid) > Ntar
        T_hi = np.where(hi, T_mid, T_hi)
        T_lo = np.where(hi, T_lo, T_mid)
    gam = 0.5 * (T_lo + T_hi)
    # deterministic analytic tail: n^2 * int_T^inf (dN/dt)/t^2 dt on a log grid
    tg = np.geomspace(T_max, 2e6, 4000)
    dens = (1 / (2 * np.pi)) * np.log(tg / (2 * np.pi))
    w = np.diff(tg)
    tm = 0.5 * (tg[:-1] + tg[1:])
    dens_m = 0.5 * (dens[:-1] + dens[1:])
    tail_unit = np.sum(dens_m * w / tm**2)      # per n^2, same for all n
    for n in range(1, NN + 1):
        z = 1 - 1 / (0.5 + 1j * gam)
        zn = np.ones(K, dtype=complex)
        for _ in range(n):
            zn = zn * z
        s = 2 - 2 * np.real(zn)
        lam_all[m, n] = s.sum() + (n**2) * tail_unit
    if (m + 1) % 250 == 0:
        print(f"   draw {m+1}/{M}", flush=True)
        np.save("heat59_lam_all_partial.npy", lam_all[: m + 1])  # crash-safe

mu = lam_all[:, 1:].mean(axis=0)
sd = lam_all[:, 1:].std(axis=0)
print("\n n |  mu_n (ensemble)   sigma_n")
for n in range(1, NN + 1):
    if n % 5 == 0 or n <= 3:
        print(f" {n:2d} | {mu[n-1]:16.6f} {sd[n-1]:12.6f}")

z = (lam_all[:, NMIN:NMAX + 1] - mu[NMIN - 1:NMAX]) / sd[NMIN - 1:NMAX]
env = np.max(np.abs(z), axis=1)
print(f"\n[1] envelope max_|z| over n in [{NMIN},{NMAX}]: "
      f"median {np.median(env):.3f}, q90 {np.quantile(env, .9):.3f}, "
      f"q99 {np.quantile(env, .99):.3f}, max {env.max():.3f}")
print(f"    P(max > 3) = {np.mean(env > 3):.4f}   [hash value 1]")

resid = lam_all[:, NMIN:NMAX + 1] - mu[None, NMIN - 1:NMAX]
nn = np.arange(NMIN, NMAX + 1)
C = np.cos(np.outer(nn, THETAS))                       # (31 windows, thetas)
# ERRATUM (2026-09-03, fixed in heat59b after two crashes; draws unaffected -- the
# checkpoint .npy held all 2000 draws before the first crash): the detector must
# slice BOTH operands, and the per-theta amplitudes must NOT be summed over theta
# (the design doc pre-registers "maximized over theta"). Original never-executed
# lines were `resid @ C[:16]` (shape error) and `.sum(axis=1)` on |A2|,|A1|
# (collapses the frequency resolution). See heat59b_complete_stats.py.
A1 = resid[:, : NMID - NMIN + 1] @ C[: NMID - NMIN + 1]   # window 1: n = 30..45
A2 = resid[:, NMID - NMIN:] @ C[NMID - NMIN:]             # window 2: n = 45..60
a2m, a1m = np.abs(A2), np.abs(A1)
with np.errstate(divide="ignore", invalid="ignore"):
    alpha = np.where(a1m > 0, (1.0 / (NMAX - NMID)) * np.log(np.maximum(a2m, 1e-300) / np.maximum(a1m, 1e-300)), 0.0)
amax_per_draw = alpha.max(axis=1)
print(f"[2] growth detector alpha_hat(theta) max over theta, n in [{NMIN},{NMAX}]:")
print(f"    median {np.median(amax_per_draw):+.4f}, q95 {np.quantile(amax_per_draw, .95):+.4f}, "
      f"q99 {np.quantile(amax_per_draw, .99):+.4f}, max {amax_per_draw.max():+.4f}   [hash value 2]")

lag1 = np.array([np.corrcoef(r[:-1], r[1:])[0, 1] for r in resid[:500]])
print(f"[3] lag-1 residual correlation: median {np.median(lag1):+.4f} "
      f"(q05 {np.quantile(lag1,.05):+.4f}, q95 {np.quantile(lag1,.95):+.4f})   [hash value 3]")

with open("heat59_gue_lambda_ensemble.results.pkl", "wb") as f:
    pickle.dump({"mu": mu, "sd": sd, "env": env, "alpha_max": amax_per_draw,
                 "lag1": lag1, "NCUE": NCUE, "M": M, "T_max": T_max, "K": K,
                 "seed": 20260903, "NN": NN}, f)
print("\nsaved heat59_gue_lambda_ensemble.results.pkl (hash target)")
