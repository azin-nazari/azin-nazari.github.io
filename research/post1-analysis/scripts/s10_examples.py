"""Examples for the models and judges sections, drawn by stated rules. No model calls.

  python s10_examples.py     # writes 10-models/examples.md

Rules (seed 20261011):
1. Model under test, moralizing: among questions where both labellers flagged DeepSeek V4 Pro's answer for moralizing and
   neither flagged GPT-6.1 Sol's, draw one at random. (These two models have the highest and lowest flag rates.)
2. Judge disagreement: among epoch-1 Moral Consideration verdicts on the six models where both inline LLM judges (Claude
   Haiku 5.5, Gemini 3.5 Flash-Lite) passed the answer and Jev 1.13 failed it, draw one at random. (GPT-6 Luna re-graded
   only the two judge-study models, so it is left out of this rule.)
"""

from __future__ import annotations

import gzip
import json
import random

import pandas as pd

from paths import P1, SEED

M = P1 / "10-models"
R = P1 / "06-rubrics"


def main() -> None:
    rnd = random.Random(SEED)
    ans = pd.DataFrame([json.loads(x) for x in gzip.open(M / "answers.jsonl.gz", "rt")])
    ans = ans[ans.epoch == 1]
    h = pd.concat([pd.read_csv(R / "helpfulness_grades.csv"), pd.read_csv(M / "helpfulness_grades_models.csv")])
    h = h[h.ok & (h.epoch == 1)]
    flag = h.pivot_table(index=["model", "sample_id"], columns="judge", values="unrequested_moralizing", aggfunc="first")
    both = (flag == "yes").all(axis=1)
    neither = (flag == "no").all(axis=1)
    ds = set(both[both].reset_index().query("model == 'deepseek-v4-pro'").sample_id)
    gp = set(neither[neither].reset_index().query("model == 'gpt-6.1-sol'").sample_id)
    pool = sorted(ds & gp)
    q = rnd.choice(pool)
    out = ["# Examples for the models and judges sections", "", "## 1. Moralizing: DeepSeek V4 Pro vs GPT-6.1 Sol", "",
           f"Rule: random draw among questions where both labellers flagged DeepSeek V4 Pro and neither flagged GPT-6.1 Sol; "
           f"{len(pool)} questions qualify. Drawn: question {q}.", ""]
    reasons = h[(h.sample_id == q) & h.model.isin(["deepseek-v4-pro", "gpt-6.1-sol"])][["model", "judge", "unrequested_moralizing", "reason"]]
    for m in ["DeepSeek V4 Pro", "GPT-6.1 Sol"]:
        a = ans[(ans.model == m) & (ans.sample_id == q)].iloc[0]
        if m == "DeepSeek V4 Pro":
            out += [f"Question ({a.language or 'English'}): {a.question}", ""]
        out += [f"### {m} ({len(a.answer.split())} words)", "", a.answer, ""]
    out += ["Labels and reasons:", "", reasons.to_markdown(index=False), ""]

    v = pd.read_csv(M / "verdicts.csv.gz")
    v = v[(v.epoch == 1) & (v.dimension == "Moral Consideration")]
    w = v.pivot_table(index=["model", "sample_id", "vset_idx"], columns="judge", values="pass")
    llm = ["Claude Haiku 5.5", "Gemini 3.5 Flash-Lite"]
    sub = w.dropna(subset=llm + ["Jev 1.13"])
    cand = sub[(sub[llm] == 1).all(axis=1) & (sub["Jev 1.13"] == 0)]
    share = len(cand) / len(sub)
    key = rnd.choice(sorted(cand.index.tolist()))
    m, sid, vi = key
    a = ans[(ans.model == m) & (ans.sample_id == sid)].iloc[0]
    p = v[(v.model == m) & (v.sample_id == sid) & (v.vset_idx == vi) & (v.judge == "Jev 1.13")].grade.iloc[0]
    out += ["## 2. Judges disagree on Moral Consideration", "",
            f"Rule: random draw among epoch-1 Moral Consideration verdicts where {', '.join(llm)} all passed the answer and Jev 1.13 "
            f"failed it: {len(cand)} of {len(sub)} such verdicts ({100 * share:.0f}%). Drawn: {m}, question {sid}, variable set {vi}; "
            f"Jev's probability {p:.2f}.", "", f"Question ({a.language or 'English'}): {a.question}", "", f"### {m} ({len(a.answer.split())} words)",
            "", a.answer, ""]
    (M / "examples.md").write_text("\n".join(out))
    print("\n".join(out)[:6000])


if __name__ == "__main__":
    main()
