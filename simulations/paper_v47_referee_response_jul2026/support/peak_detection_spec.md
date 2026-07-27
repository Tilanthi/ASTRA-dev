# Longitudinal beading peak-detection algorithm (for §4 methods; answers R2-5, R2-6.1)

For each HDF5 snapshot:
1. Assemble the global density cube ρ(x,y,z) from the per-MeshBlock arrays (LogicalLocations).
2. Collapse to a 1-D longitudinal profile by transverse averaging: p(x) = ⟨ρ⟩_{y,z}(x).
3. Normalise: d(x) = p(x)/⟨p⟩ − 1; compute rms σ = std(d).
4. Peak criterion: a cell i is a peak if d(i) > d(i−1), d(i) ≥ d(i+1), and d(i) > max(3σ, 0.02)
   (prominence threshold; the 0.02 floor prevents spurious peaks in near-uniform profiles).
5. Boundary exclusion: the two end cells on each side are excluded.
6. Spacing: λ = median of adjacent-peak separations, including the periodic-wrap separation
   (L_x − (x_last − x_first)) for periodic boxes.
7. Persistence/measurement epoch: λ is reported at the snapshot with the MAXIMUM interior peak count
   (fragmentation onset / finest pattern), not at a fixed time and not from the CFL watchdog.
8. Minimum peak separation is set implicitly by the grid (dx) and the prominence threshold; no
   additional smoothing is applied.

Units: box L_x in λ_J; positions and λ in λ_J; convert to λ/W_core = λ/0.3, and to observable
λ/W_fil via the T1 factor (§3.1). This is the identical algorithm used for all beading measurements
in the paper (ASTRA analysis code `analyze_v34.py` / `ad_trajectory.py`, released with the data).
