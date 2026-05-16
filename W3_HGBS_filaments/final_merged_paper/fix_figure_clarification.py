#!/usr/bin/env python3
"""
Fix Figure 3 clarification and bias interpretation issues
"""

import re

# Read the paper
with open('filament_spacing_streamlined_mnras.tex', 'r') as f:
    content = f.read()

# Fix 1: Update the figure caption to clarify axis units
old_caption = r'''\caption{PM/L3 convergence validation with realistic clustered core distributions. Monte Carlo simulation of a filament with true $\lambda/W = 4.0$, testing three distribution types: uniform (baseline, blue circles), two-level hierarchical (cores within fibers, orange squares), and power-law clustered (green triangles). \textbf{Panel (a)}: PM vs N for all distributions--all converge toward $L/3$ for $N \geq 500$. \textbf{Panel (b)}: NN vs N for all distributions--ALL recover the true wavelength ($\lambda/W = 4.0 \pm 0.2$) regardless of distribution type or sample size. \textbf{Panel (c)}: PM convergence to $L/3$--all distributions show PM $\approx L/3$ at large $N$, with $<20\%$ variation across types. \textbf{Panel (d)}: PM bias vs N--smooth increase with no sharp threshold at $N = 500$. \textbf{Panel (e)}: PM/NN ratio--convergence indicator showing ratio $\sim N/2$ for $N \geq 500$. \textbf{Panel (f)}: PM $-$ L/3 deviation--confirms convergence to within $\pm 1$ $\lambda/W$ for all distributions. The L/3 convergence is ROBUST to distribution type, confirming it is a FUNDAMENTAL MATHEMATICAL PROPERTY of the pairwise median statistic.}'''

new_caption = r'''\caption{PM/L3 convergence validation with realistic clustered core distributions. Monte Carlo simulation of a filament with true $\lambda/W = 4.0$, testing three distribution types: uniform (baseline, blue circles), two-level hierarchical (cores within fibers, orange squares), and power-law clustered (green triangles). \textbf{Panel (a)}: PM/$\lambda$ vs $N$ (PM normalized by the TRUE fragmentation wavelength $\lambda$, not by filament width $W$). Values $>200$ at large $N$ reflect that PM $\to L/3$, where the total filament length $L \approx N\lambda/2 \gg \lambda$ for $N \gg 1$. \textbf{Panel (b)}: NN vs $N$ for all distributions--ALL recover the true wavelength ($\lambda/W = 4.0 \pm 0.2$) regardless of distribution type or sample size. \textbf{Panel (c)}: PM/$L$ vs $N$ (PM normalized by total filament length $L$)--all distributions show PM $\approx L/3$ at large $N$, with $<20$\% variation across types. \textbf{Panel (d)}: PM bias vs $N$--smooth increase with no sharp threshold at $N = 500$. \textbf{Panel (e)}: PM/NN ratio--convergence indicator showing ratio $\sim N/2$ for $N \geq 500$. \textbf{Panel (f)}: PM $- L/3$ deviation--confirms convergence to within $\pm 1$ $\lambda/W$ for all distributions. The L/3 convergence is ROBUST to distribution type, confirming it is a FUNDAMENTAL MATHEMATICAL PROPERTY of the pairwise median statistic.}'''

content = content.replace(old_caption, new_caption)

# Fix 2: Add clarifying sentence after the bias statements
old_text = r'''    \item \textbf{L/3 convergence is ROBUST to distribution type}: All three distributions (uniform, hierarchical, power-law) show PM $\to L/3$ for $N \geq 500$. The PM/$L/3$ ratio at $N \geq 500$ is $0.88 \pm 0.01$ (uniform), $0.93 \pm 0.02$ (hierarchical), and $0.88 \pm 0.01$ (power-law). The $<20\%$ variation across distribution types confirms that the L/3 convergence is a FUNDAMENTAL MATHEMATICAL PROPERTY of the pairwise median statistic, not an artifact of idealized assumptions.
    \item \textbf{NN accuracy is independent of distribution}: NN recovers the true wavelength ($\lambda/W = 4.0 \pm 0.2$) for ALL distributions and ALL sample sizes, confirming that NN is the appropriate statistic for fragmentation wavelength measurements.
    \item \textbf{PM bias increases smoothly with N}: Figure~\ref{fig:pm_bias_clustered} shows no sharp threshold at $N = 500$. The bias is a smooth function of sample size: $<10\%$ at $N < 100$, $50$--$100\%$ at $N = 500$, and $>500\%$ at $N = 1844$.'''

new_text = r'''    \item \textbf{L/3 convergence is ROBUST to distribution type}: All three distributions (uniform, hierarchical, power-law) show PM $\to L/3$ for $N \geq 500$. The PM/$L/3$ ratio at $N \geq 500$ is $0.88 \pm 0.01$ (uniform), $0.93 \pm 0.02$ (hierarchical), and $0.88 \pm 0.01$ (power-law). The $<20\%$ variation across distribution types confirms that the L/3 convergence is a FUNDAMENTAL MATHEMATICAL PROPERTY of the pairwise median statistic, not an artifact of idealized assumptions. \textbf{Critical clarification}: The fact that PM $\approx L/3$ (within 12\%) does NOT mean PM is close to the true fragmentation wavelength. The bias is $>500\%$ at $N = 1844$ because $L/3 \gg \lambda/W$ for large samples. For a filament with $N = 1844$ cores spaced at the true wavelength ($\sim 2$ cores per wavelength), the total filament length is $L \approx 1844 \times \lambda/2 \approx 922\lambda$, so $L/3 \approx 307\lambda$, which is $\sim 75\times$ larger than the true $\lambda/W = 4$. The apparent contradiction between ``PM is within 12\% of $L/3$'' and ``PM bias is $>500\%$'' is therefore resolved: PM converges to $L/3$ as advertised, but $L/3$ itself is the wrong scale to measure for fragmentation wavelength.
    \item \textbf{NN accuracy is independent of distribution}: NN recovers the true wavelength ($\lambda/W = 4.0 \pm 0.2$) for ALL distributions and ALL sample sizes, confirming that NN is the appropriate statistic for fragmentation wavelength measurements.
    \item \textbf{PM bias increases smoothly with N}: Figure~\ref{fig:pm_bias_clustered} shows no sharp threshold at $N = 500$. The bias is a smooth function of sample size: $<10\%$ at $N < 100$, $50$--$100\%$ at $N = 500$, and $>500\%$ at $N = 1844$.'''

content = content.replace(old_text, new_text)

# Write the updated content
with open('filament_spacing_streamlined_mnras.tex', 'w') as f:
    f.write(content)

print("Fixed figure clarification and added bias interpretation")
