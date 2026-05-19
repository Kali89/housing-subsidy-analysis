"""
Visualise social housing new supply trends:
  1. The long-run collapse of social rent completions (1991–2025)
  2. What tenure is actually being built in each region today
  3. Annual social rent renewal rate by region vs existing stock

Produces data/processed/fig_new_supply.png
Run standalone:  python -m src.new_supply
"""

from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .constants import PROCESSED

RAW = PROCESSED.parent / "raw"

REGION_ORDER = [
    "South West", "West Midlands", "South East", "East of England",
    "East Midlands", "Yorkshire and The Humber", "London", "North West", "North East",
]

PALETTE = {
    "Social Rent":              "#2c6fad",
    "London Affordable Rent":   "#6aafe6",
    "Affordable Rent":          "#e07b39",
    "London":                   "#c0392b",
    "other":                    "#5b8db8",
    "annotation":               "#444",
}


def _load_completions() -> pd.DataFrame:
    df = pd.read_csv(RAW / "ahs_open_data.csv", low_memory=False)
    df = df[df["Completions"] == "Completion"].copy()
    df["year_start"] = df["Year"].str[:4].astype(int)
    return df


def _national_trend(df: pd.DataFrame) -> pd.DataFrame:
    tenures = ["Social Rent", "Affordable Rent", "London Affordable Rent"]
    annual = (
        df[df["Tenure"].isin(tenures)]
        .groupby(["Year", "year_start", "Tenure"])["Units"]
        .sum().reset_index()
    )
    pivot = (
        annual.pivot_table(index=["Year", "year_start"], columns="Tenure",
                           values="Units", aggfunc="sum")
        .fillna(0).reset_index().sort_values("year_start")
    )
    return pivot


def _regional_data(df: pd.DataFrame) -> pd.DataFrame:
    summary = pd.read_csv(PROCESSED / "subsidy_summary_by_la.csv")
    stock = (
        summary.dropna(subset=["region"])
        .groupby("region")
        .agg(la_owned=("la_owned_stock", "sum"), prp=("prp_stock", "sum"))
        .assign(total_stock=lambda x: x["la_owned"] + x["prp"])
        .reset_index()
    )

    region_map = {r: r for r in REGION_ORDER}
    region_map["Yorkshire and The Humber"] = "Yorkshire and The Humber"

    tenures = ["Social Rent", "Affordable Rent", "London Affordable Rent"]
    recent = df[(df["year_start"] >= 2020) & (df["Tenure"].isin(tenures))]
    reg_comp = (
        recent.groupby(["Region name", "Tenure"])["Units"]
        .sum().unstack(fill_value=0).reset_index()
    )
    for t in tenures:
        if t not in reg_comp.columns:
            reg_comp[t] = 0

    reg_comp["region"] = reg_comp["Region name"].map(region_map)
    reg_comp = reg_comp.merge(stock, on="region", how="left")
    reg_comp["annual_sr_rate_pct"] = (
        reg_comp["Social Rent"] / 5 / reg_comp["total_stock"] * 100
    )
    return reg_comp


def plot_new_supply(out_path: Path) -> None:
    df = _load_completions()
    trend = _national_trend(df)
    reg   = _regional_data(df)
    reg   = reg[reg["region"].isin(REGION_ORDER)].copy()
    reg["order"] = reg["region"].map({r: i for i, r in enumerate(REGION_ORDER)})
    reg = reg.sort_values("order")

    eng_stock      = reg["total_stock"].sum()
    eng_sr_ann     = reg["Social Rent"].sum() / 5
    eng_rate       = eng_sr_ann / eng_stock * 100
    years_to_replace = 100 / eng_rate

    # ── Figure layout ──────────────────────────────────────────────────────
    fig = plt.figure(figsize=(14, 11))
    fig.patch.set_facecolor("white")
    gs = gridspec.GridSpec(
        2, 2, figure=fig,
        hspace=0.42, wspace=0.38,
        left=0.07, right=0.97, top=0.91, bottom=0.07,
    )
    ax_trend  = fig.add_subplot(gs[0, :])   # full-width time series
    ax_tenure = fig.add_subplot(gs[1, 0])   # bottom-left: tenure mix by region
    ax_rate   = fig.add_subplot(gs[1, 1])   # bottom-right: renewal rate

    # ── Panel 1: National trend ────────────────────────────────────────────
    x = trend["year_start"].values
    sr  = trend["Social Rent"].values
    ar  = trend.get("Affordable Rent",  pd.Series(0, index=trend.index)).values
    lar = trend.get("London Affordable Rent", pd.Series(0, index=trend.index)).values

    ax_trend.stackplot(
        x, sr, ar, lar,
        labels=["Social Rent", "Affordable Rent", "London Affordable Rent"],
        colors=[PALETTE["Social Rent"], PALETTE["Affordable Rent"],
                PALETTE["London Affordable Rent"]],
        alpha=0.85,
    )
    ax_trend.set_xlim(x.min(), x.max())
    ax_trend.set_ylim(0)
    ax_trend.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k")
    )
    ax_trend.set_ylabel("Completions per year", fontsize=9)
    ax_trend.set_xlabel("Year", fontsize=9)
    ax_trend.tick_params(labelsize=8)
    ax_trend.spines["top"].set_visible(False)
    ax_trend.spines["right"].set_visible(False)

    # Key annotations
    peak_sr = trend["Social Rent"].max()
    peak_yr = trend.loc[trend["Social Rent"].idxmax(), "year_start"]
    ax_trend.annotate(
        f"Peak: {peak_sr/1000:.0f}k Social Rent/yr\n({peak_yr}–{peak_yr%100+1:02d})",
        xy=(peak_yr, peak_sr), xytext=(peak_yr - 2, peak_sr + 5000),
        fontsize=7.5, color=PALETTE["Social Rent"],
        arrowprops=dict(arrowstyle="->", color=PALETTE["Social Rent"], lw=0.8),
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=PALETTE["Social Rent"],
                  alpha=0.9, lw=0.7),
    )
    ax_trend.axvline(2011, color="#999", linewidth=1, linestyle=":", alpha=0.8)
    ax_trend.text(
        2011.2, ax_trend.get_ylim()[1] * 0.88,
        "2011–12: Coalition\nintroduces Affordable\nRent at up to 80%\nof market rent",
        fontsize=7, color="#555", va="top",
    )
    trough_yr = trend.loc[trend["Social Rent"].idxmin(), "year_start"]
    trough_sr = trend["Social Rent"].min()
    ax_trend.annotate(
        f"Trough: {trough_sr/1000:.1f}k/yr\n({trough_yr}–{trough_yr%100+1:02d})",
        xy=(trough_yr, trough_sr), xytext=(trough_yr + 1, trough_sr + 8000),
        fontsize=7.5, color=PALETTE["Social Rent"],
        arrowprops=dict(arrowstyle="->", color=PALETTE["Social Rent"], lw=0.8),
        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=PALETTE["Social Rent"],
                  alpha=0.9, lw=0.7),
    )
    current_sr = trend.loc[trend["year_start"] == 2024, "Social Rent"].values[0]
    ax_trend.text(
        2024.3, current_sr / 2,
        f"2024–25:\n{current_sr/1000:.0f}k/yr\n({current_sr/peak_sr*100:.0f}% of peak)",
        fontsize=7.5, color=PALETTE["Social Rent"], va="center",
    )
    ax_trend.legend(loc="upper right", fontsize=8, framealpha=0.9, edgecolor="#ddd")
    ax_trend.set_title(
        "England: annual affordable housing completions by tenure, 1991–2025\n"
        "Social Rent (genuine social housing) was largely replaced by the less-subsidised "
        "Affordable Rent tenure after 2012",
        fontsize=9, color="#333", pad=4,
    )

    # ── Panel 2: Tenure mix by region 2020–25 ─────────────────────────────
    y_pos   = np.arange(len(reg))
    regions = [r.replace("Yorkshire and The Humber", "Yorks & Humber")
               for r in reg["region"]]
    bar_colors = [PALETTE["London"] if r == "London" else PALETTE["other"]
                  for r in reg["region"]]

    ax_tenure.barh(
        y_pos, reg["Social Rent"] / 1000,
        color=PALETTE["Social Rent"], height=0.55, label="Social Rent",
    )
    ax_tenure.barh(
        y_pos, reg["London Affordable Rent"] / 1000,
        left=reg["Social Rent"] / 1000,
        color=PALETTE["London Affordable Rent"], height=0.55,
        label="London Affordable Rent",
    )
    ax_tenure.barh(
        y_pos, reg["Affordable Rent"] / 1000,
        left=(reg["Social Rent"] + reg["London Affordable Rent"]) / 1000,
        color=PALETTE["Affordable Rent"], height=0.55, alpha=0.85,
        label="Affordable Rent (≤80% market)",
    )

    ax_tenure.set_yticks(y_pos)
    ax_tenure.set_yticklabels(regions, fontsize=8.5)
    for lbl, r in zip(ax_tenure.get_yticklabels(), reg["region"]):
        if r == "London":
            lbl.set_color(PALETTE["London"])
            lbl.set_fontweight("bold")
    ax_tenure.set_xlabel("Completions 2020–25 (thousands)", fontsize=9)
    ax_tenure.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.0f}k")
    )
    ax_tenure.set_title(
        "What is actually being built? (2020–25)\nLondon's completions lean heavily on\n"
        "less-subsidised tenures",
        fontsize=9, color="#333", pad=4,
    )
    ax_tenure.spines["top"].set_visible(False)
    ax_tenure.spines["right"].set_visible(False)
    ax_tenure.tick_params(labelsize=8)
    ax_tenure.legend(fontsize=7.5, loc="lower right", framealpha=0.9, edgecolor="#ddd")

    # ── Panel 3: Annual renewal rate ───────────────────────────────────────
    reg_rate = reg.sort_values("annual_sr_rate_pct")
    regions_r = [r.replace("Yorkshire and The Humber", "Yorks & Humber")
                 for r in reg_rate["region"]]
    bar_cols_r = [PALETTE["London"] if r == "London" else PALETTE["other"]
                  for r in reg_rate["region"]]

    ax_rate.barh(
        np.arange(len(reg_rate)), reg_rate["annual_sr_rate_pct"],
        color=bar_cols_r, height=0.55, edgecolor="white", linewidth=0.3,
    )
    # England average line
    ax_rate.axvline(
        eng_rate, color="#555", linewidth=1.2, linestyle="--", alpha=0.8,
        label=f"England avg {eng_rate:.2f}%/yr",
    )
    ax_rate.set_yticks(np.arange(len(reg_rate)))
    ax_rate.set_yticklabels(regions_r, fontsize=8.5)
    for lbl, r in zip(ax_rate.get_yticklabels(), reg_rate["region"]):
        if r == "London":
            lbl.set_color(PALETTE["London"])
            lbl.set_fontweight("bold")
    ax_rate.set_xlabel("Social rent completions per year\nas % of existing social housing stock", fontsize=9)
    ax_rate.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:.2f}%")
    )
    ax_rate.set_title(
        "Annual Social Rent renewal rate by region\n"
        f"England average: {eng_rate:.2f}%/yr → stock turns over in ~{years_to_replace:.0f} yrs",
        fontsize=9, color="#333", pad=4,
    )
    ax_rate.legend(fontsize=8, loc="lower right", framealpha=0.9, edgecolor="#ddd")
    ax_rate.spines["top"].set_visible(False)
    ax_rate.spines["right"].set_visible(False)
    ax_rate.tick_params(labelsize=8)

    # ── Title + footnote ───────────────────────────────────────────────────
    fig.suptitle(
        "Social housing new supply in England: the legacy stock problem is not self-correcting",
        fontsize=12, fontweight="bold", y=0.97, color="#111",
    )
    fig.text(
        0.5, 0.01,
        "Source: MHCLG Affordable Housing Supply open data 1991–2025; "
        "MHCLG Live Table 100 (stock, March 2024). "
        "Renewal rate = annual Social Rent completions ÷ total social housing stock.",
        ha="center", fontsize=7, color="#777",
    )

    fig.savefig(out_path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def run():
    out_path = PROCESSED / "fig_new_supply.png"
    plot_new_supply(out_path)


if __name__ == "__main__":
    run()
