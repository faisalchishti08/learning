---
card: microservices
gi: 506
slug: near-cache
title: "Near cache"
---

## 1. What it is

A **near cache** is a small, fast local cache layered directly in front of a distributed cache client — the application checks the near cache (in-process memory) first, and only falls through to the actual network call to the distributed cache on a near-cache miss. It's the same two-tier structure as [local vs distributed cache](0502-local-vs-distributed-cache.md), but specifically framed around a client library's own built-in optimization: many distributed cache clients (Hazelcast, some Redis client configurations) offer this as a built-in feature, rather than something you build by hand.

## 2. Why & when

You enable a near cache specifically to shave the network round trip off of the hottest, most frequently-read keys in a distributed cache setup:

- **Even a fast distributed cache still costs a network round trip on every access.** For extremely hot keys — read thousands of times per second by a given instance — that round-trip cost adds up to real, measurable latency and network load, even against a well-performing distributed cache.
- **A near cache captures the benefit of local caching's speed specifically for the subset of data that's hot enough to justify it**, without requiring you to build and maintain a fully separate local-caching layer and invalidation strategy by hand.
- **Client library support removes most of the implementation burden.** Since the near cache is built into the distributed cache client itself, invalidation (when the distributed cache's underlying value changes) is often handled automatically by the client, rather than needing hand-rolled event-based invalidation.
- **You enable this specifically for read-heavy, hot-key workloads** where the distributed cache's own network latency is a measurable bottleneck — for cold or evenly-distributed access patterns, a near cache adds memory overhead and invalidation complexity without a meaningful corresponding speed benefit.

## 3. Core concept

Think of keeping a small personal reference card with the phone numbers you call most often, right next to your desk, even though the complete, authoritative phone directory (the distributed cache) is also easily accessible in the next room — for the handful of numbers you call constantly, glancing at your desk card is meaningfully faster than walking to the directory every single time, while for anything not on your card, you still go check the full directory.

Concretely:

1. **The near cache sits in the same process as the application**, exactly like a local cache, but it's specifically scoped as a fast-path optimization layered in front of a distributed cache client, not a standalone caching strategy of its own.
2. **A read first checks the near cache**; on a hit, it returns immediately with no network call at all — the fastest possible path.
3. **On a near-cache miss, the client falls through to the actual distributed cache**, over the network, and (typically) populates the near cache with the result before returning it, so the *next* read for that same key hits the fast local path.
4. **Invalidation is the hard part, and is often handled by the client library itself**: when the underlying distributed cache entry changes, the client needs some mechanism (often a subscription to change notifications) to invalidate the corresponding near-cache entry across every connected client instance — without this, a near cache reintroduces exactly the staleness problem [local caching](0502-local-vs-distributed-cache.md) has.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A read checks the near cache first for an instant hit; on a miss it falls through to the distributed cache over the network and populates the near cache for next time">
  <rect x="20" y="60" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="95" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">near cache</text>
  <text x="95" y="102" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">in-process, no network</text>

  <rect x="440" y="60" width="180" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="530" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">distributed cache</text>
  <text x="530" y="102" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">network round trip</text>

  <line x1="170" y1="90" x2="440" y2="90" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#a1)"/>
  <text x="300" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">only on a near-cache miss</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The near cache absorbs most reads locally; only misses pay the network cost of reaching the distributed cache.

## 5. Runnable example

Scenario: a near-cache-aware client wrapping a simulated distributed cache. We start with a basic near-cache read path measuring the speed difference, extend it to automatic population on a miss, then handle the hard case: the distributed cache's value changing underneath, requiring an invalidation notification to correctly evict the now-stale near-cache entry across the client, not just leave it silently wrong.

### Level 1 — Basic

```java
// File: NearCacheReadPath.java -- models the CORE near-cache read path:
// check the fast LOCAL near cache first, fall through to the SLOWER
// distributed cache (simulated with a delay) only on a miss.
import java.util.*;

public class NearCacheReadPath {
    static Map<String, String> nearCache = new HashMap<>();
    static Map<String, String> distributedCache = new HashMap<>(Map.of("sku-123", "in-stock"));

    static String distributedCacheGet(String key) throws InterruptedException {
        Thread.sleep(20); // simulates a real network round trip
        return distributedCache.get(key);
    }

    static String get(String key) throws InterruptedException {
        if (nearCache.containsKey(key)) {
            System.out.println("[near cache] HIT for '" + key + "' -- no network call");
            return nearCache.get(key);
        }
        System.out.println("[near cache] MISS for '" + key + "' -- falling through to distributed cache");
        String value = distributedCacheGet(key);
        nearCache.put(key, value);
        return value;
    }

    public static void main(String[] args) throws InterruptedException {
        long start1 = System.currentTimeMillis();
        get("sku-123");
        System.out.println("first call took ~" + (System.currentTimeMillis() - start1) + "ms");

        long start2 = System.currentTimeMillis();
        get("sku-123");
        System.out.println("second call took ~" + (System.currentTimeMillis() - start2) + "ms");
    }
}
```

How to run: `java NearCacheReadPath.java`

The first `get` call misses `nearCache`, pays the simulated `20ms` network delay inside `distributedCacheGet`, and populates `nearCache` before returning. The second call for the identical key hits `nearCache` directly, returning near-instantly — the measured timing difference between the two calls is the concrete, observable benefit a near cache provides for repeated reads of the same hot key.

### Level 2 — Intermediate

```java
// File: NearCacheMultipleKeys.java -- the SAME read path, now EXERCISED
// across MULTIPLE keys with different access frequencies, showing the
// near cache naturally absorbing the HOT key's repeated reads while
// COLD keys still pay the network cost every time they're accessed.
import java.util.*;

public class NearCacheMultipleKeys {
    static Map<String, String> nearCache = new HashMap<>();
    static Map<String, String> distributedCache = new HashMap<>(Map.of(
        "hot-sku", "in-stock", "cold-sku-1", "in-stock", "cold-sku-2", "out-of-stock"
    ));
    static int distributedCacheCallCount = 0;

    static String distributedCacheGet(String key) {
        distributedCacheCallCount++;
        return distributedCache.get(key);
    }

    static String get(String key) {
        if (nearCache.containsKey(key)) return nearCache.get(key);
        String value = distributedCacheGet(key);
        nearCache.put(key, value);
        return value;
    }

    public static void main(String[] args) {
        // hot-sku is read 5 times; cold keys are read once each.
        for (int i = 0; i < 5; i++) get("hot-sku");
        get("cold-sku-1");
        get("cold-sku-2");

        System.out.println("[stats] total reads: 7, actual distributed cache calls: " + distributedCacheCallCount);
        System.out.println("[stats] near cache absorbed " + (7 - distributedCacheCallCount) + " reads that would otherwise have hit the network");
    }
}
```

How to run: `java NearCacheMultipleKeys.java`

`distributedCacheCallCount` only increments inside `distributedCacheGet`, which only runs on a `nearCache` miss — `"hot-sku"` triggers exactly one such call (its first read) despite being read five times total, while each cold key triggers exactly one call each (their only read) — the near cache naturally concentrates its benefit on whichever keys are actually accessed repeatedly, with no special configuration needed to identify "hot" keys in advance.

### Level 3 — Advanced

```java
// File: NearCacheInvalidationOnChange.java -- the SAME near cache, now
// handling the PRODUCTION-FLAVORED hard case: the underlying DISTRIBUTED
// cache value CHANGES (a write happens elsewhere). Without an explicit
// invalidation mechanism, the near cache would silently keep serving the
// OLD value forever. This models the client library's typical solution:
// SUBSCRIBING to change notifications and invalidating the near-cache
// entry the moment a relevant change is detected.
import java.util.*;

public class NearCacheInvalidationOnChange {
    static Map<String, String> nearCache = new HashMap<>();
    static Map<String, String> distributedCache = new HashMap<>(Map.of("sku-123", "in-stock"));
    static List<Runnable> changeSubscribers = new ArrayList<>(); // simulates the client's change-notification subscription

    static String distributedCacheGet(String key) {
        return distributedCache.get(key);
    }

    static String get(String key) {
        if (nearCache.containsKey(key)) {
            System.out.println("[near cache] HIT for '" + key + "'");
            return nearCache.get(key);
        }
        System.out.println("[near cache] MISS for '" + key + "' -- fetching from distributed cache");
        String value = distributedCacheGet(key);
        nearCache.put(key, value);
        return value;
    }

    // A write to the distributed cache ALSO notifies every subscribed near-cache client.
    static void distributedCacheWrite(String key, String newValue) {
        distributedCache.put(key, newValue);
        System.out.println("[distributed cache] '" + key + "' updated to '" + newValue + "' -- notifying subscribers");
        for (Runnable subscriber : changeSubscribers) {
            subscriber.run();
        }
    }

    // The near cache SUBSCRIBES to changes, so it can invalidate itself when notified.
    static void subscribeToInvalidation(String key) {
        changeSubscribers.add(() -> {
            if (nearCache.remove(key) != null) {
                System.out.println("[near cache] invalidated '" + key + "' due to a change notification from the distributed cache");
            }
        });
    }

    public static void main(String[] args) {
        subscribeToInvalidation("sku-123");

        System.out.println("--- initial read, populates the near cache ---");
        System.out.println("value: " + get("sku-123"));

        System.out.println();
        System.out.println("--- someone ELSE writes a new value directly to the distributed cache ---");
        distributedCacheWrite("sku-123", "out-of-stock");

        System.out.println();
        System.out.println("--- next read: near cache was invalidated, correctly falls through and gets the NEW value ---");
        System.out.println("value: " + get("sku-123"));
    }
}
```

How to run: `java NearCacheInvalidationOnChange.java`

`subscribeToInvalidation` registers a `Runnable` that removes the specific key from `nearCache` — this stands in for the near-cache client subscribing to the distributed cache's change-notification mechanism. `distributedCacheWrite` iterates every subscriber and runs each one after updating the underlying value, so the moment `"sku-123"` changes in `distributedCache`, the corresponding `nearCache` entry is proactively removed — the next `get` call correctly finds a miss (rather than stale data) and re-fetches the genuinely current value.

## 6. Walkthrough

Trace `NearCacheInvalidationOnChange.main` in order. **First**, `subscribeToInvalidation("sku-123")` registers a change-handler `Runnable` for this specific key into `changeSubscribers` — at this point, `nearCache` is still empty and no invalidation has happened yet.

**Next**, the initial `get("sku-123")` call misses `nearCache`, calls `distributedCacheGet` to retrieve `"in-stock"`, and populates `nearCache` with that value before returning it.

**Then**, `distributedCacheWrite("sku-123", "out-of-stock")` runs: it first updates `distributedCache` directly to the new value, then iterates `changeSubscribers` — the one subscriber registered earlier runs, checking `nearCache.remove("sku-123")`, which succeeds (returns non-null) since the entry was indeed present from the earlier read, so the invalidation message prints.

**After that**, `nearCache` no longer contains an entry for `"sku-123"` at all — it was explicitly removed by the subscriber's callback, not by any TTL or capacity-based eviction.

**Finally**, the second `get("sku-123")` call runs: `nearCache.containsKey("sku-123")` is now `false`, since it was invalidated, so the miss branch runs again, calling `distributedCacheGet` fresh — this time it returns `"out-of-stock"`, the genuinely current value, which is what gets returned and re-cached, correctly avoiding what would otherwise have been silently stale data served indefinitely from the near cache.

```
--- initial read, populates the near cache ---
[near cache] MISS for 'sku-123' -- fetching from distributed cache
value: in-stock

--- someone ELSE writes a new value directly to the distributed cache ---
[distributed cache] 'sku-123' updated to 'out-of-stock' -- notifying subscribers
[near cache] invalidated 'sku-123' due to a change notification from the distributed cache

--- next read: near cache was invalidated, correctly falls through and gets the NEW value ---
[near cache] MISS for 'sku-123' -- fetching from distributed cache
value: out-of-stock
```

## 7. Gotchas & takeaways

> A near cache with no invalidation mechanism at all is worse than no near cache — it doesn't just risk occasional staleness, it *guarantees* every entry becomes permanently stale the moment the underlying distributed value changes, since nothing ever tells the near cache to reconsider. Always pair a near cache with a genuine invalidation mechanism, whether client-library-provided change notifications or a short TTL as a fallback safety net.
- Near cache is specifically valuable for a small set of genuinely hot keys — sizing it too large, or applying it universally to every key regardless of access frequency, adds memory and invalidation-subscription overhead without a corresponding benefit for keys that were never accessed often enough to justify it.
- Client libraries that offer near-cache support usually handle the change-notification subscription mechanism for you — verify your specific distributed cache client's documentation for exactly how (and how reliably) it invalidates near-cache entries before relying on it for data where staleness genuinely matters.
- This is architecturally the same two-tier idea as [local vs distributed cache](0502-local-vs-distributed-cache.md), specifically packaged as a built-in optimization within a distributed cache client rather than something assembled by hand across two separate caching systems.
- Measure the actual latency benefit before adding near-cache complexity — for a distributed cache that's already extremely fast (co-located on the same low-latency network), the marginal benefit of a near cache may be smaller than the invalidation complexity it introduces.
