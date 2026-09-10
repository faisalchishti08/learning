---
card: system-design
gi: 234
slug: rate-limiter-non-functional-requirements
title: Rate Limiter — non-functional requirements
---

## 1. What it is

This page covers the **non-functional requirements (NFRs)** facet of the **Rate Limiter** case study — the quality targets (scale, latency, accuracy, availability) the system must hit, as opposed to what it must do functionally (see [functional requirements](0233-rate-limiter-functional-requirements.md), a separate facet).

## 2. Why & when

A rate limiter sits directly in the request path of every protected service — if it is slow, it makes every request slower; if it is wrong, it either lets too much traffic through (defeating its purpose) or rejects legitimate traffic (breaking the service for real users). Define these targets right after functional requirements, since they determine whether the rate limiter can even be a synchronous, in-path component, or whether it needs to be architected differently.

## 3. Core concept

- **Latency.** The rate-limiting check itself must add negligible overhead to every request it gates — since it sits in front of potentially every request to a protected service, even a small added latency multiplies across the system's entire traffic.
- **Accuracy vs. performance tradeoff.** A perfectly accurate count of a client's requests (never allowing one request over the limit, never rejecting one request under it) generally requires strong consistency on the counter — which is expensive under high concurrency. Most real rate limiters accept a small, bounded amount of inaccuracy (allowing slightly more or fewer requests than the exact limit) in exchange for much better performance — a deliberate, stated tradeoff, not an oversight.
- **Scale.** The rate limiter must handle checking limits for a very large number of distinct clients simultaneously, at the same request rate as the service it protects — its own throughput ceiling must exceed the protected service's expected peak traffic, or it becomes the new bottleneck.
- **Availability.** The rate limiter should fail in a way that does not take down the protected service. A common, deliberate choice: if the rate limiter itself becomes unavailable, **fail open** (let requests through unchecked) rather than **fail closed** (reject everything) — because an unprotected service temporarily is usually less damaging than a fully unavailable one, though this is a real tradeoff a given system might choose differently.
- **Distributed consistency.** When the rate limiter itself runs as multiple instances (for its own scale and availability), those instances must agree closely enough on a given client's current usage that FR-1 ("enforce the limit") holds even though no single instance sees every request for that client.

## 4. Diagram

```
                    STRICT <-----------------------------> RELAXED

   LATENCY      |  overhead per request must be tiny  |
                |  (strict: sub-millisecond added        |
                |   latency on every gated request)         |

   AVAILABILITY |                                    | if the limiter itself
                |                                    | fails, prefer FAILING
                |                                    | OPEN over taking the
                |                                    | whole service down
                |                                    | (relaxed toward the
                |                                    | protected service's
                |                                    | own availability)

   ACCURACY     |                                    | small, bounded over/
                |                                    | under-counting is
                |                                    | acceptable in exchange
                |                                    | for throughput (relaxed:
                |                                    | approximate counting
                |                                    | under high concurrency
                |                                    | is a deliberate choice)
```
*Caption: latency sits on the strict end, since the limiter is on every gated request's critical path; accuracy and availability both deliberately relax in favor of not becoming the system's own point of failure.*

## 5. Runnable example

### Measurable NFR targets

```text
LATENCY
  NFR-1: Rate-limit check overhead: p99 < 5 ms added to the gated request
         (ideally sub-millisecond for an in-memory or local check).

SCALE
  NFR-2: Support 1 million distinct active clients being tracked
         simultaneously.
  NFR-3: Sustain at least the protected service's own peak QPS - if the
         protected service peaks at 50,000 QPS, the rate limiter must
         sustain checks at that same rate without becoming the bottleneck.

ACCURACY
  NFR-4: Under normal (non-adversarial) load, enforce the configured limit
         within a small bounded margin (e.g. +/- 1-2% of the configured N)
         - not necessarily exact, especially under high concurrency across
         distributed limiter instances.

AVAILABILITY
  NFR-5: If the rate limiter's own backing store (e.g. a shared cache)
         becomes unavailable, the system fails OPEN by default (requests
         pass through unchecked) rather than failing closed - a
         configurable choice per deployment, but this is the default.

DISTRIBUTED CONSISTENCY
  NFR-6: When the rate limiter runs as multiple instances, per-client
         usage counts converge across instances within a bounded delay
         (e.g. within one window's worth of time), rather than requiring
         instant, strongly consistent agreement on every single request.
```

## 6. Walkthrough

1. **NFR-1 (sub-5ms overhead) is the number that most directly shapes the algorithm choice in later facets of this case study.** A rate-limiting algorithm that requires a network round-trip to a remote, strongly-consistent store on every single request risks violating this target under real network latency — this pushes the design toward algorithms that can be checked with a fast, local (or low-latency) operation, even if that means accepting some imprecision under distributed operation.
2. **NFR-2 and NFR-3 (scale) establish that the rate limiter is not a small side component** — supporting a million distinct clients and matching the protected service's own peak throughput means the rate limiter's own storage and computation must scale independently, which is exactly the kind of number that justifies choosing a purpose-built, in-memory data structure over, say, a full relational database query per check.
3. **NFR-4 (bounded accuracy, not perfect accuracy) is a deliberate, stated relaxation, directly following from NFR-1's latency target.** A perfectly accurate distributed counter generally requires coordination (a lock, or a consensus round) that conflicts with sub-5ms latency at NFR-3's scale — accepting a small margin of error is what makes both targets simultaneously achievable, and this tradeoff must be named explicitly so nobody later assumes the rate limiter enforces limits with mathematical precision under concurrent load.
4. **NFR-5 (fail open) is a direct consequence of thinking about the rate limiter's own availability relative to the protected service's availability.** If the rate limiter were to fail closed (reject everything when its own backing store is unreachable), a rate-limiter outage would take down every service it protects — a single component becoming a much larger single point of failure than it was meant to guard against. Failing open trades away enforcement during that outage window in exchange for keeping the protected service itself available.
5. **NFR-6 (bounded convergence, not instant agreement) directly anticipates the [rate limiter's own architecture](0236-rate-limiter-high-level-architecture.md) running as multiple instances for its own scale and availability** — those instances checking a shared or partially-shared view of each client's usage is only tractable if instant, perfect agreement is not required, which is exactly what this NFR states up front.

## 7. Gotchas & takeaways

> **Gotcha:** choosing "fail open" (NFR-5) as a blanket default is not correct for every use case — a rate limiter protecting against a genuine denial-of-service attack, where letting requests through unchecked during an outage could be actively dangerous, might deliberately choose "fail closed" instead. State which choice a given deployment makes explicitly, rather than assuming fail-open is universally correct.

- Sub-5ms latency (NFR-1) is the target that most constrains later algorithm and architecture choices — any later facet page proposing a slow, remote, strongly-consistent check should be checked against this number directly.
- Bounded accuracy (NFR-4) and bounded consistency convergence (NFR-6) are the same underlying tradeoff — approximate correctness in exchange for throughput and low latency — applied at two different layers (a single instance's counting, and multiple instances' agreement).
- Fail-open vs. fail-closed (NFR-5) is a real design decision with real consequences either way; state it explicitly rather than leaving it as an implicit default nobody actually chose.
- See [Rate Limiter — capacity estimation](0235-rate-limiter-capacity-estimation.md) next, where NFR-2 and NFR-3's scale numbers get turned into concrete memory and throughput figures.
