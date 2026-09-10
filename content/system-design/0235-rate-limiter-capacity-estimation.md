---
card: system-design
gi: 235
slug: rate-limiter-capacity-estimation
title: Rate Limiter — capacity estimation
---

## 1. What it is

This page covers the **capacity estimation** facet of the **Rate Limiter** case study — turning the scale targets from [non-functional requirements](0234-rate-limiter-non-functional-requirements.md) into concrete numbers: memory needed to track every active client's usage, and the throughput the rate limiter's own storage layer must sustain.

## 2. Why & when

The [non-functional requirements](0234-rate-limiter-non-functional-requirements.md) named "1 million active clients" and "match the protected service's peak QPS" as targets, but did not say whether those targets fit comfortably in memory on a single machine, or require a distributed store. Capacity estimation answers exactly that, and the answer directly determines the [high-level architecture](0234-rate-limiter-non-functional-requirements.md)'s storage choice — do this right after NFRs are set, before picking a specific storage technology.

## 3. Core concept

The estimation chain here is shorter than a typical read-heavy system's, because the rate limiter's job is not to store growing historical data — it only needs to track *current, per-window* usage per client:

1. Start from the **number of active clients** and the **per-client state size** (how many bytes it takes to track one client's usage for one rule).
2. Multiply to get **total memory footprint** for tracking every active client simultaneously.
3. Estimate **operations per second** the storage layer must sustain — this is one read-and-increment per gated request, not per client, so it equals the protected service's own peak QPS.
4. Check whether the memory footprint fits on a single machine, or requires a distributed cache/store — this is the number that most directly shapes the architecture decision.

## 4. Diagram

```
   active clients x per-client state size (bytes)  --> total memory footprint
        |
        v
   compare against single-machine memory capacity   --> fits on one node? or
                                                          needs a distributed
                                                          store, sharded by
                                                          client ID?
        |
        v
   protected service's peak QPS                     --> ops/sec the rate
                                                          limiter's own storage
                                                          layer must sustain
```
*Caption: unlike a growing dataset, the rate limiter's memory footprint is roughly constant (bounded by the number of currently active clients), which is what makes the "does it fit on one machine" question answerable with a single multiplication.*

## 5. Runnable example

### Worked calculation

```text
ASSUMPTIONS
  - Active clients tracked simultaneously: 1,000,000 (per NFR-2).
  - Rules per client: 2 (a per-minute limit and a per-day limit, per FR-6).
  - Per-rule state size: ~40 bytes (a counter, a window-start timestamp, a
    client ID reference, plus data-structure overhead - a generous estimate
    for a token-bucket or sliding-window counter's state).
  - Protected service peak QPS: 50,000 (per NFR-3) - this becomes the rate
    limiter's own required operations/sec, roughly one check per request.

STEP 1: per-client memory footprint
  2 rules x 40 bytes/rule = 80 bytes/client

STEP 2: total memory footprint for all active clients
  1,000,000 clients x 80 bytes/client = 80,000,000 bytes ~= 80 MB

STEP 3: operations per second the storage layer must sustain
  ~50,000 QPS (one read-and-increment operation per gated request, roughly;
  some algorithms need slightly more than one operation per check, covered
  in the algorithm facet of this case study)

STEP 4: does it fit on one machine?
  80 MB is trivially small for a single modern server's memory (even a
  small instance has multiple GB of RAM) - so MEMORY is not the
  constraint. 50,000 operations/sec IS a meaningful number for a single
  in-memory store instance to sustain under NFR-1's sub-5ms latency
  target, especially if operations must also be safely concurrent.

SUMMARY
  - Total memory footprint: ~80 MB (trivial - fits comfortably on one
    machine, with enormous headroom even at 10x this client count).
  - Required throughput: ~50,000 ops/sec, which DOES justify a purpose-
    built in-memory store (not a general-purpose relational database) to
    comfortably meet the sub-5ms latency target under concurrent load.
```

## 6. Walkthrough

1. **Step 1 multiplies the number of rules per client (2, from FR-6) by the estimated size of one rule's state (~40 bytes)**, producing 80 bytes per client. This number is intentionally rough — it depends on the exact algorithm chosen (a fixed counter needs less state than a sliding-window log) — but even a generously padded estimate stays small, which is the point of doing this calculation at all.
2. **Step 2 multiplies by the total active client count (1 million, from NFR-2 in [non-functional requirements](0234-rate-limiter-non-functional-requirements.md))**, giving ~80 MB total. This is the number that answers the architecture's most important storage question directly: memory footprint is not a constraint here, even at ten times this client count it would still fit comfortably on a single machine's memory.
3. **Step 3 does not require a separate QPS-derivation calculation the way the [URL Shortener's estimation](0226-url-shortener-capacity-estimation.md) did**, because the rate limiter's required throughput is a direct pass-through of the protected service's own peak QPS (NFR-3) — every gated request triggers roughly one check, so the rate limiter's ops/sec requirement is, by definition, at least as large as the service it protects.
4. **Step 4 draws the conclusion the whole estimation was aiming for**: memory is trivially available, but sustaining 50,000 operations per second with sub-5ms latency, safely under concurrent access from many application server instances, is a real throughput requirement — this is exactly the number that justifies choosing a purpose-built, in-memory key-value store (like Redis) as the [high-level architecture](0234-rate-limiter-non-functional-requirements.md)'s storage layer, rather than a general-purpose relational database whose per-operation overhead would struggle to meet the latency target at this rate.
5. **The contrast with the [URL Shortener case study](0226-url-shortener-capacity-estimation.md) is instructive**: that system's bottleneck was storage growth over years and read QPS; this system's "storage" barely grows at all (it tracks current state, not history), and its defining number is raw operations-per-second throughput under tight latency — a genuinely different profile that leads to a genuinely different architecture, even though both systems used the same estimation method.

## 7. Gotchas & takeaways

> **Gotcha:** it is tempting to assume a rate limiter's storage needs are "basically nothing" once the memory footprint estimate comes back small (80 MB) — but the throughput requirement (50,000 ops/sec, with strict latency) is the real constraint this estimation surfaces, and it is easy to overlook if you stop calculating after the memory number looks comfortably small.

- Memory footprint and throughput are two independent numbers that can point to very different conclusions — this system's memory is trivial, but its throughput requirement is the actual design driver, and both must be checked explicitly rather than assuming a small memory number means the whole system is "easy."
- The rate limiter's memory footprint stays roughly constant regardless of how long the system has been running, unlike a system that accumulates historical records — this is a direct consequence of only tracking *current* per-window usage, not history.
- The ~50,000 ops/sec throughput number, under a sub-5ms latency target, is exactly what justifies an in-memory store like Redis over a general-purpose database for this system's storage layer — a decision made concrete by this specific estimation, not by a general preference for "using Redis."
- This closes the requirements-and-estimation portion of the Rate Limiter case study — later facet pages (API design, algorithm choice, high-level architecture) build directly on the numbers established here, the same way the [URL Shortener](0224-url-shortener-functional-requirements.md) case study's later facets built on its own estimation.
