# Is ICE's rookie-attrition problem happening anywhere else? (OPM EHRI)

`icehires` found that ICE's 2025 hiring surge came with unusually fast turnover among the
enforcement officers hired into it. This repo checks whether that's an ICE-only story: first
against FBI specifically (given 2025's leadership turmoil), then against every other federal
agency subelement, using the same OPM/EHRI records read directly with DuckDB.

## Deliverables
- **`attrition_screen.ipynb`** — the analysis, start to finish (charts + tables inline). About as
  much about the method as the answer — the naive version of this screen fails twice before it
  works, and both failures are shown, not just described.
- **`memo.md`** — one-page memo, every figure cross-referenced to a notebook section.

## Reproduce
```bash
pip install duckdb pandas matplotlib nbformat nbconvert jupyter huggingface_hub
python src/extract.py
jupyter nbconvert --to notebook --execute --inplace attrition_screen.ipynb
```

## Layout
- `src/extract.py` — pulls every slice the notebook uses: FBI Special Agents (DJ02/1811), a
  government-wide under-1-year-tenure screen (naive and permanent-appointments-only versions),
  raw (unbucketed) tenure-at-separation for the implied-hire-month correction, and an IRS/Contact
  Representative drill-down back to 2019.
- `src/lib.py` — shared paths, the anchor windows (post-Sep-2025 vs. the equal-length prior year),
  and `implied_hire_cohort()`, the function that makes the government-wide screen trustworthy (see
  Method).
- `data/` — git-ignored; `python src/extract.py` rebuilds everything.

## Method
The obvious way to screen for "are new hires washing out" — trailing-12-month separations of
under-1-year-tenure people, divided by trailing-12-month average headcount of that same group —
breaks twice before it's usable. Both breakages are load-bearing to the final numbers, not just
narrative color.

- **`length_of_service_years` has to be validated first.** It's a raw continuous field on every
  accession, separation, and employment record — not a pre-binned bracket. Checked against FBI new
  hires: 84.6% show exactly 0 years, 85.5% under a year. A further 8.0% show 5+ years of prior
  service — lateral entries carrying prior federal credit, not a data error.
- **Failure #1: an unfiltered screen is dominated by seasonal noise.** Forest Service, National
  Park Service, Census — workforces that hire and release people on a schedule every year — show
  >100% "annualized attrition" that's just normal seasonal cycling. ICE doesn't even crack the top
  of this ranking; it's buried under the noise. Fix: restrict to permanent appointments
  (`appointment_type LIKE '%PERMANENT%' AND NOT LIKE '%NONPERMANENT%'`).
- **Failure #2: a stock-based rate mechanically explodes when hiring collapses.** Even permanent
  appointments only, dividing by *current* under-1-year headcount means an agency that simply
  stopped hiring shows a huge "attrition rate" with nothing unusual happening — there's just almost
  no one left in the denominator. Several agencies (USDA's Natural Resources Conservation Service,
  Rural Development, the Comptroller of the Currency) rank near the top of a naive permanent-only
  screen for exactly this reason, not because people are quitting fast.
- **Fix #2: match departures to the hiring vintage that produced them.** For every separation
  record, back out an implied hire month (event month minus tenure-at-departure) and only count it
  against a window if that person was actually hired in it (`lib.implied_hire_cohort()`). An agency
  with collapsed hiring gets a correctly tiny, excluded denominator instead of a misleading spike.
- **Agency-level rates still dilute real signals.** ICE's all-job-series rate (17.5%) sits well
  below its enforcement-officer-specific rate (`icehires`, ~28-33%) because non-enforcement ICE
  hiring — attorneys, analysts, support staff — is far stickier. Every agency-level number in this
  repo is a screening signal, earning the same kind of series-level drill-down §4 does for IRS
  before being treated as a headline claim on its own.

## Headline findings
**FBI shows no rookie-attrition signal.** Under-1-year separations ran 0-5 a month straight
through 2025-26, no shift after September. That month's 332-person spike was 75% flagged as
Deferred Resignation Program (DRP) exits — the 2025 federal buyout offer — with average tenure at
departure 21.8 years, 78% with 20+ years in — a buyout-driven exodus of senior agents, not new
agents washing out.

**Across every other agency, exactly two combine real hiring volume with a genuinely worsened
cohort-exit rate, post-Sep-2025 vs. the equal-length prior year: ICE (4.3%→17.5%, +13 points) and
IRS (21.0%→28.9%, +8 points).** Nothing else clears both bars — sorting by the raw rate instead of
the *change* is misleading (TSA's ~18% looks alarming but is unchanged from its historical norm;
Defense Commissary Agency's rate actually improved).

**IRS's number is really a Contact Representative story.** IRS has frozen hiring almost everywhere
— Revenue Agents, Tax Examiners, clerical, IT all collapsed to near zero since September — except
Contact Representatives (taxpayer-service call-center staff, job series 0962), 92% of all IRS
hiring since then. Of 1,108 Contact Reps hired since September, **333 (30.1%) have already left,
88% a plain voluntary quit**.

**The headline: IRS Contact Representatives — the phone-line taxpayer-service reps who answer
IRS's main call center — are leaving faster, in a workforce that's been shrinking for years, and
IRS isn't replacing them.** None of those three is a record-breaker alone; what makes it worth
flagging is that all three are true at the same time, right now:

- **Leaving faster:** the share of new hires gone within 2 months has climbed for three straight
  years — 6.4% (2023-24) → 8.5% (2024-25) → 14.2% (2025-26) — back up to the 2021-22 pandemic-era
  peak (14.0%), not a new record but a real, sustained acceleration.
- **A shrinking workforce:** total headcount peaked at 25,221 in December 2024 and has fallen 28%
  (7,076 people) to 18,145 by July 2026.
- **Not being replaced:** net headcount change has been negative in 10 of the last 11 months —
  IRS is losing Contact Reps faster than it's hiring them, every month, right now.

![IRS Contact Representatives (0962): how fast they're leaving, by hiring window — not an all-time record, but a sharp recent climb (top); the size of the workforce over time, peaking Dec 2024 and down 28% since (middle); and whether IRS is replacing departures at all — net change in headcount, month over month, 10 of the last 11 months a net loss (bottom).](figures/irs_0962_summary.png)

One more angle on the same shrinkage: at the 2022 hiring peak, under-1-year employees were **32%**
of the whole 0962 workforce — nearly a third brand new. Today that share is **3%**, the lowest in
the series — a workforce that turned from mostly-fresh to almost entirely veteran well before this
window started.

![IRS Contact Representative (series 0962): hires and departures (top) and departures as a share of that window's hires (bottom), by hiring window, 2019-2026](figures/irs_0962_story.png)
