"""heat51e — THE d-LAW: even-order companion of the eps-law, closing
  BEAST's "d-precision effect" (their corrected-tables relay §3, kappa6
  Lehmer 1.48e-6 offset) as a closed form. [law corrected after the
  first run: sign is MINUS, matching the eps-law; the initial draft's
  + sign and jet/plain comparison slip were caught by the E1 ratio
  -1/720 — trap #50/#60 discipline, emitter fixed not table]

  LAW (clean derivation): f(z) = ln[Xi(m0+z)/(z^2-d_m^2)], d_m = d+delta.
  Residual vs true: Delta = ln(z^2-d^2) - ln(z^2-d_m^2)
                     ~ +2*d*delta/(z^2-d^2) = delta*[1/(z-d)-1/(z+d)]
                     = -2*delta*SUM_{k even} z^k d^(-k-1)
  (1/(z-d) = -SUM z^k d^-k-1; 1/(z+d) = +SUM (-1)^k z^k d^-k-1;
  difference cancels odd k).  So
      kappa_j(m0, d+delta) = kappa_j(m0, d) - 2*delta/d^(j+1)  (EVEN j)
  while ODD j are clean at O(delta) — exactly complementary to the
  eps-law (odd j shift by -2*eps/d^(j+1); even j clean at O(eps)).
  UNIFIED:  Delta kappa_j = -2*u_j/d^(j+1)  with u_j = eps (odd j),
  delta (even j) — parity selects which input error is ultraviolet.
  mp.taylor returns PLAIN coefficients t_k (a_k = k!*t_k).

  CHECKS (this run):
    E1  ladder: delta in {+-1e-18, +-5e-19} at exact Lehmer site ->
        t6 moves by -2*delta/d^7 (linear), t5 UNMOVED (odd), t2 moves
        by -2*delta/d^3.
    E2  machine 3's old T2g Lehmer column through BOTH laws: kappa3
        offset (odd) -> eps-law with eps = m0_T2g - m0_true; kappa6
        offset (even) -> d-law with delta = d_T2g - d_true.
    E3  float64 forensics: is d_T2g == float64(d_true)? is m0_T2g ==
        float64(m0_true)?
"""
import json
import mpmath as mp

mp.mp.dps = 50

def make_f(m0, d):
    def f(z, m0=m0, d=d):
        s = mp.mpf('0.5') + 1j*(m0+z)
        Xi = mp.mpf('0.5')*s*(s-1)*mp.power(mp.pi, -s/2)*mp.gamma(s/2)*mp.zeta(s)
        return mp.log(Xi/(z**2-d**2))
    return f

z1 = mp.zetazero(6709); z2 = mp.zetazero(6710)
m0 = (z1.imag+z2.imag)/2
d = (z2.imag-z1.imag)/2
print(f"Lehmer site: m0 = {mp.nstr(m0, 24)}  d = {mp.nstr(d, 12)}", flush=True)
print(f"d^7 = {mp.nstr(mp.power(d, 7), 6)}   2*720/d^7 = "
      f"{mp.nstr(2*720/mp.power(d, 7), 6)} per unit delta (a6 gain)", flush=True)

print("\nE1: d-ladder at exact m0 (PLAIN t_k; odd j clean under d-shift)",
      flush=True)
base = mp.taylor(make_f(m0, d), 0, 6)
for dl in (mp.mpf('1e-18'), -mp.mpf('1e-18'), mp.mpf('5e-19')):
    ct = mp.taylor(make_f(m0, d+dl), 0, 6)
    pred6 = -2*dl/mp.power(d, 7)
    pred2 = -2*dl/mp.power(d, 3)
    print(f"  delta={mp.nstr(dl, 2)}: t6 shift obs {mp.nstr(ct[6]-base[6], 4)}"
          f" pred {mp.nstr(pred6, 4)} ratio {mp.nstr((ct[6]-base[6])/pred6, 4)} | "
          f"t5 shift {mp.nstr(ct[5]-base[5], 2)} (law: 0) | "
          f"t2 shift obs {mp.nstr(ct[2]-base[2], 3)} pred {mp.nstr(pred2, 3)}",
      flush=True)

print("\nE2: machine 3 old-T2g Lehmer offsets through BOTH laws", flush=True)
old = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
                     "T2g_kappa5_coefficients.json"))["sites"]["Lehmer"]
new = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
                     "T2h_certified_identity_gated.json"))["Lehmer"]
m0_old = mp.mpf(old["m0"]); d_old = mp.mpf(old["d"])
eps_obs = m0_old - m0                       # site error (odd-j law input)
dl_obs = d_old - d                          # stored-d error
# kappa3: odd j -> eps-law  d kappa3_plain = -2*eps/d^4
k3_old = mp.mpf(old["plain"]["kappa3"])
k3_new = mp.mpf(new["kappa3_plain"])
k3_off = k3_old - k3_new
k3_pred = -2*eps_obs/mp.power(d, 4)
print(f"  eps = m0_T2g - m0_true = {mp.nstr(eps_obs, 4)}", flush=True)
print(f"  kappa3 offset obs {mp.nstr(k3_off, 4)}  eps-law pred "
      f"{mp.nstr(k3_pred, 4)}  ratio {mp.nstr(k3_off/k3_pred, 6)}", flush=True)
# kappa6: even j -> d-law  d kappa6_plain = +2*delta/d^7
k6_old = mp.mpf(old["plain"]["kappa6"])
k6_new = mp.mpf(new["kappa6_plain"])
k6_off = k6_old - k6_new
k6_pred_stored = -2*dl_obs/mp.power(d, 7)
delta_from_law = -k6_off*mp.power(d, 7)/2
print(f"  stored d offset = {mp.nstr(dl_obs, 3)} (T2g d vs true d)", flush=True)
print(f"  kappa6 offset obs {mp.nstr(k6_off, 4)}  d-law pred from stored d "
      f"{mp.nstr(k6_pred_stored, 4)}  ratio {mp.nstr(k6_off/k6_pred_stored, 6)}",
      flush=True)
print(f"  d-law: delta implied by kappa6 offset = {mp.nstr(delta_from_law, 4)}",
      flush=True)
print("E3: float64 candidates for the implied delta", flush=True)
f64_d = mp.mpf(float(d))
print(f"  float64(d)-d = {mp.nstr(f64_d-d, 4)}", flush=True)
z1f = float(z1.imag); z2f = float(z2.imag)
f64_d2 = mp.mpf((z2f-z1f)/2)
print(f"  float64((z2-z1)/2)-d = {mp.nstr(f64_d2-d, 4)}", flush=True)
f64_m0 = mp.mpf(float(m0))
print(f"  float64(m0)-m0 = {mp.nstr(f64_m0-m0, 4)}  (vs eps "
      f"{mp.nstr(eps_obs, 4)})", flush=True)
print("\nE4: second-site ladder at telescope (h=71732.9, d=0.00735 — the"
      "\n    d^-7 gain is ~1000x Lehmer's; delta rescaled to 1e-21)",
      flush=True)
import json
t2h = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
                     "T2h_certified_identity_gated.json"))
tel = t2h["telescope"]
m0t = mp.mpf(tel["m0"]); dt = mp.mpf(tel["d"])
print(f"  telescope m0 = {mp.nstr(m0t, 14)}  d = {mp.nstr(dt, 12)}  "
      f"2/d^7 = {mp.nstr(2/mp.power(dt, 7), 4)} per unit delta", flush=True)
baset = mp.taylor(make_f(m0t, dt), 0, 6)
for dl in (mp.mpf('1e-21'), -mp.mpf('1e-21')):
    ct = mp.taylor(make_f(m0t, dt+dl), 0, 6)
    pred6 = -2*dl/mp.power(dt, 7)
    print(f"  delta={mp.nstr(dl, 2)}: t6 shift obs {mp.nstr(ct[6]-baset[6], 4)}"
          f" pred {mp.nstr(pred6, 4)} ratio {mp.nstr((ct[6]-baset[6])/pred6, 4)}"
          f" | t5 shift {mp.nstr(ct[5]-baset[5], 2)} (law: 0)", flush=True)
print("done", flush=True)
