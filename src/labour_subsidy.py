"""
Visualise the 'London labour subsidy' argument:
social housing in central London acts as an implicit employer wage subsidy
by keeping the effective cost of labour below what a genuine market would require.

Produces data/processed/fig_labour_subsidy.png
Run standalone:  python -m src.labour_subsidy
"""

from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .constants import PROCESSED

# Assume ~28% effective marginal rate (basic-rate income tax + employee NI).
# A worker needs ~£1.39 extra gross pay for every £1 increase in net outgoings.
GROSS_UP = 1 / (1 - 0.28)

REGION_ORDER = [
    "London",
    "South East",
    "East of England",
    "South West",
    "East Midlands",
    "West Midlands",
    "North West",
    "Yorkshire and The Humber",
    "North East",
]

PALETTE = {
    "social_rent": "#2c6fad",
    "subsidy":     "#e05b2b",
    "London":      "#c0392b",
    "other":       "#5b8db8",
}


# ── Data preparation ──────────────────────────────────────────────────────────

def _build_regional_data() -> pd.DataFrame:
    summary = pd.read_csv(PROCESSED / "subsidy_summary_by_la.csv")
    long    = pd.read_csv(PROCESSED / "subsidy_by_la_bedroom.csv")

    units_by_la = (
        long.dropna(subset=["social_units"])
        .groupby("la_code")["social_units"].sum()
        .rename("total_social_units_rsh")
    )
    df = summary.merge(units_by_la, on="la_code", how="left")
    df["units"] = df["total_social_units_rsh"].fillna(df["total_social_stock"])
    df = df.dropna(subset=["subsidy_social_wtavg_annual", "units", "region"])
    df = df[df["units"] > 0]

    avg_rents = (
        long.dropna(subset=["social_rent_monthly", "market_rent_monthly", "social_units"])
        .assign(
            s_wt=lambda x: x["social_rent_monthly"] * x["social_units"],
            m_wt=lambda x: x["market_rent_monthly"] * x["social_units"],
        )
        .groupby("la_code")
        .agg(s_wt=("s_wt", "sum"), m_wt=("m_wt", "sum"), u=("social_units", "sum"))
        .assign(
            avg_social_rent=lambda x: x["s_wt"] / x["u"],
            avg_market_rent=lambda x: x["m_wt"] / x["u"],
        )[["avg_social_rent", "avg_market_rent"]]
    )
    df = df.merge(avg_rents, on="la_code", how="left")

    eng_total_subsidy = (df["subsidy_social_wtavg_annual"] * df["units"]).sum()
    eng_total_units   = df["units"].sum()

    reg = (
        df.groupby("region")
        .apply(
            lambda g: pd.Series({
                "total_subsidy": (g["subsidy_social_wtavg_annual"] * g["units"]).sum(),
                "total_units":   g["units"].sum(),
                "avg_social_rent": np.average(
                    g["avg_social_rent"].dropna(),
                    weights=g.loc[g["avg_social_rent"].notna(), "units"],
                ),
                "avg_market_rent": np.average(
                    g["avg_market_rent"].dropna(),
                    weights=g.loc[g["avg_market_rent"].notna(), "units"],
                ),
            }),
            include_groups=False,
        )
        .reset_index()
    )

    reg["avg_subsidy_monthly"]      = reg["avg_market_rent"] - reg["avg_social_rent"]
    reg["subsidy_share_pct"]        = reg["total_subsidy"] / eng_total_subsidy * 100
    reg["stock_share_pct"]          = reg["total_units"]   / eng_total_units   * 100
    reg["disproportionality"]       = reg["subsidy_share_pct"] / reg["stock_share_pct"]
    reg["monthly_gross_wage_saving"] = reg["avg_subsidy_monthly"] * GROSS_UP
    reg["annual_employer_saving_bn"] = reg["total_subsidy"] * GROSS_UP / 1e9
    reg["is_london"]                 = reg["region"] == "London"

    # Enforce display order, drop any regions not in our list
    reg = reg[reg["region"].isin(REGION_ORDER)].copy()
    reg["order"] = reg["region"].map({r: i for i, r in enumerate(REGION_ORDER)})
    reg = reg.sort_values("order")
    return reg


# ── Chart ─────────────────────────────────────────────────────────────────────

def plot_labour_subsidy(reg: pd.DataFrame, out_path: Path) -> None:
    fig = plt.figure(figsize=(14, 11))
    fig.patch.set_facecolor("white")

    gs = gridspec.GridSpec(
        2, 2, figure=fig,
        hspace=0.45, wspace=0.38,
        left=0.08, right=0.97, top=0.91, bottom=0.07,
    )
    ax_wedge  = fig.add_subplot(gs[0, 0])   # top-left:  rent wedge
    ax_dispro = fig.add_subplot(gs[0, 1])   # top-right: disproportionality
    ax_total  = fig.add_subplot(gs[1, :])   # bottom:    total employer benefit

    colors = [PALETTE["London"] if r == "London" else PALETTE["other"]
              for r in reg["region"]]

    # ── Panel 1: Rent wedge ────────────────────────────────────────────────
    y_pos   = np.arange(len(reg))
    regions = reg["region"].tolist()

    # Horizontal stacked bars: social rent (blue) + subsidy gap (orange) = market rent
    ax_wedge.barh(
        y_pos, reg["avg_social_rent"],
        color=PALETTE["social_rent"], height=0.6, label="Avg social rent paid",
    )
    ax_wedge.barh(
        y_pos, reg["avg_subsidy_monthly"],
        left=reg["avg_social_rent"],
        color=PALETTE["subsidy"], height=0.6, alpha=0.85,
        label="Implicit subsidy\n(state bridges this gap)",
    )
    # Market rent tick mark
    for i, row in reg.iterrows():
        idx = reg.index.get_loc(i)
        ax_wedge.plot(
            [row["avg_market_rent"]] * 2,
            [idx - 0.38, idx + 0.38],
            color="#333", linewidth=1.2, zorder=5,
        )

    ax_wedge.set_yticks(y_pos)
    ax_wedge.set_yticklabels(
        [f"{'◀ ' if r == 'London' else ''}{r}" for r in regions],
        fontsize=8.5,
    )
    ax_wedge.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax_wedge.set_xlabel("Average monthly rent per social unit (£)", fontsize=9)
    ax_wedge.set_title(
        "Social rent + implicit subsidy = market rent\n"
        "The orange gap is the effective wage subsidy to employers",
        fontsize=9, color="#333",
    )
    ax_wedge.spines["top"].set_visible(False)
    ax_wedge.spines["right"].set_visible(False)
    ax_wedge.tick_params(axis="x", labelsize=8)
    legend = ax_wedge.legend(
        fontsize=8, loc="lower right", framealpha=0.9, edgecolor="#ccc",
    )
    # Colour London label
    for lbl, r in zip(ax_wedge.get_yticklabels(), regions):
        if r == "London":
            lbl.set_color(PALETTE["London"])
            lbl.set_fontweight("bold")

    # ── Panel 2: Disproportionality ────────────────────────────────────────
    max_val = max(reg["subsidy_share_pct"].max(), reg["stock_share_pct"].max()) * 1.08
    ax_dispro.plot([0, max_val], [0, max_val], color="#aaa", linewidth=1,
                   linestyle="--", zorder=1, label="Proportional line")

    for _, row in reg.iterrows():
        ax_dispro.scatter(
            row["stock_share_pct"], row["subsidy_share_pct"],
            s=row["total_units"] / 6_000,
            color=PALETTE["London"] if row["is_london"] else PALETTE["other"],
            alpha=0.85, zorder=3, edgecolors="white", linewidths=0.5,
        )
        label = row["region"].replace("Yorkshire and The Humber", "Yorks & Humber") \
                             .replace("East of England", "East of England")
        ha = "left"
        x_off, y_off = 0.3, 0.5
        if row["region"] == "London":
            x_off, y_off = 0.3, 0.8
        elif row["region"] in ("South East", "East of England"):
            x_off, y_off = 0.3, -1.0
        ax_dispro.annotate(
            label, xy=(row["stock_share_pct"], row["subsidy_share_pct"]),
            xytext=(row["stock_share_pct"] + x_off, row["subsidy_share_pct"] + y_off),
            fontsize=7, color=PALETTE["London"] if row["is_london"] else "#444",
            fontweight="bold" if row["is_london"] else "normal",
        )

    ax_dispro.set_xlabel("Share of England's social housing stock (%)", fontsize=9)
    ax_dispro.set_ylabel("Share of total implicit subsidy (%)", fontsize=9)
    ax_dispro.set_title(
        "Subsidy share vs stock share by region\n"
        "Above the line = gets more subsidy than its stock share warrants",
        fontsize=9, color="#333",
    )
    ax_dispro.set_xlim(0, max_val)
    ax_dispro.set_ylim(0, max_val)
    ax_dispro.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax_dispro.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax_dispro.spines["top"].set_visible(False)
    ax_dispro.spines["right"].set_visible(False)
    ax_dispro.tick_params(labelsize=8)

    # Disproportionality annotation for London
    lon = reg[reg["region"] == "London"].iloc[0]
    ax_dispro.annotate(
        f"2.3× over-represented:\n{lon['subsidy_share_pct']:.0f}% of subsidy\n"
        f"from {lon['stock_share_pct']:.0f}% of stock",
        xy=(lon["stock_share_pct"], lon["subsidy_share_pct"]),
        xytext=(lon["stock_share_pct"] - 11, lon["subsidy_share_pct"] - 13),
        fontsize=7.5, color=PALETTE["London"],
        arrowprops=dict(arrowstyle="->", color=PALETTE["London"], lw=0.8),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=PALETTE["London"],
                  alpha=0.9, linewidth=0.8),
    )

    # ── Panel 3: Total employer benefit ────────────────────────────────────
    # Plot in reverse order so London is at top
    reg_rev = reg.iloc[::-1].reset_index(drop=True)
    y3      = np.arange(len(reg_rev))
    colors3 = [PALETTE["London"] if r == "London" else PALETTE["other"]
               for r in reg_rev["region"]]

    bars = ax_total.barh(
        y3, reg_rev["annual_employer_saving_bn"],
        color=colors3, height=0.55, edgecolor="white", linewidth=0.3,
    )

    # Value labels on bars
    for bar, val, region in zip(bars, reg_rev["annual_employer_saving_bn"], reg_rev["region"]):
        x = bar.get_width()
        ax_total.text(
            x + 0.1, bar.get_y() + bar.get_height() / 2,
            f"£{x:.1f}bn",
            va="center", ha="left", fontsize=8,
            color=PALETTE["London"] if region == "London" else "#555",
            fontweight="bold" if region == "London" else "normal",
        )

    ax_total.set_yticks(y3)
    ax_total.set_yticklabels(
        [r.replace("Yorkshire and The Humber", "Yorks & Humber") for r in reg_rev["region"]],
        fontsize=9,
    )
    for lbl, r in zip(ax_total.get_yticklabels(), reg_rev["region"]):
        if r == "London":
            lbl.set_color(PALETTE["London"])
            lbl.set_fontweight("bold")

    ax_total.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:.0f}bn"))
    ax_total.set_xlabel(
        "Equivalent annual gross wage saving for employers (£bn)\n"
        f"[implicit social housing subsidy grossed up at {GROSS_UP:.2f}× for income tax + NI]",
        fontsize=8.5, color="#555",
    )
    ax_total.set_title(
        "Total annual employer labour cost saving by region\n"
        "How much extra in gross wages employers would need to pay if workers had to meet market rents",
        fontsize=9, color="#333",
    )
    ax_total.spines["top"].set_visible(False)
    ax_total.spines["right"].set_visible(False)
    ax_total.tick_params(axis="x", labelsize=8)
    ax_total.set_xlim(0, reg_rev["annual_employer_saving_bn"].max() * 1.18)

    # London callout annotation
    lon_val = reg_rev.loc[reg_rev["region"] == "London", "annual_employer_saving_bn"].iloc[0]
    lon_unit = reg_rev.loc[reg_rev["region"] == "London", "monthly_gross_wage_saving"].iloc[0]
    ax_total.annotate(
        f"London: £{lon_val:.1f}bn/yr — equivalent to\n"
        f"£{lon_unit:,.0f}/month gross per social unit\n"
        f"(≈ one full NLW salary per unit per year)",
        xy=(lon_val, len(reg_rev) - 1),
        xytext=(lon_val - 6.5, len(reg_rev) - 1 - 2.2),
        fontsize=8, color=PALETTE["London"],
        arrowprops=dict(arrowstyle="->", color=PALETTE["London"], lw=0.8),
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=PALETTE["London"],
                  alpha=0.95, linewidth=0.8),
    )

    # ── Title ──────────────────────────────────────────────────────────────
    fig.suptitle(
        "Social housing as an implicit employer wage subsidy:\n"
        "how below-market rents lower London's labour costs at national expense",
        fontsize=12, fontweight="bold", y=0.97, color="#111",
    )
    fig.text(
        0.5, 0.01,
        "Source: ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25 × MHCLG Table 100. "
        "290 English LAs. Gross-up assumes 28% effective marginal tax + NI rate.",
        ha="center", fontsize=7, color="#777",
    )

    fig.savefig(out_path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def run():
    out_path = PROCESSED / "fig_labour_subsidy.png"
    reg = _build_regional_data()
    plot_labour_subsidy(reg, out_path)


if __name__ == "__main__":
    run()
