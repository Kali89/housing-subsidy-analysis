"""
Twitter-optimised standalone charts (1200×675px, 16:9).
Each chart is designed to make one argument on its own, without supporting text.

Produces data/processed/tweet_01_invisible_transfer.png  through  tweet_06_lottery.png
Run standalone:  python -m src.tweet_charts
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .constants import PROCESSED

RAW = PROCESSED.parent / "raw"

# Shared style
BLUE   = "#2c6fad"
RED    = "#c0392b"
ORANGE = "#e07b39"
GREY   = "#888888"
LIGHT  = "#f0f4f8"
WHITE  = "#ffffff"

FIGSIZE = (12, 6.75)   # 1200×675 at 100dpi
DPI = 100


def _save(fig: plt.Figure, name: str) -> None:
    out = PROCESSED / f"tweet_{name}.png"
    fig.savefig(out, bbox_inches="tight", dpi=DPI, facecolor=WHITE)
    plt.close(fig)
    print(f"  Saved: {out}")


def _source(*lines: str) -> str:
    return "  |  ".join(lines)


# ── Chart 1: The invisible transfer ───────────────────────────────────────────

def chart_invisible_transfer(summary: pd.DataFrame) -> None:
    """Regional bar: 47% of a £21bn subsidy goes to London."""
    reg = (
        summary.dropna(subset=["region", "total_annual_subsidy_social"])
        .groupby("region")["total_annual_subsidy_social"].sum()
        .sort_values() / 1e9
    )

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)

    colors = [RED if r == "London" else BLUE for r in reg.index]
    bars = ax.barh(range(len(reg)), reg.values, color=colors, height=0.65,
                   edgecolor="white", linewidth=0.5)

    for bar, val, region in zip(bars, reg.values, reg.index):
        x = bar.get_width()
        ax.text(x + 0.08, bar.get_y() + bar.get_height() / 2,
                f"£{val:.1f}bn",
                va="center", ha="left", fontsize=12,
                color=RED if region == "London" else "#333",
                fontweight="bold" if region == "London" else "normal")

    ax.set_yticks(range(len(reg)))
    ax.set_yticklabels(reg.index, fontsize=12)
    for lbl, r in zip(ax.get_yticklabels(), reg.index):
        if r == "London":
            lbl.set_color(RED)
            lbl.set_fontweight("bold")

    ax.set_xlabel("Annual implicit subsidy (£bn)", fontsize=11, color="#444")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:.0f}bn"))
    ax.tick_params(axis="x", labelsize=10, colors="#555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", left=False)

    total = reg.sum()
    london_pct = reg["London"] / total * 100

    ax.set_title(
        f"England's social housing delivers a £{total:.0f}bn annual subsidy.\n"
        f"Nearly half ({london_pct:.0f}%) goes to London — which has only 19% of the stock.",
        fontsize=15, fontweight="bold", color="#111", pad=14, loc="left",
    )
    fig.text(
        0.01, 0.01,
        "Source: ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25 × MHCLG Table 100. "
        "Subsidy = market rent − social rent, summed across all social units.",
        fontsize=8, color="#999",
    )
    _save(fig, "01_invisible_transfer")


# ── Chart 2: Social rent as % of market rent by region ────────────────────────

def chart_rent_pct(long: pd.DataFrame) -> None:
    """SR compresses geography; AR doesn't."""
    REGION_ORDER = [
        "North East", "Yorkshire and The Humber", "North West",
        "East Midlands", "West Midlands", "South West",
        "East of England", "South East", "London",
    ]
    two = long[long["bedrooms"] == "2_bed"].dropna(
        subset=["market_rent_monthly", "social_rent_monthly",
                "affordable_rent_monthly", "region"]
    )

    def wavg(g, col, wt):
        w = g[wt].fillna(1).clip(lower=1)
        return np.average(g[col], weights=w)

    reg = (
        two.groupby("region")
        .apply(lambda g: pd.Series({
            "sr_pct": wavg(g, "social_rent_monthly",   "social_units") /
                      wavg(g, "market_rent_monthly",   "social_units") * 100,
            "ar_pct": wavg(g, "affordable_rent_monthly", "affordable_units") /
                      wavg(g, "market_rent_monthly",   "social_units") * 100,
        }), include_groups=False)
        .reset_index()
    )
    reg = reg[reg["region"].isin(REGION_ORDER)].copy()
    reg["order"] = reg["region"].map({r: i for i, r in enumerate(REGION_ORDER)})
    reg = reg.sort_values("order")

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)

    y = np.arange(len(reg))
    h = 0.35

    ax.barh(y + h / 2, reg["ar_pct"], height=h,
            color=ORANGE, alpha=0.88, label="Affordable Rent (≤80% of market)")
    ax.barh(y - h / 2, reg["sr_pct"], height=h,
            color=BLUE, alpha=0.88, label="Social Rent")

    ax.axvline(100, color="#aaa", lw=1, linestyle=":", zorder=0, label="Market rent (100%)")
    ax.axvline(80,  color=ORANGE, lw=0.8, linestyle="--", alpha=0.4, zorder=0)

    for i, row in reg.iterrows():
        idx = list(reg.index).index(i)
        ax.text(row["ar_pct"] + 0.8, idx + h / 2,
                f'{row["ar_pct"]:.0f}%', va="center", fontsize=9, color=ORANGE)
        ax.text(row["sr_pct"] + 0.8, idx - h / 2,
                f'{row["sr_pct"]:.0f}%', va="center", fontsize=9, color=BLUE)

    regions_short = [r.replace("Yorkshire and The Humber", "Yorks & Humber")
                     for r in reg["region"]]
    ax.set_yticks(y)
    ax.set_yticklabels(regions_short, fontsize=11)
    for lbl, r in zip(ax.get_yticklabels(), reg["region"]):
        if r == "London":
            lbl.set_color(RED)
            lbl.set_fontweight("bold")

    ax.set_xlabel("Rent as % of local market", fontsize=11, color="#444")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlim(0, 115)
    ax.tick_params(labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", left=False)
    ax.legend(fontsize=10, loc="lower right", framealpha=0.9, edgecolor="#ddd")

    ax.set_title(
        "Social Rent: 33p in the £ in London. 75p in the North East.\n"
        "Affordable Rent offers the same 20% discount everywhere — it just replicates the market.",
        fontsize=14, fontweight="bold", color="#111", pad=14, loc="left",
    )
    fig.text(
        0.01, 0.01,
        "Source: ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25. 2-bedroom units, unit-weighted averages.",
        fontsize=8, color="#999",
    )
    _save(fig, "02_rent_pct_market")


# ── Chart 3: Employer wage subsidy ────────────────────────────────────────────

def chart_employer_subsidy(summary: pd.DataFrame, long: pd.DataFrame) -> None:
    """Total annual employer labour saving by region."""
    GROSS_UP   = 1 / (1 - 0.28)
    REGION_ORDER = [
        "North East", "Yorkshire and The Humber", "East Midlands",
        "North West", "West Midlands", "South West",
        "East of England", "South East", "London",
    ]

    units_by_la = (
        long.dropna(subset=["social_units"])
        .groupby("la_code")["social_units"].sum()
        .rename("total_social_units_rsh")
    )
    df = summary.merge(units_by_la, on="la_code", how="left")
    df["units"] = df["total_social_units_rsh"].fillna(df["total_social_stock"])
    df = df.dropna(subset=["subsidy_social_wtavg_annual", "units", "region"])

    reg = (
        df.groupby("region")
        .apply(lambda g: pd.Series({
            "employer_saving_bn": (g["subsidy_social_wtavg_annual"] * g["units"]).sum()
                                  * GROSS_UP / 1e9,
        }), include_groups=False)
        .reset_index()
    )
    reg = reg[reg["region"].isin(REGION_ORDER)].copy()
    reg = reg.sort_values("employer_saving_bn")   # ascending so London is at top

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)

    colors = [RED if r == "London" else BLUE for r in reg["region"]]
    bars = ax.barh(range(len(reg)), reg["employer_saving_bn"],
                   color=colors, height=0.62,
                   edgecolor="white", linewidth=0.4)

    for bar, val, region in zip(bars, reg["employer_saving_bn"], reg["region"]):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                f"£{val:.1f}bn",
                va="center", ha="left", fontsize=12,
                color=RED if region == "London" else "#333",
                fontweight="bold" if region == "London" else "normal")

    regions_short = [r.replace("Yorkshire and The Humber", "Yorks & Humber")
                     for r in reg["region"]]
    ax.set_yticks(range(len(reg)))
    ax.set_yticklabels(regions_short, fontsize=11)
    for lbl, r in zip(ax.get_yticklabels(), reg["region"]):
        if r == "London":
            lbl.set_color(RED)
            lbl.set_fontweight("bold")

    ax.set_xlabel("Equivalent annual gross wage saving for employers (£bn)", fontsize=10, color="#444")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:.0f}bn"))
    ax.set_xlim(0, reg["employer_saving_bn"].max() * 1.22)
    ax.tick_params(labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", left=False)

    lon_val = reg.loc[reg["region"] == "London", "employer_saving_bn"].iloc[0]
    ax.set_title(
        f"Social housing is a £{lon_val:.1f}bn/yr wage subsidy to London employers.\n"
        "Workers live at below-market rents; their employers don't have to pay market-reflective wages.",
        fontsize=14, fontweight="bold", color="#111", pad=14, loc="left",
    )
    fig.text(
        0.01, 0.01,
        "Source: ONS PRMS × RSH SDR 2024–25 × MHCLG Table 100. "
        "Gross-up at 1.39× (28% effective marginal tax + NI) converts net rent gap to gross wage equivalent.",
        fontsize=8, color="#999",
    )
    _save(fig, "03_employer_subsidy")


# ── Chart 4: Social Rent completions collapse ──────────────────────────────────

def chart_supply_collapse() -> None:
    """Stacked area: SR completions 1991–2025."""
    df = pd.read_csv(RAW / "ahs_open_data.csv", low_memory=False)
    df = df[df["Completions"] == "Completion"].copy()
    df["year_start"] = df["Year"].str[:4].astype(int)

    tenures = ["Social Rent", "Affordable Rent", "London Affordable Rent"]
    annual = (
        df[df["Tenure"].isin(tenures)]
        .groupby(["year_start", "Tenure"])["Units"]
        .sum().unstack(fill_value=0).reset_index().sort_values("year_start")
    )
    for t in tenures:
        if t not in annual.columns:
            annual[t] = 0

    x  = annual["year_start"].values
    sr  = annual["Social Rent"].values
    ar  = annual["Affordable Rent"].values
    lar = annual["London Affordable Rent"].values

    peak_sr  = sr.max()
    peak_yr  = x[sr.argmax()]
    cur_sr   = annual.loc[annual["year_start"] == 2024, "Social Rent"].values[0]
    trough_sr = sr.min()
    trough_yr = x[sr.argmin()]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)

    ax.stackplot(x, sr, ar, lar,
                 labels=["Social Rent", "Affordable Rent", "London Affordable Rent"],
                 colors=[BLUE, ORANGE, "#6aafe6"], alpha=0.85)

    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    ax.set_ylabel("Completions per year", fontsize=11, color="#444")
    ax.tick_params(labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Peak annotation — place to the right so it clears the title
    ax.annotate(
        f"Peak: {peak_sr/1000:.0f}k/yr ({peak_yr})",
        xy=(peak_yr, peak_sr), xytext=(peak_yr + 6, peak_sr - 8000),
        fontsize=9, color=BLUE, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9),
        bbox=dict(boxstyle="round,pad=0.25", fc=WHITE, ec=BLUE, alpha=0.9, lw=0.8),
    )
    # 2012 policy line
    ax.axvline(2011, color=GREY, lw=1, linestyle=":", alpha=0.7)
    ax.text(2011.3, ax.get_ylim()[1] * 0.82,
            "2011–12:\nAffordable Rent\nintroduced",
            fontsize=8, color="#666", va="top")
    # Current level
    ax.annotate(
        f"{cur_sr/1000:.0f}k/yr\n(2024–25)\n{cur_sr/peak_sr*100:.0f}% of peak",
        xy=(2024, cur_sr), xytext=(2020, cur_sr + 14000),
        fontsize=9, color=BLUE, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9),
        bbox=dict(boxstyle="round,pad=0.25", fc=WHITE, ec=BLUE, alpha=0.9, lw=0.8),
    )

    ax.legend(fontsize=10, loc="upper right", framealpha=0.9, edgecolor="#ddd")
    ax.set_title(
        f"England built {peak_sr/1000:.0f},000 Social Rent homes a year in the early 1990s. "
        f"Now: {cur_sr/1000:.0f},000.\n"
        "The replacement tenure (Affordable Rent) is cheaper to build but costs tenants far more.",
        fontsize=13.5, fontweight="bold", color="#111", pad=14, loc="left",
    )
    fig.text(
        0.01, 0.01,
        "Source: MHCLG Affordable Housing Supply statistics 1991–2025.",
        fontsize=8, color="#999",
    )
    _save(fig, "04_supply_collapse")


# ── Chart 5: "Affordable" Rent in London vs market rent in Northern cities ─────

def chart_ar_vs_north(long: pd.DataFrame) -> None:
    """The single most striking comparison: inner London AR > Northern market."""
    two = long[long["bedrooms"] == "2_bed"].dropna(
        subset=["market_rent_monthly", "social_rent_monthly", "affordable_rent_monthly"]
    )

    comparisons = [
        # (label, rent, type, is_london)
        ("Islington\nAffordable Rent",    two.loc[two["la_name"].str.contains("Islington"),   "affordable_rent_monthly"].mean(), "ar",     True),
        ("Hackney\nAffordable Rent",       two.loc[two["la_name"].str.contains("Hackney"),    "affordable_rent_monthly"].mean(), "ar",     True),
        ("Southwark\nAffordable Rent",     two.loc[two["la_name"].str.contains("Southwark"),  "affordable_rent_monthly"].mean(), "ar",     True),
        ("Manchester\nmarket rent",        two.loc[two["la_name"].str.contains("Manchester"), "market_rent_monthly"].mean(),     "market", False),
        ("Leeds\nmarket rent",             two.loc[two["la_name"].str.contains("Leeds"),      "market_rent_monthly"].mean(),     "market", False),
        ("Birmingham\nmarket rent",        two.loc[two["la_name"].str.contains("Birmingham"), "market_rent_monthly"].mean(),     "market", False),
        ("Liverpool\nmarket rent",         two.loc[two["la_name"].str.contains("Liverpool"),  "market_rent_monthly"].mean(),     "market", False),
        ("Sheffield\nmarket rent",         two.loc[two["la_name"].str.contains("Sheffield"),  "market_rent_monthly"].mean(),     "market", False),
        ("Newcastle\nmarket rent",         two.loc[two["la_name"].str.contains("Newcastle"),  "market_rent_monthly"].mean(),     "market", False),
    ]
    comparisons = [(l, v, t, il) for l, v, t, il in comparisons if not np.isnan(v)]
    comparisons.sort(key=lambda x: -x[1])

    labels = [c[0] for c in comparisons]
    values = [c[1] for c in comparisons]
    types  = [c[2] for c in comparisons]
    is_lon = [c[3] for c in comparisons]

    colors = []
    for t, il in zip(types, is_lon):
        if t == "ar" and il:
            colors.append(RED)
        elif t == "market":
            colors.append("#5b8db8")
        else:
            colors.append(ORANGE)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)

    y = np.arange(len(comparisons))
    bars = ax.barh(y, values, color=colors, height=0.62,
                   edgecolor="white", linewidth=0.4)

    for bar, val, t, il in zip(bars, values, types, is_lon):
        label_color = RED if (t == "ar" and il) else "#444"
        ax.text(bar.get_width() + 15, bar.get_y() + bar.get_height() / 2,
                f"£{val:,.0f}/mo",
                va="center", ha="left", fontsize=12,
                color=label_color,
                fontweight="bold" if (t == "ar" and il) else "normal")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11)
    for lbl, (_, _, t, il) in zip(ax.get_yticklabels(), comparisons):
        if t == "ar" and il:
            lbl.set_color(RED)
            lbl.set_fontweight("bold")

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax.set_xlabel("2-bedroom monthly rent (£)", fontsize=11, color="#444")
    ax.set_xlim(0, max(values) * 1.30)   # extra room for value labels
    ax.tick_params(labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", left=False)

    # Legend patches — top left where there's space
    patches = [
        mpatches.Patch(color=RED,       label='London "Affordable Rent"'),
        mpatches.Patch(color="#5b8db8", label="Northern city market rent"),
    ]
    ax.legend(handles=patches, fontsize=10, loc="upper left",
              framealpha=0.9, edgecolor="#ddd")

    ax.set_title(
        'A government-subsidised "Affordable Rent" flat in inner London\n'
        "costs more than a market-rate flat in any major Northern city.",
        fontsize=14, fontweight="bold", color="#111", pad=14, loc="left",
    )
    fig.text(
        0.01, 0.01,
        "Source: ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25. 2-bedroom units. "
        "Affordable Rent ≤80% of local market, set by RSH regulation.",
        fontsize=8, color="#999",
    )
    _save(fig, "05_ar_vs_north")


# ── Chart 6: The 44:1 subsidy lottery ─────────────────────────────────────────

def chart_subsidy_lottery(summary: pd.DataFrame) -> None:
    """Strip chart: per-unit subsidy across all LAs, top/bottom highlighted."""
    df = summary.dropna(subset=["subsidy_social_wtavg_annual", "region"]).copy()
    df["is_london"] = df["region"] == "London"
    df_s = df.sort_values("subsidy_social_wtavg_annual")

    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)

    y_other  = df_s[~df_s["is_london"]]["subsidy_social_wtavg_annual"].values
    y_london = df_s[df_s["is_london"]]["subsidy_social_wtavg_annual"].values

    x_other  = np.random.default_rng(42).uniform(0.6, 1.4, len(y_other))
    x_london = np.random.default_rng(42).uniform(0.6, 1.4, len(y_london))

    ax.scatter(y_other,  x_other,  s=18, alpha=0.45, color=BLUE,
               zorder=2, label="Other regions")
    ax.scatter(y_london, x_london, s=30, alpha=0.80, color=RED,
               zorder=3, label="London")

    # Annotate top and bottom
    top_row = df_s.nlargest(1, "subsidy_social_wtavg_annual").iloc[0]
    bot_row = df_s.nsmallest(1, "subsidy_social_wtavg_annual").iloc[0]

    for row, side in [(top_row, "top"), (bot_row, "bot")]:
        xv = row["subsidy_social_wtavg_annual"]
        yv = 1.0
        color = RED if row["is_london"] else BLUE
        yt = 1.55 if side == "top" else 0.45
        ax.annotate(
            f"{row['la_name']}\n£{xv:,.0f}/unit/yr",
            xy=(xv, yv), xytext=(xv, yt),
            fontsize=9.5, color=color, fontweight="bold", ha="center",
            arrowprops=dict(arrowstyle="->", color=color, lw=0.9),
            bbox=dict(boxstyle="round,pad=0.3", fc=WHITE, ec=color,
                      alpha=0.95, lw=0.8),
        )

    ratio = top_row["subsidy_social_wtavg_annual"] / bot_row["subsidy_social_wtavg_annual"]

    ax.set_xlabel("Annual implicit subsidy per social unit (£/yr)", fontsize=11, color="#444")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax.tick_params(axis="x", labelsize=10)
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_ylim(0, 2)
    ax.legend(fontsize=10, loc="upper left", framealpha=0.9, edgecolor="#ddd")

    ax.set_title(
        f"The same national system. A {ratio:.0f}:1 difference in what each tenant receives.\n"
        f"K&C: £{top_row['subsidy_social_wtavg_annual']:,.0f}/yr. "
        f"Redcar: £{bot_row['subsidy_social_wtavg_annual']:,.0f}/yr. "
        "Every dot is a local authority.",
        fontsize=13.5, fontweight="bold", color="#111", pad=14, loc="left",
    )
    fig.text(
        0.01, 0.01,
        "Source: ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25. "
        "290 English local authorities. Subsidy = (market − social rent) × stock, annualised per unit.",
        fontsize=8, color="#999",
    )
    _save(fig, "06_subsidy_lottery")


# ── Runner ─────────────────────────────────────────────────────────────────────

def run() -> None:
    summary = pd.read_csv(PROCESSED / "subsidy_summary_by_la.csv")
    long    = pd.read_csv(PROCESSED / "subsidy_by_la_bedroom.csv")

    chart_invisible_transfer(summary)
    chart_rent_pct(long)
    chart_employer_subsidy(summary, long)
    chart_supply_collapse()
    chart_ar_vs_north(long)
    chart_subsidy_lottery(summary)


if __name__ == "__main__":
    run()
