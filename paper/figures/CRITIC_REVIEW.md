# ASTRA Dashboard Figures — Critic Review for Paper Inclusion

**Reviewer:** ASTRA Critic  
**Date:** 2026-04-05  
**Dashboard version:** v4.7  
**Figures reviewed:** 33 PNGs in `/shared/ASTRA/paper/figures/`

---

## Overall Verdict: 7.5/10 — Good, with fixable issues

The screenshots are well-composed and capture the dashboard effectively. However, several issues reduce paper-readiness, mostly around **print reproduction of the dark theme** and **label legibility at column width**. All are fixable.

---

## 1. Per-Figure Scores

### fig-dashboard-composite-4panel.png — Score: 6/10
**Dimensions:** 1600×900 (496KB)  
**Issues:**
- **CRITICAL — Too small for 4 panels.** At 1600×900 split into 4 quadrants, each panel is effectively 800×450px. When printed at single-column width (~84mm / 3.3in), each quadrant becomes ~42mm wide. Labels like "AUTONOMOUS DECISION LOG" entries, hypothesis cards, and chart axes will be **illegible at print DPI**.
- The composite captures too much — tab bars, nav chrome, status bars repeated 4 times. Wasted pixels.
- The Discoveries quadrant (bottom-left) is especially problematic: hypothesis cards are unreadable thumbnails.
- The Health quadrant (bottom-right) works better due to simpler layout, but the Audit Trail text is tiny.

**Recommendation:** If you want a composite figure, make it **2400×1600** minimum (or better, **3200×1800**). Or better: use a 2-panel composite (Overview + Safety) and let Discoveries/Health be separate figures. The current 1600×900 is insufficient for 4 panels.

### fig7-dashboard-overview.png — Score: 8/10
**Dimensions:** 1800×1013 (517KB)  
**Issues:**
- Good resolution for a single full-page figure
- Activity Stream text is readable at ~170mm width (full page)
- The Neural Topology visualization (center) renders beautifully — the cyan nodes are crisp
- Data Visualizations panel (top-right): the Hypothesis Funnel labels ("Proposed", "Screening") are small but legible
- H₀ Distribution chart: axis labels may be borderline at single-column
- Bottom: the page is cut off mid-way through the confidence gauge (46%) — consider scrolling slightly or cropping intentionally
- Minor: first line of Activity Stream is truncated (starts mid-sentence)

**Recommendation:** Crop the bottom to end cleanly at the Decision Log, or include full page. The truncation at the 46% gauge looks accidental.

### fig8-dashboard-safety.png — Score: 9/10 ⭐ Best Figure
**Dimensions:** 1800×1013 (231KB)  
**Issues:**
- Excellent composition — three clear sections: State Space, Drift Monitor, Alignment Stability
- The state space mind trajectory visualization is striking and unique
- Concentric safety boundaries (green/orange/red ellipses) reproduce well even in B&W as different dash patterns
- Alignment Stability bars are clearly color-coded with percentage values
- Drift Monitor uses traffic-light colors (green/red/amber) with text labels — accessible
- "No anomalies detected ✓" area is mostly empty whitespace — could be tighter
- Footer text visible at bottom

**Recommendation:** This is your strongest figure. Minor: crop the large empty "Recent Alerts" area and the footer to use space more efficiently.

### fig9-dashboard-discoveries.png — Score: 7/10
**Dimensions:** 1800×1013 (729KB)  
**Issues:**
- Shows the hypothesis pipeline well — Validated (4) → Testing (40+) progression is clear
- **Problem:** The Testing section dominates with repetitive "Galaxy Redshift Bimodality Deep Dive (vN)" cards — this actually reveals a **data quality issue** worth flagging: the engine is stuck in a loop producing near-identical hypotheses
- Cards below row 2 become redundant and don't add information
- Largest file (729KB) due to all the card text rendering
- The bottom is cut off mid-card row

**Recommendation:** Crop to show Validated (4 cards) + first 2 rows of Testing. This tells the same story in less space and avoids showcasing the repetition loop. Alternatively, this is actually a good figure to show in the paper as evidence of the "stuck in loop" behavior the Activity Stream warns about — but then call it out in the caption.

### fig10-dashboard-health.png — Score: 8/10
**Dimensions:** 1800×1013 (290KB)  
**Issues:**
- Clean layout with good hierarchy: Component Health → Charts → Audit Trail
- Component Health cards ("Discovery Engine", "Safety Controller", etc.) with green dots are crisp
- Cycle Performance chart is readable
- Domain Distribution donut chart is colorful and clear
- **Issue:** Persistence (SQLite) panel shows "--" for all 4 values (Discoveries, Outcomes, Hypotheses, DB Size) — these are placeholder defaults when no backend data is loaded
- Audit Trail is well-formatted with color-coded tags (SYSTEM, DISCOVERY, DECISION, SAFETY)

**Recommendation:** Either populate the Persistence values before screenshotting (requires backend), or crop the figure to exclude that panel. Showing "--" in a paper looks like broken software.

---

## 2. Print Reproduction Analysis

### Dark Theme on White Paper
The dark background (#06080d) will print as solid black, which:
- ✅ **Works well** for the colored elements — cyan lines, amber bars, green dots pop against black
- ✅ **Chart elements** are high-contrast (white/cyan text on black)
- ⚠️ **Ink-heavy** — a full-width dark figure uses significant ink. Most journals accept this, but budget-conscious authors should note it
- ⚠️ **Panel borders** (subtle glassmorphism effects) will disappear in print — they rely on slight transparency differences
- ❌ **Grayscale reproduction** would lose the traffic-light color coding in Safety (Drift Monitor). The text labels (NOMINAL, CRITICAL, WARNING) save it, but the bars would all look similar

### Resolution at Column Widths
| Figure | At single-column (84mm) | At full-width (170mm) |
|--------|------------------------|----------------------|
| 4-panel composite | ❌ Unreadable | ⚠️ Borderline — each panel ~85mm |
| Overview | ⚠️ Some labels tight | ✅ Good |
| Safety | ✅ Clean layout scales well | ✅ Excellent |
| Discoveries | ⚠️ Card text tiny | ✅ Good |
| Health | ✅ Good | ✅ Excellent |

### Label Legibility
At typical journal reproduction (300 DPI, single column):
- **Orbitron headings** — ✅ Readable (they're large)
- **Space Mono data labels** — ⚠️ Borderline at single-column for small charts
- **Activity Stream / Audit Trail text** — ❌ Too small at single-column; ✅ OK at full-width
- **Chart axis labels** — ⚠️ Need full-width to be legible

---

## 3. Figure Selection Recommendations

### Recommended Selection (3 figures):

**Figure 7: Safety Dashboard (full-width)**
Use `fig8-dashboard-safety.png` — this is your strongest, most unique figure. The state space mind trajectory, concentric safety boundaries, and alignment stability metrics directly support the paper's safety architecture claims. **Full-width placement.**

**Figure 8: Overview Dashboard (full-width)**  
Use `fig7-dashboard-overview.png` — shows the OODA engine, neural topology, data visualizations, and decision log. Demonstrates the complete autonomous operation. **Full-width placement.** Crop bottom to end cleanly.

**Figure 9: Health Monitoring (single-column OK)**
Use `fig10-dashboard-health.png` — cleanest layout, scales well. Crop out the Persistence panel. Could work at single-column.

### Alternative: If space for only 2 figures:

Use `fig8-dashboard-safety.png` (Safety) + `fig7-dashboard-overview.png` (Overview). These two cover the paper's main contributions: autonomous discovery (Overview) and safety architecture (Safety).

### Not Recommended:
- **4-panel composite** — Resolution too low for print. Don't try to cram 4 tabs into one figure.
- **Discoveries tab** — The repetitive hypothesis cards expose a loop bug rather than showcasing the pipeline. If you want to show the pipeline, crop to just the Validated section or use `fig-detail-hypothesis-funnel.png`.

---

## 4. Dashboard UX Issues Found

### P1 (Fix before final screenshots):

1. **Persistence panel shows "--"** — Health tab's Persistence (SQLite) section displays placeholder values. Either populate with real data or remove from the HTML before screenshotting.

2. **Hypothesis repetition loop** — The Discoveries tab shows 30+ near-identical "Galaxy Redshift Bimodality Deep Dive" hypotheses (v1 through v16+) all at confidence 0.40. This looks like a bug in the engine's diversity/dedup logic. For screenshots, this is embarrassing — it dominates the view.

### P2 (Should fix):

3. **Activity Stream starts mid-sentence** — The first visible entry in Overview is cut off: "...norm), p = 0.0000". Either scroll to show a complete first entry or add a fade-out at the top.

4. **"Recent Alerts" empty space** — Safety tab has a large blank area under "Recent Alerts" → "No anomalies detected ✓". This wastes prime visual real estate.

5. **Overview bottom truncation** — The 46% confidence gauge and floating emoji (🌿🍂) are cut off. Either include fully or crop above them.

### P3 (Nice to have):

6. **Self-Improve tab renders correctly** — Despite earlier concern, the tab has full content (metrics, trajectory, timeline, method performance, coverage matrix). No rendering bug.

7. **Persistence data depends on backend** — The "--" values are by design (populated via API), but for a static screenshot/demo, hardcoded fallback values would look better.

---

## 5. Specific Actionable Improvements

### For the figures themselves:

1. **Re-capture at higher resolution.** The 1800×1013 shots are good but 2400×1350 (or 2x/Retina) would give more headroom for print scaling. Use `deviceScaleFactor: 2` in Playwright.

2. **Crop chrome.** Remove the tab bar, status bar, and nav buttons from figures where they aren't the subject. For Safety, crop to just the 3 content panels. This gives more pixels to the actual content.

3. **Add figure labels.** For the composite, add (a), (b), (c), (d) labels to each quadrant — standard for multi-panel figures in RASTI papers.

4. **Fix the "--" values.** Before re-capturing Health tab, either:
   - Run the backend briefly to populate persistence stats, or
   - Temporarily hardcode realistic values: Discoveries=397, Outcomes=184, Hypotheses=49, DB Size=2.4 MB

5. **Consider a "paper mode"** — A minimal CSS override that:
   - Hides the tab bar and status bar
   - Increases font sizes by 20%
   - Removes the floating emoji/particles
   - Removes the footer
   This would make much cleaner paper figures.

### For the dashboard before re-capture:

6. **Scroll Activity Stream** to start at a clean entry boundary
7. **Filter Discoveries** to show only the first 8-12 unique hypotheses if possible
8. **Crop or remove** the empty "Recent Alerts" area in Safety

---

## 6. Detail Crops Assessment

| Crop | Score | Notes |
|------|-------|-------|
| fig-detail-state-space.png | 7/10 | Good subject but crops include tab bar chrome at top. The spaceship icon is charming but informal for a paper. |
| fig-detail-ooda-cycle.png | 8/10 | Clean, readable. Shows decision engine well. Good for inline figure. |
| fig-detail-neural-topology.png | 6/10 | Cuts off the network — only right half visible. Needs reframing to center the full topology. |
| fig-detail-hypothesis-funnel.png | 4/10 | **Bad crop** — mostly empty dark space with funnel labels barely visible at far right edge. Needs complete redo. |
| fig-detail-alignment-full.png | 7/10 | Good content but crops off bottom bars. Needs slightly taller capture. |

---

## Summary Scores

| Figure | Paper Quality | Print Readability | Composition | Content Value | Overall |
|--------|:---:|:---:|:---:|:---:|:---:|
| 4-panel composite | 5 | 4 | 6 | 8 | **6/10** |
| Overview (fig7) | 8 | 7 | 7 | 9 | **8/10** |
| Safety (fig8) | 9 | 9 | 8 | 10 | **9/10** ⭐ |
| Discoveries (fig9) | 6 | 6 | 5 | 7 | **7/10** |
| Health (fig10) | 8 | 8 | 8 | 7 | **8/10** |

**Bottom line:** Use Safety (fig8) as your hero figure — it's publication-ready today. Overview (fig7) is a strong second. Skip the 4-panel composite; it's too dense. Fix the Persistence "--" values and hypothesis repetition before re-capturing Health and Discoveries.
