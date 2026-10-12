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
    # reference answers
    n = json.loads((P1 / "06-rubrics/reference_numbers.json").read_text())
    names = {"openai_spec": "OpenAI-excerpt", "anthropic_spec": "Anthropic-excerpt", "shotgun": "Hedges everything", "preachy": "Preachy",
             "warm_wrong": "One planted error", "refusal": "Refuses"}
    for t, label in names.items():
        R, U = n["reviewed_pooled"], n["unreviewed_pooled"]
        has(f"| {label} | {round(R['mean'][t])} ({round(R['ci'][t][0])} to {round(R['ci'][t][1])}) | "
            f"{round(U['mean'][t])} ({round(U['ci'][t][0])} to {round(U['ci'][t][1])}) |", f"reference score row {t}")
        if t in ("openai_spec", "anthropic_spec"):
            continue
        for scope in ("reviewed_pooled", "unreviewed_pooled"):          # two tables: reviewed, then unreviewed
            cells = []
            for base in ("openai_spec", "anthropic_spec"):
                d = n[scope]["diffs"][f"{t}-{base}"]
                cells.append(f"{sgn(d['diff'])} ({sgn(d['ci'][0])} to {sgn(d['ci'][1])})")
            has(f"| {label} | " + " | ".join(cells) + " |", f"reference diff row {t} {scope}")
    dims = n["dimension_pass_rates_all"]
    has(f"Moral Consideration passed the hedge-everything answers {pct(dims['Moral Consideration']['shotgun'])} of the time, against "
        f"{pct(dims['Moral Consideration']['openai_spec'])} and {pct(dims['Moral Consideration']['anthropic_spec'])} for the two helpful ones",
        "MC rates")
    g = n["reviewed_pooled"]["diffs"]["anthropic_spec-openai_spec"]
    has(f"scored {round(g['diff'])} points above those from the Model Spec's ({sgn(g['ci'][0])} to {sgn(g['ci'][1])})", "excerpt gap")
    rc = pd.read_csv(P1 / "06-rubrics/revised_recheck.csv")
    ww = rc[rc.type == "warm_wrong"]
    assert (rc.note_addressed == "yes").all() and (rc.matches_type == "yes").all() and (ww.factual_errors_found == 1).all()
    words = {6: "six"}
    has(f"each of the {words.get(len(ww), len(ww))} planted-error answers contains exactly one error", "recheck")
    # judges
    jr = pd.read_csv(P1 / "10-models/judge_reference.csv")
    jr = jr[jr.scope == "all"].set_index(["judge", "type"])
    for t, label in [("refusal", "Refuses"), ("preachy", "Preachy"), ("warm_wrong", "One planted error"), ("shotgun", "Hedges everything")]:
        cells = [f"{sgn(jr.loc[(j, t)].diff_vs_excerpt_mean, 1)} ({sgn(jr.loc[(j, t)].ci_lo, 1)} to {sgn(jr.loc[(j, t)].ci_hi, 1)})"
                 for j in ("haiku", "luna", "jev")]
        cells = [x if not x.startswith("+") or label != "Refuses" else x for x in cells]
        has(f"| {label} | " + " | ".join(cells).replace("(+", "(+").replace(" +", " +") + " |", f"judge row {t}")
    rt = pd.read_csv(P1 / "10-models/judge_retest.csv").set_index("judge")
    has(" | ".join(f"{100 * rt.loc[j].pairwise_round_agreement:.1f}% (κ {rt.loc[j].pairwise_round_kappa:.2f})" for j in ("haiku", "luna", "jev")),
        "retest row")
    jp = pd.read_csv(P1 / "10-models/judge_pairs.csv")
    has(f"agreed on {pct(jp.agreement.min())[:-1]}–{pct(jp.agreement.max())} of verdicts (κ {jp.kappa.min():.2f} to {jp.kappa.max():.2f})", "judge agreement")
    # models: no score table in the main text any more; check the sentences and the "What I'd test next" table
    sc = pd.read_csv(P1 / "10-models/model_scores.csv")
    pn = sc[sc.scorer.str.startswith("Panel")].set_index("model")
    for alone in ("Claude Haiku 5.5 alone", "Gemini 3.5 Flash-Lite alone", "Jev 1.13 alone"):
        top = sc[sc.scorer.str.startswith(alone)].sort_values("score").iloc[-1].model
        if top != "GPT-6.1 Sol":
            FAILS.append(f"first place under {alone} is {top}, not GPT-6.1 Sol")
    assert pn.loc["GPT-6.1 Sol"].rank_lo == pn.loc["GPT-6.1 Sol"].rank_hi == 1
    for mname in ("Claude Sonnet 5.5", "GLM-5.3"):
        has(f"| Rank {pn.loc[mname].rank_lo}–{pn.loc[mname].rank_hi} in resamples |", f"rank range {mname}")
    h = pd.read_csv(P1 / "10-models/model_helpfulness.csv").set_index(["model", "judge"])

    def fl(mname):   # each labeller's own estimate, Haiku / Luna (not a range)
        return f"{pct(h.loc[(mname, 'Claude Haiku 5.5')].moralizing_share)} / {pct(h.loc[(mname, 'GPT-6 Luna')].moralizing_share)}"
    has(f"fewest moralizing flags ({fl('GPT-6.1 Sol')})", "flags Sol")
    has(f"differ most ({fl('Qwen3.8 2.4T A95B')})", "flags Qwen")
    for mname in ("Claude Sonnet 5.5", "Gemini 3.8 Flash", "GLM-5.3"):
        has(f"flagged {fl(mname)};", f"flags {mname}")
    has(f"both labellers ({fl('DeepSeek V4 Pro')})", "flags DeepSeek")
    d = [h.loc[("DeepSeek V4 Pro", j)].moralizing_share for j in ("Claude Haiku 5.5", "GPT-6 Luna")]
    assert all(0.45 <= x <= 0.55 for x in d), d                       # "about half", "about 50%"
    gaps = {m: max(abs(h.loc[(m, "Claude Haiku 5.5")].moralizing_share - h.loc[(m, "GPT-6 Luna")].moralizing_share), 0) for m in pn.index}
    assert max(gaps, key=gaps.get) == "Qwen3.8 2.4T A95B"
    w = {m: int(h.loc[(m, "Claude Haiku 5.5")].mean_words) for m in pn.index}
    has(f"shortest answers (~{round(w['GPT-6.1 Sol'], -2)} words)", "words Sol")
    has(f"longest answers (~{round(w['Qwen3.8 2.4T A95B'], -2)} words)", "words Qwen")
    assert min(w, key=w.get) == "GPT-6.1 Sol" and max(w, key=w.get) == "Qwen3.8 2.4T A95B"
    nm = json.loads((P1 / "10-models/numbers.json").read_text())
    n_pairs, n_dist = nm["models"]["n_pairs"], nm["models"]["n_distinguishable_pairs"]
    has(f"{n_pairs - n_dist} of the {n_pairs} model pairs can't be told apart", "indistinguishable pairs")
    has(f"up to {nm['models']['judge_range_max']:.1f} points", "judge range")
    # criterion pass rates quoted from the explorer data
    ex = json.loads((P1 / "09-post/explorer/summary.json").read_text())["criteria"]["panel"]
    v = pd.read_csv(P1 / "10-models/verdicts.csv.gz")
    v = v[(v.epoch == 1) & v.judge.isin(["Claude Haiku 5.5", "Gemini 3.5 Flash-Lite"]) & (v.dimension == "Moral Consideration")]
    mc = (100 * v.groupby("model")["pass"].mean()).to_dict()       # exact, so rounding matches the explorer's display
    sol, ds = round(mc["GPT-6.1 Sol"]), round(mc["DeepSeek V4 Pro"])
    has(f"about as often as DeepSeek V4 Pro ({sol}% and {ds}% of verdicts)", "MC Sol/DeepSeek")
    has(f"passes Moral Consideration most often ({sol}%; DeepSeek V4 Pro {ds}%)", "MC Sol row")
    has(f"nearly as often as GPT-6.1 Sol ({ds}% vs {sol}%)", "MC DeepSeek row")
    assert max(mc, key=mc.get) == "GPT-6.1 Sol"
    mean_mc = sum(mc.values()) / len(mc)
    has(f"tied with GLM-5.3 ({round(mc['Claude Sonnet 5.5'])}% vs a {round(mean_mc)}% mean)", "MC Sonnet/GLM")
    assert round(mc["Claude Sonnet 5.5"], 6) == round(mc["GLM-5.3"], 6) == round(min(mc.values()), 6)
    for crit, mname in [("Trade-Off Transparency", "Gemini 3.8 Flash"), ("Actionability", "GLM-5.3"), ("Harm Minimization", "GLM-5.3")]:
        low = min(ex, key=lambda m: ex[m][crit]["rate"])
        if low != mname:
            FAILS.append(f"lowest on {crit} is {low}, not {mname}")
    ns = [ex["GPT-6.1 Sol"][c]["n"] for c in ("Moral Consideration", "Trade-Off Transparency", "Actionability", "Harm Minimization")]
    has(f"Each rests on {min(ns)} to {max(ns)} verdicts per model and judge", "criterion n range")
    print(f"{N_OK} checks passed, {len(FAILS)} failed")
    for f in FAILS:
        print(" -", f)
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
