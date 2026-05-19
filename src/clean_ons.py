"""
Parse ONS Private Rental Market Statistics (PRMS) into a tidy long-format DataFrame.

Source: ons_prms.xls  (October 2022 – September 2023 edition, discontinued series)
Output columns: la_code, la_name_ons, bedrooms, market_rent_monthly
"""

import pandas as pd

from .constants import LA_CODE_RE, RAW

# Map of bedroom label → sheet name
_BEDROOM_SHEETS = {
    "1_bed": "Table2.3",
    "2_bed": "Table2.4",
    "3_bed": "Table2.5",
    "4plus_bed": "Table2.6",
}

# The sheet has 7 preamble rows; row index 6 = header, data starts at index 7
_HEADER_ROW = 6
_DATA_START = 7

# 0-based column positions within each sheet (post-preamble)
_COL_AREA_CODE = 2   # ONS E-code
_COL_AREA_NAME = 3
_COL_MEDIAN = 7      # median monthly rent (already in £/month)


def _read_one_sheet(sheet: str, bedroom_label: str) -> pd.DataFrame:
    raw = pd.read_excel(
        RAW / "ons_prms.xls",
        sheet_name=sheet,
        engine="xlrd",
        header=None,
    )
    data = raw.iloc[_DATA_START:].reset_index(drop=True)
    data.columns = range(data.shape[1])

    # Keep only LA-level rows (filter out England total, regional sub-totals, etc.)
    la_mask = data.iloc[:, _COL_AREA_CODE].astype(str).str.match(LA_CODE_RE)
    data = data.loc[la_mask].copy()

    return pd.DataFrame(
        {
            "la_code": data.iloc[:, _COL_AREA_CODE].astype(str).str.strip(),
            "la_name_ons": data.iloc[:, _COL_AREA_NAME].astype(str).str.strip(),
            "bedrooms": bedroom_label,
            # Some cells contain ".." (suppressed) – coerce to NaN
            "market_rent_monthly": pd.to_numeric(
                data.iloc[:, _COL_MEDIAN], errors="coerce"
            ),
        }
    )


def clean_ons_prms() -> pd.DataFrame:
    """Return tidy ONS market rents (monthly £) by LA and bedroom size."""
    frames = [_read_one_sheet(sheet, label) for label, sheet in _BEDROOM_SHEETS.items()]
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["market_rent_monthly"])
    print(f"  [ONS PRMS] {df['la_code'].nunique()} LAs, {len(df)} rows")
    return df


def build_region_lookup() -> pd.DataFrame:
    """
    Extract a la_code → region lookup from the hierarchical ONS PRMS sheet.

    The sheet interleaves England total, regional (E12) sub-totals, and LA rows.
    We assign each LA to the most recent preceding E12 region row.
    """
    raw = pd.read_excel(
        RAW / "ons_prms.xls", sheet_name="Table2.3", engine="xlrd", header=None
    )
    data = raw.iloc[_DATA_START:].reset_index(drop=True)
    data.columns = range(data.shape[1])

    rows = []
    current_region: str | None = None
    for _, row in data.iterrows():
        code = str(row[_COL_AREA_CODE]).strip()
        name = str(row[_COL_AREA_NAME]).strip()
        if code.startswith("E12"):
            current_region = name.title()
        elif code.startswith(("E06", "E07", "E08", "E09")):
            rows.append({"la_code": code, "region_ons": current_region})

    return pd.DataFrame(rows).drop_duplicates("la_code")
