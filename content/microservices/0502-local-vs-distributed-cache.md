---
card: microservices
gi: 502
slug: local-vs-distributed-cache
title: "Local vs distributed cache"
---

## 1. What it is

A **local cache** lives in a single service instance's own memory — extremely fast, but private to that one instance, meaning each instance has its own separate, potentially inconsistent copy. A **distributed cache** (Redis, Memcached) lives in a separate, shared service that every instance of an application connects to over the network — slower than local memory per access, but shared and consistent across every instance, so all of them see the same cached value at the same time.

## 2. Why & when

You choose between them — or use both together in a multi-tier setup — based on how much consistency across instances actually matters versus how much raw speed you need:

- **A local cache is the fastest possible option, since there's no network hop at all** — reading from a `HashMap` in the same process is orders of magnitude faster than even the quickest network round trip to a separate cache service.
- **A local cache's isolation is also its biggest weakness at scale.** With multiple instances of a service running (which any horizontally-scaled microservice has), each instance's local cache can hold a different value for the same key — instance A might have already refreshed a cached price while instance B is still serving a stale one, with no coordination between them.
- **A distributed cache gives every instance a consistent view**, since they're all reading from and writing to the same shared cache — at the cost of network latency on every access, and the distributed cache itself becoming a new piece of infrastructure to run, scale, and keep available.
- **You reach for local caching for data where slight staleness or per-instance inconsistency is genuinely tolerable and speed matters most**, and reach for distributed caching for data where every instance needs to agree — invalidation events, session data shared across instances, or anything where inconsistency between instances would cause visible, confusing bugs.

## 3. Core concept

Think of a local cache like a personal notebook you keep on your desk — instantly accessible, but only you can see what's written in it, and if a coworker updates the "official" information elsewhere, your notebook doesn't automatically update. A distributed cache is like a shared whiteboard in a common area — anyone walking by can read the same, current information, and an update to the whiteboard is immediately visible to everyone, but reaching the whiteboard takes a moment longer than glancing at your own desk.

Concretely:

1. **Local cache**: an in-process data structure (a `HashMap`, or a dedicated in-memory caching library like Caffeine) — reads and writes are pure in-memory operations, with zero network involvement and zero coordination with any other instance.
2. **Distributed cache**: a separate networked service every instance connects to — reads and writes are network calls, but every instance sees the same underlying data, since there's genuinely only one copy.
3. **The consistency gap in a local cache is a real, structural property, not a bug to be fixed** — with N instances each running their own local cache, there are up to N different possible states for the "same" cached value at any given moment, and no built-in mechanism makes them agree.
4. **A common hybrid: a two-tier cache** — check the fast local cache first, fall back to the distributed cache on a local miss (which is itself faster than hitting the origin data store), and fall back to the origin only if both caches miss — combining local speed for hot keys with distributed consistency as the shared source of "recently cached" truth.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two service instances each have their own local cache, which can disagree; both connect to one shared distributed cache, which they always see consistently">
  <rect x="20" y="20" width="180" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance A</text>
  <text x="110" y="62" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">local cache: price=$10</text>

  <rect x="460" y="20" width="180" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance B</text>
  <text x="550" y="62" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">local cache: price=$12 (STALE!)</text>

  <rect x="230" y="130" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="155" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">distributed cache</text>
  <text x="330" y="173" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">price=$10 (ONE shared truth)</text>

  <line x1="140" y1="90" x2="280" y2="130" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="520" y1="90" x2="380" y2="130" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Local caches per instance can silently disagree; a shared distributed cache gives every instance the same view.

## 5. Runnable example

Scenario: two service instances with independent local caches versus a shared distributed cache. We start with a basic local cache demonstrating fast, isolated access, extend it to two instances' local caches diverging after a price update, then handle the hard case: a two-tier cache that checks local first and falls back to the shared distributed cache, correctly resolving the divergence a pure-local approach would leave unfixed.

### Level 1 — Basic

```java
// File: LocalCacheBasic.java -- models ONE instance's LOCAL cache: a
// plain in-process map, fast, but entirely PRIVATE to this instance.
import java.util.*;

public class LocalCacheBasic {
    static Map<String, Double> localCache = new HashMap<>();

    static double getPrice(String sku) {
        if (localCache.containsKey(sku)) {
            System.out.println("[local cache] HIT for " + sku + " -- instant, in-memory");
            return localCache.get(sku);
        }
        System.out.println("[local cache] MISS -- fetching from origin, then caching locally");
        double price = 10.00; // simulated origin fetch
        localCache.put(sku, price);
        return price;
    }

    public static void main(String[] args) {
        System.out.println("price: " + getPrice("sku-123"));
        System.out.println("price: " + getPrice("sku-123"));
    }
}
```

How to run: `java LocalCacheBasic.java`

`localCache` is a plain, in-process `HashMap` — the second call to `getPrice` hits it directly, with no network involvement at all, demonstrating the raw speed advantage local caching offers within a single instance.

### Level 2 — Intermediate

```java
// File: LocalCacheDivergence.java -- the SAME local cache pattern, now
// modeling TWO SEPARATE instances, each with their OWN local cache --
// demonstrating the REAL structural problem: a price update on one
// instance's cache does NOT propagate to the other's.
import java.util.*;

public class LocalCacheDivergence {
    static class ServiceInstance {
        String name;
        Map<String, Double> localCache = new HashMap<>();
        ServiceInstance(String name) { this.name = name; }

        double getPrice(String sku, double originValueIfMiss) {
            return localCache.computeIfAbsent(sku, k -> {
                System.out.println("[" + name + "] local cache MISS for " + sku + " -- fetching from origin");
                return originValueIfMiss;
            });
        }

        void updateLocalCacheOnly(String sku, double newPrice) {
            localCache.put(sku, newPrice);
            System.out.println("[" + name + "] local cache updated to $" + newPrice + " -- OTHER instances are unaware");
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        instanceA.getPrice("sku-123", 10.00);
        instanceB.getPrice("sku-123", 10.00);

        System.out.println();
        System.out.println("[event] a price update is applied, but ONLY instance-A's local cache is updated (simulating a partial update)");
        instanceA.updateLocalCacheOnly("sku-123", 12.00);

        System.out.println();
        System.out.println("[result] instance-A now shows: $" + instanceA.localCache.get("sku-123"));
        System.out.println("[result] instance-B STILL shows: $" + instanceB.localCache.get("sku-123") + " -- DIVERGED, and nothing in this design fixes that");
    }
}
```

How to run: `java LocalCacheDivergence.java`

`instanceA` and `instanceB` each hold their own entirely separate `localCache` map — `instanceA.updateLocalCacheOnly` mutates only `instanceA`'s own map, with no code path anywhere that would propagate that change to `instanceB`'s map. The two instances' caches genuinely and permanently diverge until something external (a TTL expiry, a restart) happens to reset one of them.

### Level 3 — Advanced

```java
// File: TwoTierCacheResolution.java -- the SAME two-instance scenario,
// now handling the PRODUCTION-FLAVORED hard case CORRECTLY: a TWO-TIER
// cache where each instance checks its OWN local cache first (fast), but
// falls back to a SHARED distributed cache (consistent) on a local miss
// or after local expiry -- resolving the divergence Level 2 demonstrated,
// without giving up local caching's speed advantage entirely.
import java.util.*;

public class TwoTierCacheResolution {
    // The ONE shared distributed cache both instances connect to.
    static Map<String, Double> distributedCache = new HashMap<>(Map.of("sku-123", 10.00));

    static class ServiceInstance {
        String name;
        Map<String, Double> localCache = new HashMap<>(); // instance's own fast tier
        ServiceInstance(String name) { this.name = name; }

        double getPrice(String sku) {
            if (localCache.containsKey(sku)) {
                System.out.println("[" + name + "] LOCAL cache HIT (fast)");
                return localCache.get(sku);
            }
            System.out.println("[" + name + "] local miss -- checking DISTRIBUTED cache (shared, consistent)");
            double fromDistributed = distributedCache.get(sku);
            localCache.put(sku, fromDistributed); // populate the LOCAL tier from the shared source
            return fromDistributed;
        }

        // A write invalidates BOTH this instance's local entry AND the shared distributed cache.
        void updatePrice(String sku, double newPrice) {
            distributedCache.put(sku, newPrice); // update the SHARED source of truth
            localCache.remove(sku); // invalidate THIS instance's own stale local copy
            System.out.println("[" + name + "] updated distributed cache to $" + newPrice + " and invalidated its OWN local entry");
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        instanceA.getPrice("sku-123");
        instanceB.getPrice("sku-123");

        System.out.println();
        System.out.println("[event] instance-A updates the price");
        instanceA.updatePrice("sku-123", 12.00);

        System.out.println();
        System.out.println("--- instance-A reads again: local was invalidated, falls through to distributed, sees the NEW price ---");
        System.out.println("[result] instance-A price: $" + instanceA.getPrice("sku-123"));

        System.out.println();
        System.out.println("--- instance-B reads again: its OWN local cache still holds the OLD value, from BEFORE the update ---");
        System.out.println("[result] instance-B price: $" + instanceB.getPrice("sku-123") + " -- still stale, because B's local entry was never invalidated");
    }
}
```

How to run: `java TwoTierCacheResolution.java`

`updatePrice` updates `distributedCache` (the shared source) and removes the *calling instance's own* `localCache` entry — but it has no way to reach into `instanceB`'s separate `localCache` map to invalidate it too. `instanceA`'s subsequent `getPrice` call correctly falls through to the now-updated distributed cache, since its local entry was removed. `instanceB`'s `getPrice` call still hits its own, never-invalidated local entry, returning the stale value — demonstrating honestly that a two-tier cache resolves *distributed*-level consistency but still requires an explicit cross-instance invalidation mechanism (like a pub/sub invalidation message) to fully resolve local-tier staleness across every instance.

## 6. Walkthrough

Trace `TwoTierCacheResolution.main` in order. **First**, both `instanceA.getPrice("sku-123")` and `instanceB.getPrice("sku-123")` run while both local caches are empty — each independently misses locally, reads `$10.00` from the shared `distributedCache`, and populates their own separate local cache with that same value.

**Next**, `instanceA.updatePrice("sku-123", 12.00)` runs: `distributedCache.put("sku-123", 12.00)` updates the one shared source of truth, and `localCache.remove("sku-123")` removes the entry from `instanceA`'s own local map specifically — `instanceB`'s local map is entirely untouched by this call, since `updatePrice` has no reference to it at all.

**Then**, `instanceA.getPrice("sku-123")` runs again. Since its local entry was just removed, `localCache.containsKey("sku-123")` is now `false` — it falls through to check `distributedCache`, which correctly returns the updated `$12.00`, and that value is used to repopulate `instanceA`'s local cache.

**After that**, `instanceB.getPrice("sku-123")` runs again. `instanceB`'s local cache still contains its original entry from the very first call — `localCache.containsKey("sku-123")` is `true`, so the local-hit branch runs, returning `$10.00` directly, without ever consulting `distributedCache` at all.

**Finally**, the printed results show `instanceA` correctly reporting the new price while `instanceB` still reports the old one — an honest demonstration that a two-tier local-plus-distributed cache solves the *distributed-cache-level* consistency problem completely, but genuinely requires an additional mechanism (invalidation events broadcast to every instance) to fully eliminate local-tier staleness across a fleet.

```
[instance-A] local miss -- checking DISTRIBUTED cache (shared, consistent)
[instance-B] local miss -- checking DISTRIBUTED cache (shared, consistent)

[event] instance-A updates the price
[instance-A] updated distributed cache to $12.0 and invalidated its OWN local entry

--- instance-A reads again: local was invalidated, falls through to distributed, sees the NEW price ---
[instance-A] local miss -- checking DISTRIBUTED cache (shared, consistent)
[result] instance-A price: $12.0

--- instance-B reads again: its OWN local cache still holds the OLD value, from BEFORE the update ---
[instance-B] LOCAL cache HIT (fast)
[result] instance-B price: $10.0 -- still stale, because B's local entry was never invalidated
```

## 7. Gotchas & takeaways

> A two-tier cache resolves the origin-vs-cache staleness problem for the *distributed* tier, but doesn't automatically make every instance's *local* tier agree — as Level 3 shows honestly, `instanceB` remains stale until something explicitly invalidates its local entry too. A complete solution typically needs a pub/sub invalidation broadcast (every instance subscribes to a "this key changed" channel and proactively clears its own local entry) on top of the two-tier read path shown here.
- Choose local caching for data where brief, per-instance inconsistency genuinely doesn't matter — configuration that changes rarely, computed values that are cheap to slightly duplicate work on — and distributed caching (or a two-tier approach with real invalidation) for anything where instances disagreeing would cause visible, confusing bugs.
- A short local-cache TTL is a simpler, if less precise, alternative to explicit cross-instance invalidation — accepting that staleness will self-resolve within, say, 10 seconds, rather than architecting a full invalidation broadcast mechanism.
- This decision connects directly to [cache invalidation](0503-cache-invalidation.md) strategy more broadly — the local-vs-distributed choice determines *where* invalidation needs to happen and how many places need to agree when a value changes.
- Measure the actual network latency cost of a distributed cache against your specific latency budget before assuming local caching is unnecessary complexity to avoid — for many services, a few milliseconds of distributed-cache latency is entirely acceptable in exchange for consistency, and premature optimization toward local-only caching can introduce exactly the divergence bugs shown here.
