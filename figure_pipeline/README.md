# Figure pipeline (Jupyter-first workflow)

This pipeline is designed to be run **inside Jupyter Notebook** for rapid visual iteration.

## Notebook quick start
In a notebook cell from repo root:
```python
%pip install matplotlib
from figure_pipeline.scripts.generate_storyline_figures import generate_all_figures

out_dir = generate_all_figures(data_dir='.', out_dir='figure_pipeline/output', show_inline=True)
out_dir
```

Generated files:
- `figure_pipeline/output/Fig1_BAU_baseline.png`
- `figure_pipeline/output/Fig2_Intervention_impacts.png`
- `figure_pipeline/output/Fig3_Cost_effectiveness_and_coabatement.png`

## Storyline coverage
1. BAU baseline: waste generation, leakage, GHG.
2. Intervention deltas: CDS/RES/RSS/SCS vs BAU.
3. Net system cost vs BAU (negative axis for savings) and co-abatement.

## Optional CLI usage
```bash
python figure_pipeline/scripts/generate_storyline_figures.py --data-dir . --out-dir figure_pipeline/output
```
