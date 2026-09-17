# Is ICE's rookie-attrition problem happening anywhere else?

**Analyst memo · data through Jul 2026 · every figure is reproduced in `attrition_screen.ipynb`**

**Bottom line.** No, mostly — with one real exception. FBI shows no rookie-attrition signal at all: its September 2025 separations spike was a buyout-driven exodus of agents averaging 22 years of service, not new agents washing out. A government-wide screen of every other agency subelement finds nothing else combining ICE's scale of hiring with ICE's scale of new-hire attrition. But the same screen surfaces a second, unrelated, comparably-sized story: **IRS Contact Representatives** — essentially the only job IRS is still hiring for — quit almost as fast as ICE's surge officers. That speed isn't an all-time record for this specific job, but it has more than doubled in the last two years, and on top of that IRS has stopped replacing them — a workforce that's been quietly hollowing out for years, not a sudden 2025 shift.

**Source.** OPM/EHRI records for hires, departures, and monthly headcount, read directly from the HuggingFace dataset `impactproject/opm-ehri-data`. Companion to the sibling `icehires` repo, which found ICE's pattern first.

---

### 1. The method: does `length_of_service_years` mean "just hired"? · *notebook §1*
Checked against FBI new hires: 84.6% show exactly 0 years of service, 85.5% under a year — the field works. Two failure modes had to be fixed before a government-wide screen was trustworthy: an unfiltered version is dominated by seasonal/term workforces (Forest Service, Census, IRS filing season) whose normal seasonal cycling looks like extreme "attrition"; and even filtered to permanent appointments, a stock-based rate (separations ÷ current under-1-year headcount) mechanically explodes for any agency that simply stopped hiring, regardless of whether people are actually quitting faster. The fix used throughout: an **implied-hire-month correction** — back out each departure's hire month from its tenure at separation, and only count it against a hiring window if that person was actually hired in it. This is the same cohort logic `icehires` uses for ICE's surge, generalized to run on any agency without knowing its hiring history in advance.

### 2. FBI: a real shock, but not a hiring problem · *notebook §2*
FBI headcount fell by 349 in the two months after September 2025. But under-1-year separations sat at 0-5 a month through the entire period — no shift at all. The September spike itself: 332 separations, 75% DRP-flagged, average tenure at departure 21.8 years, 78% with 20+ years in. A veteran buyout wave, not rookies washing out.

### 3. A government-wide screen, corrected · *notebook §3*
Every agency subelement, every job series, hires and departures counted within the same window (Sep 2025-Jul 2026 vs. the equal-length prior year), departures matched to hire vintage. Sorted by the level, TSA looks alarming (~18%) but hasn't moved from its historical norm; Defense Commissary Agency's rate actually improved. Sorted by the **change** instead — the only defensible way to read this — exactly two agencies combine real hiring volume with a genuinely worsened rate: **ICE (+13 points, 4.3%→17.5%)** and **IRS (+8 points, 21.0%→28.9%)**. Nothing else clears both bars.

### 4. IRS: what's actually happening · *notebook §4*
IRS has frozen hiring almost everywhere — Revenue Agents, Tax Examiners, clerical staff, IT all collapsed to near zero since September — **except Contact Representatives** (taxpayer-service call-center staff, job series 0962), which is 92% of all IRS hiring since then. Of the 1,108 Contact Reps hired since September, **333 (30.1%) have already left**, 88% of it a plain voluntary quit — not DRP, not a firing.

### 5. The headline: leaving faster, in a shrinking workforce, not being replaced · *notebook §4*
IRS Contact Representatives — the phone-line taxpayer-service reps who answer IRS's main call center — are leaving faster, in a workforce that's been shrinking for years, and IRS isn't replacing them. None of those three is a record-breaker alone; what makes it worth flagging is that all three are true at the same time, right now:

- **Leaving faster:** the share of new hires gone within 2 months has climbed for three straight years — **6.4% (2023-24) → 8.5% (2024-25) → 14.2% (2025-26)** — back up to the 2021-22 pandemic-era peak (14.0%), not a new record but a real, sustained acceleration.
- **A shrinking workforce:** total headcount peaked at **25,221 (Dec 2024)** and has fallen **28% (7,076 people) to 18,145 by Jul 2026**.
- **Not being replaced:** net headcount change has been negative in **10 of the last 11 months**.

![IRS Contact Representatives (0962): how fast they're leaving, by hiring window (top); the size of the workforce over time (middle); and whether IRS is replacing departures at all, net headcount change month over month (bottom).](figures/irs_0962_summary.png){width=6in}

One more angle on the same shrinkage: at the 2022 hiring peak, under-1-year employees were **32%** of the whole 0962 workforce — nearly a third brand new. Today that share is **3%**, the lowest in the series — mostly-fresh to almost entirely veteran, well before this window started.

![IRS Contact Representative (series 0962): hires and departures (top) vs. departures as a share of hires (bottom), by hiring window — 2025-26's bars are the smallest in the series, but the share lost still matches the 2021-22 peak.](figures/irs_0962_story.png){width=6in}

---

### What the data can't say (caveats) · *notebook §1, §4*
- **No person IDs.** The implied-hire-month correction is a tenure-at-departure inference, not confirmed individual tracking — the same limitation `icehires` states plainly for its own cohort number.
- **Agency-level rates dilute real signals.** ICE's all-series rate (17.5%) is well below its enforcement-officer-specific rate (`icehires`, ~28-33%) because non-enforcement ICE hiring (attorneys, analysts, support) is much stickier. Any agency-level number here is a screening signal, not a final claim — it earns a same-style drill-down (like §4's IRS section) before being quoted on its own.
- **30% for IRS Contact Reps is not a historical record, and neither is the speed of quitting.** The genuinely new thing is the multi-year collapse in how much of the workforce is even a recent hire, and the sustained net headcount losses — not the exit rate in isolation.

**Method checked (notebook §1):** the tenure field validated against known-good FBI hire data before being trusted elsewhere; the naive screen's seasonal-noise failure and the stock-based rate's hiring-collapse failure are both shown directly, not just described.

*Reproduce: `python src/extract.py` (pulls everything to `data/`), then run `attrition_screen.ipynb`. Shared paths, windows, and the cohort-correction logic are in `src/lib.py`.*
