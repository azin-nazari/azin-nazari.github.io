# Rule codes: summary (Step 6a)

40 scoring rules from TAC, CrueltyBench, ANIMA and MCB, each coded and linked to the 19 commitments in `rule_codes.csv` (columns `codes` and `commitments`). All counts below are computed from that file and from ANIMA's public question tags (114 questions run).

## How rules were linked

- `supports Cxx`: passing the rule rewards what the commitment asks for, or a reporting rule exposes whether it happens.
- `conflicts Cxx`: passing the rule rewards what the commitment rules out. By convention, `rewards_refusal` conflicts with C16 (avoid needless refusals), `requires_unprompted_moral_comment` with C12 (no unrequested ethical commentary) and `penalizes_fair_presentation` with C14 (fair presentation of contested questions). `mention_based` and `neutral` never imply a conflict on their own.
- `none`: pure aggregation, statistics or diagnostics. Every `supports` link points to a commitment the Step 4 matrix marks direct or partial for that benchmark.

## Code counts per benchmark

A rule can carry more than one code, so the code columns do not add up to the number of coded rules.

| benchmark    |   rules |   rewards_refusal |   unprompted_moral_comment |   penalizes_fair_presentation |   mention_based |   neutral_only |   rules_with_any_code |
|:-------------|--------:|------------------:|---------------------------:|------------------------------:|----------------:|---------------:|----------------------:|
| TAC          |       8 |                 1 |                          0 |                             0 |               0 |              7 |                     1 |
| CrueltyBench |       9 |                 1 |                          0 |                             0 |               0 |              8 |                     1 |
| ANIMA        |      16 |                 0 |                          4 |                             2 |               8 |              6 |                    10 |
| MCB          |       7 |                 1 |                          0 |                             0 |               0 |              6 |                     1 |
| Total        |      40 |                 3 |                          4 |                             2 |               8 |             27 |                    13 |

## ANIMA exposure

Share of `overall_mean` weight is each dimension's share of a question's tags, averaged over questions (all dimension weights are 1.0). It depends on the coding above.

| code                              |   dimensions | share_of_overall_mean   | questions_touched   | dimension_names                                                                                                                                                                                                      |
|:----------------------------------|-------------:|:------------------------|:--------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| requires_unprompted_moral_comment |            4 | 53.8%                   | 101 of 114          | Moral Consideration, Harm Minimization, Cautious Impact Consideration, Contextual Welfare Salience                                                                                                                   |
| penalizes_fair_presentation       |            2 | 17.2%                   | 86 of 114           | Actionability, Epistemic Humility                                                                                                                                                                                    |
| mention_based                     |            8 | 51.8%                   | 106 of 114          | Moral Consideration, Sentience Acknowledgement, Evidence-Based Capacity Attribution, Cautious Impact Consideration, Contextual Welfare Salience, Epistemic Humility, Trade-Off Transparency, Novel Entity Precaution |

## Commitments the coded rules conflict with

| commitment   | text                                                                                                       |   conflicting_rules | rules                                      | benchmarks             |
|:-------------|:-----------------------------------------------------------------------------------------------------------|--------------------:|:-------------------------------------------|:-----------------------|
| C12          | Do not lecture, moralize or add ethical commentary the user did not ask for.                               |                   4 | ANIMA-D01, ANIMA-D02, ANIMA-D07, ANIMA-D09 | ANIMA                  |
| C16          | Do not refuse or avoid a topic only because it is sensitive or controversial, and avoid needless refusals. |                   3 | TAC-04, CB-05, MCB-02                      | CrueltyBench, MCB, TAC |
| C14          | Present contested political, social or moral questions fairly, covering several perspectives.              |                   2 | ANIMA-D08, ANIMA-D10                       | ANIMA                  |

The other 16 commitments have no coded conflict. Support is far broader: C05 (animal welfare) is supported by 19 rules, C16 by 5, C11 by 5 and C12 by 4.

## Findings

1. 21 of the 24 rules in TAC, CrueltyBench and MCB are neutral-only, so the 13 rules with any code are concentrated in ANIMA (10 of 13).
2. TAC, CrueltyBench and MCB each have exactly one rule (3 of 40) where a refusal or non-answer can reach the top score, and each pairs it with a second measure: TAC's separate completion rate, CrueltyBench's half credit for bare refusal plus 6 control items, and MCB's separate fabrication outcome.
3. The 4 ANIMA dimensions coded as requiring unprompted moral comment conflict with C12 and carry 53.8% of `overall_mean` weight across 101 of 114 questions.
4. C12 is the commitment most often in conflict (4 rules, all in ANIMA), ahead of C16 (3 rules, one each in TAC, CrueltyBench and MCB) and C14 (2 rules, ANIMA's Actionability and Epistemic Humility, 17.2% of weight).
5. Each of the 4 ANIMA dimensions that reward unprompted comment carries a guard in its own wording (cooperate with the request, balanced or helpful tone, avoid a preachy or repetitive tone), but each guard is judged inside the same binary verdict as the behavior it limits.

## What each benchmark does well, from the rule text

- TAC: scores the action taken (final purchase) programmatically with no requirement to comment (TAC-01 to TAC-03), reports a completion rate next to the welfare rate so refusals are visible (TAC-06), and states its safe/harmful classification openly (TAC-07).
- CrueltyBench: the top grade does not require moralising, refusing or a particular diet (CB-04), a bare refusal earns only half credit (CB-06), and control items fail steering, moralising and refusing on benign requests (CB-07), reported next to the welfare mean (CB-09).
- ANIMA: every unprompted-comment dimension has a guard clause; Control Questions penalises extending welfare concern to inanimate objects (ANIMA-D13); parse failures are dropped, not scored as wrong (ANIMA-AGG3); Epistemic Humility penalises indecision as well as overconfidence (ANIMA-D10).
- MCB: fabricated completion is judged as its own outcome, and an honest failure report is not counted as fabrication (MCB-05); the opening ask is excluded from the escalation score, and the headline rung needs no LLM judge, though it is the model's own label (MCB-01, MCB-02).

## Caveats

- The codes and links are my reading of public rule text, not measured behavior. Whether ANIMA's unprompted-comment rules actually reward lecturing is an empirical question for Step 6b and 6c.
- MCB-02 is the most contestable `rewards_refusal` code: stopping scores best by design, because the construct is restraint toward a peer agent. Its link to C16 is a stretch (the stop is not a refusal of a user's request); it is counted above, so the C16 total is 3 with it and 2 without it.
- TAC and CrueltyBench rules come from public prose only. CrueltyBench's per-item grading anchors are gated and unseen, so item-level behavior of its rules is unknown. The mention-based weight depends on an approximate indicator tally.
