#!/usr/bin/env python3
"""heat78c — the SURVIVOR-SET CENSUS scored runner (prereg = m1-L158).

Lattice (frozen in the prereg letter BEFORE any displaced M64 verdict was computed):
  - pairs k = 0..24 at phi = 4/8 (midpoint), delta in {0.05, 0.10, 0.20, 0.30, 0.45}   (125)
  - pairs k = 0..7  at phi in {2/8, 6/8}, same delta ladder                            (80)
  - controls: k = 0..7 at phi = 4/8, delta = 0                                          (8)
  - M in {8, 64}, T = 200. 213 configs x 2 M = 426 solves.
Config: K_S = K_T200 - gram(z_k) - gram(z_{k+1}) + quad_ex(g, delta),
  g = z_k + phi*(z_{k+1} - z_k).   Verdict: FIRES iff lam_min < -1e-12.
Controls execute FIRST at each M; any control firing = RED, displaced cells at that M
are not scored.
Deliverables: verdict lattice; M8->M64 FLIP SET with overlap TYPE per flip
(descent vs reorganization vs the delta=0 spectrum at M64); M8 geometry table
(lam_min, PT = ||P||_G / gap01); per-M fire counts.
Known-data disclosure: m3-L158 (25 rows @ delta=0.1), m3-L159 (3 pairs x 5 delta),
m1 heat79/80 verifications of the same. Everything else is blind until reveal.
Kernels: M8 = committed identity target; M64 = heat78a frozen kernel.
Validates the frozen input hashes at startup; any mismatch = abort (outcome (c)),
no cell scored.
"""
import hashlib
import json
import sys
import time
from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

mp.dps = 45
HALF = mpf(1) / 2
THRESH = mpf("-1e-12")
T0 = time.time()

GEN = "/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/code/machine1_heat70_genomes_m8_m64.json"
IDT = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat72k_identity_target_m8.json"
K64 = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat78a_m64_kernel.json"
OUTJ = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/heat78c_census_result.json"

DELTAS = ["0.05", "0.1", "0.2", "0.3", "0.45"]

# frozen input seals (m1-L158); mismatch = abort, outcome (c)
HASHES = {
    GEN: "1065fd370fd9370807ea61f19708cbf1d16be77179f279760864386d299da56b",
    IDT: "12b81d093a0eb9d76709a61a9e22015af81a646e18faab722443efc0b03f87ff",
    K64: "f992234913440a6af50cccf6016af260afc0be0fdcac417500d94b47331e3c51",
}


def check_seals():
    bad = []
    for path, want in HASHES.items():
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if h != want:
            bad.append((path, h, want))
    if bad:
        for (path, got, want) in bad:
            print("SEAL MISMATCH %s\n  got  %s\n  want %s" % (path, got, want), flush=True)
        sys.exit("INPUT SEAL FAILURE — aborting, nothing scored (outcome c)")
    print("input seals verified (3/3)", flush=True)


def theta_step(s):
    if s <= 0:
        return mpf(0)
    if s >= 1:
        return mpf(1)
    return exp(-1 / s) / (exp(-1 / s) + exp(-1 / (1 - s)))


def window(x):
    return theta_step((8 - fabs(x)) / 2)


def bumpval(t):
    if fabs(t) >= 1:
        return mpf(0)
    return exp(-1 / (1 - t * t))


def make_phi(genome):
    triples = [(mpf(str(c)), mpf(str(mu)), mpf(str(s))) for (c, mu, s) in genome]

    def phi(x):
        tot = mpf(0)
        for (c, mu, s) in triples:
            tot += c * bumpval((x - mu) / s)
        return window(x) * tot

    edges = sorted(set([mpf(-8), mpf(-6), mpf(6), mpf(8)] +
                       [mu - s for (c, mu, s) in triples] + [mu + s for (c, mu, s) in triples]))
    return phi, edges


class Instrument:
    def __init__(self, M, K, G, phis, edges):
        self.M, self.K, self.G, self.phis, self.edges = M, K, G, phis, edges
        self.gram_cache = {}
        self.Uc = {}

    def U(self, i, s):
        key = str(s)
        if (i, key) not in self.Uc:
            self.Uc[(i, key)] = quad(lambda t: self.phis[i](t) * exp(s * t), self.edges[i])
        return self.Uc[(i, key)]

    def gram(self, g0):
        key = "g" + mp.nstr(g0, 25)
        if key not in self.gram_cache:
            uv = [self.U(i, mpc(HALF, g0)) for i in range(self.M)]
            M = mp.matrix(self.M, self.M)
            for i in range(self.M):
                for j in range(self.M):
                    M[i, j] = 2 * mpre(uv[i] * conj(uv[j]))
            self.gram_cache[key] = M
        return self.gram_cache[key]

    def quad_ex(self, g0, d):
        p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
        up = [self.U(i, p) for i in range(self.M)]
        uq = [self.U(i, q) for i in range(self.M)]
        M = mp.matrix(self.M, self.M)
        for i in range(self.M):
            for j in range(self.M):
                M[i, j] = 2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i]))
        return M

    def eig(self, F):
        Gm = self.G
        L = mp.cholesky(Gm)
        Li = mp.inverse(L)
        B = Li * F * Li.T
        B = (B + B.T) / 2
        E, V = mp.eigsy(B)
        idx = sorted(range(self.M), key=lambda i: E[i])
        return [E[i] for i in idx], [Li.T * mp.matrix([V[r, i] for r in range(self.M)]) for i in idx]

    def bil(self, v, w):
        return sum(v[i] * self.G[i, j] * w[j] for i in range(self.M) for j in range(self.M))

    def gnorm(self, P):
        L = mp.cholesky(self.G)
        Li = mp.inverse(L)
        B = Li * P * Li.T
        B = (B + B.T) / 2
        E, _ = mp.eigsy(B)
        return max(fabs(x) for x in E)


def main():
    selftest = "--selftest" in sys.argv
    check_seals()
    gdata = json.load(open(GEN))["genomes"]
    idt = json.load(open(IDT))["seeds"]["s1/M8"]
    k64 = json.load(open(K64))

    insts = {}
    for M, (K, G, ph) in (
        (8, (idt, idt, "s1/M8")),
        (64, (k64, k64, "s1/M64")),
    ):
        genomes = gdata[ph]
        phis, edges = zip(*[make_phi(g) for g in genomes])
        if M == 8:
            K = mp.matrix(M, M)
            G = mp.matrix(M, M)
            for i in range(M):
                for j in range(M):
                    K[i, j] = mpf(idt["K_T200"][i][j])
                    G[i, j] = mpf(idt["G_raw"][i][j])
        else:
            K = mp.matrix(M, M)
            G = mp.matrix(M, M)
            for i in range(M):
                for j in range(M):
                    K[i, j] = mpf(k64["K_T200"][i][j])
                    G[i, j] = mpf(k64["G_raw"][i][j])
        insts[M] = Instrument(M, K, G, phis, edges)
    print("instruments built %.1fs" % (time.time() - T0), flush=True)

    zeros = [mpf(str(mpim(zetazero(n)))) for n in range(1, 27)]

    def g_of(k, phi8):
        return zeros[k] + (zeros[k + 1] - zeros[k]) * mpf(phi8) / 8

    if selftest:
        inst = insts[8]
        for k in range(8):
            KS = inst.K - inst.gram(zeros[k]) - inst.gram(zeros[k + 1]) + inst.quad_ex(g_of(k, 4), mpf(0))
            vals, _ = inst.eig(KS)
            print("SELFTEST control M8 k=%d lam_min %s  %s" % (
                k, mp.nstr(vals[0], 14), "FIRES-RED" if vals[0] < THRESH else "ok"), flush=True)
        print("selftest done %.1fs (no displaced cell touched)" % (time.time() - T0), flush=True)
        return

    cells = []
    for k in range(25):
        for d in DELTAS:
            cells.append((k, 4, d))
    for k in range(8):
        for phi8 in (2, 6):
            for d in DELTAS:
                cells.append((k, phi8, d))
    controls = [(k, 4, "0") for k in range(8)]

    results = {}
    status = {}
    for M in (8, 64):
        inst = insts[M]
        # controls first: any firing = RED for this M
        red = False
        for (k, phi8, dstr) in controls:
            KS = inst.K - inst.gram(zeros[k]) - inst.gram(zeros[k + 1]) + inst.quad_ex(g_of(k, phi8), mpf(0))
            vals, _ = inst.eig(KS)
            fires = vals[0] < THRESH
            results[("ctl", M, k)] = {"lam_min": mp.nstr(vals[0], 25), "fires": fires}
            if fires:
                red = True
            print("[M%d] CONTROL k=%d lam_min %s %s" % (M, k, mp.nstr(vals[0], 12), "FIRES-RED" if fires else "ok"), flush=True)
        status[M] = "RED" if red else "GREEN"
        if red:
            print("[M%d] CONTROLS RED — displaced cells NOT scored at this M" % M, flush=True)
            continue

        for (k, phi8, dstr) in cells:
            KS = inst.K - inst.gram(zeros[k]) - inst.gram(zeros[k + 1]) + inst.quad_ex(g_of(k, phi8), mpf(dstr))
            vals, vecs = inst.eig(KS)
            fires = vals[0] < THRESH
            rec = {"lam_min": mp.nstr(vals[0], 25), "fires": fires, "gap01": mp.nstr(vals[1] - vals[0], 18)}
            if M == 8:
                P = inst.quad_ex(g_of(k, phi8), mpf(dstr)) - inst.quad_ex(g_of(k, phi8), mpf(0))
                rec["PT"] = mp.nstr(inst.gnorm(P) / (vals[1] - vals[0]), 8)
            results[(M, k, phi8, dstr)] = rec
            if (len(results) % 20) == 0:
                print("[M%d] %d cells done %.1fs" % (M, len(results), time.time() - T0), flush=True)
        print("[M%d] lattice complete %.1fs" % (M, time.time() - T0), flush=True)

    # flip analysis + overlap typing
    flips = []
    if status.get(64) == "GREEN":
        inst64 = insts[64]
        for (k, phi8, dstr) in cells:
            r8, r64 = results.get((8, k, phi8, dstr)), results.get((64, k, phi8, dstr))
            if r8 and r64 and (not r8["fires"]) and r64["fires"]:
                KS0 = inst64.K - inst64.gram(zeros[k]) - inst64.gram(zeros[k + 1]) + inst64.quad_ex(g_of(k, phi8), mpf(0))
                v0, V0 = inst64.eig(KS0)
                KSd = inst64.K - inst64.gram(zeros[k]) - inst64.gram(zeros[k + 1]) + inst64.quad_ex(g_of(k, phi8), mpf(dstr))
                vd, Vd = inst64.eig(KSd)
                ovs = [fabs(inst64.bil(Vd[0], V0[j])) for j in range(4)]
                jmax = max(range(4), key=lambda j: ovs[j])
                typ = "descent" if jmax == 0 else ("reorganization" if ovs[jmax] > 0.5 else "mixed")
                flips.append({"k": k, "phi8": phi8, "delta": dstr,
                              "lam8": r8["lam_min"], "lam64": r64["lam_min"],
                              "overlaps_0_3": [mp.nstr(o, 6) for o in ovs], "type": typ})
                print("FLIP k=%d phi=%d/8 d=%s  %s -> %s  type=%s ovs=%s" % (
                    k, phi8, dstr, r8["lam_min"], r64["lam_min"], typ,
                    ",".join(mp.nstr(o, 4) for o in ovs)), flush=True)

    nfire = {M: sum(1 for (k, phi8, d) in cells if results.get((M, k, phi8, d), {}).get("fires"))
             for M in (8, 64) if status.get(M) == "GREEN"}
    print("SUMMARY n_fire %s  flips %d  status %s" % (nfire, len(flips), status), flush=True)

    def key2str(key):
        return "/".join(str(x) for x in key)

    out = {
        "prereg": "m1-L158", "threshold": "-1e-12", "deltas": DELTAS,
        "status": {str(k): v for k, v in status.items()},
        "n_fire": {str(k): v for k, v in nfire.items()},
        "flips": flips,
        "results": {key2str(k): v for k, v in results.items()},
        "wall_seconds": time.time() - T0,
    }
    with open(OUTJ, "w") as fh:
        json.dump(out, fh, indent=1)
    print("WROTE %s" % OUTJ, flush=True)
    print("heat78c done %.1fs" % (time.time() - T0), flush=True)


if __name__ == "__main__":
    main()
