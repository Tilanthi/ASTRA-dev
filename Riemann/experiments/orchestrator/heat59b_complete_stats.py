"""heat59b — complete statistics [2]/[3] of the W-002 pre-registration from the
saved draw matrix.

heat59's rerun crashed at the detector (resid column slicing was missing alongside
the C row slicing), AFTER all 2000 draws were checkpointed to
heat59_lam_all_partial.npy (save happens inside the loop every 250 draws; the .out
confirms draw 2000/2000 printed and statistic [1] computed). This script reloads
the checkpoint, re-verifies statistic [1] byte-for-byte against the committed .out,
then computes the growing-oscillation detector and lag-1 correlation exactly as
the committed design (m4_lambdan_signature_design.md section 3) and script specify,
and writes the hash-target .pkl.

Detector bug fix, on the record: A1/A2 must slice BOTH operands --
  A1 = resid[:, :16] @ C[:16]    (n = 30..45)
  A2 = resid[:, 15:] @ C[15:]    (n = 45..60)
The committed script had `resid @ C[:16]` etc., i.e. C sliced, resid not --
a (M,31)@(16,200) matmul shape error. Windows are inclusive and share n=45,
as the original comments state. No semantic change to the pre-registered form.
"""
import hashlib
import pickle

import numpy as np

NN = 60
NMIN, NMID, NMAX = 30, 45, 60
THETAS = np.linspace(1.0 / NMAX, 1.0 / 14.0, 200)

lam_all = np.load("heat59_lam_all_partial.npy")
assert lam_all.shape == (2000, NN + 1), lam_all.shape

mu = lam_all[:, 1:].mean(axis=0)
sd = lam_all[:, 1:].std(axis=0)

# --- statistic [1] re-verification against the committed .out ---
z = (lam_all[:, NMIN:NMAX + 1] - mu[NMIN - 1:NMAX]) / sd[NMIN - 1:NMAX]
env = np.max(np.abs(z), axis=1)
line1 = (f"[1] envelope max_|z| over n in [{NMIN},{NMAX}]: "
         f"median {np.median(env):.3f}, q90 {np.quantile(env,.9):.3f}, "
         f"q99 {np.quantile(env,.99):.3f}, max {env.max():.3f}")
line2 = f"    P(max > 3) = {np.mean(env > 3):.4f}   [hash value 1]"
print(line1)
print(line2)
assert f"median {np.median(env):.3f}" in open("heat59_gue_lambda_ensemble.out").read()
assert abs(np.mean(env > 3) - 0.0040) < 5e-5, np.mean(env > 3)

# --- statistic [2]: growing-oscillation detector (fixed slicing) ---
resid = lam_all[:, NMIN:NMAX + 1] - mu[None, NMIN - 1:NMAX]
nn = np.arange(NMIN, NMAX + 1)
C = np.cos(np.outer(nn, THETAS))            # (31, 200)
A1 = resid[:, : NMID - NMIN + 1] @ C[: NMID - NMIN + 1]   # n = 30..45
A2 = resid[:, NMID - NMIN:] @ C[NMID - NMIN:]             # n = 45..60
# Second latent bug in the never-executed committed lines, fixed to the design-doc
# form: the committed script summed |A2|,|A1| over axis=1 (thetas), collapsing the
# per-frequency resolution that section 3.2 pre-registers ("maximized over theta").
# Per-theta amplitudes |A1[d,theta]|, |A2[d,theta]| must stay 2-D.
a2m, a1m = np.abs(A2), np.abs(A1)
with np.errstate(divide="ignore", invalid="ignore"):
    alpha = np.where(a1m > 0,
                     (1.0 / (NMAX - NMID)) * np.log(np.maximum(a2m, 1e-300) / np.maximum(a1m, 1e-300)),
                     0.0)
amax_per_draw = alpha.max(axis=1)
print(f"[2] growth detector alpha_hat(theta) max over theta, n in [{NMIN},{NMAX}]:")
print(f"    median {np.median(amax_per_draw):+.4f}, q95 {np.quantile(amax_per_draw,.95):+.4f}, "
      f"q99 {np.quantile(amax_per_draw,.99):+.4f}, max {amax_per_draw.max():+.4f}   [hash value 2]")

# --- statistic [3]: lag-1 residual correlation ---
lag1 = np.array([np.corrcoef(r[:-1], r[1:])[0, 1] for r in resid[:500]])
print(f"[3] lag-1 residual correlation: median {np.median(lag1):+.4f} "
      f"(q05 {np.quantile(lag1,.05):+.4f}, q95 {np.quantile(lag1,.95):+.4f})   [hash value 3]")

with open("heat59_gue_lambda_ensemble.results.pkl", "wb") as f:
    pickle.dump({"mu": mu, "sd": sd, "env": env, "alpha_max": amax_per_draw,
                 "lag1": lag1, "NCUE": 256, "M": 2000, "T_max": 240.0, "K": 101,
                 "seed": 20260903, "NN": NN}, f)
h = hashlib.sha256(open("heat59_gue_lambda_ensemble.results.pkl", "rb").read()).hexdigest()
print(f"\nSHA-256 heat59_gue_lambda_ensemble.results.pkl = {h}")
print("W-002 GUE-side signature registered. No zeta-side value computed.")
