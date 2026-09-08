# RFC-014: Retention Tiers, Downsampling and Deletion

**Status:** Accepted
**Authors:** P. Okonkwo (storage), M. Halvorsen (storage), R. Bhatt (SRE)
**Created:** 2026-03-02
**Accepted:** 2026-04-11
**Supersedes:** RFC-006 (Retention v1), RFC-009 (Rollup prototype)
**Audience:** Engineering (internal)

---

## 1. Summary

This RFC defines how Tideline stores raw data points, how it downsamples them into coarser rollup tiers over time, and how expired data is deleted. It replaces the flat single-retention model of RFC-006, under which every project stored raw resolution for its full retention window.

The change reduces storage cost per project by an estimated 71% at the median, at the cost of raw resolution beyond 14 days.

---

## 2. Terminology

- **Data point** — one timestamp-value pair in one series.
- **Series** — a unique combination of metric name and tag set.
- **Raw shard** — an immutable 2-hour block of full-resolution points.
- **Rollup tier** — a derived, pre-aggregated view of a raw shard at a coarser interval.
- **Watermark** — the timestamp before which all raw shards for a project are known to be sealed and eligible for compaction.
- **Tombstone** — a deletion marker written to the metadata store; the data itself is removed later by the garbage collector.

---

## 3. Retention tiers

Every project stores four tiers. Tier lifetimes are fixed and not individually configurable by customers.

| Tier | Interval | Lifetime | Aggregations stored |
|---|---|---|---|
| Raw | native | **14 days** | — |
| Fine rollup | 1 minute | **90 days** | min, max, sum, count, last |
| Coarse rollup | 1 hour | **400 days** | min, max, sum, count, last |
| Archive rollup | 1 day | **5 years** | min, max, sum, count |

A project's *advertised retention* (the number surfaced in the console and in commercial documents) is the window over which queries return data at any resolution. The tier lifetimes above are the internal implementation of that window and are deliberately longer than the shortest advertised retention.

### 3.1 Default advertised retention

Prior to 2026-05-01, new projects on the Team plan were created with a 30-day advertised retention window.

**Effective 2026-05-01, the default advertised retention for new Team projects is 90 days.** This aligns Team with the fine rollup tier lifetime and removes a class of confusing "your data exists but you cannot query it" support tickets.

Existing Team projects created before 2026-05-01 keep their 30-day window until they are migrated. The migration is described in section 8.

Note for reviewers: the customer-facing pricing FAQ still states 30 days for Team as of this RFC's acceptance date. RevOps has been notified. Until the FAQ is republished, support should treat the RFC as authoritative for what the system does and the FAQ as authoritative for what a customer was told at signup.

---

## 4. Downsampling

### 4.1 Compaction schedule

The compaction worker runs **every 6 hours** per project (00:00, 06:00, 12:00, 18:00 UTC, jittered by up to 20 minutes to spread load).

Each run:

1. Advances the project watermark to `now - 2 hours`.
2. Selects sealed raw shards newer than the last compaction point.
3. Computes fine rollups, then derives coarse rollups from fine, and archive rollups from coarse.
4. Writes rollups, then records the compaction point.

Rollups are derived hierarchically rather than each being computed from raw. This is 4-6x cheaper and means a bug in fine rollup computation propagates upward — see section 7.

### 4.2 Aggregation semantics

`sum` and `count` are stored so that averages can be computed at query time without loss. Storing `avg` directly would make re-aggregation across intervals incorrect, which was the defect that killed RFC-009.

Gauges, counters and histograms are all treated identically by the rollup pipeline. Counter resets are **not** detected during downsampling; reset handling happens at query time in TideQL.

### 4.3 Late and out-of-order writes

The **backfill window is 48 hours**. Writes with a timestamp older than 48 hours are rejected with:

```
HTTP 409 Conflict
{"error": "backfill_window_exceeded", "oldest_accepted": "<timestamp>"}
```

Writes inside the backfill window but older than the watermark mark the affected raw shards dirty and trigger recompaction of the affected rollup ranges on the next scheduled run. Recompaction is not immediate; a late write may take up to 6 hours to appear in rollup-resolution queries.

**The 48-hour limit is a hard constraint, not a configurable one.** There is no operator override and no support-initiated bypass. Historical bulk loads must go through the offline import path described in RFC-011.

---

## 5. Deletion

Deletion is asynchronous and two-phase.

1. **Tombstone.** The retention enforcer runs hourly, identifies tiers past their lifetime, and writes tombstones. Tombstoned data is immediately excluded from query results.
2. **Garbage collection.** The GC worker reclaims tombstoned blocks. Nominal completion is **within 24 hours** of tombstoning. Under sustained write load or during compaction backlog, GC may lag up to **72 hours**.

Between tombstone and GC, data is present on disk but unreachable through any public API. It is recoverable only by a manual storage-team intervention against the tombstone log, and only before GC completes.

**Tombstones are not reversible through any customer-facing or support-facing tool.** This is deliberate: a reversible delete path was rejected in review as a data-governance risk under customer DPAs.

---

## 6. Limits

| Limit | Value | Behaviour on breach |
|---|---|---|
| Active series per project | 500,000 | New series rejected with 422; existing series unaffected |
| Tags per series | 40 | Write rejected with 422 |
| Tag key length | 128 bytes | Write rejected with 422 |
| Tag value length | 512 bytes | Write rejected with 422 |
| Raw shard size | 512 MB | Shard split automatically |
| Concurrent compaction jobs per node | 4 | Queued |

"Active" means written to within the last 7 days. Series that go inactive are not counted against the limit but continue to occupy storage until their tiers expire.

---

## 7. Failure modes and alerting

| Alert | Condition | Severity |
|---|---|---|
| `TL-COMPACT-LAG` | Compaction point older than **12 hours** | P2 |
| `TL-GC-BACKLOG` | Tombstoned bytes pending GC above 2 TB per region | P3 |
| `TL-ROLLUP-MISMATCH` | Sampled fine-rollup recomputation differs from stored by more than 0.1% | P1 |
| `TL-WATERMARK-STALL` | Watermark unchanged for 3 consecutive runs | P2 |

Known gaps at time of acceptance:

- There is **no alert on unexpected tombstone volume.** A retention misconfiguration that tombstones far more data than usual will not page anyone. This was raised in review and deferred to a follow-up (TL-4417) on the grounds that tombstone volume is naturally spiky and a useful threshold was not obvious.
- `TL-COMPACT-LAG` fires on compaction lag only. It does not observe the retention enforcer, which runs on a separate schedule and a separate code path.
- Rollup correctness sampling covers 1 in 500 shards. A localised corruption is unlikely to be sampled.

---

## 8. Migration plan

Existing Team projects move to the 90-day default in batches of 200 projects, one batch per deploy train, starting 2026-05-04.

Per batch:

1. Update the project's `advertised_retention_days` in the control-plane database.
2. Publish a config invalidation event to the `retention.config` topic.
3. Verify that the retention enforcer and GC worker for the affected shards have picked up the new value before proceeding to the next batch.

Step 3 is a manual check against the worker's exposed config endpoint. Automating it is tracked in TL-4402.

Note on config propagation: the control-plane config cache has a **15-minute TTL**, but not every worker re-reads config on TTL expiry. Workers that read retention config at process start hold it until restart. The storage team's position is that all retention-path workers re-read on the invalidation event; this has not been verified end to end for the GC worker.

---

## 9. Regional availability

| Region | Raw + rollup tiers | Notes |
|---|---|---|
| `us-east-1` | GA | Reference region |
| `ap-southeast-2` | GA since 2026-04-01 | |
| `eu-west-1` | **Not GA** | Downsampling runs in shadow mode only; queries still served from raw. Target GA Q3 2026. |

`eu-west-1` projects therefore retain raw resolution for their full advertised window and cost materially more per project to serve. This is not currently reflected in pricing.

---

## 10. Rejected alternatives

- **Customer-configurable tier lifetimes.** Rejected: multiplies the retention-enforcer state space, and the support burden of explaining tier interactions was judged worse than the flexibility gained.
- **Synchronous deletion.** Rejected: deletion latency would be bounded by GC throughput, making retention enforcement a write-path dependency.
- **Computing every rollup tier from raw.** Rejected on cost (4-6x) despite better fault isolation. Revisit if `TL-ROLLUP-MISMATCH` fires more than twice per quarter.
- **Extending the backfill window to 7 days.** Rejected: recompaction cost grows with the square of the window in the current design.

---

## 11. Open questions

1. Should `eu-west-1` carry a price premium until downsampling is GA there? Deferred to RevOps.
2. What is the right threshold for a tombstone-volume alert? (TL-4417)
3. Do we need a break-glass path to halt GC region-wide during a retention incident? Currently the only mechanism is scaling the GC deployment to zero replicas, which is undocumented outside the storage team runbook.
