---
card: system-design
gi: 238
slug: rate-limiter-data-model-schema
title: Rate Limiter — data model & schema
---

## 1. What it is

This page covers the **data model & schema** facet of the **Rate Limiter** case study — the concrete keys and values the [shared counter store from the high-level architecture](0237-rate-limiter-high-level-architecture.md) actually holds, and the separate, small configuration schema that defines each client's limits (FR-4).

## 2. Why & when

The architecture facet named "a shared counter store" as a component; this facet defines exactly what is stored in it — the key structure, value shape, and expiration behavior — since those details directly determine whether the store can answer `allow(...)` with a single atomic operation, as the architecture requires.

## 3. Core concept

- **Counter data model: key-value, not relational.** Unlike the [URL Shortener](0229-url-shortener-data-model-schema.md)'s entities with real relationships, the rate limiter's counter data is a flat mapping — `(clientId, ruleName) → current count within the active window` — with no joins needed, which is exactly the profile a key-value store handles best.
- **Key structure: `ratelimit:{clientId}:{ruleName}`.** Combining client and rule into one key means each rule's counter is fully independent (FR-6), and the key naturally partitions well across a sharded store (each key hashes to one shard, and no single client's rules need to coordinate across shards).
- **Value shape depends on the algorithm.** A fixed-window counter needs just an integer count plus an implicit or explicit window-start time. A sliding-window-log algorithm needs a list of individual request timestamps. A token-bucket algorithm needs a token count and a last-refill timestamp. This page's schema below shows the token-bucket shape, since it is the algorithm chosen in this case study's [deep-dive facet](0239-rate-limiter-deep-dive-distributed-counter-accuracy-algorith.md).
- **TTL matching the window, not a separate cleanup process.** Rather than a background job deleting expired counters, each key's TTL is set to (roughly) the rule's window length, so the store's own built-in expiration mechanism removes stale counters automatically — no manual cleanup logic needed.
- **Configuration data model: a small, separate table/lookup, not co-located with counters.** `(clientId or tier) → {limit, windowSeconds}` per rule — this data changes rarely (an admin adjusting a client's tier) compared to the counters (updated on every request), so keeping it separate avoids mixing a low-write-frequency dataset with an extremely high-write-frequency one.

## 4. Diagram

```
   COUNTER STORE (key-value, high write frequency)     CONFIG STORE (low write frequency)

   Key: "ratelimit:c-42:per-minute"                     Key: clientId or tier name
   Value: { tokens: 37.0, lastRefillAt: 1699999950 }     Value: { limit: 100, windowSeconds: 60,
   TTL: matches window (auto-expires)                             ruleName: "per-minute" }

   Key: "ratelimit:c-42:per-day"                        Key: "tier:free"
   Value: { tokens: 4801.0, lastRefillAt: ... }          Value: { limit: 100, windowSeconds: 60 }
   TTL: matches window (auto-expires)

   Key: "ratelimit:c-99:per-minute"                     Key: "tier:paid"
   Value: { tokens: 8532.0, lastRefillAt: ... }          Value: { limit: 10000, windowSeconds: 60 }
   TTL: matches window (auto-expires)
```
*Caption: the counter store is written on nearly every request and self-expires via TTL; the config store is written rarely (a tier change) and read on every request to know which limit applies — two very different access patterns, kept in two separate structures.*

## 5. Runnable example

### Schema (key-value shape, expressed as JSON document structure)

```json
// Counter store entry - one per (clientId, ruleName) pair.
// Key: "ratelimit:{clientId}:{ruleName}"
{
  "tokens": 37.0,
  "lastRefillAt": 1699999950,
  "_ttlSeconds": 60
}

// Config store entry - one per client OR per tier (whichever a given
// deployment uses to assign limits; tiers are shown here per FR-4).
// Key: "tier:{tierName}" or "client:{clientId}" (client-specific override)
{
  "rules": [
    { "ruleName": "per-minute", "limit": 100,  "windowSeconds": 60 },
    { "ruleName": "per-day",    "limit": 5000, "windowSeconds": 86400 }
  ]
}

// Client-to-tier assignment (a small, separate lookup).
// Key: "client-tier:{clientId}"
{
  "tier": "free"
}
```

## 6. Walkthrough

1. **The counter store's key, `"ratelimit:c-42:per-minute"`, combines the client ID and the rule name into a single string**, which is what lets a single atomic `INCR`-style operation on this one key answer "how many requests has `c-42` made under the `per-minute` rule" — no join, no secondary lookup, exactly the single-operation atomicity the [high-level architecture](0237-rate-limiter-high-level-architecture.md) requires for correctness under concurrency.
2. **The value, `{ tokens: 37.0, lastRefillAt: 1699999950 }`, reflects the token-bucket algorithm's specific state**, not a plain counter — this shape is chosen because the [deep-dive facet](0239-rate-limiter-deep-dive-distributed-counter-accuracy-algorith.md) selects token bucket as this case study's algorithm; a different algorithm choice (fixed window, sliding window) would need a different value shape, which is why this facet explicitly notes the value shape is algorithm-dependent rather than fixed.
3. **The `_ttlSeconds` matching the rule's window means the store itself removes this key once the window has fully elapsed with no further activity** — for a `per-minute` rule, a client that stops making requests has its counter key expire and disappear within roughly a minute, with zero manual cleanup logic required anywhere in the application code.
4. **The config entry under `"tier:free"` lists both rules (`per-minute` and `per-day`) together**, directly implementing FR-6 — a single client can be checked against multiple named rules, and each rule's `limit` and `windowSeconds` come from this one config lookup, read once per request (or cached briefly, since it changes rarely) rather than hardcoded into application logic.
5. **`"client-tier:c-42"` mapping to `{"tier": "free"}` is a separate, small lookup from the tier's actual rule definitions** — this indirection is what implements FR-4's "different limits for different clients or tiers" cleanly: changing `c-42`'s tier from `free` to `paid` is a single small write to this mapping, with zero changes needed to the tier definitions or the counter data itself.

## 7. Gotchas & takeaways

> **Gotcha:** setting a counter key's TTL to exactly the window length, refreshed on every increment, can cause a client's window to never fully reset if they make at least one request per window indefinitely — each request pushes the TTL forward again before it expires. A correct token-bucket or fixed-window implementation must set the TTL (or compute the window boundary) independently of individual request timestamps, not refresh it on every touch.

- The counter store's key structure (`clientId` + `ruleName`) is what makes FR-3 (per-client independence) and FR-6 (multiple simultaneous rules) both hold simultaneously — each combination gets its own fully independent key.
- Separate the high-write-frequency counter data from the low-write-frequency configuration data — mixing them (e.g. storing a client's limit inline with its counter, rewritten on every request) risks accidentally overwriting configuration during a routine counter update.
- Let the store's own TTL mechanism handle counter expiration rather than a manual cleanup job — this is both simpler and avoids an entire class of "stale counter never got cleaned up" bugs.
- See [Rate Limiter — deep-dive: distributed counter accuracy & algorithm choice](0239-rate-limiter-deep-dive-distributed-counter-accuracy-algorith.md) next for the actual token-bucket algorithm that reads and writes the `tokens`/`lastRefillAt` value shape defined here.
