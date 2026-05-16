# Theoretician Campaign Results

Campaign: THEORETICIAN_CAMPAIGN_PACKAGE_220VCPU
Server: astra-climate (224 vCPU AMD EPYC 7B13)
Date: 2026-05-01
Run by: astra-pa (Taurus agent)

## Contents

- `ANALYSIS_REPORT.md` — Full written analysis with tables, fits, and findings
- `analysis_summary.json` — Machine-readable summary with all statistics and fit params
- `all_results.csv` — Per-simulation results table (149 rows)
- `figures/` — 7 publication-quality figures (PDF + PNG)
  - fig1_stv_heatmap — STV t_frag(f,β) annotated heatmap
  - fig2_stv_powerlaws — STV power-law fits vs f and vs β
  - fig3_pfs_heatmap — PFS t_frag(f,β) annotated heatmap
  - fig4_pfs_vs_f — PFS power-law fits vs f
  - fig5_geometry_comparison — θ=0° vs θ=90° paired speedup chart
  - fig6_ncri_vs_f — NCRI near-critical t_frag with STV reference
  - fig7_parameter_space — Contour maps of t_frag(f,β) both geometries
- `sim_results/{STV,PFS,NCRI}/` — Per-simulation status.json records
- `all_results_runner.json` — Raw runner output
- `MASTER.log` — Timestamped runner log

## Key Results

- 149/150 FRAG, 0 TIMEOUT, 0 FAILED (1 sim in slow-collapse, ongoing)
- STV (θ=0°): t_frag = 1.161 ± 0.250 t_J; fit: a·f^α·β^γ
- PFS (θ=90°): t_frag = 0.636 ± 0.160 t_J; θ=90° is 2-3× faster than θ=0°
- NCRI: all near-critical (f=1.0) filaments fragment; no stability threshold
- Universal instability confirmed across full parameter space
