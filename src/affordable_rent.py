"""
Affordable Rent at 80% of market: does it fix or replicate geographic inequality?

Social Rent is set by a national formula that barely tracks market rents, so it
compresses the rent gap between London and the North. Affordable Rent is just
a 20% discount off market, so it faithfully replicates — and sometimes exceeds —
local market prices.

Produces data/processed/fig_affordable_rent.png
Run standalone:  python -m src.affordable_rent
"""

from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .constants import PROCESSED


REGION_ORDER = [
    "London",
    "South East",
    "East of England",
    "South West",
    "West Midlands",
    "North West",
    "East Midlands",
    "Yorkshire and The Humber",
    "North East",
]

PALETTE = {
    "market":   "#555555",
    "ar":       "#e07b39",
    "sr":       "#2c6fad",
    "London":   "#c0392b",
    "other":    "#5b8db8",
    "negative": "#d62728",
}


def _build_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    long = pd.read_csv(PROCESSED / "subsidy_by_la_bedroom.csv")

    two = long[long["bedrooms"] == "2_bed"].dropna(
        subset=["market_rent_monthly", "social_rent_monthly",
                "affordable_rent_monthly", "region"]
    ).copy()

    two["sr_pct_mkt"] = two["social_rent_monthly"]   / two["market_rent_monthly"] * 100
    two["ar_pct_mkt"] = two["affordable_rent_monthly"] / two["market_rent_monthly"] * 100
    two["ar_over_market"] = two["affordable_rent_monthly"] > two["market_rent_monthly"]

    def _wavg(g, col, wt_col):
        w = g[wt_col].fillna(1)
        w = w.where(w > 0, 1)
        return np.average(g[col], weights=w)

    reg = (
        two.groupby("region")
        .apply(
            lambda g: pd.Series({
                "avg_market": _wavg(g, "market_rent_monthly",   "social_units"),
                "avg_sr":     _wavg(g, "social_rent_monthly",   "social_units"),
                "avg_ar":     _wavg(g, "affordable_rent_monthly", "affordable_units"),
                "n_las":      len(g),
                "n_ar_over_market": g["ar_over_market"].sum(),
            }),
            include_groups=False,
        )
        .reset_index()
    )
    reg["sr_pct_mkt"] = reg["avg_sr"] / reg["avg_market"] * 100
    reg["ar_pct_mkt"] = reg["avg_ar"] / reg["avg_market"] * 100

    reg = reg[reg["region"].isin(REGION_ORDER)].copy()
    reg["order"] = reg["region"].map({r: i for i, r in enumerate(REGION_ORDER)})
    reg = reg.sort_values("order").reset_index(drop=True)

    return reg, two


def plot_affordable_rent(out_path: Path) -> None:
    reg, la_level = _build_data()

    fig = plt.figure(figsize=(14, 12))
    fig.patch.set_facecolor("white")
    gs = gridspec.GridSpec(
        2, 2, figure=fig,
        hspace=0.45, wspace=0.40,
        left=0.07, right=0.97, top=0.91, bottom=0.07,
    )
    ax_ladder = fig.add_subplot(gs[0, :])   # full-width: rent ladder
    ax_pct    = fig.add_subplot(gs[1, 0])   # bottom-left: % of market
    ax_dist   = fig.add_subplot(gs[1, 1])   # bottom-right: LA-level distribution

    # ── Panel 1: Rent ladder by region ────────────────────────────────────
    n = len(reg)
    y_pos = np.arange(n)
    h = 0.24

    regions_short = [r.replace("Yorkshire and The Humber", "Yorks & Humber")
                     for r in reg["region"]]

    # Market rent (light grey background bar)
    ax_ladder.barh(y_pos + h, reg["avg_market"],
                   color=PALETTE["market"], height=h, alpha=0.25, label="Market rent")
    ax_ladder.barh(y_pos, reg["avg_ar"],
                   color=PALETTE["ar"], height=h, alpha=0.88, label="Affordable Rent (actual ~80%)")
    ax_ladder.barh(y_pos - h, reg["avg_sr"],
                   color=PALETTE["sr"], height=h, alpha=0.88, label="Social Rent")

    # Value labels on AR and SR bars
    for i, row in reg.iterrows():
        ax_ladder.text(row["avg_ar"]  + 12, i,          f'£{row["avg_ar"]:,.0f}',
                       va="center", fontsize=7.5, color=PALETTE["ar"])
        ax_ladder.text(row["avg_sr"]  + 12, i - h,      f'£{row["avg_sr"]:,.0f}',
                       va="center", fontsize=7.5, color=PALETTE["sr"])
        ax_ladder.text(row["avg_market"] + 12, i + h,   f'£{row["avg_market"]:,.0f}',
                       va="center", fontsize=7.5, color="#666")

    ax_ladder.set_yticks(y_pos)
    ax_ladder.set_yticklabels(regions_short, fontsize=9)
    for lbl, r in zip(ax_ladder.get_yticklabels(), reg["region"]):
        if r == "London":
            lbl.set_color(PALETTE["London"])
            lbl.set_fontweight("bold")

    ax_ladder.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax_ladder.set_xlabel("Average 2-bedroom monthly rent (£)", fontsize=9)
    ax_ladder.spines["top"].set_visible(False)
    ax_ladder.spines["right"].set_visible(False)
    ax_ladder.tick_params(labelsize=8)
    ax_ladder.legend(fontsize=8.5, loc="lower right", framealpha=0.9, edgecolor="#ddd")

    # Key callout: London AR vs North East AR
    lon = reg[reg["region"] == "London"].iloc[0]
    ne  = reg[reg["region"] == "North East"].iloc[0]
    ax_ladder.annotate(
        f"London AR: £{lon['avg_ar']:,.0f}/month\n({lon['ar_pct_mkt']:.0f}% of market)\n"
        f"vs North East AR: £{ne['avg_ar']:,.0f}/month\n({ne['ar_pct_mkt']:.0f}% of market)",
        xy=(lon["avg_ar"], 0), xytext=(lon["avg_ar"] - 420, 0 + 1.6),
        fontsize=8, color=PALETTE["London"],
        arrowprops=dict(arrowstyle="->", color=PALETTE["London"], lw=0.8),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=PALETTE["London"],
                  alpha=0.92, linewidth=0.8),
    )

    ax_ladder.set_title(
        "The rent ladder by region (2-bedroom, 2024–25)\n"
        "Affordable Rent tracks the market; Social Rent barely rises from North to South",
        fontsize=9.5, color="#333", pad=5,
    )

    # ── Panel 2: % of market rent by region ───────────────────────────────
    y2 = np.arange(len(reg))
    h2 = 0.32

    ax_pct.barh(y2 + h2 / 2, reg["ar_pct_mkt"],
                color=PALETTE["ar"], height=h2, alpha=0.88, label="Affordable Rent")
    ax_pct.barh(y2 - h2 / 2, reg["sr_pct_mkt"],
                color=PALETTE["sr"], height=h2, alpha=0.88, label="Social Rent")

    # 100% market reference
    ax_pct.axvline(100, color="#aaa", linewidth=1, linestyle=":", alpha=0.8)
    ax_pct.axvline(80,  color=PALETTE["ar"], linewidth=0.8, linestyle="--",
                   alpha=0.5, label="80% target")

    ax_pct.set_yticks(y2)
    ax_pct.set_yticklabels(regions_short, fontsize=8.5)
    for lbl, r in zip(ax_pct.get_yticklabels(), reg["region"]):
        if r == "London":
            lbl.set_color(PALETTE["London"])
            lbl.set_fontweight("bold")

    ax_pct.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax_pct.set_xlabel("Rent as % of local market rent", fontsize=9)
    ax_pct.spines["top"].set_visible(False)
    ax_pct.spines["right"].set_visible(False)
    ax_pct.tick_params(labelsize=8)
    ax_pct.legend(fontsize=8, loc="lower right", framealpha=0.9, edgecolor="#ddd")

    # Annotations on key data points
    for i, row in reg.iterrows():
        ax_pct.text(row["ar_pct_mkt"] + 0.8, i + h2 / 2,
                    f'{row["ar_pct_mkt"]:.0f}%',
                    va="center", fontsize=7, color=PALETTE["ar"])
        ax_pct.text(row["sr_pct_mkt"] + 0.8, i - h2 / 2,
                    f'{row["sr_pct_mkt"]:.0f}%',
                    va="center", fontsize=7, color=PALETTE["sr"])

    ax_pct.set_title(
        "Rent as % of local market, by region\n"
        "Social Rent: 33% in London → 75% in North East\n"
        "Affordable Rent: roughly 58–95% everywhere — still tracks the market",
        fontsize=9, color="#333", pad=5,
    )

    # ── Panel 3: LA-level distribution of AR vs market ────────────────────
    # Scatter: x = market rent, y = AR rent; colour by region (London red)
    la_london = la_level[la_level["region"] == "London"]
    la_other  = la_level[la_level["region"] != "London"]

    ax_dist.scatter(
        la_other["market_rent_monthly"], la_other["affordable_rent_monthly"],
        s=18, alpha=0.55, color=PALETTE["other"], zorder=2, label="Other regions",
    )
    ax_dist.scatter(
        la_london["market_rent_monthly"], la_london["affordable_rent_monthly"],
        s=25, alpha=0.75, color=PALETTE["London"], zorder=3, label="London",
    )

    # y = x reference (AR = market)
    max_v = max(la_level["market_rent_monthly"].max(),
                la_level["affordable_rent_monthly"].max()) * 1.05
    ax_dist.plot([0, max_v], [0, max_v], color="#aaa", lw=1, linestyle=":",
                 zorder=1, label="AR = market")
    # y = 0.8x reference
    ax_dist.plot([0, max_v], [0, max_v * 0.8], color=PALETTE["ar"], lw=1,
                 linestyle="--", alpha=0.6, zorder=1, label="80% of market")

    # Highlight LAs where AR > market (dots above diagonal)
    la_over = la_level[la_level["ar_over_market"]]
    ax_dist.scatter(
        la_over["market_rent_monthly"], la_over["affordable_rent_monthly"],
        s=45, color=PALETTE["negative"], zorder=4,
        marker="^", label=f"AR > market ({len(la_over)} LAs)",
    )

    ax_dist.set_xlabel("Market rent (£/month, 2-bed)", fontsize=9)
    ax_dist.set_ylabel("Affordable Rent (£/month, 2-bed)", fontsize=9)
    ax_dist.set_xlim(0, max_v)
    ax_dist.set_ylim(0, max_v)
    ax_dist.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax_dist.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax_dist.tick_params(labelsize=8)
    ax_dist.spines["top"].set_visible(False)
    ax_dist.spines["right"].set_visible(False)
    ax_dist.legend(fontsize=7.5, loc="upper left", framealpha=0.9, edgecolor="#ddd")
    ax_dist.set_title(
        "Affordable Rent vs local market rent (LA level, 2-bed)\n"
        f"{len(la_over)} LAs where AR exceeds market rent entirely",
        fontsize=9, color="#333", pad=5,
    )

    # ── Figure title & footnote ────────────────────────────────────────────
    fig.suptitle(
        '"Affordable Rent" at 80% of market replicates geographic inequality —\n'
        "it offers a flat discount, not a correction for where rents are highest",
        fontsize=11.5, fontweight="bold", y=0.97, color="#111",
    )
    fig.text(
        0.5, 0.01,
        "Source: ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25. 2-bedroom units. "
        "Averages weighted by unit counts. AR > market occurs in thin private rental markets.",
        ha="center", fontsize=7, color="#777",
    )

    fig.savefig(out_path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def run():
    out_path = PROCESSED / "fig_affordable_rent.png"
    plot_affordable_rent(out_path)


if __name__ == "__main__":
    run()
