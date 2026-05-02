# Figure pipeline for article storyline

This pipeline generates publication-ready figures directly from the CSV outputs in this repository.

## Storyline covered
1. **BAU baseline**: waste generation, leakage, and GHG emissions over time.
2. **Intervention effects**: how CDS/RES/RSS/SCS change leakage and GHG relative to BAU.
3. **Economics + co-abatement**: cost-effectiveness and joint GHG + leakage abatement.

## Quick start
```bash
python figure_pipeline/scripts/generate_storyline_figures.py \
  --data-dir . \
  --out-dir figure_pipeline/output
```

## Iteration workflow
- Edit styling in `figure_pipeline/config/style.yaml`.
- Edit chart logic in `figure_pipeline/scripts/generate_storyline_figures.py`.
- Re-run the command above; outputs are overwritten deterministically.

## Outputs
- `Fig1_BAU_baseline.png`
- `Fig2_Intervention_impacts.png`
- `Fig3_Cost_effectiveness_and_coabatement.png`

You can re-run at any time to regenerate all figures after visual tweaks.
