"""
Create two high-impact Nature-style BAU figures from model output CSV files.

The figures focus on the baseline plastic waste management system from 2020 to 2044
and are exported as separate files (no multi-panel composites).

Expected files in BASE_DIR:
- annual_pathway_diagnostics.csv
- cumulative_pathway_diagnostics.csv
- plastic_waste_generation_annual_main.csv
- stock_pollution_legacy_annual.csv

Outputs:
- figures_bau/bau_figure_1_bau_system_timeseries.png/.svg
- figures_bau/bau_figure_2_bau_legacy_and_cumulative.png/.svg
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
START_YEAR = 2020
END_YEAR = 2044

COLORS = {
    "black": "#222222",
    "grey": "#7A7A7A",
    "light_grey": "#D9D9D9",
    "blue": "#3B6EA8",
    "sky": "#6BAED6",
    "teal": "#3A9D8F",
    "green": "#6CA66B",
    "orange": "#D9853B",
    "red": "#B64C3B",
    "purple": "#7A68A6",
    "brown": "#8C6D31",
    "sand": "#D6C6A8",
}


def mt(values):
    return np.asarray(values, dtype=float) / 1e6


def load_inputs(base_dir: Path):
    annual = pd.read_csv(base_dir / "annual_pathway_diagnostics.csv")
    generation = pd.read_csv(base_dir / "plastic_waste_generation_annual_main.csv")
    cumulative = pd.read_csv(base_dir / "cumulative_pathway_diagnostics.csv")
    legacy = pd.read_csv(base_dir / "stock_pollution_legacy_annual.csv")
    return annual, generation, cumulative, legacy


def bau_variant(df: pd.DataFrame, variant: str | None = CENTRAL):
    out = df[df["scenario"].eq(SCENARIO)].copy()
    if variant is not None and "variant" in out.columns:
        out = out[out["variant"].eq(variant)].copy()
    if "year" in out.columns:
        out = out[out["year"].between(START_YEAR, END_YEAR)]
        out = out.sort_values("year")
    return out


def setup_matplotlib():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "axes.linewidth": 0.7,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.4,
            "figure.titlesize": 12,
            "savefig.dpi": 600,
            "figure.dpi": 120,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def style_axis(ax, ylabel=None):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["black"])
    ax.spines["bottom"].set_color(COLORS["black"])
    ax.tick_params(length=3, width=0.6, color=COLORS["black"])
    ax.grid(axis="y", color="#ECECEC", linewidth=0.65)
    ax.set_axisbelow(True)
    ax.set_xlim(START_YEAR, END_YEAR)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=7))
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:g}"))


def plot_uncertainty_band(ax, df, col, color, alpha=0.14):
    c = bau_variant(df, CENTRAL)
    l = bau_variant(df, LOWER)
    u = bau_variant(df, UPPER)
    if l.empty or u.empty or col not in l.columns or col not in u.columns:
        return
    ax.fill_between(
        c["year"].to_numpy(),
        mt(l[col]),
        mt(u[col]),
        color=color,
        alpha=alpha,
        linewidth=0,
        zorder=1,
    )


def make_figure_1(annual, generation):
    """Single-file BAU system pathways time-series figure (no panels)."""
    setup_matplotlib()
    fig, ax = plt.subplots(figsize=(7.2, 4.6), constrained_layout=True)

    ann = bau_variant(annual, CENTRAL)
    gen = bau_variant(generation, CENTRAL)

    # Primary pathways and outcomes from system to leakage.
    series = [
        (gen, "plastic_waste_generation_t", "Waste generation", COLORS["blue"], 2.4),
        (annual, "formal_collection_t", "Formal collection", COLORS["green"], 1.8),
        (annual, "informal_collection_t", "Informal collection", COLORS["teal"], 1.8),
        (annual, "uncollected_t", "Uncollected", COLORS["red"], 2.0),
        (annual, "open_loop_mr_t", "Open-loop recycling", COLORS["purple"], 1.6),
        (annual, "closed_loop_mr_t", "Closed-loop recycling", COLORS["grey"], 1.6),
        (annual, "total_leakage_t", "Total leakage", COLORS["black"], 2.2),
    ]

    for source_df, col, label, color, lw in series:
        plot_uncertainty_band(ax, source_df, col, color)
        x = ann["year"].to_numpy() if source_df is annual else gen["year"].to_numpy()
        y = mt(ann[col] if source_df is annual else gen[col])
        ax.plot(x, y, color=color, lw=lw, label=label, zorder=3)

    style_axis(ax, "Mt yr$^{-1}$")
    ax.set_xlabel("Year")
    ax.set_title("BAU plastic waste system pathways and leakage, 2020–2044", loc="left", pad=7)

    # Keep the plotting area clean: push legend outside and reserve right margin via constrained layout.
    ax.legend(frameon=False, ncol=1, loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0.0)

    # Endpoint callouts for readability.
    ax.text(
        END_YEAR - 1.8,
        mt(gen["plastic_waste_generation_t"].iloc[-1]) + 0.08,
        f"Generation {mt(gen['plastic_waste_generation_t'].iloc[-1]):.2f} Mt",
        color=COLORS["blue"],
        fontsize=7.3,
        ha="left",
        va="center",
    )
    ax.text(
        END_YEAR - 1.8,
        mt(ann["total_leakage_t"].iloc[-1]) - 0.08,
        f"Leakage {mt(ann['total_leakage_t'].iloc[-1]):.2f} Mt",
        color=COLORS["black"],
        fontsize=7.3,
        ha="left",
        va="center",
    )

    fig.text(
        0.01,
        0.01,
        "Shaded bands indicate LOWER–UPPER variants where available. Values are annual million tonnes.",
        ha="left",
        va="bottom",
        fontsize=7.2,
        color=COLORS["grey"],
    )

    png = OUT_DIR / "bau_figure_1_bau_system_timeseries.png"
    svg = OUT_DIR / "bau_figure_1_bau_system_timeseries.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def make_figure_2(cumulative, legacy):
    """Single-file BAU cumulative burden figure (no panels)."""
    setup_matplotlib()
    fig, ax = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)

    leg = legacy[(legacy["scenario"].eq(SCENARIO)) & (legacy["year"].between(START_YEAR, END_YEAR))].sort_values("year")

    # Legacy stock composition across time.
    stock_cols = [
        ("unsanitary_dumpsites_stock_t", "Unsanitary dumpsites", COLORS["brown"]),
        ("ocean_leakage_stock_t", "Ocean stock", COLORS["blue"]),
        ("land_pollution_stock_t", "Land stock", COLORS["sand"]),
        ("surface_store_stock_t", "Surface store", COLORS["purple"]),
    ]

    ax.stackplot(
        leg["year"],
        [mt(leg[c]) for c, _, _ in stock_cols],
        labels=[label for _, label, _ in stock_cols],
        colors=[color for _, _, color in stock_cols],
        alpha=0.9,
        linewidth=0,
    )
    total_stock = np.sum([mt(leg[c]) for c, _, _ in stock_cols], axis=0)
    ax.plot(leg["year"], total_stock, color=COLORS["black"], lw=1.8, label="Total stock burden")

    style_axis(ax, "Mt stock")
    ax.set_xlabel("Year")
    ax.set_title("BAU legacy accumulation and cumulative leakage burden, 2020–2044", loc="left", pad=7)

    # Add concise cumulative leakage context inside the same figure.
    cum = cumulative[cumulative["scenario"].eq(SCENARIO)]
    cum_c = cum[cum["variant"].eq(CENTRAL)].iloc[0]
    total_cum = cum_c["total_leakage_t"] / 1e6
    aquatic_cum = cum_c["aquatic_t"] / 1e6
    terrestrial_cum = cum_c["terrestrial_t"] / 1e6
    burning_cum = cum_c["open_burning_t"] / 1e6

    ax.text(
        0.02,
        0.96,
        (
            f"Cumulative leakage (2020–2044): {total_cum:.1f} Mt\n"
            f"• Open burning: {burning_cum:.1f} Mt\n"
            f"• Aquatic: {aquatic_cum:.1f} Mt\n"
            f"• Terrestrial: {terrestrial_cum:.1f} Mt"
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.4,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CFCFCF", linewidth=0.6),
    )

    ax.legend(frameon=False, ncol=1, loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0.0)

    png = OUT_DIR / "bau_figure_2_bau_legacy_and_cumulative.png"
    svg = OUT_DIR / "bau_figure_2_bau_legacy_and_cumulative.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def main():
    annual, generation, cumulative, legacy = load_inputs(BASE_DIR)
    fig1 = make_figure_1(annual, generation)
    fig2 = make_figure_2(cumulative, legacy)
    print("Saved:")
    print(fig1[0])
    print(fig1[1])
    print(fig2[0])
    print(fig2[1])


if __name__ == "__main__":
    main()
