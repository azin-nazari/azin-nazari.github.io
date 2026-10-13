"""Figures for the post (static SVG, one light and one dark version each). No model calls.

  python s9_figures.py coverage          # coverage_{light,dark}.svg          full 19 x 21 matrix (04-coverage/coverage_matrix.csv)
  python s9_figures.py coverage_summary  # coverage_summary_{light,dark}.svg  direct / partial counts per expectation
  python s9_figures.py reference_diff    # reference_diff_{light,dark}.svg    intended-failure answers minus excerpt answers
                                         #                                    (06-rubrics/reference_numbers.json)
  python s9_figures.py judges            # judges_{light,dark}.svg            what each judge marks down (10-models/judge_reference.csv)
  python s9_figures.py models            # models_{light,dark}.svg            six models: ANIMA score and moralizing flags
                                         #                                    (10-models/model_scores.csv, model_helpfulness.csv)
  python s9_figures.py all
  (python s9_figures.py reference        # first-version dot plot of mean scores; kept for the record, not in the post)

Colours follow the dataviz reference palette and were checked with its validator: the coverage map is a one-hue ordinal
ramp (partial, direct) over a neutral 'none'; categorical slots 1-3 identify the three judges used throughout (Claude Haiku 5.5 blue, GPT-6 Luna orange, Jev 1.13 aqua;
the first three slots pass the validator on all pairs in both modes); every judge also has its own marker shape and a
legend, and Gemini 3.5 Flash-Lite is drawn in neutral ink with a fourth shape. Reviewed vs unreviewed questions are
filled vs hollow markers. Every figure has a data table in the post or in the data files.
"""

from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from paths import P1, SEED  # noqa: E402

OUT = P1 / "09-post" / "figures"
THEME = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781", "grid": "#e1e0d9", "none": "#f0efec",
              "partial": "#86b6ef", "direct": "#1c5cab", "s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781", "grid": "#2c2c2a", "none": "#2c2c2a",
             "partial": "#184f95", "direct": "#6da7ec", "s1": "#3987e5", "s2": "#d95926", "s3": "#199e70"},
}
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "svg.fonttype": "none",
                     "svg.hashsalt": "post1"})  # fixed clip-path ids, so rebuilt SVGs are byte-identical

SHORT = {
    "C01": "Care about non-users in the conversation", "C02": "Don't help seriously harm third parties",
    "C03": "Weigh severe, wide or irreversible harms more", "C04": "As an agent, keep side effects small",
    "C05": "Weigh the welfare of animals", "C06": "Provider: non-human welfare in risk review",
    "C07": "No gratuitous cruelty to animals", "C08": "No hateful or harassing content", "C09": "Protect others' privacy",
    "C10": "Volunteer information the user would want", "C11": "Be accurate, no false impressions",
    "C12": "Don't moralize unprompted", "C13": "Respect the user's own decisions", "C14": "Present contested questions fairly",
    "C15": "Say plainly when a matter is settled", "C16": "No needless refusals", "C17": "Don't steer users to own views",
    "C18": "Courtesy, not obedience, to other AI agents", "C19": "Give an honest view on hard moral questions",
}


def _preview(fig, name: str) -> None:
    """PNG copy for eyeballing layout, only when PREVIEW_DIR is set (not part of the outputs)."""
    import os
    d = os.environ.get("PREVIEW_DIR")
    if d:
        fig.savefig(f"{d}/{name}.png", dpi=110, facecolor=fig.get_facecolor())


def coverage(mode: str) -> None:
    t = THEME[mode]
    m = pd.read_csv(P1 / "04-coverage/coverage_matrix.csv")
    b = pd.read_csv(P1 / "03-landscape/benchmarks.csv")
    order_b = list(b.benchmark)
    lvl = {"none": 0, "partial": 1, "direct": 2}
    piv = m.assign(v=m.coverage.map(lvl)).pivot(index="commitment_id", columns="benchmark", values="v")[order_b]
    n_direct = (piv == 2).sum(axis=1)
    piv = piv.loc[n_direct.sort_values(ascending=False, kind="stable").index]
    fig, ax = plt.subplots(figsize=(9.4, 7.6), facecolor=t["surface"])
    ax.set_facecolor(t["surface"])
    cmap = ListedColormap([t["none"], t["partial"], t["direct"]])
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            ax.add_patch(plt.Rectangle((j + 0.06, i + 0.06), 0.88, 0.88, color=cmap(int(piv.iat[i, j])), lw=0))
    ax.set_xlim(0, piv.shape[1])
    ax.set_ylim(piv.shape[0], 0)
    ax.set_xticks(np.arange(piv.shape[1]) + 0.5)
    ax.set_xticklabels([c.replace(" (machine ethics)", "").replace(" 1.0", "") for c in piv.columns], rotation=60, ha="right", fontsize=10, color=t["ink2"])
    ax.set_yticks(np.arange(piv.shape[0]) + 0.5)
    ax.set_yticklabels([f"{SHORT[c]}  ({n_direct[c]})" for c in piv.index], fontsize=10.5, color=t["ink"])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.legend(handles=[Patch(color=t["direct"], label="direct: the benchmark's score checks it"), Patch(color=t["partial"], label="partial"),
                       Patch(color=t["none"], label="none")], loc="upper left", bbox_to_anchor=(-0.02, 1.10), ncol=3, frameon=False,
              fontsize=10, labelcolor=t["ink2"], handlelength=1.2)
    fig.text(0.01, 0.985, "Which expectations do 21 benchmarks measure?", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.945, "Rows: 19 expectations (in brackets, how many benchmarks measure each directly).", fontsize=10, color=t["ink2"], va="top")
    fig.text(0.01, 0.915, "Columns: 21 benchmarks, CaML's six first.", fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.445, right=0.99, top=0.83, bottom=0.17)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"coverage_{mode}.svg", facecolor=t["surface"], metadata={"Date": None})
    _preview(fig, f"coverage_{mode}")
    plt.close(fig)


def reference(mode: str) -> None:
    t = THEME[mode]
    s = pd.read_csv(P1 / "06-rubrics/reference_scores.csv")
    s = s[s.judge == "pooled"]
    ans = s.groupby(["reviewed", "question_id", "type"]).score.mean().reset_index()
    types = ["openai_spec", "anthropic_spec", "preachy", "shotgun", "warm_wrong", "refusal"]
    label = {"openai_spec": "Follows OpenAI's Model Spec", "anthropic_spec": "Follows Anthropic's constitution", "preachy": "Preachy",
             "shotgun": "Hedges everything", "warm_wrong": "Kind but factually wrong", "refusal": "Refuses"}
    rng = np.random.default_rng(SEED)
    fig, ax = plt.subplots(figsize=(7.6, 4.9), facecolor=t["surface"])
    ax.set_facecolor(t["surface"])
    for off, (scope, sub, filled) in zip([-0.14, 0.14], [("10 reviewed questions", ans[ans.reviewed], True), ("20 unreviewed questions", ans[~ans.reviewed], False)]):
        m = sub.pivot(index="question_id", columns="type", values="score")[types].dropna()
        idx = rng.integers(0, len(m), size=(4000, len(m)))
        boot = m.values[idx].mean(axis=1)
        lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
        for i, ty in enumerate(types):
            c = t["s1"] if ty.endswith("_spec") else t["s2"]
            y = i + off
            ax.plot([100 * lo[i], 100 * hi[i]], [y, y], color=c, lw=2, solid_capstyle="round")
            ax.plot(100 * m[ty].mean(), y, "o", ms=8, color=c if filled else t["surface"], markeredgecolor=c, markeredgewidth=2)
    ax.set_yticks(range(len(types)))
    ax.set_yticklabels([label[x] for x in types], fontsize=11, color=t["ink"])
    ax.set_ylim(len(types) - 0.5, -0.6)
    ax.set_xlim(0, 100)
    ax.set_xlabel("ANIMA score (0–100): mean over questions, 95% interval", fontsize=10, color=t["ink2"])
    ax.grid(axis="x", color=t["grid"], lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=t["muted"], length=0)
    for lab in ax.get_yticklabels():
        lab.set_color(t["ink"])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", ms=8, color=t["ink2"], label="10 reviewed questions"),
                       plt.Line2D([], [], marker="o", ls="", ms=8, markerfacecolor=t["surface"], markeredgecolor=t["ink2"], markeredgewidth=2,
                                  label="20 unreviewed questions")],
              loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2, frameon=False, fontsize=10, labelcolor=t["ink2"])
    fig.text(0.01, 0.98, "How ANIMA scores answers written to known types", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.915, "Blue: follows a developer's published guidelines. Orange: fails in a known way.",
             fontsize=10, color=t["ink2"], va="top")
    fig.text(0.01, 0.865, "Judges: Claude Haiku 5.5, GPT-6 Luna, Jev 1.13; three rounds each.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.36, right=0.98, top=0.73, bottom=0.13)
    fig.savefig(OUT / f"reference_{mode}.svg", facecolor=t["surface"], metadata={"Date": None})
    _preview(fig, f"reference_{mode}")
    plt.close(fig)


JUDGE_STYLE = {  # colour slot, marker
    "Claude Haiku 5.5": ("s1", "o"), "GPT-6 Luna": ("s2", "s"), "Jev 1.13": ("s3", "D"), "Gemini 3.5 Flash-Lite": ("ink2", "^"),
}
JKEY = {"haiku": "Claude Haiku 5.5", "luna": "GPT-6 Luna", "jev": "Jev 1.13"}
FAIL = [("refusal", "Refusal"), ("warm_wrong", "Planted factual error"), ("preachy", "Moralizing"), ("shotgun", "Hedging")]


def _style(ax, t):
    ax.set_facecolor(t["surface"])
    ax.tick_params(colors=t["muted"], length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.grid(axis="x", color=t["grid"], lw=0.8)
    ax.set_axisbelow(True)


def _save(fig, name, mode, t):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}_{mode}.svg", facecolor=t["surface"], metadata={"Date": None})
    _preview(fig, f"{name}_{mode}")
    plt.close(fig)


def coverage_summary(mode: str) -> None:
    t = THEME[mode]
    c = pd.read_csv(P1 / "04-coverage/coverage_by_commitment.csv")
    c = c.assign(prov=c.commitment_id.eq("C06")).sort_values(["prov", "n_direct", "n_partial"], ascending=[True, False, False],
                                                              kind="stable").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8.4, 6.8), facecolor=t["surface"])
    _style(ax, t)
    y = np.arange(len(c))
    h = 0.62
    for i, r in c.iterrows():
        if r.n_direct:
            ax.barh(i, r.n_direct, height=h, color=t["direct"], lw=0)
        if r.n_partial:
            ax.barh(i, r.n_partial - 0.06, left=r.n_direct + 0.06 if r.n_direct else 0, height=h, color=t["partial"], lw=0)
        lab = f"{r.n_direct} direct" + (f", {r.n_partial} partial" if r.n_partial else "")
        ax.text(r.n_direct + r.n_partial + 0.25, i, lab, va="center", fontsize=9, color=t["ink2"])
    names = ["Provider duty: non-human welfare in risk review" if k == "C06" else SHORT[k] for k in c.commitment_id]
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10, color=t["ink"])
    ax.set_ylim(len(c) - 0.5, -0.6)
    ax.set_xlim(0, 15.5)
    ax.set_xticks([0, 3, 6, 9, 12, 15])
    ax.set_xlabel("Number of the 21 benchmarks", fontsize=10, color=t["ink2"])
    nzero = int((c[c.commitment_id != "C06"].n_direct == 0).sum())
    ax.axhline(int((c.n_direct > 0).sum()) - 0.5, color=t["ink2"], lw=1)
    ax.axhline(len(c) - 1.5, color=t["grid"], lw=1)
    ax.legend(handles=[Patch(color=t["direct"], label="direct: the score checks the behaviour"), Patch(color=t["partial"], label="partial")],
              loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2, frameon=False, fontsize=10, labelcolor=t["ink2"], handlelength=1.2)
    fig.text(0.01, 0.985, "How many benchmarks measure each expectation?", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.945, f"Below the line: {nzero} of 18 model-behaviour expectations with no direct measure, plus one provider duty.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.42, right=0.98, top=0.86, bottom=0.08)
    _save(fig, "coverage_summary", mode, t)


def _diff_rows(ax, t, rows, color):
    """rows: list of (y, mean, lo, hi, filled)."""
    for y, m, lo, hi, filled in rows:
        ax.plot([lo, hi], [y, y], color=color, lw=2, solid_capstyle="round", zorder=2)
        ax.plot(m, y, "o", ms=8.5, color=color if filled else t["surface"], markeredgecolor=color, markeredgewidth=2, zorder=3)


def reference_diff(mode: str) -> None:
    """The reference-answer test, all 30 questions, three judges pooled the way ANIMA averages its judges."""
    t = THEME[mode]
    j = pd.read_csv(P1 / "10-models/judge_reference.csv")
    j = j[(j.scope == "all") & (j.judge == "pooled")].set_index("type")
    fig, ax = plt.subplots(figsize=(8.2, 3.9), facecolor=t["surface"])
    _style(ax, t)
    ax.axvline(0, color=t["ink2"], lw=1, zorder=1)
    for i, (ty, _) in enumerate(FAIL):
        r = j.loc[ty]
        clear = r.ci_hi < 0 or r.ci_lo > 0
        c = t["s2"] if clear else t["ink2"]
        ax.plot([r.ci_lo, r.ci_hi], [i, i], color=c, lw=2.2, solid_capstyle="round", zorder=2)
        ax.plot(r.diff_vs_excerpt_mean, i, "o", ms=9, color=c if clear else t["surface"], markeredgecolor=c, markeredgewidth=2, zorder=3)
        ax.text(r.ci_hi + 1.5, i, f"{r.diff_vs_excerpt_mean:+.0f}".replace("-", "\u2212"), va="center", fontsize=10, color=t["ink2"])
    ax.set_yticks(range(len(FAIL)))
    ax.set_yticklabels([lab for _, lab in FAIL], fontsize=11, color=t["ink"])
    ax.set_ylim(len(FAIL) - 0.5, -0.6)
    ax.set_xlim(-62, 22)
    ax.set_xticks([-60, -40, -20, 0, 20])
    ax.set_xlabel("ANIMA points compared with a helpful answer to the same question", fontsize=9.5, color=t["ink2"])
    fig.text(0.01, 0.985, "Which failures does the score penalize?", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.915, "30 questions, judges pooled, 95% intervals. Filled: clearly below the helpful answer. Hollow: no clear difference.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.24, right=0.97, top=0.80, bottom=0.17)
    _save(fig, "reference_diff", mode, t)


def judges(mode: str) -> None:
    t = THEME[mode]
    j = pd.read_csv(P1 / "10-models/judge_reference.csv")
    j = j[(j.scope == "all") & (j.judge != "pooled")]
    fig, ax = plt.subplots(figsize=(7.8, 4.6), facecolor=t["surface"])
    _style(ax, t)
    ax.axvline(0, color=t["ink2"], lw=1, zorder=1)
    offs = {"haiku": -0.22, "luna": 0.0, "jev": 0.22}
    for jk, off in offs.items():
        col, mk = JUDGE_STYLE[JKEY[jk]]
        c = t[col]
        for i, (ty, _) in enumerate(FAIL):
            r = j[(j.judge == jk) & (j.type == ty)].iloc[0]
            ax.plot([r.ci_lo, r.ci_hi], [i + off, i + off], color=c, lw=2, solid_capstyle="round", zorder=2)
            ax.plot(r.diff_vs_excerpt_mean, i + off, mk, ms=8, color=c, markeredgecolor=t["surface"], markeredgewidth=1.5, zorder=3)
    ax.set_yticks(range(len(FAIL)))
    ax.set_yticklabels([lab for _, lab in FAIL], fontsize=11, color=t["ink"])
    ax.set_ylim(len(FAIL) - 0.5, -0.6)
    ax.set_xlim(-65, 30)
    ax.set_xlabel("ANIMA points compared with a helpful answer to the same question, 30 questions", fontsize=9.5, color=t["ink2"])
    leg = [plt.Line2D([], [], marker=JUDGE_STYLE[n][1], ls="-", lw=2, ms=8, color=t[JUDGE_STYLE[n][0]], label=n)
           for n in ["Claude Haiku 5.5", "GPT-6 Luna", "Jev 1.13"]]
    ax.legend(handles=leg, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, frameon=False, fontsize=10, labelcolor=t["ink2"])
    fig.text(0.01, 0.985, "Which intended failures does each judge penalize?", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.925, "Same 180 answers, each judge alone, 95% intervals. Left of the line = scored below the helpful answers.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.22, right=0.98, top=0.74, bottom=0.14)
    _save(fig, "judges", mode, t)


def jev(mode: str) -> None:
    """Where the decision model departs from the chat-model judges: by criterion on real answers, and on Moral Consideration
    for the reference answers (helpful vs moralizing)."""
    import json
    t = THEME[mode]
    a = pd.read_csv(P1 / "10-models/jev_agreement.csv")
    a = a[a.verdicts_panel_agrees >= 30].copy()
    a["strict"] = 100 * a.jev_stricter / a.verdicts_panel_agrees
    a["loose"] = 100 * a.jev_looser / a.verdicts_panel_agrees
    a = a.sort_values("jev_disagrees_pct", ascending=False).reset_index(drop=True)
    n = json.loads((P1 / "06-rubrics/reference_numbers.json").read_text())["moral_consideration_by_judge"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 6.0), gridspec_kw={"width_ratios": [1.25, 1]}, facecolor=t["surface"])
    for ax in (a1, a2):
        _style(ax, t)
    jc = t["s3"]
    y = range(len(a))
    a1.barh(list(y), a.strict, height=0.62, color=jc, lw=0, label="Jev fails what both passed")
    a1.barh(list(y), a.loose, left=a.strict + 0.4, height=0.62, color=jc, alpha=0.38, lw=0, label="Jev passes what both failed")
    for i, r in a.iterrows():
        a1.text(r.strict + r.loose + 1.2, i, f"{r.jev_disagrees_pct:.0f}%", va="center", fontsize=9, color=t["ink2"])
    a1.set_yticks(list(y))
    a1.set_yticklabels([f"{c} ({n_})" for c, n_ in zip(a.criterion, a.verdicts_panel_agrees)], fontsize=10, color=t["ink"])
    a1.set_ylim(len(a) - 0.5, -0.6)
    a1.set_xlim(0, 30)
    a1.set_xlabel("% of verdicts where both panel\njudges agreed (count in brackets)", fontsize=10, color=t["ink2"])
    a1.set_title("Real answers: how often Jev\noverrules the panel", fontsize=11, color=t["ink"], loc="left")
    a1.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=t["ink2"], handlelength=1.2)
    judges = [("haiku", "Claude Haiku 5.5"), ("luna", "GPT-6 Luna"), ("jev", "Jev 1.13")]
    for k, (jk, name) in enumerate(judges):
        col, mk = JUDGE_STYLE[name]
        c = t[col]
        helpful = 100 * (n[jk]["openai_spec"] + n[jk]["anthropic_spec"]) / 2
        moral = 100 * n[jk]["preachy"]
        a2.plot([helpful, moral], [k, k], color=c, lw=2, zorder=2)
        a2.plot(helpful, k, mk, ms=9, color=t["surface"], markeredgecolor=c, markeredgewidth=2, zorder=3)
        a2.plot(moral, k, mk, ms=9, color=c, markeredgecolor=t["surface"], markeredgewidth=1.2, zorder=3)
        a2.text(helpful, k - 0.3, f"{helpful:.0f}%", ha="center", fontsize=9.5, color=t["ink2"])
        a2.text(moral, k - 0.3, f"{moral:.0f}%", ha="center", fontsize=9.5, color=t["ink2"])
    a2.set_yticks(range(3))
    a2.set_yticklabels([nm for _, nm in judges], fontsize=10, color=t["ink"])
    a2.set_ylim(2.7, -0.7)
    a2.set_xlim(0, 100)
    a2.set_xlabel("% passed on\nMoral Consideration", fontsize=10, color=t["ink2"])
    a2.set_title("Reference answers", fontsize=11, color=t["ink"], loc="left")
    a2.text(1, 2.45, "hollow: helpful  ·  filled: moralizing", fontsize=9, color=t["ink2"])
    fig.text(0.01, 0.985, "Where Jev departs from the chat-model judges", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.94, "Close to the panel on practical criteria; far stricter on Moral Consideration, except for answers that moralize.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.33, right=0.98, top=0.82, bottom=0.14, wspace=0.55)
    _save(fig, "jev", mode, t)


def models(mode: str) -> None:
    t = THEME[mode]
    s = pd.read_csv(P1 / "10-models/model_scores.csv")
    h = pd.read_csv(P1 / "10-models/model_helpfulness.csv")
    panel = s[s.scorer.str.startswith("Panel")].sort_values("score", ascending=False)
    order = list(panel.model)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.0, 4.9), sharey=True, gridspec_kw={"width_ratios": [1.35, 1]}, facecolor=t["surface"])
    for ax in (a1, a2):
        _style(ax, t)
    y = {m: i for i, m in enumerate(order)}
    for _, r in panel.iterrows():
        a1.plot([r.ci_lo, r.ci_hi], [y[r.model], y[r.model]], color=t["ink"], lw=5, alpha=0.18, solid_capstyle="round", zorder=1)
        a1.plot(r.score, y[r.model], "|", ms=16, mew=2.5, color=t["ink"], zorder=3)
    for _, r in panel.iterrows():
        a1.text(r.ci_hi + 1.0, y[r.model], f"{r.score:.1f}", va="center", fontsize=9.5, color=t["ink2"])
    a1.set_xlim(45, 85)
    a1.set_xlabel("ANIMA score (0-100), panel of two judges", fontsize=10, color=t["ink2"])
    a1.set_title("ANIMA score, 95% interval", fontsize=11, color=t["ink"], loc="left")
    for jn, off in [("Claude Haiku 5.5", -0.13), ("GPT-6 Luna", 0.13)]:
        col, mk = JUDGE_STYLE[jn]
        d = h[h.judge == jn]
        for _, r in d.iterrows():
            yy = y[r.model] + off
            a2.plot([100 * r.moralizing_ci_lo, 100 * r.moralizing_ci_hi], [yy, yy], color=t[col], lw=2, solid_capstyle="round", zorder=2)
            a2.plot(100 * r.moralizing_share, yy, mk, ms=7.5, color=t[col], markeredgecolor=t["surface"], markeredgewidth=1.2, zorder=3)
    a2.set_xlim(0, 60)
    a2.set_xlabel("% of answers flagged", fontsize=10, color=t["ink2"])
    a2.set_title("Answers flagged for moralizing", fontsize=11, color=t["ink"], loc="left")
    a1.set_yticks(range(len(order)))
    a1.set_yticklabels(order, fontsize=11, color=t["ink"])
    a1.set_ylim(len(order) - 0.5, -0.6)
    top = order[0]   # label the two labellers directly on the first row instead of a legend
    for jn, off in [("Claude Haiku 5.5", -0.13), ("GPT-6 Luna", 0.13)]:
        r = h[(h.judge == jn) & (h.model == top)].iloc[0]
        a2.text(100 * r.moralizing_ci_hi + 1.2, y[top] + off, jn + " labels", va="center", fontsize=9, color=t[JUDGE_STYLE[jn][0]])
    fig.text(0.01, 0.985, "Six models, two different measurements", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.925, "GPT-6.1 Sol scores highest and is flagged least. For the others, moralizing flags don't follow the score.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.17, right=0.985, top=0.80, bottom=0.12, wspace=0.08)
    _save(fig, "models", mode, t)
    if mode == "light":   # alt text for the post, written from the same data
        hh = h.pivot(index="model", columns="judge", values="moralizing_share")
        parts = [f"{m} {r.score:.0f}" for m, r in panel.set_index("model").iterrows()]
        flags = [f"{m} {100 * hh.loc[m, 'Claude Haiku 5.5']:.0f} and {100 * hh.loc[m, 'GPT-6 Luna']:.0f} percent" for m in order]
        (P1 / "10-models" / "models_alt.txt").write_text(
            "Two panels with one row per model, ordered by ANIMA score. Left, ANIMA score under the two-judge panel: " + ", ".join(parts)
            + " (95 percent intervals about 10 points wide). Right, share of answers flagged for "
            "moralizing by Claude Haiku 5.5 and GPT-6 Luna, in that order: " + ", ".join(flags) + ".")


if __name__ == "__main__":
    fns = {"coverage": coverage, "coverage_summary": coverage_summary, "reference": reference, "reference_diff": reference_diff,
           "judges": judges, "jev": jev, "models": models}
    todo = ["coverage", "coverage_summary", "reference_diff", "judges", "jev", "models"] if sys.argv[1] == "all" else [sys.argv[1]]
    for name in todo:
        for mode in ("light", "dark"):
            fns[name](mode)
    print("ok")
