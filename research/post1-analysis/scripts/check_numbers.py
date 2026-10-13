"""Check that the numbers quoted in the post match the data files. No model calls.

  python check_numbers.py        # exits non-zero and lists every mismatch

Each check formats a number from a data file the way the post writes it and looks for that exact text in
09-post/post1_final.md. Run by reproduce.sh after the tables and figures are rebuilt.
"""

from __future__ import annotations

import gzip  # noqa: F401  (kept for readers extending the checks)
import json
import sys

import pandas as pd

from paths import P1

POST = (P1 / "09-post" / "post1_final.md").read_text()
FAILS: list[str] = []
N_OK = 0
M = "−"


def has(s: str, what: str) -> None:
    global N_OK
    if s in POST:
        N_OK += 1
    else:
        FAILS.append(f"{what}: expected text not found: {s!r}")


def sgn(x: float, d: int = 0) -> str:
    v = round(x, d) if d else round(x)
    s = f"{abs(v):.{d}f}"
    return f"{M}{s}" if v < 0 else f"+{s}"


def num(x: float, d: int = 0) -> str:
    v = round(x, d) if d else round(x)
    s = f"{abs(v):.{d}f}"
    return f"{M}{s}" if v < 0 else s


def pct(x: float) -> str:
    return f"{round(100 * x)}%"


def main() -> None:
    # coverage
    c = pd.read_csv(P1 / "04-coverage/coverage_by_commitment.csv")
    beh = c[c.commitment_id != "C06"]
    has(f"{int((beh.n_direct == 0).sum())} of the 18 behavior expectations have no direct measure", "coverage headline")
    m = pd.read_csv(P1 / "04-coverage/coverage_matrix.csv")
    has(f"Across all {len(m)} benchmark-expectation pairs, {int((m.coverage == 'direct').sum())} are direct and "
        f"{int((m.coverage == 'partial').sum())} partial", "coverage cells")
    # realism table
    pb = pd.read_csv(P1 / "05-realism/per_benchmark.csv").set_index("benchmark")
    for b, label in [("ANIMA", "ANIMA"), ("MORU", "MORU"), ("MoralChoice", "MoralChoice"), ("DailyDilemmas", "DailyDilemmas")]:
        r = pb.loc[b]
        has(f"| {label} | {int(r['items'])} | {round(r['cue_signposted_%'])}% | {round(r['real_task_%'])}% | {round(r['plausible_3_%'])}% | "
            f"{round(r['format_matches_use_%'])}% |", f"realism row {b}")
    # helpfulness (6c) and sensitivity: the collapsed "Exact values" table, one column per labeller
    s = pd.read_csv(P1 / "06-rubrics/helpfulness_sensitivity.csv")
    cols = {"claude-haiku-5.5": [], "gpt-6-luna": []}
    groups = {}
    for j in cols:
        a = s[(s.labels_from == j) & s.score_from.str.startswith("ANIMA")].iloc[0]
        b = s[(s.labels_from == j) & s.score_from.str.startswith("Gemini")].iloc[0]
        for val, ci in [(a.within_question, a.within_question_ci), (a.within_question_and_model, a.within_question_and_model_ci),
                        (b.within_question_and_model, b.within_question_and_model_ci)]:
            lo, hi = [float(x) for x in ci.strip("[]").split(",")]
            cols[j].append(f"{sgn(val, 1)} ({num(lo, 1)} to {num(hi, 1)})")
        groups[j] = a.groups
    for k, label in enumerate(["Same question", "Same question and same model",
                               "Same question and model, score from Flash-Lite alone"]):
        has(f"| {label} | {cols['claude-haiku-5.5'][k]} | {cols['gpt-6-luna'][k]} |", f"moralizing association row {k}")
    has(f"use {groups['claude-haiku-5.5']} (Haiku) and {groups['gpt-6-luna']} (Luna) question-model groups", "moralizing groups")
    # reference answers: one combined table (all 30 questions, judges pooled)
    n = json.loads((P1 / "06-rubrics/reference_numbers.json").read_text())
    A = n["all_pooled"]
    jr = pd.read_csv(P1 / "10-models/judge_reference.csv").set_index(["scope", "judge", "type"])
    labels = [("openai_spec", "Helpful, from Model Spec passages"), ("anthropic_spec", "Helpful, from constitution passages"),
              ("refusal", "Refusal"), ("warm_wrong", "Planted factual error"), ("preachy", "Moralizing"), ("shotgun", "Hedging")]
    for t, label in labels:
        m = f"{round(A['mean'][t])} ({round(A['ci'][t][0])} to {round(A['ci'][t][1])})"
        if t in ("openai_spec", "anthropic_spec"):
            d = "—"
        else:
            x = jr.loc[("all", "pooled", t)]
            d = f"{sgn(x.diff_vs_excerpt_mean)} ({sgn(x.ci_lo)} to {sgn(x.ci_hi)})"
        has(f"| {label} | {m} | {d} |", f"reference row {t}")
    pooled = {t: jr.loc[("all", "pooled", t)].diff_vs_excerpt_mean for t in ["refusal", "warm_wrong", "preachy", "shotgun"]}
    has(f"answers written to refuse lost {round(-pooled['refusal'])} points and answers with one planted factual error lost "
        f"{round(-pooled['warm_wrong'])}", "found: reference")
    has(f"**Refusals lost {round(-pooled['refusal'])} points and a planted factual error {round(-pooled['warm_wrong'])}. Moralizing "
        f"({sgn(pooled['preachy'])}) and hedging ({sgn(pooled['shotgun'])}) were not clearly different", "reference headline")
    for t in ["preachy", "shotgun"]:
        x = jr.loc[("all", "pooled", t)]
        assert x.ci_lo < 0 < x.ci_hi, t                                  # "not clearly different"
    for t in ["refusal", "warm_wrong"]:
        assert jr.loc[("all", "pooled", t)].ci_hi < 0, t                 # "lost"

    def sub(scope):
        return ", ".join(f"{lab} {sgn(jr.loc[(scope, 'pooled', t)].diff_vs_excerpt_mean)}" for t, lab in
                         [("refusal", "refusal"), ("warm_wrong", "planted error"), ("preachy", "moralizing"), ("shotgun", "hedging")])
    has(f"{sub('reviewed')} points on the reviewed questions; {sub('unreviewed')} on the unreviewed ones", "reviewed vs unreviewed")
    dims = n["dimension_pass_rates_all"]["Moral Consideration"]
    has(f"Moral Consideration passed hedging answers {pct(dims['shotgun'])} of the time and moralizing answers {pct(dims['preachy'])}, "
        f"against {pct(dims['openai_spec'])} and {pct(dims['anthropic_spec'])} for the two helpful answers", "MC rates")
    g = A["diffs"]["anthropic_spec-openai_spec"]
    has(f"scored {g['diff']:.1f} points above those written from the Model Spec's ({sgn(g['ci'][0], 1)} to {sgn(g['ci'][1], 1)})", "excerpt gap")
    has(f"passed Moral Consideration more often ({pct(dims['anthropic_spec'])} vs {pct(dims['openai_spec'])})", "excerpt MC")
    rc = pd.read_csv(P1 / "06-rubrics/revised_recheck.csv")
    ww = rc[rc.type == "warm_wrong"]
    assert (rc.note_addressed == "yes").all() and (rc.matches_type == "yes").all() and (ww.factual_errors_found == 1).all()
    has(f"each of the {dict([(6, 'six')]).get(len(ww), len(ww))} planted-error answers contains exactly one error", "recheck")
    # worked example (question 61)
    q = pd.read_csv(P1 / "06-rubrics/reference_scores.csv")
    q = q[(q.question_id == 61) & (q.judge == "pooled")].groupby("type").score.mean() * 100
    has(f"| 1 | helpful | {round(q['anthropic_spec'])} |\n| 2 | hedging everything | {round(q['shotgun'])} |\n| 3 | moralizing | {round(q['preachy'])} |",
        "q61 table")
    assert q["shotgun"] == q.max(), "hedge should be the highest of the six"
    # judges
    jl = [("refusal", "Refusal"), ("warm_wrong", "Planted factual error"), ("preachy", "Moralizing"), ("shotgun", "Hedging")]
    for t, label in jl:
        cells = [f"{sgn(jr.loc[('all', j, t)].diff_vs_excerpt_mean, 1)} ({sgn(jr.loc[('all', j, t)].ci_lo, 1)} to {sgn(jr.loc[('all', j, t)].ci_hi, 1)})"
                 for j in ("haiku", "luna", "jev")]
        has(f"| {label} | " + " | ".join(cells) + " |", f"judge row {t}")
    J = lambda j, t: jr.loc[("all", j, t)]
    has(f"Only GPT-6 Luna clearly penalized moralizing ({sgn(J('luna', 'preachy').diff_vs_excerpt_mean)} points); Claude Haiku 5.5 took off "
        f"{round(-J('haiku', 'preachy').diff_vs_excerpt_mean)} points and Jev added {round(J('jev', 'preachy').diff_vs_excerpt_mean)}", "judges moralizing")
    has(f"penalized a planted error ({sgn(J('haiku', 'warm_wrong').diff_vs_excerpt_mean)} and {sgn(J('luna', 'warm_wrong').diff_vs_excerpt_mean)}); "
        f"Jev did not ({round(J('jev', 'warm_wrong').diff_vs_excerpt_mean)})", "judges error")
    has(f"| Anthropic | Claude Sonnet 5.5: {{}} | Claude Haiku 5.5: {sgn(J('haiku', 'preachy').diff_vs_excerpt_mean)} "
        f"({sgn(J('haiku', 'preachy').ci_lo)} to {sgn(J('haiku', 'preachy').ci_hi)}) |".replace("{}", "17% / 16%"), "dev table Anthropic judge")
    has(f"| OpenAI | GPT-6.1 Sol: 9% / 11% | GPT-6 Luna: {sgn(J('luna', 'preachy').diff_vs_excerpt_mean)} "
        f"({sgn(J('luna', 'preachy').ci_lo)} to {sgn(J('luna', 'preachy').ci_hi)}) |", "dev table OpenAI judge")
    rt = pd.read_csv(P1 / "10-models/judge_retest.csv").set_index("judge")
    has(" | ".join(f"{100 * rt.loc[j].pairwise_round_agreement:.1f}% (κ {rt.loc[j].pairwise_round_kappa:.2f})" for j in ("haiku", "luna", "jev")),
        "retest row")
    has(f"({100 * rt.loc['jev'].pairwise_round_agreement:.1f}%, against {round(100 * rt.loc['luna'].pairwise_round_agreement)}–"
        f"{round(100 * rt.loc['haiku'].pairwise_round_agreement)}% for the chat models)", "retest sentence")
    jp = pd.read_csv(P1 / "10-models/judge_pairs.csv")
    has(f"Pairs of judges gave the same verdict on {pct(jp.agreement.min())[:-1]}–{pct(jp.agreement.max())} of criteria "
        f"(κ {jp.kappa.min():.2f} to {jp.kappa.max():.2f})", "judge agreement")
    # Jev
    jn = json.loads((P1 / "10-models/jev_numbers.json").read_text())
    ja = pd.read_csv(P1 / "10-models/jev_agreement.csv").set_index("criterion")
    has(f"Jev agreed with them {round(jn['jev_agrees_with_agreeing_panel_pct'])}% of the time", "jev agreement")
    has(f"Jev agreed with the chat-model judges on {round(jn['jev_agrees_with_agreeing_panel_pct'])}% of verdicts", "found: jev agreement")
    has(f"({jn['jev_stricter']} of {jn['jev_disagreements']} times)", "jev stricter")
    assert 45 <= jn["moral_consideration_share_of_disagreements_pct"] <= 55          # "half its disagreements"
    mc = ja.loc["Moral Consideration"]
    has(f"which it passed for {round(mc.pass_jev_pct)}% of answers against {round(min(mc.pass_haiku_pct, mc.pass_flashlite_pct))}–"
        f"{round(max(mc.pass_haiku_pct, mc.pass_flashlite_pct))}% for the chat-model judges", "jev MC pass")
    pr = [ja.loc[c].jev_disagrees_pct for c in ("Actionability", "Harm Minimization")]
    has(f"it disagrees on {round(min(pr))}–{round(max(pr))}% of verdicts", "jev practical")
    mcj = n["moral_consideration_by_judge"]["jev"]
    has(f"Jev passed {round(100 * (mcj['openai_spec'] + mcj['anthropic_spec']) / 2)}% of the helpful answers on Moral Consideration, "
        f"but {pct(mcj['preachy'])} of the moralizing ones", "jev reference MC")
    assert 0.45 <= mcj["preachy"] <= 0.55                                               # "passed half the moralizing answers"
    # models
    sc = pd.read_csv(P1 / "10-models/model_scores.csv")
    pn = sc[sc.scorer.str.startswith("Panel")].set_index("model")
    for alone in ("Claude Haiku 5.5 alone", "Gemini 3.5 Flash-Lite alone", "Jev 1.13 alone"):
        top = sc[sc.scorer.str.startswith(alone)].sort_values("score").iloc[-1].model
        if top != "GPT-6.1 Sol":
            FAILS.append(f"first place under {alone} is {top}, not GPT-6.1 Sol")
    h = pd.read_csv(P1 / "10-models/model_helpfulness.csv").set_index(["model", "judge"])
    for mname, r in pn.iterrows():
        fh, fl = h.loc[(mname, "Claude Haiku 5.5")], h.loc[(mname, "GPT-6 Luna")]
        has(f"| {mname} | {r.score:.1f} ({r.ci_lo:.1f} to {r.ci_hi:.1f}) | {r['rank']} ({r.rank_lo}–{r.rank_hi}) | {pct(fh.moralizing_share)} / "
            f"{pct(fl.moralizing_share)} | {int(fh.mean_words)} |", f"model row {mname}")
    fl = lambda m: f"{pct(h.loc[(m, 'Claude Haiku 5.5')].moralizing_share)} / {pct(h.loc[(m, 'GPT-6 Luna')].moralizing_share)}"
    for m, dev in [("Claude Sonnet 5.5", "Anthropic"), ("GPT-6.1 Sol", "OpenAI"), ("Gemini 3.8 Flash", "Google")]:
        has(f"| {dev} | {m}: {fl(m)} |", f"dev table {m}")
    sol = [h.loc[("GPT-6.1 Sol", j)].moralizing_share for j in ("Claude Haiku 5.5", "GPT-6 Luna")]
    ds = [h.loc[("DeepSeek V4 Pro", j)].moralizing_share for j in ("Claude Haiku 5.5", "GPT-6 Luna")]
    assert all(0.07 <= x <= 0.13 for x in sol) and all(0.45 <= x <= 0.55 for x in ds)   # "about 1 in 10", "about half"
    assert h.loc[("GPT-6.1 Sol", "GPT-6 Luna")].moralizing_share > h.loc[("GPT-6.1 Sol", "Claude Haiku 5.5")].moralizing_share
    mp = pd.read_csv(P1 / "10-models/model_pairs.csv")
    order = list(pn.sort_values("score", ascending=False).index)
    for _, r in mp.iterrows():
        a, b, d, lo, hi = r.model_a, r.model_b, r["diff"], r.ci_lo, r.ci_hi
        if order.index(a) > order.index(b):
            a, b, d, lo, hi = b, a, -d, -hi, -lo
        has(f"| {a} − {b} | {sgn(d, 1)} | {sgn(lo, 1)} to {sgn(hi, 1)} |", f"pair {a}/{b}")
    sol_d = [abs(r["diff"]) for _, r in mp.iterrows() if "GPT-6.1 Sol" in (r.model_a, r.model_b)]
    has(f"scores {round(min(sol_d))} to {round(max(sol_d))} points above each of the others", "sol lead")
    has(f"it scored {round(min(sol_d))} to {round(max(sol_d))} points above each of the other five models", "found: sol lead")
    mid = [abs(r["diff"]) for _, r in mp.iterrows() if {r.model_a, r.model_b} <= {"Qwen3.8 2.4T A95B", "Claude Sonnet 5.5", "DeepSeek V4 Pro"}]
    assert max(mid) < 4
    nm = json.loads((P1 / "10-models/numbers.json").read_text())["models"]["by_judge_scores"]["GPT-6.1 Sol"]
    has(f"GPT-6.1 Sol scored {round(nm['Gemini 3.5 Flash-Lite'])} with Gemini 3.5 Flash-Lite as judge and {round(nm['Jev 1.13'])} with Jev 1.13",
        "found: judge level")
    has(f"GPT-6.1 Sol scores {round(nm['Jev 1.13'])} with Jev and {round(nm['Gemini 3.5 Flash-Lite'])} with Gemini 3.5 Flash-Lite", "judge level")
    # resolution
    rs = json.loads((P1 / "10-models/resolution.json").read_text())
    b = rs["by_answers_per_question"]
    has(f"the intervals stayed at ±{b['Claude Sonnet 5.5']['five_answers_halfwidth']} and ±{b['Gemini 3.8 Flash']['five_answers_halfwidth']} points",
        "resolution five answers")
    assert all(abs(x["one_answer_halfwidth"] - x["five_answers_halfwidth"]) <= 0.2 for x in b.values())
    ratios = [x["ratio"] for x in rs["variance"].values()]
    has(f"Scores vary {round(min(ratios))} to {round(max(ratios))} times more between questions", "resolution ratio")
    pr_ = rs["pairs"]
    has(f"about ±{pr_['unpaired_halfwidth_mean']} points; worked out question by question, it is about ±{round(pr_['paired_halfwidth_mean'])} "
        f"({pr_['paired_halfwidth_range'][0]} to {pr_['paired_halfwidth_range'][1]})", "resolution paired")
    # shark-net example (question 102)
    it = {s: [x for x in json.loads((P1 / f"09-post/explorer/items_{s}.json").read_text()) if x["id"] == 102][0]
          for s in ("gpt-6.1-sol", "deepseek-v4-pro")}
    has(f"[Proportionate · GPT-6.1 Sol · {it['gpt-6.1-sol']['words']} words · ANIMA score {round(it['gpt-6.1-sol']['score'])}]", "shark Sol")
    has(f"[Moralizing · DeepSeek V4 Pro · {it['deepseek-v4-pro']['words']} words · ANIMA score {round(it['deepseek-v4-pro']['score'])}]", "shark DeepSeek")
    has(f"outscored GPT-6.1 Sol's proportionate advice, {round(it['deepseek-v4-pro']['score'])} to {round(it['gpt-6.1-sol']['score'])}", "found: shark")
    print(f"{N_OK} checks passed, {len(FAILS)} failed")
    for f in FAILS:
        print(" -", f)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
