#!/usr/bin/env python3
"""
Fix all \textbf{} sections that incorrectly include math mode
"""

import re

# Read the paper
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    content = f.read()

# Fix 1: Line 205 - Full sample PM result
old_text_1 = r'''\textbf{Full sample PM result}: For completeness, the weighted mean across all 8 HGBS regions is $0.279 \pm 0.019$ pc ($\lambda/W = 2.79 \pm 0.19$), but 92\% of cores (4,658/5,069) come from regions with $N \geq 500$, making this value unreliable. \textbf{The primary observational result comes from the four small-$N$ regions ($N < 500$, where the PM/L3 artifact is minimal): Serpens ($3.31 \pm 0.97$), TMC1 ($1.95 \pm 0.56$), CRA ($2.48 \pm 0.72$), and Ophiuchus ($2.84 \pm 0.82$), giving a weighted mean of $\lambda/W = 2.6 \pm 0.4$. This is 35\% below the classical IM92 prediction of $4\times$ with large but quantified uncertainty.'''

new_text_1 = r'''\textbf{Full sample PM result}: For completeness, the weighted mean across all 8 HGBS regions is $0.279 \pm 0.019$ pc ($\lambda/W = 2.79 \pm 0.19$), but 92\% of cores (4,658/5,069) come from regions with $N \geq 500$, making this value unreliable. \textbf{The primary observational result comes from the four small-N regions} (where the PM/L3 artifact is minimal): Serpens ($3.31 \pm 0.97$), TMC1 ($1.95 \pm 0.56$), CRA ($2.48 \pm 0.72$), and Ophiuchus ($2.84 \pm 0.82$), giving a weighted mean of $\lambda/W = 2.6 \pm 0.4$. This is 35\% below the classical IM92 prediction of $4\times$ with large but quantified uncertainty.'''

content = content.replace(old_text_1, new_text_1)

# Fix 2: Table footnote that has similar issue
old_text_2 = r'''$^d$\textbf{Weighted mean is unreliable}: The weighted mean of $0.279$ pc ($\lambda/W = 2.79$) is dominated by regions with $N \geq 500$ (4,658 out of 5,069 cores = 92\% of the sample). Since the PM values for these regions are unreliable due to the $L/3$ convergence artifact, the weighted mean should \textbf{not} be interpreted as the true fragmentation spacing. A more reliable estimate comes from the PM values of small-$N$ regions only (Serpens: $3.31 \pm 0.97$, TMC1: $1.95 \pm 0.56$, CRA: $2.48 \pm 0.72$, Ophiuchus: $2.84 \pm 0.82$), which give a weighted mean of $\lambda/W = 2.6 \pm 0.4$. This represents our primary observational constraint: 35\% below the classical IM92 prediction with large but quantified uncertainty. The true population-level $\lambda/W$ for all HGBS filaments cannot be established from PM statistics alone.'''

new_text_2 = r'''$^d$\textbf{Weighted mean is unreliable}: The weighted mean of $0.279$ pc ($\lambda/W = 2.79$) is dominated by regions with $N \geq 500$ (4,658 out of 5,069 cores = 92\% of the sample). Since the PM values for these regions are unreliable due to the $L/3$ convergence artifact, the weighted mean should \textbf{not} be interpreted as the true fragmentation spacing. A more reliable estimate comes from the PM values of small-N regions only (Serpens: $3.31 \pm 0.97$, TMC1: $1.95 \pm 0.56$, CRA: $2.48 \pm 0.72$, Ophiuchus: $2.84 \pm 0.82$), which give a weighted mean of $\lambda/W = 2.6 \pm 0.4$. This represents our primary observational constraint: 35\% below the classical IM92 prediction with large but quantified uncertainty. The true population-level $\lambda/W$ for all HGBS filaments cannot be established from PM statistics alone.'''

content = content.replace(old_text_2, new_text_2)

# Fix 3: Small-N mean section with math mode inside textbf
old_text_3 = r'''\textbf{However, since the full-sample weighted mean ($\lambda/W = 2.79$) is unreliable due to the PM/L3 artifact affecting 92\% of cores, we adopt the small-$N$ regional mean ($\lambda/W = 2.6 \pm 0.4$) as our primary observational constraint.}'''

new_text_3 = r'''\textbf{However, since the full-sample weighted mean is unreliable due to the PM/L3 artifact affecting 92\% of cores, we adopt the small-N regional mean as our primary observational constraint.}'''

content = content.replace(old_text_3, new_text_3)

# Fix 4: Conclusion bullet point with math mode inside textbf
old_text_4 = r'''    \item \textbf{Consistent PM analysis reveals robust sub-Jeans spacing with quantified uncertainty}. All eight HGBS regions show $\lambda/W < 4\times$ (range: 1.95--3.46). The four small-$N$ regions ($N < 500$, where the PM/L3 artifact is minimal) give a weighted mean of $\lambda/W = 2.6 \pm 0.4$, 35\% below the classical IM92 prediction with large but quantified uncertainty. The positive correlation between $\lambda/W$ and sample size $N$ confirms the PM/L3 artifact predicted by Monte Carlo simulations. The full-sample weighted mean ($\lambda/W = 2.79$) is unreliable as 92\% of cores come from large-$N$ regions affected by the artifact. \textbf{We attempted NN analysis using publicly available HGBS skeleton data but obtained zero core-filament associations (0/5,213 cores)}, confirming that published NN values cannot be verified without access to proprietary HGBS data products. The primary observational constraint therefore comes from the small-$N$ PM mean of $\lambda/W = 2.6 \pm 0.4$.'''

new_text_4 = r'''    \item \textbf{Consistent PM analysis reveals robust sub-Jeans spacing with quantified uncertainty}. All eight HGBS regions show $\lambda/W < 4\times$ (range: 1.95--3.46). The four small-N regions (where the PM/L3 artifact is minimal) give a weighted mean of $\lambda/W = 2.6 \pm 0.4$, 35\% below the classical IM92 prediction with large but quantified uncertainty. The positive correlation between $\lambda/W$ and sample size $N$ confirms the PM/L3 artifact predicted by Monte Carlo simulations. The full-sample weighted mean ($\lambda/W = 2.79$) is unreliable as 92\% of cores come from large-N regions affected by the artifact. \textbf{We attempted NN analysis using publicly available HGBS skeleton data but obtained zero core-filament associations} (0/5,213 cores), confirming that published NN values cannot be verified without access to proprietary HGBS data products. The primary observational constraint therefore comes from the small-N PM mean of $\lambda/W = 2.6 \pm 0.4$.'''

content = content.replace(old_text_4, new_text_4)

# Fix 5: Honest assessment section
old_text_5 = r'''    \textbf{Honest assessment of scope}: The small-$N$ PM analysis rests on four regions with 718 cores total, which provides a reliable lower bound but not a complete population-level measurement. The regional variation is substantial (coefficient of variation $\sim$25\%), suggesting either real physical differences between regions or unquantified measurement uncertainties. The full-sample PM mean ($\lambda/W = 2.79$) is unreliable due to the PM/L3 artifact affecting 92\% of cores. A definitive population-level measurement requires access to proprietary HGBS core-to-filament association tables for NN analysis. Until such access is granted, the small-$N$ PM mean ($\lambda/W = 2.6 \pm 0.4$) represents our best observational constraint with explicitly quantified uncertainty.'''

new_text_5 = r'''    \textbf{Honest assessment of scope}: The small-N PM analysis rests on four regions with 718 cores total, which provides a reliable lower bound but not a complete population-level measurement. The regional variation is substantial (coefficient of variation $\sim$25\%), suggesting either real physical differences between regions or unquantified measurement uncertainties. The full-sample PM mean ($\lambda/W = 2.79$) is unreliable due to the PM/L3 artifact affecting 92\% of cores. A definitive population-level measurement requires access to proprietary HGBS core-to-filament association tables for NN analysis. Until such access is granted, the small-N PM mean ($\lambda/W = 2.6 \pm 0.4$) represents our best observational constraint with explicitly quantified uncertainty.'''

content = content.replace(old_text_5, new_text_5)

# Write the updated content
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(content)

print("Fixed all textbf with math mode issues")
