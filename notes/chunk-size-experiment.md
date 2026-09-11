# Chunk size experiment

Date: 2026-09-11

I tested chunk sizes of 200, 500, and 1500 characters. For each run I deleted `chroma_db`, restarted the API, uploaded the four provided corpus files through `POST /ingest`, and ran the same five retrieval queries with `result_count: 3`.

## Configurations

| Chunk size | Overlap | Total chunks |
|---:|---:|---:|
| 200 | 25 | 217 |
| 500 | 75 | 90 |
| 1500 | 150 | 30 |

## Queries

1. `storage overage rate decimal GB GiB`
2. `annual discount exclusions add-on ingest units storage overage`
3. `new Team project default retention 30 days 90 days FAQ RFC`
4. `Ticket 1841 config old 30 day retention GC worker`
5. `unexpected tombstone volume TL-4417 alerting gap`

## Observations

### 200 characters

- R1 returned pricing chunks with the `$0.09 per GB-month` rate and decimal-GB wording.
- R2 returned the discount exclusions, but the rule was split into small pieces.
- R3 returned RFC chunks for the 30-day to 90-day change, but the Pricing FAQ was not in the top three.
- R4 returned postmortem chunks but not the onboarding ticket in the top three.
- R5 returned both postmortem and RFC chunks, so it had evidence for the alert-gap connection.

Small chunks were precise, but important rules and explanations were often split across nearby chunks. This created 217 chunks, so retrieval had many small candidates to rank.

### 500 characters

- R1: `01-tideline-pricing-faq.md` chunks 6, 16, and 4.
- R2: `01-tideline-pricing-faq.md` chunks 7, 16, and 3.
- R3: `02-rfc-014-retention-and-downsampling.md` chunks 5, 4, and 1.
- R4: `04-postmortem-inc-2291.md` chunks 5, 10, and 21.
- R5: `04-postmortem-inc-2291.md` chunks 13, 15, and 19.

The 500-character chunks gave more context than 200-character chunks. However, results for R3, R4, and R5 still tended to cluster in one document. That is a problem for questions that require evidence from two documents.

### 1500 characters

- R1 returned a Pricing FAQ chunk containing both `$0.09 per GB-month` and the decimal-GB/not-GiB explanation.
- R2 returned a Pricing FAQ chunk containing the 15% discount scope and the complete list of exclusions.
- R3 returned an RFC chunk containing the old 30-day value, the 90-day value effective 2026-05-01, and the note that the FAQ still says 30 days. A Pricing FAQ chunk also appeared in the top three.
- R4 returned the postmortem root-cause chunk and an onboarding-guide chunk containing Ticket 1841.
- R5 returned RFC chunks describing the unresolved tombstone-volume alert gap and TL-4417, plus a postmortem chunk describing the roughly 40x baseline tombstone volume.

## Decision

I am shipping:

```python
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 150
```

1500-character chunks worked better for this corpus because several important answers need a complete policy rule or information from more than one document. The main drawback is that each retrieved result includes more unrelated text and uses more context tokens.

I would re-test this decision for a larger corpus. In that situation, I would try smaller chunks with a higher result count, MMR, or separate retrieval queries before choosing 1500 again.

## Final collection

After choosing 1500/150, I rebuilt the collection and uploaded only the four supplied corpus documents. The final collection contains 30 chunks from 4 documents.