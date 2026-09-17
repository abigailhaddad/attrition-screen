# Is ICE's rookie-attrition problem happening anywhere else? (OPM EHRI)

`icehires` found ICE's 2025 hiring surge came with unusually fast new-hire turnover. This checks
FBI, then every other federal agency, for the same pattern — using the same OPM/EHRI records.

## Deliverables
- **`attrition_screen.ipynb`** — full analysis, charts + tables inline.
- **`memo.md`** — one-page summary.

## Reproduce
```bash
pip install duckdb pandas matplotlib nbformat nbconvert jupyter huggingface_hub
python src/extract.py
jupyter nbconvert --to notebook --execute --inplace attrition_screen.ipynb
```

## Layout
- `src/extract.py` — pulls FBI Special Agents (DJ02/1811), a government-wide under-1-year-tenure
  screen, and an IRS Contact Representative drill-down back to 2019.
- `src/lib.py` — shared paths, the anchor windows, and `implied_hire_cohort()` (see Method).
- `data/` — git-ignored; `python src/extract.py` rebuilds it.

## Method
A naive screen — separations of under-1-year hires ÷ their headcount — breaks twice:

- **Seasonal noise.** Forest Service, Census, and other schedule-driven hirers post >100%
  "attrition" that's just normal seasonal cycling, burying ICE's real signal. Fix: permanent
  appointments only.
- **Stock collapse.** Even filtered, an agency that stops hiring shows a huge rate for no real
  reason — the denominator just empties out. This is why NRCS, Rural Development, and the
  Comptroller of the Currency top a naive permanent-only ranking. Fix: `implied_hire_cohort()`
  matches each departure to its actual hire month, so a frozen agency gets correctly excluded
  instead of spiking.
- **Agency-level rates still dilute.** ICE's all-series rate (17.5%) sits well below its
  enforcement-officer-specific rate (`icehires`, ~28-33%) because non-enforcement hiring is
  stickier. Treat any number here as a screening signal, not a final claim, until it gets the same
  drill-down IRS gets below.

## Findings

**FBI: no signal.** Under-1-year separations held flat (0-5/month) through 2025-26. The September
spike (332 people) was 75% Deferred Resignation Program (DRP) exits — senior agents averaging 22
years of service, not new hires.

**Only ICE and IRS combine real hiring volume with a worsened exit rate**, post-Sep-2025 vs. the
prior year: ICE 4.3%→17.5%, IRS 21.0%→28.9%. TSA looks alarming (~18%) but hasn't moved; Defense
Commissary Agency's rate actually improved.

**IRS's number is a Contact Representative story** — taxpayer-service call-center staff, job
series 0962, permanent appointments only (temp/seasonal excluded throughout), 92% of all IRS
hiring since September once every other role froze.

**The headline:** Contact Reps are leaving faster, in a shrinking workforce, and IRS isn't
replacing them — three things true at once, none a record alone:

- Quit-within-2-months rate: 6.4% (2023-24) → 8.5% (2024-25) → 14.2% (2025-26), matching the
  2021-22 pandemic-era peak.
- Headcount peaked at 25,221 (Dec 2024), down 28% to 18,145 (Jul 2026).
- Net headcount change negative in 10 of the last 11 months.

![IRS Contact Representatives (permanent staff): leaving faster, in a shrinking workforce, and not being replaced — quit-within-2-months rate by hiring window (top); total permanent headcount over time (middle); net monthly headcount change (bottom).](figures/irs_0962_summary.png)

Footnote: under-1-year employees were 32% of the 0962 workforce at the 2022 peak; today, 3%.

![IRS Contact Representative (0962, permanent staff): hires and departures (top) and departures as a share of hires (bottom), by hiring window, 2019-2026](figures/irs_0962_story.png)
