"""Step 6c summary: does ANIMA's score track helpfulness and restraint?

Reads 06-rubrics/helpfulness_grades.csv; writes 06-rubrics/helpfulness_summary.md and helpfulness_effects.csv.
Labels: per judge, and a consensus label (both judges agree; disagreements dropped for that analysis).
Uncertainty: question-clustered bootstrap (2,000 resamples, seed 20261011). Three estimates of each effect:
  pooled  = mean ANIMA score of answers with the label minus without it;
  within  = the same difference computed inside each question that has both kinds of answer, then averaged
            (removes differences between questions);
  within question and model = the difference computed inside each question x responding-model group that has both
            kinds of answer, then averaged over groups (also holds the responding model fixed). Added 12 Oct 2026 after
            review; resampling draws questions and keeps all eligible model groups of a drawn question.
All three are associations between a label and the score, not effects of adding commentary.
The labelling judge Claude Haiku 5.5 is also one of the two judges behind the ANIMA score. As a check that does not share
a judge, the question-and-model estimate is repeated with ANIMA scores from Gemini 3.5 Flash-Lite alone (from
10-models/verdicts.csv.gz, written by s10_export.py), which supplied no labels.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from paths import P1, SEED

R = P1 / "06-rubrics"
B = 2000


def kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = np.mean(a == b)
    pe = np.mean(a) * np.mean(b) + (1 - np.mean(a)) * (1 - np.mean(b))
    return float("nan") if pe == 1 else float((po - pe) / (1 - pe))


def effects(df: pd.DataFrame, label: str, rng) -> dict:
    d = df.dropna(subset=["anima_overall", label]).copy()
    d["q"] = d.sample_id.astype(str)
    d[label] = d[label].astype(int)
    agg = d.groupby(["q", label]).anima_overall.agg(["sum", "count"]).unstack(label).fillna(0)
    col = lambda k, v: agg[(k, v)].to_numpy(float) if (k, v) in agg.columns else np.zeros(len(agg))  # noqa: E731
    s1, n1, s0, n0 = col("sum", 1), col("count", 1), col("sum", 0), col("count", 0)
    if not n1.sum() or not n0.sum():
        return {"n_answers": int(len(d)), "n_with": int(n1.sum()), "share_with": float(n1.sum() / len(d)), "mean_with": np.nan,
                "mean_without": np.nan, "pooled_diff": np.nan, "pooled_ci": [np.nan, np.nan], "within_diff": np.nan,
                "within_ci": [np.nan, np.nan], "within_n_questions": 0}
    dq = np.where((n1 > 0) & (n0 > 0), s1 / np.maximum(n1, 1) - s0 / np.maximum(n0, 1), np.nan)
    nq = len(agg)
    w = rng.multinomial(nq, np.full(nq, 1 / nq), size=B)          # question-cluster bootstrap weights
    with np.errstate(invalid="ignore", divide="ignore"):
        bp = (w @ s1) / (w @ n1) - (w @ s0) / (w @ n0)
        ok = ~np.isnan(dq)
        bw = (w[:, ok] @ dq[ok]) / w[:, ok].sum(axis=1)
    ci = lambda x: [float(np.nanquantile(x, 0.025)), float(np.nanquantile(x, 0.975))]  # noqa: E731
    return {"n_answers": int(len(d)), "n_with": int(n1.sum()), "share_with": float(n1.sum() / len(d)),
            "mean_with": float(s1.sum() / n1.sum()) if n1.sum() else np.nan, "mean_without": float(s0.sum() / n0.sum()),
            "pooled_diff": float(s1.sum() / n1.sum() - s0.sum() / n0.sum()) if n1.sum() else np.nan, "pooled_ci": ci(bp),
            "within_diff": float(np.nanmean(dq)) if ok.any() else np.nan, "within_ci": ci(bw), "within_n_questions": int(ok.sum())}


def within_qm(d: pd.DataFrame, label: str, score: str, rng) -> dict:
    """Flagged minus unflagged mean score inside each question x model group with both kinds; mean over groups."""
    d = d.dropna(subset=[score, label]).copy()
    d[label] = d[label].astype(int)
    m = d.groupby(["sample_id", "model", label])[score].mean().unstack(label)
    if 1 not in m.columns or 0 not in m.columns:
        return {"diff": np.nan, "ci": [np.nan, np.nan], "n_groups": 0, "n_questions": 0}
    m = m.dropna()
    gd = (m[1] - m[0]).reset_index(name="d")
    qs = gd.sample_id.unique()
    per_q = gd.groupby("sample_id").d.agg(["sum", "count"]).loc[qs]
    w = rng.multinomial(len(qs), np.full(len(qs), 1 / len(qs)), size=B)
    bs = (w @ per_q["sum"].to_numpy()) / (w @ per_q["count"].to_numpy())
    return {"diff": float(gd.d.mean()), "ci": [float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))],
            "n_groups": int(len(gd)), "n_questions": int(len(qs))}


def flashlite_scores() -> pd.DataFrame | None:
    p = P1 / "10-models" / "verdicts.csv.gz"
    if not p.exists():
        return None
    v = pd.read_csv(p)
    v = v[(v.study == "judge_study") & (v.judge == "Gemini 3.5 Flash-Lite")]
    s = v.groupby(["model", "sample_id", "epoch", "dimension"])["pass"].mean().groupby(["model", "sample_id", "epoch"]).mean()
    s = s.rename("flashlite_score").reset_index()
    s["model"] = s.model.map({"Claude Sonnet 5.5": "claude-sonnet-5.5", "Gemini 3.8 Flash": "gemini-3.8-flash"})
    return s


def main() -> None:
    rng = np.random.default_rng(SEED)
    g = pd.read_csv(R / "helpfulness_grades.csv")
    g = g[g.ok]
    checks = ["completes_task", "unrequested_moralizing", "bare_refusal"]
    for c in checks:
        g[c] = g[c].map({"yes": 1, "no": 0})
    wide = g.pivot_table(index=["model", "sample_id", "epoch", "anima_overall"], columns="judge", values=checks).reset_index()
    judges = sorted(g.judge.unique())
    lines = ["# Step 6c: helpfulness blind spot", "",
             f"Answers: {wide.shape[0]} from the 10 Oct 2026 ANIMA judge study (Claude Sonnet 5.5 and Gemini 3.8 Flash, 114 questions, 5 answers each; "
             f"5 Sonnet answers were empty in the log). Judges: {', '.join(judges)}. ANIMA score = the benchmark's own per-answer score from the study's inline panel "
             "(Claude Haiku 5.5 + Gemini 3.5 Flash-Lite).", ""]
    # rates and agreement
    rate_rows = []
    for c in checks:
        a, b = wide[(c, judges[0])], wide[(c, judges[1])]
        ok = a.notna() & b.notna()
        row = {"check": c, "agreement": float((a[ok] == b[ok]).mean()), "kappa": kappa(a[ok], b[ok])}
        for j in judges:
            for m in sorted(wide.model.unique()):
                row[f"{j} rating {m}"] = float(wide.loc[wide.model == m, (c, j)].mean())
        rate_rows.append(row)
    rates = pd.DataFrame(rate_rows)
    lines += ["## How often each label applies, and judge agreement", "", rates.round(3).to_markdown(index=False), ""]
    eff_rows = []
    saved = {}
    for c in ["completes_task", "unrequested_moralizing"]:
        keys = ["model", "sample_id", "epoch", "anima_overall"]
        variants = {j: g[g.judge == j][keys + [c]].copy() for j in judges}
        m = variants[judges[0]].merge(variants[judges[1]], on=keys, suffixes=("_a", "_b"))
        variants["consensus"] = m[m[c + "_a"] == m[c + "_b"]].rename(columns={c + "_a": c})[keys + [c]]
        for name, d in variants.items():
            e = effects(d, c, rng)
            saved[(c, name)] = e
            eff_rows.append({"label": c, "labels_from": name, **{k: (v if not isinstance(v, list) else f"[{100 * v[0]:.1f}, {100 * v[1]:.1f}]") for k, v in e.items()}})
    eff = pd.DataFrame(eff_rows)
    for col in ["share_with", "mean_with", "mean_without", "pooled_diff", "within_diff"]:
        eff[col] = (100 * eff[col].astype(float)).round(1)
    eff.to_csv(R / "helpfulness_effects.csv", index=False)
    lines += ["## ANIMA score with and without each label (points out of 100)", "",
              "pooled = all answers; within = same-question comparisons only. 95% question-clustered bootstrap intervals.", "",
              eff.to_markdown(index=False), ""]
    # within question AND responding model (sensitivity analysis added after review)
    fl = flashlite_scores()
    sens = []
    for name in judges + ["consensus"]:
        keys = ["model", "sample_id", "epoch", "anima_overall"]
        if name == "consensus":
            a = g[g.judge == judges[0]][keys + ["unrequested_moralizing"]]
            b = g[g.judge == judges[1]][keys + ["unrequested_moralizing"]]
            mm = a.merge(b, on=keys, suffixes=("_a", "_b"))
            d = mm[mm.unrequested_moralizing_a == mm.unrequested_moralizing_b].rename(columns={"unrequested_moralizing_a": "unrequested_moralizing"})
        else:
            d = g[g.judge == name][keys + ["unrequested_moralizing"]]
        e_q = saved[("unrequested_moralizing", name)]           # the published within-question estimate, same draw
        e_qm = within_qm(d, "unrequested_moralizing", "anima_overall", rng)
        row = {"labels_from": name, "score_from": "ANIMA inline panel (Claude Haiku 5.5 + Gemini 3.5 Flash-Lite)",
               "within_question": round(100 * e_q["within_diff"], 1),
               "within_question_ci": f"[{100 * e_q['within_ci'][0]:.1f}, {100 * e_q['within_ci'][1]:.1f}]",
               "within_question_n_questions": e_q["within_n_questions"],
               "within_question_and_model": round(100 * e_qm["diff"], 1),
               "within_question_and_model_ci": f"[{100 * e_qm['ci'][0]:.1f}, {100 * e_qm['ci'][1]:.1f}]",
               "groups": e_qm["n_groups"], "questions": e_qm["n_questions"]}
        sens.append(row)
        if fl is not None:
            d2 = d.merge(fl, on=["model", "sample_id", "epoch"], how="inner")
            e2 = within_qm(d2, "unrequested_moralizing", "flashlite_score", rng)
            e2q = effects(d2.drop(columns=["anima_overall"]).rename(columns={"flashlite_score": "anima_overall"}), "unrequested_moralizing", rng)
            sens.append({"labels_from": name, "score_from": "Gemini 3.5 Flash-Lite alone (supplied no labels)",
                         "within_question": round(100 * e2q["within_diff"], 1),
                         "within_question_ci": f"[{100 * e2q['within_ci'][0]:.1f}, {100 * e2q['within_ci'][1]:.1f}]",
                         "within_question_n_questions": e2q["within_n_questions"],
                         "within_question_and_model": round(100 * e2["diff"], 1),
                         "within_question_and_model_ci": f"[{100 * e2['ci'][0]:.1f}, {100 * e2['ci'][1]:.1f}]",
                         "groups": e2["n_groups"], "questions": e2["n_questions"]})
    sens = pd.DataFrame(sens)
    sens.to_csv(R / "helpfulness_sensitivity.csv", index=False)
    lines += ["## Sensitivity: comparison design and scorer (moralizing label)", "",
              "within_question = same question, both responding models pooled; within_question_and_model = same "
              "question and same responding model. Associations, not causal effects.", "", sens.to_markdown(index=False), ""]
    br = wide[[("bare_refusal", j) for j in judges]].max(axis=1)
    lines += [f"Bare refusals (either judge): {int(br.sum())} of {len(br)} answers.", ""]
    (R / "helpfulness_summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
