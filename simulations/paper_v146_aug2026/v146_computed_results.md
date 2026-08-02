# Supporting computations for the revised manuscript (internal record)

## 1. Injection-recovery validation of the core-masked clustering null

A synthetic core population was drawn directly from the column-density-conditioned intensity, so
that it contains NO intrinsic clustering by construction. Each synthetic core's own column-density
imprint was then added to the map (a factor 1.76-1.77 enhancement within one association radius,
measured from the real data), and the identical masking, interpolation, refitting and null-testing
chain applied. 200 trials per cloud, 400 null realisations per trial.

| Cloud   | N cores | core boost | FP rate p<0.05 | FP rate p<0.01 | median recovered p |
|---------|---------|------------|----------------|----------------|--------------------|
| Taurus  | 463     | 1.76       | 0.725          | 0.415          | 0.017              |
| Orion B | 995     | 1.77       | 1.000          | 1.000          | 0.002              |

**The test is not calibrated.** A procedure that reports an excess on unclustered data most of the
time cannot support a detection. Part of this traces to a mismatch between the exponent used to
generate the synthetic population and the exponent refitted to the masked reconstruction, which is
itself a property of the procedure.

**Consequence: the Taurus "detection" (p = 2e-4) is withdrawn as a detection** and reported only as
the one cloud whose Fano factor exceeds its null. The three non-detections are unaffected and remain
conservative. Propagated to the abstract, Section 2.11, Table 6 caption and Conclusion (vi).

## 2. Synthetic-observation purity test of the two skeleton ontologies

A simulated filament was projected to a column-density map, a second superposed at 30 deg, a smooth
cirrus background added and the whole convolved with a 3-pixel beam, so that the true ridges are
known exactly (total injected length 1180 px).

| extraction                     | recovered/true length | frac within 1 beam | median offset (beams) |
|--------------------------------|-----------------------|--------------------|-----------------------|
| medial axis, mask > 80th pct   | 4.47                  | 0.125              | 53.5                  |
| medial axis, mask > 90th pct   | 2.33                  | 0.303              | 58.3                  |
| persistence crest, 3 sigma     | 0.07                  | 0.695              | 0.10                  |

The crest construction is incomplete but pure; the medial axis is complete-plus but impure, and the
excess length is largely not on any real ridge. This is the non-circular basis for preferring the
persistent-crest network that Referee 3 asked for, and it is reported with its limitations (one
synthetic realisation, a simplified stand-in for the published extraction, purity not completeness).
It bears directly on S_global, since impurity inflates L.

## 3. Connected-component counts (new column in Table 10)

| Region  | components retained | components contributing pairs |
|---------|---------------------|-------------------------------|
| Orion B | 378                 | 203                           |
| Aquila  | 182                 | 77                            |
| Perseus | 107                 | 32                            |
| Taurus  | 104                 | 11                            |

Taurus's 440 pairs come from only 11 components; Orion B's 699 from 203.

## 4. Sample-selection criteria (new Table 3), with real catalogue counts

Orion B 1844, Perseus 816, Aquila 749, Taurus 536 (all primary); Ophiuchus 513 (fails topology only),
TMC1 178 and CRA 239 (fail the >500 core criterion), Serpens (fails the distance criterion; no
published catalogue count is quoted, the file available to us being a derived product).

## 5. Projected Ostriker FWHM (Appendix C)
N(x) ~ [1+(x/R_flat)^2]^(-3/2), half-maximum at 0.766 R_flat, so W_FWHM = 4.33 H and
lambda_m/W_FWHM = 5.1 (5.9 under the Gaussian inner-profile convention).

## 6. Non-thermal rescaling of the benchmark
c_eff^2 = c_s^2 + sigma_nt^2 rescales lambda_m and R_flat alike, so lambda_m/W_FWHM is unchanged.
Transonic support raises both scales by 41 per cent and leaves the ratio alone. The comparison,
being in units of the measured width, is insensitive at leading order.

## 7. Editorial checks performed
- All 42 citations resolve in the bibliography; every citation context inspected and appropriate.
- 0 dead cross-references; 1 \begin{document}, 1 \end{document}, 1 \bibliography.
- 0 duplicate sentences (8-gram overlap scan); 8 near-duplicates removed.
- Internal inconsistencies fixed: "sixteen" vs "fifteen" dynamical runs; ladder figure caption title.
- De-AI: "rather than" reduced from 74 to 34 occurrences and replaced by a mix of "and not",
  ", not" and "instead of"; "therefore" from 47 to 18; grammar re-checked after substitution.
- Excess precision reduced on skeleton-limited quantities.
