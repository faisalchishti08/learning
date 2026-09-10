---
card: system-design
gi: 253
slug: web-crawler-capacity-estimation
title: Web Crawler — capacity estimation
---

## 1. What it is

This page covers the **capacity estimation** facet of the **Web Crawler** case study — turning the [non-functional requirements](0252-web-crawler-non-functional-requirements.md)'s throughput target (1,000 pages/sec) and storage implication into concrete numbers: total pages crawled over time, storage volume, bandwidth, and — a genuinely new kind of calculation this case study needs — the number of parallel fetcher workers required, given the per-domain politeness constraint.

## 2. Why & when

Earlier case studies estimated QPS and storage from monthly usage figures. This system's estimation works differently: NFR-1's throughput target is a direct input, not something derived from a usage projection, and the politeness constraint (NFR-2) introduces a calculation none of the earlier case studies needed — how many parallel workers are required to sustain a given throughput while respecting a strict per-domain delay.

## 3. Core concept

The estimation chain here has a genuinely different shape from the read-heavy case studies:

1. Start from the **target throughput** (NFR-1: 1,000 pages/sec) directly, rather than deriving it from a usage projection.
2. Estimate **average page size** to compute bandwidth and storage.
3. Compute **storage growth** over the crawl's intended duration.
4. Compute **required worker parallelism**, using the per-domain politeness constraint (NFR-2) and an assumption about how many distinct domains are being crawled concurrently — this is the calculation unique to this case study.

## 4. Diagram

```
   target throughput (1,000 pages/sec)   --> bandwidth = throughput x avg page size
        |
        v
   pages/sec x seconds in crawl duration --> total pages crawled
        |
        v
   total pages x avg page size            --> total storage
        |
        v
   PER-DOMAIN POLITENESS (1 req / 2 sec)  --> how many domains must be
   + assumed concurrent distinct domains      "in flight" simultaneously
        being crawled                          to sustain 1,000 pages/sec
        |                                       without violating politeness
        v                                       for any single one
   required worker parallelism (workers,
   not just raw threads - see walkthrough)
```
*Caption: the last step, deriving required parallelism from a politeness constraint, is a calculation this case study needs that none of the earlier three did — a direct consequence of NFR-2's per-domain rate limit.*

## 5. Runnable example

### Worked calculation

```text
ASSUMPTIONS
  - Target throughput: 1,000 pages/sec (NFR-1).
  - Average page size (HTML content, after stripping large embedded
    media which a real crawler would often skip or fetch separately):
    ~100 KB.
  - Politeness: at most 1 request per domain every 2 seconds (NFR-2).
  - Crawl duration for a concrete storage projection: 90 days
    (continuous operation).
  - Assumed number of distinct domains actively being crawled at any
    given moment: 50,000 (a broad crawl touches a very large number of
    domains; this is a reasonable planning assumption, clearly flagged
    as such since the real number depends heavily on the crawl's scope).

STEP 1: bandwidth
  1,000 pages/sec x 100 KB/page = 100,000 KB/sec = ~100 MB/sec = ~800 Mbps

STEP 2: total pages crawled over 90 days
  90 days x 86,400 sec/day x 1,000 pages/sec = 7,776,000,000 pages
  ~= ~7.8 billion pages

STEP 3: total storage over 90 days
  7,776,000,000 pages x 100 KB/page = 777,600,000,000 KB
  ~= ~778 TB over 90 days

  (for comparison: this single 90-day crawl accumulates roughly 100x the
  URL Shortener's ENTIRE 5-year storage total - a direct consequence of
  fetching and storing full page content, at web scale, continuously)

STEP 4: required worker parallelism (the politeness-driven calculation)
  Per-domain politeness allows 1 request every 2 seconds PER DOMAIN, so
  a single domain can sustain at most 0.5 pages/sec from this crawler.

  To sustain 1,000 pages/sec in AGGREGATE while respecting that per-domain
  limit, the crawler must be actively fetching from MANY DIFFERENT domains
  simultaneously - specifically, at least:
    1,000 pages/sec / 0.5 pages/sec/domain = 2,000 domains "in flight"
    simultaneously, at minimum (assuming perfectly even distribution
    across the 50,000 assumed active domains - in practice, real traffic
    is unevenly distributed, so the actual number of in-flight domains
    needed is HIGHER than this theoretical minimum).

  Each in-flight domain fetch, accounting for network latency (assume
  ~200ms average page fetch time), needs its own worker "slot" for that
  duration - so required concurrent worker slots:
    2,000 domains-in-flight x (1 request in flight per domain, per the
    politeness limit itself) = at least 2,000 concurrent fetch operations
    in flight at any given instant, just to hit the 1,000 pages/sec target
    while respecting politeness.

SUMMARY
  - Bandwidth: ~800 Mbps sustained.
  - Total pages over 90 days: ~7.8 billion.
  - Total storage over 90 days: ~778 TB.
  - Minimum concurrent fetch operations needed: ~2,000+ (this is the
    number that most directly drives the worker-pool sizing decision in
    high-level architecture).
```

## 6. Walkthrough

1. **Step 1 is a direct multiplication of the target throughput by average page size**, unlike the earlier case studies' QPS-from-monthly-usage derivation — this reflects NFR-1 being stated as a direct throughput target rather than something to derive from a usage projection.
2. **Step 2 and Step 3 follow the familiar pattern from the [Pastebin](0244-pastebin-capacity-estimation.md) estimation** (rate × time → total volume), but the resulting number, ~778 TB over just 90 days, dwarfs anything in the earlier case studies — this single number is the clearest illustration in this whole series of how "crawl and store the open web" operates at a fundamentally different scale than "serve a bounded set of user-submitted content."
3. **Step 4 is the calculation genuinely unique to this case study.** Politeness (NFR-2) caps any single domain at 0.5 pages/sec from this crawler. To reach 1,000 pages/sec in aggregate without violating that cap for any individual domain, the crawler cannot simply run 1,000 sequential single-domain fetchers — it must be actively working across at least 2,000 different domains simultaneously, since no domain alone can contribute more than 0.5 pages/sec to the total.
4. **This 2,000+ figure is explicitly a *minimum*, and the walkthrough's own assumption notes why**: real-world URL discovery is not evenly distributed across domains — a crawl following links naturally encounters some domains far more often than others (a popular site with many internal pages), meaning some domains will be "ready to crawl again" faster than others by simple chance, and the crawler needs enough domain diversity and queue depth to always have *some* eligible domain to fetch from at any given instant, or throughput drops below target even with 2,000 nominal slots.
5. **This number, not storage or bandwidth, is what most directly shapes the [high-level architecture](0255-web-crawler-high-level-architecture.md)'s worker-pool design** — a system needing 778 TB of storage is a solvable, if substantial, infrastructure problem using well-understood distributed storage; a system needing thousands of concurrent, domain-aware fetch operations, each respecting an independent per-domain rate limit, is a genuinely different kind of coordination problem, addressed directly in the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md).

## 7. Gotchas & takeaways

> **Gotcha:** it is tempting to treat "2,000 concurrent fetch operations" as simply "run 2,000 threads" — but each of those operations must also respect that specific domain's own politeness timer independently, meaning the actual coordination problem is not just achieving 2,000-way concurrency, but achieving it while a large, dynamic set of independent per-domain rate limits are all being tracked and honored simultaneously. This distinction is exactly why the URL frontier deep-dive gets its own dedicated facet in this case study.

- The 778 TB storage figure and the 2,000+ concurrent-fetch figure are the two numbers that most directly shape [high-level architecture](0255-web-crawler-high-level-architecture.md) — cite both when explaining why this system's design differs so substantially from the earlier three case studies'.
- Deriving required parallelism from a politeness constraint (Step 4) is a calculation pattern specific to systems that must rate-limit themselves against many independent external targets, not something the earlier case studies' estimation methods needed — recognize when a system's own NFRs (not just its usage volume) demand this kind of derived-parallelism calculation.
- The "2,000+ domains in flight" figure is explicitly a lower bound under an idealized even-distribution assumption — real designs should provision meaningfully above this minimum to absorb the natural unevenness of real link-discovery patterns.
- See [Web Crawler — API design](0254-web-crawler-api-design.md) next for how an operator actually configures and monitors a crawl of this scale, since — as [functional requirements](0251-web-crawler-functional-requirements.md) noted — this system has no traditional end-user-facing API.
