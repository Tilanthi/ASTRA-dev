# v48 Referee-Response Support (ASTRA-PA computational deliverables)

Companion to `correction_plan_v48.md`. Each file backs a specific referee item (see the plan's Part V).

- `figures/fig7_eos_nocaption.png/.pdf` — P1 fix (EOS figure without baked-in caption).
- `figures/T1_distribution.png` + `T1_distribution.json` — R2-11.4 (T1 median 0.607 vs adopted 0.65 flag).
- `truelove_check.json` — R1-M3 / R2-13.5 (near-crit longitudinal Truelove-satisfied at spacing epoch; perp ambipolar Truelove-violated → resolution-limited).
- `mass_to_flux_mapping.json` — R2-4 (μ_Φ/μ_crit ∝ f√β; low-β runs NOT strictly subcritical → rename Regime I).
- `ambient_ensemble_table.csv` + `ambient_ensemble_summary.json` — R2-12 (39-run table; periodic vs reflecting KS p=0.17).
- `perp_field_consolidated.csv` + `_summary.json` — R2-15 (perpendicular taxonomy + 96-vs-18 reconciliation; 0.85≈0.81 same).
- `oblique_fit.json` — R2-3.5 (R²=0.985 but 3 points → not a validation).
- `rt_two_proportion.json` — R1-minor (z=6.25, p=4×10⁻¹⁰; only if §6 kept).
- `peak_detection_spec.md` — R2-5/R2-6.1 (beading peak-detection algorithm).
- `ambipolar_implementation.md` — R2-16 / R1-minor η_AD (induction eq + η_AD→physical mapping).
- `figure_pipeline_grep.md` — P1/C8 literal-\n audit.

PENDING (ASTRA-PA can deliver on request/with time): multi-resolution λ/W convergence; per-image
forward-model of the 39 snapshots → direct λ/W_obs; axial/radial mode-amplitude(t); extra ambient
seeds + box variation; dispersion-relation growth-rate plot (needs Glenn's exact F(kR)).

NEEDS GLENN'S OBSERVATIONAL DATA (HGBS maps/catalogues/DisPerSE code): region-specific deconvolved
widths (top priority, R1-M1/R2-7); NN-pipeline reproducibility (R2-6); hierarchical bootstrap +
population/completeness splits (R2-8/10); mock-observation blending (R2-9).
