"""
Equalisation cost curve: total extra annual spend required to bring all
social tenants up to a given subsidy-per-unit target.

Produces data/processed/fig_equalisation_curve.png
Run standalone:  python -m src.equalisation
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from .constants import PROCESSED


def build_curve_data(df: pd.DataFrame, n_points: int = 500) -> pd.DataFrame:
    """
    For each target T sampled across the subsidy range, compute:
      - extra_cost_bn  : sum of shortfalls × units (£bn)
      - las_affected   : number of LAs below the target
      - units_affected : total units in those LAs
    """
    s = df["subsidy_social_wtavg_annual"].values
    u = df["units"].values
    targets = np.linspace(s.min(), s.max(), n_points)

    return pd.DataFrame(
        {
            "target": targets,
            "extra_cost_bn": [((np.maximum(0, t - s)) * u).sum() / 1e9 for t in targets],
            "las_affected": [(s < t).sum() for t in targets],
            "units_affected": [(u[s < t]).sum() for t in targets],
        }
    )


def plot_equalisation_curve(df: pd.DataFrame, out_path: Path) -> None:
    s = df["subsidy_social_wtavg_annual"].values
    u = df["units"].values
    total_las = len(df)

    curve = build_curve_data(df)

    # Key reference points (value, display label, annotation y-anchor fraction 0–1)
    markers = [
        (np.percentile(s, 25), "Lower\nquartile", 0.10),
        (np.percentile(s, 50), "Median",           0.22),
        (s.mean(),             "Mean",              0.34),
        (np.percentile(s, 75), "Upper\nquartile",  0.50),
    ]

    existing_bn = (s * u).sum() / 1e9

    # ── Figure: two-panel layout ───────────────────────────────────────────
    # Left panel zooms into the policy-relevant range (up to ~£15k);
    # right panel shows the full range for context.
    fig, (ax_zoom, ax_full) = plt.subplots(
        1, 2, figsize=(13, 6),
        gridspec_kw={"width_ratios": [3, 2]},
    )
    fig.patch.set_facecolor("white")

    ZOOM_MAX = 15_000   # x-axis cap for left panel

    for ax, x_max, panel_label in [
        (ax_zoom, ZOOM_MAX, "Zoom: £0 – £15,000 target range"),
        (ax_full, s.max(),  "Full range to maximum (K&C)"),
    ]:
        zoom_mask = curve["target"] <= x_max
        cx = curve.loc[zoom_mask, "target"]
        cy = curve.loc[zoom_mask, "extra_cost_bn"]
        cy2 = curve.loc[zoom_mask, "las_affected"] / total_las * 100

        # Cost fill + line
        ax.fill_between(cx, cy, alpha=0.10, color="#1f6db5")
        ax.plot(cx, cy, color="#1f6db5", linewidth=2.5, zorder=3,
                label="Extra annual cost (left)")

        # Secondary axis: % LAs affected
        ax2 = ax.twinx()
        ax2.plot(cx, cy2, color="#e05b2b", linewidth=1.5,
                 linestyle="--", alpha=0.85, zorder=2,
                 label="LAs below target (right)")
        ax2.set_ylim(0, 105)
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
        ax2.tick_params(axis="y", colors="#e05b2b", labelsize=8)
        ax2.spines["right"].set_color("#e05b2b")
        ax2.spines["top"].set_visible(False)
        if ax is ax_full:
            ax2.set_ylabel("LAs brought up to target", color="#e05b2b", fontsize=9)

        # Existing total subsidy reference
        ax.axhline(existing_bn, color="#888", linewidth=0.9,
                   linestyle=":", alpha=0.7, zorder=1)
        if ax is ax_zoom:
            ax.text(200, existing_bn + 0.3,
                    f"Existing total subsidy  £{existing_bn:.0f}bn",
                    fontsize=7.5, color="#666", va="bottom")

        # Marker lines — only on zoom panel where they're readable
        if ax is ax_zoom:
            y_top = cy.max() * 1.05
            for x_val, label, _ in markers:
                if x_val > x_max:
                    continue
                cost_at = ((np.maximum(0, x_val - s)) * u).sum() / 1e9
                las_pct = (s < x_val).sum() / total_las * 100
                ax.axvline(x_val, color="#aaa", linewidth=0.8,
                           linestyle=":", zorder=1)
                ax.scatter([x_val], [cost_at], color="#1f6db5", s=50, zorder=5)
                ax.annotate(
                    f"{label}\n£{x_val:,.0f}/unit\n→ £{cost_at:.1f}bn\n   {las_pct:.0f}% of LAs",
                    xy=(x_val, cost_at),
                    xytext=(x_val + 300, cost_at + 1.5),
                    fontsize=7.5,
                    color="#333",
                    va="bottom",
                    arrowprops=dict(arrowstyle="-", color="#bbb", lw=0.8),
                    bbox=dict(boxstyle="round,pad=0.2", fc="white",
                              ec="#ddd", alpha=0.85),
                )

        ax.set_xlim(0, x_max + x_max * 0.02)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Target subsidy (£/unit/year)", fontsize=9)
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}")
        )
        ax.tick_params(axis="x", labelsize=8, rotation=15)
        ax.spines["top"].set_visible(False)
        ax.set_title(panel_label, fontsize=9, color="#444", pad=4)

    ax_zoom.set_ylabel("Extra annual cost to equalise (£bn)",
                       color="#1f6db5", fontsize=10)
    ax_zoom.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"£{x:.0f}bn")
    )
    ax_zoom.tick_params(axis="y", colors="#1f6db5", labelsize=9)
    ax_zoom.spines["left"].set_color("#1f6db5")

    ax_full.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"£{x:.0f}bn")
    )
    ax_full.tick_params(axis="y", labelsize=9)
    ax_full.spines["left"].set_visible(False)
    ax_full.tick_params(axis="y", left=False, labelleft=False)

    # Shared legend
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color="#1f6db5", lw=2.5,
               label="Extra annual cost to equalise (left axis)"),
        Line2D([0], [0], color="#e05b2b", lw=1.5, linestyle="--",
               label="% of LAs below target (right axis)"),
        Line2D([0], [0], color="#888", lw=0.9, linestyle=":",
               label=f"Existing total subsidy (£{existing_bn:.0f}bn)"),
    ]
    ax_zoom.legend(handles=handles, loc="upper left", fontsize=8,
                   framealpha=0.9, edgecolor="#ddd")

    fig.suptitle(
        "Cost of equalising the implicit social housing subsidy across English local authorities",
        fontsize=12, fontweight="bold", y=1.01,
    )
    fig.text(
        0.5, -0.02,
        "Each point on the curve = total extra annual spend needed to bring every LA below that target up to it.\n"
        "Source: ONS PRMS (Oct 2022–Sep 2023) × RSH SDR 2024–25. 290 English LAs, ~3.1m social units.",
        ha="center", fontsize=7.5, color="#666",
    )

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(out_path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def run():
    from .constants import PROCESSED
    import pandas as pd

    summary = pd.read_csv(PROCESSED.parent / "processed" / "subsidy_summary_by_la.csv")

    # Rebuild unit counts (same logic as in the analysis response)
    long = pd.read_csv(PROCESSED.parent / "processed" / "subsidy_by_la_bedroom.csv")
    units_by_la = (
        long.dropna(subset=["social_units"])
        .groupby("la_code")["social_units"]
        .sum()
        .rename("total_social_units_rsh")
    )
    df = summary.merge(units_by_la, on="la_code", how="left")
    df["units"] = df["total_social_units_rsh"].fillna(df["total_social_stock"])
    df = df.dropna(subset=["subsidy_social_wtavg_annual", "units"])
    df = df[df["units"] > 0].copy()

    out_path = PROCESSED / "fig_equalisation_curve.png"
    plot_equalisation_curve(df, out_path)


if __name__ == "__main__":
    run()
