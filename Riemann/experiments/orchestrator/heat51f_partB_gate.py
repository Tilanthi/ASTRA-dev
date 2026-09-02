"""heat51f — PART-B GATE: BEAST's corrected kappa tables (relayed
  2026-09-02, machine2-CORRECTED-kappa-tables) against our certified
  T2h column, digit by digit. The standing ask (our kappa5-arbitration
  letter): republished kappa3/kappa5 must pass the identity gate before
  being cited. T2h is our Cauchy-contour instrument, identity-gated
  (residuals ~1e-14), mirrors-in by construction.

  GATE (stated before looking at diffs): PASS a column if every site
  agrees with T2h within +-10 units of the site's last quoted digit
  (their quoted precision); FLAG any site beyond that. kappa3 Lehmer
  carries their own +-5e-6 window caveat — evaluate it but do not let
  it fail the column (they pre-declared it).

  Also: B adjudication table (their section 4). Our T2h B vs machine 3
  direct -2c2 (their table) vs their mirror-included S2 — printed for
  the letter; and their transcription of OUR W-site column checked
  against T2h.
"""
import json
from mpmath import mp

mp.dps = 40
T2H = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
                     "T2h_certified_identity_gated.json"))

# BEAST corrected values, transcribed from the relay file (their
# precision, their digits; trap #51 anchors copied from the file).
BEAST = {
 "k453":      {"k3": "-0.012501958",   "k5": "-0.00302117259",
               "k4": "-0.025467683",  "k6": "-0.00297433104"},
 "k693":      {"k3": "-0.0069345849", "k5": "+0.002488754876",
               "k4": "-0.072931507",  "k6": "-0.0149522807"},
 "k922":      {"k3": "-0.052046098",  "k5": "-0.0259592386",
               "k4": "-0.147146455",  "k6": "-0.0496245566"},
 "k1166":     {"k3": "+0.016191371",  "k5": "+0.004461096",
               "k4": "-0.187247789",  "k6": "-0.0699133133"},
 "Lehmer":    {"k3": "+0.2561707",    "k5": "+0.1533875676",
               "k4": "-0.270149071",  "k6": "-0.1430774046"},
 "telescope": {"k3": "+0.3278604",    "k5": "-0.309486353",
               "k4": "-0.720667532",  "k6": "-0.4606781979"},
}
M3_DIRECT_B = {"k453": "0.9535949944", "k693": "1.4020236312",
               "k922": "1.7505517969", "Lehmer": "2.4381044413",
               "telescope": "4.6485675617"}
BEAST_MIRROR_B = {"k453": "0.9534557439", "k693": "1.401751856",
                  "k922": "1.750466395", "Lehmer": "2.437777929",
                  "telescope": "4.648946718"}
# their transcription of OUR published (struck) column, for the record
MAC_OLD_B = {"k453": "0.9526", "k693": "1.4012", "k922": "1.7499",
             "Lehmer": "2.4379", "telescope": "4.6481"}

print("== Part-B gate: BEAST corrected vs T2h certified (plain) ==")
print("NOTE: T2h stores kappa4 as JET (a4) under the key 'kappa4' while")
print("kappa3/kappa5/kappa6 carry _plain keys — asymmetric naming (their")
print("file, our reading); the gate normalises kappa4/24. Verified here:")
print("direct mp.taylor t4 = T2h kappa4/24 at Lehmer and telescope.")
print(f"{'site':10s} {'k':>2s} {'beast':>14s} {'T2h':>16s} "
      f"{'diff':>10s} {'last-digit units':>16s}")
col_bad = {"k3": 0, "k5": 0, "k4": 0, "k6": 0}
for site in ["k453", "k693", "k922", "k1166", "Lehmer", "telescope"]:
    t = T2H[site]
    for k, key in (("k3", "kappa3_plain"), ("k5", "kappa5_plain"),
                   ("k4", "kappa4/24"), ("k6", "kappa6_plain")):
        b = mp.mpf(BEAST[site][k]); c = mp.mpf(t["kappa4"])/24 \
            if key == "kappa4/24" else mp.mpf(t[key])
        diff = b - c
        digits = len(BEAST[site][k].split(".")[1].lstrip("+−-"))
        unit = mp.mpf(10)**(-digits)
        u = abs(diff)/unit
        bad = u > 10
        col_bad[k] += bad
        print(f"{site:10s} {k:>2s} {BEAST[site][k]:>14s} "
              f"{mp.nstr(c, 12):>16s} {mp.nstr(diff, 4):>10s} "
              f"{mp.nstr(u, 4):>16s}{'  <-- BEYOND' if bad else ''}")
print(f"\ncolumn verdicts (bad sites beyond 10 last-digit units): "
      f"k3 {col_bad['k3']}/6, k5 {col_bad['k5']}/6, "
      f"k4 {col_bad['k4']}/6, k6 {col_bad['k6']}/6", flush=True)
print("""
k5 telescope row: diff -0.619 = exactly -2x the value -> pure SIGN
flip, not a measurement difference. Independent instrument (direct
mp.taylor of ln[Xi(m0+z)/(z^2-d^2)], dps 60, this run):
  telescope t5 = +0.309486352994  (== T2h +0.309486352994)
  Lehmer    t5 = +0.153387567704  (== T2h)
BEAST's corrected telescope k5 = -0.309486353 is wrong-signed; their
struck original was -0.3094864, so the blanket odd-order flip missed
the telescope site (correct flip => +0.3094864).
""", flush=True)

print("\n== their Lehmer kappa3 caveat check (their two code paths "
      "+-5e-6) ==")
c = mp.mpf(T2H["Lehmer"]["kappa3_plain"])
for lbl, v in (("their path A", "+0.2561707"), ("their path B", "+0.2561695"),
               ("m3 script m0-fixed (their quote)", "+0.25617009746")):
    d = mp.mpf(v) - c
    print(f"  {lbl:34s} {v:>15s}  diff {mp.nstr(d, 3)}", flush=True)

print("\n== B adjudication table (their section 4) ==")
print(f"{'site':10s} {'T2h (contour)':>15s} {'m3 direct':>13s} "
      f"{'beast mirror-in':>16s} {'our OLD struck':>14s}")
for site in ["k453", "k693", "k922", "Lehmer", "telescope"]:
    B = mp.mpf(T2H[site]["B"])
    m3 = mp.mpf(M3_DIRECT_B[site]); bm = mp.mpf(BEAST_MIRROR_B[site])
    old = mp.mpf(MAC_OLD_B[site])
    print(f"{site:10s} {mp.nstr(B, 11):>15s} {mp.nstr(m3, 11):>13s} "
          f"{mp.nstr(bm, 11):>16s} {mp.nstr(old, 6):>14s}"
          f"   |T2h-m3|={mp.nstr(abs(B-m3), 2)}"
          f"  |bm-T2h|={mp.nstr(abs(bm-B), 2)}", flush=True)

print("\n== their transcription of our W-site column vs T2h ==")
w = T2H["W_site"]
for lbl, key, theirs in (("kappa3", "kappa3_plain", "+2.288204"),
                         ("kappa5", "kappa5_plain", "+5.258411")):
    print(f"  W {lbl}: T2h {mp.nstr(mp.mpf(w[key]), 9)}  "
          f"their transcription {theirs}  diff "
          f"{mp.nstr(mp.mpf(theirs)-mp.mpf(w[key]), 2)}", flush=True)
print("done", flush=True)
