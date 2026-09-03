"""heat56 — RELATIVE-ERROR re-scoring of the Part-B gate.

This is a POST-HOC re-scoring, not a blind gate, and the letter says so:
every value here has already been seen by all three parties. What makes it
honest is that the METRIC and the TARGET WIDTHS are the counterparty's own
proposal (machine2-reply-to-partB-gate §3: "gate on relative error against
a declared target s.f."; honest widths k3 4 s.f. / k4 6 / k5 6 as a column
with Lehmer and telescope 9-10 individually / k6 9). We choose no threshold.

Per cell:
  rel   = |b - c| / |c|          b = BEAST corrected column (parsed from the
                                 committed relay 0ea87ad, trap #63),
                                 c = T2h certified plain column.
  gate  PASS iff rel <= 10^(-target_sf).
  Also print the OLD absolute-units verdict (|b-c| vs 10^-(quoted digits),
  >10 units = BEYOND) so the raw verdicts and the re-scoring sit in one
  table — the separation BEAST asked for as the second option; we deliver
  both, and adopt the first as the standing gate.
Carried s.f. = floor(-log10(rel)) + 1 (logarithmic convention, stated).
"""
import re
import subprocess
import json
import mpmath as mp

mp.mp.dps = 60
GIT = ["git", "-C", "/Users/gjw255/astrodata/SWARM/Riemann_exchange",
       "show", "0ea87ad:machine2-CORRECTED-kappa-tables-2026-09-02-RELAY-BY-astra-pa.md"]
RAW = subprocess.run(GIT, capture_output=True, text=True, check=True).stdout
LINES = RAW.splitlines()
SITES = ["k453", "k693", "k922", "k1166", "Lehmer", "telescope"]
BOLDNUM = re.compile(r"\*\*([−+]?[\d.]+)\*\*")

def row_of(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

def extract(site, header_key):
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

parsed = {}
for site in SITES:
    parsed[site] = dict(
        k3=extract(site, "κ₃ (plain)"), k5=extract(site, "κ₅ (plain)"),
        k4=extract(site, "κ₄ and κ₆"), k6=extract(site, "κ₄ and κ₆"))
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

T2H = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
                     "T2h_certified_identity_gated.json"))

# BEAST-declared honest widths (their §3 W1 table). Lehmer and telescope k5
# carry 9 s.f. individually (their words), so target 9 there.
TARGET = {("k3", s): 4 for s in SITES}
TARGET.update({("k4", s): 6 for s in SITES})
TARGET.update({("k5", s): 6 for s in SITES})
TARGET.update({("k5", "Lehmer"): 9, ("k5", "telescope"): 9})
TARGET.update({("k6", s): 9 for s in SITES})

print("== heat56: relative-error re-scoring (metric + widths: BEAST §3 proposal) ==")
print("   carried sf = floor(-log10 rel) + 1; PASS iff rel <= 10^-target")
rows = []
tally = {}
for site in SITES:
    t = T2H[site]
    for k, key in (("k3", "kappa3_plain"), ("k5", "kappa5_plain"),
                   ("k4", "kappa4_plain"), ("k6", "kappa6_plain")):
        b = mp.mpf(parsed[site][k].replace("−", "-"))
        c = mp.mpf(t[key])
        rel = abs(b - c)/abs(c)
        tgt = TARGET[(k, site)]
        qd = len(parsed[site][k].split(".")[1])
        units = abs(b - c)/mp.mpf(10)**(-qd)
        old = "BEYOND" if units > 10 else "pass"
        carried = int(mp.floor(-mp.log10(rel) if rel > 0 else mp.mpf(30))) + 1
        new = "PASS" if rel <= mp.mpf(10)**(-tgt) else "FAIL"
        tally.setdefault(k, []).append(new)
        rows.append(dict(site=site, col=k, quoted=parsed[site][k],
                         rel=float(rel), target_sf=tgt, carried_sf=carried,
                         old_units_verdict=old, new_verdict=new))
        print(f"  {site:10s} {k}: rel={mp.nstr(rel, 3):>9s}  carried~{carried:2d} sf  "
              f"target {tgt} -> {new:4s}   (old abs-units: {old})")

print()
for k in ("k3", "k5", "k4", "k6"):
    npass = sum(1 for v in tally[k] if v == "PASS")
    print(f"  column {k}: {npass}/6 PASS at BEAST's declared width")
print("\nold gate (abs units >10): %s" %
      {k: sum(1 for r in rows if r["col"] == k and r["old_units_verdict"] == "BEYOND")
       for k in ("k3", "k5", "k4", "k6")})
json.dump(rows, open("heat56_relative_gate.results.json", "w"), indent=1)
print("persisted heat56_relative_gate.results.json")
