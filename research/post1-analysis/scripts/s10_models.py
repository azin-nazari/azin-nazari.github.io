"""Models under test and judges. No model calls; reads saved files only.

  python s10_models.py

Inputs
- 10-models/verdicts.csv.gz          (s10_export.py): every criterion verdict for six models, four judges
- 06-rubrics/helpfulness_grades.csv, 10-models/helpfulness_grades_models.csv: moralizing / completion / refusal labels
- 06-rubrics/reference_scores.csv, reference_grades.jsonl: the reference-answer test (three judges, three rounds)
Outputs (10-models/)
- model_scores.csv     ANIMA score per model under each scorer, 95% interval and rank interval
- model_pairs.csv      every pairwise model difference under the default panel, 95% interval
- judge_pairs.csv      pairwise agreement and Cohen's kappa between judges on identical verdicts
- judge_vs_others.csv  each judge against the majority of the other three
- judge_pass_rates.csv pass rate per judge, overall and per criterion
- model_helpfulness.csv labels per model (share flagged for moralizing, completion, bare refusals, answer length)
- judge_reference.csv  per judge: score of each intended-failure answer minus the excerpt-conditioned answers
- judge_retest.csv     per judge: agreement with itself across the three grading rounds of the reference test
- numbers.json         every number the post quotes from this step

Answers: one per question per model (epoch 1) for all six models; the 10 Oct judge study's other four epochs are not used
here. GPT-6 Luna's ANIMA grades exist only for the two judge-study models (epoch 1), so per-judge model scores use the
three judges that graded all six, and judge agreement is computed pairwise on every verdict both judges made.
Conventions: scores follow ANIMA's aggregation (judges and variable sets averaged per criterion, criteria averaged per
answer, answers averaged per question, questions averaged per model). Jev returns P(criterion met); a verdict counts as a
pass when P >= 0.5. Uncertainty: 2,000 resamples of questions (paired across models), seed 20261011.
"""

from __future__ import annotations

import itertools
import json

import numpy as np
import pandas as pd

from paths import P1, SEED

M = P1 / "10-models"
R = P1 / "06-rubrics"
MODELS = ["Claude Sonnet 5.5", "Gemini 3.8 Flash", "GPT-6.1 Sol", "DeepSeek V4 Pro", "Qwen3.8 2.4T A95B", "GLM-5.3"]
INLINE = ["Claude Haiku 5.5", "Gemini 3.5 Flash-Lite"]
JUDGES = INLINE + ["GPT-6 Luna", "Jev 1.13"]
B = 2000
OUT: dict = {}


def kappa(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    po = np.mean(a == b)
    pe = np.mean(a) * np.mean(b) + (1 - np.mean(a)) * (1 - np.mean(b))
    return float("nan") if pe == 1 else float((po - pe) / (1 - pe))


def kendall(x, y) -> float:
    """Kendall's tau-a over model pairs (no ties expected in six scores)."""
    s = [np.sign(x[i] - x[j]) * np.sign(y[i] - y[j]) for i, j in itertools.combinations(range(len(x)), 2)]
    return float(np.mean(s))


def q_scores(v: pd.DataFrame) -> pd.DataFrame:
    """question x model matrix of ANIMA scores (0-100) from a verdict table."""
    d = v.groupby(["model", "sample_id", "epoch", "dimension"])["pass"].mean()
    d = d.groupby(["model", "sample_id", "epoch"]).mean().groupby(["model", "sample_id"]).mean()
    return (100 * d).unstack("model")[MODELS].dropna()


def boot_idx(n: int, rng) -> np.ndarray:
    return rng.integers(0, n, size=(B, n))


def scores_block(name: str, mat: pd.DataFrame, rng) -> list[dict]:
    idx = boot_idx(len(mat), rng)
    bm = mat.values[idx].mean(axis=1)                         # B x models
    ranks = (-bm).argsort(axis=1).argsort(axis=1) + 1         # 1 = highest score
    point = mat.mean()
    prank = point.rank(ascending=False, method="min").astype(int)
    rows = []
    for k, m in enumerate(MODELS):
        rows.append({"scorer": name, "model": m, "score": round(float(point[m]), 1),
                     "ci_lo": round(float(np.percentile(bm[:, k], 2.5)), 1), "ci_hi": round(float(np.percentile(bm[:, k], 97.5)), 1),
                     "rank": int(prank[m]), "rank_lo": int(np.percentile(ranks[:, k], 2.5)), "rank_hi": int(np.percentile(ranks[:, k], 97.5)),
                     "n_questions": int(len(mat))})
    return rows


def models_and_judges(v: pd.DataFrame, rng) -> None:
    v = v[v.study.isin(["judge_study", "more_models"]) & (v.epoch == 1)]
    # default ANIMA configuration in our runs: the two inline judges. One answer per question for every model (epoch 1):
    # the 12 Oct runs stopped at the key's credit cap after epoch 1, so epoch 2 exists only for some answers.
    panel = q_scores(v[v.judge.isin(INLINE) & (v.epoch == 1)])
    rows = scores_block("Panel: Claude Haiku 5.5 + Gemini 3.5 Flash-Lite (1 answer per question)", panel, rng)
    # each judge alone, on the identical epoch-1 answers (GPT-6 Luna graded epoch 1 only)
    per_judge = {}
    for j in JUDGES:
        if set(v[v.judge == j].model.unique()) != set(MODELS):
            print(f"skipping {j}: verdicts for {sorted(v[v.judge == j].model.unique())}")
            continue
        per_judge[j] = q_scores(v[(v.judge == j) & (v.epoch == 1)])
        rows += scores_block(j + " alone (1 answer per question)", per_judge[j], rng)
    sc = pd.DataFrame(rows)
    sc.to_csv(M / "model_scores.csv", index=False)

    idx = boot_idx(len(panel), rng)
    pr = []
    for a, b in itertools.combinations(MODELS, 2):
        d = (panel[a] - panel[b]).values
        bd = d[idx].mean(axis=1)
        lo, hi = np.percentile(bd, [2.5, 97.5])
        pr.append({"model_a": a, "model_b": b, "diff": round(float(d.mean()), 1), "ci_lo": round(float(lo), 1), "ci_hi": round(float(hi), 1),
                   "distinguishable": bool(lo > 0 or hi < 0)})
    pairs = pd.DataFrame(pr)
    pairs.to_csv(M / "model_pairs.csv", index=False)

    # judge dependence of model scores
    pj = sc[~sc.scorer.str.startswith("Panel")].copy()
    pj["judge"] = pj.scorer.str.replace(" alone (1 answer per question)", "", regex=False)
    JP = [j for j in JUDGES if j in set(pj.judge)]
    wide = pj.pivot(index="model", columns="judge", values="score")[JP]
    rng_by_model = (wide.max(axis=1) - wide.min(axis=1)).round(1)
    rank_w = pj.pivot(index="model", columns="judge", values="rank")[JP]
    taus = {f"{a} vs {b}": round(kendall(wide[a].to_numpy(), wide[b].to_numpy()), 2) for a, b in itertools.combinations(JP, 2)}
    # same-developer check: does a judge score its own developer's model higher than the other judges do, relative to
    # how it scores the other models? offset = (judge - mean of other judges) on the own model minus the same on the rest
    own = {"Claude Haiku 5.5": "Claude Sonnet 5.5", "Gemini 3.5 Flash-Lite": "Gemini 3.8 Flash", "GPT-6 Luna": "GPT-6.1 Sol"}
    jl = list(per_judge)
    qs = sorted(set.intersection(*[set(per_judge[j].index) for j in jl]))
    mats = {j: per_judge[j].loc[qs, MODELS].to_numpy() for j in jl}
    idx = boot_idx(len(qs), rng)
    same_dev = {}
    for j, m in own.items():
        if j not in mats:
            continue
        others = [o for o in jl if o != j]
        k = MODELS.index(m)

        def stat(ix):
            dev = mats[j][ix].mean(axis=-2) - np.mean([mats[o][ix].mean(axis=-2) for o in others], axis=0)
            return dev[..., k] - np.delete(dev, k, axis=-1).mean(axis=-1)
        pt = float(stat(np.arange(len(qs))))
        bs = stat(idx)
        same_dev[j] = {"own_model": m, "offset": round(pt, 1), "ci": [round(float(np.percentile(bs, 2.5)), 1), round(float(np.percentile(bs, 97.5)), 1)]}
    OUT["models"] = {
        "same_developer_offset": same_dev,
        "panel": sc[sc.scorer.str.startswith("Panel")].set_index("model")[["score", "ci_lo", "ci_hi", "rank", "rank_lo", "rank_hi"]].to_dict(orient="index"),
        "by_judge_scores": wide.round(1).to_dict(orient="index"),
        "by_judge_ranks": rank_w.to_dict(orient="index"),
        "judge_range_by_model": rng_by_model.to_dict(),
        "judge_range_max": float(rng_by_model.max()), "judge_range_min": float(rng_by_model.min()),
        "kendall_tau_between_judges": taus,
        "n_pairs": int(len(pairs)), "n_distinguishable_pairs": int(pairs.distinguishable.sum()),
        "pairs_distinguishable": pairs[pairs.distinguishable][["model_a", "model_b", "diff", "ci_lo", "ci_hi"]].to_dict(orient="records"),
        "n_questions": int(len(panel)),
    }

    # agreement on identical verdicts (epoch 1, all six models)
    full = v[v.epoch == 1].pivot_table(index=["model", "sample_id", "dimension", "vset_idx"], columns="judge", values="pass")
    full = full[[j for j in JUDGES if j in full.columns]]
    jp = []
    for a, b in itertools.combinations(full.columns, 2):          # pairwise-complete: every verdict both judges made
        x = full[[a, b]].dropna()
        jp.append({"judge_a": a, "judge_b": b, "agreement": round(float(np.mean(x[a] == x[b])), 3), "kappa": round(kappa(x[a], x[b]), 2),
                   "n_verdicts": int(len(x)), "models": int(x.reset_index().model.nunique())})
    jp = pd.DataFrame(jp)
    e1 = full.dropna()                                            # rows where all four judges gave a verdict
    jp.to_csv(M / "judge_pairs.csv", index=False)
    vo = []
    for j in JUDGES:
        others = [o for o in JUDGES if o != j]
        s = e1[others].sum(axis=1)
        maj = e1[others].mean(axis=1)
        ok = s.isin([0, 3]) | s.isin([1, 2]) & (maj != 0.5)          # three others: always a majority
        m = (maj >= 0.5).astype(float)
        unanimous = s.isin([0, 3])
        vo.append({"judge": j, "agree_with_majority_of_others": round(float(np.mean(e1[j][ok] == m[ok])), 3),
                   "kappa_with_majority": round(kappa(e1[j][ok], m[ok]), 2),
                   "agree_when_others_unanimous": round(float(np.mean(e1[j][unanimous] == m[unanimous])), 3),
                   "share_others_unanimous": round(float(unanimous.mean()), 3),
                   "pass_rate": round(float(e1[j].mean()), 3)})
    vo = pd.DataFrame(vo)
    vo.to_csv(M / "judge_vs_others.csv", index=False)
    long = e1.reset_index().melt(id_vars=["model", "sample_id", "dimension", "vset_idx"], var_name="judge", value_name="pass")
    pr_dim = long.groupby(["dimension", "judge"])["pass"].mean().unstack()[JUDGES]
    pr_dim["spread"] = pr_dim[JUDGES].max(axis=1) - pr_dim[JUDGES].min(axis=1)
    pr_dim["n_verdicts"] = long[long.judge == JUDGES[0]].groupby("dimension").size()
    pr_dim.round(3).to_csv(M / "judge_pass_rates.csv")
    llm_pairs = jp[~jp.judge_a.eq("Jev 1.13") & ~jp.judge_b.eq("Jev 1.13")]
    jev_pairs = jp[jp.judge_a.eq("Jev 1.13") | jp.judge_b.eq("Jev 1.13")]
    OUT["judges"] = {
        "n_verdicts_all_four": int(len(e1)), "models_all_four": int(e1.reset_index().model.nunique()),
        "pairs": jp.to_dict(orient="records"),
        "llm_llm_agreement_range": [float(llm_pairs.agreement.min()), float(llm_pairs.agreement.max())],
        "llm_llm_kappa_range": [float(llm_pairs.kappa.min()), float(llm_pairs.kappa.max())],
        "jev_agreement_range": [float(jev_pairs.agreement.min()), float(jev_pairs.agreement.max())],
        "jev_kappa_range": [float(jev_pairs.kappa.min()), float(jev_pairs.kappa.max())],
        "vs_others": vo.set_index("judge").to_dict(orient="index"),
        "largest_criterion_spreads": pr_dim.spread.sort_values(ascending=False).head(4).round(3).to_dict(),
        "pass_rates_by_criterion": pr_dim[JUDGES].round(3).to_dict(orient="index"),
    }


def helpfulness_by_model(rng) -> None:
    frames = [pd.read_csv(R / "helpfulness_grades.csv")]
    p = M / "helpfulness_grades_models.csv"
    if p.exists():
        frames.append(pd.read_csv(p))
    g = pd.concat(frames, ignore_index=True)
    g = g[g.ok & (g.epoch == 1)]
    name = {"claude-sonnet-5.5": "Claude Sonnet 5.5", "gemini-3.8-flash": "Gemini 3.8 Flash", "gpt-6.1-sol": "GPT-6.1 Sol",
            "deepseek-v4-pro": "DeepSeek V4 Pro", "qwen3.8-2.4t-a95b": "Qwen3.8 2.4T A95B", "glm-5.3": "GLM-5.3"}
    g["model"] = g.model.map(lambda x: name.get(x, x))
    jn = {"claude-haiku-5.5": "Claude Haiku 5.5", "gpt-6-luna": "GPT-6 Luna"}
    g["judge"] = g.judge.map(lambda x: jn.get(x, x))
    for c in ["completes_task", "unrequested_moralizing", "bare_refusal"]:
        g[c] = g[c].map({"yes": 1, "no": 0})
    rows = []
    for (m, j), d in g.groupby(["model", "judge"]):
        q = d.groupby("sample_id").unrequested_moralizing.mean()
        idx = boot_idx(len(q), rng)
        bm = q.values[idx].mean(axis=1)
        rows.append({"model": m, "judge": j, "n_answers": int(len(d)), "moralizing_share": round(float(d.unrequested_moralizing.mean()), 3),
                     "moralizing_ci_lo": round(float(np.percentile(bm, 2.5)), 3), "moralizing_ci_hi": round(float(np.percentile(bm, 97.5)), 3),
                     "completes_share": round(float(d.completes_task.mean()), 3), "bare_refusals": int(d.bare_refusal.sum()),
                     "mean_words": round(float(d.answer_words.mean()), 0)})
    h = pd.DataFrame(rows)
    h.to_csv(M / "model_helpfulness.csv", index=False)
    both = g.pivot_table(index=["model", "sample_id", "epoch"], columns="judge", values="unrequested_moralizing").dropna()
    OUT["helpfulness"] = {"rows": h.to_dict(orient="records"),
                          "moralizing_kappa_all_models": round(kappa(both.iloc[:, 0], both.iloc[:, 1]), 2),
                          "moralizing_agreement_all_models": round(float(np.mean(both.iloc[:, 0] == both.iloc[:, 1])), 3),
                          "n_answers_labelled_by_both": int(len(both))}


def reference_judges() -> None:
    rng = np.random.default_rng(SEED)
    s = pd.read_csv(R / "reference_scores.csv")
    types = ["openai_spec", "anthropic_spec", "preachy", "refusal", "shotgun", "warm_wrong"]
    rows = []
    for scope in ["all", "reviewed"]:
        for j in ["haiku", "luna", "jev", "pooled"]:
            d = s[s.judge == j]
            if scope == "reviewed":
                d = d[d.reviewed]
            m = d.groupby(["question_id", "type"]).score.mean().unstack()[types].dropna() * 100
            base = (m["openai_spec"] + m["anthropic_spec"]) / 2
            idx = rng.integers(0, len(m), size=(4000, len(m)))
            for t in ["refusal", "preachy", "warm_wrong", "shotgun"]:
                x = (m[t] - base).values
                bx = x[idx].mean(axis=1)
                rows.append({"scope": scope, "judge": j, "type": t, "diff_vs_excerpt_mean": round(float(x.mean()), 1),
                             "ci_lo": round(float(np.percentile(bx, 2.5)), 1), "ci_hi": round(float(np.percentile(bx, 97.5)), 1),
                             "n_questions": int(len(m))})
    jr = pd.DataFrame(rows)
    jr.to_csv(M / "judge_reference.csv", index=False)
    g = pd.DataFrame([json.loads(x) for x in open(R / "reference_grades.jsonl")]).dropna(subset=["grade"])
    rt = []
    for j, d in g.groupby("judge"):
        w = d.pivot_table(index=["question_id", "type", "dimension", "vset"], columns="epoch", values="grade").dropna()
        same = (w.nunique(axis=1) == 1).mean()
        pa = [float(np.mean(w[a] == w[b])) for a, b in itertools.combinations(w.columns, 2)]
        kp = [kappa(w[a], w[b]) for a, b in itertools.combinations(w.columns, 2)]
        rt.append({"judge": j, "verdicts": int(len(w)), "identical_all_three_rounds": round(float(same), 3),
                   "pairwise_round_agreement": round(float(np.mean(pa)), 3), "pairwise_round_kappa": round(float(np.mean(kp)), 2)})
    rt = pd.DataFrame(rt)
    rt.to_csv(M / "judge_retest.csv", index=False)
    OUT["reference_judges"] = {"rows": jr.to_dict(orient="records"), "retest": rt.set_index("judge").to_dict(orient="index")}


def main() -> None:
    rng = np.random.default_rng(SEED)
    v = pd.read_csv(M / "verdicts.csv.gz")
    present = set(v.model.unique())
    missing = [m for m in MODELS if m not in present]
    if missing:
        raise SystemExit(f"verdicts missing for {missing}; run s10_export.py after the runs finish")
    models_and_judges(v, rng)
    helpfulness_by_model(rng)
    reference_judges()
    (M / "numbers.json").write_text(json.dumps(OUT, indent=1, default=float))
    print(json.dumps({k: OUT[k] for k in ["models"]}, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
