---
card: microservices
gi: 503
slug: cache-invalidation
title: "Cache invalidation"
---

## 1. What it is

**Cache invalidation** is the process of removing or updating a cached value once the underlying source data has changed, so the cache stops serving stale, incorrect data. The three primary mechanisms are **TTL (time-to-live) expiry** (entries automatically expire after a set duration, regardless of whether the data actually changed), **explicit invalidation** (the writer that changes the data proactively removes or updates the corresponding cache entry), and **event-based invalidation** (a change event is published, and every cache — potentially across multiple instances — subscribes and invalidates itself in response).

## 2. Why & when

You need a deliberate invalidation strategy for any cache, because a cache with no invalidation mechanism at all is really just a way to serve permanently, increasingly wrong data:

- **TTL expiry is simple and requires no coordination, but trades staleness for that simplicity.** An entry with a 60-second TTL can be up to 60 seconds stale at any given moment — acceptable for data where brief staleness genuinely doesn't matter, unacceptable for data where staleness causes real, visible problems.
- **Explicit invalidation eliminates staleness for changes made through the known write path**, but only covers writes the invalidation logic actually knows about — a database updated directly, bypassing the application's normal write path, wouldn't trigger this invalidation at all, leaving the cache stale despite the explicit mechanism being in place.
- **Event-based invalidation is what's needed once multiple cache instances (or a mix of local and distributed caches) all need to agree that a value has changed** — a single instance's explicit invalidation only clears *that instance's* cache; an event broadcast to every instance is what closes the gap [local caches](0502-local-vs-distributed-cache.md) leave open.
- **You choose the mechanism (or combine several) based on how much staleness is actually tolerable for that specific piece of data** — this is a per-data-type decision, not a single blanket policy that has to apply identically to every cached value in a system.

## 3. Core concept

Think of a "best by" date stamped on packaged food (TTL expiry — automatic, no active decision needed, but imprecise about exactly when the food actually goes bad) versus a store actively pulling a specific product off shelves the moment a recall is announced (explicit invalidation — precise and immediate, but only works if the store actually hears about the recall) versus a company-wide alert system that notifies every single store location simultaneously the instant a recall happens (event-based invalidation — precise and reaches every location, but requires that alert infrastructure to exist and work reliably).

Concretely:

1. **TTL expiry**: every cache entry is stored with an expiration time; on read, if the current time is past that expiration, the entry is treated as a miss and refreshed from the source — no active invalidation logic needed anywhere, staleness is simply bounded by the TTL duration.
2. **Explicit invalidation**: the code path that writes new data also explicitly removes (or updates) the corresponding cache entry as part of that same write operation — precise, but only as complete as the invalidation logic's coverage of every actual write path.
3. **Event-based invalidation**: a write publishes a "this key changed" event to a shared channel; every cache instance subscribed to that channel reacts by invalidating its own copy of the affected key — this is what makes invalidation work correctly across multiple instances or cache tiers, not just within a single process.
4. **These mechanisms compose**: a TTL as a safety net catches any staleness that slips past explicit or event-based invalidation (from a write path nobody accounted for), while explicit or event-based invalidation handles the common case with much lower latency than waiting out a full TTL window.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three invalidation mechanisms: TTL expiry happens automatically over time, explicit invalidation happens at the write site, and event-based invalidation broadcasts to every cache instance">
  <rect x="20" y="20" width="190" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">TTL expiry</text>
  <text x="115" y="65" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">automatic, bounded staleness</text>

  <rect x="235" y="20" width="190" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">explicit invalidation</text>
  <text x="330" y="65" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">precise, but only ONE instance</text>

  <rect x="450" y="20" width="190" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">event-based invalidation</text>
  <text x="545" y="65" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">broadcasts to EVERY instance</text>

  <text x="330" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">TTL as a safety net; explicit or event-based invalidation for lower staleness on known write paths</text>
</svg>

Three complementary mechanisms — automatic expiry, precise single-instance invalidation, and multi-instance broadcast invalidation.

## 5. Runnable example

Scenario: a cache using each mechanism in turn. We start with basic TTL expiry, extend it to explicit invalidation at the write site, then handle the hard case: event-based invalidation across multiple instances, where a write on one instance must correctly invalidate every other instance's cache too, not just its own.

### Level 1 — Basic

```java
// File: TtlExpiryBasic.java -- models TTL-based cache expiry: entries
// AUTOMATICALLY become stale after a fixed duration, with NO active
// invalidation logic anywhere.
import java.util.*;

public class TtlExpiryBasic {
    record CacheEntry(double value, long expiresAtMs) {}
    static Map<String, CacheEntry> cache = new HashMap<>();
    static long ttlMs = 100;

    static double getPrice(String sku) {
        CacheEntry entry = cache.get(sku);
        long now = System.currentTimeMillis();
        if (entry != null && now < entry.expiresAtMs()) {
            System.out.println("[ttl cache] HIT, not yet expired");
            return entry.value();
        }
        System.out.println("[ttl cache] MISS or EXPIRED -- refreshing from origin");
        double fresh = 10.00;
        cache.put(sku, new CacheEntry(fresh, now + ttlMs));
        return fresh;
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("price: " + getPrice("sku-123"));
        System.out.println("price (immediately after): " + getPrice("sku-123"));
        Thread.sleep(150); // longer than the 100ms TTL
        System.out.println("price (after TTL expired): " + getPrice("sku-123"));
    }
}
```

How to run: `java TtlExpiryBasic.java`

`CacheEntry` stores its own `expiresAtMs`, and `getPrice` compares it against the current time on every read — no code anywhere explicitly clears this entry; it simply becomes ineligible to be treated as a hit once enough time has passed, which is TTL expiry's defining, entirely automatic mechanism.

### Level 2 — Intermediate

```java
// File: ExplicitInvalidationBasic.java -- the SAME cache, now with
// EXPLICIT invalidation: the WRITE path directly removes the stale entry,
// making the new value visible IMMEDIATELY, without waiting for any TTL.
import java.util.*;

public class ExplicitInvalidationBasic {
    static Map<String, Double> cache = new HashMap<>();
    static Map<String, Double> store = new HashMap<>(Map.of("sku-123", 10.00));

    static double getPrice(String sku) {
        if (cache.containsKey(sku)) {
            System.out.println("[cache] HIT");
            return cache.get(sku);
        }
        System.out.println("[cache] MISS -- reading from store");
        double value = store.get(sku);
        cache.put(sku, value);
        return value;
    }

    static void updatePrice(String sku, double newPrice) {
        store.put(sku, newPrice);
        cache.remove(sku); // EXPLICIT invalidation, right at the write site
        System.out.println("[write] updated store to $" + newPrice + " and EXPLICITLY invalidated the cache entry");
    }

    public static void main(String[] args) {
        System.out.println("price: " + getPrice("sku-123"));
        updatePrice("sku-123", 12.00);
        System.out.println("price (immediately after update, no TTL wait needed): " + getPrice("sku-123"));
    }
}
```

How to run: `java ExplicitInvalidationBasic.java`

`updatePrice` calls `cache.remove(sku)` as an explicit step, right alongside the actual store write — the very next `getPrice` call finds no cached entry at all (since it was just removed), correctly falls through to read the freshly-updated `store`, and repopulates the cache — all with zero delay, unlike TTL expiry's inherent wait window.

### Level 3 — Advanced

```java
// File: EventBasedInvalidationMultiInstance.java -- the SAME explicit
// invalidation idea, now handling the PRODUCTION-FLAVORED hard case:
// MULTIPLE instances, each with their OWN local cache. A write on ONE
// instance must invalidate EVERY instance's local cache, not just its
// own -- achieved by PUBLISHING an invalidation EVENT that every instance
// SUBSCRIBES to and reacts to independently.
import java.util.*;

public class EventBasedInvalidationMultiInstance {
    // A simple simulated pub/sub bus every instance subscribes to.
    static List<ServiceInstance> subscribedInstances = new ArrayList<>();

    static void publishInvalidationEvent(String sku) {
        System.out.println("[event bus] broadcasting invalidation event for '" + sku + "' to " + subscribedInstances.size() + " subscribed instance(s)");
        for (ServiceInstance instance : subscribedInstances) {
            instance.onInvalidationEvent(sku);
        }
    }

    static class ServiceInstance {
        String name;
        Map<String, Double> localCache = new HashMap<>();

        ServiceInstance(String name) {
            this.name = name;
            subscribedInstances.add(this); // subscribes itself to the event bus on creation
        }

        double getPrice(String sku, double originValue) {
            return localCache.computeIfAbsent(sku, k -> {
                System.out.println("[" + name + "] local MISS -- caching $" + originValue);
                return originValue;
            });
        }

        void updatePrice(String sku, double newPrice) {
            System.out.println("[" + name + "] performing write, new price $" + newPrice);
            publishInvalidationEvent(sku); // notify EVERY instance, not just this one
        }

        // Reacts to an invalidation event by clearing ITS OWN local entry.
        void onInvalidationEvent(String sku) {
            if (localCache.remove(sku) != null) {
                System.out.println("[" + name + "] received invalidation event -- cleared its own stale local entry for '" + sku + "'");
            }
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");
        ServiceInstance instanceC = new ServiceInstance("instance-C");

        instanceA.getPrice("sku-123", 10.00);
        instanceB.getPrice("sku-123", 10.00);
        instanceC.getPrice("sku-123", 10.00);

        System.out.println();
        System.out.println("[event] instance-A performs a price update");
        instanceA.updatePrice("sku-123", 12.00);

        System.out.println();
        System.out.println("[result] instance-A local cache: " + instanceA.localCache.containsKey("sku-123") + " (invalidated too, via its own broadcast)");
        System.out.println("[result] instance-B local cache: " + instanceB.localCache.containsKey("sku-123") + " (invalidated via the event)");
        System.out.println("[result] instance-C local cache: " + instanceC.localCache.containsKey("sku-123") + " (invalidated via the event)");
    }
}
```

How to run: `java EventBasedInvalidationMultiInstance.java`

Every `ServiceInstance` adds itself to the shared `subscribedInstances` list on construction. `updatePrice` doesn't clear the calling instance's own cache directly — it calls `publishInvalidationEvent`, which loops over *every* subscribed instance and calls `onInvalidationEvent` on each one, including the instance that originated the write. Since `onInvalidationEvent` removes the key from whichever instance's `localCache` it's called on, all three instances — `A`, `B`, and `C` — end up with their local entry cleared, not just the one that performed the update.

## 6. Walkthrough

Trace `EventBasedInvalidationMultiInstance.main` in order. **First**, all three instances are constructed, each adding itself to `subscribedInstances` — by the time construction finishes, the shared list contains all three. Then each instance's `getPrice` call independently populates its own separate `localCache` with `$10.00`.

**Next**, `instanceA.updatePrice("sku-123", 12.00)` runs. It prints its own write confirmation, then calls `publishInvalidationEvent("sku-123")` — critically, it does *not* directly call `instanceA.localCache.remove(...)` anywhere in `updatePrice`'s own code.

**Then**, inside `publishInvalidationEvent`, the loop iterates `subscribedInstances`, which contains `instanceA`, `instanceB`, and `instanceC` in that order. For each one, `onInvalidationEvent("sku-123")` is called — including on `instanceA` itself, since it's a member of the same subscribed list as everyone else, with no special-casing to skip the originator.

**After that**, each `onInvalidationEvent` call independently checks `localCache.remove(sku) != null` — for all three instances, the key was present (each had cached it from the earlier reads), so each removal succeeds and each instance prints its own confirmation of clearing its own stale entry.

**Finally**, `main`'s result-printing section checks `containsKey("sku-123")` on all three instances' local caches, and all three report `false` — every instance's local cache was correctly invalidated by the single broadcast event, not just the instance that happened to perform the write, closing exactly the gap that a purely local, per-instance explicit invalidation (as in Level 2, applied naively across multiple instances) would have left open.

```
[instance-A] local MISS -- caching $10.0
[instance-B] local MISS -- caching $10.0
[instance-C] local MISS -- caching $10.0

[event] instance-A performs a price update
[instance-A] performing write, new price $12.0
[event bus] broadcasting invalidation event for 'sku-123' to 3 subscribed instance(s)
[instance-A] received invalidation event -- cleared its own stale local entry for 'sku-123'
[instance-B] received invalidation event -- cleared its own stale local entry for 'sku-123'
[instance-C] received invalidation event -- cleared its own stale local entry for 'sku-123'

[result] instance-A local cache: false (invalidated too, via its own broadcast)
[result] instance-B local cache: false (invalidated via the event)
[result] instance-C local cache: false (invalidated via the event)
```

## 7. Gotchas & takeaways

> Explicit invalidation that only clears the *writing* instance's own local cache — a common oversight when a single-instance pattern is naively scaled to multiple instances — leaves every other instance stale indefinitely, or until their own TTL happens to expire. Event-based invalidation, broadcasting to every subscribed instance including the writer itself, is what actually closes this gap.
- TTL expiry remains valuable even alongside explicit or event-based invalidation, as a safety net catching staleness from any write path that bypassed the invalidation logic entirely (a direct database change, a batch job, a bug in the invalidation code itself).
- A real event bus for this purpose (Redis pub/sub, a message broker) needs its own reliability considerations — a dropped invalidation event means an instance never learns to invalidate its stale entry, so combining event-based invalidation with a TTL safety net is a common, prudent belt-and-suspenders approach.
- This is the concrete mechanism that resolves the divergence shown in [local vs distributed cache](0502-local-vs-distributed-cache.md) — a distributed cache naturally has only one copy to invalidate, but a fleet of local caches genuinely needs a broadcast mechanism like this to stay in sync.
- Match your invalidation approach's precision to the actual cost of staleness for that specific data — not every cached value needs sub-second invalidation precision, and building event-based invalidation for data where a 30-second TTL would have been entirely sufficient is often unnecessary complexity.
