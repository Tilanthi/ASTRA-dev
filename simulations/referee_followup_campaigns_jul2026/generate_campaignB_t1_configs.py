#!/usr/bin/env python3
"""Campaign B -- generate filament configs for the synthetic-HGBS T1
forward model (referee #5).

The T1 width-normalisation (0.606, Plummer-corrected ~0.71) dominates every
simulation-observation comparison but was derived via a Gaussian-convolution
proxy. The referee asks for a direct forward model: simulate filaments, build a
synthetic column-density map, convolve with the HGBS beam, and fit with the SAME
Plummer methodology used on real HGBS data. Campaign B produces the density
cubes; the pipeline synthetic_hgbs_forward_model.py does the observation +
fitting and measures W_form, W_gaussian, W_plummer, hence T1, directly.

Grid (11 runs):
  B_t1_grid : f in {1.0,1.5,2.0} x beta in {0.5,1.0,2.0}, seed 42
            + fiducial (f=1.5,beta=1.0) seeds {137,251} for scatter
All runs: theta=0, Lx=8 lambda_J, perturb=1e-2, odt=0.02 (moderate; the pipeline
selects the pre-collapse formation epoch), tlim=0.3.
"""
import json
from pathlib import Path
from common import add

OUT = 'configs'


def main():
    manifest = {
        'purpose': 'Campaign B: synthetic-HGBS T1 forward model (referee #5)',
        'pipeline': 'synthetic_hgbs_forward_model.py: project -> beam-convolve '
                    '-> Plummer-2 + Gaussian fits -> W_form/W_plummer = T1',
        'suites': {},
        'total_sims': 0,
    }
    for f in [1.0, 1.5, 2.0]:
        for beta in [0.5, 1.0, 2.0]:
            pid = f'B_f{f}_b{beta}_th0_Lx8_s42'
            add(manifest, 'B_t1_grid', pid, OUT,
                f=f, beta=beta, theta=0.0, Lx=8, seed=42,
                perturb=1e-2, odt=0.02, tlim=0.3)
    # fiducial scatter
    for s in [137, 251]:
        pid = f'B_f1.5_b1.0_th0_Lx8_s{s}'
        add(manifest, 'B_t1_grid', pid, OUT,
            f=1.5, beta=1.0, theta=0.0, Lx=8, seed=s,
            perturb=1e-2, odt=0.02, tlim=0.3)

    manifest['total_sims'] = sum(len(v) for v in manifest['suites'].values())
    Path(OUT).mkdir(exist_ok=True)
    Path(OUT, 'manifest_campaignB.json').write_text(json.dumps(manifest, indent=2))
    print('Campaign B total', manifest['total_sims'])
    for k, v in manifest['suites'].items():
        print(' ', k, len(v))


if __name__ == '__main__':
    main()
