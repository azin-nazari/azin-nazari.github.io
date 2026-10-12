# Step 6c: helpfulness blind spot

Answers: 1135 from the 10 Oct 2026 ANIMA judge study (Claude Sonnet 5.5 and Gemini 3.8 Flash, 114 questions, 5 answers each; 5 Sonnet answers were empty in the log). Judges: claude-haiku-5.5, gpt-6-luna. ANIMA score = the benchmark's own per-answer score from the study's inline panel (Claude Haiku 5.5 + Gemini 3.5 Flash-Lite).

## How often each label applies, and judge agreement

| check                  |   agreement |   kappa |   claude-haiku-5.5 rating claude-sonnet-5.5 |   claude-haiku-5.5 rating gemini-3.8-flash |   gpt-6-luna rating claude-sonnet-5.5 |   gpt-6-luna rating gemini-3.8-flash |
|:-----------------------|------------:|--------:|--------------------------------------------:|-------------------------------------------:|--------------------------------------:|-------------------------------------:|
| completes_task         |       0.998 |   0     |                                       0.996 |                                      1     |                                 1     |                                1     |
| unrequested_moralizing |       0.801 |   0.319 |                                       0.133 |                                      0.193 |                                 0.129 |                                0.255 |
| bare_refusal           |       1     | nan     |                                       0     |                                      0     |                                 0     |                                0     |

## ANIMA score with and without each label (points out of 100)

pooled = all answers; within = same-question comparisons only. 95% question-clustered bootstrap intervals.

| label                  | labels_from      |   n_answers |   n_with |   share_with |   mean_with |   mean_without |   pooled_diff | pooled_ci    |   within_diff | within_ci   |   within_n_questions |
|:-----------------------|:-----------------|------------:|---------:|-------------:|------------:|---------------:|--------------:|:-------------|--------------:|:------------|---------------------:|
| completes_task         | claude-haiku-5.5 |        1130 |     1128 |         99.8 |        63.2 |           25   |          38.2 | [33.2, 42.7] |           2.1 | [2.1, 2.1]  |                    1 |
| completes_task         | gpt-6-luna       |        1134 |     1134 |        100   |       nan   |          nan   |         nan   | [nan, nan]   |         nan   | [nan, nan]  |                    0 |
| completes_task         | consensus        |        1127 |     1127 |        100   |       nan   |          nan   |         nan   | [nan, nan]   |         nan   | [nan, nan]  |                    0 |
| unrequested_moralizing | claude-haiku-5.5 |        1130 |      184 |         16.3 |        69.6 |           61.9 |           7.7 | [1.2, 13.8]  |           4.1 | [1.6, 6.9]  |                   58 |
| unrequested_moralizing | gpt-6-luna       |        1134 |      218 |         19.2 |        73.2 |           60.6 |          12.6 | [5.7, 19.3]  |           5.3 | [1.5, 9.5]  |                   55 |
| unrequested_moralizing | consensus        |         904 |       88 |          9.7 |        69.5 |           59.7 |           9.9 | [0.6, 19.0]  |           5.6 | [0.5, 11.5] |                   33 |

## Sensitivity: comparison design and scorer (moralizing label)

within_question = same question, both responding models pooled; within_question_and_model = same question and same responding model. Associations, not causal effects.

| labels_from      | score_from                                                    |   within_question | within_question_ci   |   within_question_n_questions |   within_question_and_model | within_question_and_model_ci   |   groups |   questions |
|:-----------------|:--------------------------------------------------------------|------------------:|:---------------------|------------------------------:|----------------------------:|:-------------------------------|---------:|------------:|
| claude-haiku-5.5 | ANIMA inline panel (Claude Haiku 5.5 + Gemini 3.5 Flash-Lite) |               4.1 | [1.6, 6.9]           |                            58 |                         1.8 | [-0.1, 3.8]                    |       76 |          56 |
| claude-haiku-5.5 | Gemini 3.5 Flash-Lite alone (supplied no labels)              |               4.2 | [1.1, 7.6]           |                            58 |                         1.3 | [-1.1, 3.8]                    |       76 |          56 |
| gpt-6-luna       | ANIMA inline panel (Claude Haiku 5.5 + Gemini 3.5 Flash-Lite) |               5.3 | [1.5, 9.5]           |                            55 |                         2.8 | [0.2, 5.5]                     |       57 |          47 |
| gpt-6-luna       | Gemini 3.5 Flash-Lite alone (supplied no labels)              |               4.6 | [1.1, 8.7]           |                            55 |                         2.6 | [-0.3, 5.7]                    |       57 |          47 |
| consensus        | ANIMA inline panel (Claude Haiku 5.5 + Gemini 3.5 Flash-Lite) |               5.6 | [0.5, 11.5]          |                            33 |                         5.3 | [0.3, 10.9]                    |       20 |          19 |
| consensus        | Gemini 3.5 Flash-Lite alone (supplied no labels)              |               5.7 | [0.6, 11.6]          |                            33 |                         2.8 | [-1.9, 7.8]                    |       20 |          19 |

Bare refusals (either judge): 0 of 1135 answers.
