"""
Combine LARP and PRP rents into a single per-LA per-bedroom dataset,
then join with ONS market rents.

Key design choices:
- PRP rents are location-based (stock is in the reported LA).
- LARP rents are reported by the owning LA regardless of location.
  For most authorities these coincide; the discrepancy is a noted caveat.
- Where both LARP and PRP have data for the same (LA, bedroom), we combine them
  into a single weighted average using the respective unit counts as weights.
- Region is taken from LARP data; LAs without LARP coverage inherit region
  via a separate region lookup derived from the same source.
"""

import pandas as pd

from .clean_ons import build_region_lookup, clean_ons_prms
from .clean_rsh_larp import clean_larp_affordable, clean_larp_social
from .clean_rsh_prp import clean_prp_affordable, clean_prp_social
from .clean_stock import clean_mhclg_stock


def _weighted_avg_rent(
    larp: pd.DataFrame,
    prp: pd.DataFrame,
    rent_col: str = "rent_monthly",
) -> pd.DataFrame:
    """
    Merge LARP and PRP rents for the same tenure type, producing a
    weighted-average monthly rent and total unit count per (LA, bedroom).

    Also carries the LARP region through (region is available in LARP only).
    """
    # Standardise column names before concat
    larp_std = larp[["la_code", "la_name_larp", "region", "bedrooms", "units", rent_col]].copy()
    larp_std.columns = ["la_code", "la_name", "region", "bedrooms", "units", "rent_monthly"]
    larp_std["source"] = "larp"

    prp_std = prp[["la_code", "bedrooms", "units", rent_col]].copy()
    prp_std.columns = ["la_code", "bedrooms", "units", "rent_monthly"]
    prp_std["la_name"] = pd.NA
    prp_std["region"] = pd.NA
    prp_std["source"] = "prp"

    combined = pd.concat([larp_std, prp_std], ignore_index=True)
    combined = combined.dropna(subset=["units", "rent_monthly"])
    combined = combined[combined["units"] > 0]

    combined["numer"] = combined["units"] * combined["rent_monthly"]

    agg = (
        combined.groupby(["la_code", "bedrooms"], as_index=False)
        .agg(
            units=("units", "sum"),
            numer=("numer", "sum"),
            la_name=("la_name", "first"),
            region=("region", "first"),
        )
    )
    agg["avg_rent_monthly"] = agg["numer"] / agg["units"]
    return agg[["la_code", "la_name", "region", "bedrooms", "units", "avg_rent_monthly"]]


def _build_region_lookup(larp_social: pd.DataFrame) -> pd.DataFrame:
    """Derive a la_code → (la_name, region) lookup from LARP social data."""
    return (
        larp_social[["la_code", "la_name_larp", "region"]]
        .drop_duplicates("la_code")
        .rename(columns={"la_name_larp": "la_name"})
    )


def build_analysis_dataset() -> pd.DataFrame:
    """
    Load, clean, and join all sources into one wide analysis dataset.

    Returns a DataFrame with one row per (LA, bedroom_size) and columns for
    market rent, social rent, affordable rent, and unit counts.
    """
    print("Loading source data ...")
    ons = clean_ons_prms()
    larp_soc = clean_larp_social()
    larp_aff = clean_larp_affordable()
    prp_soc = clean_prp_social()
    prp_aff = clean_prp_affordable()
    stock = clean_mhclg_stock()

    print("Combining LARP + PRP rents ...")
    social = _weighted_avg_rent(larp_soc, prp_soc)
    social = social.rename(columns={"units": "social_units", "avg_rent_monthly": "social_rent_monthly"})

    affordable = _weighted_avg_rent(larp_aff, prp_aff)
    affordable = affordable.rename(
        columns={"units": "affordable_units", "avg_rent_monthly": "affordable_rent_monthly"}
    )

    print("Merging with ONS market rents ...")
    df = ons.rename(columns={"la_name_ons": "la_name_ons"}).merge(
        social[["la_code", "la_name", "region", "bedrooms", "social_units", "social_rent_monthly"]],
        on=["la_code", "bedrooms"],
        how="outer",
    ).merge(
        affordable[["la_code", "bedrooms", "affordable_units", "affordable_rent_monthly"]],
        on=["la_code", "bedrooms"],
        how="outer",
    )

    # Fill la_name from LARP where ONS has a different name or is missing
    df["la_name"] = df["la_name"].fillna(df["la_name_ons"])
    df = df.drop(columns=["la_name_ons"], errors="ignore")

    # Fill region and la_name gaps using LARP lookup first, then ONS hierarchy
    larp_lookup = _build_region_lookup(larp_soc)
    ons_region_lookup = build_region_lookup()

    df = df.merge(
        larp_lookup[["la_code", "la_name", "region"]].rename(
            columns={"la_name": "la_name_lk", "region": "region_lk"}
        ),
        on="la_code", how="left",
    )
    df["region"] = df["region"].fillna(df["region_lk"])
    df["la_name"] = df["la_name"].fillna(df["la_name_lk"])
    df = df.drop(columns=["la_name_lk", "region_lk"], errors="ignore")

    # Second pass: fill remaining gaps from ONS region hierarchy
    df = df.merge(ons_region_lookup.rename(columns={"region_ons": "region_ons"}),
                  on="la_code", how="left")
    df["region"] = df["region"].fillna(df["region_ons"])
    df = df.drop(columns=["region_ons"], errors="ignore")

    print("Merging MHCLG total stock ...")
    df = df.merge(
        stock[["la_code", "la_owned_stock", "prp_stock", "total_social_stock"]],
        on="la_code",
        how="left",
    )

    # Filter to England LAs only (exclude any stray non-E codes)
    df = df[df["la_code"].str.match(r"^E0[6-9]", na=False)].copy()

    # Normalise region names (sources use slightly different capitalisations)
    _REGION_NORM = {
        "East": "East of England",
        "Yorkshire And The Humber": "Yorkshire and The Humber",
        "Yorkshire and the Humber": "Yorkshire and The Humber",
    }
    df["region"] = df["region"].replace(_REGION_NORM)

    print(f"  Combined dataset: {df['la_code'].nunique()} LAs, {len(df)} rows")
    return df
