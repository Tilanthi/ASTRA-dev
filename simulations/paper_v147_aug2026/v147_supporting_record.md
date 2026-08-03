# Supporting record for the revised manuscript (internal, not part of the paper)

## Referee items addressed

### Referee 1
1.1 lambda_turn presented as a logical bound: dGamma/dlambda does not change sign on the converged
    interval, hence lambda_peak < lambda_min,conv ~ 1.1 lambda_J *if a maximum exists at all*
    (new Eq. 7). Added a paragraph naming the physics that would produce a genuine maximum
    (stiffening EOS, ambipolar damping, viscous/turbulent drain). Abstract now says the
    simulations resolve no self-selecting wavelength.
1.2 Magnetic geometries: the imbalance is stated in the Introduction before any results; the
    seeded-helical case is described as an out-of-equilibrium dynamic pinch; Section 6.3 states
    that the magnetostatic helical framework is neither tested nor invalidated.
1.3 The conditional null is presented as a designed calibration whose outcome is that no
    quantitative significance can be assigned; the kinematic recommendation is now a firm
    methodological conclusion rather than a note.
minor Fig. 3 rounding harmonised (1.4, exact median no longer quoted separately); Athena++
    version nomenclature replaced by the release date; orphaned line feeds checked.

### Referee 2
2.1  New "What is measured and what is interpreted" paragraph in the Introduction listing the
     observables and stating that neither s_ACS nor L/N is by itself a fragmentation wavelength.
2.2  S_global reworded as the closest measurable analogue, in the notation block, Section 5.1
     and the Fig. 8 caption.
2.3  Error budget restructured into measurement / calibration / object-definition / modelling;
     the skeleton algorithm moved into the object-definition category with the explicit statement
     that the factor of two is not an uncertainty bar on one quantity.
2.4  Association fractions (41-86 per cent) added to the abstract.
2.5  Conditional-null machinery reduced in the main text; the exponent fitting, cross-validation
     and p-value definition moved to Appendix H.
2.6  Simulation conclusion reworded everywhere as "dynamical evolution allows fragmentation at a
     gravitational scale appropriate to the instantaneous state".
2.7  Eq. 7 added, as above.
2.8  Figure 8 rebuilt as two panels: (a) observed point-process statistics, (b) model scales,
     each model annotated with the observable it would predict.
2.9  Helical-equilibrium implementation obstacles moved to Appendix E.
2.10 New paragraph listing the four causes that can produce a short S_local and naming the single
     observation that separates them.
2.11 Point-process result made the primary conclusion.
2.12 Further material moved to appendices: resolution and field-geometry campaigns, ontology
     table, population-split table, convention decoder, width table, masking-radius sweep.
minor Stray spaces before punctuation removed (11); abstract restructured; Fig. 3 band relabelled
     as a reference; "30-100 times smaller" qualified; isotropic-pressure caveat added to the
     non-thermal scaling; "classical" replaced by "equilibrium-cylinder reference" throughout
     (18 substitutions).

### Referee 3
3.1  Orion B core count reconciled: 1870 deposited catalogue entries with usable coordinates used
     everywhere, with a footnote recording that Konyves et al. (2020) quote 1844. Weighted total
     updated to 3971.
3.2  The N = 4 scope sentence moved into the abstract body.
3.3  CMF argument rewritten to show the degeneracy explicitly: epsilon ~ 0.3 for lambda = 0.1-0.2 pc
     and epsilon ~ 0.05-0.1 for the equilibrium-cylinder scale both reproduce the observed peak, so
     no support is drawn from it either way.
3.4  Manual-editing entry relabelled "unvalidated proxy bound" in the error budget.
3.5  Sample sizes attached: the Pearson coefficient replaced by a qualitative statement, the
     turbulence entry marked N = 1 per point.
3.6  "Existence proof" replaced by "a counterexample, within the idealised initial-value set-up
     explored here".
minor Dagger on the Taurus row of Table 6; reader's roadmap at the start of Section 2; unreferenced
     tables now cited.

## Internal review, round 1 (structure and consistency)
- Every float now referenced; no dead cross-references; one \begin{document}.
- Conceptual figure corrected: panels (a) and (b) now carry the same ten cores so that L/N is
  genuinely unchanged, and the caption matches the figure.
- The conditional null removed from the list of "decisive" tests.
- "sub-classical" replaced by "below the reference band" (18 places), with seven grammar repairs
  afterwards.
- Orphaned sentence about the Euclidean nearest-neighbour distance moved to its proper paragraph.

## Internal review, round 2 (read-through)
- Duplicated "benchmark under non-thermal support" paragraph removed from Section 3.1.
- Broken sentence at the end of the helical-scan paragraph repaired.
- Table 13 cited twice for two different things; corrected.
- lambda_turn quoted consistently as <~ 1.1 lambda_J in Table 1, Fig. 9 and the text.
- Awkward connectives from the de-AI pass repaired (19 instances of "hence", "accordingly" and
  "in consequence" inserted mid-sentence).
- Six remaining "---" are all table entries meaning "no value", not prose em-dashes.

## Final state
29 pages, abstract 287 words, 13 figures, 19 tables, 0 undefined control sequences, 0 undefined
references, 0 duplicate sentences, 0 stray spaces before punctuation. All 42 citations resolve
and every citation context was inspected.
