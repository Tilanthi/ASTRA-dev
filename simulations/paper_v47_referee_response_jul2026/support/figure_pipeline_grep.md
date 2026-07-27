# Figure-pipeline literal-\n audit (P1 / C8 follow-up)

Referee 1-P1 and the earlier C8 recommendation: grep the whole figure-generation codebase for
literal escape sequences in title/label strings (as opposed to real Python newlines).

Known remaining instances in v47:
1. **Figure 7 (EOS)** — a baked-in matplotlib `suptitle` reading "Figure 6. EOS sensitivity: …" was
   embedded in the image (duplicate figure number, wrong font). FIXED: regenerated without any
   suptitle → `figures/fig7_eos_nocaption.png`. (Root cause: ASTRA-PA's v42 regeneration script added
   `fig.suptitle("Figure 6. …")`; removed.)
2. **Figure 6 (DTC β,f grid)** legend still contains a literal `\n`: "FRAG (2/2) [incl.\ncorrected
   re-runs]". Regenerate with the legend label as "FRAG (2/2), incl. corrected re-runs" (single line)
   or a real newline.

Recommended sweep command on the plotting scripts:
  grep -rnE '\\\\n' <figure_scripts_dir>        # doubled backslash-n in strings
  grep -rn 'suptitle' <figure_scripts_dir>      # stray baked-in captions
Regenerate every multi-panel figure and proof each against its typeset caption before resubmission.
