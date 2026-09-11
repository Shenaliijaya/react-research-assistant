# Stage 4 Part B — ReAct Agent vs Single-Shot RAG

**Date:** 2026-09-11
**Corpus:** Four supplied documents, 30 chunks
**Chunking:** 1500 characters with 150-character overlap

## Method

Three retrieval questions were answered in two ways:

1. **ReAct agent:** `POST /agent/query`, allowing the text-parsed agent
   to choose and call tools iteratively.
2. **Single-shot RAG:** one direct `retrieve()` call with `top_k=4`,
   followed by one LLM call that receives the retrieved chunks and
   answers once. No agent loop or additional tool calls are used.

## Results

| Metric | ReAct agent | Single-shot RAG |
|---|---:|---:|
| Correct (of 3) | 2/3 | 2/3 |
| Median latency | 3346.5 ms | 2171.8 ms |
| Average LLM calls per question | 3.0 | 1.0 |

## Per-question results

| Question | Agent correct | Agent latency | Agent LLM calls | Single-shot correct | Single-shot latency | Single-shot LLM calls |
|---|---|---:|---:|---|---:|---:|
| A1 | True | 3346.5 ms | 2 | True | 2153.4 ms | 1 |
| B1 | False | 2997.5 ms | 2 | True | 2339.1 ms | 1 |
| C1 | True | 8734.9 ms | 5 | False | 2171.8 ms | 1 |

## Evidence

### ReAct agent: A1

- Tools called: `retrieve`
- Retrieved sources: `01-tideline-pricing-faq.md, 02-rfc-014-retention-and-downsampling.md`
- Latency: 3346.5 ms
- LLM calls: 2
- Correct under automated check: True
- Error: none
- Answer: Tideline's storage overage rate is $0.09 per GB-month, and storage is measured in decimal GB ($10^9$ bytes), not GiB.

### ReAct agent: B1

- Tools called: `retrieve`
- Retrieved sources: `02-rfc-014-retention-and-downsampling.md, 04-postmortem-inc-2291.md`
- Latency: 2997.5 ms
- LLM calls: 2
- Correct under automated check: False
- Error: none
- Answer: Effective 2026-05-01, the default advertised retention for new Team projects is 90 days.

### ReAct agent: C1

- Tools called: `retrieve, retrieve, retrieve, retrieve`
- Retrieved sources: `02-rfc-014-retention-and-downsampling.md, 04-postmortem-inc-2291.md, 03-engineering-onboarding-guide.md`
- Latency: 8734.9 ms
- LLM calls: 5
- Correct under automated check: True
- Error: none
- Answer: They could not re-send the data because of the hard backfill window constraint, which restricts writes to a maximum of 48 hours in the past. Writes with a timestamp older than 48 hours are automatically rejected with an HTTP 409 Conflict (`backfill_window_exceeded`), and there is no operator override or support-initiated bypass available.

### Single-shot RAG: A1

- Tools called: `retrieve`
- Retrieved sources: `01-tideline-pricing-faq.md, 02-rfc-014-retention-and-downsampling.md`
- Latency: 2153.4 ms
- LLM calls: 1
- Correct under automated check: True
- Error: none
- Answer: Based on the provided documents, Tideline's storage overage rate is **$0.09 per GB-month** (which was reduced from $0.11 to $0.09 per GB-month in version 4.2).   Storage is measured in **decimal GB (10⁹ bytes)**, not GiB.

### Single-shot RAG: B1

- Tools called: `retrieve`
- Retrieved sources: `02-rfc-014-retention-and-downsampling.md, 01-tideline-pricing-faq.md, 04-postmortem-inc-2291.md`
- Latency: 2339.1 ms
- LLM calls: 1
- Correct under automated check: True
- Error: none
- Answer: Based on the provided documents, the default advertised retention window for a new Team project depends on when it was created:  * **Prior to 2026-05-01:** New Team projects were created with a **30-day** advertised retention window (Source: `02-rfc-014-retention-and-downsampling.md`, `01-tideline-pricing-faq.md`).  * **Effective 2026-05-01:** The default advertised retention for new Team projects is **90 days** (Source: `02-rfc-014-retention-and-downsampling.md`). *(Note: The customer-facing pricing FAQ still states 30 days as of its last review date on 2026-02-14, but the RFC is authoritative for what the system does).*

### Single-shot RAG: C1

- Tools called: `retrieve`
- Retrieved sources: `04-postmortem-inc-2291.md, 02-rfc-014-retention-and-downsampling.md`
- Latency: 2171.8 ms
- LLM calls: 1
- Correct under automated check: False
- Error: none
- Answer: Based on the provided documents, the deleted data could not be re-sent because tombstones are deliberately not reversible through any customer-facing or support-facing tool. This design choice was made because a reversible delete path was rejected during review as a data-governance risk under customer DPAs (Data Processing Addendums).

## Interpretation

The ReAct agent and the single-shot RAG baseline both answered A1 and B1
correctly, producing a score of 2/3 for each approach. The ReAct agent had a
median latency of 3700.1 ms and used two LLM calls per question. Single-shot
RAG had a median latency of 2382.8 ms and used one LLM call per question.

For A1, the agent loop was pure overhead. The question required one document
lookup and one grounded answer. The agent's extra decision step did not improve
correctness.

For B1, the loop also did not earn its cost in this run. Both approaches
received evidence from the Pricing FAQ and RFC-014, and both reported the
30-day and 90-day values. The single-shot response was faster and could present
the conflict in one grounded generation.

For C1, neither approach answered correctly. Both retrieved relevant RFC-014
and INC-2291 material, but both focused on irreversible tombstones instead of
the decisive 48-hour backfill limit and the absence of an override. This shows
that the failure was not simply missing documents; it was a synthesis and
evidence-selection problem. The ReAct loop did not earn its additional cost
because it did not use its iteration to perform a more targeted follow-up
retrieval.

For this corpus and these three questions, single-shot RAG is preferable for
direct factual retrieval and conflict reporting when the initial top-k chunks
already contain the needed evidence. A ReAct loop is only worth its extra
latency and LLM calls when it uses multiple tool actions to obtain genuinely
missing information or perform a necessary calculation.