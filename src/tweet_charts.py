"""
Twitter-optimised standalone charts (1200×675 px, 16:9).
Each chart makes one argument on its own.

Run:  python -m src.tweet_charts
"""

from pathlib import Path

import matplotlib.font_manager as _fm
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .constants import PROCESSED

RAW = PROCESSED.parent / "raw"

FIGSIZE = (12, 6.75)
DPI = 100

# ── Palette ────────────────────────────────────────────────────────────────────

C = {
    "bg":      "#FAF9F7",   # warm near-white — all backgrounds
    "london":  "#B52D1E",   # deep crimson — London / high subsidy
    "north":   "#1A5E99",   # rich steel blue — Northern regions
    "mid":     "#7AAEC1",   # muted teal-blue — other regions
    "grey":    "#B0BAC4",   # neutral grey
    "text":    "#1C1C1E",   # near-black body text
    "sub":     "#5A6270",   # axis labels, secondary text
    "source":  "#ABABAB",   # footnote text
    "grid":    "#E0DAD4",   # warm light gridlines
    "divider": "#CCC6BC",   # stronger rule lines
    "sr":      "#1A5E99",   # Social Rent fill
    "ar":      "#C87722",   # Affordable Rent fill
    "lar":     "#7AAEC1",   # London Affordable Rent fill
    "gap_pos": "#C87722",   # overbuilding (positive gap) — amber
    "gap_neg": "#1A5E99",   # underbuilding (negative gap) — blue
}

NORTH = {"North East", "North West", "Yorkshire and The Humber"}

REGIONAL_POP = {
    "North East":               2_647_000,
    "North West":               7_417_000,
    "Yorkshire and The Humber": 5_480_000,
    "East Midlands":            4_934_000,
    "West Midlands":            5_902_000,
    "East of England":          6_335_000,
    "London":                   8_796_000,
    "South East":               9_180_000,
    "South West":               5_701_000,
}

# ── Font ───────────────────────────────────────────────────────────────────────

def _setup_fonts() -> str:
    """Download Barlow from Google Fonts if not cached; fall back to Avenir Next."""
    fonts_dir = PROCESSED.parent / "fonts"
    fonts_dir.mkdir(exist_ok=True)

    weights = {
        "Barlow-Regular.ttf":  "https://github.com/google/fonts/raw/main/ofl/barlow/Barlow-Regular.ttf",
        "Barlow-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/barlow/Barlow-SemiBold.ttf",
        "Barlow-Bold.ttf":     "https://github.com/google/fonts/raw/main/ofl/barlow/Barlow-Bold.ttf",
    }
    try:
        import requests
        for fname, url in weights.items():
            dest = fonts_dir / fname
            if not dest.exists():
                print(f"  Downloading font: {fname}")
                r = requests.get(url, timeout=20)
                r.raise_for_status()
                dest.write_bytes(r.content)
            _fm.fontManager.addfont(str(dest))
        return "Barlow"
    except Exception as exc:
        print(f"  Font: {exc} — using Avenir Next")
        return "Avenir Next"


FONT = _setup_fonts()

plt.rcParams.update({
    "font.family":        FONT,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   False,
    "axes.spines.bottom": True,
    "xtick.color":        C["sub"],
    "ytick.color":        C["text"],
    "xtick.labelsize":    10,
    "ytick.labelsize":    10.5,
    "axes.labelsize":     10.5,
    "axes.labelcolor":    C["sub"],
    "text.color":         C["text"],
    "legend.framealpha":  0.97,
    "legend.edgecolor":   C["divider"],
    "legend.fontsize":    9.5,
})

# ── Shared helpers ─────────────────────────────────────────────────────────────

def _region_color(r: str) -> str:
    if r == "London": return C["london"]
    if r in NORTH:    return C["north"]
    return C["mid"]

def _short(r: str) -> str:
    return r.replace("Yorkshire and The Humber", "Yorks & Humber")

def _save(fig: plt.Figure, name: str) -> None:
    out = PROCESSED / f"tweet_{name}.png"
    fig.savefig(out, bbox_inches="tight", dpi=DPI, facecolor=C["bg"])
    plt.close(fig)
    print(f"  Saved: {out}")

def _footnote(fig: plt.Figure, source: str, note: str = None) -> None:
    if note:
        fig.text(0.015, 0.040, note, fontsize=7.5, color=C["sub"],
                 style="italic", ha="left")
    fig.text(0.015, 0.012, f"Source: {source}", fontsize=8,
             color=C["source"], ha="left")

def _ax_base(ax) -> None:
    """Standard axis chrome for all charts."""
    ax.set_facecolor(C["bg"])
    ax.tick_params(axis="y", left=False)
    ax.spines["bottom"].set_color(C["divider"])
    ax.grid(axis="x", color=C["grid"], linewidth=0.65, zorder=0)
    ax.set_axisbelow(True)

def _ytick_style(ax, regions) -> None:
    for lbl, r in zip(ax.get_yticklabels(), regions):
        lbl.set_color(_region_color(r))
        if r in {"London", "North East", "North West",
                 "Yorkshire and The Humber"}:
            lbl.set_fontweight("bold")

def _title(ax, main: str, sub: str = "") -> None:
    full = f"{main}\n{sub}" if sub else main
    ax.set_title(full, fontsize=14.5, fontweight="bold", color=C["text"],
                 pad=14, loc="left", linespacing=1.45)

def _annotate(ax, text, xy, xytext, color, ha="center") -> None:
    ax.annotate(
        text, xy=xy, xytext=xytext,
        fontsize=9, color=color, fontweight="bold", ha=ha,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=0.9,
                        connectionstyle="arc3,rad=0.0"),
        bbox=dict(boxstyle="round,pad=0.32", fc=C["bg"], ec=color,
                  alpha=0.97, lw=0.9),
    )

def _bar_labels(ax, bars, values, fmt, region_list) -> None:
    """Add right-aligned value labels to horizontal bars."""
    xlim = ax.get_xlim()
    pad = (xlim[1] - xlim[0]) * 0.013
    for bar, val, region in zip(bars, values, region_list):
        ax.text(
            bar.get_width() + pad,
            bar.get_y() + bar.get_height() / 2,
            fmt(val), va="center", ha="left", fontsize=11,
            color=_region_color(region),
            fontweight="bold" if region in {"London", "North East"} else "normal",
        )


# ── Chart 1: The invisible transfer ───────────────────────────────────────────

def chart_invisible_transfer(summary: pd.DataFrame) -> None:
    reg = (
        summary.dropna(subset=["region", "total_annual_subsidy_social"])
        .groupby("region")["total_annual_subsidy_social"].sum()
        .sort_values() / 1e9
    )

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.20, "right": 0.86,
                                        "top": 0.87, "bottom": 0.12})
    fig.patch.set_facecolor(C["bg"])
    _ax_base(ax)

    colors = [_region_color(r) for r in reg.index]
    bars = ax.barh(range(len(reg)), reg.values, color=colors,
                   height=0.62, edgecolor=C["bg"], linewidth=0.8)

    ax.set_xlim(0, reg.max() * 1.28)
    _bar_labels(ax, bars, reg.values, lambda v: f"£{v:.1f}bn", list(reg.index))

    # Pct labels inside bars for London
    total = reg.sum()
    lon_i = list(reg.index).index("London")
    ax.text(reg["London"] / 2, lon_i,
            f"{reg['London']/total*100:.0f}% of total",
            va="center", ha="center", fontsize=9.5, color="white",
            fontweight="bold")

    ax.set_yticks(range(len(reg)))
    ax.set_yticklabels([_short(r) for r in reg.index], fontsize=11)
    _ytick_style(ax, list(reg.index))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:.0f}bn"))
    ax.set_xlabel("Annual implicit subsidy (£bn)", color=C["sub"])

    _title(ax,
        f"England's social housing hides a £{total:.0f}bn annual subsidy.",
        f"Nearly half ({reg['London']/total*100:.0f}%) goes to London — "
        f"which holds only 19% of the stock.")
    _footnote(fig,
        "ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25 × MHCLG Table 100. "
        "Subsidy = market rent − social rent, summed across all social units.")
    _save(fig, "01_invisible_transfer")


# ── Chart 2: Per-unit subsidy by region ───────────────────────────────────────

def chart_per_unit_subsidy(summary: pd.DataFrame, long: pd.DataFrame) -> None:
    units_by_la = (
        long.dropna(subset=["social_units"])
        .groupby("la_code")["social_units"].sum()
        .rename("rsh_units")
    )
    df = summary.merge(units_by_la, on="la_code", how="left")
    df["units"] = df["rsh_units"].fillna(df["total_social_stock"])
    df = df.dropna(subset=["subsidy_social_wtavg_annual", "units", "region"])

    reg = (
        df.groupby("region")
        .apply(lambda g: pd.Series({
            "per_unit": (g["subsidy_social_wtavg_annual"] * g["units"]).sum()
                        / g["units"].sum(),
        }), include_groups=False)
        .reset_index()
        .sort_values("per_unit")
    )

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.20, "right": 0.84,
                                        "top": 0.87, "bottom": 0.12})
    fig.patch.set_facecolor(C["bg"])
    _ax_base(ax)

    colors = [_region_color(r) for r in reg["region"]]
    bars = ax.barh(range(len(reg)), reg["per_unit"] / 1000,
                   color=colors, height=0.62,
                   edgecolor=C["bg"], linewidth=0.8)

    ax.set_xlim(0, reg["per_unit"].max() / 1000 * 1.26)
    _bar_labels(ax, bars, reg["per_unit"],
                lambda v: f"£{v:,.0f}", list(reg["region"]))

    ax.set_yticks(range(len(reg)))
    ax.set_yticklabels([_short(r) for r in reg["region"]], fontsize=11)
    _ytick_style(ax, list(reg["region"]))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:.0f}k"))
    ax.set_xlabel("Average annual implicit subsidy per social home")

    lon = reg.loc[reg["region"] == "London", "per_unit"].iloc[0]
    ne  = reg.loc[reg["region"] == "North East", "per_unit"].iloc[0]
    _title(ax,
        f"A social home in London receives £{lon:,.0f}/yr in hidden subsidy.",
        f"In the North East: £{ne:,.0f}. Same national system. {lon/ne:.0f}× difference.")
    _footnote(fig,
        "ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25 × MHCLG Table 100. "
        "Stock-weighted average subsidy per social unit, annualised.")
    _save(fig, "02_per_unit_subsidy")


# ── Chart 3: Employer wage subsidy ────────────────────────────────────────────

def chart_employer_subsidy(summary: pd.DataFrame, long: pd.DataFrame) -> None:
    GROSS_UP = 1 / (1 - 0.28)

    units_by_la = (
        long.dropna(subset=["social_units"])
        .groupby("la_code")["social_units"].sum()
        .rename("rsh_units")
    )
    df = summary.merge(units_by_la, on="la_code", how="left")
    df["units"] = df["rsh_units"].fillna(df["total_social_stock"])
    df = df.dropna(subset=["subsidy_social_wtavg_annual", "units", "region"])

    reg = (
        df.groupby("region")
        .apply(lambda g: pd.Series({
            "saving_bn": (g["subsidy_social_wtavg_annual"] * g["units"]).sum()
                         * GROSS_UP / 1e9,
        }), include_groups=False)
        .reset_index()
    )
    reg = reg[reg["region"].isin(REGIONAL_POP)].sort_values("saving_bn")

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.20, "right": 0.84,
                                        "top": 0.87, "bottom": 0.12})
    fig.patch.set_facecolor(C["bg"])
    _ax_base(ax)

    colors = [_region_color(r) for r in reg["region"]]
    bars = ax.barh(range(len(reg)), reg["saving_bn"],
                   color=colors, height=0.62,
                   edgecolor=C["bg"], linewidth=0.8)

    ax.set_xlim(0, reg["saving_bn"].max() * 1.26)
    _bar_labels(ax, bars, reg["saving_bn"],
                lambda v: f"£{v:.1f}bn", list(reg["region"]))

    ax.set_yticks(range(len(reg)))
    ax.set_yticklabels([_short(r) for r in reg["region"]], fontsize=11)
    _ytick_style(ax, list(reg["region"]))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"£{v:.0f}bn"))
    ax.set_xlabel("Equivalent annual gross wage saving for employers (£bn)")

    lon_v = reg.loc[reg["region"] == "London", "saving_bn"].iloc[0]
    _title(ax,
        f"Social housing is a £{lon_v:.1f}bn/yr wage subsidy to London employers.",
        "Workers live at below-market rents; employers don't have to pay "
        "wages that reflect London's true cost of living.")
    _footnote(fig,
        "ONS PRMS × RSH SDR 2024–25 × MHCLG Table 100. "
        "Gross-up at 1.39× (28% effective marginal rate) converts net rent gap "
        "to equivalent gross wage.")
    _save(fig, "03_employer_subsidy")


# ── Chart 4: Social Rent completions collapse ──────────────────────────────────

def chart_supply_collapse() -> None:
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

    x   = annual["year_start"].values
    sr  = annual["Social Rent"].values
    ar  = annual["Affordable Rent"].values
    lar = annual["London Affordable Rent"].values

    peak_sr  = sr.max()
    peak_yr  = int(x[sr.argmax()])
    cur_sr   = int(annual.loc[annual["year_start"] == 2024, "Social Rent"].values[0])

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.09, "right": 0.97,
                                        "top": 0.87, "bottom": 0.12})
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(C["divider"])
    ax.spines["bottom"].set_color(C["divider"])
    ax.grid(axis="y", color=C["grid"], linewidth=0.65, zorder=0)
    ax.set_axisbelow(True)

    ax.stackplot(x, sr, ar, lar,
                 labels=["Social Rent", "Affordable Rent",
                         "London Affordable Rent"],
                 colors=[C["sr"], C["ar"], C["lar"]], alpha=0.88)

    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    ax.set_ylabel("Completions per year", color=C["sub"])
    ax.tick_params(labelsize=10)

    # Peak annotation — right of peak, below the top
    _annotate(ax,
        f"Peak: {peak_sr/1000:.0f}k/yr ({peak_yr})",
        xy=(peak_yr, peak_sr),
        xytext=(peak_yr + 7, peak_sr * 0.72),
        color=C["sr"])

    # Policy marker
    ax.axvline(2011, color=C["grey"], lw=1, linestyle=":", alpha=0.7)
    ax.text(2011.4, ax.get_ylim()[1] * 0.80,
            "2011–12: Affordable\nRent introduced\nat up to 80% market",
            fontsize=8, color=C["sub"], va="top")

    # Current level
    _annotate(ax,
        f"{cur_sr/1000:.0f}k/yr in 2024–25\n({cur_sr/peak_sr*100:.0f}% of peak)",
        xy=(2024, cur_sr),
        xytext=(2020, cur_sr + 18000),
        color=C["sr"])

    ax.legend(loc="upper right", framealpha=0.97)
    _title(ax,
        f"England built {peak_sr/1000:.0f},000 Social Rent homes a year in 1992. Now: {cur_sr/1000:.0f},000.",
        "The replacement tenure costs tenants far more — and the collapse is not self-correcting.")
    _footnote(fig, "MHCLG Affordable Housing Supply statistics 1991–2025.")
    _save(fig, "04_supply_collapse")


# ── Chart 5: North vs London — homes and subsidy ──────────────────────────────

def chart_north_vs_london(summary: pd.DataFrame, long: pd.DataFrame) -> None:
    units_by_la = (
        long.dropna(subset=["social_units"])
        .groupby("la_code")["social_units"].sum().rename("rsh_units")
    )
    df = summary.merge(units_by_la, on="la_code", how="left")
    df["units"] = df["rsh_units"].fillna(df["total_social_stock"])
    df = df.dropna(subset=["subsidy_social_wtavg_annual", "units", "region"])

    reg = (
        df.groupby("region")
        .apply(lambda g: pd.Series({
            "total_bn": (g["subsidy_social_wtavg_annual"] * g["units"]).sum() / 1e9,
            "units":    g["units"].sum(),
        }), include_groups=False)
        .reset_index()
    )

    north_regions = ["North East", "North West", "Yorkshire and The Humber"]
    london    = reg[reg["region"] == "London"].iloc[0]
    north     = reg[reg["region"].isin(north_regions)]
    north_bn  = north["total_bn"].sum()
    north_u   = north["units"].sum()
    lon_bn    = london["total_bn"]
    lon_u     = london["units"]

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE,
                             gridspec_kw={"wspace": 0.32, "left": 0.06,
                                          "right": 0.96, "top": 0.82,
                                          "bottom": 0.14})
    fig.patch.set_facecolor(C["bg"])

    labels = ["London", "The North\n(NE + NW + Yorks)"]
    bar_colors = [C["london"], C["north"]]
    x = np.array([0, 1])
    w = 0.50

    for ax in axes:
        ax.set_facecolor(C["bg"])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(C["divider"])
        ax.tick_params(axis="y", left=False, labelleft=False)
        ax.tick_params(axis="x", labelsize=10, colors=C["sub"])
        ax.grid(axis="y", color=C["grid"], linewidth=0.65, zorder=0)
        ax.set_axisbelow(True)

    # ── Left: social homes
    ax_h = axes[0]
    vals_h = [lon_u / 1e5, north_u / 1e5]
    b1 = ax_h.bar(x, vals_h, width=w, color=bar_colors,
                  edgecolor=C["bg"], linewidth=0.8)
    for bar, raw, col in zip(b1, [lon_u, north_u], bar_colors):
        ax_h.text(bar.get_x() + w / 2, bar.get_height() + max(vals_h) * 0.03,
                  f"{raw/1e6:.2f}m", ha="center", va="bottom",
                  fontsize=16, fontweight="bold", color=col)
    ax_h.set_xticks(x)
    ax_h.set_xticklabels(labels, fontsize=12)
    ax_h.get_xticklabels()[0].set_color(C["london"])
    ax_h.get_xticklabels()[0].set_fontweight("bold")
    ax_h.set_ylim(0, max(vals_h) * 1.30)
    ax_h.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v*100:.0f}k"))
    ax_h.set_title("Social homes", fontsize=12, color=C["sub"], pad=6)

    # ── Right: annual subsidy
    ax_s = axes[1]
    vals_s = [lon_bn, north_bn]
    b2 = ax_s.bar(x, vals_s, width=w, color=bar_colors,
                  edgecolor=C["bg"], linewidth=0.8)
    for bar, val, col in zip(b2, vals_s, bar_colors):
        ax_s.text(bar.get_x() + w / 2, bar.get_height() + max(vals_s) * 0.03,
                  f"£{val:.1f}bn/yr", ha="center", va="bottom",
                  fontsize=16, fontweight="bold", color=col)
    ax_s.set_xticks(x)
    ax_s.set_xticklabels(labels, fontsize=12)
    ax_s.get_xticklabels()[0].set_color(C["london"])
    ax_s.get_xticklabels()[0].set_fontweight("bold")
    ax_s.set_ylim(0, max(vals_s) * 1.30)
    ax_s.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"£{v:.0f}bn"))
    ax_s.set_title("Annual implicit subsidy", fontsize=12, color=C["sub"], pad=6)
    ax_s.tick_params(axis="y", left=True, labelleft=True)

    fig.suptitle(
        f"The North has {north_u/lon_u:.0f}× as many social homes as London. "
        f"It gets {lon_bn/north_bn:.1f}× less money.",
        fontsize=15.5, fontweight="bold", color=C["text"], y=0.97,
    )
    _footnote(fig,
        'ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25 × MHCLG Table 100. '
        '"The North" = North East + North West + Yorkshire and The Humber.')
    _save(fig, "05_north_vs_london")


# ── Chart 6: The subsidy lottery — regional beeswarm ─────────────────────────
# Redesigned from a 2D scatter to a regional strip/forest plot.
# Each row = one region. Each dot = one LA. Diamond = regional median.
# Shows a 1D distribution of a 1D quantity, grouped by region.

def chart_subsidy_lottery(summary: pd.DataFrame) -> None:
    df = summary.dropna(subset=["subsidy_social_wtavg_annual",
                                "region", "la_name"]).copy()

    NINE = {
        "North East", "North West", "Yorkshire and The Humber",
        "East Midlands", "West Midlands", "South West",
        "East of England", "South East", "London",
    }
    df = df[df["region"].isin(NINE)]

    # Regions ordered lowest to highest median — NE at bottom, London at top
    region_order = (
        df.groupby("region")["subsidy_social_wtavg_annual"]
        .median().sort_values().index.tolist()
    )

    rng = np.random.default_rng(42)

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.20, "right": 0.92,
                                        "top": 0.87, "bottom": 0.12})
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(C["divider"])
    ax.grid(axis="x", color=C["grid"], linewidth=0.65, zorder=0)
    ax.set_axisbelow(True)

    for i, region in enumerate(region_order):
        rdata = df[df["region"] == region]["subsidy_social_wtavg_annual"].values
        col   = _region_color(region)

        # Range bar: 10th–90th percentile
        p10, p90 = np.percentile(rdata, [10, 90])
        ax.plot([p10, p90], [i, i], color=col, linewidth=2.0,
                alpha=0.30, solid_capstyle="round", zorder=1)

        # Individual LA dots (jittered vertically)
        y_jit = i + rng.uniform(-0.30, 0.30, len(rdata))
        ax.scatter(rdata, y_jit, s=16, alpha=0.45, color=col,
                   linewidths=0, zorder=2)

        # Median diamond
        med = np.median(rdata)
        ax.scatter([med], [i], s=90, color=col, marker="D",
                   edgecolors="white", linewidths=0.8, zorder=5)

        # Median label
        ax.text(med, i + 0.40, f"£{med:,.0f}",
                ha="center", va="bottom", fontsize=7.5,
                color=col, fontweight="bold")

    # Label K&C (highest) and Redcar (lowest)
    top = df.nlargest(1, "subsidy_social_wtavg_annual").iloc[0]
    bot = df.nsmallest(1, "subsidy_social_wtavg_annual").iloc[0]
    top_i = region_order.index(top["region"])
    bot_i = region_order.index(bot["region"])

    _annotate(ax,
        f"{top['la_name']}\n£{top['subsidy_social_wtavg_annual']:,.0f}/yr",
        xy=(top["subsidy_social_wtavg_annual"], top_i),
        xytext=(top["subsidy_social_wtavg_annual"] * 0.80, top_i + 1.4),
        color=C["london"], ha="center")

    _annotate(ax,
        f"{bot['la_name']}\n£{bot['subsidy_social_wtavg_annual']:,.0f}/yr",
        xy=(bot["subsidy_social_wtavg_annual"], bot_i),
        xytext=(bot["subsidy_social_wtavg_annual"] + 2800, bot_i - 1.3),
        color=C["north"], ha="left")

    ax.set_yticks(range(len(region_order)))
    ax.set_yticklabels([_short(r) for r in region_order], fontsize=10.5)
    _ytick_style(ax, region_order)
    ax.tick_params(axis="y", left=False)
    ax.set_ylim(-0.8, len(region_order) - 0.3)

    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax.set_xlabel("Annual implicit subsidy per social home (£/yr)")

    ratio = (top["subsidy_social_wtavg_annual"]
             / bot["subsidy_social_wtavg_annual"])
    _title(ax,
        f"The same national system. A {ratio:.0f}:1 lottery.",
        "Every dot is a local authority. Diamonds show regional medians.")
    _footnote(fig,
        "ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25. "
        "290 English local authorities. Per-unit annual subsidy, stock-weighted.")
    _save(fig, "06_subsidy_lottery")


# ── Chart 7: Supply gap — completions vs stock share ──────────────────────────
# Redesigned as a diverging gap chart (completions share − stock share).
# Bars left of zero = underbuilding; bars right = overbuilding.

def chart_supply_vs_stock() -> None:
    df = pd.read_csv(RAW / "ahs_open_data.csv", low_memory=False)
    df = df[df["Completions"] == "Completion"].copy()
    df["year_start"] = df["Year"].str[:4].astype(int)

    sr   = df[(df["Tenure"] == "Social Rent") & (df["year_start"] >= 2020)]
    comp = sr.groupby("Region name")["Units"].sum()

    summ = pd.read_csv(PROCESSED / "subsidy_summary_by_la.csv")
    stock = (
        summ.dropna(subset=["region"])
        .groupby("region")["total_social_stock"].sum()
    )

    regions = [r for r in comp.index if r in stock.index]
    total_c = comp[regions].sum()
    total_s = stock[regions].sum()

    data = pd.DataFrame({
        "region":    regions,
        "comp_pct":  [comp[r] / total_c * 100  for r in regions],
        "stock_pct": [stock[r] / total_s * 100 for r in regions],
    })
    data["gap"] = data["comp_pct"] - data["stock_pct"]
    data = data.sort_values("gap").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.22, "right": 0.94,
                                        "top": 0.87, "bottom": 0.12})
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(C["divider"])
    ax.grid(axis="x", color=C["grid"], linewidth=0.65, zorder=0)
    ax.set_axisbelow(True)

    y = np.arange(len(data))

    for i, row in data.iterrows():
        color = C["gap_pos"] if row["gap"] > 0 else C["gap_neg"]
        if row["region"] in NORTH:
            color = C["london"]
        ax.barh(i, row["gap"], height=0.58, color=color,
                alpha=0.88, edgecolor=C["bg"], linewidth=0.5)

    # Label Northern regions only; place just right of the zero line to avoid y-axis overlap
    for i, row in data.iterrows():
        if row["region"] not in NORTH:
            continue
        # Position label inside the positive (empty) side, anchored at 0.15pp right of zero
        ax.text(0.20, i,
                f'{row["comp_pct"]:.1f}% built / {row["stock_pct"]:.1f}% of stock',
                va="center", ha="left", fontsize=8.5,
                color=C["london"], fontweight="bold")

    # Zero reference
    ax.axvline(0, color=C["divider"], lw=1.2, zorder=3)

    ax.set_yticks(y)
    ax.set_yticklabels([_short(r) for r in data["region"]], fontsize=10.5)
    _ytick_style(ax, list(data["region"]))
    ax.tick_params(axis="y", left=False)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v:+.1f}pp"))
    ax.set_xlabel("Completions share minus stock share (percentage points)")

    # Legend patches
    patches = [
        mpatches.Patch(color=C["london"],   label="Northern regions (underbuilding)"),
        mpatches.Patch(color=C["gap_neg"],  label="Other underbuilders"),
        mpatches.Patch(color=C["gap_pos"],  label="Overbuilders — mostly via S106"),
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=9)

    ne  = data.loc[data["region"] == "North East"]
    nw  = data.loc[data["region"] == "North West"]
    ne_str = f"NE: {ne['comp_pct'].iloc[0]:.1f}% built, {ne['stock_pct'].iloc[0]:.1f}% of stock"
    _title(ax,
        "The North holds the stock but isn't building.",
        f"{ne_str} — its completions rate is less than a third of its fair share.")
    _footnote(fig,
        "MHCLG Affordable Housing Supply 2020–24 × MHCLG Table 100. "
        "Social Rent completions only. Zero line = building at proportionate rate.",
        note="Overbuilding in South West and West Midlands is driven "
             "by Section 106 planning obligations, not government grant.")
    _save(fig, "07_supply_vs_stock")


# ── Chart 8: Govt-grant investment — NE vs London ─────────────────────────────

def _grant_units() -> pd.DataFrame:
    df = pd.read_csv(RAW / "ahs_open_data.csv", low_memory=False)
    df = df[df["Completions"] == "Completion"].copy()
    df["year_start"] = df["Year"].str[:4].astype(int)

    def is_grant(x):
        x = str(x)
        return "HE/GLA funded" in x or "HE Funded" in x or "Guarantees" in x

    sr = df[(df["Tenure"] == "Social Rent") & (df["year_start"] >= 2009)].copy()
    sr["govt_grant"] = sr["LT1000"].apply(is_grant)

    grant = (
        sr[sr["govt_grant"]]
        .groupby(["Region name", "year_start"])["Units"].sum()
        .reset_index()
    )
    grant["pop"]      = grant["Region name"].map(REGIONAL_POP)
    grant["per_100k"] = grant["Units"] / (grant["pop"] / 100_000)
    return grant


def chart_grant_investment_ne_london() -> None:
    grant  = _grant_units()
    years  = sorted(grant["year_start"].unique())
    ne_p   = (grant[grant["Region name"] == "North East"]
              .set_index("year_start")["per_100k"]
              .reindex(years, fill_value=0))
    lon_p  = (grant[grant["Region name"] == "London"]
              .set_index("year_start")["per_100k"]
              .reindex(years, fill_value=0))

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.09, "right": 0.97,
                                        "top": 0.87, "bottom": 0.14})
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(C["divider"])
    ax.spines["bottom"].set_color(C["divider"])
    ax.grid(axis="y", color=C["grid"], linewidth=0.65, zorder=0)
    ax.set_axisbelow(True)

    ax.fill_between(years, lon_p, alpha=0.10, color=C["london"])
    ax.fill_between(years, ne_p,  alpha=0.15, color=C["north"])
    ax.plot(years, lon_p, color=C["london"], linewidth=2.5,
            label="London", zorder=3)
    ax.plot(years, ne_p,  color=C["north"],  linewidth=2.5,
            label="North East", zorder=3)

    # Annotate 2017 (NE = 0)
    ax.annotate(
        "North East: 0 homes\nLondon: 2.8 per 100k",
        xy=(2017, 0), xytext=(2015.2, 28),
        fontsize=8.5, color=C["sub"],
        arrowprops=dict(arrowstyle="-|>", color=C["sub"], lw=0.8),
        bbox=dict(boxstyle="round,pad=0.28", fc=C["bg"],
                  ec=C["divider"], alpha=0.97, lw=0.8),
    )

    # London peak
    peak_yr = int(lon_p.idxmax())
    peak_v  = lon_p[peak_yr]
    _annotate(ax,
        f"London peak: {peak_v:.0f}/100k ({peak_yr})",
        xy=(peak_yr, peak_v),
        xytext=(peak_yr + 3, peak_v - 28),
        color=C["london"])

    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Govt-grant Social Rent completions\nper 100,000 people",
                  color=C["sub"])
    ax.tick_params(labelsize=10)
    ax.legend(loc="upper right")

    ne_cum  = ne_p.sum()
    lon_cum = lon_p.sum()
    _title(ax,
        f"Over 15 years, London received {lon_cum/ne_cum:.1f}× more "
        f"government-funded Social Rent homes per person.",
        "In 2017 the North East received zero.")
    _footnote(fig,
        "MHCLG Affordable Housing Supply 2009–2024. "
        "Government grant = HE/GLA funded completions only (excludes S106). "
        "Population: 2021 Census.",
        note="London's figure includes the GLA Mayor's Housing Programme — "
             "a dedicated regional authority with no Northern equivalent.")
    _save(fig, "08_grant_investment_ne_london")


# ── Chart 9: Govt-grant per capita — all regions ──────────────────────────────

def chart_grant_per_capita_all_regions() -> None:
    grant = _grant_units()
    reg = (
        grant.groupby("Region name")
        .apply(lambda g: pd.Series({
            "per_100k": g["Units"].sum() / (g["pop"].iloc[0] / 100_000),
        }), include_groups=False)
        .reset_index()
        .sort_values("per_100k")
    )
    reg = reg[reg["Region name"].isin(REGIONAL_POP)].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=FIGSIZE,
                           gridspec_kw={"left": 0.20, "right": 0.84,
                                        "top": 0.87, "bottom": 0.12})
    fig.patch.set_facecolor(C["bg"])
    _ax_base(ax)

    colors = [_region_color(r) for r in reg["Region name"]]
    bars = ax.barh(range(len(reg)), reg["per_100k"],
                   color=colors, height=0.62,
                   edgecolor=C["bg"], linewidth=0.8)

    ax.set_xlim(0, reg["per_100k"].max() * 1.22)
    _bar_labels(ax, bars, reg["per_100k"],
                lambda v: f"{v:.0f}", list(reg["Region name"]))

    ax.set_yticks(range(len(reg)))
    ax.set_yticklabels([_short(r) for r in reg["Region name"]], fontsize=11)
    _ytick_style(ax, list(reg["Region name"]))
    ax.set_xlabel(
        "Govt-grant Social Rent completions per 100,000 people, 2009–2024")

    lon_v = reg.loc[reg["Region name"] == "London",     "per_100k"].iloc[0]
    ne_v  = reg.loc[reg["Region name"] == "North East", "per_100k"].iloc[0]
    yk_v  = reg.loc[reg["Region name"] == "Yorkshire and The Humber",
                    "per_100k"].iloc[0]

    _title(ax,
        f"London received {lon_v/ne_v:.1f}× more government-funded Social Rent "
        f"per person than the North East,",
        f"and {lon_v/yk_v:.1f}× more than Yorkshire, over 15 years.")
    _footnote(fig,
        "MHCLG Affordable Housing Supply 2009–2024. "
        "Excludes S106 and local authority own funding. "
        "Population: 2021 Census.",
        note="London's figure includes the GLA Mayor's Housing Programme — "
             "a dedicated regional housing authority with no Northern equivalent.")
    _save(fig, "09_grant_per_capita_regions")


# ── Runner ─────────────────────────────────────────────────────────────────────

def run() -> None:
    summary = pd.read_csv(PROCESSED / "subsidy_summary_by_la.csv")
    long    = pd.read_csv(PROCESSED / "subsidy_by_la_bedroom.csv")

    chart_invisible_transfer(summary)
    chart_per_unit_subsidy(summary, long)
    chart_employer_subsidy(summary, long)
    chart_supply_collapse()
    chart_north_vs_london(summary, long)
    chart_subsidy_lottery(summary)
    chart_supply_vs_stock()
    chart_grant_investment_ne_london()
    chart_grant_per_capita_all_regions()


if __name__ == "__main__":
    run()
