"""Step 4: summarize the coverage matrix (commitments x benchmarks).

Input : 02-commitments/commitments.csv, 03-landscape/benchmarks.csv, 04-coverage/coverage_matrix.csv
        (long form: commitment_id, benchmark, coverage in {direct, partial, none}, reason)
Output: 04-coverage/coverage_summary.md and 04-coverage/coverage_by_commitment.csv
Every headline number in the summary is computed here.
"""

from __future__ import annotations

import pandas as pd

from paths import P1

C = P1 / "04-coverage"


def main() -> None:
    com = pd.read_csv(P1 / "02-commitments" / "commitments.csv")
    ben = pd.read_csv(P1 / "03-landscape" / "benchmarks.csv")
    mat = pd.read_csv(C / "coverage_matrix.csv")
    assert set(mat.coverage) <= {"direct", "partial", "none"}, set(mat.coverage)
    missing = (len(com) * len(ben)) - len(mat)
    assert missing == 0, f"{missing} cells missing"
    bad = mat[(mat.coverage != "none") & mat.reason.isna()]
    assert bad.empty, f"{len(bad)} direct/partial cells without a reason"
    m = mat.merge(ben[["benchmark", "format", "affected_party", "measures"]], on="benchmark", how="left")
    rows = []
    for cid, g in m.groupby("commitment_id"):
        d = g[g.coverage == "direct"]
        p = g[g.coverage == "partial"]
        rows.append({"commitment_id": cid, "commitment": com.set_index("commitment_id").loc[cid, "commitment"],
                     "affected_party": com.set_index("commitment_id").loc[cid, "affected_party"],
                     "n_direct": len(d), "n_partial": len(p),
                     "direct_benchmarks": "; ".join(sorted(d.benchmark)),
                     "direct_formats": "; ".join(sorted(set(d.format.dropna()))),
                     "direct_behavioral": int((d.measures == "behavior").sum()),
                     "direct_agentic_or_multiturn": int(d.format.isin(["agentic", "multi-turn"]).sum())})
    by = pd.DataFrame(rows).sort_values(["n_direct", "n_partial"])
    by.to_csv(C / "coverage_by_commitment.csv", index=False)
    none = by[by.n_direct == 0]
    single_only = by[(by.n_direct > 0) & (by.direct_agentic_or_multiturn == 0)]
    party = by.groupby("affected_party").agg(commitments=("commitment_id", "count"),
                                             with_direct=("n_direct", lambda x: int((x > 0).sum())),
                                             mean_direct_benchmarks=("n_direct", "mean")).round(2)
    n = len(by)
    heads = [
        f"{len(none)} of {n} commitments have no benchmark that measures them directly.",
        f"{len(single_only)} of the {n - len(none)} directly measured commitments are measured only in single-turn formats (no agentic or multi-turn benchmark).",
        f"{int((by.n_direct >= 3).sum())} of {n} commitments are measured directly by three or more of the {len(ben)} benchmarks.",
        f"Across all {len(mat)} cells, {int((mat.coverage == 'direct').sum())} are direct, {int((mat.coverage == 'partial').sum())} partial and {int((mat.coverage == 'none').sum())} none.",
    ]
    md = ["# Coverage summary", "", f"{n} commitments (Step 2) × {len(ben)} benchmarks (Step 3). Cells: direct = the benchmark's scoring checks this behavior; "
          "partial = a related behavior, a proxy, or only part of the expectation (for example one kind of affected party, stated views only, or a small subset of items); none. Direct measures are also bounded by their own setting: direct means the score checks one operational instance of the expectation, not the whole of it.", "", "## Headlines", ""] + [f"- {h}" for h in heads] + [
          "", "## Commitments with no direct coverage", ""] + [f"- **{r.commitment_id}** {r.commitment} ({r.affected_party}); partial in {r.n_partial}" for r in none.itertuples()] + [
          "", "## Directly measured only in single-turn formats", ""] + [f"- **{r.commitment_id}** {r.commitment}: {r.direct_benchmarks}" for r in single_only.itertuples()] + [
          "", "## By affected party", "", party.to_markdown(), "", "## Every commitment", "", by.drop(columns=["direct_formats"]).to_markdown(index=False), ""]
    (C / "coverage_summary.md").write_text("\n".join(md))
    print("\n".join(md[:12]))


if __name__ == "__main__":
    main()
