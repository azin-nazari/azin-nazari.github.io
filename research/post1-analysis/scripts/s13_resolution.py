"""How precise are the model comparisons, and what would make them more precise? No model calls.

  python s13_resolution.py      # writes 10-models/resolution.json

1. For the two models that answered every question five times, the 95% interval of the panel score with one answer per
   question versus all five (resampling questions, as everywhere in the post).
2. How much of the spread is between questions versus between answers to the same question.
3. For all 15 model pairs, the interval of the difference computed on the same questions (paired) versus from the two
   models' separate scores (unpaired).
"""

from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

from paths import P1, SEED

M = P1 / "10-models"
INLINE = ["Claude Haiku 5.5", "Gemini 3.5 Flash-Lite"]
B = 2000


def answer_scores(v: pd.DataFrame) -> pd.Series:
    """ANIMA panel score per model, question and answer (epoch), 0-100."""
    return v.groupby(["model", "sample_id", "epoch", "dimension"])["pass"].mean().groupby(["model", "sample_id", "epoch"]).mean() * 100


def halfwidth(x: np.ndarray, rng) -> float:
    idx = rng.integers(0, len(x), size=(B, len(x)))
    b = x[idx].mean(axis=1)
    return float((np.percentile(b, 97.5) - np.percentile(b, 2.5)) / 2)


def main() -> None:
    rng = np.random.default_rng(SEED)
    v = pd.read_csv(M / "verdicts.csv.gz")
    v = v[v.judge.isin(INLINE)]
    a = answer_scores(v)
    out = {"by_answers_per_question": {}, "variance": {}}
    for model in ["Claude Sonnet 5.5", "Gemini 3.8 Flash"]:
        x = a.loc[model].unstack("epoch")
        one = x[1].dropna().values
        five = x.mean(axis=1).values
        out["by_answers_per_question"][model] = {"one_answer_halfwidth": round(halfwidth(one, rng), 1),
                                                 "five_answers_halfwidth": round(halfwidth(five, rng), 1)}
        within = float(x.var(axis=1).mean())
        between = float(x.mean(axis=1).var())
        out["variance"][model] = {"within_question": round(within, 1), "between_questions": round(between, 1),
                                  "ratio": round(between / within, 1)}
    q = a.xs(1, level="epoch").unstack("model").dropna()
    paired, unpaired = [], []
    for m1, m2 in itertools.combinations(q.columns, 2):
        d = (q[m1] - q[m2]).values
        paired.append(halfwidth(d, rng))
        i1 = rng.integers(0, len(q), size=(B, len(q)))
        i2 = rng.integers(0, len(q), size=(B, len(q)))
        bd = q[m1].values[i1].mean(axis=1) - q[m2].values[i2].mean(axis=1)
        unpaired.append(float((np.percentile(bd, 97.5) - np.percentile(bd, 2.5)) / 2))
    out["pairs"] = {"n_pairs": len(paired), "paired_halfwidth_mean": round(float(np.mean(paired)), 1),
                    "paired_halfwidth_range": [round(min(paired), 1), round(max(paired), 1)],
                    "unpaired_halfwidth_mean": round(float(np.mean(unpaired)), 1)}
    (M / "resolution.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
