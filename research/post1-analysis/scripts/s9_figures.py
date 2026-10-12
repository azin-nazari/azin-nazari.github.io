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
FAIL = [("refusal", "Refuses"), ("preachy", "Preachy"), ("warm_wrong", "One planted error"), ("shotgun", "Hedges everything")]


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
    import json
    t = THEME[mode]
    n = json.loads((P1 / "06-rubrics/reference_numbers.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.4), sharey=True, facecolor=t["surface"])
    for ax, (base, title) in zip(axes, [("openai_spec", "vs the OpenAI-excerpt answer"), ("anthropic_spec", "vs the Anthropic-excerpt answer")]):
        _style(ax, t)
        ax.axvline(0, color=t["ink2"], lw=1, zorder=1)
        rows = []
        for i, (ty, _) in enumerate(FAIL):
            for off, scope, filled in [(-0.15, "reviewed_pooled", True), (0.15, "unreviewed_pooled", False)]:
                d = n[scope]["diffs"][f"{ty}-{base}"]
                rows.append((i + off, d["diff"], d["ci"][0], d["ci"][1], filled))
        _diff_rows(ax, t, rows, t["s2"])
        ax.set_xlim(-70, 35)
        ax.set_xticks([-60, -40, -20, 0, 20])
        ax.set_title(title, fontsize=11, color=t["ink"], loc="left")
        ax.set_xlabel("Points (intended failure minus helpful answer)", fontsize=9.5, color=t["ink2"])
    axes[0].set_yticks(range(len(FAIL)))
    axes[0].set_yticklabels([lab for _, lab in FAIL], fontsize=11, color=t["ink"])
    axes[0].set_ylim(len(FAIL) - 0.5, -0.6)
    leg = [plt.Line2D([], [], marker="o", ls="", ms=8, color=t["s2"], label="10 reviewed questions"),
           plt.Line2D([], [], marker="o", ls="", ms=8, markerfacecolor=t["surface"], markeredgecolor=t["s2"], markeredgewidth=2,
                      label="20 unreviewed questions")]
    fig.legend(handles=leg, loc="upper right", bbox_to_anchor=(0.985, 0.90), ncol=2, frameon=False, fontsize=10, labelcolor=t["ink2"])
    fig.text(0.01, 0.985, "Which intended failures does the score penalize?", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.925, "Left of the line = scored below the helpful answer to the same question. Mean and 95% interval.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.17, right=0.985, top=0.76, bottom=0.14, wspace=0.08)
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
    ax.set_xlabel("Points vs the two helpful answers (their mean), 30 questions", fontsize=9.5, color=t["ink2"])
    leg = [plt.Line2D([], [], marker=JUDGE_STYLE[n][1], ls="-", lw=2, ms=8, color=t[JUDGE_STYLE[n][0]], label=n)
           for n in ["Claude Haiku 5.5", "GPT-6 Luna", "Jev 1.13"]]
    ax.legend(handles=leg, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, frameon=False, fontsize=10, labelcolor=t["ink2"])
    fig.text(0.01, 0.985, "Which intended failures does each judge penalize?", fontsize=14, color=t["ink"], weight="bold", va="top")
    fig.text(0.01, 0.925, "Same 180 answers, each judge alone. Left of the line = scored below the two helpful answers. 95% intervals.",
             fontsize=10, color=t["ink2"], va="top")
    fig.subplots_adjust(left=0.22, right=0.98, top=0.74, bottom=0.14)
    _save(fig, "judges", mode, t)


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
    a1.set_xlabel("ANIMA score (0-100), two-judge panel", fontsize=10, color=t["ink2"])
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
    a2.set_title("Flagged for excessive moral commentary", fontsize=11, color=t["ink"], loc="left")
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
            "excessive moral commentary by Claude Haiku 5.5 and GPT-6 Luna, in that order: " + ", ".join(flags) + ".")


if __name__ == "__main__":
    fns = {"coverage": coverage, "coverage_summary": coverage_summary, "reference": reference, "reference_diff": reference_diff,
           "judges": judges, "models": models}
    todo = ["coverage", "coverage_summary", "reference_diff", "judges", "models"] if sys.argv[1] == "all" else [sys.argv[1]]
    for name in todo:
        for mode in ("light", "dark"):
            fns[name](mode)
    print("ok")
