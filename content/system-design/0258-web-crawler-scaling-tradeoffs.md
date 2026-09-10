---
card: system-design
gi: 258
slug: web-crawler-scaling-tradeoffs
title: Web Crawler — scaling & tradeoffs
---

## 1. What it is

This page covers the **scaling & tradeoffs** facet of the **Web Crawler** case study — what breaks first in the [high-level architecture](0255-web-crawler-high-level-architecture.md)'s single-machine Frontier and Bloom filter (from the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md)) as the crawl grows toward the [capacity estimation](0253-web-crawler-capacity-estimation.md)'s full ~7.8 billion page, ~2,000+ concurrent-fetch scale, and the fix and new tradeoff for each.

## 2. Why & when

The deep-dive facet's Bloom filter and domain-aware priority frontier were shown running as single, in-process structures. At web-crawler scale, neither fits comfortably on one machine — this facet is where that gap becomes a concrete distributed design, following the same bottleneck-fix-tradeoff discipline as every earlier case study's scaling facet.

## 3. Core concept

- **Bottleneck 1: a single-machine Bloom filter cannot hold billions of URLs' worth of bits, and a single-machine Frontier cannot handle 2,000+ concurrent workers querying and updating it.**
  - **Fix: partition both the Bloom filter and the Frontier by domain hash**, so each shard owns a subset of domains completely — every worker fetching a URL for `example.com` always talks to the same shard, which holds both that domain's Frontier queue and the relevant portion of the dedup structure.
  - **New tradeoff introduced:** a worker must now route to the correct shard based on a URL's domain before it can even check eligibility or dedup status, adding a routing/lookup step that a single in-process structure never needed — directly analogous to the [URL Shortener](0231-url-shortener-scaling-tradeoffs.md)'s sharding tradeoff, but partitioned by domain here rather than by record ID.
- **Bottleneck 2: a single content storage system under ~778 TB (for a 90-day crawl) and growing.** Even a well-provisioned object store benefits from deliberate partitioning strategy at this volume, echoing [Pastebin's own Bottleneck 1](0249-pastebin-scaling-tradeoffs.md).
  - **Fix: partition content storage by crawl date and/or domain**, the same principle as Pastebin's fix, applied here at a much larger scale.
  - **New tradeoff introduced:** downstream consumers (like a search indexer, FR-6) that want "all pages from domain X" or "all pages crawled this week" must query across the correct partition scheme rather than a flat namespace — a real integration cost for whatever system consumes this crawler's output.
- **Bottleneck 3: the fetcher worker pool itself becoming the bottleneck under network and DNS resolution overhead**, not raw compute — at thousands of concurrent connections, DNS lookups and TCP/TLS handshake overhead per new domain can dominate, especially early in a crawl when many domains are being contacted for the first time.
  - **Fix: a shared, caching DNS resolver layer in front of the fetcher pool**, plus connection pooling/reuse for domains fetched repeatedly within a short window.
  - **New tradeoff introduced:** a cached DNS entry can go stale if a target domain's IP address changes during a long-running crawl, risking fetches against a now-incorrect address until the cache entry expires and refreshes — a small, generally low-impact staleness window, but worth stating explicitly rather than assuming DNS caching is free of any downside.

## 4. Diagram

```
   BEFORE (single-machine Frontier, single Bloom filter, single content store)

   All Fetcher Workers --> one Frontier + one Bloom filter --> one Content Storage


   AFTER (sharded by domain, partitioned storage, shared DNS cache)

   Fetcher Workers --> Domain Router --> Frontier Shard 1 (domains A-M) + its own Bloom filter portion
                                     --> Frontier Shard 2 (domains N-Z) + its own Bloom filter portion
                            |
                            v
                     Shared DNS Cache (across all workers)
                            |
                            v
                     Content Storage (partitioned by crawl date / domain)
```
*Caption: domain-hash partitioning is the load-bearing fix for both the Frontier and the Bloom filter simultaneously, since both structures are naturally organized around the same domain key — a convenient alignment this system's design already leaned toward in the deep-dive facet.*

## 5. Runnable example

### Bottleneck-to-fix-to-tradeoff summary

```text
BOTTLENECK 1: single-machine Frontier + Bloom filter, cannot hold/serve
  billions of URLs and thousands of concurrent worker queries
  Symptom:  memory exhaustion (Bloom filter sized for billions of URLs
            does not fit one machine's RAM) and query contention (2,000+
            workers hitting one in-process structure serially).
  Fix:      partition BOTH the Frontier and the Bloom filter by domain
            hash - a natural alignment, since both structures already
            organize their internal state around domain.
  New tradeoff:
    - Workers need a routing step (hash the URL's domain, find the
      owning shard) before every Frontier/dedup operation - a new,
      small but real per-operation cost that a single in-process
      structure never had.

BOTTLENECK 2: single content storage system under ~778 TB and growing
  Symptom:  similar operational friction to Pastebin's Bottleneck 1, at
            a much larger absolute scale.
  Fix:      partition content storage by crawl date and/or domain.
  New tradeoff:
    - Downstream consumers (a search indexer, per FR-6) must query
      across the partition scheme rather than a flat namespace - an
      integration cost passed to whatever system consumes crawler output.

BOTTLENECK 3: DNS/connection overhead dominating at thousands of
  concurrent connections, especially against many first-contact domains
  Symptom:  fetcher workers spend a disproportionate amount of time on
            DNS resolution and connection setup rather than actual
            content transfer, especially early in a broad crawl.
  Fix:      a shared, caching DNS resolver layer; connection reuse for
            domains fetched repeatedly within a short window.
  New tradeoff:
    - A cached DNS entry can go stale if a target domain's IP changes
      mid-crawl, causing fetches against an outdated address until the
      cache entry's own TTL expires and refreshes.
```

## 6. Walkthrough

1. **Bottleneck 1 is the direct consequence of the [deep-dive facet](0257-web-crawler-deep-dive-url-frontier-dedup-politeness.md)'s structures being demonstrated as single, in-process data structures** — entirely appropriate for explaining the algorithm, but genuinely insufficient at the [capacity estimation](0253-web-crawler-capacity-estimation.md)'s actual scale of billions of URLs and thousands of concurrent workers.
2. **The domain-hash partitioning fix is a particularly clean one in this case study, worth noting explicitly**: because both the Frontier and the Bloom filter's core logic already organize themselves around `domain` (the Frontier for politeness tracking, and — in a sharded deployment — the Bloom filter partitioned the same way so a domain's dedup checks stay co-located with its queue), partitioning both by the same key means a single routing decision (which shard owns this domain) serves both structures at once, rather than needing two separate, potentially inconsistent partitioning schemes.
3. **Bottleneck 2 directly parallels [Pastebin's Bottleneck 1](0249-pastebin-scaling-tradeoffs.md)**, and recognizing that parallel is itself useful — the same underlying problem (a flat storage namespace strained by object count and volume) and the same class of fix (partition by a natural key) recur across multiple case studies in this series, reinforcing that this is a broadly reusable pattern, not a coincidence specific to either system.
4. **Bottleneck 3 introduces a genuinely new category of bottleneck this case study needed that none of the earlier three did**: DNS and connection-setup overhead. This is a direct consequence of the crawler's unique position of actively initiating outbound connections to a huge number of independent, often first-time-contacted servers — the earlier case studies' bottlenecks were all about the system's own infrastructure (databases, caches) straining under load, never about the overhead of *initiating* connections to external parties at this volume.
5. **The DNS-staleness tradeoff for Bottleneck 3's fix is a small, easy-to-overlook risk worth stating explicitly** — much like the [Rate Limiter](0240-rate-limiter-scaling-tradeoffs.md) case study's regional-store tradeoff or [Pastebin](0249-pastebin-scaling-tradeoffs.md)'s CDN-invalidation tradeoff, this is a case where a scaling fix (DNS caching) trades a small amount of correctness risk for a real, necessary performance gain, and naming that tradeoff explicitly is what separates a considered engineering decision from an unexamined default.

## 7. Gotchas & takeaways

> **Gotcha:** partitioning the Frontier and Bloom filter by domain hash assumes a roughly even distribution of crawl activity across domains — but real-world link structure is famously uneven (a small number of domains receive a disproportionate share of links and crawl activity). A naive hash-based partition can leave some shards far busier than others; a production system typically needs some form of load-aware rebalancing or a deliberately coarser partition scheme for known high-traffic domains, rather than assuming uniform hash distribution alone solves the problem.

- The domain-hash partitioning fix serving both the Frontier and Bloom filter simultaneously is a direct payoff of the deep-dive facet's deliberate choice to organize both structures around `domain` from the start — a design decision made early paying off cleanly at scaling time.
- Recognize the parallel between this system's Bottleneck 2 and Pastebin's own storage-partitioning bottleneck — the same fix pattern (partition by a natural key) applies, reinforcing it as a transferable technique rather than a one-off solution.
- DNS/connection overhead (Bottleneck 3) is a bottleneck category unique to this case study among the four covered in this series, directly reflecting the crawler's distinctive role as an active outbound connector to a huge number of independent external servers.
- See [Web Crawler — Spring/Java implementation approach](0259-web-crawler-spring-java-implementation-approach.md) next for how this whole design — the self-feeding loop, politeness-aware Frontier, and Bloom filter dedup — translates into an actual Spring Boot service, closing out this case study.
