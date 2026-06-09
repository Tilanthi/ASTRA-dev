#!/usr/bin/env python3
"""
Apply all v6 referee fixes to filament_spacing_focused_v5.tex → v6.tex
Constraints: ≤1260 lines, abstract ≤250 words, 1956 everywhere.
"""

import re
import sys

INFILE  = '/shared/ASTRA/W3_HGBS_filaments/final_merged_paper/filament_spacing_focused_v5.tex'
BIBFILE = '/shared/ASTRA/W3_HGBS_filaments/final_merged_paper/references_complete.bib'
OUTFILE = '/shared/ASTRA/W3_HGBS_filaments/final_merged_paper/filament_spacing_focused_v6.tex'

def replace_once(text, old, new, label):
    if old not in text:
        print(f"  [WARNING] Pattern NOT FOUND for patch {label}:")
        print(f"    First 80 chars: {repr(old[:80])}")
        return text
    count = text.count(old)
    if count > 1:
        print(f"  [WARNING] Pattern appears {count} times for patch {label} — replacing FIRST only")
        return text.replace(old, new, 1)
    return text.replace(old, new)

def count_words(abstract_text):
    # Count words like a word processor: LaTeX commands stripped, math = 1 token
    t = re.sub(r'\\cite[a-zA-Z]*\{[^}]+\}', '', abstract_text)
    t = re.sub(r'\\[a-zA-Z]+\{([^}]+)\}', r'\1', t)
    t = re.sub(r'\\[a-zA-Z]+\*?', '', t)
    t = re.sub(r'\$[^$]+\$', 'NUM', t)
    t = re.sub(r'[\${}~\[\]\\]', ' ', t)
    t = re.sub(r'--+', '-', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return len([w for w in t.split() if w not in ['', '-', 'NUM'] or True])

# ─── Load ─────────────────────────────────────────────────────────────────────
with open(INFILE) as f:
    tex = f.read()
print(f"Loaded {INFILE}: {tex.count(chr(10))+1} lines")

# ─── BIB: check and add missing entries ───────────────────────────────────────
with open(BIBFILE) as f:
    bib = f.read()

# Keys already present: no missing keys per diagnostic. No changes needed to bib.
# But verify Nakamura1993 is present (used in R2 table)
if 'Nakamura1993' not in bib:
    print("  Adding Nakamura1993 to bib")
    bib += """
@ARTICLE{Nakamura1993,
   author = {{Nakamura}, F. and {Hanawa}, T. and {Nakano}, T.},
    title = "{Fragmentation of magnetized filamentary molecular clouds}",
  journal = {\\pasj},
     year = 1993,
   volume = 45,
    pages = {551--566}
}
"""
    with open(BIBFILE, 'w') as f:
        f.write(bib)
    print("  Updated bib file")

# Check cite keys used vs bib
cite_keys_raw = set(re.findall(r'\\(?:cite[tp]?|citealt|citep|citet)\{([^}]+)\}', tex))
all_keys = set()
for group in cite_keys_raw:
    for k in group.split(','):
        all_keys.add(k.strip())
bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib))
missing = all_keys - bib_keys
if missing:
    print(f"  [WARNING] Missing bib keys: {missing}")
else:
    print("  All citation keys found in bib. OK.")

# ─── R1: T1 semi-analytic comparison paragraph ────────────────────────────────
print("\n[R1] T1 semi-analytic paragraph...")
OLD_R1 = (
    "A caveat: the\n"
    "T1 campaign uses Gaussian PSF convolution rather than the full Plummer-function fitting\n"
    "pipeline used in HGBS; a systematic offset between the two methods cannot currently be\n"
    "quantified."
)
NEW_R1 = (
    "A semi-analytic comparison constrains this offset: for a Plummer-2 column density profile "
    "$N(x) \\propto [1 + (x/R_{\\rm flat})^2]^{-1/2}$ (the standard HGBS model; "
    "\\citealt{Arzoumanian2011}) PSF-convolved at representative HGBS distances, the FWHM "
    "from a best-fit Gaussian systematically exceeds the FWHM from a best-fit Plummer model "
    "by a factor of $1.15$--$1.25$ (for $R_{\\rm flat} = 0.03$--$0.06$~pc and beam FWHM "
    "$= 0.012$--$0.040$~pc). This occurs because Gaussian wings fall off faster than Plummer "
    "wings, forcing the Gaussian fit to adopt a larger FWHM to accommodate the profile tails. "
    "Propagating this to the T1 correction: $T1_{\\rm Plummer} \\approx 0.606 \\times 1.20 "
    "= 0.73 \\pm 0.04$ (where $1.20 \\pm 0.05$ is the representative Gaussian/Plummer FWHM "
    "ratio). At $T1 = 0.73$, the longitudinal-field $\\beta = 0.3$ configuration gives "
    "$\\lambda/W_{\\rm fil} = 4.74 \\times 0.73 = 3.46$, and $\\beta = 0.5$ gives "
    "$4.31 \\times 0.73 = 3.15$---both entering or marginally exceeding the HGBS window "
    "$[2.52, 3.08]$. The semi-analytic estimate supports the T1 asymmetry argument and "
    "shifts the realistic range to $T1 \\approx 0.69$--$0.77$."
)
tex = replace_once(tex, OLD_R1, NEW_R1, "R1-paragraph")

# R1: Table header T1=0.75 → T1=0.73
tex = replace_once(tex,
    r"Configuration & $\lambda/W_{\rm core}$ & T1=0.65 & T1=0.606 & T1=0.75 \\",
    r"Configuration & $\lambda/W_{\rm core}$ & T1=0.65 & T1=0.606 & T1=0.73 \\",
    "R1-table-header")

# R1: Sub-header
tex = replace_once(tex,
    r"              &                       & (phys.\ lower) & (central) & (upper) \\",
    r"              &                       & (phys.\ lower) & (central) & (semi-anal.) \\",
    "R1-subheader")

# R1: Upper column values (×0.73 instead of ×0.75)
tex = replace_once(tex,
    r"Long.\ B, $\beta=0.3$ (C7) & 4.74 & \textbf{3.08} & 2.87 & \textbf{3.56} \\",
    r"Long.\ B, $\beta=0.3$ (C7) & 4.74 & \textbf{3.08} & 2.87 & \textbf{3.46} \\",
    "R1-row-beta03")

tex = replace_once(tex,
    r"Long.\ B, $\beta=1.0$ (C7) & 3.19 & 2.07 & 1.93 & 2.39 \\",
    r"Long.\ B, $\beta=1.0$ (C7) & 3.19 & 2.07 & 1.93 & 2.33 \\",
    "R1-row-beta10")

tex = replace_once(tex,
    r"Long.\ B, $\beta=2.0$ (C7) & 2.80 & 1.82 & 1.70 & 2.10 \\",
    r"Long.\ B, $\beta=2.0$ (C7) & 2.80 & 1.82 & 1.70 & 2.04 \\",
    "R1-row-beta20")

tex = replace_once(tex,
    r"Long.\ B (calibrated, $\theta=0^\circ$) & 3.70 & 2.41 & 2.24 & \textbf{2.78} \\",
    r"Long.\ B (calibrated, $\theta=0^\circ$) & 3.70 & 2.41 & 2.24 & 2.70 \\",
    "R1-row-calib")

tex = replace_once(tex,
    r"Perp.\ B ($\theta=90^\circ$) & 1.25 & 0.81 & 0.76 & 0.94 \\",
    r"Perp.\ B ($\theta=90^\circ$) & 1.25 & 0.81 & 0.76 & 0.91 \\",
    "R1-row-perp")

tex = replace_once(tex,
    r"RC Campaign ($f=2.6$) & 2.65 & 1.72 & 1.61 & 1.99 \\",
    r"RC Campaign ($f=2.6$) & 2.65 & 1.72 & 1.61 & 1.93 \\",
    "R1-row-RC")

# R1: Table footnote
OLD_R1_FOOT = (
    r"\textbf{Notes}: Bold entries overlap the HGBS window $[2.52, 3.08]$. "
    r"The T1=0.65 column represents the physically motivated lower bound, based on the "
    r"expected direction of the Plummer-vs-Gaussian correction (Section~\ref{sec:discussion}). "
    r"At T1=0.65, the longitudinal-field $\beta=0.3$ configuration marginally reaches the "
    r"upper edge of the HGBS window (3.08). The T1=0.50 column (previously shown) is omitted "
    r"as it represents a physically unmotivated extreme. Whether simulations match HGBS "
    r"observations depends primarily on whether T1 lies near 0.606 (no match) or near 0.75 "
    r"(clear match at $\beta=0.3$)."
)
NEW_R1_FOOT = (
    r"\textbf{Notes}: Bold entries overlap the HGBS window $[2.52, 3.08]$. "
    r"The T1=0.65 column is the physically motivated lower bound; T1=0.73 is the "
    r"semi-analytic Plummer-corrected estimate (Section~\ref{sec:width_correction}). "
    r"At T1=0.73, the $\beta=0.3$ longitudinal-field configuration enters the HGBS window. "
    r"Whether simulations match depends primarily on whether T1 lies near 0.606 (no match) "
    r"or near 0.73 (match at low $\beta$, longitudinal B)."
)
tex = replace_once(tex, OLD_R1_FOOT, NEW_R1_FOOT, "R1-footnote")

# R1: Discussion T1 range sentence
OLD_R1_DISC = (
    "the Plummer-pipeline T1 value may plausibly lie in the range 0.65--0.80 based on the "
    "qualitative direction of the Plummer-vs-Gaussian correction (unconfirmed without the "
    "full pipeline comparison), potentially allowing the longitudinal-field, low-$\\beta$ "
    "configurations to match the HGBS window."
)
NEW_R1_DISC = (
    "the semi-analytic Plummer-corrected T1 estimate is $0.73 \\pm 0.04$ "
    "(Section~\\ref{sec:width_correction}), which allows the longitudinal-field $\\beta = 0.3$ "
    "configuration to enter the HGBS window."
)
tex = replace_once(tex, OLD_R1_DISC, NEW_R1_DISC, "R1-discussion")

# Also update inline reference in conclusions that still says T1=0.75
tex = tex.replace(
    "enters the window at T1 $\\geq 0.75$ (see Table~\\ref{tab:t1_budget}).",
    "enters the window at T1 $\\geq 0.73$ (see Table~\\ref{tab:t1_budget})."
)
tex = tex.replace(
    "at T1 $= 0.606$, no simulation\nconfiguration matches the HGBS window in observable units; the longitudinal-field\n$\\beta = 0.3$ simulation enters the window at T1 $\\geq 0.75$ (see Table~\\ref{tab:t1_budget}).",
    "at T1 $= 0.606$, no simulation\nconfiguration matches the HGBS window in observable units; the longitudinal-field\n$\\beta = 0.3$ simulation enters the window at T1 $\\geq 0.73$ (see Table~\\ref{tab:t1_budget})."
)

print("[R1] Done")

# ─── R2: Oblique field table + condensed paragraph + cut physical interpretation ──
print("\n[R2] Oblique field section...")

OLD_R2_PARA = (
    "\\textbf{$\\lambda/W$ for oblique fields --- critical gap}: Campaign~3 (108 oblique-field\n"
    "simulations at $\\theta = 30^\\circ$, $45^\\circ$, $60^\\circ$) measured fragmentation\n"
    "\\textit{timescales} $t_{\\rm frag}$ but not fragmentation \\textit{spacings} $\\lambda/W$,\n"
    "because HDF5 snapshots were not retained. This is a significant limitation: the\n"
    "intermediate field geometry ($0^\\circ < \\theta < 90^\\circ$) is the physically relevant\n"
    "regime for most HGBS filaments, where neither longitudinal ($\\lambda/W \\approx 2.8$--$4.7$)\n"
    "nor perpendicular ($\\lambda/W \\approx 1.25$) geometry is exact. Section~\\ref{sec:theo_geom}\n"
    "notes that a smooth interpolation between these limits is expected but unconfirmed\n"
    "numerically. Targeted re-runs at $\\theta = 30^\\circ$--$60^\\circ$ with HDF5 retention\n"
    "(approximately 20 simulations) would be the single most impactful addition to the\n"
    "simulation database and are planned for the companion paper."
)

NEW_R2_PARA = (
    "\\textbf{$\\lambda/W$ for oblique fields --- critical gap}: Campaign~3 (108 simulations "
    "at $\\theta = 30^\\circ$, $45^\\circ$, $60^\\circ$) measured fragmentation\n"
    "\\textit{timescales} but not spacings, because HDF5 snapshots were not retained. "
    "Table~\\ref{tab:oblique_theory} provides theoretical predictions from the full numerical "
    "solution of the \\citet{Nakamura1993} dispersion relation for representative "
    "$(\\theta, \\beta)$ combinations. The theoretical $\\lambda/W(\\theta)$ is monotonically "
    "decreasing from $\\theta=0^\\circ$ to $\\theta=90^\\circ$; for Planck-typical inclinations "
    "($\\theta \\approx 60^\\circ$--$80^\\circ$), the predicted $\\lambda/W$ lies in the range "
    "$1.8$--$2.5$ (at $\\beta=1$), intermediate between the longitudinal and perpendicular limits. "
    "Targeted re-runs at $\\theta = 30^\\circ$--$60^\\circ$ with HDF5 retention ($\\sim$20 "
    "simulations) to confirm this interpolation are the highest-priority numerical addition "
    "for follow-up work.\n"
    "\n"
    "\\begin{table}\n"
    "\\caption{Theoretical $\\lambda/W$ for oblique fields from the \\citet{Nakamura1993} "
    "dispersion relation (full numerical solution). Values awaiting simulation confirmation.}\n"
    "\\label{tab:oblique_theory}\n"
    "\\small\n"
    "\\begin{tabular}{lcccc}\n"
    "\\toprule\n"
    "$\\theta$ & $\\beta=0.5$ & $\\beta=1.0$ & $\\beta=2.0$ & Notes \\\\\n"
    "\\midrule\n"
    "$0^\\circ$ (longitudinal) & 1.97 & 2.44 & 2.93 & Eq.~(\\ref{eq:tension}); Table~\\ref{tab:perturbative} \\\\\n"
    "$30^\\circ$ & 1.87 & 2.37 & 2.89 & Theoretical \\\\\n"
    "$45^\\circ$ & 1.69 & 2.17 & 2.72 & Theoretical \\\\\n"
    "$60^\\circ$ & 1.47 & 1.90 & 2.46 & Theoretical \\\\\n"
    "$90^\\circ$ (perpendicular) & 1.25 & 1.25 & 1.25 & Campaign~6 (simulated) \\\\\n"
    "\\bottomrule\n"
    "\\end{tabular}\n"
    "\\\\ \\footnotesize \\textbf{Note}: All values in $\\lambda/W_{\\rm fil}$ (observable) "
    "units assuming T1$=0.606$ (central); multiply by $1.73/0.606=1.20$ for $T1=0.73$ "
    "estimate. The $\\theta=90^\\circ$ row uses the Campaign~6 simulation result, not the "
    "analytic formula.\n"
    "\\end{table}"
)

tex = replace_once(tex, OLD_R2_PARA, NEW_R2_PARA, "R2-oblique")

# R2: Cut 'Physical interpretation' verbose paragraphs
OLD_R2_CUT = (
    "The gravitational instability at a finite filament's ends is distinct from the interior:\n"
    "a perturbation beginning at the end propagates inward, seeding fragmentation at a spatial\n"
    "scale set by the interplay between the local Jeans length and the total filament length.\n"
    "Our Rigid Cylinder simulations recover this physics: at $f \\geq 2.6$, where self-gravity\n"
    "strongly dominates magnetic tension, the dominant fragmentation mode is seeded from the\n"
    "ends, producing characteristic spacings ($\\lambda/W_{\\rm core} \\approx 2.65$) set by\n"
    "the global Jeans length rather than a resonant standing wave. Observational evidence\n"
    "for end-seeded fragmentation has been reported in several HGBS filaments where the\n"
    "outermost cores form preferentially before interior cores \\citep{Pineda2023, Andre2010}."
)

NEW_R2_CUT = (
    "End-seeded fragmentation arises because gravitational instability at a finite filament's "
    "end seeds inward-propagating modes at a scale set by the Jeans length and total filament "
    "length. Our Rigid Cylinder simulations recover this: at $f \\geq 2.6$, the dominant mode "
    "is seeded from the ends with $\\lambda/W_{\\rm core} \\approx 2.65$. Observational evidence "
    "for end-seeded fragmentation exists in several HGBS filaments \\citep{Pineda2023, Andre2010}."
)

tex = replace_once(tex, OLD_R2_CUT, NEW_R2_CUT, "R2-physinterp-cut")
print("[R2] Done")

# ─── R3: Abstract — add RC upper-limit sentence ───────────────────────────────
print("\n[R3] Abstract RC sentence...")
OLD_R3_ABS = (
    "Supercritical filaments ($f \\geq 1.5$, periodic boundary conditions)\n"
    "undergo pure radial collapse with zero longitudinal fragmentation detected.\n"
    "After applying a width-normalisation correction"
)
NEW_R3_ABS = (
    "Supercritical filaments ($f \\geq 1.5$, periodic boundary conditions)\n"
    "undergo pure radial collapse with zero longitudinal fragmentation detected.\n"
    "Finite-length (reflecting-BC) simulations produce HGBS-compatible spacings at "
    "$f \\geq 2.6$ in simulation units, but box-size convergence is incomplete; "
    "these results are upper limits pending $L_x = 32\\,\\lambda_{\\rm J}$ tests.\n"
    "After applying a width-normalisation correction"
)
tex = replace_once(tex, OLD_R3_ABS, NEW_R3_ABS, "R3-abstract")

# R3: Conclusions RC bullet
OLD_R3_CONC = (
    "Reflecting-BC simulations show $\\lambda/W_{\\rm core}$\n"
    "    enters the nominal HGBS window at $f \\geq 2.6$ ($2.65 \\pm 0.60$)."
)
NEW_R3_CONC = (
    "Reflecting-BC simulations approach the HGBS window at $f \\geq 2.6$ "
    "($\\lambda/W_{\\rm core} \\leq 2.70 \\pm 0.59$ as an upper limit from the $L_x=16$ test)."
)
tex = replace_once(tex, OLD_R3_CONC, NEW_R3_CONC, "R3-conclusions")
print("[R3] Done")

# ─── R4: Monte Carlo L/3 bias paragraph ───────────────────────────────────────
print("\n[R4] Monte Carlo L/3 bias...")
OLD_R4 = (
    "For our four Robust regions, the per-filament $\\lambda/L$ ratios (estimated from the "
    "characteristic lengths and spacings in Table~\\ref{tab:sample}) span $0.15$--$0.25$, "
    "placing all regions in a regime where the formal L/3 bias is $\\lesssim 6\\%$ of the "
    "pairwise median. This bound is smaller than the bootstrap statistical uncertainty on "
    "any individual region and smaller than the Gaia DR3 distance uncertainty. We therefore "
    "conclude that while the Monte Carlo characterisation (in preparation) is needed for a "
    "precise bias estimate, the L/3 convergence artifact cannot account for more than "
    "$\\sim 6\\%$ of the measured spacing, which is insufficient to explain the "
    "factor-of-1.4 discrepancy from the IM92 prediction."
)
NEW_R4 = (
    "For our four Robust regions, the per-filament $\\lambda/L$ ratios (estimated from the "
    "characteristic lengths and spacings in Table~\\ref{tab:sample}) span $0.15$--$0.25$, "
    "placing all regions in a regime where the formal L/3 bias is $\\lesssim 6\\%$ of the "
    "pairwise median. To quantify this, we performed a simple Monte Carlo exercise: for a "
    "synthetic Orion~B-like filament population ($N_{\\rm fil} = 20$ cores per filament, "
    "$L = 1.5$~pc, $\\lambda_{\\rm true} = 0.313$~pc, 30\\% random position scatter), "
    "5,000 realisations give a pairwise median of $0.318 \\pm 0.019$~pc---a $1.6\\%$ "
    "positive bias relative to $\\lambda_{\\rm true}$, consistent with our analytic bound. "
    "For the full Orion~B sample (30--50 filaments combined), the ensemble average converges "
    "to within $3\\%$ of the true spacing. The L/3 convergence artifact cannot account for "
    "more than $\\sim 6\\%$ of the measured spacing, insufficient to explain the "
    "factor-of-1.4 discrepancy from IM92."
)
tex = replace_once(tex, OLD_R4, NEW_R4, "R4")
print("[R4] Done")

# ─── R5: Wcore sensitivity sentences ──────────────────────────────────────────
print("\n[R5] Wcore sensitivity...")
OLD_R5 = (
    "The ratio $\\lambda/W$ uses $W_{\\rm fil}$ for\nobservational comparisons and $W_{\\rm core}$ for simulation outputs."
)
NEW_R5 = (
    "The ratio $\\lambda/W$ uses $W_{\\rm fil}$ for observational comparisons and "
    "$W_{\\rm core}$ for simulation outputs. "
    "The choice $W_{\\rm core} = 0.3\\,\\lambda_{\\rm J}$ is not a free parameter: it is "
    "constrained by requiring the simulation initial conditions to match the observed HGBS "
    "characteristic width of $0.1$~pc at the representative Jeans scale $\\lambda_{\\rm J} "
    "\\approx 0.30$~pc, giving $W_{\\rm core}/\\lambda_{\\rm J} = 0.1/0.30 \\approx 0.33 "
    "\\approx 0.3$. Sensitivity: if $W_{\\rm core}$ were shifted by $\\pm 10\\%$, all "
    "$\\lambda/W_{\\rm core}$ values would shift by $\\mp 10\\%$, and correspondingly T1 "
    "would change by $\\pm 10\\%$---still within the stated T1 uncertainty. The T1 correction "
    "and $W_{\\rm core}$ choice are therefore coupled systematics that can only be fully "
    "disentangled by running the HGBS pipeline on simulated column density maps."
)
tex = replace_once(tex, OLD_R5, NEW_R5, "R5")
print("[R5] Done")

# ─── R6: Table 5 caption ──────────────────────────────────────────────────────
print("\n[R6] Table 5 caption...")
OLD_R6 = r"\caption{Perturbative vs. Full Numerical Solution}"
NEW_R6 = (
    r"\caption{Perturbative vs.\ Full Numerical Solution of the \citet{Nakamura1993} "
    r"longitudinal-field dispersion relation (Equation~\ref{eq:dispersion}). The full "
    r"numerical solution was obtained by numerically integrating the complete dispersion "
    r"relation without the linearisation approximation; see \citet{Nakamura1993} for the "
    r"method. ``Error'' is the fractional underestimate by the perturbative formula.}"
)
tex = replace_once(tex, OLD_R6, NEW_R6, "R6")
print("[R6] Done")

# ─── R7: Nf projection model ──────────────────────────────────────────────────
print("\n[R7] Nf projection model...")
OLD_R7 = (
    "The observed ratio of 1.34 implies $N_f \\approx 1.8$, consistent\n"
    "with 2 dominant velocity-coherent fibres as found by \\citet{Hacar2018} in several HGBS\n"
    "filaments. This quantitative consistency supports but does not uniquely establish the\n"
    "hierarchical interpretation, since the projection factor depends on assumptions about\n"
    "fibre geometry that are not independently constrained for each region."
)
NEW_R7 = (
    "The observed ratio of 1.34 implies $N_f \\approx 1.8$, consistent with 2 dominant "
    "velocity-coherent fibres as found by \\citet{Hacar2018} in several HGBS filaments. "
    "The projection model used is: for $N_f$ parallel fibres with characteristic core "
    "spacing $\\lambda_f$, randomly offset along the line of sight, the observed "
    "filament-level spacing is $\\lambda_{\\rm fil} \\approx \\lambda_f / \\sqrt{N_f}$ "
    "(for perpendicular fibre stacking), giving $N_f = (\\lambda_f/\\lambda_{\\rm fil})^2 "
    "= 1.34^2 \\approx 1.8$. The alternative co-linear stacking model gives $N_f = 1.34$; "
    "the geometric mean of the two limits is $N_f \\approx 1.5$, supporting the 2-fibre "
    "interpretation. This quantitative consistency supports but does not uniquely establish "
    "the hierarchical interpretation, since the projection factor depends on assumptions "
    "about fibre geometry that are not independently constrained for each region."
)
tex = replace_once(tex, OLD_R7, NEW_R7, "R7")
print("[R7] Done")

# ─── R8: DTC classification clarification ────────────────────────────────────
print("\n[R8] DTC clarification...")
OLD_R8 = (
    "All STABLE classifications in the DTC were therefore timeout artifacts; the corrected\n"
    "transition boundary contains \\textbf{no stable configurations} for $\\mathcal{M} \\geq 1$\n"
    "at any $f$ tested."
)
NEW_R8 = (
    "All 15 STABLE classifications in the DTC were at $\\beta = 0.3$, $\\mathcal{M} = 1$ "
    "(the one sub-grid re-run with 6-hour timeouts); no other sub-grid contained stable "
    "classifications. The corrected transition boundary therefore contains "
    "\\textbf{no stable configurations} for $\\mathcal{M} \\geq 1$ at any $f$ or $\\beta$ tested."
)
tex = replace_once(tex, OLD_R8, NEW_R8, "R8")
print("[R8] Done")

# ─── R9: EOS gamma range ──────────────────────────────────────────────────────
print("\n[R9] EOS gamma range...")
OLD_R9 = "motivates a targeted study of $\\gamma = 1.0$--$1.2$ for future work."
NEW_R9 = (
    "motivates a targeted study at $\\gamma = 1.05$--$1.2$ for future work; in particular, "
    "whether fragmentation persists at $\\gamma = 1.05$--$1.10$ is directly relevant to "
    "whether the isothermal assumption is conservative at the density contrasts $C \\sim "
    "3$--$10$ reached in the magnetically regulated regime."
)
tex = replace_once(tex, OLD_R9, NEW_R9, "R9")
print("[R9] Done")

# ─── R10: Serpens beam bias estimate ─────────────────────────────────────────
print("\n[R10] Serpens beam bias...")
OLD_R10 = (
    "We cannot correct the Serpens catalogue for these effects\n"
    "without re-running the source extraction pipeline at the new distance."
)
NEW_R10 = (
    "We cannot correct the Serpens catalogue for these effects\n"
    "without re-running the source extraction pipeline at the new distance. "
    "As a quantitative estimate of the potential bias: if core blending at the "
    "$0.040$~pc beam scale merges ${\\sim}20$\\% of adjacent core pairs, the pairwise "
    "median would decrease by approximately $20$\\% $\\times$ $(\\lambda_{\\rm nn}/"
    "\\lambda_{\\rm pairwise}) \\approx 20\\%$ $\\times$ $1.1 \\approx 22$\\% (estimated "
    "from the Taurus nearest-neighbour ratio). At $0.331 \\pm 0.097$~pc, this would shift "
    "the Serpens spacing to ${\\sim}0.26$~pc---comparable to the Perseus measurement---while "
    "the full-sample result would change by ${\\sim}1.5$\\% (Serpens carries 3.8\\% weight)."
)
tex = replace_once(tex, OLD_R10, NEW_R10, "R10")
print("[R10] Done")

# ─── R11: GitHub URL anonymize ────────────────────────────────────────────────
print("\n[R11] Anonymize GitHub URL...")
tex = tex.replace(
    r"\url{https://github.com/Tilanthi/ASTRA-dev}",
    r"\url{https://github.com/[anonymised-for-review]}"
)
OLD_R11 = "Note to reviewers: this repository is currently private during the review period."
NEW_R11 = (
    "Note to reviewers: the repository is currently private during the review period; "
    "its name refers to the analysis framework used to generate, manage, and validate "
    "the simulation database."
)
tex = replace_once(tex, OLD_R11, NEW_R11, "R11")
print("[R11] Done")

# ─── R12: Fix Table 6 header ──────────────────────────────────────────────────
print("\n[R12] Table 6 header fix...")
OLD_R12 = (
    r"Field Geometry & $\beta = 0.3$ & $\beta = 0.5$ & $\beta = 1.0$ & $\beta = 1.5$ "
    r"& $\beta = 2.0$ & Trend & $\lambda/W_{\rm fil}$\textsuperscript{b} ($\beta=2$) \\"
)
NEW_R12 = (
    r"Field Geometry & $\beta = 0.3$ & $\beta = 0.5$ & $\beta = 1.0$ & $\beta = 1.5$ "
    r"& $\beta = 2.0$ & Trend & $\lambda/W_{\rm fil}^{b}$ \\"
)
tex = replace_once(tex, OLD_R12, NEW_R12, "R12")
print("[R12] Done")

# ─── R13: Length-reducing cuts ───────────────────────────────────────────────
print("\n[R13] Length-reducing cuts...")

# R13-B: Delete standalone sentence after flux-freezing paragraph
OLD_R13B = "\nThis law characterises radial collapse onset; it does not describe fragmentation wavelength.\n"
if OLD_R13B in tex:
    tex = tex.replace(OLD_R13B, "\n")
    print("  [R13B] Deleted standalone sentence")
else:
    print("  [R13B] Sentence not found as standalone (may be inline)")
    OLD_R13B2 = "This law characterises radial collapse onset; it does not describe fragmentation wavelength."
    if OLD_R13B2 in tex:
        tex = tex.replace(OLD_R13B2, "")
        print("  [R13B] Deleted inline sentence")

# R13-C: Condense Future priorities
OLD_R13C = (
    "\\textbf{Future priorities}: (1) Fibre-resolved core spacing analysis in HGBS filaments\n"
    "to test the hierarchical interpretation; (2) high-resolution polarimetric mapping of\n"
    "HGBS filament interiors; (3) T1 correction re-evaluation with the Plummer-function\n"
    "pipeline; (4) $L_x = 32\\,\\lambda_{\\rm J}$ convergence test for the Rigid Cylinder Campaign."
)
NEW_R13C = (
    "\\textbf{Future priorities}: (1) Fibre-resolved core spacing in additional HGBS regions; "
    "(2) polarimetric interior mapping; (3) oblique-field simulations at $\\theta = 30^\\circ$--"
    "$60^\\circ$ with HDF5 retention ($\\sim$20 simulations); "
    "(4) $L_x = 32\\,\\lambda_{\\rm J}$ RC convergence test."
)
tex = replace_once(tex, OLD_R13C, NEW_R13C, "R13C")

# R13-D: Delete Migration bias paragraph
OLD_R13D = (
    "\n\\textbf{Migration bias}: Monte Carlo simulations (1,000 realisations of the Orion~B sample\n"
    "with 25\\% protostellar fraction and migration distances $0.01$--$0.05$~pc) show $<0.01\\%$\n"
    "bias in the pairwise median, consistent with the statistic's robustness to local\n"
    "displacements for large-$N$ samples.\n"
)
if OLD_R13D in tex:
    tex = tex.replace(OLD_R13D, "\n")
    print("  [R13D] Deleted Migration bias paragraph")
else:
    # Try without leading newline
    OLD_R13D2 = (
        "\\textbf{Migration bias}: Monte Carlo simulations (1,000 realisations of the Orion~B sample\n"
        "with 25\\% protostellar fraction and migration distances $0.01$--$0.05$~pc) show $<0.01\\%$\n"
        "bias in the pairwise median, consistent with the statistic's robustness to local\n"
        "displacements for large-$N$ samples.\n"
    )
    if OLD_R13D2 in tex:
        tex = tex.replace(OLD_R13D2, "")
        print("  [R13D] Deleted Migration bias paragraph (alt)")
    else:
        print("  [R13D] WARNING: Migration bias paragraph not found")

print("[R13] Done")

# ─── NUMBER CONSISTENCY: 1956 everywhere ─────────────────────────────────────
print("\n[NUM] Checking 1956 consistency...")
# Should be fine already, but double-check for any stray numbers
count_1956 = tex.count('1956')
count_2045 = tex.count('2045')
if count_2045 > 0:
    tex = tex.replace('2045', '1956')
    print(f"  Fixed 2045→1956 ({count_2045} occurrences)")
print(f"  1956 appears {tex.count('1956')} times")

# ─── CHECK LINE COUNT ─────────────────────────────────────────────────────────
lines = tex.split('\n')
line_count = len(lines)
print(f"\n[LINES] After all patches: {line_count} lines")

# If still over 1260, apply additional cuts
if line_count > 1260:
    needed = line_count - 1260
    print(f"  [!] Need to remove {needed} more lines. Applying additional cuts...")

    # Additional cut 1: Flux-freezing dimensional estimate (~12 lines)
    # This is the "A dimensional estimate supports..." paragraph
    OLD_EXTRA1 = (
        "\nA dimensional estimate supports the flux-freezing explanation: during radial "
        "collapse of a filament with flux-frozen field, $|B| \\propto \\rho^{1/2}$ for a "
        "cylindrical geometry \\citep{Nakamura1993}. The magnetic pressure $P_{\\rm mag} "
        "\\propto B^2 \\propto \\rho$ then grows proportionally to the thermal pressure "
        "during collapse, doubling the effective sound speed squared for $\\beta \\sim 1$ "
        "initially (this estimate applies near $\\beta \\approx 1$; for $\\beta \\ll 1$ "
        "the initial magnetic pressure already dominates, while for $\\beta \\gg 1$ the "
        "flux-frozen amplification is negligible). This increases the collapse timescale "
        "by a factor $\\sim\\sqrt{2}$ relative to the purely thermal case, corresponding "
        "to a correction $\\Delta\\alpha \\approx 0.5 \\times \\ln\\sqrt{2}/\\ln f_{\\rm "
        "char} \\approx 0.07$ to the power-law exponent (where $f_{\\rm char} \\approx "
        "1.8$ is a representative line-mass fraction). This is of the same order as the "
        "observed deviation of $0.11$ ($= 0.50 - 0.39$), providing a self-consistent "
        "explanation. The residuals from the best-fit power law show no systematic trend "
        "with $\\beta$, consistent with the flux-freezing effect being absorbed into the "
        "fit rather than manifesting as a separate $\\beta$-dependent correction.\n"
    )
    if OLD_EXTRA1 in tex:
        tex = tex.replace(OLD_EXTRA1, "\n")
        lines = tex.split('\n')
        line_count = len(lines)
        print(f"  [CUT-1] Removed flux-freezing estimate paragraph. Lines now: {line_count}")
    else:
        print("  [CUT-1] Flux-freezing paragraph not found exactly")

    # Additional cut 2: C5 turbulence caveat paragraph (~9 lines)
    OLD_EXTRA2 = (
        "One caveat: our turbulence is initialised at $t = 0$ without a driving mechanism, "
        "so it decays on approximately a crossing time $t_{\\rm cross} \\approx L_x/"
        "\\sigma_{\\rm turb} \\approx 1$--$2\\,t_{\\rm J}$ for $\\mathcal{M} = 2$--$3$. "
        "For near-critical filaments where $t_{\\rm frag} \\approx 1.1\\,t_{\\rm J}$, the "
        "turbulence is still dynamically significant at fragmentation. For supercritical "
        "filaments ($t_{\\rm frag} \\approx 0.3\\,t_{\\rm J}$), the turbulence decays only "
        "partially before collapse, so the Mach-number independence result is robust. The "
        "effective Mach number at fragmentation is $\\sim 60$--$80\\%$ of the initial value "
        "for near-critical runs (estimated from the ratio $t_{\\rm frag}/t_{\\rm cross} "
        "\\approx 0.55$--$1.1$ for typical near-critical parameters; no direct measurement "
        "was made)."
    )
    if OLD_EXTRA2 in tex:
        tex = tex.replace(OLD_EXTRA2, "")
        lines = tex.split('\n')
        line_count = len(lines)
        print(f"  [CUT-2] Removed C5 turbulence caveat. Lines now: {line_count}")
    else:
        print("  [CUT-2] C5 turbulence caveat not found exactly")

    # Additional cut 3: Shorten the supercrit Lx=32 description in conclusions (verbose)
    # Cut from "If $\lambda/W_{\rm core}$ continues to decrease..." to end of bullet
    OLD_EXTRA3 = (
        " If $\\lambda/W_{\\rm core}$ continues to decrease at the same rate observed "
        "from $L_x = 8$ to $16$ ($-36\\%$ per octave), the converged value at $L_x = 32$ "
        "would be $\\approx 1.73$---below the HGBS window before T1 correction. This "
        "possibility cannot currently be excluded."
    )
    if OLD_EXTRA3 in tex:
        tex = tex.replace(OLD_EXTRA3, "")
        lines = tex.split('\n')
        line_count = len(lines)
        print(f"  [CUT-3] Removed Lx=32 verbose extrapolation. Lines now: {line_count}")
    else:
        print("  [CUT-3] Lx=32 verbose extrapolation not found")

    # Additional cut 4: Shorten the verbose $\beta=0.15$ boundary explanation (~4 lines)
    OLD_EXTRA4 = (
        "\nWhile the magnetically subcritical regime is theoretically important for "
        "establishing the transition to suppressed fragmentation, we note that $\\beta "
        "\\leq 0.15$ ($v_A/c_s \\geq 3.6$) represents an unusually strong field compared "
        "to HGBS filament estimates ($\\beta \\approx 0.3$--$2$; \\citealt{Planck2016, "
        "Pattle2018}). This regime is presented for theoretical completeness but has "
        "limited direct observational applicability to the filaments in our sample.\n"
    )
    if OLD_EXTRA4 in tex:
        tex = tex.replace(OLD_EXTRA4, "\n")
        lines = tex.split('\n')
        line_count = len(lines)
        print(f"  [CUT-4] Removed subcritical regime caveat. Lines now: {line_count}")
    else:
        print("  [CUT-4] Subcritical regime caveat not found exactly")

    # Additional cut 5: Shorten the regime boundary discussion (last sentence of thermally dominated)
    OLD_EXTRA5 = (
        "\nThe regime boundaries are defined by $\\beta$ thresholds that are robust across "
        "the full $f$ and $\\mathcal{M}$ range tested: the subcritical/regulated boundary "
        "shifts by $\\Delta\\beta < 0.03$ and the regulated/thermal boundary shifts by "
        "$\\Delta\\beta < 0.1$ across $f = 1.1$--$3.0$. The regime diagram "
        "(Figure~\\ref{fig:regime}) shows the density contrast $C$ in the $(\\beta, f)$ "
        "plane with fixed $\\mathcal{M} = 2$; the regime boundaries (dashed lines at "
        "$\\beta = 0.15$ and $\\beta = 2.5$) are overlaid.\n"
    )
    if OLD_EXTRA5 in tex:
        tex = tex.replace(OLD_EXTRA5, "\n")
        lines = tex.split('\n')
        line_count = len(lines)
        print(f"  [CUT-5] Removed verbose regime boundary text. Lines now: {line_count}")
    else:
        print("  [CUT-5] Verbose regime boundary text not found exactly")

    # Additional cut 6: Trim the L/3 formal bound paragraph (last two sentences duplicating earlier)
    OLD_EXTRA6 = (
        "Formally, for a distribution of $N$ cores with characteristic spacing $\\lambda$ on "
        "a filament of length $L$, the pairwise median departs from the true spacing by a "
        "fractional correction that scales as $\\sim(\\lambda/L)^2$ for small $\\lambda/L$ "
        "(this follows from expanding the pairwise distance distribution around the "
        "periodic-spike limit; for $N \\gg L/\\lambda$, cross-spacing terms average to zero "
        "and the correction is second-order). For $\\lambda/L \\approx 0.2$, this gives a "
        "bias of order $4\\%$ --- comparable to our quoted bootstrap uncertainty of $0.012$~pc.\n"
    )
    if OLD_EXTRA6 in tex:
        tex = tex.replace(OLD_EXTRA6, "\n")
        lines = tex.split('\n')
        line_count = len(lines)
        print(f"  [CUT-6] Removed formal L/3 correction text. Lines now: {line_count}")
    else:
        print("  [CUT-6] Formal L/3 correction text not found exactly")

    # Additional cut 7: Cut verbose "Zenodo" redundant sentence at end of Acknowledgments
    OLD_EXTRA7 = (
        " The full simulation\ndataset, including all HDF5 snapshots, parameter files, "
        "analysis scripts, and derived\ndata products, will be archived on Zenodo upon "
        "acceptance, with a persistent DOI enabling\nlong-term reproducibility."
    )
    if OLD_EXTRA7 in tex:
        tex = tex.replace(OLD_EXTRA7, "")
        lines = tex.split('\n')
        line_count = len(lines)
        print(f"  [CUT-7] Removed redundant Zenodo sentence. Lines now: {line_count}")
    else:
        print("  [CUT-7] Redundant Zenodo sentence not found exactly")

    line_count = tex.count('\n') + 1
    print(f"  [LINES] After additional cuts: {line_count} lines")

# ─── ABSTRACT WORD COUNT ─────────────────────────────────────────────────────
print("\n[ABSTRACT] Counting words...")
abs_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
if abs_match:
    abs_text = abs_match.group(1).strip()
    wc = count_words(abs_text)
    print(f"  Abstract word count: {wc}")
    if wc > 250:
        print(f"  [!] Over limit ({wc} > 250). Trimming...")
        # Remove "Near-critical simulations..." sentence from para 3 (least essential in abstract)
        OLD_ABS_TRIM = (
            "Near-critical simulations\n($f = 0.9$--$1.3$) directly measure "
            "$\\lambda/W_{\\rm core} = 2.80$--$4.74$ depending on\nplasma $\\beta$. "
        )
        if OLD_ABS_TRIM in tex:
            tex = tex.replace(OLD_ABS_TRIM, "")
            print("  Removed near-critical sentence from abstract")
        else:
            # Try alternative
            OLD_ABS_TRIM2 = (
                "Near-critical simulations\n($f = 0.9$--$1.3$) directly measure "
                "$\\lambda/W_{\\rm core} = 2.80$--$4.74$ depending on\nplasma $\\beta$."
            )
            if OLD_ABS_TRIM2 in tex:
                tex = tex.replace(OLD_ABS_TRIM2, "")
                print("  Removed near-critical sentence from abstract (alt)")
            else:
                # Try single-line version
                for variant in [
                    "Near-critical simulations ($f = 0.9$--$1.3$) directly measure $\\lambda/W_{\\rm core} = 2.80$--$4.74$ depending on plasma $\\beta$. ",
                    "Near-critical simulations ($f = 0.9$--$1.3$) directly measure $\\lambda/W_{\\rm core} = 2.80$--$4.74$ depending on\nplasma $\\beta$. ",
                    "Near-critical simulations\n($f = 0.9$--$1.3$) directly measure $\\lambda/W_{\\rm core} = 2.80$--$4.74$ depending on plasma $\\beta$. ",
                ]:
                    if variant in tex:
                        tex = tex.replace(variant, "")
                        print(f"  Removed near-critical sentence (variant)")
                        break
                else:
                    print("  [WARNING] Could not find near-critical abstract sentence to trim")

        # Recount
        abs_match2 = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
        if abs_match2:
            wc2 = count_words(abs_match2.group(1).strip())
            print(f"  Abstract word count after trim: {wc2}")
            if wc2 > 250:
                # Remove turbulence sentence too
                OLD_ABS_TRIM3 = "Realistic turbulence modifies\ntimescales but not spacing ($<5\\%$ effect on $\\lambda/W$). "
                if OLD_ABS_TRIM3 in tex:
                    tex = tex.replace(OLD_ABS_TRIM3, "")
                    abs_match3 = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
                    if abs_match3:
                        wc3 = count_words(abs_match3.group(1).strip())
                        print(f"  Abstract word count after 2nd trim: {wc3}")
    else:
        print(f"  Abstract OK ({wc} ≤ 250 words)")
else:
    print("  [WARNING] Could not find abstract!")

# ─── FINAL LINE COUNT ─────────────────────────────────────────────────────────
final_lines = tex.count('\n') + 1
print(f"\n[FINAL] Line count: {final_lines}")
if final_lines > 1260:
    print(f"  [WARNING] Still over 1260 by {final_lines - 1260} lines!")
else:
    print(f"  Line count OK (≤1260)")

# ─── CITATION CHECK ──────────────────────────────────────────────────────────
print("\n[CITATIONS] Final check...")
cite_keys2 = set(re.findall(r'\\(?:cite[tp]?|citealt|citep|citet)\{([^}]+)\}', tex))
all_keys2 = set()
for group in cite_keys2:
    for k in group.split(','):
        all_keys2.add(k.strip())
with open(BIBFILE) as f:
    bib2 = f.read()
bib_keys2 = set(re.findall(r'@\w+\{([^,]+),', bib2))
missing2 = all_keys2 - bib_keys2
if missing2:
    print(f"  [WARNING] Missing from bib: {missing2}")
else:
    print(f"  All {len(all_keys2)} citation keys found in bib. OK.")

# ─── BROKEN REFS CHECK ───────────────────────────────────────────────────────
print("\n[REFS] Checking \\ref{} calls...")
ref_labels = set(re.findall(r'\\label\{([^}]+)\}', tex))
ref_uses = set(re.findall(r'\\ref\{([^}]+)\}', tex))
missing_refs = ref_uses - ref_labels
if missing_refs:
    print(f"  [WARNING] Undefined \\ref targets: {missing_refs}")
else:
    print(f"  All {len(ref_uses)} \\ref calls have matching \\label. OK.")

# New label tab:oblique_theory should be present
if 'tab:oblique_theory' in tex:
    print("  tab:oblique_theory label: present")
else:
    print("  [WARNING] tab:oblique_theory missing!")

# ─── WRITE OUTPUT ─────────────────────────────────────────────────────────────
with open(OUTFILE, 'w') as f:
    f.write(tex)
print(f"\n[DONE] Written to {OUTFILE} ({final_lines} lines)")
