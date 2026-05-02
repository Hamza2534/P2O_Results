#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${1:-.}"
OUT_DIR="${2:-figure_pipeline/output}"

python figure_pipeline/scripts/generate_storyline_figures.py --data-dir "$DATA_DIR" --out-dir "$OUT_DIR"
