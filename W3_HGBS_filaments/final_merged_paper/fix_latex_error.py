#!/usr/bin/env python3
"""
Fix LaTeX error with \textbf and math mode
"""

import re

# Read the paper
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    content = f.read()

# Fix the problematic line - the \textbf is too long and includes math mode
# Let's break it up properly
old_text = r'''\textbf{CRITICAL OBSERVATIONAL LIMITATION: PM/L3 Convergence Artifact}. The pairwise median (PM) statistic used throughout HGBS spacing analyses converges toward $L/3$ for filaments with $N \geq 500$ cores, \textit{regardless of the true fragmentation wavelength}. Our Monte Carlo simulations (Section~\ref{sec:statistics}) demonstrate that PM measures the overall filament scale, not the fragmentation wavelength. For Orion B ($N = 1,844$, the largest sample), PM almost certainly reflects $L/3$ rather than true $\lambda/W$. \textbf{The most reliable observational constraint comes from the four small-$N$ regions ($N < 500$, where the PM/L3 artifact is minimal): Serpens ($\lambda/W = 3.31 \pm 0.97$), TMC1 ($\lambda/W = 1.95 \pm 0.56$), CRA ($\lambda/W = 2.48 \pm 0.72$), and Ophiuchus ($\lambda/W = 2.84 \pm 0.82$). These give a weighted mean of $\lambda/W = 2.6 \pm 0.4$, 35\% below the classical IM92 prediction of $4\times$ with large but quantified uncertainty. The true population-level $\lambda/W$ for all HGBS filaments cannot be established from PM statistics alone due to the $L/3$ artifact affecting 92\% of cores.'''

new_text = r'''\textbf{CRITICAL OBSERVATIONAL LIMITATION: PM/L3 Convergence Artifact}. The pairwise median (PM) statistic used throughout HGBS spacing analyses converges toward $L/3$ for filaments with $N \geq 500$ cores, \textit{regardless of the true fragmentation wavelength}. Our Monte Carlo simulations (Section~\ref{sec:statistics}) demonstrate that PM measures the overall filament scale, not the fragmentation wavelength. For Orion B ($N = 1,844$, the largest sample), PM almost certainly reflects $L/3$ rather than true $\lambda/W$.

\textbf{The most reliable observational constraint comes from the four small-$N$ regions} ($N < 500$, where the PM/L3 artifact is minimal): Serpens ($\lambda/W = 3.31 \pm 0.97$), TMC1 ($\lambda/W = 1.95 \pm 0.56$), CRA ($\lambda/W = 2.48 \pm 0.72$), and Ophiuchus ($\lambda/W = 2.84 \pm 0.82$). These give a weighted mean of $\lambda/W = 2.6 \pm 0.4$, 35\% below the classical IM92 prediction of $4\times$ with large but quantified uncertainty. The true population-level $\lambda/W$ for all HGBS filaments cannot be established from PM statistics alone due to the $L/3$ artifact affecting 92\% of cores.'''

content = content.replace(old_text, new_text)

# Write the updated content
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(content)

print("Fixed LaTeX error")
