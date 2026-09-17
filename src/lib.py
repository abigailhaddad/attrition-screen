"""Shared paths and helpers. See extract.py's docstring for what each data file is
and how it's filtered."""
from pathlib import Path
import duckdb
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

FBI_ACC = str(DATA / "fbi_accessions.parquet")
FBI_SEP = str(DATA / "fbi_separations.parquet")
FBI_EMP = str(DATA / "fbi_employment.parquet")

SCREEN_NAIVE_EMP = str(DATA / "screen_naive_employment.parquet")
SCREEN_NAIVE_SEP = str(DATA / "screen_naive_separations.parquet")
SCREEN_PERM_EMP = str(DATA / "screen_perm_employment.parquet")
SCREEN_PERM_SEP = str(DATA / "screen_perm_separations.parquet")
SCREEN_PERM_ACC = str(DATA / "screen_perm_accessions.parquet")
SCREEN_PERM_SEP_RAWLOS = str(DATA / "screen_perm_sep_rawlos.parquet")
SCREEN_PERM_SEP_RAWLOS_PRIORYEAR = str(DATA / "screen_perm_sep_rawlos_prioryear.parquet")

IRS_ACC = str(DATA / "irs_accessions.parquet")
IRS_SEP = str(DATA / "irs_separations.parquet")
IRS_0962_ACC_HIST = str(DATA / "irs_0962_accessions_hist.parquet")
IRS_0962_SEP_HIST = str(DATA / "irs_0962_separations_hist.parquet")
IRS_0962_EMP_HIST = str(DATA / "irs_0962_employment_hist.parquet")

DRP_MONTH = "202509"          # FBI's DRP-driven separations spike
POST_START, POST_END = "202509", "202607"    # the post-Sep-2025 hiring window this whole repo is anchored on
PRIOR_START, PRIOR_END = "202409", "202507"  # equal-length prior-year window, for comparison


def con():
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false;")
    return c


def dbl(col):
    return f"TRY_CAST({col} AS DOUBLE)"


def implied_hire_cohort(sep_df, window_start, window_end):
    """Given a raw separations extract (columns: ym, length_of_service_years, ..., n),
    back out each departure's implied hire month (event month minus tenure-at-departure)
    and keep only departures whose implied hire falls inside [window_start, window_end] --
    i.e. people actually hired in that window, not just anyone who happens to have short
    tenure when they leave. This is what makes the post-Sep-2025 numbers in this repo
    comparable across agencies with wildly different hiring trajectories: an agency whose
    hiring collapsed doesn't get a mechanically inflated rate, because departures are
    attributed to the hiring vintage that actually produced them, not to whatever the
    current (possibly tiny) headcount stock happens to be.
    """
    df = sep_df.copy()
    df["event_idx"] = df.ym.str[:4].astype(int) * 12 + df.ym.str[4:6].astype(int)
    df["los"] = pd.to_numeric(df.length_of_service_years, errors="coerce")
    df["implied_hire_idx"] = df.event_idx - (df.los * 12).round()
    start_idx = int(window_start[:4]) * 12 + int(window_start[4:6])
    end_idx = int(window_end[:4]) * 12 + int(window_end[4:6])
    return df[(df.implied_hire_idx >= start_idx) & (df.implied_hire_idx <= end_idx) & (df.event_idx <= end_idx)]
