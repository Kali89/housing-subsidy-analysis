"""
Parse RSH Local Authority Registered Provider (LARP) rents into tidy long format.

Source: rsh_larp_2025.xlsx  (2024–25 data, published October 2025)
Rents are in £/week; we convert to £/month.

Caveats:
- LARP data is reported by the *owning* LA, not the geographic location of the stock.
  For most LAs their stock is within their own area, but cross-boundary ownership
  creates a small mismatch for some authorities.

Output columns (for both social and affordable):
    la_code, la_name_larp, region, bedrooms, units, rent_weekly, rent_monthly
"""

import numpy as np
import pandas as pd

from .constants import RAW, WEEKLY_TO_MONTHLY

# Row containing column headers (0-indexed); data from the row after
_HEADER_ROW = 5

# Column positions shared by both the social-rent and affordable-rent sheets
_COL_LA_NAME = 2
_COL_LA_CODE = 3     # ONS GSS code
_COL_REGION = 4

# Social rent (LADR25_Low_Cost_Rental_Data)
# "General Needs - excluding AR, HIST and all units excepted in the policy statement"
_SOCIAL_COUNT_COLS = {
    "1_bed": 11,
    "2_bed": 12,
    "3_bed": 13,
    "4plus_bed": 14,   # "Four bedrooms" – the RSH table also has 5-bed and 6+ but
}                       # ONS PRMS tops out at "4 or more"; we aggregate below.
_SOCIAL_RENT_COLS = {
    "1_bed": 21,        # avg weekly NET rent
    "2_bed": 22,
    "3_bed": 23,
    "4plus_bed": 24,
}
# Extra bedroom sizes to fold into "4plus_bed"
_SOCIAL_COUNT_COLS_EXTRA = {"5_bed": 15, "6plus_bed": 16}
_SOCIAL_RENT_COLS_EXTRA = {"5_bed": 25, "6plus_bed": 26}

# Affordable rent (LADR25_Affordable_Rent_Data) – same column offsets
_AR_COUNT_COLS = {k: v for k, v in _SOCIAL_COUNT_COLS.items()}
_AR_COUNT_COLS_EXTRA = {k: v for k, v in _SOCIAL_COUNT_COLS_EXTRA.items()}
_AR_RENT_COLS = {k: v for k, v in _SOCIAL_RENT_COLS.items()}
_AR_RENT_COLS_EXTRA = {k: v for k, v in _SOCIAL_RENT_COLS_EXTRA.items()}


def _numeric(series: pd.Series) -> pd.Series:
    """Replace '[x]' markers and coerce to float."""
    return pd.to_numeric(series.replace(r"^\[x\]$", np.nan, regex=True), errors="coerce")


def _read_sheet(sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(
        RAW / "rsh_larp_2025.xlsx",
        sheet_name=sheet_name,
        engine="openpyxl",
        header=_HEADER_ROW,
    )
    # After header=_HEADER_ROW pandas reads the first column name from that row.
    # Rename positionally to avoid collision on duplicate names.
    df.columns = range(df.shape[1])
    return df


def _extract_long(
    df: pd.DataFrame,
    count_cols: dict,
    rent_cols: dict,
    count_cols_extra: dict,
    rent_cols_extra: dict,
) -> pd.DataFrame:
    """
    Build a long DataFrame with one row per (LA, bedroom_size).

    For '4plus_bed' we aggregate columns 4-bed + 5-bed + 6+ into a weighted average.
    """
    rows = []
    base_cols = list(count_cols.keys())  # ["1_bed", "2_bed", "3_bed", "4plus_bed"]

    for _, row in df.iterrows():
        la_code = str(row[_COL_LA_CODE]).strip()
        la_name = str(row[_COL_LA_NAME]).strip()
        region = str(row[_COL_REGION]).strip()

        if not la_code.startswith("E"):
            continue

        for bed in base_cols:
            if bed == "4plus_bed":
                # Aggregate 4, 5, 6+ into one weighted average
                pairs = [(count_cols["4plus_bed"], rent_cols["4plus_bed"])]
                for extra_key, extra_cnt in count_cols_extra.items():
                    pairs.append((extra_cnt, rent_cols_extra[extra_key]))

                total_units = 0
                weighted_rent = 0.0
                valid = False
                for c_col, r_col in pairs:
                    n = _numeric(pd.Series([row[c_col]])).iloc[0]
                    r = _numeric(pd.Series([row[r_col]])).iloc[0]
                    if pd.notna(n) and pd.notna(r) and n > 0:
                        total_units += n
                        weighted_rent += n * r
                        valid = True
                rent = (weighted_rent / total_units) if (valid and total_units > 0) else np.nan
                units = total_units if valid else np.nan
            else:
                units = _numeric(pd.Series([row[count_cols[bed]]])).iloc[0]
                rent = _numeric(pd.Series([row[rent_cols[bed]]])).iloc[0]

            rows.append(
                {
                    "la_code": la_code,
                    "la_name_larp": la_name,
                    "region": region,
                    "bedrooms": bed,
                    "units": units,
                    "rent_weekly": rent,
                }
            )

    result = pd.DataFrame(rows)
    result["rent_monthly"] = result["rent_weekly"] * WEEKLY_TO_MONTHLY
    return result


def clean_larp_social() -> pd.DataFrame:
    """LARP social (General Needs) rents by LA and bedroom size."""
    df = _read_sheet("LADR25_Low_Cost_Rental_Data")
    out = _extract_long(df, _SOCIAL_COUNT_COLS, _SOCIAL_RENT_COLS,
                        _SOCIAL_COUNT_COLS_EXTRA, _SOCIAL_RENT_COLS_EXTRA)
    print(f"  [LARP Social] {out['la_code'].nunique()} LAs, {len(out)} rows")
    return out


def clean_larp_affordable() -> pd.DataFrame:
    """LARP affordable rents by LA and bedroom size."""
    df = _read_sheet("LADR25_Affordable_Rent_Data")
    out = _extract_long(df, _AR_COUNT_COLS, _AR_RENT_COLS,
                        _AR_COUNT_COLS_EXTRA, _AR_RENT_COLS_EXTRA)
    print(f"  [LARP Affordable] {out['la_code'].nunique()} LAs, {len(out)} rows")
    return out
