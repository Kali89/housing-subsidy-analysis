"""
Compute implicit subsidy estimates from the merged rent dataset.

Definitions:
  subsidy_social     = market_rent_monthly - social_rent_monthly      (£/unit/month)
  subsidy_affordable = market_rent_monthly - affordable_rent_monthly   (£/unit/month)

Annual figures multiply monthly subsidy × 12 × unit_count.

Stock-weighted averages weight bedroom-size subsidies by the relevant unit counts
(social or affordable), giving a single per-LA per-tenure figure.

Notes on data limitations (reflected in NaN handling):
  - ONS PRMS covers Oct 2022–Sep 2023; RSH data is 2024–25. Rents have risen since,
    so subsidies are likely understated for the ONS period relative to current market.
  - Some LAs have no ONS market-rent observation (suppressed or zero sample); these
    return NaN subsidies and are excluded from aggregate statistics.
  - Some LAs have no RSH social or affordable rent data; likewise returned as NaN.
"""

import numpy as np
import pandas as pd

from .constants import BEDROOM_LABELS, PROCESSED
from .merge import build_analysis_dataset


def compute_subsidies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add subsidy columns to the per-(LA, bedroom) dataset and return it.
    Negative subsidies (where social rent exceeds market rent) are retained as-is.
    """
    df = df.copy()

    df["subsidy_social_monthly"] = df["market_rent_monthly"] - df["social_rent_monthly"]
    df["subsidy_social_annual_per_unit"] = df["subsidy_social_monthly"] * 12

    df["subsidy_affordable_monthly"] = df["market_rent_monthly"] - df["affordable_rent_monthly"]
    df["subsidy_affordable_annual_per_unit"] = df["subsidy_affordable_monthly"] * 12

    # Annual subsidy bill = per-unit × stock
    df["annual_subsidy_social_total"] = (
        df["subsidy_social_annual_per_unit"] * df["social_units"]
    )
    df["annual_subsidy_affordable_total"] = (
        df["subsidy_affordable_annual_per_unit"] * df["affordable_units"]
    )

    return df


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Weighted mean ignoring NaN pairs."""
    mask = values.notna() & weights.notna() & (weights > 0)
    if mask.sum() == 0:
        return np.nan
    return np.average(values[mask], weights=weights[mask])


def build_la_summary(long: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse the per-(LA, bedroom) dataset into one row per LA with:
      - bedroom-level rents and subsidies (wide format)
      - stock-weighted average subsidies
      - total annual subsidy bill (social and affordable)
    """
    rows = []
    for la_code, grp in long.groupby("la_code"):
        row = {
            "la_code": la_code,
            "la_name": grp["la_name"].iloc[0],
            "region": grp["region"].iloc[0],
        }

        # Bedroom-level values
        for bed in BEDROOM_LABELS:
            sub = grp[grp["bedrooms"] == bed]
            if len(sub) == 1:
                r = sub.iloc[0]
                row[f"market_rent_monthly_{bed}"] = r["market_rent_monthly"]
                row[f"social_rent_monthly_{bed}"] = r["social_rent_monthly"]
                row[f"affordable_rent_monthly_{bed}"] = r["affordable_rent_monthly"]
                row[f"subsidy_social_monthly_{bed}"] = r["subsidy_social_monthly"]
                row[f"subsidy_affordable_monthly_{bed}"] = r["subsidy_affordable_monthly"]
                row[f"social_units_{bed}"] = r["social_units"]
                row[f"affordable_units_{bed}"] = r["affordable_units"]
            else:
                for col in [
                    "market_rent_monthly", "social_rent_monthly", "affordable_rent_monthly",
                    "subsidy_social_monthly", "subsidy_affordable_monthly",
                    "social_units", "affordable_units",
                ]:
                    row[f"{col}_{bed}"] = np.nan

        # Stock-weighted average subsidies
        soc_vals = grp["subsidy_social_monthly"].values
        soc_wts = grp["social_units"].values
        aff_vals = grp["subsidy_affordable_monthly"].values
        aff_wts = grp["affordable_units"].values

        row["subsidy_social_wtavg_monthly"] = _weighted_mean(
            pd.Series(soc_vals), pd.Series(soc_wts)
        )
        row["subsidy_affordable_wtavg_monthly"] = _weighted_mean(
            pd.Series(aff_vals), pd.Series(aff_wts)
        )
        row["subsidy_social_wtavg_annual"] = (
            row["subsidy_social_wtavg_monthly"] * 12
            if pd.notna(row["subsidy_social_wtavg_monthly"])
            else np.nan
        )
        row["subsidy_affordable_wtavg_annual"] = (
            row["subsidy_affordable_wtavg_monthly"] * 12
            if pd.notna(row["subsidy_affordable_wtavg_monthly"])
            else np.nan
        )

        # Total annual subsidy bill (sum across bedroom sizes)
        row["total_annual_subsidy_social"] = grp["annual_subsidy_social_total"].sum(
            min_count=1
        )
        row["total_annual_subsidy_affordable"] = grp["annual_subsidy_affordable_total"].sum(
            min_count=1
        )

        # MHCLG stock totals (same for all bedroom rows in the group)
        row["la_owned_stock"] = grp["la_owned_stock"].iloc[0]
        row["prp_stock"] = grp["prp_stock"].iloc[0]
        row["total_social_stock"] = grp["total_social_stock"].iloc[0]

        rows.append(row)

    summary = pd.DataFrame(rows)
    summary = summary.sort_values(
        "subsidy_social_wtavg_annual", ascending=False, na_position="last"
    ).reset_index(drop=True)
    return summary


def run_analysis() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the full analysis pipeline and return (long_df, summary_df).
    Also writes both to data/processed/.
    """
    PROCESSED.mkdir(parents=True, exist_ok=True)

    print("=== Building analysis dataset ===")
    long = build_analysis_dataset()

    print("=== Computing subsidies ===")
    long = compute_subsidies(long)

    print("=== Building LA summary ===")
    summary = build_la_summary(long)

    long_path = PROCESSED / "subsidy_by_la_bedroom.csv"
    summary_path = PROCESSED / "subsidy_summary_by_la.csv"

    long.to_csv(long_path, index=False)
    summary.to_csv(summary_path, index=False)

    print(f"\nOutput written to:")
    print(f"  {long_path}")
    print(f"  {summary_path}")
    print(f"\nTop 5 LAs by stock-weighted social subsidy:")
    cols = ["la_name", "region", "subsidy_social_wtavg_annual", "total_annual_subsidy_social"]
    print(summary[cols].head(5).to_string(index=False))

    return long, summary
