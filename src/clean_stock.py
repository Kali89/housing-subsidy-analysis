"""
Parse MHCLG Table 100 dwelling-stock estimates (2024) by tenure and local authority.

Source: mhclg_table100.ods  (Live Table 100, published May 2025, data to 31 March 2024)
Output columns: la_code, la_name_mhclg, la_owned_stock, prp_stock, total_social_stock
"""

import pandas as pd

from .constants import LA_CODE_RE, RAW

_SHEET = "2024"
_HEADER_ROW = 4   # 0-indexed; row 4 is the column header in the 2024 sheet

# 0-based column positions (post-header)
_COL_OLD_CODE = 0
_COL_NEW_CODE = 1
_COL_NAME = 2
_COL_LA_OWNED = 3
_COL_PRP = 4
_COL_OTHER_PUBLIC = 5


def clean_mhclg_stock() -> pd.DataFrame:
    """Return LA-level social housing stock: LA-owned and PRP units."""
    raw = pd.read_excel(
        RAW / "mhclg_table100.ods",
        sheet_name=_SHEET,
        engine="odf",
        header=_HEADER_ROW,
    )
    raw.columns = range(raw.shape[1])

    # Filter to LA-level rows (E06–E09)
    la_mask = raw.iloc[:, _COL_NEW_CODE].astype(str).str.match(LA_CODE_RE)
    raw = raw.loc[la_mask].copy()

    df = pd.DataFrame(
        {
            "la_code": raw.iloc[:, _COL_NEW_CODE].astype(str).str.strip(),
            "la_name_mhclg": raw.iloc[:, _COL_NAME].astype(str).str.strip(),
            "la_owned_stock": pd.to_numeric(raw.iloc[:, _COL_LA_OWNED], errors="coerce"),
            "prp_stock": pd.to_numeric(raw.iloc[:, _COL_PRP], errors="coerce"),
        }
    )
    df["total_social_stock"] = df["la_owned_stock"].fillna(0) + df["prp_stock"].fillna(0)

    print(f"  [MHCLG Stock] {len(df)} LAs")
    return df
