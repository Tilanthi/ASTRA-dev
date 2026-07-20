#!/usr/bin/env python3
"""Campaign A -- generate configs to validate the t_frag ~ f^-0.39 scaling
against a physically motivated density-contrast diagnostic (referee #4).

The paper reports 1/t_frag proportional to f^0.39 (r^2=0.999), but t_frag there
is defined by a CFL-timestep-crash trigger. The referee asks whether this
reflects physical collapse dynamics or merely the trigger. Campaign A re-runs a
representative f-grid under the validated configuration with DENSE HDF5 output,
so that the time to reach fixed density contrasts (10, 100, 1000) can be
measured independently of the CFL trigger. If 1/t_contrast scales with f with
the same exponent as the CFL-trigger time, the scaling is physical.

Grid (16 runs, ~few minutes each; collapses well before tlim):
  A_main_fgrid : f in {1.1,1.3,1.5,2.0,2.5,3.0}, beta=1.0, theta=0, seeds {42,137}
  A_betaspread : f in {1.5,2.0}, beta in {0.5,2.0}, seed 42   (beta-robustness)
All runs: Lx=8 lambda_J, cells_per_lambda=64, perturb=1e-2, odt=0.005 (dense),
tlim=0.5.
"""
import json
from pathlib import Path
from common import add

OUT = 'configs'


def main():
    manifest = {
        'purpose': 'Campaign A: density-contrast validation of the t_frag-f '
                   'scaling (referee #4)',
        'diagnostic': 't(contrast >= 10/100/1000) from dense HDF5 vs CFL-trigger '
                      'time from HST; fit 1/t ~ f^alpha for both',
        'suites': {},
        'total_sims': 0,
    }
    # main f-grid, beta=1.0, two seeds
    for f in [1.1, 1.3, 1.5, 2.0, 2.5, 3.0]:
        for s in [42, 137]:
            pid = f'A_f{f}_b1.0_th0_Lx8_s{s}'
            add(manifest, 'A_main_fgrid', pid, OUT,
                f=f, beta=1.0, theta=0.0, Lx=8, seed=s,
                perturb=1e-2, odt=0.005, tlim=0.5)
    # beta-robustness at two f values
    for f in [1.5, 2.0]:
        for beta in [0.5, 2.0]:
            pid = f'A_f{f}_b{beta}_th0_Lx8_s42'
            add(manifest, 'A_betaspread', pid, OUT,
                f=f, beta=beta, theta=0.0, Lx=8, seed=42,
                perturb=1e-2, odt=0.005, tlim=0.5)

    manifest['total_sims'] = sum(len(v) for v in manifest['suites'].values())
    Path(OUT).mkdir(exist_ok=True)
    Path(OUT, 'manifest_campaignA.json').write_text(json.dumps(manifest, indent=2))
    print('Campaign A total', manifest['total_sims'])
    for k, v in manifest['suites'].items():
        print(' ', k, len(v))


if __name__ == '__main__':
    main()
