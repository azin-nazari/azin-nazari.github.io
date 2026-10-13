"""Data for the post's model explorer. No model calls; reads saved files only.

  python s11_explorer_data.py [--anima-dir DIR]   # writes 09-post/explorer/{summary.json, items_<model>.json}

Writes the data the explorer loads (the grader rationales come from s11_rationales.py).

Inputs: 10-models/verdicts.csv.gz, answers.jsonl.gz, model_scores.csv, model_helpfulness.csv, judge_pass_rates.csv,
06-rubrics/helpfulness_grades.csv, 10-models/helpfulness_grades_models.csv, and the ANIMA 2.2 questions (for the English
translations of non-English questions; a copy is kept as 10-models/anima_questions_2.2.jsonl, CC BY-NC 4.0, CompassioninMachineLearning).

Everything is epoch 1 (one answer per question per model), as in the post. Jev verdicts carry their probability; a pass is
P >= 0.5. GPT-6 Luna graded only the two judge-study models, which the explorer shows as missing for the other four.
"""

from __future__ import annotations

import argparse
import gzip
import json

import numpy as np
import pandas as pd

from paths import ANIMA_DIR, P1, SEED

M = P1 / "10-models"
OUT = P1 / "09-post" / "explorer"
MODELS = ["GPT-6.1 Sol", "Qwen3.8 2.4T A95B", "Claude Sonnet 5.5", "DeepSeek V4 Pro", "Gemini 3.8 Flash", "GLM-5.3"]
INFO = {  # developer, weights, OpenRouter id, note
    "Claude Sonnet 5.5": ("Anthropic", "closed", "anthropic/claude-sonnet-5.5", ""),
    "Gemini 3.8 Flash": ("Google", "closed", "google/gemini-3.8-flash", "a lower-cost tier than the Anthropic and OpenAI models here"),
    "GPT-6.1 Sol": ("OpenAI", "closed", "openai/gpt-6.1-sol", ""),
    "DeepSeek V4 Pro": ("DeepSeek", "open weights", "deepseek/deepseek-v4-pro", "also wrote the reference answers used to test the judges"),
    "Qwen3.8 2.4T A95B": ("Qwen (Alibaba)", "open weights", "qwen/qwen3.8-2.4t-a95b", ""),
    "GLM-5.3": ("Z.ai", "open weights", "z-ai/glm-5.3", ""),
}
SLUG = {"Claude Sonnet 5.5": "claude-sonnet-5.5", "Gemini 3.8 Flash": "gemini-3.8-flash", "GPT-6.1 Sol": "gpt-6.1-sol",
        "DeepSeek V4 Pro": "deepseek-v4-pro", "Qwen3.8 2.4T A95B": "qwen3.8-2.4t-a95b", "GLM-5.3": "glm-5.3"}
JUDGES = ["Claude Haiku 5.5", "Gemini 3.5 Flash-Lite", "Jev 1.13", "GPT-6 Luna"]
INLINE = ["Claude Haiku 5.5", "Gemini 3.5 Flash-Lite"]
SCORERS = {"panel": "Panel: Claude Haiku 5.5 + Gemini 3.5 Flash-Lite, votes averaged", "Claude Haiku 5.5": "Claude Haiku 5.5 alone",
           "Gemini 3.5 Flash-Lite": "Gemini 3.5 Flash-Lite alone", "Jev 1.13": "Jev 1.13 alone", "GPT-6 Luna": "GPT-6 Luna alone"}


def r1(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 1)


def main(anima_dir) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    qfile = anima_dir / "questions.jsonl" if (anima_dir / "questions.jsonl").exists() else M / "anima_questions_2.2.jsonl"
    qs = {q["id"]: q for q in map(json.loads, open(qfile))}
    if qfile != M / "anima_questions_2.2.jsonl":
        with open(M / "anima_questions_2.2.jsonl", "w") as f:
            for q in qs.values():
                f.write(json.dumps(q, ensure_ascii=False) + "\n")
    v = pd.read_csv(M / "verdicts.csv.gz")
    v = v[v.epoch == 1]
    sc = pd.read_csv(M / "model_scores.csv")
    hm = pd.read_csv(M / "model_helpfulness.csv")

    # ---- summary: scores per scorer (Luna: two models only, recomputed here with the same bootstrap as s10_models)
    scores = {}
    for key, label in SCORERS.items():
        name = "Panel" if key == "panel" else key + " alone"
        rows = sc[sc.scorer.str.startswith(name)] if key != "panel" else sc[sc.scorer.str.startswith("Panel")]
        if len(rows):
            scores[key] = {r.model: {"score": r.score, "lo": r.ci_lo, "hi": r.ci_hi, "rank": int(r["rank"]), "rank_lo": int(r.rank_lo),
                                     "rank_hi": int(r.rank_hi), "n": int(r.n_questions)} for _, r in rows.iterrows()}
    # GPT-6 Luna: score the two models it graded, same aggregation, question bootstrap
    lv = v[v.judge == "GPT-6 Luna"]
    if len(lv):
        d = lv.groupby(["model", "sample_id", "dimension"])["pass"].mean().groupby(["model", "sample_id"]).mean()
        mat = (100 * d).unstack("model").dropna()
        rng = np.random.default_rng(SEED)
        idx = rng.integers(0, len(mat), size=(2000, len(mat)))
        bm = mat.values[idx].mean(axis=1)
        scores["GPT-6 Luna"] = {m: {"score": r1(mat[m].mean()), "lo": r1(np.percentile(bm[:, k], 2.5)), "hi": r1(np.percentile(bm[:, k], 97.5)),
                                    "rank": None, "rank_lo": None, "rank_hi": None, "n": int(len(mat))} for k, m in enumerate(mat.columns)}
    # criterion pass rates per model and scorer
    crit = {}
    for key in SCORERS:
        d = v[v.judge.isin(INLINE)] if key == "panel" else v[v.judge == key]
        if d.empty:
            continue
        pr = d.groupby(["model", "dimension"])["pass"].mean().unstack()
        n = d[d.judge == d.judge.iloc[0]].groupby(["model", "dimension"]).size().unstack()
        crit[key] = {m: {c: {"rate": r1(100 * pr.loc[m, c]), "n": int(n.loc[m, c])} for c in pr.columns if not np.isnan(pr.loc[m, c])}
                     for m in pr.index}
    flags = {}
    for _, r in hm.iterrows():
        flags.setdefault(r.model, {})[r.judge] = {"share": r1(100 * r.moralizing_share), "lo": r1(100 * r.moralizing_ci_lo),
                                                  "hi": r1(100 * r.moralizing_ci_hi), "n": int(r.n_answers),
                                                  "completes": r1(100 * r.completes_share), "bare_refusals": int(r.bare_refusals),
                                                  "words": int(r.mean_words)}
    summary = {
        "models": [{"name": m, "slug": SLUG[m], "developer": INFO[m][0], "weights": INFO[m][1], "openrouter": INFO[m][2], "note": INFO[m][3]}
                   for m in MODELS],
        "scorers": [{"key": k, "label": SCORERS[k], "models_graded": sorted(scores.get(k, {}).keys())} for k in SCORERS if k in scores],
        "scores": scores, "criteria": crit, "flags": flags,
        "settings": "One answer per question (114 ANIMA 2.2 questions, epoch 1), provider default temperature, run through OpenRouter "
                    "with inspect_evals 0.24.0 on 10 Oct (Claude Sonnet 5.5, Gemini 3.8 Flash) and 12 Oct 2026 (the other four).",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))

    # ---- per-model items
    ans = pd.DataFrame([json.loads(x) for x in gzip.open(M / "answers.jsonl.gz", "rt")])
    ans = ans[ans.epoch == 1]
    lab = pd.concat([pd.read_csv(P1 / "06-rubrics/helpfulness_grades.csv"), pd.read_csv(M / "helpfulness_grades_models.csv")])
    lab = lab[lab.epoch == 1]
    jn = {"claude-haiku-5.5": "Claude Haiku 5.5", "gpt-6-luna": "GPT-6 Luna"}
    for m in MODELS:
        vm = v[v.model == m]
        per = vm.groupby(["sample_id", "dimension", "judge"]).agg(p=("pass", "mean"), g=("grade", "mean")).reset_index()
        panel = vm[vm.judge.isin(INLINE)].groupby(["sample_id", "dimension"])["pass"].mean().groupby("sample_id").mean() * 100
        lm = lab[lab.model == SLUG[m]]
        items = []
        for _, a in ans[ans.model == m].sort_values("sample_id").iterrows():
            sid = int(a.sample_id)
            q = qs.get(sid, {})
            crits = {}
            for _, r in per[per.sample_id == sid].iterrows():
                val = round(float(r.g), 2) if r.judge == "Jev 1.13" else r1(r.p)   # Jev: its probability, as given (two decimals)
                crits.setdefault(r.dimension, {})[r.judge] = val
            labels = {}
            for _, r in lm[lm.sample_id == sid].iterrows():
                if r.ok:
                    labels[jn[r.judge]] = {"moralizing": r.unrequested_moralizing, "completes": r.completes_task, "refusal": r.bare_refusal,
                                           "reason": r.reason}
            items.append({"id": sid, "lang": a.language or "English", "q": a.question, "q_en": q.get("translation"),
                          "answer": a.answer, "words": len(a.answer.split()), "score": r1(panel.get(sid)), "criteria": crits, "labels": labels})
        (OUT / f"items_{SLUG[m]}.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")))
        print(m, len(items))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--anima-dir", default=str(ANIMA_DIR))
    from pathlib import Path
    main(Path(ap.parse_args().anima_dir))
