"""heat51h — GATE AUDIT + re-run, after the telescope kappa5 sign defect
  was traced to OUR hand-typed transcription dictionary (trap #51
  violation inside the very script that claimed to follow it).

  FACTS (git, this run): the relay file at commit 0ea87ad, line 82,
  reads '+0.309486353' at telescope kappa5 — single commit, never
  modified. Our heat51f BEAST dict carried '-0.309486353'. BEAST's
  corrected column was RIGHT at all six sites; our 'wrong-signed
  telescope' letter claim (machine1-partB-gate-and-dlaw.md section 2)
  was a false defect manufactured by our own transcription.

  This script:
    A1  parse EVERY value of the relay file's four kappa tables + B
        table straight from `git show 0ea87ad:<file>` (no hand-typing);
    A2  diff parsed vs our hand dict cell by cell — enumerate ALL
        transcription errors, not just the known one;
    A3  re-run the Part-B gate with parsed values only.
    H1  verify BEAST's cycle-8 H1 even-channel law ourselves at Lehmer,
        dps 100:  D kappa_n(eps) = (n+1)*kappa_{n+1}*eps + O(eps^2)
        from non-pair zeros, for n=2,4,6 — the law that supersedes our
        'even j clean at O(eps)' phrasing.
    X1  verify the delta->odd exact identity (machine 3 letter 16):
        at delta/d = 1% and 5%, D kappa_3 = D kappa_5 = 0 to machine
        zero (divisor even in z => ALL odd coefficients delta-free).
"""
import re
import subprocess
import mpmath as mp

mp.mp.dps = 100 if False else 60   # A/H/X blocks run at dps 60; H at 100 needs longer
GIT = ["git", "-C", "/Users/gjw255/astrodata/SWARM/Riemann_exchange",
       "show", "0ea87ad:machine2-CORRECTED-kappa-tables-2026-09-02-RELAY-BY-astra-pa.md"]
RAW = subprocess.run(GIT, capture_output=True, text=True, check=True).stdout
LINES = RAW.splitlines()

SITES = ["k453", "k693", "k922", "k1166", "Lehmer", "telescope"]

def row_of(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

BOLDNUM = re.compile(r"\*\*([−+]?[\d.]+)\*\*")

def extract(site, header_key):
    """find the table row for site in the section whose header mentions
    header_key; return the CORRECTED column (bold numeric, not the
    struck ~~..~~ cell whose [WITHDRAWN] tag is also bold)."""
    in_sec = False
    for ln in LINES:
        if ln.startswith("## "):
            in_sec = header_key in ln
            continue
        if in_sec and ln.startswith("|") and ln.strip("|").strip().startswith(site):
            m = BOLDNUM.search(ln)
            if m:
                return m.group(1)
            cells = row_of(ln)
            return re.sub(r"[~*]", "", cells[1]).strip()
    return None

print("== A1: values parsed from the committed file (0ea87ad) ==")
parsed = {}
for site in SITES:
    parsed[site] = dict(
        k3=extract(site, "κ₃ (plain)"), k5=extract(site, "κ₅ (plain)"),
        k4=extract(site, "κ₄ and κ₆"), k6=extract(site, "κ₄ and κ₆"))
# kappa4/kappa6 are two plain columns of one row in section 3
for site in SITES:
    in_sec = False
    for ln in LINES:
        if ln.startswith("## "):
            in_sec = "κ₄ and κ₆" in ln
            continue
        if in_sec and ln.startswith("|") and ln.strip("|").strip().startswith(site):
            cells = row_of(ln)
            parsed[site]["k4"] = cells[1].strip()
            parsed[site]["k6"] = cells[2].strip()
            break
for site in SITES:
    print(f"  {site:10s} k3={parsed[site]['k3']:>15s} k5={parsed[site]['k5']:>16s} "
          f"k4={parsed[site]['k4']:>13s} k6={parsed[site]['k6']:>15s}")

print("\n== A2: parsed vs OUR hand-typed heat51f dict (all cells) ==")
OURS = {
 "k453":      {"k3": "-0.012501958",   "k5": "-0.00302117259", "k4": "-0.025467683",  "k6": "-0.00297433104"},
 "k693":      {"k3": "-0.0069345849", "k5": "+0.002488754876", "k4": "-0.072931507",  "k6": "-0.0149522807"},
 "k922":      {"k3": "-0.052046098",  "k5": "-0.0259592386", "k4": "-0.147146455",  "k6": "-0.0496245566"},
 "k1166":     {"k3": "+0.016191371",  "k5": "+0.004461096", "k4": "-0.187247789",  "k6": "-0.0699133133"},
 "Lehmer":    {"k3": "+0.2561707",    "k5": "+0.1533875676", "k4": "-0.270149071",  "k6": "-0.1430774046"},
 "telescope": {"k3": "+0.3278604",    "k5": "-0.309486353", "k4": "-0.720667532",  "k6": "-0.4606781979"},
}
nerr = 0
for site in SITES:
    for k in ("k3", "k5", "k4", "k6"):
        pv, ov = parsed[site][k], OURS[site][k]
        pn = float(pv.replace("−", "-"))
        on = float(ov)
        if pn != on:
            nerr += 1
            print(f"  MISMATCH {site} {k}: committed {pv:>17s} vs our dict {ov:>17s}")
print(f"  transcription errors found: {nerr} (of 24 cells)")

print("\n== A3: gate re-run on PARSED values vs T2h (plain) ==")
import json
T2H = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
                     "T2h_certified_identity_gated.json"))
col_bad = {"k3": 0, "k5": 0, "k4": 0, "k6": 0}
for site in SITES:
    t = T2H[site]
    for k, key in (("k3", "kappa3_plain"), ("k5", "kappa5_plain"),
                   ("k4", "kappa4_plain"), ("k6", "kappa6_plain")):
        b = mp.mpf(parsed[site][k].replace("−", "-"))
        c = mp.mpf(t[key])
        digits = len(parsed[site][k].split(".")[1])
        u = abs(b - c)/mp.mpf(10)**(-digits)
        bad = u > 10
        col_bad[k] += bad
        if bad or site == "telescope":
            print(f"  {site:10s} {k}: committed {parsed[site][k]:>16s} "
                  f"T2h {mp.nstr(c, 10):>13s}  {mp.nstr(u, 4):>9s} units"
                  f"{'  BEYOND' if bad else ''}")
print(f"  column verdicts (>10 units): k3 {col_bad['k3']}/6, k5 {col_bad['k5']}/6, "
      f"k4 {col_bad['k4']}/6, k6 {col_bad['k6']}/6")

print("\n== H1: BEAST's even-channel law, our own check at Lehmer ==")
print("   D kappa_n(eps) = (n+1)*kappa_{n+1}*eps + O(eps^2)  (non-pair zeros)")
z1 = mp.zetazero(6709); z2 = mp.zetazero(6710)
m0 = (z1.imag + z2.imag)/2
d = (z2.imag - z1.imag)/2

def coeffs(m0v, dv):
    def f(z, m0v=m0v, dv=dv):
        s = mp.mpf('0.5') + 1j*(m0v+z)
        Xi = mp.mpf('0.5')*s*(s-1)*mp.power(mp.pi, -s/2)*mp.gamma(s/2)*mp.zeta(s)
        return mp.log(Xi/(z**2 - dv**2))
    return mp.taylor(f, 0, 7)

base = coeffs(m0, d)
for eps in (mp.mpf('1e-13'), mp.mpf('1e-12'), mp.mpf('1e-11')):
    sh = coeffs(m0+eps, d)
    parts = []
    for n, np1 in ((2, 3), (4, 5), (6, 7)):
        obs = (sh[n]-base[n])/eps
        pred = (n+1)*base[np1]
        parts.append(f"k{n}: obs {mp.nstr(obs, 6)} pred {mp.nstr(pred, 6)} "
                     f"ratio {mp.nstr(obs/pred, 4)}")
    print(f"  eps={mp.nstr(eps, 2)}: " + " | ".join(parts), flush=True)

print("\n== X1: delta->odd exact identity (delta/d = 1%, 5%) ==")
for frac in (mp.mpf('0.01'), mp.mpf('0.05')):
    sh = coeffs(m0, d*(1+frac))
    print(f"  delta/d={mp.nstr(frac, 2)}: D kappa_3 = {mp.nstr(sh[3]-base[3], 3)}  "
          f"D kappa_5 = {mp.nstr(sh[5]-base[5], 3)}  (exact identity: ~1e-54..-57 "
          f"machine zero at dps 60)", flush=True)

print("\n== H2: second-order coefficient extraction (two-eps subtraction) ==")
print("   D kappa_n = A_n*eps + B_n*eps^2; A_n = (n+1) kappa_{n+1} (H1),")
print("   B_n = -(n+1)/d^(n+2) (pair curvature, closed form: exact pair")
print("   block -1/k*[(d-eps)^-k + (d+eps)^-k - 2 d^-k], even k). Note:")
print("   first draft of the closed form said -n/d^(n+2), dropping the")
print("   eps^2 term inside the log argument — same slip class as #60.")
sh1 = coeffs(m0 + mp.mpf('1e-13'), d)
sh2 = coeffs(m0 + mp.mpf('1e-12'), d)
e1, e2 = mp.mpf('1e-13'), mp.mpf('1e-12')
for n in (2, 4, 6):
    y1 = (sh1[n]-base[n])/e1
    y2 = (sh2[n]-base[n])/e2
    B = (y2-y1)/(e2-e1)
    A = y1 - B*e1
    print(f"  n={n}: A = {mp.nstr(A, 6)}  H1 pred {mp.nstr((n+1)*base[n+1], 6)}"
          f"  | B = {mp.nstr(B, 4)}  pair pred {mp.nstr(-(n+1)/mp.power(d, n+2), 4)}"
          f"  | eps* = kappa_{n+1}*d^{n+2} = {mp.nstr(base[n+1]*mp.power(d, n+2), 3)}"
          f"  | A/|B| = {mp.nstr(A/abs(B), 2)}", flush=True)
print("done", flush=True)
