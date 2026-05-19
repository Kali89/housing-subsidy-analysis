"""
Aggregate RSH Private Registered Provider (PRP) rents to local authority level.

Source: rsh_prp_2025.xlsx  (2024–25 data, published October 2025)
Input: one row per provider × LA combination.
Output: one row per LA × bedroom_size, weighted-average rent.

Sheets used:
  SDR25_RENTS_COMB_GN   – Combined general needs social rents (all providers,
                           covering both those with and without rent exceptions)
  SDR25_ARGN_Rents      – Affordable Rent, general needs

Rents are in £/week; we convert to £/month.
"""

import numpy as np
import pandas as pd

from .constants import RAW, WEEKLY_TO_MONTHLY

_HEADER_ROW = 3   # 0-indexed; row 3 is the column header row in both sheets

# Column positions for provider-level data (same in both COMB_GN and ARGN sheets)
_COL_LA_CODE = 4  # "LA code"

# SDR25_RENTS_COMB_GN: 7-column blocks per bedroom type, starting from col 13
# Pattern: [count, avg_net_rent, sc_eligible_count, avg_sc_eligible,
#           sc_ineligible_count, avg_sc_ineligible, hist_count]
# 1-bed starts at col 20, then +7 for each subsequent bedroom size.
_SOCIAL_COLS = {
    "1_bed":     (20, 21),
    "2_bed":     (27, 28),
    "3_bed":     (34, 35),
    "4_bed":     (41, 42),
    "5_bed":     (48, 49),
    "6plus_bed": (55, 56),
}

# SDR25_ARGN_Rents: 5-column blocks per bedroom type, starting from col 15
# Pattern: [count_excl_hist, avg_gross_rent_excl_hist, hist_count, avg_hist_rent, total_count]
# 1-bed starts at col 15, then +5 for each.
_AFFORDABLE_COLS = {
    "1_bed":     (15, 16),
    "2_bed":     (20, 21),
    "3_bed":     (25, 26),
    "4_bed":     (30, 31),
    "5_bed":     (35, 36),
    "6plus_bed": (40, 41),
}

# Map raw bedroom keys → canonical output labels
_BED_MAP = {
    "1_bed": "1_bed",
    "2_bed": "2_bed",
    "3_bed": "3_bed",
    # 4, 5, 6+ collapsed to match ONS "4 or more bedrooms" category
    "4_bed": "4plus_bed",
    "5_bed": "4plus_bed",
    "6plus_bed": "4plus_bed",
}


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace(r"^\[x\]$", np.nan, regex=True), errors="coerce")


def _read_sheet(sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(
        RAW / "rsh_prp_2025.xlsx",
        sheet_name=sheet_name,
        engine="openpyxl",
        header=_HEADER_ROW,
    )


def _aggregate_to_la(df: pd.DataFrame, bed_cols: dict) -> pd.DataFrame:
    """
    From a provider×LA DataFrame, produce a LA×bedroom weighted-average rent.

    Strategy:
      1. Melt each bedroom size into long format with (la_code, bedrooms, units, rent).
      2. Drop rows with missing LA code, units, or rent.
      3. Group by (la_code, bedrooms); weighted-average rent = sum(n*r)/sum(n).
      4. Collapse 4/5/6+ into "4plus_bed" before aggregation.
    """
    # Rename columns positionally to avoid pandas collision on duplicate names
    df = df.copy()
    df.columns = range(df.shape[1])

    la_col = df.iloc[:, _COL_LA_CODE].astype(str).str.strip()
    valid_la = la_col.str.match(r"^E\d")
    df = df.loc[valid_la].copy()

    rows = []
    for bed_key, (c_col, r_col) in bed_cols.items():
        canonical = _BED_MAP[bed_key]
        units = _numeric(df.iloc[:, c_col])
        rent = _numeric(df.iloc[:, r_col])
        sub = pd.DataFrame(
            {
                "la_code": la_col[valid_la].values,
                "bedrooms": canonical,
                "units": units.values,
                "rent_weekly": rent.values,
            }
        )
        rows.append(sub)

    long = pd.concat(rows, ignore_index=True)
    long = long.dropna(subset=["units", "rent_weekly"])
    long = long[long["units"] > 0]

    # Weighted-average rent within each (LA, bedroom) group
    long["numer"] = long["units"] * long["rent_weekly"]
    agg = (
        long.groupby(["la_code", "bedrooms"], as_index=False)
        .agg(units=("units", "sum"), numer=("numer", "sum"))
    )
    agg["rent_weekly"] = agg["numer"] / agg["units"]
    agg["rent_monthly"] = agg["rent_weekly"] * WEEKLY_TO_MONTHLY
    return agg[["la_code", "bedrooms", "units", "rent_weekly", "rent_monthly"]]


def clean_prp_social() -> pd.DataFrame:
    """PRP combined general-needs social rents aggregated to LA level."""
    df = _read_sheet("SDR25_RENTS_COMB_GN")
    out = _aggregate_to_la(df, _SOCIAL_COLS)
    print(f"  [PRP Social] {out['la_code'].nunique()} LAs, {len(out)} rows")
    return out


def clean_prp_affordable() -> pd.DataFrame:
    """PRP affordable rents aggregated to LA level."""
    df = _read_sheet("SDR25_ARGN_Rents")
    out = _aggregate_to_la(df, _AFFORDABLE_COLS)
    print(f"  [PRP Affordable] {out['la_code'].nunique()} LAs, {len(out)} rows")
    return out
