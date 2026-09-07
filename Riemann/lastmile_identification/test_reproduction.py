#!/usr/bin/env python3
"""STATUS LABEL: NON-DESTRUCTIVE REPRODUCTION TEST (robopol-style reference design).

Re-derives the identification table's machine-checkable rows from the sealed
inputs WITHOUT modifying anything sealed: hashes (manifest), strings (R4, R5),
zero cut (R2), and — by default — one full-precision matrix element of the
zero-side kernel (R1's K[0,0], tolerance relative 1e-40; the measured full-
matrix agreement was 5.73e-46, and any side/basis/convention error is O(1), so
the tolerance separates the two regimes by >5 orders with >10x headroom).
--full additionally re-derives all 8x8 entries (R1) and the surgery
exact-equality checks quad_ex(g,0) == 2*gram(g) at k=2,3,7 (R3), mirroring the
primary measurement (A1) with make_phi imported from the sealed runner [S1]
itself — never re-typed (trap #S12). It writes only its own receipt
(test_reproduction.out); it never writes to a sealed path (A1's own OUT path is
theirs — this script does not import A1 for exactly that reason).

Modes: --quick (~5 s) | default (~2 min: + K[0,0]) | --full (~15 min: + 8x8 + R3)
"""
import hashlib
import importlib.util
import json
import os
import sys
import time

from mpmath import mp, mpf, mpc, exp, quad, zetazero, re as mpre, im as mpim, conj, fabs

HERE = os.path.dirname(os.path.abspath(__file__))
ASTRA = os.path.abspath(os.path.join(HERE, "..", ".."))
EXCH = "/Users/gjw255/astrodata/SWARM/Riemann_exchange"
REPOS = {"ASTRA-dev-main": ASTRA, "Riemann_exchange": EXCH}

MODE = "--full" if "--full" in sys.argv else ("--quick" if "--quick" in sys.argv else "default")
T0 = time.time()
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail else ""), flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---- 1. manifest hashes ------------------------------------------------------
man = json.load(open(os.path.join(HERE, "manifest.json")))
bad = []
for group in ("inputs", "members"):
    for key, entry in man[group].items():
        p = os.path.join(REPOS[entry["repo"]], entry["path"])
        if not os.path.exists(p) or sha256(p) != entry["sha256"]:
            bad.append(group + "/" + key)
check("manifest: all %d member+input hashes match" % (len(man["members"]) + len(man["inputs"])), not bad,
      ", ".join(bad) if bad else "nothing modified")

# ---- 2. sealed-input loads (S2 genomes, S3 identity target, S5 m64 kernel) ---
GEN = os.path.join(EXCH, "data/code/machine1_heat70_genomes_m8_m64.json")
IDT = os.path.join(ASTRA, "Riemann/experiments/orchestrator/heat72k_identity_target_m8.json")
M64 = os.path.join(EXCH, "data/machine1_heat78a_m64_kernel.json")
RUNNER = os.path.join(EXCH, "data/code/machine1_heat78c_survivor_census.py")
idt = json.load(open(IDT))

# R4: convention-string provenance, verbatim
CONV = ("raw genome basis; K_FE = sum_{0<Im rho<=T} 2Re[U_a(rho) conj(U_b(rho))]; "
        "U_a(rho)=int phi_a e^{rho t}; breakpoints per spec; mp.dps 45")
check("R4 convention string verbatim in sealed S3", idt.get("convention") == CONV)

# R5: the note field carries m3's receipt
note = idt.get("note", "")
check("R5 S3 note field carries m3 Kowalski Prop 1.2.1 receipt",
      ("Kowalski Prop 1.2.1" in note) and ("m3" in note))

# ---- 3. R2: the T=200 zero cut ----------------------------------------------
# dps 45 from the start (matching the primary measurement A1): dps-30 ordinates
# would inject ~1e-28-scale error into the 1e-40 kernel band below.
mp.dps = 45
n, zeros = 1, []
while True:
    g = mpim(zetazero(n))
    if g > 200:
        break
    zeros.append(g)
    n += 1
check("R2 zero cut = 79 zeros, Im(z79)<=200<Im(z80)",
      len(zeros) == 79 and zeros[-1] <= 200 < g,
      "Im(z79)=%s Im(z80)=%s" % (mp.nstr(zeros[-1], 11), mp.nstr(g, 11)))
m64 = json.load(open(M64))
check("R2 agrees with M64 kernel build n_zeros field", int(m64["n_zeros"]) == 79)

# ---- 4. R1: zero-side kernel element(s) re-derivation -----------------------
if MODE != "--quick":
    HALF = mpf(1) / 2
    spec = importlib.util.spec_from_file_location("h78c", RUNNER)
    h78c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h78c)
    check("sealed runner [S1] imported (make_phi used verbatim, trap #S12)", True,
          "sha256 %s" % hashlib.sha256(open(RUNNER, "rb").read()).hexdigest()[:16])
    genomes = json.load(open(GEN))["genomes"]["s1/M8"]
    M = 8
    phis, edges = zip(*[h78c.make_phi(g) for g in genomes])
    K_stored = [[mpf(x) for x in idt["seeds"]["s1/M8"]["K_T200"][i]] for i in range(M)]

    def U(i, s):
        return quad(lambda t: phis[i](t) * exp(s * t), edges[i])

    if MODE == "--full":
        Uz = [[U(i, mpc(HALF, g)) for g in zeros] for i in range(M)]
        dmax, scale = mpf(0), max(fabs(K_stored[i][j]) for i in range(M) for j in range(M))
        for i in range(M):
            for j in range(M):
                dmax = max(dmax, fabs(sum(2 * mpre(Uz[i][n_] * conj(Uz[j][n_])) for n_ in range(79)) - K_stored[i][j]))
        rel = dmax / scale
        check("R1 full 8x8 zero-side re-derivation (tol rel 1e-40; measured at A1 5.73e-46)",
              rel < mpf("1e-40"), "max|diff|=%s rel=%s" % (mp.nstr(dmax, 6), mp.nstr(rel, 6)))
        # R3: surgery semantics, exact equality (gram/quad_ex re-typed from sealed
        # runner lines 105-124 exactly as the primary measurement [A1] did)
        zk = [mpf(str(mpim(zetazero(n_)))) for n_ in range(1, 27)]

        def gram(g0):
            uv = [U(i, mpc(HALF, g0)) for i in range(M)]
            return [[2 * mpre(uv[i] * conj(uv[j])) for j in range(M)] for i in range(M)]

        def quad_ex(g0, d):
            p, q = mpc(HALF + d, g0), mpc(HALF - d, g0)
            up = [U(i, p) for i in range(M)]
            uq = [U(i, q) for i in range(M)]
            return [[2 * mpre(up[i] * conj(uq[j]) + up[j] * conj(uq[i])) for j in range(M)] for i in range(M)]

        for k in (2, 3, 7):
            g = zk[k] + (zk[k + 1] - zk[k]) * mpf(4) / 8
            db = max(fabs(quad_ex(g, mpf(0))[i][j] - 2 * gram(g)[i][j]) for i in range(M) for j in range(M))
            check("R3 quad_ex(g,0) == 2*gram(g) exactly at k=%d" % k, db == 0, "max|diff|=%s" % mp.nstr(db, 3))
    else:
        row = []
        for gg in zeros:
            u = U(0, mpc(HALF, gg))
            row.append(2 * mpre(u * conj(u)))
        k00 = sum(row)
        rel = fabs(k00 - K_stored[0][0]) / fabs(K_stored[0][0])
        check("R1 K[0,0] zero-side re-derivation (tol rel 1e-40; full-matrix measured 5.73e-46)",
              rel < mpf("1e-40"), "rel=%s" % mp.nstr(rel, 6))

# ---- summary -----------------------------------------------------------------
print("mode=%s  %d/%d checks passed  (%.1fs)" % (MODE, sum(RESULTS), len(RESULTS), time.time() - T0))
sys.exit(0 if all(RESULTS) else 1)
