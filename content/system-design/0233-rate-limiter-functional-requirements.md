---
card: system-design
gi: 233
slug: rate-limiter-functional-requirements
title: Rate Limiter — functional requirements
---

## 1. What it is

This page covers the **functional requirements** facet of the **Rate Limiter** system-design case study — a service that limits how many requests a client can make in a given time window, protecting downstream systems from being overwhelmed. Functional requirements are the concrete things the system must do, as opposed to how fast or reliable it must do them (a separate facet, [non-functional requirements](0234-rate-limiter-non-functional-requirements.md)).

## 2. Why & when

A rate limiter's entire job is enforcing a rule ("no more than N requests per window"), so getting that rule's exact behavior right — what counts as a "request," how the window works, what happens right at the limit — is the foundation every later facet builds on. Start here, before considering algorithms or architecture, because those choices only make sense once the exact rules to enforce are pinned down.

## 3. Core concept

Prioritize using **MoSCoW** (Must / Should / Could):

- **Must have:**
  - Given a client identifier (API key, user ID, or IP address) and a configured limit (e.g. "100 requests per minute"), allow requests up to that limit within the current window and reject requests beyond it.
  - Return a clear signal to a rejected client that it was rate-limited, distinct from any other kind of failure.
  - Apply limits per client independently — one client exceeding its limit must not affect any other client's ability to make requests.
- **Should have:**
  - Support **different limits for different clients or tiers** (a free-tier client gets 100 req/min, a paid-tier client gets 10,000 req/min).
  - Expose the client's current usage and remaining quota via response headers (see [rate-limit & caching headers](0214-rate-limit-caching-headers.md)), so well-behaved clients can self-throttle proactively.
  - Support multiple simultaneous limit rules per client (e.g. both "100/minute" and "5,000/day" enforced together).
- **Could have:**
  - Allow a short **burst** above the steady-state limit, as long as the longer-term average stays within bounds (this is a specific algorithmic choice, covered in later facets).
  - Support dynamically updating a client's limit without restarting the service (e.g. an admin manually raising a specific client's quota).
- **Explicitly out of scope for this case study:**
  - Authentication of the client identifier itself (the rate limiter trusts whatever identifier it is given — validating that identifier belongs to who claims it is a separate concern).
  - Billing or usage-based pricing built on top of the rate-limit data (the rate limiter enforces and reports usage; what a billing system does with that data is out of scope).

## 4. Diagram

```
        +------------------+                        +------------------+
        |   Client A        |                        |   Client B        |
        |  (100 req/min)    |                        |  (10,000 req/min) |
        +--------+---------+                        +--------+---------+
                 |                                              |
      "make requests, up to my limit"              "make requests, up to my limit"
      "know my remaining quota" (should)            (independent limit, own tier)
                 |                                              |
                 v                                              v
        +------------------------------------------------------------+
        |                        Rate Limiter                          |
        +------------------------------------------------------------+
                 |
      "reject clearly when over limit"
      "never let one client affect another's quota"
```
*Caption: every client is limited independently — Client A exceeding its own limit has zero effect on Client B's ability to make requests, which is a hard requirement, not an implementation detail.*

## 5. Runnable example

### Requirements list

```text
MUST HAVE
  FR-1: Enforce a configured limit (N requests per time window T) per client
        identifier.
  FR-2: Reject requests beyond the limit with a clear, distinguishable
        signal (not a generic error).
  FR-3: Enforce limits independently per client - one client's usage must
        never affect another client's quota.

SHOULD HAVE
  FR-4: Support different limits per client or client tier.
  FR-5: Expose current usage / remaining quota via response headers.
  FR-6: Support multiple simultaneous limit rules per client (e.g. a
        per-minute AND a per-day limit, both enforced).

COULD HAVE
  FR-7: Allow short bursts above the steady-state limit, bounded by a
        longer-term average (an algorithmic choice, not a hard requirement).
  FR-8: Support live limit updates for a specific client, with no restart.

OUT OF SCOPE
  - Authenticating the client identifier itself.
  - Billing or usage-based pricing on top of collected usage data.
```

## 6. Walkthrough

1. **FR-1 and FR-2 are the reason this system exists** — enforcing a numeric limit and clearly signaling rejection. Every later facet, including the choice of algorithm, exists to satisfy these two requirements efficiently and correctly at scale.
2. **FR-3 (per-client independence) has a direct architectural implication**: it means the rate limiter's internal state (how many requests a client has made so far) must be tracked per client identifier, never as one shared global counter — a design that pools usage across clients, even accidentally, would violate this requirement outright.
3. **FR-4 (per-tier limits) affects configuration, not the core algorithm** — whatever mechanism enforces "N requests per window" for one client works identically for a different N assigned to a different client; the requirement is about configurability, not a fundamentally different enforcement mechanism per tier.
4. **FR-5 (usage headers) directly reuses the pattern from [rate-limit & caching headers](0214-rate-limit-caching-headers.md)** — `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` on every response, not just on a rejection, so well-behaved clients can see they are approaching their limit and slow down before being rejected.
5. **FR-6 (multiple simultaneous rules) is what pushes the design toward an algorithm that can track more than one window size at once** — a per-minute and a per-day limit enforced together means the chosen algorithm (covered in the algorithm facet of this case study) must support layering multiple rules per client, not just a single window.

## 7. Gotchas & takeaways

> **Gotcha:** FR-3 (per-client independence) is easy to state and easy to accidentally violate in implementation — a naive shared data structure (like one global counter map keyed loosely, or a single lock protecting all clients' counters) can create contention or cross-client interference that was never intended. Treat this requirement as a hard constraint on the data model, not just a description of desired behavior.

- FR-1 through FR-3 define the non-negotiable core; everything else in this list builds on top of a system that already gets those three exactly right.
- Listing "authenticating the client identifier" as explicitly out of scope avoids a common confusion — a rate limiter enforces limits against whatever identifier it is handed, and trusting that identifier is a separate system's job (usually an API gateway performing auth before the rate limiter ever runs, as in [API gateway & BFF composition](0215-api-gateway-bff-composition.md)).
- See [Rate Limiter — non-functional requirements](0234-rate-limiter-non-functional-requirements.md) next for the latency, accuracy, and scale targets these functional requirements must be delivered under.
