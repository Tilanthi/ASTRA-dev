# Supporting record (internal; not part of the manuscript)

## Item 2 — the Ostriker FWHM error was real and is corrected

The referee's derivation is right and Table 10 was wrong. For rho(r) = rho_c [1+(r/R_flat)^2]^-2
with R_flat = sqrt(8) H:

    projected column density  Sigma(b) ∝ [1+(b/R_flat)^2]^(-3/2)
    half maximum at 1+(b/R_flat)^2 = 2^(2/3)
    W_Sigma = 2 R_flat (2^(2/3)-1)^(1/2) = 2H sqrt(8(2^(2/3)-1)) = 4.336 H
    lambda_m / W_Sigma = 22 / 4.336 = 5.07

    volume-density FWHM: 1+(r/R_flat)^2 = 2^(1/2)
    W_rho = 2 R_flat (2^(1/2)-1)^(1/2) = 3.641 H
    lambda_m / W_rho = 6.04

    lambda_m / (2 R_flat) = 22/5.657 = 3.89
    lambda_cr = 22 x (1.2/2.3) = 11.5 H ; lambda_cr / W_Sigma = 2.65

The old "W_FWHM ~ 3.9 H" was a transcription of the lambda_m/(2R_flat) = 3.89 entry into the
width row, which then propagated to "5.6". Table 10 is rebuilt with both FWHM conventions listed
separately, and the 5-6 band now has an exact origin: 5.07 (projected) to 6.04 (volume).
Appendix C carries the full derivation, Eq. C1.

## Items addressed

1  Explicit five-point hierarchy added at the end of the Introduction and referenced at the start
   of the Discussion. Points (i)-(iii) observational, (iv)-(v) theoretical.
2  As above.
3  Dynamical interpretation weakened throughout: "mode selection follows the gravitational scale
   of the evolving background, with only a modest residual displacement". Residual quantified as
   13 per cent (median of the 16 dynamical runs: lambda/22H(rho_eff) = 0.869, range 0.785-1.123).
   Two occurrences of "15 per cent" corrected to 13.
4  Section 5 retitled "Constraints on mode selection in the simulations". lambda_turn redefined in
   Table 1 as "shortest wavelength at which Gamma is demonstrably converged, hence an upper limit
   on any unresolved maximum". "the simulated fragmentation scale" removed.
5  S_global qualified as "the closest available observational proxy, provided the measured length
   corresponds to fragmentation-eligible, velocity-coherent filament", in Section 5.1 and the
   Fig. 8 caption, with the explicit statement that the proviso is not satisfied here.
6  Skeleton ontology elevated to its own paragraph in the abstract and reworded in the Conclusions:
   "the present data cannot separate the underlying physical contribution from the definitional
   one". The phrase "and not by physics" is removed.
7  "Poisson" -> "homogeneous Poisson" in the abstract, Section 2.12 and the Conclusions, with the
   qualification that whether the inhomogeneity exceeds the filament's own structure is not
   determinable from these data.
8  Eq. 11 labelled an interleaving-limit geometrical scaling, with a new sentence listing why real
   fibres violate its assumptions; Fig. 13 caption updated.
9  Section 6.3 compressed to a four-item summary; the technical obstacles remain in Appendix E and
   the campaign detail in Appendix D.
10 "representative and not tuned" -> "the adopted contrast is observationally plausible, although
   the calculation remains an idealised controlled experiment".
11 "No preferred wavelength is detected above the numerical convergence limit", with the explicit
   note that this is weaker than saying the filament has none.
12 The gamma_eff > 1 density claim withdrawn to "non-isothermal thermodynamics may eventually
   introduce a physical turnover; whether it does so at densities relevant to core formation
   requires radiative and thermal modelling beyond an isothermal calculation".
13 "identification of the region-extent bias" -> "a demonstration of the practical consequence of
   the all-pairs order statistic for filament-spacing measurements, the statistical property
   itself being elementary and long known".

## Internal review round 1
- 0 dead cross-references, 0 unreferenced floats, 1 \begin{document}.
- Key numbers cross-checked: 4.336, 5.07, 6.04, 2.65, 3.89, 0.87, -0.49, 1.1 lambda_J, 1870.
- No process-history language in the typeset PDF (7 patterns tested).

## Internal review round 2
- Enumerated hierarchy rendered (i)-(v) but the following sentence said "Points 1-3"; corrected.
- Two near-verbatim echoes between the compressed main text and the moved appendix material
  (perpendicular-field paragraph, all-pairs consequence) reworded.
- 12 mid-sentence double spaces from the earlier connective substitutions removed.
- The six remaining "---" are table entries meaning "no value".
- 0 exact duplicate sentences, 0 stray spaces before punctuation.

## Final state
29 pages, abstract 298 words, 13 figures, 19 tables, 0 undefined control sequences, 0 undefined
references. The abstract exceeds 250 words because eight separate clauses in it are required by
the reports (N=4 scope, the estimator point, both statistics, occupancy, the homogeneous-Poisson
qualification, the inhomogeneity caveat, the ontology result and the simulation reframing).
