---
card: system-design
gi: 231
slug: url-shortener-scaling-tradeoffs
title: URL Shortener — scaling & tradeoffs
---

## 1. What it is

This page covers the **scaling & tradeoffs** facet of the **URL Shortener** case study — what breaks first in the [high-level architecture](0228-url-shortener-high-level-architecture.md) as real traffic grows past the [capacity estimation](0226-url-shortener-capacity-estimation.md)'s numbers, and the specific fix for each bottleneck, along with the new tradeoff each fix introduces.

## 2. Why & when

An architecture sized for today's estimate eventually meets tomorrow's actual traffic, which is often larger, lumpier, and differently distributed than the back-of-envelope numbers assumed. This facet walks through the architecture's bottlenecks in the order they would actually bite as scale increases, and the standard fix for each — because every fix has a real cost, not just a benefit, worth naming explicitly rather than presenting scaling as a free upgrade.

## 3. Core concept

- **Bottleneck 1: single database instance under write load.** Even though writes are a small fraction of total traffic (per the 100:1 ratio), a single database instance has a ceiling on writes/sec it can sustain, and creation traffic could plausibly exceed it during a viral spike in link creation (a marketing campaign, a bot attack).
  - **Fix: shard the database by `short_code`.** Route each write (and cache-miss read) to a specific shard based on a hash of `short_code`, spreading load across many database instances.
  - **New tradeoff introduced:** cross-shard operations (like "list my URLs" for FR-7, which spans codes on every shard if `creator_id` is not the shard key) become significantly more complex, since no single shard has the full answer.
- **Bottleneck 2: a single-region cache and database under global traffic.** Users far from the system's one deployed region see high redirect latency, violating the strict redirect-latency NFR for those users.
  - **Fix: [multi-region deployment](0221-multi-az-multi-region-deployment.md)**, with a cache (and read replica) in each region, serving redirects locally.
  - **New tradeoff introduced:** cross-region replication is asynchronous (per multi-region's own core concept), so a URL created in one region may take a short time to become resolvable from another region — the [non-functional requirements](0225-url-shortener-non-functional-requirements.md)'s eventual-consistency NFR already anticipated this, but it becomes an operationally real concern, not just a theoretical allowance, at this scale.
- **Bottleneck 3: cache capacity, as the total number of hot URLs grows.** A cache sized for today's hot set eventually cannot hold tomorrow's larger hot set, causing cache eviction of genuinely popular codes and a rising cache-miss rate.
  - **Fix: a distributed cache cluster** (many cache nodes, each holding a portion of the keyspace, coordinated by consistent hashing) instead of a single cache instance.
  - **New tradeoff introduced:** the cache cluster itself now needs operational management — node failures, rebalancing when nodes are added or removed — complexity that did not exist with a single cache instance.

## 4. Diagram

```
   BEFORE (single region, single DB, single cache)

   Client --> LB --> App Servers --> Cache (1 node) --> DB (1 instance)


   AFTER (sharded DB, multi-region, distributed cache)

   Region: us-east                              Region: eu-west
   Client --> LB --> App Servers                Client --> LB --> App Servers
                        |                                            |
                 Cache Cluster (N nodes,                      Cache Cluster (N nodes,
                 consistent hashing)                            consistent hashing)
                        |                                            |
              DB Shard 1 | DB Shard 2 | ... <---async replication---> DB Shard 1 | DB Shard 2 | ...
              (hash(short_code) determines shard)
```
*Caption: each fix on the right addresses one specific bottleneck from the left — sharding fixes write throughput, multi-region fixes global latency, a cache cluster fixes hot-set capacity — but none of them is free, as the walkthrough details.*

## 5. Runnable example

### Bottleneck-to-fix-to-tradeoff summary

```text
BOTTLENECK 1: single DB instance, write throughput ceiling
  Symptom:  creation requests queue up or time out during a traffic spike
            (e.g. a viral campaign driving a surge in new short URLs).
  Fix:      shard the database by hash(short_code) across N instances.
  New tradeoff:
    - FR-7 ("list my URLs") now requires querying every shard and merging
      results, since a user's URLs are scattered by short_code hash, not
      grouped by creator_id.
    - Re-sharding (adding more shards later) requires a data migration.

BOTTLENECK 2: single-region deployment, global latency
  Symptom:  redirect-latency NFR (p99 < 100ms) is violated for users far
            from the single deployed region.
  Fix:      multi-region deployment - cache + read replica per region.
  New tradeoff:
    - Cross-region replication is asynchronous: a URL created in region A
      may not resolve in region B for a short window after creation.
    - Running infrastructure in multiple regions multiplies operational
      cost and complexity (see multi-AZ & multi-region deployment).

BOTTLENECK 3: single cache instance, hot-set capacity
  Symptom:  cache-miss rate rises as the number of genuinely popular URLs
            grows past what one cache instance can hold, pushing more
            traffic to the database than the architecture was designed for.
  Fix:      distributed cache cluster (consistent hashing across nodes).
  New tradeoff:
    - The cache cluster itself needs monitoring, node-failure handling,
      and rebalancing logic that a single cache instance never needed.
    - A cache node failure now affects only a portion of the keyspace
      (better than losing the whole cache) but requires the app servers
      to know how to route around a failed node.
```

## 6. Walkthrough

1. **Bottleneck 1 is a write-side problem, even though writes are the minority of traffic** (per the 100:1 ratio established in [non-functional requirements](0225-url-shortener-non-functional-requirements.md)) — because a single database instance's absolute write ceiling can still be exceeded during a sudden spike in creation traffic, regardless of how small writes are relative to reads. Sharding by `short_code` hash spreads that write load across many instances, each handling a fraction of it.
2. **The sharding fix directly conflicts with FR-7 from [functional requirements](0224-url-shortener-functional-requirements.md).** Because the shard key is `short_code` (chosen to spread write load evenly), a single user's URLs end up scattered across every shard rather than grouped together — "list my URLs" now requires a fan-out query to every shard and a merge of the results, a real added complexity that did not exist with one database instance. This tradeoff is a direct, traceable cost of the sharding fix, not a separate, unrelated problem.
3. **Bottleneck 2 is a latency problem invisible in the original single-region design**, because [capacity estimation](0226-url-shortener-capacity-estimation.md)'s QPS numbers say nothing about *where* traffic originates geographically — a system correctly sized for total QPS can still fail its latency NFR for specific users simply due to physical distance from the one deployed region.
4. **The multi-region fix reintroduces the eventual-consistency behavior [non-functional requirements](0225-url-shortener-non-functional-requirements.md) already flagged as acceptable (NFR-7)** — but at this scale, "a newly created URL may take a few seconds to resolve elsewhere" becomes an operationally real, frequently-observed behavior rather than a theoretical allowance, since cross-region creation-then-immediate-click-from-another-region becomes a real, if infrequent, occurrence.
5. **Bottleneck 3 is the cache's own success outgrowing its capacity** — the [high-level architecture](0228-url-shortener-high-level-architecture.md)'s cache-aside design works precisely because a small hot set captures most traffic, but as total URL volume and popularity spread grow, that hot set itself grows past a single cache instance's memory. Moving to a distributed cache cluster fixes the capacity ceiling, but the new tradeoff — operational complexity of a multi-node cache, including how app servers route to the correct node and how a node failure is handled — is a genuinely new category of operational work the single-cache design never had.

## 7. Gotchas & takeaways

> **Gotcha:** applying a scaling fix "because it sounds like best practice" without first identifying which specific bottleneck it addresses is how systems end up with unnecessary complexity — a distributed cache cluster is pure operational overhead for a system whose single cache instance was never actually running out of capacity. Match each fix to an observed or projected bottleneck, not to a generic scaling checklist.

- Every fix in this facet solves exactly one specific, named bottleneck — trace any proposed scaling change back to the bottleneck it addresses before adopting it, the same discipline used throughout this case study.
- No scaling fix is free — each one introduced here trades away something (cross-shard query complexity, consistency freshness, operational overhead) in exchange for removing the bottleneck, and stating that tradeoff explicitly is what separates a real design discussion from a checklist.
- These three bottlenecks tend to appear roughly in this order as real traffic grows — write throughput and cache capacity are usually felt well before global latency becomes the binding constraint, though the exact order depends on a given system's actual user distribution.
- See [URL Shortener — Spring/Java implementation approach](0232-url-shortener-spring-java-implementation-approach.md) next for how this whole design, including the scaling considerations here, translates into an actual Spring Boot service.
