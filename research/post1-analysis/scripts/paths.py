"""Paths and constants shared by every script. Pure Python: no model access needed.

Scripts that only read saved outputs import this module (not common.py), so they run with the packages in
requirements-analysis.txt alone. See README.md, "Reproduce the tables and figures".
"""

from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent                      # post1-analysis/
SEED = 20261011                       # every resampling uses this seed

# Public inputs that are not stored in this folder (downloaded by fetch_public_inputs.py). Override with environment variables.
EXT = Path(os.environ.get("POST1_EXT", P1 / "_ext"))            # MCB logs, Model Spec repo, Hugging Face files
ANIMA_DIR = Path(os.environ.get("ANIMA_DIR", EXT / "anima"))     # questions.jsonl, dimensions.jsonl (dataset 2.2)
