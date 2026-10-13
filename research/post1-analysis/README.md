# Analysis for "The absent stakeholder"

Data and code behind [The absent stakeholder: measuring AI's consideration for others](https://azin-nazari.github.io/posts/2026-10-absent-stakeholder/) (Azin Nazari, 12 October 2026).

## Reproduce the tables and figures

Every table, figure and checked number in the post can be rebuilt from the files in this folder with Python alone: no API key and no model calls.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-analysis.txt
bash reproduce.sh
```

`reproduce.sh` rebuilds the coverage summary, the realism comparison, the reference-answer results, the moralizing analysis, the model and judge tables, the explorer data and all figures, then runs `scripts/check_numbers.py`, which formats each checked number from the data files the way the post writes it and confirms that `09-post/post1_final.md` contains it. Every resampling uses the seed 20261011, so the rebuilt files are byte-identical to the ones here. Tested with Python 3.13.

## Contents

| Folder | What it holds |
|---|---|
| `02-commitments/` | `commitments.csv`: the 19 expectations, with each document's status, quotes and links. `spec_excerpts.json`: the passages of the Model Spec and the constitution used to write the helpful reference answers. |
| `03-landscape/` | `benchmarks.csv`: the 21 benchmarks, with format, what they measure and sources. |
| `04-coverage/` | `coverage_matrix.csv` (every benchmark-expectation pair, coded direct, partial or none, with the reason), `coverage_by_commitment.csv`, `coverage_summary.md`. |
| `05-realism/` | `sample.jsonl` (rated items), `ratings.csv` (two LLM raters), `human_ratings.csv` (my 95 ratings, AI-assisted and not blind), `per_benchmark.csv`, `agreement.csv`, `author_vs_llm*.csv`, `realism_summary.md`, `caml_paper_scenarios.csv` (TAC and CrueltyBench scenarios as described in their papers). |
| `06-rubrics/` | `rule_codes.csv` (40 scoring rules, coded); the reference-answer test: `reference_questions.json`, `reference_answers.jsonl` (all 180 answers with English translations, review notes and revision flags), `reference_grades.jsonl`, `reference_scores.csv`, `reference_numbers.json`, `revised_recheck.csv`; the moralizing analysis: `helpfulness_grades.csv`, `helpfulness_effects.csv`, `helpfulness_sensitivity.csv`, `helpfulness_summary.md`. |
| `07-reliability/` | `reliability_numbers.csv`, `details.json`, `mcb_aggregation.csv`, `composite_sensitivity.csv`: computed from public data (ANIMA 2.2, the inspect_evals 0.24.0 source, MCB's public logs, the CaML board) and the paper figures cited in the post. |
| `09-post/` | `post1_final.md` (the text of the post plus a number trace mapping every number to its file), `figures/`, `explorer/` (the model explorer and the data it loads, including the two panel judges' written reasoning for every verdict in `rationales_<model>.json`). |
| `10-models/` | `answers.jsonl.gz` (every answer from the six models), `verdicts.csv.gz` (every criterion verdict from every judge), model and judge tables, `jev_agreement.csv` (where Jev 1.13 departs from the panel), `resolution.json` (interval widths: one vs five answers, paired vs unpaired), `examples.md`, `anima_questions_2.2.jsonl`. |
| `ledger/` | `calls.jsonl.gz`: one line per model call made for this analysis, with model, role, settings sent, tokens, cost, latency, retries, prompt and response. |
| `scripts/` | The scripts run by `reproduce.sh`. |

## Model calls

All model calls went through OpenRouter and were made with my own evaluation harness, which is not part of this folder. The call log in `ledger/` holds every prompt, setting and response, so any OpenAI-compatible client can audit or replay them. The ANIMA runs used `inspect_evals` 0.24.0 (task `anima`, dataset 2.2) with `grader_models` set explicitly.

## Licences

Text is CC BY 4.0 and code is MIT, as for the rest of this site. ANIMA questions and criteria (in `10-models/anima_questions_2.2.jsonl` and quoted elsewhere) are CC BY-NC 4.0, Compassion in Machine Learning. Items from the other benchmarks in `05-realism/sample.jsonl` remain under their original licences.
