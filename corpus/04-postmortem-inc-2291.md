# Postmortem: INC-2291 — Premature deletion of raw data during retention migration

**Severity:** SEV-2
**Date of incident:** 2026-05-06
**Duration:** 09:14 – 18:34 UTC (9h 20m)
**Author:** R. Bhatt (SRE)
**Reviewers:** P. Okonkwo (storage), D. Ferreira (support), J. Lindqvist (EM)
**Published:** 2026-05-12
**Status:** Action items open

Blameless postmortem. The purpose of this document is to understand the system, not the people operating it.

---

## 1. Summary

During batch 3 of the RFC-014 retention migration, the garbage collection worker in `us-east-1` continued to enforce the **old 30-day** retention value for projects that had already been migrated to a **90-day** advertised window. Raw shards and fine rollups between 30 and 90 days old were tombstoned and then garbage collected for 14 Team-tier projects.

Approximately **3.1 billion data points** were deleted earlier than the migrated policy allowed. Coarse and archive rollup tiers were unaffected, so the data was recoverable at 1-hour and 1-day resolution but **not at raw or 1-minute resolution**.

Four customers were affected. Two requested service credits, totalling **$2,610**.

The incident was detected by a customer support ticket, not by monitoring.

---

## 2. Impact

| Measure | Value |
|---|---|
| Projects affected | 14 |
| Organisations affected | 4 |
| Data points deleted prematurely | ~3.1 billion |
| Time range of deleted data | 30-90 days before incident |
| Recoverable at 1-hour resolution | Yes, all of it |
| Recoverable at 1-minute or raw resolution | No |
| Customer-reported symptom | Queries returning empty results for the 30-90 day range |
| Service credits issued | $2,610 across 2 organisations |
| Customer churn attributable | 0 as of publication; 1 organisation asked about contract terms |

One affected organisation was running a quarterly capacity model off 1-minute data. They have rebuilt it against 1-hour rollups and reported the result as "usable but coarser than we would like."

---

## 3. Timeline (all times UTC, 2026-05-06)

| Time | Event |
|---|---|
| 10:00 (2026-05-04) | Migration batch 1 (200 projects) ships on the 10:00 deploy train. Manual verification of step 3 passes. |
| 14:00 (2026-05-05) | Batch 2 ships. Verification passes. |
| 10:00 | Batch 3 ships on the 10:00 train. Verification step 3 is performed against the **retention enforcer** config endpoint, which reports the new value. The GC worker is not separately checked. |
| 09:14 | *(prior day's batch)* Customer opens ticket 1841 reporting empty query results for the last 45 days despite a 90-day console value. Ticket enters the normal support queue as P3. |
| 11:02 | Support asks the customer for a project ID and a sample query. |
| 13:40 | Second organisation opens a similar ticket. Support notices the pattern and escalates. |
| 13:58 | Incident declared SEV-3. Storage on-call paged. |
| 14:26 | Storage confirms tombstones exist for shards inside the 90-day window on a migrated project. Severity raised to SEV-2. |
| 14:31 | GC deployment in `us-east-1` scaled to zero replicas to stop further reclamation. This is the only available mechanism and is documented only in the storage runbook. |
| 14:50 | Tombstone log analysis begins to determine scope. |
| 15:35 | Scope established: 14 projects, all from batch 3, all in `us-east-1`. |
| 15:41 | Attempt to identify data still tombstoned but not yet garbage collected. **All affected shards had already been reclaimed** — GC had completed within roughly 4 hours of tombstoning, well inside the 24-hour nominal window. |
| 16:20 | Root cause identified: GC worker pods had read retention config at process start and had not restarted since 2026-04-29. |
| 16:44 | GC worker deployment restarted; pods confirmed reading the new config values. |
| 17:10 | GC scaled back to normal replica count with the retention enforcer paused as a precaution. |
| 17:55 | Recovery plan agreed: no raw-resolution recovery possible; affected customers to be notified with 1-hour rollups confirmed intact. |
| 18:34 | Incident closed. Customer notifications sent. |

---

## 4. Root cause

The control-plane config cache has a 15-minute TTL. The retention enforcer subscribes to the `retention.config` invalidation topic and re-reads config on the invalidation event. **The GC worker does not subscribe to that topic.** It reads `advertised_retention_days` once at process start and holds the value for the lifetime of the pod.

Because the GC worker pods had not restarted in seven days, they were operating on config read on 2026-04-29 — before batch 3 projects were migrated. When the retention enforcer, using the new 90-day value, wrote tombstones only for data older than 90 days, that was correct. The premature tombstones came from the GC worker's own secondary retention check, a defensive consistency check added in 2025 to catch enforcer bugs, which independently tombstones anything it believes to be past retention.

The defensive check was designed on the assumption that the GC worker and the enforcer always agree on the retention value. Under a config skew, the check inverts its purpose: instead of catching enforcer bugs, it deletes data the enforcer correctly retained.

RFC-014 section 8 records that end-to-end config propagation "has not been verified end to end for the GC worker." That known gap is the direct cause of this incident.

---

## 5. Contributing factors

1. **No alert on tombstone volume.** RFC-014 section 7 lists this as a known gap, deferred as TL-4417. Tombstone volume during the incident was roughly 40x baseline for the affected region and would have been trivially detectable.
2. **`TL-COMPACT-LAG` does not observe the retention path.** The only retention-adjacent alert watches compaction lag, which was healthy throughout.
3. **Migration verification checked one worker of two.** RFC-014 step 3 says to verify "the retention enforcer and GC worker." In practice the runbook had a single check against the enforcer endpoint, and nobody noticed the RFC asked for more.
4. **GC completed faster than nominal.** The 24-hour nominal GC window created an informal assumption of a recovery buffer. Actual completion was about 4 hours, so by the time the incident was declared there was nothing left to recover.
5. **Tombstones are irreversible by design.** Correct for data governance, but it means the only recovery path is the rollup tiers.
6. **The 48-hour backfill window prevented customer self-recovery.** Two affected organisations still held the raw data in their own pipelines and offered to re-send it. Writes at 30-90 days old are rejected with 409 `backfill_window_exceeded` and there is no operator override. The offline import path (RFC-011) exists but requires a signed data-handling addendum and was judged too slow to be useful here.
7. **Ticket 1841 sat as P3 for over four hours.** "Queries return nothing" was read as a query-syntax question. Per our own severity definitions, silent incorrectness affecting some customers is a P2.

---

## 6. What went well

- Once the pattern was spotted, escalation to storage took 18 minutes.
- Scaling GC to zero was the right containment action and was taken 33 minutes after declaration.
- Coarse and archive rollup tiers were intact, so no data was lost at all resolutions — the hierarchical derivation described in RFC-014 section 4.1 meant the damage stopped at the fine tier.
- Customer notifications went out the same day, with specific per-project ranges rather than a generic notice.

---

## 7. What went badly

- We shipped a migration whose own RFC named an unverified assumption, and we did not verify it.
- Detection was a customer ticket. Mean time to detect was effectively four hours and twenty-six minutes from first report, and unbounded from first deletion.
- The containment mechanism was an undocumented replica scale-down known to one team.
- Our severity definitions were correct and we did not follow them.

---

## 8. Action items

| ID | Action | Owner | Due | Status |
|---|---|---|---|---|
| TL-4417 | Alert on tombstone volume deviating more than 5x from a 7-day baseline, per region | SRE | 2026-05-22 | In progress |
| TL-4431 | GC worker subscribes to `retention.config` invalidation; remove boot-time-only read | Storage | 2026-05-29 | In progress |
| TL-4432 | Remove the GC worker's independent retention check; make the enforcer the single writer of tombstones | Storage | 2026-06-12 | Open |
| TL-4402 | Automate migration step 3 verification across **all** retention-path workers | Storage | 2026-06-05 | Open |
| TL-4438 | Document a break-glass GC halt procedure outside the storage runbook; add `just gc-halt` | SRE | 2026-05-22 | Done |
| TL-4441 | Support triage guidance: "queries return nothing unexpectedly" is a P2 candidate, not P3 | Support | 2026-05-20 | Done |
| TL-4445 | Evaluate a time-boxed operator override for the backfill window during declared incidents | Storage | 2026-07-03 | Open |
| TL-4449 | Halt remaining migration batches until TL-4431 and TL-4402 ship | SRE | 2026-05-08 | Done |

Batches 4 onward are paused. 600 of approximately 2,400 eligible Team projects have been migrated.

---

## 9. Lessons

An RFC that documents a known unverified assumption is not the same as having verified it. Writing the gap down felt like managing the risk; it only recorded it. Where an RFC says something has not been verified end to end, that sentence should block the migration that depends on it.

A second lesson concerns defensive checks. The GC worker's independent retention check was added to make the system safer. It made the system more dangerous, because it duplicated authority over a destructive operation without duplicating the config path that authority depended on. Two components that can both delete data must agree on why, not merely on how.
