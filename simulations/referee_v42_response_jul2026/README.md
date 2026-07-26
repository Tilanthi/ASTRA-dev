# Referee v42 Response Package — ASTRA-PA (2026-07-26)

Response to the MNRAS referee on "Core Spacing in HGBS Filaments…" (G. J. White, v42), covering the
simulation/analysis points **A2, A3, A5, A6, A7, C4–C8, the non-monotonic perpendicular beading, and the
λ/W_core→λ/W_fil arithmetic (point D)**.

## Start here
- **`report_v42_response.md`** — the full response with drop-in text and instructions for the paper writer.

## Contents
- `report_v42_response.md` — main report (read this first).
- `appendixB_campaign_table.tex` — ready-to-drop LaTeX table for A7 (Appendix B).
- `figures/`
  - `fig2_regime_corrected.pdf` / `.png` — corrected Figure 2 (C4): real newline title, correct colour key,
    non-clipped regime labels.
  - `make_fig2_corrected.py` — script that produced it.
- `analysis/`
  - `ensemble_A3_A6_D.py` — reproduces the 39-run ensemble stats (T1/arithmetic + A6 merging check).
  - `ad_trajectory.py`, `ad_lambda_trajectory.json` — ambipolar λ(t) trajectory (A2).
  - `analyze_A5.py`, `A5_progress.json`, `A5_collapse_vs_beta.png` — A5 collapse-vs-β diagnostics (running).
- `configs/`
  - `configs_A5/` (+ `gen_A5.py`) — 10 A5 magnetic-subcriticality long-integration configs (f=1.5,2.0 × β).
  - `configs_A2/` — 4 ambipolar finer-cadence reruns.
- `data/` — `rc1_beading.json`, `rc2_beading.json` (39-run ensemble), `ad_beading_final.json` (ambipolar 24/24).

## Headline conclusions
- **T1 inconsistency (D, A3):** paper text adopts T1=0.65 but numbers use 0.606. 3.27×0.606=1.98 (printed "2.0");
  ×0.65=2.12. Fix globally → recommend T1=0.65 ⇒ λ/W_fil = **2.1 ± 0.4**.
- **A6:** merging bias does NOT apply — λ measured at fragmentation onset; 38/39 runs have max bead count at the
  final snapshot, 0/39 show merging. No sims needed.
- **A2:** ambipolar runs are CFL-collapse-limited (not diffusion-wall-limited); reframe as onset wavelength.
- **A5:** the "no stability boundary above the critical line mass" apparent contradiction is a magnetic-vs-thermal
  criticality framing issue; fix wording + state the Fig-2 grid f. Long-integration test running.
- **A7:** ≈2110 Athena++ MHD runs (excl. 519+5060 RT post-processing); do not double-count the Field-Geometry
  components; confirm Fig-2 f and oblique count.
- **C4–C8:** production defects confirmed by rendering; corrected Fig 2 supplied; per-figure instructions given.
