---
card: microservices
gi: 530
slug: spring-cache-abstraction-cacheable-cacheevict
title: "Spring Cache abstraction (@Cacheable, @CacheEvict)"
---

## 1. What it is

**Spring's Cache abstraction** is a set of annotations — `@Cacheable`, `@CacheEvict`, `@CachePut`, `@Caching` — that let a method's return value be transparently cached and reused, without the method's own code containing any caching logic at all. `@Cacheable` on a method means "check the cache first; if present, return the cached value and skip the method body entirely; if absent, run the method, cache its result, then return it." `@CacheEvict` removes an entry (typically after a write invalidates it). The actual cache storage (in-memory, Redis, Caffeine, Hazelcast) is a pluggable backend behind this same annotation-driven interface, so switching cache providers doesn't require touching the annotated business code at all.

## 2. Why & when

You reach for the Cache abstraction whenever a method is expensive (a slow query, a costly computation, a remote call) and frequently called with the same arguments, because caching it directly in business logic is repetitive and easy to get subtly wrong:

- **Caching logic is boilerplate that has nothing to do with business logic** — "check cache, call method if miss, store result" is the same shape regardless of what the method actually does, and hand-writing it in every method that needs caching duplicates that shape everywhere and couples business logic to a specific cache implementation.
- **The abstraction separates "what to cache" (expressed declaratively via annotations) from "how caching actually works" (the pluggable `CacheManager` backend)** — a method annotated `@Cacheable("orders")` doesn't know or care whether "orders" is backed by an in-memory `ConcurrentHashMap`, Caffeine, or Redis; that's a configuration decision made elsewhere.
- **`@CacheEvict` keeps the cache from serving stale data after a write** — an update or delete operation that changes underlying data can be annotated to evict the corresponding cache entry (or clear the whole cache) at the same time, so subsequent reads correctly miss the stale cache and repopulate with fresh data.
- **You reach for this whenever repeated calls with the same key would return the same result** and the cost of recomputing or refetching that result is meaningfully higher than the cost of a cache lookup — a database query behind a `getById` method is the textbook case; a method whose result changes on every call (like a random number generator, or a live "current time" lookup) is the wrong candidate, since caching it would return stale or meaningless data.

## 3. Core concept

Think of a librarian who, instead of walking to the archive room for every single request for a popular book, keeps recently-requested books on a nearby shelf and checks that shelf first. If the book's there, it's handed over immediately; if not, the librarian fetches it from the archive, hands it over, *and* puts a copy on the nearby shelf for next time. If the archive later gets an updated edition of that book, the librarian removes the outdated copy from the nearby shelf (eviction) so the next request for it correctly goes back to the archive and picks up the new edition, rather than handing out the stale one indefinitely. The librarian's actual expertise (finding books) isn't duplicated by this process — the shelf-checking behavior is a separate, addable layer in front of it.

Concretely:

1. **`@Cacheable(cacheNames = "orders", key = "#orderId")`** on a method means: before running the method, look up `orderId` in the `"orders"` cache; if found, return the cached value and skip the method body; if not found, run the method, store its return value under that key, then return it.
2. **`@CacheEvict(cacheNames = "orders", key = "#orderId")`** on a different method (typically one that updates or deletes the underlying data) removes that key's entry from the `"orders"` cache, so a subsequent `@Cacheable` call for the same key correctly misses and refetches fresh data instead of returning stale results.
3. **`@CachePut(cacheNames = "orders", key = "#order.id")`** always runs the method (unlike `@Cacheable`, it never skips execution) but updates the cache with the fresh return value afterward — useful for a "save" operation that should both persist and refresh the cache in one step.
4. **The `key` expression (written in Spring Expression Language, SpEL)** determines cache granularity — `#orderId` caches per distinct order ID; omitting a key and caching a method with no arguments effectively caches one shared value for all callers.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cacheable checks the cache first and only runs the method on a miss; CacheEvict removes a stale entry so the next Cacheable call correctly misses and refetches">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Cacheable flow</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">call getOrder("42")</text>
  <rect x="20" y="75" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">cache HIT -&gt; return cached, skip method</text>
  <rect x="20" y="115" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">cache MISS -&gt; run method, store, return</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">@CacheEvict flow</text>
  <rect x="380" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">call updateOrder("42", ...)</text>
  <rect x="380" y="75" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="510" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">evict key "42" from cache</text>
  <rect x="380" y="115" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">next getOrder("42") correctly misses, refetches</text>
</svg>

Cacheable serves repeat calls from the cache; CacheEvict on writes ensures the next read after a change correctly misses and picks up fresh data.

## 5. Runnable example

Scenario: caching an expensive order lookup. We start with a plain Java model of the cache-check-then-call pattern, then show the real `@Cacheable`/`@CacheEvict` annotated Spring service, then handle the hard case: keying the cache per-argument and evicting correctly on update so stale reads never happen.

### Level 1 — Basic

```java
// File: ManualCachingConcept.java -- models the CORE idea @Cacheable
// automates: check a cache map first, only call the expensive method
// on a miss, and store the result for next time.
import java.util.*;

public class ManualCachingConcept {
    static Map<String, String> cache = new HashMap<>();
    static int expensiveCallCount = 0;

    static String expensiveGetOrder(String orderId) {
        expensiveCallCount++;
        System.out.println("[expensive call] fetching order " + orderId + " (call #" + expensiveCallCount + ")");
        return "{\"orderId\":\"" + orderId + "\"}";
    }

    // this IS the boilerplate @Cacheable eliminates
    static String getOrderCached(String orderId) {
        if (cache.containsKey(orderId)) {
            System.out.println("[cache hit] " + orderId);
            return cache.get(orderId);
        }
        String result = expensiveGetOrder(orderId);
        cache.put(orderId, result);
        return result;
    }

    public static void main(String[] args) {
        getOrderCached("42"); // miss -- calls the expensive method
        getOrderCached("42"); // hit -- skips the expensive method entirely
        getOrderCached("42"); // hit again
        System.out.println("Expensive method was actually called " + expensiveCallCount + " time(s) for 3 requests.");
    }
}
```

How to run: `java ManualCachingConcept.java`

`getOrderCached` implements, by hand, exactly the pattern `@Cacheable` automates: check the cache, return on hit, call-and-store on miss. The output shows `expensiveGetOrder` only actually runs once, even though `getOrderCached("42")` is called three times — the second and third calls are served entirely from `cache`.

### Level 2 — Intermediate

```java
// File: CacheableRealShape.java -- the REAL Spring shape: @Cacheable
// on a service method, with the cache lookup handled entirely by Spring's
// proxy-based AOP, not by any code inside the method itself.
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

public class CacheableRealShape {

    @Service
    static class OrderService {

        @Cacheable(cacheNames = "orders", key = "#orderId")
        public String getOrder(String orderId) {
            // this method body ONLY runs on a cache miss -- Spring's proxy intercepts the call
            System.out.println("[expensive call] fetching order " + orderId + " from the database");
            return "{\"orderId\":\"" + orderId + "\"}";
        }
    }
}
```

How to run: requires `spring-boot-starter-cache` on the classpath and `@EnableCaching` on a `@Configuration` class in a Spring Boot application context; run via `mvn spring-boot:run` and call `getOrder("42")` twice through an injected `OrderService` bean to see the "fetching order" log line print only once.

Spring wraps `OrderService` in a proxy at startup because of `@Cacheable`; every call to `getOrder` first goes through that proxy, which checks the `"orders"` cache using the key `#orderId` (a SpEL expression referring to the method's `orderId` parameter) before ever invoking the real method body — the method itself contains zero caching code, exactly matching the separation of concerns the Level 1 example modeled by hand.

### Level 3 — Advanced

```java
// File: CacheEvictOnUpdate.java -- adds @CacheEvict on the UPDATE path,
// so a write correctly invalidates the cached read, preventing STALE
// reads after an order's data actually changes.
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

public class CacheEvictOnUpdate {

    @Service
    static class OrderService {

        @Cacheable(cacheNames = "orders", key = "#orderId")
        public String getOrder(String orderId) {
            System.out.println("[expensive call] fetching order " + orderId + " from the database");
            return "{\"orderId\":\"" + orderId + "\",\"status\":\"SUBMITTED\"}";
        }

        // evicts the SAME key the read path caches under, so the next
        // getOrder(orderId) call correctly misses and refetches the new status
        @CacheEvict(cacheNames = "orders", key = "#orderId")
        public void updateOrderStatus(String orderId, String newStatus) {
            System.out.println("[write] updating order " + orderId + " to status " + newStatus + " in the database");
        }
    }

    // Illustrative call sequence (as it would run against a real Spring context):
    // 1. getOrder("42")          -> MISS, fetches and caches "SUBMITTED"
    // 2. getOrder("42")          -> HIT, returns cached "SUBMITTED", no DB call
    // 3. updateOrderStatus("42", "SHIPPED") -> evicts "orders"::42 from the cache
    // 4. getOrder("42")          -> MISS again (evicted), fetches fresh "SHIPPED" from the database
}
```

How to run: requires `spring-boot-starter-cache`, `@EnableCaching`, and a `CacheManager` bean configured in a Spring Boot application; run the illustrated call sequence against an injected `OrderService` bean and observe the "fetching order" log line print exactly at steps 1 and 4, never at step 2, confirming the cache correctly serves the hit at step 2 and correctly misses again at step 4 after the eviction.

`key = "#orderId"` is identical on both `@Cacheable` and `@CacheEvict` — this is essential: evicting the wrong key (or forgetting to evict at all) would leave the cache serving stale data indefinitely after a write. Because both annotations reference the exact same SpEL key expression, `updateOrderStatus("42", ...)` evicts precisely the entry `getOrder("42")` would otherwise keep serving, guaranteeing the next read reflects the write.

## 6. Walkthrough

Trace the illustrative call sequence from Level 3 end to end:

1. **`getOrder("42")` is called for the first time.** Spring's caching proxy checks the `"orders"` cache for key `"42"` — it's empty, a miss — so the proxy invokes the real method body, which prints `[expensive call] fetching order 42...` and returns `{"orderId":"42","status":"SUBMITTED"}`. The proxy stores this return value under key `"42"` in the `"orders"` cache before handing it back to the caller.
2. **`getOrder("42")` is called a second time.** The proxy checks the `"orders"` cache for key `"42"` again — this time it's present (from step 1) — so the proxy returns the cached value directly, *without ever invoking the real method body*. No "fetching order" log line prints this time.
3. **`updateOrderStatus("42", "SHIPPED")` is called.** Spring's proxy for this method, driven by `@CacheEvict(cacheNames = "orders", key = "#orderId")`, first lets the real method body run (printing `[write] updating order 42...`), then removes the entry under key `"42"` from the `"orders"` cache — the cache no longer has any entry for `"42"` at all.
4. **`getOrder("42")` is called a third time.** The proxy checks the `"orders"` cache for key `"42"` — because step 3 evicted it, this is a miss again, so the real method body runs once more, prints `[expensive call] fetching order 42...`, and returns the now-current data reflecting the update (in a real database-backed implementation, this would return `status: SHIPPED` rather than the stale `SUBMITTED` a naive, never-evicted cache would have incorrectly kept serving).

The structural guarantee this depends on: the eviction's key expression (`#orderId` on `updateOrderStatus`) must resolve to the exact same cache key the read's key expression (`#orderId` on `getOrder`) would have used for the same order — if the two expressions could ever diverge (different parameter names, different derived key logic), the eviction could silently miss the entry it was meant to invalidate, and stale data would keep being served indefinitely.

## 7. Gotchas & takeaways

> **Gotcha:** `@Cacheable` and `@CacheEvict` on methods within the *same class* only work correctly when called from **outside** that class, through the Spring-managed proxy — calling `this.getOrder(...)` from another method inside the same bean bypasses the proxy entirely, silently skipping the caching logic altogether, since Spring's default proxy-based AOP only intercepts calls that go through the proxy, not direct internal method calls.

- `@Cacheable` skips the method body entirely on a cache hit; `@CachePut` always runs the method but refreshes the cache with the result — pick the one matching whether the method's execution is itself required (a write) or purely a lookup (a read).
- Always evict (or update) the corresponding cache entry when the underlying data changes — a `@Cacheable` read without a matching `@CacheEvict` (or `@CachePut`) on the write path serves stale data forever until the cache entry expires on its own, if it ever does.
- The `key` SpEL expression must produce identical values on both the caching side and the evicting side for the same logical entity, or eviction silently misses the entry it was meant to invalidate.
- The actual storage backend (in-memory map, Caffeine, Redis, Hazelcast) is a `CacheManager` configuration detail, entirely separate from the `@Cacheable`/`@CacheEvict` annotations on business methods — switching providers is a configuration change, not a code change to any annotated method.
