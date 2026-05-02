#!/usr/bin/env python3
"""Generate storyline-aligned figures for the article.

Figures:
1) BAU baseline: waste generation, leakage, GHG
2) Intervention effects on leakage and GHG vs BAU
3) Cost-effectiveness + co-abatement (leakage avoided vs GHG reduction)
"""

from __future__ import annotations

import argparse
from pathlib import Path
import csv

import matplotlib.pyplot as plt


SCENARIO_LABELS = {
    "BAU": "Business-as-Usual",
    "CDS": "Collection & Disposal",
    "RES": "Recycling Expansion",
    "RSS": "Reduce & Substitute",
    "SCS": "System Change",
}

COLORS = {
    "BAU": "#4D4D4D",
    "CDS": "#2C7FB8",
    "RES": "#41AB5D",
    "RSS": "#F16913",
    "SCS": "#54278F",
}


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(v: str) -> float:
    if v is None or v == "":
        return float("nan")
    return float(v)


def fig1_bau(data_dir: Path, out_dir: Path):
    waste = [r for r in read_csv(data_dir / "plastic_waste_generation_annual_main.csv") if r["scenario"] == "BAU" and r["variant"] == "CENTRAL"]
    policy = [r for r in read_csv(data_dir / "annual_policy_trajectories.csv") if r["scenario"] == "BAU" and r["variant"] == "CENTRAL"]

    years = [int(r["year"]) for r in waste]
    waste_mt = [to_float(r["plastic_waste_generation_Mt"]) for r in waste]
    leakage_mt = [to_float(r["total_leakage_t"]) / 1e6 for r in policy]
    ghg_mt = [to_float(r["ghg_total"]) / 1e6 for r in policy]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharex=True)
    axes[0].plot(years, waste_mt, color=COLORS["BAU"], lw=2.2)
    axes[0].set_title("BAU waste generation")
    axes[0].set_ylabel("Mt/year")

    axes[1].plot(years, leakage_mt, color=COLORS["BAU"], lw=2.2)
    axes[1].set_title("BAU leakage")
    axes[1].set_ylabel("Mt/year")

    axes[2].plot(years, ghg_mt, color=COLORS["BAU"], lw=2.2)
    axes[2].set_title("BAU GHG")
    axes[2].set_ylabel("MtCO2e/year")

    for ax in axes:
        ax.set_xlabel("Year")
        ax.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(out_dir / "Fig1_BAU_baseline.png", dpi=300)
    plt.close(fig)


def fig2_interventions(data_dir: Path, out_dir: Path):
    rows = [r for r in read_csv(data_dir / "annual_policy_trajectories.csv") if r["variant"] == "CENTRAL"]
    by_scen = {}
    for r in rows:
        by_scen.setdefault(r["scenario"], []).append(r)
    for s in by_scen:
        by_scen[s].sort(key=lambda x: int(x["year"]))

    years = [int(r["year"]) for r in by_scen["BAU"]]
    bau_leak = [to_float(r["total_leakage_t"]) / 1e6 for r in by_scen["BAU"]]
    bau_ghg = [to_float(r["ghg_total"]) / 1e6 for r in by_scen["BAU"]]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)

    for s in ["CDS", "RES", "RSS", "SCS"]:
        leak = [to_float(r["total_leakage_t"]) / 1e6 for r in by_scen[s]]
        ghg = [to_float(r["ghg_total"]) / 1e6 for r in by_scen[s]]
        leak_delta = [b - x for b, x in zip(bau_leak, leak)]
        ghg_delta = [b - x for b, x in zip(bau_ghg, ghg)]
        axes[0].plot(years, leak_delta, label=s, color=COLORS[s], lw=2.2)
        axes[1].plot(years, ghg_delta, label=s, color=COLORS[s], lw=2.2)

    axes[0].set_title("Leakage reduction vs BAU")
    axes[0].set_ylabel("Mt/year avoided")
    axes[1].set_title("GHG reduction vs BAU")
    axes[1].set_ylabel("MtCO2e/year avoided")

    for ax in axes:
        ax.set_xlabel("Year")
        ax.grid(alpha=0.2)

    axes[1].legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "Fig2_Intervention_impacts.png", dpi=300)
    plt.close(fig)


def fig3_cost_coabatement(data_dir: Path, out_dir: Path):
    rows = [r for r in read_csv(data_dir / "policy_core_metrics.csv") if r["variant"] == "CENTRAL"]
    rows = sorted(rows, key=lambda r: ["BAU", "CDS", "RES", "RSS", "SCS"].index(r["scenario"]))

    scenarios = [r["scenario"] for r in rows if r["scenario"] != "BAU"]
    inv_per_t = [to_float(r["investment_per_t_avoided_pv_3_5_usd"]) for r in rows if r["scenario"] != "BAU"]

    annual = [r for r in read_csv(data_dir / "annual_policy_trajectories.csv") if r["variant"] == "CENTRAL"]
    by_scen = {}
    for r in annual:
        by_scen.setdefault(r["scenario"], []).append(r)

    ghg_red, leak_avoid = [], []
    bau_ghg = sum(to_float(r["ghg_total"]) for r in by_scen["BAU"])
    bau_leak = sum(to_float(r["total_leakage_t"]) for r in by_scen["BAU"])
    for s in scenarios:
        ghg_red.append((bau_ghg - sum(to_float(r["ghg_total"]) for r in by_scen[s])) / 1e6)
        leak_avoid.append((bau_leak - sum(to_float(r["total_leakage_t"]) for r in by_scen[s])) / 1e6)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].bar(scenarios, inv_per_t, color=[COLORS[s] for s in scenarios])
    axes[0].set_title("Cost-effectiveness (PV 3.5%)")
    axes[0].set_ylabel("USD per t leakage avoided")

    for s, x, y in zip(scenarios, leak_avoid, ghg_red):
        axes[1].scatter(x, y, s=90, color=COLORS[s], label=s)
        axes[1].annotate(s, (x, y), textcoords="offset points", xytext=(6, 4), fontsize=9)
    axes[1].set_title("Co-abatement vs BAU")
    axes[1].set_xlabel("Leakage avoided (Mt, cumulative)")
    axes[1].set_ylabel("GHG reduced (MtCO2e, cumulative)")
    axes[1].grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(out_dir / "Fig3_Cost_effectiveness_and_coabatement.png", dpi=300)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=Path("figure_pipeline/output"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    fig1_bau(args.data_dir, args.out_dir)
    fig2_interventions(args.data_dir, args.out_dir)
    fig3_cost_coabatement(args.data_dir, args.out_dir)
    print(f"Generated figures in: {args.out_dir}")


if __name__ == "__main__":
    main()
