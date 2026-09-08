# Tideline — Pricing & Plans FAQ

**Halcyon Labs, Inc.**
Document owner: Revenue Operations
Audience: Customers and prospects (public)
Last reviewed: 2026-02-14
Version: 4.2

---

## What is Tideline?

Tideline is a managed time-series database for operational and product metrics. You send data points over HTTP or the native line protocol, Tideline stores them, downsamples them over time, and serves queries through TideQL.

This document covers commercial terms only. For storage internals, retention mechanics and downsampling behaviour, see RFC-014.

---

## 1. Plans

### 1.1 Developer — Free

- 1 ingest unit
- 7-day retention
- 1 project
- Community forum support only
- No SLA, no uptime commitment, no credits
- Intended for evaluation, side projects and local development

Developer projects that receive no writes for 45 consecutive days are archived. Archived projects can be restored within 90 days by opening a forum thread; after 90 days the data is deleted.

### 1.2 Team — $180 / month

- 5 ingest units included
- **30-day retention (default)**
- 5 projects
- 100 GB included storage
- Email support, 1 business day first response
- Additional ingest units: **$28 / month each**

### 1.3 Scale — $1,450 / month

- 40 ingest units included
- 90-day retention
- Unlimited projects
- 1 TB included storage
- Email and chat support, 4-hour first response during business hours
- Additional ingest units: **$22 / month each**

### 1.4 Enterprise — custom

Annual contract, negotiated commercial terms, single-tenant deployment option, SSO/SAML, custom data processing addendum. Contact sales. Pricing is not published.

---

## 2. What is an ingest unit?

**One ingest unit = 10 million data points per day.**

A data point is one timestamp-value pair written to one series. A single write request containing 40 fields across 2 series counts as 80 data points.

Ingest units are measured on a rolling daily basis in UTC. You are billed on your plan's included units regardless of usage; you are not refunded for unused capacity.

### 2.1 Overage

If you exceed your included ingest units on a given day, the excess is billed at **$0.80 per million data points**, calculated daily and summed at the end of the billing period.

Overage is billed rather than throttled on Team and Scale. On Developer, writes above the included unit are rejected with HTTP 429 for the remainder of the UTC day.

**Worked example.** A Team customer with 5 included units (50 million points/day) writes 63 million points on one day. The excess is 13 million points, billed at $0.80 per million = $10.40 for that day.

---

## 3. Storage

Included storage covers all resolutions after downsampling, measured as a daily average over the billing period.

- Team: 100 GB included
- Scale: 1 TB included
- Overage: **$0.09 per GB-month**

Storage is measured in decimal GB (10⁹ bytes), not GiB. The figure shown in the console dashboard is decimal GB and matches the invoice.

---

## 4. Annual prepay discount

Customers who prepay 12 months receive **15% off the plan base price and its included units**.

**The discount does not apply to:**

- additional ingest units purchased as add-ons
- ingest overage charges
- storage overage charges
- the Premium Support add-on
- the retention extension add-on

Annual prepay is invoiced once, in advance. Overage and add-ons accrued during the year are invoiced monthly in arrears at list price.

---

## 5. Add-ons

### 5.1 Premium Support — greater of $400/month or 12% of monthly spend

Includes a named support contact, 1-hour P1 response, and a quarterly review call. "Monthly spend" means base plus add-on units, and excludes overage charges and taxes.

### 5.2 Retention extension — $150 / month per project

Adds 30 days of retention to a single project, on top of the plan default. Can be stacked up to three times per project (maximum +90 days). Not available on Developer.

### 5.3 Additional regions — $75 / month per region per project

Projects are created in one primary region. Replication to an additional region can be enabled for eligible plans.

---

## 6. Billing mechanics

- All prices are in USD and exclude sales tax, VAT and GST.
- Monthly plans are invoiced in arrears on the first of the month, net 15.
- Payment by card, ACH, or wire. Wire requires a minimum $5,000 annual commitment.
- Plan upgrades take effect immediately and are prorated to the day.
- Plan downgrades take effect at the start of the next billing period and are **not** prorated.
- Monthly plans are not refunded for partial months.
- Annual prepay is refundable pro rata within the first 30 days only.

### 6.1 Cancellation and data export

On cancellation your projects become read-only for **30 days**, during which you can export via the bulk export API at no charge. After 30 days, projects and their data are deleted and cannot be recovered.

---

## 7. Trials

New accounts can start a **21-day trial** of Scale features. No card required. At the end of the trial, projects fall back to Developer limits; data above the Developer retention window becomes unreadable but is not immediately deleted (see RFC-014 for deletion timing).

Trials cannot be extended, and one trial is permitted per organisation domain.

---

## 8. Regions

Tideline is available in three regions:

| Region code | Location |
|---|---|
| `us-east-1` | Northern Virginia, USA |
| `eu-west-1` | Dublin, Ireland |
| `ap-southeast-2` | Sydney, Australia |

Not every feature is generally available in every region at the same time. Region-specific feature availability is tracked in the engineering RFCs rather than in this document.

---

## 9. Frequently asked

**Can I mix plans across projects?**
No. A plan applies to the whole organisation. Project count limits are per organisation.

**Do you charge for queries?**
Not currently. Query volume is subject to fair-use rate limits of 60 requests per minute per project, and 10 concurrent long-running queries per organisation. Sustained abuse may be throttled after written notice.

**What happens if my card fails?**
We retry on days 3, 7 and 14. After day 14 the organisation is suspended (writes rejected, reads permitted). After day 45 of non-payment, data is subject to deletion.

**Do you offer discounts for startups, non-profits or education?**
Yes — 50% off Team for 12 months, subject to eligibility review. Not stackable with the annual prepay discount.

**Can I get a copy of my data if I stop paying?**
Yes, during the 30-day read-only window described in 6.1.

**Where do I see what I'm being charged for?**
The console billing page itemises base, add-on units, ingest overage and storage overage separately, updated daily with a lag of up to 6 hours.

---

## 10. Change log

| Version | Date | Change |
|---|---|---|
| 4.2 | 2026-02-14 | Storage overage reduced from $0.11 to $0.09 per GB-month |
| 4.1 | 2026-01-09 | Added `ap-southeast-2` region |
| 4.0 | 2025-11-20 | Introduced Premium Support add-on; Team base raised from $150 to $180 |
| 3.6 | 2025-09-02 | Trial shortened from 30 to 21 days |

---

*This FAQ is maintained by Revenue Operations. Where this document and an engineering RFC disagree on a technical default, the RFC describes what the system currently does; this FAQ describes what was last published to customers. Discrepancies should be reported to revops@halcyonlabs.example.*
