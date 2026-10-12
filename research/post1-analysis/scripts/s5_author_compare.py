"""Realism: compare the author's ratings of the 95-item subset with the two LLM raters. No model calls.

  python s5_author_compare.py     # 05-realism/author_vs_llm.csv, author_vs_llm_by_benchmark.csv; appends a section to realism_summary.md

Provenance: the author's 95 ratings were made with AI assistance and with the source benchmark visible, so they are a
third, non-independent rating, not a blind human validation.
"""

from __future__ import annotations

import pandas as pd

from paths import P1

D = P1 / "05-realism"
CHECKS = ["cue_signposted", "real_task", "plausible3", "format_matches_use"]


def kappa(a: pd.Series, b: pd.Series) -> float:
    a, b = a.map(str), b.map(str)
    po = (a == b).mean()
    cats = sorted(set(a) | set(b))
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main() -> None:
    llm = pd.read_csv(D / "ratings.csv")
    own = pd.read_csv(D / "human_ratings.csv")
    own["rater"] = "author (AI-assisted, not blind)"
    for df in (llm, own):
        df["plausible_request"] = pd.to_numeric(df["plausible_request"], errors="coerce")
        df["plausible3"] = (df.plausible_request == 3).map({True: "yes", False: "no"})
        for c in ["cue_signposted", "real_task", "format_matches_use"]:
            df[c] = df[c].astype(str).str.strip().str.lower()
    key = llm[["item_id", "benchmark"]].drop_duplicates()
    own = own.merge(key, on="item_id", how="left")
    rows = []
    for r in ["claude-haiku-5.5", "gpt-6-luna"]:
        m = own.merge(llm[(llm.rater == r) & llm.ok.astype(bool)], on="item_id", suffixes=("_o", "_l"))
        for c in CHECKS:
            rows.append({"llm_rater": r, "check": c, "n": len(m), "agreement": round(float((m[c + "_o"] == m[c + "_l"]).mean()), 3),
                         "kappa": round(kappa(m[c + "_o"], m[c + "_l"]), 3)})
    agree = pd.DataFrame(rows)
    agree.to_csv(D / "author_vs_llm.csv", index=False)
    # benchmark-level shares on the subset: author vs the two LLM raters' mean
    sub = llm[llm.item_id.isin(own.item_id) & llm.ok.astype(bool)]
    share = []
    for b, g in own.groupby("benchmark"):
        lg = sub[sub.benchmark == b]
        share.append({"benchmark": b, "items": len(g),
                      "author_plausible3_%": round(100 * (g.plausible3 == "yes").mean()),
                      "llm_plausible3_%": round(100 * (lg.plausible3 == "yes").mean()),
                      "author_signposted_%": round(100 * (g.cue_signposted == "yes").mean()),
                      "llm_signposted_%": round(100 * (lg.cue_signposted == "yes").mean())})
    share = pd.DataFrame(share)
    share.to_csv(D / "author_vs_llm_by_benchmark.csv", index=False)
    text = ["", "## The author's 95-item ratings", "",
            "The author rated the 95-item subset with AI assistance and with the source benchmark visible, so this is a third, non-independent, unblinded rating, not a blind human validation.", "",
            agree.to_markdown(index=False), "", share.to_markdown(index=False), ""]
    p = D / "realism_summary.md"
    s = p.read_text()
    s = s.split("\n## The author's 95-item ratings")[0]
    p.write_text(s.rstrip() + "\n" + "\n".join(text))
    print("\n".join(text))


if __name__ == "__main__":
    main()
