# Stage 4 — First Evaluation Run Analysis

**Date:** 2026-09-11  
**Collection:** 30 chunks from the four supplied corpus documents  
**Chunking configuration:** 1500-character chunks with 150-character overlap  
**Execution method:** HTTP calls to `POST /agent/query`, with `return_trace=true`

## Scope

The supplied question bank contains 18 A–F questions and one three-turn G1
conversation scenario. I added six original questions. I recorded G1 as three
separate HTTP-request rows because each turn requires its own tool trace and
memory behaviour check.

Therefore, this run contains:

- 18 A–F request rows
- 3 G1 request rows
- 6 custom request rows
- 27 recorded request rows in total

## Baseline result

The first unattended baseline run produced **18 passes and 9 failures out of
27 recorded request rows**.

I did not tune the agent before completing this baseline. I first reviewed
tool paths, final answers, and saved traces to distinguish agent failures from
false negatives caused by overly literal automated substring checks.

## Failure classification

| ID | Initial result | Classification | Diagnosis |
|---|---|---|---|
| A1 | Fail | Harness false negative | The answer correctly stated `$0.09 per GB-month` and decimal GB rather than GiB. The automated text rule did not recognise the valid phrasing. |
| B1 | Fail | Prompt | The agent reported only the 90-day default and omitted the contradictory 30-day customer-facing FAQ value. It did not clearly attribute both values to their respective sources. |
| C1 | Fail | Retrieval | The answer did not include the required 48-hour backfill window or the fact that no operator override or support bypass exists. The necessary multi-document evidence was not successfully synthesised. |
| D1 | Fail | Model | The agent repeatedly retrieved documents, encountered parser exceptions, reached the 10-step cap, and never returned the required `$4,188` calculation. The repeated failures show unreliable ReAct-format following and loop completion for this multi-part calculation. |
| E2 | Fail | Harness false negative | The response correctly said that available documentation contains no Scale-plan uptime SLA, but the test expected a more literal wording. |
| G1 Turn 2 | Fail | Partial retrieval/content weakness | Session history correctly resolved “the testing section” to the onboarding guide, but the answer did not fully provide the soak-test details required by the evaluation criteria. |
| G1 Turn 3 | Fail | Prompt/tool-path | The model produced a suitable table from session history but made no retrieval call. The supplied evaluation requires retrieval on each G1 turn, so this is a tool-path failure despite a useful final answer. |
| CUSTOM2 | Fail | Arithmetic | The response computed the 40-million-point excess but did not complete the required multiplication by `$0.80 per million` to state the `$32.00` daily overage. |
| CUSTOM4 | Fail | Harness false negative | The answer `HTTP 409 Conflict` was correct. The failure came from the evaluator rule rather than the agent. |

## Important passed-but-weak cases

- **C1:** Later passed, but required seven retrieval calls and approximately
  59 seconds. This indicates inefficient repeated retrieval before synthesis.
- **E2:** Later passed, but required four retrieval calls and approximately
  43 seconds for an unanswerable question. The agent should stop earlier once
  the available evidence is sufficient to say that no answer is published.
- **CUSTOM2:** Later passed, but emitted parser exception steps before arriving
  at the calculation. The result is correct but formatting reliability remains
  weak.
- **D3:** Passed despite parser exceptions. This is evidence that a pass alone
  does not mean the execution path is robust.
- **D1:** Failed again in the second run, so it remains the highest-priority
  real reliability failure.

## Harness corrections after baseline

After the first baseline, I corrected only false-negative evaluation rules. I
did not change the agent before the second run.

The corrections made automated checks less dependent on exact model phrasing.
For example, valid expressions such as “there is no mention of an uptime SLA”
must be accepted as equivalent to “not published,” while source attribution
for B1 is inspected manually from the full answer and trace rather than
relying solely on literal substring matching.

## Second-run comparison

The second run produced **23 passes and 4 failures out of 27 request rows**.

Several first-run failures became passes, including C1, G1 Turn 2, G1 Turn 3,
CUSTOM2, and CUSTOM4. However, D1 still failed because the agent reached the
iteration limit without producing a usable answer. B1 and CUSTOM6 exposed the
remaining limitation of literal substring-based checks: correct semantic
answers can be falsely marked as failures when wording differs.

This comparison shows why the harness records traces, tool paths, latency, and
full answers rather than relying only on a pass count.