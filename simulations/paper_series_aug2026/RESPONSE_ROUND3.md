# Response to the final reassessment — both papers, minor revision

All items are addressed. No new calculations were required; the run accounting has
been reconciled and the residual fixed-box interpretations have been removed.

## Paper I

| Item | Action |
|---|---|
| 1. Qualify 0.293L in the abstract | Adopted the referee's wording: "for points distributed uniformly along, or regularly across, a segment the all-pairs median converges on 0.293 L; more generally it behaves as an extent statistic rather than a local-spacing estimator." Abstract is 250 words. |
| 2. Table F1 heading | "Unconditional (what fragmentation theory predicts)" → **"Unconditional skeleton line-density statistics (the closest available proxy for what one-bead-per-wavelength theory predicts)"**. |
| 3. Figure and symbol inspection | Done at 200 dpi. The symbols themselves were correct, but the inspection found **two genuine layout defects** in Paper II's Figure 1, now fixed (below). |

## Paper II

| Item | Action |
|---|---|
| 1. "ρ_eff is the controlling variable" | **Removed in all three places.** Conclusion (iv) is now "Neither the imposed kick nor the density has been established as a general controlling variable", with the correlation stated for the production box and its failure in the wider domain. Section 4's two statements are explicitly restricted to L⊥ = 4 λ_J. |
| 2. Appendix A | Now ends: "Within the production domain it exhibits the expected correlation with ρ_eff, but that correlation is not reproduced when the transverse boundary is moved. The timescale argument is therefore a plausible interpretation of the fixed-box ordering, not a demonstrated general law." |
| 3. Figure 4 caption | Now **opens** with: "All panels refer to the production domain, L⊥ = 4 λ_J. The apparent ρ_eff^(−1/2) relation in panel (c) and the 0.87 median normalisation in panel (d) are not reproduced in the wider-domain test of Table 8 and must not be read as transverse-box-converged results." |
| 4. Run accounting | Reconciled. Two rows added — "Contraction ladder, doubled transverse domain: 2" (the Section 2 diagnostic) and "Contraction ladder, larger transverse domain, extended axial modes: 4" (the Section 4 convergence test). **Load-bearing 87 → 93; total 2264 → 2270.** Updated in the table header, the table total, the Section 2 text and the Data Availability statement. Arithmetic verified: 93 load-bearing rows + 2177 exploratory rows = 2270. |
| 5. Which "static" configuration | Made explicit. Table 8's A = 0 entry is the **static rung of the impulsive-contraction ladder**, initialised from the relaxed Ostriker profile with no imposed inward velocity; it is *not* the separately prepared drag-relaxed equilibrium-recovery control of Section 3, which was not repeated in the wider domain. The abstract now says "The distinction between the static and contracting **ladder states** also survives in a larger transverse domain", and the surrounding text names the contrast in its ladder form. |
| 6. Estimator sentence | Adopted: "The equilibrium-versus-contracting contrast is robust to the grid and box changes tested here, although single-mode and comoving-coordinate checks remain desirable validation of the detailed growth-rate ordering." |

## Figure 1 of Paper II — two defects found and fixed during the requested inspection

The reported malformed labels were `pdftotext` artefacts, as suspected; at 200 dpi
W_core = σ_0, W_form, W_fil, s_ACS,med, L_skel and λ_turn^lim all render correctly.
The inspection did however find two real problems:

1. The `W_form` and `W_fil` annotations **overflowed the right-hand edge of panel (a)
   and printed over panel (b)**. Both are now placed inside the axes.
2. The intra-group spacing arrow had collapsed to a marker-sized glyph. It now spans
   the group extent and is labelled accordingly.

A literal `--` in one matplotlib label (rendering as two hyphens rather than an
en-dash in "5–6 W") was also corrected.

The schematic caption was additionally brought into line with Paper I's revised
terminology: "filament-averaged line density L/N is near-classical" →
"skeleton-averaged line density L_skel/N approaches the classical value under the
conventions adopted in Paper I but not under others".

## Final state

| | Pages | Figures | Tables | Abstract |
|---|---|---|---|---|
| Paper I | 19 | 8 | 16 | 250 words |
| Paper II | 15 | 4 | 10 | 249 words |

Both compile with zero undefined control sequences, zero undefined references, no
unreferenced floats and no duplicated sentences. No figure in either paper contains
the string "global". The two papers share no prose.
