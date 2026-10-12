"""Numbers for the post's reference-answer paragraph, from 06-rubrics/reference_scores.csv and reference_grades.jsonl.

  python s6b_numbers.py        # writes 06-rubrics/reference_numbers.json and prints it
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from paths import P1, SEED

R = P1 / "06-rubrics"
TYPES = ["openai_spec", "anthropic_spec", "preachy", "refusal", "shotgun", "warm_wrong"]


def main() -> None:
    s = pd.read_csv(R / "reference_scores.csv")
    rng = np.random.default_rng(SEED)
    out = {}

    def per_q(judge, scope):
        d = s[s.judge == judge]
        if scope is True:
            d = d[d.reviewed]
        elif scope == "unreviewed":
            d = d[~d.reviewed]
        return d.groupby(["question_id", "type"]).score.mean().unstack()[TYPES].dropna() * 100

    def ci(x):
        idx = rng.integers(0, len(x), size=(4000, len(x)))
        b = np.asarray(x)[idx].mean(axis=1)
        return [round(float(np.percentile(b, 2.5)), 1), round(float(np.percentile(b, 97.5)), 1)]

    for scope, rev in [("reviewed", True), ("unreviewed", "unreviewed"), ("all", False)]:
        for judge in ["pooled", "haiku", "luna", "jev"]:
            m = per_q(judge, rev)
            key = f"{scope}_{judge}"
            out[key] = {"n_questions": len(m), "mean": {t: round(float(m[t].mean()), 1) for t in TYPES},
                        "ci": {t: ci(m[t].values) for t in TYPES}}
            diffs = {}
            for spec in ["openai_spec", "anthropic_spec"]:
                for t in ["preachy", "refusal", "shotgun", "warm_wrong"]:
                    d = (m[t] - m[spec]).values
                    diffs[f"{t}-{spec}"] = {"diff": round(float(d.mean()), 1), "ci": ci(d), "ties_or_beats": int((d >= -1e-9).sum())}
            d = (m["anthropic_spec"] - m["openai_spec"]).values
            diffs["anthropic_spec-openai_spec"] = {"diff": round(float(d.mean()), 1), "ci": ci(d)}
            out[key]["diffs"] = diffs
    g = pd.DataFrame([json.loads(x) for x in open(R / "reference_grades.jsonl")]).dropna(subset=["grade"])
    dim = g.groupby(["dimension", "type"]).grade.mean().unstack()[TYPES]
    out["dimension_pass_rates_all"] = {d: {t: round(float(v), 3) for t, v in row.items()} for d, row in dim.iterrows()}
    out["n_grades"] = int(len(g))
    # how many of the 30 sampled questions carry each criterion, and per-judge pass rates for Moral Consideration
    nq = g.groupby("dimension").question_id.nunique()
    out["questions_per_dimension"] = {k: int(v) for k, v in nq.items()}
    mc = g[g.dimension == "Moral Consideration"].groupby(["judge", "type"]).grade.mean().unstack()[TYPES]
    out["moral_consideration_by_judge"] = {j: {t: round(float(v), 3) for t, v in row.items()} for j, row in mc.iterrows()}
    (R / "reference_numbers.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k]["mean"] for k in ["reviewed_pooled", "unreviewed_pooled", "all_pooled"]}, indent=1))


if __name__ == "__main__":
    main()
