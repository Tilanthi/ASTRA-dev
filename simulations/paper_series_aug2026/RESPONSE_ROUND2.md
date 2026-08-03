# Response to the third referee's reassessment

Two referees recommended acceptance. The third asked for minor revisions to Paper I
and either (Route A) a larger-box, extended-mode convergence test of the density
ladder in Paper II, or (Route B) substantial demotion of the unconverged quantities.

**We performed Route A. It failed.** We have therefore also implemented Route B,
on the strength of the calculation rather than in place of it.

---

## Paper II: the transverse-box test (Route A)

Four rungs of the impulsive-contraction ladder — static, high-density,
intermediate and rebounded low-density, i.e. the referee's minimum useful set and
the three positions where independent perturbation realisations already existed —
were repeated at `L_perp = 8 λ_J` (twice the production width) at **fixed cell
size**, with the problem generator modified so that the seeded axial mode set
could be extended from 12 to **24 modes**, so that a shortened maximum would be
resolved rather than accumulating at the top of the seeded range.

| A | ρ_eff/ρ0 (was) | n_max (was) | λ_max/λ_J (was) | λ_max/22H(ρ_eff) (was) |
|---|---|---|---|---|
| 0.0 static | 9.10 (1.42) | 14 (5) | 1.14 (3.20) | 0.985 (1.088) |
| 0.2 | 7.28 (3.47) | 19 (10) | 0.84 (<1.60) | 0.649 (<0.851) |
| 0.5 | 4.88 (1.83) | 20 (7), limit | <0.80 (2.29) | <0.505 (0.882) |
| 1.2 | 3.14 (0.47) | 17 (4) | 0.94 (4.00) | 0.476 (0.785) |

Against the referee's five criteria:

1. **Rank ordering survives?** *No.* The static rung now has the highest ρ_eff and the longest wavelength — the opposite of the required direction.
2. **Slope consistent with −1/2?** *No.* A censored fit to the four runs gives **+0.15**.
3. **Intrinsic scatter comparable?** Larger (0.15 vs 0.08 dex), on four points.
4. **Median λ/22H near 0.87?** *No.* 0.505 for the contracting rungs.
5. **Equilibrium and contracting still distinguishable?** **Yes, and more cleanly**: 0.985 versus 0.476–0.649, a wider separation than the 1.088 versus 0.79–1.12 obtained at the production width.

So the counterexample survives the boundary change and strengthens; the quantitative
scaling does not survive it.

We also state two caveats that stop the large-box runs being a clean replacement:
their higher densities sit closer to the Truelove floor (N_J ≈ 5–9 against 5–7 in
production), and four runs cannot constrain a slope well. The claim we make is
that the fixed-box scaling **is not reproduced when the boundary is moved**, not
that a different scaling has been measured.

### Consequent changes (Route B)

* `−0.48 ± 0.05` **removed from the abstract as a principal result**; replaced by "within a fixed transverse domain the resolved modes follow a gravitational ρ^(−1/2) scaling ... It is a fixed-box result, not a measured exponent."
* The "13 per cent residual displacement" is **removed from the abstract** and labelled in the conclusions as a fixed-box value.
* The **equilibrium-recovery control is now the sole principal result**, stated as such in the Structure paragraph, the conclusions and the abstract.
* The ladder is presented throughout as supporting, box-dependent evidence.
* "Every comparison ... is unaffected" → *"Comparisons made at the same box size preserve the qualitative ordering in the doubled-box test, but the slope and normalisation of the full ladder have not been demonstrated to be transverse-box converged."*
* New Table 8 reports the large-box runs in full.

## Paper II: other required changes

| Item | Action |
|---|---|
| Perpendicular-field inconsistency | Adopted the referee's wording verbatim: the ideal calculation resolves monolithic radial collapse and yields no axial wavelength; only the ambipolar-diffusion case remains unresolved. Abstract and conclusions corrected. |
| "periodic chain by construction" | Replaced, in both places it occurred, with the statistically-homogeneous formulation. |
| "classical mode selection is not obligatory" | Now qualified "for the idealised configuration tested here" in both abstract and conclusion (ii), with the note that one counterexample defeats necessity but does not describe the population. |
| Figure labels | `fig_schematic` rebuilt: "global L/N near-classical" → "skeleton L_skel/N: near-classical only under the adopted convention"; W_core = σ_0 and λ_turn^lim now render correctly. `fig_growthrate` regenerated with λ_turn^lim in place of λ_max. |
| "White 026a/b" | Cause identified: mnras.bst truncates a five-character year field to four characters when building the citation label. Fixed by citing the companion papers as "Paper I"/"Paper II" in text with `\nocite`; the reference list entries now read "White G. J., 2026a/2026b, MNRAS (Paper I/II, submitted)". |

## Paper I

| Item | Action |
|---|---|
| 1. Conclusion (ii) | Replaced with the referee's formulation: proximity holds under the adopted persistent-crest network, 0.06 pc association radius, all-source catalogue and fixed-width convention; other defensible choices move S_skel over a factor-of-eight envelope; it is an operational diagnostic, not a test of the cylinder model. |
| 2. Conclusion (vi) | Now restricted to uniform or regularly spaced points, with the general extent-statistic statement given separately — matching the Introduction. |
| 3. Figure 5 caption | Corrected. The caption no longer summarises all four clouds as showing a small-gap deficit; R > 1 in Orion B and Aquila (deficit) and R < 1 in Perseus and Taurus (excess) are now stated separately. |
| 4. Figure 6 caption | Replaced with: "No feature is detected at the classical scale. This does not exclude a weak periodic modulation superposed on an inhomogeneous intensity field, which these data cannot bound." |
| 5. S_skel in figures | `fig_envelope`, `fig_intermittency` and `fig_scaletests` regenerated; no figure in either paper now contains the string "global". |
| 6. Citation and label errors | "White 026a/b" fixed as above. The "Wcore = 0" and "turn 1 J" fragments were **pdftotext extraction artefacts of matplotlib mathtext**, not errors in the compiled figures; the figures were inspected at full resolution and the affected ones regenerated regardless, so the point is now moot. |

## New calculations for this round (6 runs plus a code change)

* Problem generator `filament_ambient.cpp` modified to make the seeded axial mode count a runtime parameter (`n_modes`, default 12); rebuilt as a separate binary.
* `LADBIG_A{0.0, 0.2, 0.5, 1.2}` — 4 runs at L_perp = 8 λ_J, n_modes = 24.
* `LADBOX_A{0.0, 0.6}` — 2 doubled-box runs at the original mode count, retained as the diagnostic that motivated the test.

Cumulative load-bearing count is unchanged in the manuscript text pending the
editor's decision on whether the large-box set should be folded into the
accounting table as load-bearing or as a convergence test; they are presently
listed as the latter.
