"""
Create high-impact Nature-style BAU figures from model output CSV files.

Expected files in BASE_DIR:
- annual_pathway_diagnostics.csv
- annual_policy_trajectories.csv
- cumulative_pathway_diagnostics.csv
- plastic_waste_generation_annual_main.csv
- stock_pollution_legacy_annual.csv

Outputs:
- bau_figure_1_annual_system_pathways.png/.svg
- bau_figure_2_legacy_and_cumulative_burden.png/.svg
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator


BASE_DIR = Path(".")
OUT_DIR = BASE_DIR / "figures_bau"
OUT_DIR.mkdir(exist_ok=True)

SCENARIO = "BAU"
CENTRAL = "CENTRAL"
LOWER = "LOWER"
UPPER = "UPPER"

COLORS = {
    "black": "#222222",
    "grey": "#7A7A7A",
    "light_grey": "#D9D9D9",
    "blue": "#3B6EA8",
    "sky": "#6BAED6",
    "teal": "#3A9D8F",
    "green": "#6CA66B",
    "yellow": "#C9A646",
    "orange": "#D9853B",
    "red": "#B64C3B",
    "purple": "#7A68A6",
    "brown": "#8C6D31",
    "sand": "#D6C6A8",
}

PATHWAY_LABELS = {
    "formal_collection_t": "Formal collection",
    "informal_collection_t": "Informal collection",
    "mixed_collection_t": "Mixed collection",
    "uncollected_t": "Uncollected",
    "closed_loop_mr_t": "Closed-loop mechanical recycling",
    "open_loop_mr_t": "Open-loop mechanical recycling",
    "chemical_p2p_t": "Chemical recycling: plastic-to-plastic",
    "chemical_p2f_t": "Chemical recycling: plastic-to-fuel",
    "engineered_landfill_t": "Engineered landfill",
    "thermal_treatment_t": "Thermal treatment",
    "unsanitary_dumpsite_t": "Unsanitary dumpsites",
    "uncollected_to_burn_t": "Uncollected → open burning",
    "uncollected_to_land_t": "Uncollected → land",
    "uncollected_to_water_t": "Uncollected → water",
    "post_collection_mismanaged_t": "Post-collection mismanaged",
    "aquatic_t": "Aquatic leakage",
    "terrestrial_t": "Terrestrial leakage",
    "open_burning_t": "Open burning",
    "total_leakage_t": "Total leakage",
}

def mt(values):
    return np.asarray(values, dtype=float) / 1e6

def pct_change(start, end):
    return 100 * (end / start - 1)

def load_inputs(base_dir: Path):
    annual = pd.read_csv(base_dir / "annual_pathway_diagnostics.csv")
    generation = pd.read_csv(base_dir / "plastic_waste_generation_annual_main.csv")
    policy = pd.read_csv(base_dir / "annual_policy_trajectories.csv")
    cumulative = pd.read_csv(base_dir / "cumulative_pathway_diagnostics.csv")
    legacy = pd.read_csv(base_dir / "stock_pollution_legacy_annual.csv")
    return annual, generation, policy, cumulative, legacy

def bau_variant(df: pd.DataFrame, variant: str | None = CENTRAL):
    out = df[df["scenario"].eq(SCENARIO)].copy()
    if variant is not None and "variant" in out.columns:
        out = out[out["variant"].eq(variant)].copy()
    return out.sort_values("year")

def setup_matplotlib():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 8.5,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "axes.linewidth": 0.7,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7.5,
        "figure.titlesize": 12,
        "savefig.dpi": 600,
        "figure.dpi": 120,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

def style_axis(ax, ylabel=None):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["black"])
    ax.spines["bottom"].set_color(COLORS["black"])
    ax.tick_params(length=3, width=0.6, color=COLORS["black"])
    ax.grid(axis="y", color="#ECECEC", linewidth=0.65)
    ax.set_axisbelow(True)
    ax.set_xlim(2020, 2044)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}"))

def panel_label(ax, label):
    ax.text(
        -0.12, 1.06, label, transform=ax.transAxes,
        fontsize=11, fontweight="bold", va="top", ha="left", color=COLORS["black"]
    )

def plot_with_uncertainty(ax, df, ycol, color, label, lw=1.8, alpha=0.16, zorder=3):
    central = bau_variant(df, CENTRAL)
    lower = bau_variant(df, LOWER)
    upper = bau_variant(df, UPPER)
    x = central["year"].to_numpy()
    y = mt(central[ycol])
    ax.plot(x, y, color=color, lw=lw, label=label, zorder=zorder)
    if not lower.empty and not upper.empty and ycol in lower.columns and ycol in upper.columns:
        ax.fill_between(
            x, mt(lower[ycol]), mt(upper[ycol]),
            color=color, alpha=alpha, linewidth=0, zorder=zorder - 1
        )
    return x, y

def endpoint_label(ax, x, y, text, color, dx=0.25):
    ax.text(
        x[-1] + dx, y[-1], text,
        color=color, fontsize=7.5, va="center", ha="left"
    )

def make_figure_1(annual, generation):
    setup_matplotlib()
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4), constrained_layout=True)
    ax_a, ax_b, ax_c, ax_d = axes.ravel()

    gen_c = bau_variant(generation, CENTRAL)
    ann_c = bau_variant(annual, CENTRAL)

    xg, yg = plot_with_uncertainty(
        ax_a, generation, "plastic_waste_generation_t",
        COLORS["blue"], "Plastic waste generation", lw=2.0
    )
    xl, yl = plot_with_uncertainty(
        ax_a, annual, "total_leakage_t",
        COLORS["red"], "Total leakage", lw=2.0
    )
    style_axis(ax_a, "Mt yr$^{-1}$")
    panel_label(ax_a, "a")
    ax_a.set_title("Rising demand pressure and leakage under BAU", loc="left", pad=7)
    ax_a.legend(frameon=False, loc="upper left")
    endpoint_label(ax_a, xg, yg, f"{yg[-1]:.2f} Mt", COLORS["blue"])
    endpoint_label(ax_a, xl, yl, f"{yl[-1]:.2f} Mt", COLORS["red"])
    g0, g1 = gen_c.iloc[0]["plastic_waste_generation_t"], gen_c.iloc[-1]["plastic_waste_generation_t"]
    l0, l1 = ann_c.iloc[0]["total_leakage_t"], ann_c.iloc[-1]["total_leakage_t"]
    ax_a.text(
        0.03, 0.53,
        f"Generation: +{pct_change(g0, g1):.0f}%\nLeakage: +{pct_change(l0, l1):.0f}%",
        transform=ax_a.transAxes, ha="left", va="top", fontsize=7.5,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#CFCFCF", linewidth=0.6)
    )

    throughput_cols = [
        ("uncollected_t", COLORS["red"]),
        ("informal_collection_t", COLORS["green"]),
        ("formal_collection_t", COLORS["blue"]),
        ("mixed_collection_t", COLORS["purple"]),
        ("open_loop_mr_t", COLORS["teal"]),
        ("closed_loop_mr_t", COLORS["grey"]),
        ("unsanitary_dumpsite_t", COLORS["brown"]),
    ]
    for col, color in throughput_cols:
        ax_b.plot(
            ann_c["year"], mt(ann_c[col]), color=color, lw=1.65,
            label=PATHWAY_LABELS[col]
        )
    style_axis(ax_b, "Mt yr$^{-1}$")
    panel_label(ax_b, "b")
    ax_b.set_title("Annual process throughputs", loc="left", pad=7)
    ax_b.legend(frameon=False, ncol=1, loc="upper left", bbox_to_anchor=(1.01, 1.02), borderaxespad=0)
    ax_b.text(
        0.03, 0.05,
        "Process throughputs are plotted separately;\ncollection/recovery lines are not additive.",
        transform=ax_b.transAxes, ha="left", va="bottom", fontsize=7.1, color=COLORS["grey"]
    )

    mis_cols = [
        "uncollected_to_burn_t",
        "uncollected_to_land_t",
        "uncollected_to_water_t",
        "post_collection_mismanaged_t",
    ]
    mis_colors = [COLORS["orange"], COLORS["sand"], COLORS["sky"], COLORS["purple"]]
    ax_c.stackplot(
        ann_c["year"],
        [mt(ann_c[c]) for c in mis_cols],
        labels=[PATHWAY_LABELS[c] for c in mis_cols],
        colors=mis_colors,
        alpha=0.92,
        linewidth=0
    )
    style_axis(ax_c, "Mt yr$^{-1}$")
    panel_label(ax_c, "c")
    ax_c.set_title("Mismanaged source routes", loc="left", pad=7)
    ax_c.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.02), borderaxespad=0)

    leak_cols = ["open_burning_t", "aquatic_t", "terrestrial_t"]
    leak_colors = [COLORS["orange"], COLORS["blue"], COLORS["brown"]]
    ax_d.stackplot(
        ann_c["year"],
        [mt(ann_c[c]) for c in leak_cols],
        labels=[PATHWAY_LABELS[c] for c in leak_cols],
        colors=leak_colors,
        alpha=0.92,
        linewidth=0
    )
    ax_d.plot(
        ann_c["year"], mt(ann_c["total_leakage_t"]),
        color=COLORS["black"], lw=1.3, label="Total leakage"
    )
    style_axis(ax_d, "Mt yr$^{-1}$")
    panel_label(ax_d, "d")
    ax_d.set_title("Leakage outcomes", loc="left", pad=7)
    ax_d.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.02), borderaxespad=0)
    ax_d.set_xlabel("Year")
    ax_c.set_xlabel("Year")

    fig.suptitle(
        "Business-as-usual plastic waste management system, 2020–2044",
        x=0.02, ha="left", y=1.02, fontweight="bold"
    )
    fig.text(
        0.02, -0.02,
        "Values are shown in million tonnes per year. Shaded bands in panel a show LOWER–UPPER model variants where available.",
        ha="left", va="top", fontsize=7.3, color=COLORS["grey"]
    )

    png = OUT_DIR / "bau_figure_1_annual_system_pathways.png"
    svg = OUT_DIR / "bau_figure_1_annual_system_pathways.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg

def make_figure_2(cumulative, legacy):
    setup_matplotlib()
    fig = plt.figure(figsize=(7.2, 3.8), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])

    leg = legacy[(legacy["scenario"].eq(SCENARIO)) & (legacy["year"].between(2020, 2044))].sort_values("year")
    stock_cols = [
        ("unsanitary_dumpsites_stock_t", "Unsanitary dumpsite stock", COLORS["brown"]),
        ("ocean_leakage_stock_t", "Ocean leakage stock", COLORS["blue"]),
        ("land_pollution_stock_t", "Land pollution stock", COLORS["sand"]),
        ("surface_store_stock_t", "Surface store stock", COLORS["purple"]),
    ]
    ax_a.stackplot(
        leg["year"],
        [mt(leg[c]) for c, _, _ in stock_cols],
        labels=[lab for _, lab, _ in stock_cols],
        colors=[col for _, _, col in stock_cols],
        alpha=0.92,
        linewidth=0
    )
    total_stock = np.sum([mt(leg[c]) for c, _, _ in stock_cols], axis=0)
    ax_a.plot(leg["year"], total_stock, color=COLORS["black"], lw=1.35, label="Total stock burden")
    style_axis(ax_a, "Mt stock")
    panel_label(ax_a, "a")
    ax_a.set_title("Accumulation of legacy pollution and disposal stocks", loc="left", pad=7)
    ax_a.set_xlabel("Year")
    ax_a.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1.02), borderaxespad=0)
    ax_a.text(
        0.04, 0.93,
        f"2020: {total_stock[0]:.2f} Mt\n2044: {total_stock[-1]:.2f} Mt",
        transform=ax_a.transAxes, va="top", ha="left", fontsize=7.5,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#CFCFCF", linewidth=0.6)
    )

    cum = cumulative[cumulative["scenario"].eq(SCENARIO)].copy()
    cats = ["open_burning_t", "aquatic_t", "terrestrial_t"]
    labels = [PATHWAY_LABELS[c] for c in cats]
    colors = [COLORS["orange"], COLORS["blue"], COLORS["brown"]]

    central = cum[cum["variant"].eq(CENTRAL)].set_index("variant")
    lower = cum[cum["variant"].eq(LOWER)]
    upper = cum[cum["variant"].eq(UPPER)]

    vals = np.array([cum.loc[cum["variant"].eq(CENTRAL), c].iloc[0] / 1e6 for c in cats])
    lower_vals = np.array([lower[c].iloc[0] / 1e6 if not lower.empty else np.nan for c in cats])
    upper_vals = np.array([upper[c].iloc[0] / 1e6 if not upper.empty else np.nan for c in cats])
    y = np.arange(len(cats))[::-1]

    for i, (val, lab, col) in enumerate(zip(vals, labels, colors)):
        yy = y[i]
        if not np.isnan(lower_vals[i]) and not np.isnan(upper_vals[i]):
            xerr = np.array([[val - lower_vals[i]], [upper_vals[i] - val]])
            ax_b.errorbar(
                val, yy, xerr=xerr, fmt="o", ms=5,
                color=col, ecolor=col, elinewidth=1.15, capsize=3, zorder=3
            )
        ax_b.barh(yy, val, height=0.42, color=col, alpha=0.35, edgecolor="none", zorder=2)
        ax_b.text(val + 0.35, yy, f"{val:.1f} Mt", va="center", ha="left", fontsize=8, color=COLORS["black"])

    total = cum.loc[cum["variant"].eq(CENTRAL), "total_leakage_t"].iloc[0] / 1e6
    ax_b.set_yticks(y)
    ax_b.set_yticklabels(labels)
    ax_b.set_xlabel("Cumulative leakage, 2020–2044 (Mt)")
    ax_b.set_title("Twenty-five-year leakage burden", loc="left", pad=7)
    panel_label(ax_b, "b")
    ax_b.spines["top"].set_visible(False)
    ax_b.spines["right"].set_visible(False)
    ax_b.spines["left"].set_visible(False)
    ax_b.grid(axis="x", color="#ECECEC", linewidth=0.65)
    ax_b.set_axisbelow(True)
    ax_b.tick_params(axis="y", length=0)
    ax_b.set_xlim(0, max(upper_vals[~np.isnan(upper_vals)].max() if np.any(~np.isnan(upper_vals)) else vals.max(), vals.max()) * 1.32)
    ax_b.text(
        0.02, 0.05,
        f"Total BAU leakage: {total:.1f} Mt",
        transform=ax_b.transAxes, ha="left", va="bottom", fontsize=8.2,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#CFCFCF", linewidth=0.6)
    )

    fig.suptitle(
        "Baseline accumulation and cumulative leakage burden",
        x=0.02, ha="left", y=1.04, fontweight="bold"
    )
    fig.text(
        0.02, -0.03,
        "Panel b points show central cumulative values; horizontal intervals show LOWER–UPPER variants.",
        ha="left", va="top", fontsize=7.3, color=COLORS["grey"]
    )

    png = OUT_DIR / "bau_figure_2_legacy_and_cumulative_burden.png"
    svg = OUT_DIR / "bau_figure_2_legacy_and_cumulative_burden.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg

def main():
    annual, generation, policy, cumulative, legacy = load_inputs(BASE_DIR)
    fig1 = make_figure_1(annual, generation)
    fig2 = make_figure_2(cumulative, legacy)
    print("Saved:")
    print(fig1[0])
    print(fig1[1])
    print(fig2[0])
    print(fig2[1])

if __name__ == "__main__":
    main()
