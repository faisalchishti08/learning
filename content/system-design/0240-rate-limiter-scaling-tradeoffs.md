---
card: system-design
gi: 240
slug: rate-limiter-scaling-tradeoffs
title: Rate Limiter — scaling & tradeoffs
---

## 1. What it is

This page covers the **scaling & tradeoffs** facet of the **Rate Limiter** case study — what breaks first in the [high-level architecture](0237-rate-limiter-high-level-architecture.md)'s single shared counter store as real client count and request volume grow past the [capacity estimation](0235-rate-limiter-capacity-estimation.md)'s numbers, and the fix and new tradeoff for each.

## 2. Why & when

The original estimation sized a comfortable single-instance shared store (~80 MB, ~50,000 ops/sec). Real growth — more clients, higher traffic per protected service, new protected services sharing the same limiter — eventually exceeds those numbers. This facet walks through the bottlenecks in the order they would actually appear, and names the real cost of each fix.

## 3. Core concept

- **Bottleneck 1: single store instance throughput ceiling.** As total request volume across all protected services grows past what one store instance can sustain (even though memory is not the constraint, raw operations/sec eventually is), the store itself becomes the bottleneck every gated request waits on.
  - **Fix: shard the store by `clientId` hash**, spreading the check-and-increment load across multiple store instances, the same sharding principle used in the [URL Shortener](0231-url-shortener-scaling-tradeoffs.md)'s database scaling.
  - **New tradeoff introduced:** a client whose multiple simultaneous rules (FR-6) happen to hash to different shards loses the ability to atomically check both rules together in one operation — each rule's check becomes an independent call to its own shard, which is fine for independent rules but adds a small amount of complexity versus a single-store, single-round-trip check.
- **Bottleneck 2: cross-region latency for a globally distributed protected service.** If the protected service itself is deployed [multi-region](0221-multi-az-multi-region-deployment.md), but the rate limiter's shared store lives in only one region, every app server outside that region pays a cross-region round-trip on every single gated request — directly violating NFR-1's sub-5ms latency target for those instances.
  - **Fix: a regional store per deployment region**, with each region's app servers checking their own local store.
  - **New tradeoff introduced:** a client whose requests are split across regions (a mobile client roaming, or a client behind a geographically distributed CDN/anycast setup) now has its usage tracked independently per region — the "global" limit becomes, in practice, N separate regional limits, each enforced locally. This is a real, stated relaxation of FR-1's "enforce N requests total" in exchange for the latency NFR holding globally.
- **Bottleneck 3: config lookups (FR-4/tier assignment) adding latency on every request.** As the number of distinct clients and tiers grows, looking up "what is this client's limit" on every single request (even from a fast config store) adds up.
  - **Fix: cache the client-to-tier and tier-to-limits mapping locally on each app server**, refreshed periodically (e.g. every 30 seconds) rather than looked up per request.
  - **New tradeoff introduced:** a change to a client's tier (an admin upgrading them from free to paid) takes up to the cache refresh interval to actually take effect everywhere — a small, bounded staleness window, directly analogous to the eventual-consistency tradeoffs seen throughout this whole set of case studies.

## 4. Diagram

```
   BEFORE (single store, single region)          AFTER (sharded, multi-region)

   All app servers                                Region: us-east              Region: eu-west
        |                                          App Servers                  App Servers
        v                                               |                            |
   +---------------+                                    v                            v
   | Single Store   |                          +----------------+          +----------------+
   | instance        |                          | Regional Store  |          | Regional Store  |
   +---------------+                          | (sharded by       |          | (sharded by       |
                                                |  clientId hash)    |          |  clientId hash)    |
                                                +----------------+          +----------------+

                                                each region enforces its OWN view of a client's
                                                usage - a client split across regions gets, in
                                                effect, per-region limits rather than one true
                                                global limit
```
*Caption: sharding within a region fixes throughput; a store per region fixes cross-region latency — but the second fix trades away a single, globally-accurate count for regional independence, a real and sometimes surprising consequence.*

## 5. Runnable example

### Bottleneck-to-fix-to-tradeoff summary

```text
BOTTLENECK 1: single store instance, throughput ceiling
  Symptom:  check-and-increment operations queue up under very high total
            request volume across all protected services sharing this
            rate limiter, adding latency that risks violating NFR-1.
  Fix:      shard the store by hash(clientId) across N instances.
  New tradeoff:
    - Multiple simultaneous rules for one client (FR-6) may land on
      different shards, losing single-round-trip atomicity across rules
      (each rule's own atomicity within its shard is unaffected).

BOTTLENECK 2: cross-region latency for a multi-region protected service
  Symptom:  app servers outside the store's one deployed region see
            latency violating NFR-1, purely from network distance to the
            shared store.
  Fix:      a regional store per deployment region, each serving that
            region's local app servers.
  New tradeoff:
    - A client's usage is now tracked per-region, not globally - a client
      making requests from two regions effectively gets up to 2x its
      nominal limit, split across regions. This must be explicitly stated
      as an accepted relaxation of FR-1's "enforce N total," not a bug.

BOTTLENECK 3: per-request config lookup latency (FR-4 tier assignment)
  Symptom:  looking up a client's current tier/limit on every single
            gated request adds latency, even against a fast config store.
  Fix:      cache client-to-tier and tier-to-limits mappings locally on
            each app server, refreshed periodically (e.g. every 30s).
  New tradeoff:
    - A tier change takes up to the refresh interval to take effect -
      a bounded staleness window, acceptable for infrequent admin changes,
      but worth stating explicitly to anyone expecting instant effect.
```

## 6. Walkthrough

1. **Bottleneck 1 arises purely from total throughput, not memory** — this directly echoes the [capacity estimation](0235-rate-limiter-capacity-estimation.md)'s conclusion that operations/sec, not memory footprint, was always the binding constraint for this system. Sharding by `clientId` hash distributes that throughput across multiple store instances, the same principle as the [URL Shortener](0231-url-shortener-scaling-tradeoffs.md)'s database sharding, applied here to the counter store instead.
2. **The tradeoff for Bottleneck 1's fix specifically affects FR-6 (multiple simultaneous rules).** With a single store instance, checking both a client's `per-minute` and `per-day` rules could, in principle, happen as related operations against the same instance; once sharded by `clientId` hash, both rules for the *same* client actually land on the *same* shard (since sharding is by `clientId`, not by `clientId+rule`), so this specific tradeoff is more subtle than it first appears — worth verifying the sharding key choice preserves the property you actually need, rather than assuming any sharding scheme is equivalent.
3. **Bottleneck 2 is a latency problem the original architecture never considered**, because the [capacity estimation](0235-rate-limiter-capacity-estimation.md) reasoned about total throughput, not geography — exactly the same category of gap the [URL Shortener](0231-url-shortener-scaling-tradeoffs.md)'s Bottleneck 2 (single-region latency) exposed for that system.
4. **The regional-store fix's tradeoff is the most consequential one on this page**: it means FR-1 ("enforce N requests per client") is no longer strictly true in a global sense once a client can be served from multiple regions — each region enforces its own local count. This must be surfaced explicitly to whoever owns the functional requirement, since "each region enforces its own limit" is a materially different guarantee than "there is one true global limit," even though both are reasonable designs depending on the actual use case.
5. **Bottleneck 3's fix (local config caching) is the lowest-risk of the three**, since FR-4's tier data changes far less often than request volume — caching it with a modest refresh interval (30 seconds) trades a small, bounded staleness window for removing a per-request lookup from the critical path entirely, a favorable tradeoff for almost any real deployment.

## 7. Gotchas & takeaways

> **Gotcha:** the regional-store fix for Bottleneck 2 is the one place in this whole case study where a scaling fix changes the actual *meaning* of a functional requirement (FR-1), not just its performance characteristics. Every other fix in this case study trades performance for operational complexity or a bounded staleness window; this one trades global accuracy for regional independence — a fundamentally different kind of tradeoff that deserves explicit sign-off from whoever owns the product requirement, not just an engineering decision made silently.

- Trace each fix back to the specific bottleneck it addresses, exactly as the [URL Shortener](0231-url-shortener-scaling-tradeoffs.md) case study's scaling facet modeled — a distributed rate limiter is genuinely more complex than a single-instance one, and that complexity should be justified by an actual measured or projected bottleneck.
- Sharding by `clientId` (not `clientId+rule`) is a deliberate choice that keeps one client's multiple rules together on one shard — verify a sharding key against every requirement it might affect (here, FR-6) before adopting it, rather than assuming any partitioning scheme is interchangeable.
- The regional-store tradeoff (per-region rather than global enforcement) is a case where a scaling fix changes a functional guarantee, not just a performance number — flag this kind of tradeoff loudly, since it is easy for it to go unnoticed until a client's actual behavior (making requests from multiple regions) exposes it in production.
- See [Rate Limiter — Spring/Java implementation approach](0241-rate-limiter-spring-java-implementation-approach.md) next for how the token-bucket algorithm and this architecture translate into an actual Spring Boot service, including a `@Component`-based `allow(...)` implementation.
