---
card: system-design
gi: 249
slug: pastebin-scaling-tradeoffs
title: Pastebin — scaling & tradeoffs
---

## 1. What it is

This page covers the **scaling & tradeoffs** facet of the **Pastebin** case study — what breaks first in the [high-level architecture](0246-pastebin-high-level-architecture.md) as total content volume and traffic grow past the [capacity estimation](0244-pastebin-capacity-estimation.md)'s ~7.3 TB / 2-year projection, and the fix and new tradeoff for each bottleneck.

## 2. Why & when

The capacity estimation identified storage volume, not QPS, as Pastebin's dominant constraint — a genuinely different profile from the URL Shortener's QPS-driven scaling story. This facet walks through the bottlenecks that specifically follow from a storage-bound system, in the order they would actually appear.

## 3. Core concept

- **Bottleneck 1: a single blob storage bucket/namespace under object-count and volume growth.** Even a highly scalable object store can face practical limits on listing performance or per-prefix throughput within a single flat namespace as object count grows into the hundreds of millions.
  - **Fix: partition blob keys by a prefix derived from `paste_id` or creation date** (e.g. `pastes/2026/09/10/xK9pLm2`), spreading objects across many effective partitions within the store, which most object stores handle far better than one enormous flat namespace.
  - **New tradeoff introduced:** the expiration sweeper's query pattern (from the [deep-dive facet](0248-pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup.md)) must now account for the date-based prefix if it wants to efficiently target older content, adding a small amount of complexity to what was a flat "any expired row" scan.
- **Bottleneck 2: metadata database write throughput, as creation volume grows.** Even though Pastebin's writes are far less frequent than the URL Shortener's read traffic, the metadata database still has a write ceiling, and very high paste-creation volume (e.g. a public API being used programmatically at scale) can approach it.
  - **Fix: shard the metadata database by `paste_id` hash**, the same principle as the URL Shortener's Bottleneck 1 fix.
  - **New tradeoff introduced:** the expiration sweeper (and FR-7's "list my pastes," if in scope) must now query every shard rather than one database instance — the same fan-out complexity the URL Shortener's sharding fix introduced for its own creator-listing feature.
- **Bottleneck 3: the cache's hit rate degrading as total unique content grows.** Given Pastebin's more modest 10:1 read:write ratio (from [non-functional requirements](0243-pastebin-non-functional-requirements.md)), a large fraction of pastes may only ever be viewed a handful of times by a specific small audience — meaning the "hot set" that makes caching effective is proportionally smaller and less concentrated than the URL Shortener's, and a growing total content volume can dilute cache effectiveness further over time.
  - **Fix: rely more heavily on blob storage's own read performance and a CDN for publicly shared, non-burn pastes**, rather than trying to grow the cache to compensate — since blob storage and CDNs are built to serve large content volumes with a long tail directly, more cost-effectively than scaling a cache to match.
  - **New tradeoff introduced:** a CDN-fronted paste is cached at edge locations with its own TTL, separate from the origin's cache — meaning updates to a paste's expiration or burn status (if either changes after initial caching) must be reflected via CDN invalidation, an operational step the origin-only cache never needed.

## 4. Diagram

```
   BEFORE (single blob namespace, single metadata DB, cache-reliant)

   App Servers --> Cache --> Metadata DB (1 instance) --> Blob Storage (flat namespace)


   AFTER (partitioned blobs, sharded metadata, CDN for public content)

   App Servers --> CDN (public, non-burn pastes) --> Blob Storage
                       |                              (partitioned by date/id prefix)
                       v
                    Cache (smaller, hot-set only) --> Metadata DB Shard 1 | Shard 2 | ...
                                                        (hash(paste_id) determines shard)
```
*Caption: each fix targets the specific bottleneck the capacity estimation's storage-volume finding predicted would matter most for this system — a different emphasis from the URL Shortener's QPS-driven scaling story.*

## 5. Runnable example

### Bottleneck-to-fix-to-tradeoff summary

```text
BOTTLENECK 1: single flat blob storage namespace, object-count growth
  Symptom:  listing/prefix-scan performance in blob storage degrades as
            object count grows into the hundreds of millions (a direct
            consequence of the ~7.3 TB / large-object-count trajectory
            from capacity estimation).
  Fix:      partition blob keys by date/id prefix (e.g. pastes/2026/09/10/id).
  New tradeoff:
    - The expiration sweeper's targeting logic must account for the
      prefix structure to efficiently find old content, rather than a
      flat scan across every object.

BOTTLENECK 2: metadata DB write throughput under high creation volume
  Symptom:  paste creation requests queue up under sustained high-volume
            programmatic use (e.g. an API integration creating many
            pastes automatically).
  Fix:      shard the metadata database by hash(paste_id).
  New tradeoff:
    - The expiration sweeper (and FR-7's "list my pastes," if in scope)
      must fan out across every shard rather than querying one instance -
      the same tradeoff the URL Shortener's equivalent fix introduced.

BOTTLENECK 3: cache hit rate dilutes as total unique content grows
  Symptom:  Pastebin's smaller, less concentrated "hot set" (per the
            10:1 read:write ratio) means cache effectiveness degrades
            faster, per unit of total content, than the URL Shortener's
            experienced.
  Fix:      shift reliance toward blob storage's native read performance
            and a CDN for public, non-burn pastes, rather than scaling
            the cache to compensate.
  New tradeoff:
    - CDN-cached content has its own edge TTL, independent of the
      origin - a paste's expiration or burn-status change now requires
      an explicit CDN invalidation step to take effect everywhere
      promptly, an operational step a cache-only design never needed.
```

## 6. Walkthrough

1. **Bottleneck 1 follows directly from the [capacity estimation](0244-pastebin-capacity-estimation.md)'s conclusion that storage volume, not QPS, is this system's defining number** — a flat object namespace that comfortably handles the URL Shortener's much smaller total record count can face real operational friction at Pastebin's much larger object count and total size, even without a corresponding QPS increase.
2. **The date/ID-prefix partitioning fix directly complicates the [deep-dive facet](0248-pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup.md)'s expiration sweeper.** That facet's sweeper queried the metadata database (not blob storage) for expired rows, so this specific tradeoff is more about efficient targeting when the sweeper needs to reason about *where* content physically lives (for operational or cost-management purposes) than about the correctness logic itself — worth noting that not every scaling tradeoff touches the same downstream facet equally.
3. **Bottleneck 2 mirrors the [URL Shortener's own Bottleneck 1](0231-url-shortener-scaling-tradeoffs.md) almost exactly**, including its tradeoff (fan-out queries across shards) — this is a deliberate, useful pattern to recognize: sharding a database by its primary access key is a broadly reusable fix whose tradeoff (loss of easy cross-shard aggregation) recurs across many different systems, not just this one.
4. **Bottleneck 3 is the tradeoff most specific to Pastebin's own capacity profile**, and it is worth contrasting directly with the URL Shortener's Bottleneck 3 (distributed cache cluster) — that system's fix scaled the cache itself, because its 100:1 ratio and highly concentrated hot set made caching the right lever to keep pulling. Pastebin's more modest 10:1 ratio and more evenly-spread access pattern make blob storage's own native scalability, plus a CDN, the more cost-effective lever instead — the same underlying principle (match the fix to the actual bottleneck) produces a genuinely different specific fix here.
5. **The CDN tradeoff (edge TTL independent of origin) is a new category of complexity this case study had not needed before** — it directly interacts with FR-4 (expiration) and FR-6 (burn after reading): if a paste is CDN-cached and then burns or expires at the origin, the CDN edge might still serve the old, cached content until its own TTL passes or an explicit invalidation is issued. This is exactly the kind of interaction between a scaling fix and an existing functional requirement that must be surfaced explicitly, the same discipline the [Rate Limiter](0240-rate-limiter-scaling-tradeoffs.md) case study's regional-store tradeoff demanded.

## 7. Gotchas & takeaways

> **Gotcha:** introducing a CDN for public pastes without explicitly reconciling it against FR-6 (burn after reading) is a real correctness risk, not just a performance detail — a CDN edge node could keep serving a "burned" paste's content to new requesters for as long as its own cache TTL lasts, directly violating the "shown exactly once" guarantee that feature promises. Either exclude burn-after-reading pastes from CDN caching entirely, or set an aggressively short edge TTL specifically for them, and state this exclusion explicitly in the design.

- Pastebin's scaling story follows directly from its own capacity estimation's specific finding (storage volume dominant, not QPS) — contrast this deliberately with the URL Shortener's QPS-driven story to reinforce that scaling fixes should always trace back to a system's own measured bottleneck, never a generic checklist applied uniformly.
- Database sharding's fan-out tradeoff (Bottleneck 2) is a broadly reusable pattern recognizable across multiple case studies in this series — once learned once, it transfers directly.
- A CDN interacting badly with a "shown exactly once" feature (FR-6) is exactly the kind of subtle correctness bug a scaling fix can silently introduce — always re-check every functional requirement against a proposed scaling fix, not just its performance characteristics.
- See [Pastebin — Spring/Java implementation approach](0250-pastebin-spring-java-implementation-approach.md) next for how this whole design, including the metadata/blob split and expiration handling, translates into an actual Spring Boot service.
