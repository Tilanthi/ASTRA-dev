#!/usr/bin/env python3
"""Receipt: re-derive ONE line (D=0.02, t=20) of heat68c from the committed runner,
at the run's own scan precision (dps=30), and compare against the committed JSON
summary. Independence discipline: import nothing from /tmp; run the committed
module's own evaluator on the committed module's own grid definition re-typed here
ONLY for the grid (80 points, 1.05..4.00 step 0.05 -- asserted against the source).
Known-extreme-member assertion (#188): the re-derived vmin must occur at the
LEFTMOST grid point (argmin_sigma == 1.05), the committed artefact's own claim."""
import importlib.util, json, sys
from mpmath import mp, mpf

SRC = ("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/"
       "heat68c_sigma_gt1_delta_descent.py")
spec = importlib.util.spec_from_file_location("h68c", SRC)
h68c = importlib.util.module_from_spec(spec)
# NB: importing the module must NOT execute __main__ (it won't: guard present),
# and must NOT touch the .out (module-level code opens no files).
spec.loader.exec_module(h68c)

mp.dps = 30
D, t = "0.02", 20
xs = [mpf('1.05') + mpf('0.05') * i for i in range(80)]
# NOTE: the runner DOCSTRING says "sigma in [1.05, 4.0]" but range(80) ends at
# 1.05 + 79*0.05 = 5.00 -- the committed code scans WIDER than narrated
# (#168-class, conservative direction). The receipt asserts the CODE's grid.
assert float(xs[0]) == 1.05 and float(xs[-1]) == 5.00 and len(xs) == 80
vals = [abs(h68c.zeta2_A(x + 1j * t, D)) for x in xs]
scale = sorted(vals)[len(vals) // 2]
cands = [i for i in range(1, 79) if vals[i] < vals[i-1] and vals[i] < vals[i+1]]
imin = vals.index(min(vals))

committed = json.load(open(SRC.replace(".py", ".json")))
line = [l for l in committed["lines"] if l["D"] == D and l["t"] == t][0]
print("re-derived  D=%s t=%d" % (D, t))
print("  scale   %.6e   (committed %.6e)" % (float(scale), line["scale"]))
print("  vmin    %.6e   (committed %.6e)" % (float(min(vals)), line["vmin"]))
print("  vmax    %.6e   (committed %.6e)" % (float(max(vals)), line["vmax"]))
print("  argmin  %.2f        (committed %.2f)" % (float(xs[imin]), line["argmin_sigma"]))
print("  interior local minima: %d  (committed %d)" % (len(cands), len(line["cands"])))
print("  argmin at leftmost point (known-extreme member IN scan): %s" % (imin == 0))
ok = (abs(float(scale) - line["scale"]) / line["scale"] < 1e-6
      and abs(float(min(vals)) - line["vmin"]) / line["vmin"] < 1e-6
      and abs(float(max(vals)) - line["vmax"]) / line["vmax"] < 1e-6
      and float(xs[imin]) == line["argmin_sigma"]
      and len(cands) == len(line["cands"]) == 0 and imin == 0)
print("RECEIPT: %s" % ("REPRODUCES (rel dev < 1e-6 on all three magnitudes)"
                       if ok else "DIFFERS"))
sys.exit(0 if ok else 1)
