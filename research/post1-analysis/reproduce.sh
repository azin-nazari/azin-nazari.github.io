#!/usr/bin/env bash
# Rebuild every table and figure in the post from the saved outputs in this folder, then check the post's numbers.
# No model calls and no API key. Tested with Python 3.13 and the packages in requirements-analysis.txt:
#   python -m venv .venv && . .venv/bin/activate && pip install -r requirements-analysis.txt && bash reproduce.sh
set -euo pipefail
cd "$(dirname "$0")/scripts"
python s4_coverage_summary.py   > /dev/null   # 04-coverage/coverage_summary.md, coverage_by_commitment.csv
python s5_author_compare.py     > /dev/null   # 05-realism/author_vs_llm*.csv
python s6b_numbers.py           > /dev/null   # 06-rubrics/reference_numbers.json
python s6c_summary.py           > /dev/null   # 06-rubrics/helpfulness_summary.md, helpfulness_effects.csv, helpfulness_sensitivity.csv
python s10_models.py            > /dev/null   # 10-models/*.csv, numbers.json
python s10_examples.py          > /dev/null   # 10-models/examples.md
python s11_explorer_data.py     > /dev/null   # 09-post/explorer/summary.json, items_<model>.json (the post's model explorer)
python s12_jev.py               > /dev/null   # 10-models/jev_agreement.csv, jev_numbers.json
python s13_resolution.py        > /dev/null   # 10-models/resolution.json
python s9_figures.py all                      # 09-post/figures/*.svg
python check_numbers.py                       # every checked number in 09-post/post1_final.md matches the files above
