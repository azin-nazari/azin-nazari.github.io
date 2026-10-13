"""Where the decision model Jev 1.13 departs from the two panel judges. No model calls.

  python s12_jev.py        # writes 10-models/jev_agreement.csv and 10-models/jev_numbers.json

On the first answers of all six models: for every verdict where both panel judges (Claude Haiku 5.5, Gemini 3.5 Flash-Lite)
gave the same verdict, does Jev (pass = P >= 0.5) agree, and if not, is it stricter (fails what both passed) or looser?
"""

from __future__ import annotations

import json

import pandas as pd

from paths import P1

M = P1 / "10-models"
H, F, J = "Claude Haiku 5.5", "Gemini 3.5 Flash-Lite", "Jev 1.13"


def main() -> None:
    v = pd.read_csv(M / "verdicts.csv.gz")
    v = v[v.epoch == 1]
    w = v.pivot_table(index=["model", "sample_id", "dimension", "vset_idx"], columns="judge", values="pass").reset_index()
    x = w.dropna(subset=[H, F, J])
    agree = x[x[H] == x[F]].copy()
    agree["dis"] = agree[J] != agree[H]
    agree["stricter"] = (agree[J] == 0) & (agree[H] == 1)
    agree["looser"] = (agree[J] == 1) & (agree[H] == 0)
    rows = []
    pr = v.groupby(["dimension", "judge"])["pass"].mean().unstack()
    for dim, g in agree.groupby("dimension"):
        rows.append({"criterion": dim, "verdicts_panel_agrees": len(g), "jev_disagrees_pct": round(100 * g.dis.mean(), 1),
                     "jev_stricter": int(g.stricter.sum()), "jev_looser": int(g.looser.sum()),
                     "pass_haiku_pct": round(100 * pr.loc[dim, H], 1), "pass_flashlite_pct": round(100 * pr.loc[dim, F], 1),
                     "pass_jev_pct": round(100 * pr.loc[dim, J], 1)})
    t = pd.DataFrame(rows).sort_values("verdicts_panel_agrees", ascending=False)
    t.to_csv(M / "jev_agreement.csv", index=False)
    n = {"verdicts_all_three": int(len(x)), "panel_agrees": int(len(agree)),
         "panel_agrees_pct": round(100 * len(agree) / len(x), 1),
         "jev_agrees_with_agreeing_panel_pct": round(100 * (1 - agree.dis.mean()), 1),
         "jev_disagreements": int(agree.dis.sum()), "jev_stricter": int(agree.stricter.sum()), "jev_looser": int(agree.looser.sum()),
         "moral_consideration_share_of_disagreements_pct": round(100 * agree[agree.dimension == "Moral Consideration"].dis.sum() / agree.dis.sum(), 1)}
    (M / "jev_numbers.json").write_text(json.dumps(n, indent=1))
    print(t.to_string(index=False))
    print(n)


if __name__ == "__main__":
    main()
