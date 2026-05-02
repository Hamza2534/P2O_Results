# Jupyter Notebook Execution Guide (Step-by-step)

This guide shows how to run and iterate the figure pipeline entirely in Jupyter.

## 1) Launch Jupyter from repository root
```bash
cd P2O_Results
jupyter notebook
```
Create a new Python notebook.

## 2) Install dependency in the notebook kernel
Run in first cell:
```python
%pip install matplotlib
```

## 3) Import pipeline
```python
from pathlib import Path
from figure_pipeline.scripts.generate_storyline_figures import generate_all_figures, DEFAULT_STYLE
```

## 4) Generate all figures and show inline
```python
out_dir = generate_all_figures(
    data_dir='.',
    out_dir='figure_pipeline/output',
    style=DEFAULT_STYLE,
    show_inline=True,
)
print('Saved to:', out_dir)
```

## 5) Verify output files
```python
sorted([p.name for p in Path('figure_pipeline/output').glob('*.png')])
```

Expected:
- `Fig1_BAU_baseline.png`
- `Fig2_Intervention_impacts.png`
- `Fig3_Cost_effectiveness_and_coabatement.png`

## 6) Iterate style quickly in notebook
```python
custom = dict(DEFAULT_STYLE)
custom['line_width'] = 2.8
custom['figure_dpi'] = 350
custom['scenario_colors'] = dict(DEFAULT_STYLE['scenario_colors'])
custom['scenario_colors']['SCS'] = '#6A3D9A'

generate_all_figures(data_dir='.', out_dir='figure_pipeline/output', style=custom, show_inline=True)
```

## 7) Regenerate after script edits
If you modify `figure_pipeline/scripts/generate_storyline_figures.py`, reload in notebook:
```python
import importlib
import figure_pipeline.scripts.generate_storyline_figures as figs
importlib.reload(figs)

figs.generate_all_figures(data_dir='.', out_dir='figure_pipeline/output', show_inline=True)
```

## 8) Optional: run via terminal wrappers
```bash
bash figure_pipeline/run_figures.sh . figure_pipeline/output
```
or
```bash
cd figure_pipeline
make figures
```

## Notes
- Scenario framing is fixed: BAU baseline, interventions = CDS/RES/RSS/SCS.
- Figures are overwritten each run for deterministic iteration.
