#!/usr/bin/env python3
"""Generate storyline-aligned figures for article charts.

Notebook-friendly API:
- call `generate_all_figures(data_dir, out_dir, show_inline=True)` in Jupyter.
CLI:
- run this file directly with --data-dir and --out-dir.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt

SCENARIO_ORDER = ["BAU", "CDS", "RES", "RSS", "SCS"]
DEFAULT_STYLE = {
    "font_family": "Arial",
    "font_fallback": "Helvetica",
    "figure_dpi": 300,
    "save_transparent": False,
    "line_width": 2.2,
    "bau_color": "#4D4D4D",
    "scenario_colors": {
        "CDS": "#2C7FB8",
        "RES": "#41AB5D",
        "RSS": "#F16913",
        "SCS": "#54278F",
    },
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(v: str) -> float:
    return float("nan") if v in (None, "") else float(v)


def _apply_style(style: dict) -> dict:
    colors = {"BAU": style["bau_color"], **style["scenario_colors"]}
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [style["font_family"], style["font_fallback"], "DejaVu Sans"]
    return colors


def fig1_bau(data_dir: Path, out_dir: Path, style: dict, show_inline: bool = False):
    colors = _apply_style(style)
    waste = [r for r in read_csv(data_dir / "plastic_waste_generation_annual_main.csv") if r["scenario"] == "BAU" and r["variant"] == "CENTRAL"]
    policy = [r for r in read_csv(data_dir / "annual_policy_trajectories.csv") if r["scenario"] == "BAU" and r["variant"] == "CENTRAL"]

    years = [int(r["year"]) for r in waste]
    waste_mt = [to_float(r["plastic_waste_generation_Mt"]) for r in waste]
    leakage_mt = [to_float(r["total_leakage_t"]) / 1e6 for r in policy]
    ghg_mt = [to_float(r["ghg_total"]) / 1e6 for r in policy]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharex=True)
    axes[0].plot(years, waste_mt, color=colors["BAU"], lw=style["line_width"])
    axes[0].set_title("BAU waste generation")
    axes[0].set_ylabel("Mt/year")
    axes[1].plot(years, leakage_mt, color=colors["BAU"], lw=style["line_width"])
    axes[1].set_title("BAU leakage")
    axes[1].set_ylabel("Mt/year")
    axes[2].plot(years, ghg_mt, color=colors["BAU"], lw=style["line_width"])
    axes[2].set_title("BAU GHG")
    axes[2].set_ylabel("MtCO2e/year")
    for ax in axes:
        ax.set_xlabel("Year")
        ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig1_BAU_baseline.png", dpi=style["figure_dpi"], transparent=style["save_transparent"])
    if show_inline:
        plt.show()
    plt.close(fig)


def fig2_interventions(data_dir: Path, out_dir: Path, style: dict, show_inline: bool = False):
    colors = _apply_style(style)
    rows = [r for r in read_csv(data_dir / "annual_policy_trajectories.csv") if r["variant"] == "CENTRAL"]
    by_scen = {s: [] for s in SCENARIO_ORDER}
    for r in rows:
        by_scen[r["scenario"]].append(r)
    for s in by_scen:
        by_scen[s].sort(key=lambda x: int(x["year"]))

    years = [int(r["year"]) for r in by_scen["BAU"]]
    bau_leak = [to_float(r["total_leakage_t"]) / 1e6 for r in by_scen["BAU"]]
    bau_ghg = [to_float(r["ghg_total"]) / 1e6 for r in by_scen["BAU"]]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
    for s in ["CDS", "RES", "RSS", "SCS"]:
        leak = [to_float(r["total_leakage_t"]) / 1e6 for r in by_scen[s]]
        ghg = [to_float(r["ghg_total"]) / 1e6 for r in by_scen[s]]
        axes[0].plot(years, [b - x for b, x in zip(bau_leak, leak)], label=s, color=colors[s], lw=style["line_width"])
        axes[1].plot(years, [b - x for b, x in zip(bau_ghg, ghg)], label=s, color=colors[s], lw=style["line_width"])

    axes[0].set_title("Leakage reduction vs BAU")
    axes[0].set_ylabel("Mt/year avoided")
    axes[1].set_title("GHG reduction vs BAU")
    axes[1].set_ylabel("MtCO2e/year avoided")
    for ax in axes:
        ax.set_xlabel("Year")
        ax.grid(alpha=0.2)
    axes[1].legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig2_Intervention_impacts.png", dpi=style["figure_dpi"], transparent=style["save_transparent"])
    if show_inline:
        plt.show()
    plt.close(fig)


def fig3_cost_coabatement(data_dir: Path, out_dir: Path, style: dict, show_inline: bool = False):
    colors = _apply_style(style)
    rows = [r for r in read_csv(data_dir / "policy_core_metrics.csv") if r["variant"] == "CENTRAL"]
    rows = sorted(rows, key=lambda r: SCENARIO_ORDER.index(r["scenario"]))
    scenarios = [r["scenario"] for r in rows if r["scenario"] != "BAU"]
    inv_per_t = [to_float(r["investment_per_t_avoided_pv_3_5_usd"]) for r in rows if r["scenario"] != "BAU"]

    annual = [r for r in read_csv(data_dir / "annual_policy_trajectories.csv") if r["variant"] == "CENTRAL"]
    by_scen = {s: [] for s in SCENARIO_ORDER}
    for r in annual:
        by_scen[r["scenario"]].append(r)
    bau_ghg = sum(to_float(r["ghg_total"]) for r in by_scen["BAU"])
    bau_leak = sum(to_float(r["total_leakage_t"]) for r in by_scen["BAU"])
    ghg_red = [(bau_ghg - sum(to_float(r["ghg_total"]) for r in by_scen[s])) / 1e6 for s in scenarios]
    leak_avoid = [(bau_leak - sum(to_float(r["total_leakage_t"]) for r in by_scen[s])) / 1e6 for s in scenarios]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].bar(scenarios, inv_per_t, color=[colors[s] for s in scenarios])
    axes[0].set_title("Cost-effectiveness (PV 3.5%)")
    axes[0].set_ylabel("USD per t leakage avoided")
    for s, x, y in zip(scenarios, leak_avoid, ghg_red):
        axes[1].scatter(x, y, s=95, color=colors[s])
        axes[1].annotate(s, (x, y), textcoords="offset points", xytext=(6, 4), fontsize=9)
    axes[1].set_title("Co-abatement vs BAU")
    axes[1].set_xlabel("Leakage avoided (Mt, cumulative)")
    axes[1].set_ylabel("GHG reduced (MtCO2e, cumulative)")
    axes[1].grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig3_Cost_effectiveness_and_coabatement.png", dpi=style["figure_dpi"], transparent=style["save_transparent"])
    if show_inline:
        plt.show()
    plt.close(fig)


def generate_all_figures(data_dir: Path | str = ".", out_dir: Path | str = "figure_pipeline/output", style: dict | None = None, show_inline: bool = False):
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    style_cfg = DEFAULT_STYLE if style is None else style
    fig1_bau(data_dir, out_dir, style_cfg, show_inline=show_inline)
    fig2_interventions(data_dir, out_dir, style_cfg, show_inline=show_inline)
    fig3_cost_coabatement(data_dir, out_dir, style_cfg, show_inline=show_inline)
    return out_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=Path("figure_pipeline/output"))
    args = parser.parse_args()
    out = generate_all_figures(args.data_dir, args.out_dir, style=DEFAULT_STYLE, show_inline=False)
    print(f"Generated figures in: {out}")


if __name__ == "__main__":
    main()
