# HGBS filament core spacing — two-paper split (August 2026)

The material previously carried as a single 29-page manuscript is split into a
self-contained observational paper and a self-contained numerical paper.

| | Title | Pages | Figs | Tables |
|---|---|---|---|---|
| **Paper I** | Core spacing and filament occupancy in *Herschel* Gould Belt filaments | 17 | 8 | 13 |
| **Paper II** | Fragmentation of evolving filaments: MHD simulations and the equilibrium-cylinder wavelength | 12 | 4 | 6 |

**Build**: `pdflatex paperN; bibtex paperN; pdflatex paperN; pdflatex paperN`
(requires `mnras.cls`, `mnras.bst`, `references_complete.bib`, `figures/`).

Each paper compiles with zero undefined control sequences and zero undefined
references; both abstracts are within the MNRAS 250-word limit.

## Paper I — the observational question
Leads with the question ("how far apart are the cores, and is that consistent with
the equilibrium-cylinder calculation?"), introduces only three quantities in the
main text (`s_ACS`, `L/N`, `f_occ`), gives the answer in the Introduction, and
moves the systematics machinery, the conditional null, the convention decoder and
the literature comparison into appendices.

## Paper II — the numerical question
A narrow theoretical question: must an evolving filament select the wavelength of
its initial equilibrium? Answer: no — the equilibrium control recovers 22H, the
evolving filament shows no maximum in the converged band, and mode selection
tracks the instantaneous density as rho^-0.49+-0.05. States explicitly that it
does not explain the observations.

## Changes made during the split
Beyond the restructuring, the following substantive corrections were made:

1. **Two different quantities were sharing the symbol `s_ACS,med`.** The measured
   along-crest adjacent-core separations (0.177, 0.166, 0.297, 0.181 pc for
   Orion B, Aquila, Perseus, Taurus) are now used everywhere. A set of legacy
   reference constants (0.207, 0.210, 0.263, 0.124 pc), which had propagated into
   the widths table, the spacing figure, the convention decoder and the
   literature-comparison table, has been removed. `S_local` = 1.7-3.0
   (fixed-width) and the adopted region-Plummer reference value 1.4 are unchanged;
   the fixed-width decoder value moves 2.1 -> 1.8 and the FilFinder range
   0.4-0.8 -> 0.5-1.5.
2. Two figures regenerated from the corrected values
   (`figure1_spacing_comparison.pdf`, `fig_envelope.pdf`).
3. Literature agreement re-stated quantitatively (consistent to within about a
   third per cloud) rather than as "3 per cent".
4. Derived quantities swept for consistency: association-radius bound
   16 -> 17 per cent, median-to-mean rise 40-120 -> 30-120 per cent,
   local/global contrast under FilFinder 6-17 -> 9-17, fibre scaling
   r/N 0.07-0.35 -> 0.2-0.4 (adopted) / 0.1-0.6 (envelope), Aquila and Perseus
   occupancy fractions 0.24/0.11 -> 0.27/0.12.
5. Error budget split: observational terms stay in Paper I, numerical and
   unit-conversion terms move to Paper II (new Table 3).
6. Paper II: a stray `\end{document}` that was truncating three appendices removed;
   an internally duplicated paragraph removed; two damaged connectives repaired.
