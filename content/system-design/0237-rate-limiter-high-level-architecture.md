---
card: system-design
gi: 237
slug: rate-limiter-high-level-architecture
title: Rate Limiter — high-level architecture
---

## 1. What it is

This page covers the **high-level architecture** facet of the **Rate Limiter** case study — the components (app servers, a shared counter store, the limiter logic itself) and how the `allow(...)` check from [API design](0236-rate-limiter-api-design.md) actually gets answered fast enough to sit on every request's critical path.

## 2. Why & when

The [capacity estimation](0235-rate-limiter-capacity-estimation.md) established that memory footprint is trivial (~80 MB) but throughput (~50,000 ops/sec, sub-5ms latency) is the real constraint. This facet is where that specific constraint becomes a concrete architecture — namely, why a shared, purpose-built in-memory store beats both a fully local (per-instance) counter and a general-purpose database.

## 3. Core concept

- **Stateless app servers, calling a shared counter store.** Since the [non-functional requirements](0234-rate-limiter-non-functional-requirements.md)'s FR-3 (per-client independence) and NFR-6 (bounded convergence across instances) both assume the rate limiter's state is visible across every app server instance, the counter data cannot live only in one instance's local memory — otherwise a client's requests landing on different app server instances (the normal case, behind a load balancer) would each see a different, incomplete view of that client's usage.
- **A purpose-built in-memory store (e.g. Redis) as the shared counter backend.** Chosen directly from the capacity estimation's throughput number — Redis's single-threaded, in-memory design and atomic increment operations (`INCR`, or a Lua script for more complex logic) meet the sub-5ms latency target at the required ~50,000 ops/sec, which a general-purpose relational database's per-query overhead would struggle to match.
- **Atomic operations, not read-then-write.** A naive "read the counter, check it, increment it" sequence has a race condition under concurrent requests from the same client (two requests both read count=99, both think they are allowed, both increment — the client ends up over its limit). The store must perform the check-and-increment as one atomic operation.
- **A local, short-lived cache on the app server as an optional fast path.** For very tight latency budgets, each app server can cache a client's last-known remaining quota locally for a very short time (milliseconds), avoiding a network round-trip to the shared store for every single request — at the cost of slightly relaxed accuracy, which NFR-4 already permits.
- **Fail-open fallback.** If the shared store becomes unreachable, the app server's `allow(...)` call catches that failure and returns `true` (allow) by default, per NFR-5 — the protected service keeps running, unprotected, until the store recovers.

## 4. Diagram

```
                              +----------------+
      Client requests ------->|  Load Balancer   |
                              +--------+--------+
                                       |
                    +------------------+------------------+
                    v                                       v
             +-------------+                         +-------------+
             | App Server A |                         | App Server B |
             | (stateless)  |                         | (stateless)  |
             +------+------+                         +------+------+
                    |                                        |
                    |     allow(clientId, rule)                |
                    +------------------+-----------------------+
                                       v
                          +---------------------------+
                          |   Shared Counter Store       |
                          |   (e.g. Redis, in-memory,     |
                          |    atomic INCR / Lua script)   |
                          +---------------------------+

   Both app servers check the SAME shared store, so a client's requests
   landing on either instance are counted against the same total - this
   is what makes FR-3 (per-client independence across the whole system,
   not just within one instance) actually hold.
```
*Caption: the shared store is what makes rate limiting correct across multiple app server instances — without it, each instance would enforce its own, smaller, effectively wrong limit.*

## 5. Runnable example

### Component list and key configuration

```text
APP SERVER (stateless, horizontally scaled)
  - Calls allow(clientId, rule) once per gated request, before business logic.
  - On allow()==false: returns 429 immediately, does not proceed.
  - On store failure/timeout: fails open (allow()==true), per NFR-5.
  - Optionally caches a client's last-known remaining quota locally for a
    few milliseconds, to shave off a network round-trip on true hot paths -
    a deliberate, small accuracy/latency tradeoff, allowed by NFR-4.

SHARED COUNTER STORE (e.g. Redis)
  - Key: clientId + rule name (e.g. "ratelimit:c-42:per-minute").
  - Value: current count within the active window, with a TTL matching the
    window length so old windows expire automatically with no manual cleanup.
  - All check-and-increment operations are ATOMIC (a single INCR command,
    or a Lua script for more complex algorithms), to avoid a check-then-
    increment race condition under concurrent requests.
  - Sized per capacity estimation: ~80 MB for 1M clients x 2 rules -
    trivially fits one well-provisioned instance; horizontal sharding by
    clientId hash is available if client count grows far beyond estimate.

CONFIGURATION SOURCE (per client/tier limits, FR-4)
  - A small, infrequently-changing config (client -> {limit, window} per
    rule), loaded by app servers, or looked up alongside the counter check.
```

## 6. Walkthrough

1. **A request from client `c-42` can land on App Server A or App Server B**, depending on the load balancer's routing decision for that particular request — this is normal, expected behavior for a horizontally scaled, stateless application layer, and the rate limiter's architecture must work correctly regardless of which instance handles any given request.
2. **Both app servers call `allow("c-42", "per-minute")` against the same shared counter store**, not against any instance-local state. This is the direct architectural answer to [functional requirements](0233-rate-limiter-functional-requirements.md)'s FR-3: if App Server A tracked `c-42`'s usage locally and App Server B tracked it separately, `c-42` could effectively get 2x its intended limit simply by having its requests split across the two instances — the shared store is what prevents this.
3. **The shared store performs the check-and-increment as a single atomic operation** (an `INCR` command, or a small Lua script for a more involved algorithm), rather than the app server reading the current count, checking it, and issuing a separate increment. Two nearly-simultaneous requests for the same client, from two different app servers, both reach the store — but because the store processes operations for a given key sequentially (Redis, being single-threaded per key operation, guarantees this), one of them sees the post-increment count and correctly gets rejected if it is over the limit, rather than both incorrectly succeeding due to a race.
4. **The store's key includes both `clientId` and the specific rule name** (`"ratelimit:c-42:per-minute"`), directly supporting FR-6's multiple-simultaneous-rules requirement — a separate key (and separate TTL matching that rule's window) tracks the `per-day` rule independently, so exhausting one does not affect the other's count.
5. **If the shared store becomes unreachable** (a network partition, the store itself being down), the app server's call to `allow(...)` times out or throws; the architecture's fail-open policy (from NFR-5) catches this specific failure and returns `true`, letting the request through unchecked rather than rejecting every request system-wide — a deliberate choice that the rate limiter's own failure should degrade gracefully rather than becoming a bigger outage than the one it was protecting against.

## 7. Gotchas & takeaways

> **Gotcha:** the local, short-lived app-server-side cache mentioned as an optional fast path introduces a real accuracy cost that is easy to underestimate — if every app server independently caches "this client still has quota" for even a few milliseconds, a burst of requests hitting many app servers simultaneously within that cache window can let a client exceed its limit by a multiple of the number of app server instances, not just by a small margin. Use this optimization only where NFR-4's accuracy tolerance genuinely allows it, and keep the cache window as short as the latency budget allows.

- The shared counter store is the architecture's load-bearing component — trace this choice directly back to FR-3 (per-client independence must hold *system-wide*, not per-instance) and to the capacity estimation's throughput number, not to a generic "use Redis for caching" instinct.
- Atomic check-and-increment operations are non-negotiable for correctness under concurrency — a naive read-then-write sequence looks correct in testing (low concurrency) and silently breaks under real production load (high concurrency), exactly the kind of bug that is hard to catch without deliberately designing atomicity in from the start.
- Fail-open (NFR-5) is implemented at the app-server level, in the `allow(...)` call's own failure handling — it is not something the shared store does on its own, since the store being unreachable is precisely the failure this policy needs to handle.
- See [Rate Limiter — deep-dive: distributed counter accuracy & algorithm choice](0239-rate-limiter-deep-dive-distributed-counter-accuracy-algorith.md) next for the specific algorithms (fixed window, sliding window, token bucket) that implement the counting logic this architecture's shared store executes.
