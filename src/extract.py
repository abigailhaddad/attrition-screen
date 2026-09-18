"""Serverside-query impactproject/opm-ehri-data (HuggingFace) for every slice this repo's
notebook uses. Each OPM monthly file is incremental (mostly that month's actions, plus a
trickle of late-reported earlier ones), so an event-month series is built by summing
`count` across every file grouped by `personnel_action_effective_date_yyyymm` -- never by
which file reported it.

What gets pulled, and why:

- **fbi_***: FBI Special Agents only (agency DJ02, job series 1811 -- not the whole Bureau).
  Row-level enough (category, DRP flag, tenure, grade, age) for the notebook to check
  whether the September 2025 separations spike looks like a hiring problem.

- **screen_naive_***: every agency subelement, every job series, filtered to
  `length_of_service_years < 1`, EVERY appointment type. This is deliberately the "wrong"
  version -- the notebook uses it to show that seasonal/term workforces (Forest Service,
  Census, IRS filing season) make an unfiltered under-1-year screen useless.

- **screen_perm_***: the same screen, filtered to permanent appointments only
  (`appointment_type LIKE '%PERMANENT%' AND NOT LIKE '%NONPERMANENT%'`). `_accessions` adds
  new-hire counts (needed as a denominator); `_sep_rawlos` and `_sep_rawlos_prioryear` keep
  the *raw* (unbucketed) `length_of_service_years` value on separations -- required to back
  out each departure's implied hire month (see lib.implied_hire_cohort) rather than just
  bucketing by current tenure, which silently mixes hiring vintages.

- **irs_***: IRS-specific detail (series, grade, separation reason) once the government-wide
  screen flags it, mirroring the same drill-down `dhs_hiring_surge.ipynb` (in the sibling
  `icehires` repo) does for ICE.

- **irs_0962_*_hist**: IRS Contact Representatives (job series 0962) back to 2019 -- is the
  2025-26 cohort's exit rate actually unusual, or does this specific job always churn this
  fast?

- **irs_0962_separations_alltenure**: same population, no tenure filter at all -- needed to
  tell whether the *whole* workforce's departures (not just the recent-hire cohort) are
  voluntary quits or something else, like a DRP wave among longer-tenured staff.

- **irs_0962_accessions_los**: tenure-at-hire for 0962 new hires -- quantifies how much of a
  blind spot the implied-hire-month correction has for this specific population (small, ~1-5%;
  see notebook §1).
"""
import re
from pathlib import Path

import duckdb
from huggingface_hub import list_repo_files

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://huggingface.co/datasets/impactproject/opm-ehri-data/resolve/main"
HF_REPO = "impactproject/opm-ehri-data"

PERM = "appointment_type LIKE '%PERMANENT%' AND appointment_type NOT LIKE '%NONPERMANENT%'"
FBI_START = "201801"
SCREEN_START = "202101"
HIST_START = "201901"


def con():
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false;")
    c.execute("SET threads=4;")
    return c


def file_map(kind):
    files = list_repo_files(HF_REPO, repo_type="dataset")
    pat = re.compile(rf"^{kind}/{kind}_(\d{{6}})_v(\d+)\.parquet$")
    best = {}
    for f in files:
        m = pat.match(f)
        if m:
            ym, v = m.group(1), int(m.group(2))
            if ym not in best or v > best[ym][0]:
                best[ym] = (v, f)
    return {ym: fn for ym, (v, fn) in best.items()}


def urls(fm, kind, lo, hi=None):
    return [f"{BASE}/{fm[kind][ym]}" for ym in sorted(fm[kind]) if ym >= lo and (hi is None or ym <= hi)]


def pull(c, u, date_col, cols, where, out_name):
    select_cols = f"{date_col} AS ym, {cols}," if cols else f"{date_col} AS ym,"
    print(f"{out_name}: reading {len(u)} remote files ...", flush=True)
    c.execute(f"""
        COPY (
          SELECT {select_cols} SUM(TRY_CAST(count AS INT)) AS n
          FROM read_parquet({u!r}, union_by_name=true)
          WHERE {where}
          GROUP BY ALL
        ) TO '{ROOT / "data" / out_name}.parquet' (FORMAT parquet);
    """)
    n = c.execute(f"SELECT COUNT(*) FROM '{ROOT / 'data' / out_name}.parquet'").fetchone()[0]
    print(f"  {out_name}: {n:,} rows", flush=True)


def run():
    c = con()
    fm = {k: file_map(k) for k in ("accessions", "separations", "employment")}

    # ---- FBI Special Agents (DJ02, series 1811) ----
    FBI_FP = "agency_subelement_code = 'DJ02' AND occupational_series_code = '1811'"
    common_person_cols = "length_of_service_years, education_level_bracket, appointment_type, grade, tenure, age_bracket"
    pull(c, urls(fm, "accessions", FBI_START), "personnel_action_effective_date_yyyymm",
         f"accession_category, {common_person_cols}", FBI_FP, "fbi_accessions")
    pull(c, urls(fm, "separations", FBI_START), "personnel_action_effective_date_yyyymm",
         f"separation_category, drp_indicator, {common_person_cols}", FBI_FP, "fbi_separations")
    pull(c, urls(fm, "employment", FBI_START), "snapshot_yyyymm",
         common_person_cols, FBI_FP, "fbi_employment")

    # ---- Government-wide under-1-year screen: naive (all appointment types) ----
    UNDER1 = "TRY_CAST(length_of_service_years AS DOUBLE) < 1"
    pull(c, urls(fm, "employment", SCREEN_START), "snapshot_yyyymm",
         "agency, agency_subelement, agency_subelement_code, occupational_series, occupational_series_code",
         UNDER1, "screen_naive_employment")
    pull(c, urls(fm, "separations", SCREEN_START), "personnel_action_effective_date_yyyymm",
         "agency, agency_subelement, agency_subelement_code, occupational_series, occupational_series_code, "
         "separation_category, drp_indicator",
         UNDER1, "screen_naive_separations")

    # ---- Same screen, permanent appointments only (the version worth ranking) ----
    pull(c, urls(fm, "employment", SCREEN_START), "snapshot_yyyymm",
         "agency, agency_subelement, agency_subelement_code",
         f"{UNDER1} AND {PERM}", "screen_perm_employment")
    pull(c, urls(fm, "separations", SCREEN_START), "personnel_action_effective_date_yyyymm",
         "agency, agency_subelement, agency_subelement_code",
         f"{UNDER1} AND {PERM}", "screen_perm_separations")
    pull(c, urls(fm, "accessions", SCREEN_START), "personnel_action_effective_date_yyyymm",
         "agency, agency_subelement, agency_subelement_code",
         f"accession_category LIKE 'NEW HIRE%' AND {PERM}", "screen_perm_accessions")

    # ---- Raw (unbucketed) tenure-at-separation, for the implied-hire-month correction ----
    LOS2 = "TRY_CAST(length_of_service_years AS DOUBLE) < 2"
    pull(c, urls(fm, "separations", "202509"), "personnel_action_effective_date_yyyymm",
         "agency, agency_subelement, agency_subelement_code, length_of_service_years",
         f"{LOS2} AND {PERM}", "screen_perm_sep_rawlos")
    pull(c, urls(fm, "separations", "202409", "202507"), "personnel_action_effective_date_yyyymm",
         "agency, agency_subelement, agency_subelement_code, length_of_service_years",
         f"{LOS2} AND {PERM}", "screen_perm_sep_rawlos_prioryear")

    # ---- IRS drill-down ----
    IRS = "agency_subelement_code = 'TR93'"
    pull(c, urls(fm, "accessions", "202409"), "personnel_action_effective_date_yyyymm",
         "occupational_series, occupational_series_code, grade, age_bracket, accession_category",
         f"{IRS} AND accession_category LIKE 'NEW HIRE%' AND {PERM}", "irs_accessions")
    pull(c, urls(fm, "separations", "202509"), "personnel_action_effective_date_yyyymm",
         "occupational_series, occupational_series_code, grade, age_bracket, separation_category, "
         "drp_indicator, length_of_service_years",
         f"{IRS} AND {PERM} AND {LOS2}", "irs_separations")

    # ---- IRS Contact Representatives (0962), 2019-> : is 2025-26 actually unusual? ----
    IRS_0962 = f"{IRS} AND occupational_series_code = '0962'"
    pull(c, urls(fm, "accessions", HIST_START), "personnel_action_effective_date_yyyymm",
         "", f"{IRS_0962} AND accession_category LIKE 'NEW HIRE%' AND {PERM}", "irs_0962_accessions_hist")
    pull(c, urls(fm, "separations", HIST_START), "personnel_action_effective_date_yyyymm",
         "length_of_service_years, separation_category, drp_indicator",
         f"{IRS_0962} AND {PERM} AND {LOS2}", "irs_0962_separations_hist")
    pull(c, urls(fm, "employment", HIST_START), "snapshot_yyyymm",
         "length_of_service_years", f"{IRS_0962} AND {PERM}", "irs_0962_employment_hist")
    # Same population, but NO tenure filter -- needed to see whether departures across the
    # WHOLE workforce (not just recent hires) are voluntary or not, and whether a DRP wave
    # among longer-tenured staff explains the headcount collapse better than organic quitting.
    pull(c, urls(fm, "separations", HIST_START), "personnel_action_effective_date_yyyymm",
         "separation_category, drp_indicator", f"{IRS_0962} AND {PERM}", "irs_0962_separations_alltenure")
    # Tenure AT HIRE for 0962 new hires -- checks how much of a blind spot
    # implied_hire_cohort() has: a lateral hire with prior federal credit shows that prior
    # tenure at separation too, so a quick quitter among them would get an implied hire
    # date years in the past and silently drop out of the cohort count.
    pull(c, urls(fm, "accessions", HIST_START), "personnel_action_effective_date_yyyymm",
         "length_of_service_years", f"{IRS_0962} AND accession_category LIKE 'NEW HIRE%' AND {PERM}",
         "irs_0962_accessions_los")


if __name__ == "__main__":
    run()
