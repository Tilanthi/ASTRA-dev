#!/usr/bin/env python3
# heat78d: analysis of the scored census JSON (heat78c_census_result.json) -> m1-L165 fill tables.
# Reads the raw JSON only; class assignment + prediction scoring per frozen m1-L158 e926548.
# No compute beyond table assembly. VERIFIED-HERE labels attach to numbers read from the JSON.
import json, sys

OUTJ = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat78c_census_result.json"
DELTAS = ["0.05", "0.1", "0.2", "0.3", "0.45"]

# first 25 zeta zero ordinates (standard, for gamma0 height + gap width ordering)
Z = [14.13472514173469, 21.02203963877155, 25.01085758014586, 30.42487612585951,
     32.93506158773919, 37.58617815882567, 40.91871901214750, 43.32707328091400,
     48.00515088116716, 49.77383247767230, 52.97030381358059, 56.44624369483810,
     59.34704400260275, 60.83177852442857, 65.11254404828464, 67.07981052949418,
     69.54640171117400, 72.06715767448189, 75.65403532594610, 77.14484006887490,
     79.33749319030000, 82.91044054346019, 84.73548532821479, 87.42527319002310,
     88.76557942908868, 92.49185527071328]

with open(OUTJ) as fh:
    R = json.load(fh)

status, nfire, flips = R["status"], R["n_fire"], R["flips"]
res = R["results"]
print("status", status, " n_fire", nfire, " n_flips", len(flips), " wall %.0fs" % R["wall_seconds"])

# ---- outcome class per L158 par.3
disp8  = [v for key, v in res.items() if key.startswith("8/") and "fires" in v]
disp64 = [v for key, v in res.items() if key.startswith("64/") and "fires" in v]
f8  = sum(1 for v in disp8 if v["fires"])
f64 = sum(1 for v in disp64 if v["fires"])
print("displaced cells scored: M8 %d (fires %d), M64 %d (fires %d)" % (len(disp8), f8, len(disp64), f64))
if status.get("8") == "RED" or status.get("64") == "RED":
    print("CLASS: control RED at", {m: status[m] for m in status if status[m] == "RED"}, "-> that M unscored (L158 rule)")
elif f8 == len(disp8):
    print("CLASS (a): ALL displaced fire at M8")
elif len(flips) > 0:
    print("CLASS (b1): non-empty M64 flip set (%d flips)" % len(flips))
else:
    print("CLASS (b2): empty flip set — k=0-concentration statement territory")

# ---- prediction 1: flip delta_c per k ordered by gamma0 height vs gap width
# delta_c(k, phi) = smallest delta in ladder where a flip occurs for that (k, phi)
armA = [(k, 4) for k in range(25)]
armB = [(k, p) for k in range(8) for p in (2, 6)]
dmin = {}
for fl in flips:
    kk = (fl["k"], fl["phi8"])
    if kk not in dmin or DELTAS.index(fl["delta"]) < DELTAS.index(dmin[kk]):
        dmin[kk] = fl["delta"]
if flips:
    print("\n-- prediction 1 (height-ordering): delta_c per (k,phi) with flips")
    rows = sorted(dmin.items(), key=lambda kv: kv[0])
    for (k, phi), d in rows:
        print("  k=%2d phi=%d/8  delta_c=%s  gamma0=%.3f  gap=%.4f" %
              (k, phi, d, Z[k], Z[k+1] - Z[k]))
    # arm-A-only Spearman check delta_c index vs gamma0 vs gap
    aak = sorted([(Z[k], Z[k+1]-Z[k], DELTAS.index(d), k) for (k, phi), d in dmin.items() if phi == 4])
    if len(aak) >= 3:
        def rank(xs):
            order = sorted(range(len(xs)), key=lambda i: xs[i]); rk = [0]*len(xs)
            for r, i in enumerate(order): rk[i] = r
            return rk
        di = rank([r[2] for r in aak]); gr = rank([r[0] for r in aak]); gp = rank([r[1] for r in aak])
        def spear(a, b):
            n = len(a); return 1 - 6*sum((a[i]-b[i])**2 for i in range(n))/(n*(n*n-1))
        print("  Spearman(delta_c, gamma0)=%.2f  Spearman(delta_c, gap)=%.2f  (n=%d, arm A)" %
              (spear(di, gr), spear(di, gp), len(aak)))
else:
    print("\n-- prediction 1: VACUOUS (empty flip set)")

# ---- prediction 2: flip typing
if flips:
    types = {}
    for fl in flips: types[fl["type"]] = types.get(fl["type"], 0) + 1
    print("\n-- prediction 2 (typing):", types, "(descent / reorganization / mixed counts)")
    small = [fl for fl in flips if fl["delta"] in ("0.05", "0.1")]
    print("   small-delta (0.05/0.1) flips: %d; their types:" % len(small),
          {t: sum(1 for fl in small if fl['type']==t) for t in ('descent','reorganization','mixed')})

# ---- prediction 3: M64 lambda_min distribution (plateau two-way)
if disp64:
    lams = sorted(float(v["lam_min"]) for v in disp64)
    n = len(lams)
    print("\n-- prediction 3 (plateau): M64 displaced lambda_min distribution")
    print("   min %.3e  q25 %.3e  median %.3e  q75 %.3e  max %.3e" %
          (lams[0], lams[n//4], lams[n//2], lams[3*n//4], lams[-1]))
    b1e8 = sum(1 for x in lams if 1e-10 <= x <= 1e-8); b1e5 = sum(1 for x in lams if x > 1e-6)
    print("   count in [1e-10, 1e-8] (floor-reading band): %d/%d ;  count > 1e-6 (coupling band): %d/%d" %
          (b1e8, n, b1e5, n))
    lams8 = sorted(float(v["lam_min"]) for v in disp8)
    print("   [M8 reference] min %.3e median %.3e max %.3e" % (lams8[0], lams8[len(lams8)//2], lams8[-1]))

# ---- fires-map for the letter tables (arm A k=0..24 phi=4)
print("\n-- arm A fires map (rows k, cols delta; F=fires, .=no; upper=M8 lower=M64)")
for arm, mm in (("M8", "8"), ("M64", "64")):
    print("  %s:" % arm)
    for k in range(25):
        row = []
        for d in DELTAS:
            v = res.get("%s/%d/4/%s" % (mm, k, d))
            row.append("F" if (v and v["fires"]) else ".")
        print("   k=%2d %s" % (k, "".join(row)))
print("\n-- arm B fires map (phi=2/8 and 6/8)")
for arm, mm in (("M8", "8"), ("M64", "64")):
    print("  %s (phi=2 left, phi=6 right per cell pair):" % arm)
    for k in range(8):
        row = []
        for p in (2, 6):
            for d in DELTAS:
                v = res.get("%s/%d/%d/%s" % (mm, k, p, d))
                row.append("F" if (v and v["fires"]) else ".")
        print("   k=%d %s" % (k, "".join(row)))

# ---- disclosed-cell confirmation (34 cells: arm A k=0..24 @ 0.1; k in {1,2,9} @ 0.2,0.3,0.45)
print("\n-- disclosed-cell M8 confirmation vs m3-L158/159 (fires bit only here; values in JSON)")
conf = [(k, "0.1") for k in range(25)] + [(k, d) for k in (1, 2, 9) for d in ("0.2", "0.3", "0.45")]
mism = [(k, d, res.get("8/%d/4/%s" % (k, d))) for (k, d) in conf
        if res.get("8/%d/4/%s" % (k, d)) and res["8/%d/4/%s" % (k, d)]["fires"]]
print("   disclosed M8 cells that FIRE in tonight's run:", mism if mism else "NONE (consistent with m3's non-firing disclosures)")
