---
card: microservices
gi: 285
slug: result-caching-for-resiliency
title: "Result caching for resiliency"
---

## 1. What it is

Result caching for resiliency is the broader practice of caching the *results* of calls to a dependency — not only to use as a fallback during failures (see [cache as fallback](0284-cache-as-fallback-stale-data.md)), but proactively, on the normal success path, so that most requests never need to reach the fragile dependency at all. Fewer calls reaching a downstream dependency means fewer opportunities for that dependency's slowness or instability to affect the caller, and it means the dependency itself experiences less load, which can prevent it from becoming overloaded and failing in the first place.

## 2. Why & when

Every resilience pattern discussed so far — [circuit breaker](0250-circuit-breaker-pattern.md), [retry](0259-retry-pattern.md), [bulkhead](0267-bulkhead-pattern.md), [rate limiter](0273-rate-limiter-pattern.md), [timeout](0280-timeout-pattern-timelimiter.md) — reacts to a call that has already been made. Caching is different: it reduces how often the call needs to be made in the first place, attacking the problem upstream of all those other patterns. A request that's served entirely from cache cannot time out, cannot trip a circuit breaker, and cannot be rate-limited by the dependency, because it never touches the dependency at all.

This has a second, less obvious resiliency benefit beyond serving individual requests faster: it reduces aggregate load on the dependency, which directly helps that dependency stay healthy under traffic spikes — a caching layer in front of a database or downstream service effectively multiplies that dependency's practical capacity. Use result caching wherever data is read far more often than it changes (a very common pattern — product catalogs, configuration, reference data, computed aggregates) and a short period of staleness on reads is acceptable.

## 3. Core concept

A read-through cache checks the cache first; on a miss, it calls the underlying dependency, stores the result with a time-to-live (TTL), and returns it — subsequent reads within the TTL are served entirely from cache.

```java
class ReadThroughCache<K, V> {
    record Entry<V>(V value, long expiresAtMillis) {}
    final java.util.Map<K, Entry<V>> store = new java.util.concurrent.ConcurrentHashMap<>();
    final long ttlMillis;

    ReadThroughCache(long ttlMillis) { this.ttlMillis = ttlMillis; }

    V get(K key, java.util.function.Function<K, V> loader) {
        Entry<V> entry = store.get(key);
        if (entry != null && System.currentTimeMillis() < entry.expiresAtMillis()) {
            return entry.value(); // CACHE HIT -- dependency never called
        }
        V loaded = loader.apply(key); // CACHE MISS -- dependency called ONCE, result stored
        store.put(key, new Entry<>(loaded, System.currentTimeMillis() + ttlMillis));
        return loaded;
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Most requests hit the cache and are served without ever reaching the downstream dependency; only cache misses reach the dependency, which sees dramatically reduced load and is correspondingly less likely to become overloaded or unstable">
  <rect x="30" y="60" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="84" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">many requests</text>

  <line x1="150" y1="80" x2="260" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr285)"/>
  <text x="220" y="35" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">cache HIT (most)</text>
  <rect x="260" y="20" width="130" height="40" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="325" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">served from cache</text>

  <line x1="150" y1="85" x2="260" y2="120" stroke="#8b949e" marker-end="url(#arr285)"/>
  <text x="220" y="140" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">cache MISS (few)</text>
  <rect x="260" y="100" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="325" y="124" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">dependency call</text>

  <text x="500" y="124" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">dependency sees far less load overall</text>

  <defs><marker id="arr285" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Most traffic is absorbed by the cache; only a small fraction of requests ever put load on the actual dependency.

## 5. Runnable example

Scenario: repeated identical calls hitting a slow dependency directly on every request, extended to add a read-through cache with a TTL that dramatically cuts the number of dependency calls, and finally adding request coalescing so that concurrent cache misses for the same key trigger only one dependency call instead of one per concurrent caller — a common production refinement called the "thundering herd" fix.

### Level 1 — Basic

```java
// File: NoCachingHitsDependencyEveryTime.java -- every request calls
// the (simulated slow) dependency directly, even for the exact same key
// requested repeatedly within a short window.
public class NoCachingHitsDependencyEveryTime {
    static int callCount = 0;
    static String fetchProductName(String productId) {
        callCount++;
        return "Product-" + productId; // pretend this is an expensive/slow DB call
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            System.out.println("Request " + (i + 1) + ": " + fetchProductName("sku-123"));
        }
        System.out.println("Total dependency calls: " + callCount + " (for 5 identical requests)");
    }
}
```

How to run: `java NoCachingHitsDependencyEveryTime.java`

Five requests for the exact same product ID each call `fetchProductName` directly, so the dependency is hit five times for data that never changed between calls. Under real load — thousands of requests per second for popular, mostly-static data — this pattern needlessly multiplies load on the dependency by the request volume.

### Level 2 — Intermediate

```java
// File: ReadThroughCacheReducesLoad.java -- the same five requests now
// go through a read-through cache with a TTL; only the FIRST request for
// a given key reaches the dependency, the rest are served from cache.
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

public class ReadThroughCacheReducesLoad {
    static int callCount = 0;
    static String fetchProductName(String productId) {
        callCount++;
        return "Product-" + productId;
    }

    record Entry(String value, long expiresAtMillis) {}
    static final Map<String, Entry> cache = new ConcurrentHashMap<>();
    static final long ttlMillis = 5000;

    static String getWithCache(String productId) {
        Entry entry = cache.get(productId);
        if (entry != null && System.currentTimeMillis() < entry.expiresAtMillis()) {
            return entry.value(); // HIT
        }
        String loaded = fetchProductName(productId); // MISS
        cache.put(productId, new Entry(loaded, System.currentTimeMillis() + ttlMillis));
        return loaded;
    }

    public static void main(String[] args) {
        for (int i = 0; i < 5; i++) {
            System.out.println("Request " + (i + 1) + ": " + getWithCache("sku-123"));
        }
        System.out.println("Total dependency calls: " + callCount + " (for 5 identical requests, TTL=" + ttlMillis + "ms)");
    }
}
```

How to run: `java ReadThroughCacheReducesLoad.java`

The first request for `"sku-123"` misses the cache, calls `fetchProductName` (call count becomes 1), and stores the result with a 5-second expiry. The remaining four requests, arriving well within that 5-second window, find a valid cache entry and are served without ever calling `fetchProductName` again. The dependency call count stays at 1 instead of 5 — an 80% reduction in load for this small example, which scales proportionally with request volume in a real system.

### Level 3 — Advanced

```java
// File: CoalescingCacheAvoidsThunderingHerd.java -- CONCURRENT requests
// for the same uncached key would each independently see a cache miss
// and all call the dependency simultaneously (a "thundering herd").
// This version coalesces concurrent misses for the same key into a
// single in-flight dependency call that all callers share.
import java.util.Map;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class CoalescingCacheAvoidsThunderingHerd {
    static AtomicInteger callCount = new AtomicInteger(0);
    static String fetchProductName(String productId) throws InterruptedException {
        callCount.incrementAndGet();
        Thread.sleep(200); // simulate a slow dependency call
        return "Product-" + productId;
    }

    static final Map<String, CompletableFuture<String>> inFlight = new ConcurrentHashMap<>();

    static CompletableFuture<String> getCoalesced(String productId) {
        // computeIfAbsent is atomic: only the FIRST concurrent caller for a
        // given key actually starts the dependency call; everyone else gets
        // the SAME in-flight future and simply awaits its result.
        return inFlight.computeIfAbsent(productId, key -> CompletableFuture.supplyAsync(() -> {
            try { return fetchProductName(key); }
            catch (InterruptedException e) { throw new RuntimeException(e); }
        }).whenComplete((result, ex) -> inFlight.remove(productId))); // clear once done, so future requests refetch
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(10);
        CountDownLatch done = new CountDownLatch(10);
        // 10 CONCURRENT requests for the SAME key, simulating a burst against a cold cache.
        for (int i = 0; i < 10; i++) {
            pool.submit(() -> {
                try { getCoalesced("sku-123").get(); } catch (Exception ignored) {}
                done.countDown();
            });
        }
        done.await();
        pool.shutdown();
        System.out.println("Total dependency calls for 10 CONCURRENT identical requests: " + callCount.get());
    }
}
```

How to run: `java CoalescingCacheAvoidsThunderingHerd.java`

Ten threads simultaneously request the same product ID against a cold cache. Without coalescing, all ten would see a miss at roughly the same instant and all ten would call the slow dependency concurrently — a thundering herd that can itself overload the dependency, especially right after a cache-wide expiry or a cold start affecting a popular key. Here, `inFlight.computeIfAbsent` is atomic: only the very first caller to reach it actually creates and starts the `CompletableFuture` that calls `fetchProductName`; the other nine callers, arriving while that future is still in flight, get the *same* future object back and simply wait on it via `.get()`. The final printed call count is 1, not 10 — the dependency was protected from the burst entirely, and all ten callers still got the correct result.

## 6. Walkthrough

Trace `CoalescingCacheAvoidsThunderingHerd.main` in execution order. **First**, a 10-thread pool is created and 10 tasks are submitted almost simultaneously, each calling `getCoalesced("sku-123")` and blocking on `.get()`.

**The first task to actually execute `inFlight.computeIfAbsent("sku-123", ...)`** finds no existing entry for that key, so it runs the supplied lambda: it creates a `CompletableFuture` via `CompletableFuture.supplyAsync`, which schedules `fetchProductName("sku-123")` to run asynchronously (incrementing `callCount` to 1 and sleeping 200ms to simulate real work), and stores this future in the `inFlight` map under `"sku-123"`.

**The remaining nine tasks**, executing `computeIfAbsent` for the same key while that entry already exists (even though the underlying call hasn't finished yet — the map holds the *future*, not the result), simply receive the same already-present `CompletableFuture` object. `computeIfAbsent` guarantees this atomically: no two threads can both observe "key absent" and both proceed to create a new future for the same key.

**All ten tasks then call `.get()`** on what is, for nine of them, someone else's already-in-flight future. `.get()` blocks each calling thread until that future completes — since it's the same future object for all ten, they all unblock together once the single underlying `fetchProductName` call finishes after its 200ms sleep.

**Once the future completes**, its `whenComplete` callback removes the entry from `inFlight` — this is important: it means a *future* burst of requests for `"sku-123"` (after this one has resolved) will again see the key absent and trigger exactly one new dependency call, rather than the coalescing entry lingering forever and never refreshing.

**Final state**: `callCount` is 1, all ten tasks received the correct, identical result, and the dependency experienced exactly one 200ms call instead of ten concurrent ones — precisely the load-shielding this pattern is designed to provide.

```
10 threads call getCoalesced("sku-123") near-simultaneously
        |
        v
inFlight.computeIfAbsent("sku-123", ...)   <- ATOMIC: only ONE thread actually creates the future
        |
   thread #1 creates future -> calls fetchProductName() ONCE
   threads #2-10 -> receive the SAME future, just await it
        |
        v
future completes -> all 10 threads unblock with the SAME result -> entry removed from inFlight
```

## 7. Gotchas & takeaways

> Caching without coalescing does not fully protect a dependency during a burst — a cold cache (startup, expiry, or eviction) hit by many concurrent requests for the same key can still produce a thundering herd of simultaneous dependency calls even though every individual request "correctly" checked the cache first.

- Result caching is the only resilience pattern here that *reduces* load on a dependency rather than just reacting to failures of it — it's often the highest-leverage change for both latency and stability.
- Set the TTL based on how tolerable staleness is for that specific data and how much load reduction is needed — there is a direct tradeoff between freshness and dependency load.
- Request coalescing (sharing one in-flight call across many concurrent callers for the same key) specifically prevents cache-miss bursts from becoming dependency-overload events, which is especially important right after a deploy, a cache flush, or a TTL expiring on a very popular key.
- Combine result caching with [cache as fallback](0284-cache-as-fallback-stale-data.md): the same cache infrastructure that reduces normal-path load can also serve as the emergency fallback during an actual outage, by relaxing (or ignoring) the TTL check specifically on the failure path.
