"""heat68b — rect-Epstein sigma>1 zero probe (follow-up QUESTION registered in
machine1-letter-dh-re1-sourced.md; NOT a scored rung).

Question: does zeta^(2)(s, D) = 1/2 sum' (j^2 + D^2 k^2)^{-s} have zeros with
Re s > 1? (Cassels showed D-H does; Saias-Weingartner's structure theorem does
NOT apply to this carrier — coefficients are representation counts, not
periodic — so the answer is open. If YES: the sequential/decay half breaks on
the rectangular carrier too, same as D-H and Epstein h>1. If NO at scanned
heights: height-limited absence only.)

Pre-stated outcomes (before data, per letter):
  (a) no |zeta^(2)| local minimum below FIND_THRESHOLD at any scanned (D, t,
      sigma) -> outcome NO-EVIDENCE (height-limited); report raw curves.
  (b) candidate local minimum below FIND_THRESHOLD -> 2D bisection refine at
      dps=50, then dual-evaluator verification (A and B agree at the minimum;
      B = theta-Mellin split, independent construction). Verified -> REPORT +
      letter; fails verification -> report as artifact with diagnosis.
  (c) minima within 3x of threshold -> ambiguous, report raw, no claim.

Method: evaluator A (Bessel representation, as heat68 runner, mpmath dps=30
scan / dps=50 refine). Scan D in {0.05, 0.10}, t in {5,10,15,20},
sigma in [1.05, 4.0] step 0.05 (79 pts/line). Local minima of |zeta2_A| with
both-sides-higher shape recorded. Threshold: FIND_THRESHOLD = 1e-3 * median
scale of the line (zeros -> 0; pole at s=1 is far at these t).

machine1, single process (CPU cap respected; heat68 has its own core).
"""
import json, time
from mpmath import mp, mpf, mpc, pi, sqrt, exp, log, gamma, zeta, besselk, fabs, arg

mp.dps = 30

def zeta2_A(s, D):
    """Bessel representation (heat68 evaluator A, k-power (m/k)^{s-1/2} per trap #77 fix)."""
    D = mpf(D); s = mpc(s)
    t1 = zeta(2*s)
    t2 = sqrt(pi)*gamma(s - mpf('0.5'))*D**(1 - 2*s)*zeta(2*s - 1)/gamma(s)
    tot = t1 + t2
    nu = s - mpf('0.5')
    ssum = mpf(0)
    for k in range(1, 60):
        z = 2*pi*D*k
        inner = mpf(0)
        for m in range(1, 60):
            inner += (mpf(m)/k)**nu * besselk(nu, z*m)
        term = inner
        ssum += term
        if abs(term) < mpf('1e-40') and k > 5:
            break
    return tot + (4*pi**s/gamma(s))*D**(mpf('0.5') - s)*ssum

def scan_line(D, t):
    xs = [mpf('1.05') + mpf('0.05')*i for i in range(80)]   # 1.05 .. 4.00
    vals = []
    for x in xs:
        s = x + 1j*t
        vals.append(abs(zeta2_A(s, D)))
    scale = sorted(vals)[len(vals)//2]
    cands = []
    for i in range(1, len(xs)-1):
        if vals[i] < vals[i-1] and vals[i] < vals[i+1]:
            cands.append((float(xs[i]), float(t), float(vals[i]), float(vals[i]/scale)))
    return xs, vals, scale, cands

if __name__ == '__main__':
    t0 = time.time()
    print("heat68b sigma>1 probe. dps=30 scan. Pre-stated outcomes a/b/c (letter).", flush=True)
    THRESH = mpf('1e-3')
    out = {'lines': [], 'candidates': [], 'outcome': None, 'notes': []}
    for D in ['0.05', '0.10']:
        for t in [5, 10, 15, 20]:
            xs, vals, scale, cands = scan_line(D, t)
            line = dict(D=D, t=t, scale=float(scale),
                        vmin=float(min(vals)), vmax=float(max(vals)),
                        argmin_sigma=float(xs[vals.index(min(vals))]),
                        cands=[dict(sigma=c[0], absval=c[2], ratio=c[3]) for c in cands])
            out['lines'].append(line)
            print(f"D={D} t={t:2d}: scale={float(scale):.3e} min|z2|={line['vmin']:.3e} "
                  f"at sigma={line['argmin_sigma']:.2f}  local-minima={len(cands)}", flush=True)
            for c in cands:
                out['candidates'].append(dict(D=D, t=t, **dict(sigma=c[0], absval=c[2], ratio=c[3])))
                print(f"    local min at sigma={c[0]:.2f}: |z2|={c[2]:.3e}  ratio={c[3]:.3e}", flush=True)
    hits = [c for c in out['candidates'] if c['ratio'] < float(THRESH)]
    if not hits:
        out['outcome'] = 'a'   # no-evidence (height-limited)
        print(f"\nOUTCOME (a): no candidate below threshold {THRESH} — height-limited no-evidence.", flush=True)
    elif any(c['ratio'] < float(THRESH)/3 for c in hits):
        out['outcome'] = 'b-verify-needed'
        print(f"\nOUTCOME (b): {len(hits)} candidate(s) below threshold — 2D refine + dual-evaluator verify next.", flush=True)
    else:
        out['outcome'] = 'c-ambiguous'
        print(f"\nOUTCOME (c): minima within 3x of threshold — raw report only.", flush=True)
    out['elapsed_s'] = time.time() - t0
    json.dump(out, open('heat68b_sigma_gt1_probe.json', 'w'), indent=1)
    print(f"done in {out['elapsed_s']:.0f}s; json written", flush=True)
