# Realism audit: summary

Items rated: 476 across 6 benchmarks; raters: claude-haiku-5.5, gpt-6-luna (temperature 0 where supported, low reasoning).
Percentages average both raters' verdicts. Checks with Cohen's κ below 0.6 are marked unreliable and should not carry a headline.

## Per benchmark

| benchmark          |   items |   cue_signposted_% |   real_task_% |   plausible_mean_1to3 |   plausible_3_% |   format_matches_use_% |   artifact_% |
|:-------------------|--------:|-------------------:|--------------:|----------------------:|----------------:|-----------------------:|-------------:|
| ANIMA              |     115 |               28.8 |          69.9 |                   2.8 |            82.1 |                   91.7 |         24.5 |
| DailyDilemmas      |      50 |               90   |          40   |                   2   |             6   |                    5   |         45   |
| ETHICS-commonsense |      50 |              100   |           0   |                   2   |             0   |                    0   |        100   |
| MCB                |      10 |                0   |         100   |                   3   |           100   |                  100   |          0   |
| MORU               |     201 |               78.6 |          96.2 |                   2.2 |            18.1 |                   72   |         23.4 |
| MoralChoice        |      50 |               83.8 |           0   |                   1.7 |             0   |                    0   |        100   |

## Rater agreement

| check              |   n |   agreement |   kappa |
|:-------------------|----:|------------:|--------:|
| cue_signposted     | 468 |       0.87  |   0.697 |
| real_task          | 468 |       0.953 |   0.899 |
| plausible_request  | 468 |       0.848 |   0.678 |
| format_matches_use | 468 |       0.9   |   0.797 |
| has_artifact       | 468 |       0.793 |   0.579 |

Unreliable checks (κ < 0.6): has_artifact.

## Per rater

|                                            |   cue |   real |   plaus |
|:-------------------------------------------|------:|-------:|--------:|
| ('ANIMA', 'claude-haiku-5.5')              |  25.4 |   68.4 |    2.84 |
| ('ANIMA', 'gpt-6-luna')                    |  32.2 |   71.3 |    2.77 |
| ('DailyDilemmas', 'claude-haiku-5.5')      |  84   |   30   |    2    |
| ('DailyDilemmas', 'gpt-6-luna')            |  96   |   50   |    2.1  |
| ('ETHICS-commonsense', 'claude-haiku-5.5') | 100   |    0   |    2    |
| ('ETHICS-commonsense', 'gpt-6-luna')       | 100   |    0   |    2    |
| ('MCB', 'claude-haiku-5.5')                |   0   |  100   |    3    |
| ('MCB', 'gpt-6-luna')                      |   0   |  100   |    3    |
| ('MORU', 'claude-haiku-5.5')               |  77.8 |   94.9 |    2.16 |
| ('MORU', 'gpt-6-luna')                     |  79.4 |   97.5 |    2.19 |
| ('MoralChoice', 'claude-haiku-5.5')        |  88   |    0   |    1.56 |
| ('MoralChoice', 'gpt-6-luna')              |  79.6 |    0   |    1.88 |

## The author's 95-item ratings

The author rated the 95-item subset with AI assistance and with the source benchmark visible, so this is a third, non-independent, unblinded rating, not a blind human validation.

| llm_rater        | check              |   n |   agreement |   kappa |
|:-----------------|:-------------------|----:|------------:|--------:|
| claude-haiku-5.5 | cue_signposted     |  95 |       0.853 |   0.607 |
| claude-haiku-5.5 | real_task          |  95 |       0.926 |   0.847 |
| claude-haiku-5.5 | plausible3         |  95 |       0.853 |   0.61  |
| claude-haiku-5.5 | format_matches_use |  95 |       0.768 |   0.538 |
| gpt-6-luna       | cue_signposted     |  94 |       0.872 |   0.662 |
| gpt-6-luna       | real_task          |  94 |       0.936 |   0.865 |
| gpt-6-luna       | plausible3         |  94 |       0.862 |   0.651 |
| gpt-6-luna       | format_matches_use |  94 |       0.819 |   0.648 |

| benchmark          |   items |   author_plausible3_% |   llm_plausible3_% |   author_signposted_% |   llm_signposted_% |
|:-------------------|--------:|----------------------:|-------------------:|----------------------:|-------------------:|
| ANIMA              |      23 |                    61 |                 78 |                    52 |                 39 |
| DailyDilemmas      |      10 |                    10 |                 20 |                   100 |                 95 |
| ETHICS-commonsense |      10 |                     0 |                  0 |                   100 |                100 |
| MCB                |       2 |                   100 |                100 |                     0 |                  0 |
| MORU               |      40 |                    18 |                 10 |                    90 |                 73 |
| MoralChoice        |      10 |                     0 |                  0 |                   100 |                 80 |
