"""heat51g — exact mirror term at k922 (footnote to the B adjudication,
  machine1-partB-gate-and-dlaw.md section 4). Quantifies BEAST's
  mirror-included jump against the true mirror sum.

  RESULT (run 2026-09-03, dps 30; output below verbatim):
    k922 m0 = 1329.12426839
    table zeros used: 4858
    mirror sum (table)     = 0.00045349321
    mirror sum PNT tail    = 0.00018817067
    mirror sum (total)     = 0.00064166388
    beast jump (mir-nomir) = 6.19705e-4  (1.750466395 - 1.74984669)
    ratio beast/true       = 0.96578

  Reading: BEAST's mirror term captured 96.6% of the true one; the
  2.20e-5 shortfall is the mirror-tail beyond their window. Their
  residual vs the direct B (1.750466395 vs 1.7505517969 = -8.54e-5)
  decomposes as -2.2e-5 (missing mirror tail) + -6.3e-5 (primary S2
  window/tail truncation) — both the Sigma(1/u^2) convergence class
  they themselves declared. Confirms the adjudication quantitatively.
"""
import json
import mpmath as mp

mp.mp.dps = 30
t = json.load(open("/Users/gjw255/astrodata/SWARM/Riemann_exchange/data/"
                   "T2h_certified_identity_gated.json"))
m0 = mp.mpf(t['k922']['m0'])
print('k922 m0 =', mp.nstr(m0, 12))
S = mp.mpf('0'); n = 1; last = 0
while True:
    g = mp.zetazero(n).imag
    if g > 4*m0:
        break
    S += 1/(m0+g)**2
    last = n; n += 1
print('table zeros used:', last)
G = mp.zetazero(last).imag
L = mp.quad(lambda u: (mp.log(u/(2*mp.pi)))/(2*mp.pi)/(m0+u)**2, [G, mp.inf])
print('mirror sum (table)     =', mp.nstr(S, 8))
print('mirror sum PNT tail    =', mp.nstr(L, 8))
print('mirror sum (total)     =', mp.nstr(S+L, 8))
print('beast jump (mir-nomir) = 6.19705e-4  (1.750466395 - 1.74984669)')
print('ratio beast/true       =',
      mp.nstr((mp.mpf('1.750466395')-mp.mpf('1.74984669'))/(S+L), 5))
