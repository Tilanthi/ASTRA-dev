#!/usr/bin/env python3
"""heat74 — machine 1 independent verification of m2 CYCLE 24 (79fa152) + ERRATUM 9.

Sections
  A  node count: replicate m2's gl_nodes code path; degree 7/8/9/10 -> 192/384/768/1536?
  B  widths from genomes (my arithmetic, their breakpoint convention):
       h_max  = max consecutive-breakpoint gap (containers, incl. EMPTY ones)
       eff_exact = measure(panel ∩ union of clipped bump supports)  (exact support, no threshold)
     verify basis 7's widest container is EMPTY; basis 2's failing panel is near-full;
     reproduce their hmax column; compare eff ranking (b1/b7 tied on gamma anyway).
  C  statistics from THEIR breakdown.json (break@deg7 + effmax/hmax):
       Spearman(effmax, gamma_bad), Spearman(hmax, gamma_bad), exact permutation P (8!),
       product laws, external gamma*heff/n at n=192; then re-run Spearman with MY eff_exact.
  D  ground-truth spot check: my dps-45 composite tanh-sinh u_i(0.5+i*gamma) vs their
     composite-GL u_true on bases 0/2/7 (their gt_basis{0,2,7}.json rows).
"""
import hashlib, itertools, json, os, sys, time
from mpmath import mp, mpf, mpc, exp, pi

EXCH = "/Users/gjw255/astrodata/SWARM/Riemann_exchange"
ASTRA = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main"
DPS = 45
mp.dps = DPS

def sec(t):
    print(f"\n{'='*72}\n{t}\n{'='*72}")

def relerr(a, b):
    return abs(a - b) / abs(b)

# ---------------------------------------------------------------- conventions
def theta(y):
    if y <= 0:
        return mpf(0)
    if y >= 1:
        return mpf(1)
    a = exp(-1 / y)
    b = exp(-1 / (1 - y))
    return a / (a + b)

def window(x):
    return theta((8 - abs(x)) / 2)

def make_phi(genome):
    bumps = [(mpf(str(c)), mpf(str(mu)), mpf(str(s))) for c, mu, s in genome]
    def phi(x):
        tot = mpf(0)
        for c, mu, s in bumps:
            t = (x - mu) / s
            if abs(t) < 1:
                tot += c * exp(-1 / (1 - t * t))
        if tot == 0:
            return mpf(0)
        return window(x) * tot
    return phi, bumps

def breakpoints(bumps):
    """m2's convention: bump supports clipped to +-8, split at +-6 (only inside a support)."""
    pts = set()
    for c, mu, s in bumps:
        lo, hi = mu - s, mu + s
        if hi <= -8 or lo >= 8:
            continue
        lo = max(lo, mpf(-8)); hi = min(hi, mpf(8))
        pts.add(lo); pts.add(hi)
        for cut in (mpf(-6), mpf(6)):
            if lo < cut < hi:
                pts.add(cut)
    return sorted(pts)

def support_union(bumps):
    """Exact open supports of phi's bump part, clipped to (-8,8)."""
    ivs = []
    for c, mu, s in bumps:
        lo, hi = mu - s, mu + s
        if hi <= -8 or lo >= 8:
            continue
        ivs.append((max(lo, mpf(-8)), min(hi, mpf(8))))
    ivs.sort()
    merged = []
    for a, b in ivs:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged

def overlap(a, b, ivs):
    return sum(max(mpf(0), min(b, y) - max(a, x)) for x, y in ivs)

# ---------------------------------------------------------------- A: node count
sec("A  node count — m2's gl_nodes code path (ERRATUM 9 strike 1)")
from mpmath.calculus.quadrature import GaussLegendre
_gl = GaussLegendre(mp)
for deg in (7, 8, 9, 10):
    raw = _gl.get_nodes(mpf(0), mpf(1), deg, mp.prec)
    nodes = raw[0] if isinstance(raw[0], list) else raw
    print(f"degree {deg:2d}: len(gl_nodes(0,1,{deg})) = {len(nodes)}   (3*2^(d-1) = {3*2**(deg-1)})")

# ---------------------------------------------------------------- genomes
GEN_EXCH = f"{EXCH}/data/code/machine1_heat70_genomes_m8_m64.json"
GEN_ASTRA = f"{ASTRA}/Riemann/experiments/orchestrator/machine1_heat70_genomes_m8_m64.json"
h1 = hashlib.sha1(open(GEN_EXCH, 'rb').read()).hexdigest()
h2 = hashlib.sha1(open(GEN_ASTRA, 'rb').read()).hexdigest() if os.path.exists(GEN_ASTRA) else None
print(f"\ngenome file exchange sha1 {h1[:16]}  astra-side {h2[:16] if h2 else 'ABSENT'}  identical={h1==h2}")
genomes = json.load(open(GEN_EXCH))["genomes"]["s1/M8"]
print(f"M = {len(genomes)} genomes; bump counts = {[len(g) for g in genomes]}")

# ---------------------------------------------------------------- B: widths
sec("B  widths from genomes (independent arithmetic)")
BD = json.load(open(f"{EXCH}/data/machine2_cycle24_breakdown.json"))
WL = json.load(open(f"{EXCH}/data/machine2_cycle24_widthlaw.json"))
print(f"{'b':>2} {'hmax(mine)':>12} {'hmax(m2)':>12} {'eff_exact':>12} {'effmax(m2)':>12} "
      f"{'wl_heffmax':>12} {'empty_gap':>10}")
my_effmax, my_hmax = [], []
for i, g in enumerate(genomes):
    phi, bumps = make_phi(g)
    pts = breakpoints(bumps)
    gaps = [pts[k+1] - pts[k] for k in range(len(pts)-1)]
    hmax = max(gaps)
    sup = support_union(bumps)
    effs = [overlap(pts[k], pts[k+1], sup) for k in range(len(pts)-1)]
    effmax = max(effs)
    # widest container and whether it intersects the support at all
    kmax = gaps.index(hmax)
    a, b = pts[kmax], pts[kmax+1]
    empty = overlap(a, b, sup) == 0
    wl_max = max((r["heff"] for r in WL if r["basis"] == i), default=None)
    my_effmax.append(float(effmax)); my_hmax.append(float(hmax))
    print(f"{i:>2} {float(hmax):>12.4f} {BD[str(i)]['hmax']:>12.4f} {float(effmax):>12.4f} "
          f"{BD[str(i)]['effmax']:>12.4f} {wl_max if wl_max else -1:>12.4f} "
          f"{('EMPTY' if empty else f'{float(overlap(a,b,sup)):.3f}'):>10}")
print("\n(wl_heffmax = max panel heff in their widthlaw.json — a third convention; "
      "b1/b7 order swaps between conventions but both are gamma-tied at 260)")

# ---------------------------------------------------------------- C: statistics
sec("C  statistics — break@deg7 + effmax/hmax, raw AND gated, then my eff_exact")
gb_raw = [BD[str(i)]["break"]["7"] for i in range(8)]       # [None,260,140,340,220,20,400,260]
# gated vector: letter §3 table (b5: raw 20 at deg 7/8/9/10 alike = their caught GT artefact;
# gated re-run m2_c24_breakdown_gated.py writes breakdown5.json, NOT committed — letter value 280)
gb_gated = [None, 260, 140, 340, 220, 280, 400, 260]
print(f"raw   break@7 = {gb_raw}")
print(f"gated break@7 = {gb_gated}   (only b5 differs: 20 -> 280)")
def ranks(v):
    s = sorted(range(len(v)), key=lambda i: v[i]); out = [0.0]*len(v); i = 0
    while i < len(s):
        j = i
        while j+1 < len(s) and v[s[j+1]] == v[s[i]]:
            j += 1
        m = (i + j)/2 + 1
        for k in range(i, j+1):
            out[s[k]] = m
        i = j + 1
    return out
def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx)/8, sum(ry)/8
    num = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    den = (sum((a-mx)**2 for a in rx) * sum((b-my)**2 for b in ry))**0.5
    return num/den
def perm_p(hv, gv, rho_obs):
    """exact one-sided P: fraction of 8! pairings with rho <= rho_obs"""
    rg = ranks(gv)
    mg = sum(rg)/8
    sg = (sum((b-mg)**2 for b in rg))**0.5
    cnt = 0; tot = 0
    for perm in itertools.permutations(range(8)):
        rh = [0.0]*8
        for pos, idx in enumerate(perm):
            rh[idx] = pos + 1
        mh = 4.5
        sh = (sum((a-mh)**2 for a in rh))**0.5
        num = sum((a-mh)*(b-mg) for a, b in zip(rh, rg))
        rho = num/(sh*sg)
        tot += 1
        if rho <= rho_obs:
            cnt += 1
    return cnt, tot
def prod_law(hv, label):
    xs = [(g, h) for g, h in zip(cens, hv) if g is not None and g < 450]
    # use only non-censored for the law (their stated convention: 7 points)
    ps = [g*h for g, h in xs]
    m = sum(ps)/len(ps)
    sd = (sum((p-m)**2 for p in ps)/len(ps))**0.5
    sd_s = (sum((p-m)**2 for p in ps)/(len(ps)-1))**0.5
    print(f"  {label}: mean {m:.1f}  pop-sd {sd:.1f} ({100*sd/m:.1f}%)  samp-sd {sd_s:.1f} ({100*sd_s/m:.1f}%)  n={len(ps)}")
    return m

for label, gbv in [("GATED", gb_gated), ("RAW  ", gb_raw)]:
    cens = [450.0 if v is None else float(v) for v in gbv]
    print(f"\n--- {label} vector ---")
    for tag, hv in [("their effmax", [BD[str(i)]["effmax"] for i in range(8)]),
                    ("their hmax  ", [BD[str(i)]["hmax"] for i in range(8)]),
                    ("my eff_exact", my_effmax),
                    ("my hmax     ", my_hmax)]:
        rho = spearman(hv, cens)
        c, t = perm_p(hv, cens, rho)
        print(f"{tag}: Spearman = {rho:+.4f}   exact P(rho<=obs) = {c}/{t} = {c/t:.2e}   (claim: "
              f"{'-0.9940 / 9.9e-5' if 'eff' in tag else '-0.6946 / 0.063'})")
    cens_g = cens
    m_eff = prod_law([BD[str(i)]["effmax"] for i in range(8)], f"gamma*effmax ({label})")
    prod_law([BD[str(i)]["hmax"] for i in range(8)], f"gamma*hmax   ({label})")
    if label == "GATED":
        print(f"  external: gamma*heff/n at deg-7 (n=192) = {m_eff/192:.3f}  (their claim 3.22)")

# ---------------------------------------------------------------- D: GT spot check
sec("D  ground-truth spot check — my dps-45 composite tanh-sinh vs their u_true")
def u_mine(genome, gamma, piece_per_lambda=8):
    """u_i(0.5 + i*gamma) via composite tanh-sinh on breakpoint intervals split to <= lambda/8."""
    phi, bumps = make_phi(genome)
    rho = mpc(mpf('0.5'), mpf(gamma))
    lam = 2*pi/mpf(gamma)
    piece = lam / piece_per_lambda
    pts = breakpoints(bumps)
    tot = mpc(0)
    for k in range(len(pts)-1):
        a, b = pts[k], pts[k+1]
        if overlap(a, b, support_union(bumps)) == 0:
            continue
        n = int(mp.ceil((b - a)/piece))
        for j in range(n):
            x0 = a + (b - a)*j/n
            x1 = a + (b - a)*(j+1)/n
            tot += mp.quad(lambda x: phi(x)*exp(rho*x), [x0, x1])
    return tot

targets = [("0", 100.0), ("0", 200.0), ("2", 200.0), ("2", 250.0), ("2", 350.0), ("7", 250.0), ("7", 400.0)]
gts = {k: json.load(open(f"{EXCH}/data/machine2_cycle24_gt_basis{k}.json"))[k]["rows"] for k in ("0", "2", "7")}
worst = mpf(0)
for k, gam in targets:
    row = next((r for r in gts[k] if float(r["gamma"]) == gam), None)
    if row is None:
        print(f"basis {k} gamma {gam}: NO ROW"); continue
    t0 = time.time()
    um = u_mine(genomes[int(k)], gam)
    s = row["u_true"]
    ut = abs(mpf(s.split("e")[0])) * mpf(10)**(int(s.split("e")[1]) if "e" in s else 0)  # magnitude
    re_ = float(abs(abs(um) - ut)/ut)
    worst = max(worst, mpf(re_))
    print(f"basis {k} gamma {gam:6.1f}: |u_mine| = {float(abs(um)):.12e}   their u_true = {float(ut):.12e}   "
          f"rel diff = {re_:.3e}   [{time.time()-t0:.0f}s]")
print(f"\nworst relative difference across spot checks: {float(worst):.3e}")

sec("heat74 done")
