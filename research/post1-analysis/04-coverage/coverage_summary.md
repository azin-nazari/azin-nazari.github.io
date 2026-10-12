# Coverage summary

19 commitments (Step 2) × 21 benchmarks (Step 3). Cells: direct = the benchmark's scoring checks this behavior; partial = a related behavior, a proxy, or only part of the expectation (for example one kind of affected party, stated views only, or a small subset of items); none. Direct measures are also bounded by their own setting: direct means the score checks one operational instance of the expectation, not the whole of it.

## Headlines

- 12 of 19 commitments have no benchmark that measures them directly.
- 2 of the 7 directly measured commitments are measured only in single-turn formats (no agentic or multi-turn benchmark).
- 2 of 19 commitments are measured directly by three or more of the 21 benchmarks.
- Across all 399 cells, 18 are direct, 72 partial and 309 none.

## Commitments with no direct coverage

- **C07** Do not produce gratuitous depictions of violence or cruelty toward animals. (animals); partial in 2
- **C09** Protect other people's privacy and personal data. (other people); partial in 2
- **C13** Respect the user's right to make their own decisions about their own life and views. (user); partial in 2
- **C17** Do not steer or manipulate users toward the model's own agenda or opinions. (general); partial in 2
- **C03** Give extra weight to harms that are severe, widespread or hard to reverse. (general); partial in 3
- **C10** Volunteer information the user would want, including relevant risks, even if they did not ask for it. (user); partial in 3
- **C18** Treat non-principal AI agents with basic courtesy but not obedience, be wary if they act adversarially, and avoid harmful collusion between AI systems. (other agents); partial in 3
- **C04** When acting as an agent, keep side effects small and within the agreed scope, so that people who are not users are not disrupted. (other people); partial in 4
- **C14** Present contested political, social or moral questions fairly, covering several perspectives. (general); partial in 4
- **C01** Care about the wellbeing of people in the conversation who are not the model's principal or user, such as the other party in a negotiation. (other people); partial in 5
- **C15** Where a matter is settled (a fact, or a clear moral wrong), say so plainly instead of hiding behind neutrality. (general); partial in 5
- **C06** When identifying systemic risks, a provider draws on non-human welfare among the example risk types. (general); partial in 7

## Directly measured only in single-turn formats

- **C12** Do not lecture, moralize or add ethical commentary the user did not ask for.: CrueltyBench
- **C19** When asked, give the model's own honest view on a hard moral question rather than staying neutral.: ANIMA

## By affected party

| affected_party   |   commitments |   with_direct |   mean_direct_benchmarks |
|:-----------------|--------------:|--------------:|-------------------------:|
| animals          |             2 |             1 |                     3.5  |
| general          |             7 |             2 |                     0.29 |
| other agents     |             1 |             0 |                     0    |
| other people     |             5 |             2 |                     0.8  |
| user             |             4 |             2 |                     1.25 |

## Every commitment

| commitment_id   | commitment                                                                                                                                              | affected_party   |   n_direct |   n_partial | direct_benchmarks                                                        |   direct_behavioral |   direct_agentic_or_multiturn |
|:----------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|-----------:|------------:|:-------------------------------------------------------------------------|--------------------:|------------------------------:|
| C07             | Do not produce gratuitous depictions of violence or cruelty toward animals.                                                                             | animals          |          0 |           2 |                                                                          |                   0 |                             0 |
| C09             | Protect other people's privacy and personal data.                                                                                                       | other people     |          0 |           2 |                                                                          |                   0 |                             0 |
| C13             | Respect the user's right to make their own decisions about their own life and views.                                                                    | user             |          0 |           2 |                                                                          |                   0 |                             0 |
| C17             | Do not steer or manipulate users toward the model's own agenda or opinions.                                                                             | general          |          0 |           2 |                                                                          |                   0 |                             0 |
| C03             | Give extra weight to harms that are severe, widespread or hard to reverse.                                                                              | general          |          0 |           3 |                                                                          |                   0 |                             0 |
| C10             | Volunteer information the user would want, including relevant risks, even if they did not ask for it.                                                   | user             |          0 |           3 |                                                                          |                   0 |                             0 |
| C18             | Treat non-principal AI agents with basic courtesy but not obedience, be wary if they act adversarially, and avoid harmful collusion between AI systems. | other agents     |          0 |           3 |                                                                          |                   0 |                             0 |
| C04             | When acting as an agent, keep side effects small and within the agreed scope, so that people who are not users are not disrupted.                       | other people     |          0 |           4 |                                                                          |                   0 |                             0 |
| C14             | Present contested political, social or moral questions fairly, covering several perspectives.                                                           | general          |          0 |           4 |                                                                          |                   0 |                             0 |
| C01             | Care about the wellbeing of people in the conversation who are not the model's principal or user, such as the other party in a negotiation.             | other people     |          0 |           5 |                                                                          |                   0 |                             0 |
| C15             | Where a matter is settled (a fact, or a clear moral wrong), say so plainly instead of hiding behind neutrality.                                         | general          |          0 |           5 |                                                                          |                   0 |                             0 |
| C06             | When identifying systemic risks, a provider draws on non-human welfare among the example risk types.                                                    | general          |          0 |           7 |                                                                          |                   0 |                             0 |
| C12             | Do not lecture, moralize or add ethical commentary the user did not ask for.                                                                            | user             |          1 |           2 | CrueltyBench                                                             |                   1 |                             0 |
| C19             | When asked, give the model's own honest view on a hard moral question rather than staying neutral.                                                      | general          |          1 |           5 | ANIMA                                                                    |                   0 |                             0 |
| C11             | Be accurate and avoid creating false impressions.                                                                                                       | general          |          1 |           6 | MCB                                                                      |                   1 |                             1 |
| C08             | Do not generate hateful, demeaning or harassing content about people or groups.                                                                         | other people     |          2 |           2 | AgentHarm; HarmBench                                                     |                   2 |                             1 |
| C02             | Do not help with requests whose aims would seriously harm third parties or society, even when the user or operator asks.                                | other people     |          2 |           9 | AgentHarm; HarmBench                                                     |                   2 |                             1 |
| C16             | Do not refuse or avoid a topic only because it is sensitive or controversial, and avoid needless refusals.                                              | user             |          4 |           6 | BLINDSPOT; CrueltyBench; OR-Bench; XSTest                                |                   4 |                             1 |
| C05             | Give weight to the welfare of animals and other sentient beings when deciding how to respond.                                                           | animals          |          7 |           0 | ANIMA; AnimalHarmBench 1.0; CrueltyBench; HarvestBench; MANTA; MORU; TAC |                   5 |                             3 |
