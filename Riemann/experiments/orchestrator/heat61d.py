"""heat61d — post-completion verification ladder for the run-3 lineage winners.

Loads genomes from heat61_w_search.log.json — PARSED, never hand-copied (trap #63) —
and runs the heat61c protocol on each: prime-side refinement ladder 2^19 -> 2^21 -> 2^23
(via heat61_w_search.prime_side_genome, the same self-contained evaluator the halt rule
uses), plus the zero side at 2^23 (T = 100/150/200 saturation).

Why this exists (NOTES 88f design-gap note): the halt rule self-checks only genomes that
cross -eps_cert at both grids. But ANY Q measurably below zero is disproof-class if true,
and run-3's LB lineage spent generations 45-70 creeping through -9e-4 territory at 2^19 —
between the class floor (~1e-4) and the halt line. This script closes that gap for the
final winners. Pre-stated outcomes:
  (a) ladder converges >= 0: grid artifact again -> D7 deepens (third #65 firing);
  (b) ladder stable < 0 with prime/zero agreement: genuine negative Q cell -> freeze,
      NO claim language, counterparty first (machine 3's validated burnol_final.py);
  (c) drift in between: map it, raise the floor, resume.
Import of heat61_w_search is side-effect-safe: module level builds the sieve and L-C
machinery only; run() sits behind the __main__ guard (verified lines 399-412).
"""
import json
import sys

import mpmath as mp
import numpy as np

import heat61_w_search as H

mp.mp.dps = 30


def build_f_grid(lineage, genome, grid_log2):
    """Re-realize f on an arbitrary grid, mirroring prime_side_genome lines 271-291."""
    LGRID, N = 24.0, 1 << grid_log2
    dx = 2 * LGRID / N
    xs = -LGRID + dx * np.arange(N)
    win = H.window(xs)
    if lineage == "LA":
        f = np.zeros_like(xs)
        for c, mu, sg in genome["terms"]:
            f += c * np.exp(-((xs - mu) ** 2) / (2 * sg * sg))
    elif lineage == "LB":
        f = np.zeros_like(xs)
        cc = genome["c"]
        for ctr, amp in genome["pairs"]:
            t = xs - ctr
            safe = np.abs(t) > 1e-10
            f += amp * np.where(safe, np.sin(cc * t) / (np.pi * np.where(safe, t, 1.0)), cc / np.pi)
    else:
        P = np.zeros(H.NT, dtype=complex)
        for a, p in genome["terms"]:
            P += a * np.exp(-(0.5 + 1j * H.TS_C) * np.log(p))
        gh = P * np.conj(P) * H._theta((H.TMAX - np.abs(H.TS_C)) / (H.TMAX / 4))
        f = np.exp(-xs / 2) * H._realize_f_on(gh, xs)
    f = f * win
    return xs, dx, f / max(np.sqrt(dx * (f * f).sum()), 1e-300)


def zero_side(xs, dx, f, T):
    def gh(s):
        w = f * np.exp(complex(s) * xs)
        return dx * (w.sum() - 0.5 * (w[0] + w[-1]))
    total, n = 0.0, 1
    last = None
    while True:
        z = mp.zetazero(n)
        if z.imag > T:
            break
        rho = complex(z)
        term = 2.0 * (gh(rho) * gh(1 - rho)).real
        total += term
        last = abs(term)
        n += 1
    return total, n - 1, last


if __name__ == "__main__":
    with open("heat61_w_search.log.json") as fh:
        REC = json.load(fh)
    targets = []
    for fr in REC.get("frozen", []):
        if fr.get("genome") is not None:
            targets.append((fr["lineage"], fr["genome"],
                            f"frozen gen {fr['gen']} Q_search {fr['Q_search']:+.3e}"))
    if "final" in REC:
        for L, pair in REC["final"].items():
            qfinal, blob = pair[0], pair[1]
            targets.append((L, json.loads(blob), f"final best (fitness {qfinal:+.3e})"))
    if not targets:
        print("no targets yet (search still running: no frozen entries, no final block)")
        sys.exit(0)
    print(f"targets: {len(targets)} (drift-rejects carry no genome; Q-values only in log)")
    for L, g, tag in targets:
        print(f"\n===== {L} [{tag}] =====")
        print(f"  genome: {json.dumps(g)[:200]}")
        for gl in (19, 21, 23):
            print(f"  2^{gl}: Q_prime = {H.prime_side_genome(L, g, gl):+.8e}")
            sys.stdout.flush()
        xs, dx, f = build_f_grid(L, g, 23)
        for T in (100.0, 150.0, 200.0):
            qz, nz, last = zero_side(xs, dx, f, T)
            print(f"  zero T={T:5.0f} ({nz:3d} zeros): Q_zero = {qz:+.8e}   last|term| {last:.2e}")
            sys.stdout.flush()
    print("\nverdict per NOTES 88f pre-statement: (a) >=0 artifact / (b) <0 both sides -> freeze, "
          "counterparty, no claims / (c) drift -> map it")
