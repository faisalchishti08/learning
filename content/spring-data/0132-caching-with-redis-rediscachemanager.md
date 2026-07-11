---
card: spring-data
gi: 132
slug: caching-with-redis-rediscachemanager
title: "Caching with Redis (RedisCacheManager)"
---

## 1. What it is

`RedisCacheManager` plugs Redis into Spring's cache abstraction (`@Cacheable`, `@CacheEvict`, `@CachePut`), so a method can be cached simply by annotating it — Spring generates the cache key, checks Redis before running the method body, and stores the result after, all without any direct `RedisTemplate` calls in your business logic.

```java
@Service
class OrderService {
    @Cacheable(value = "orders", key = "#orderId")
    Order findOrder(String orderId) {
        return expensiveDatabaseLookup(orderId); // only runs on a cache MISS
    }
}
```

## 2. Why & when

Earlier cards in this section used `RedisTemplate`/`opsForValue()` directly to build a cache-check-then-compute pattern by hand (as the runnable-example card for `RedisTemplate` did). `RedisCacheManager` removes that boilerplate entirely: Spring's `@Cacheable` annotation handles the check-then-compute-then-store logic generically, for *any* method, backed by whichever `CacheManager` is configured — Redis being one option among several (Caffeine, EhCache, a simple in-memory map).

Reach for `@Cacheable` + `RedisCacheManager` when:

- You want to cache the result of a method — especially an expensive database call or external API call — without writing manual `get`-check-`compute`-`set` logic at every call site, as the earlier `RedisTemplate` card had to.
- You want caching to be shared across multiple application instances (a distributed cache) rather than local to one JVM — Redis being externally reachable is exactly what makes this work, unlike a purely in-process cache.
- You want per-cache configuration (a different TTL, a different serializer) for different logical caches within the same application — `RedisCacheManager` supports this via named cache configurations.

## 3. Core concept

```
 @Cacheable(value = "orders", key = "#orderId")
 Order findOrder(String orderId) { ... }

 findOrder("1") called:
   1. compute cache key: "orders::1"   (cache name + generated/SpEL key)
   2. GET orders::1 from Redis
   3a. HIT  -> deserialize and return immediately, method body NEVER RUNS
   3b. MISS -> run the method body, SET orders::1 = result in Redis, then return it
```

The annotation intercepts the method call entirely — on a cache hit, the actual method body doesn't execute at all, which is the whole point: skipping the expensive work.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A call to a cacheable method either returns a cached Redis value directly or runs the method and stores the result">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findOrder("1")</text>

  <rect x="250" y="20" width="140" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GET orders::1</text>

  <line x1="200" y1="42" x2="245" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="440" y="20" width="170" height="40" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="525" y="44" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">HIT -&gt; return cached value</text>
  <line x1="390" y1="35" x2="435" y2="35" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="440" y="100" width="170" height="55" rx="6" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="525" y="122" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">MISS -&gt; run method,</text>
  <text x="525" y="136" fill="#f85149" font-size="9.5" text-anchor="middle" font-family="sans-serif">SET orders::1 = result</text>
  <line x1="390" y1="55" x2="435" y2="115" stroke="#f85149" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A cache hit short-circuits the method entirely; only a miss ever runs the real work.

## 5. Runnable example

The scenario: caching an expensive order lookup, evolving from a basic `@Cacheable`-style interceptor around a method call, to `@CacheEvict` invalidating a stale entry on update, to per-cache TTL configuration matching `RedisCacheManager`'s named cache configurations.

### Level 1 — Basic

Model the core `@Cacheable` behavior: a proxy checks the cache before running the real method.

```java
import java.util.*;
import java.util.function.*;

public class CachingLevel1 {
    static int realCallCount = 0;
    static String expensiveOrderLookup(String orderId) {
        realCallCount++;
        return "Order[" + orderId + "]-loaded-from-db-call#" + realCallCount;
    }

    public static void main(String[] args) {
        RedisCache cache = new RedisCache();

        // Mirrors @Cacheable(value = "orders", key = "#orderId") wrapping findOrder(orderId).
        Function<String, String> cachedFindOrder = orderId ->
            cache.getOrCompute("orders::" + orderId, () -> expensiveOrderLookup(orderId));

        System.out.println(cachedFindOrder.apply("1")); // MISS -- runs the real method
        System.out.println(cachedFindOrder.apply("1")); // HIT  -- method body never runs again
        System.out.println("Real method actually ran " + realCallCount + " time(s).");
    }
}

class RedisCache {
    private final Map<String, String> store = new HashMap<>();

    String getOrCompute(String key, Supplier<String> ifMissing) {
        if (store.containsKey(key)) {
            System.out.println("  [cache HIT for " + key + "]");
            return store.get(key);
        }
        System.out.println("  [cache MISS for " + key + " -- running the real method]");
        String result = ifMissing.get(); // the ACTUAL @Cacheable-annotated method body
        store.put(key, result);
        return result;
    }
}
```

How to run: `java CachingLevel1.java`

`getOrCompute` mirrors exactly what a `@Cacheable`-generated proxy does: check Redis first, and only call `ifMissing` (standing in for the real, annotated method body) on a miss. The second call to `cachedFindOrder.apply("1")` hits the cache and returns instantly — `realCallCount` stays at `1` even though the method was "called" twice, proving the expensive logic only actually ran once.

### Level 2 — Intermediate

Add `@CacheEvict`-style invalidation: updating an order must remove its stale cache entry, so the next read recomputes fresh data instead of serving outdated cached results.

```java
import java.util.*;
import java.util.function.*;

public class CachingLevel2 {
    static Map<String, String> database = new HashMap<>(Map.of("1", "PENDING"));
    static int realCallCount = 0;

    static String loadOrderStatus(String orderId) { realCallCount++; return database.get(orderId); }

    public static void main(String[] args) {
        RedisCache cache = new RedisCache();

        Function<String, String> cachedFindStatus = orderId -> cache.getOrCompute("orders::" + orderId, () -> loadOrderStatus(orderId));
        Consumer<String> updateAndEvict = orderId -> {
            database.put(orderId, "SHIPPED"); // the actual update
            cache.evict("orders::" + orderId); // @CacheEvict(value = "orders", key = "#orderId") -- clears the STALE entry
            System.out.println("  [evicted orders::" + orderId + " after update]");
        };

        System.out.println("First read:  " + cachedFindStatus.apply("1")); // MISS, caches "PENDING"
        System.out.println("Second read: " + cachedFindStatus.apply("1")); // HIT, still "PENDING" from cache

        updateAndEvict.accept("1"); // status changes AND the stale cache entry is cleared

        System.out.println("Read after update: " + cachedFindStatus.apply("1")); // MISS again -- fresh value loaded
        System.out.println("Real method ran " + realCallCount + " time(s) total.");
    }
}

class RedisCache {
    private final Map<String, String> store = new HashMap<>();
    String getOrCompute(String key, Supplier<String> ifMissing) {
        if (store.containsKey(key)) { System.out.println("  [cache HIT for " + key + "]"); return store.get(key); }
        System.out.println("  [cache MISS for " + key + "]");
        String result = ifMissing.get();
        store.put(key, result);
        return result;
    }
    void evict(String key) { store.remove(key); }
}
```

How to run: `java CachingLevel2.java`

`updateAndEvict` mirrors a `@CacheEvict(value = "orders", key = "#orderId")`-annotated method: it performs the real update *and* removes the now-stale cache entry in the same operation. Without the `evict` call, the third read would incorrectly return the cached `"PENDING"` forever, even after the underlying data changed to `"SHIPPED"` — eviction is what keeps a cache from silently serving outdated data after a write.

### Level 3 — Advanced

Give different named caches different TTLs, matching `RedisCacheManager`'s per-cache configuration (`RedisCacheConfiguration.defaultCacheConfig().entryTtl(...)` per cache name) — a short-lived cache for volatile data, a longer-lived one for stable data.

```java
import java.util.*;
import java.util.function.*;

public class CachingLevel3 {
    static int ordersCallCount = 0, productsCallCount = 0;
    static String loadOrder(String id) { ordersCallCount++; return "Order-" + id + "-v" + ordersCallCount; }
    static String loadProduct(String id) { productsCallCount++; return "Product-" + id + "-v" + productsCallCount; }

    public static void main(String[] args) {
        CacheManager cacheManager = new CacheManager();
        cacheManager.registerCache("orders", 60);     // volatile data -- short TTL, 60s
        cacheManager.registerCache("products", 3600);  // stable data -- long TTL, 3600s

        long t = 0;
        System.out.println(cacheManager.getOrCompute("orders", "1", t, () -> loadOrder("1")));   // MISS
        System.out.println(cacheManager.getOrCompute("products", "1", t, () -> loadProduct("1"))); // MISS

        t = 100; // 100 seconds later
        System.out.println("--- at t=100s ---");
        System.out.println(cacheManager.getOrCompute("orders", "1", t, () -> loadOrder("1")));   // MISS -- orders TTL (60s) expired
        System.out.println(cacheManager.getOrCompute("products", "1", t, () -> loadProduct("1"))); // HIT  -- products TTL (3600s) still valid
    }
}

class CacheEntry { String value; long expiresAt; CacheEntry(String value, long expiresAt) { this.value = value; this.expiresAt = expiresAt; } }

class CacheManager {
    private final Map<String, Long> ttlByCacheName = new HashMap<>(); // per-cache TTL, mirrors RedisCacheConfiguration per name
    private final Map<String, CacheEntry> store = new HashMap<>();

    void registerCache(String cacheName, long ttlSeconds) { ttlByCacheName.put(cacheName, ttlSeconds); }

    String getOrCompute(String cacheName, String key, long nowSeconds, Supplier<String> ifMissing) {
        String fullKey = cacheName + "::" + key;
        CacheEntry entry = store.get(fullKey);
        if (entry != null && nowSeconds < entry.expiresAt) {
            System.out.println("  [" + cacheName + " HIT for " + key + "]");
            return entry.value;
        }
        System.out.println("  [" + cacheName + " MISS for " + key + "]");
        String result = ifMissing.get();
        long ttl = ttlByCacheName.get(cacheName);
        store.put(fullKey, new CacheEntry(result, nowSeconds + ttl));
        return result;
    }
}
```

How to run: `java CachingLevel3.java`

`orders` is registered with a 60-second TTL, `products` with a 3600-second TTL — mirroring how `RedisCacheManager` can be built with different `RedisCacheConfiguration`s per named cache. At `t=0`, both caches miss and populate. At `t=100`, the `orders` entry's TTL (expiring at `t=60`) has already passed, so it misses again and recomputes; the `products` entry's TTL (expiring at `t=3600`) hasn't, so it still hits — one Redis-backed cache manager serving two logical caches with entirely different freshness requirements.

## 6. Walkthrough

Execution starts in `main` for Level 3. `cacheManager.registerCache("orders", 60)` and `registerCache("products", 3600)` populate `ttlByCacheName` with `{"orders": 60, "products": 3600}`.

At `t=0`, `cacheManager.getOrCompute("orders", "1", 0, () -> loadOrder("1"))` looks up `"orders::1"` in `store` — nothing is there, so it's a miss. `loadOrder("1")` runs, incrementing `ordersCallCount` to `1` and returning `"Order-1-v1"`. This gets stored with `expiresAt = 0 + 60 = 60`. The equivalent call for `"products::1"` stores its result with `expiresAt = 0 + 3600 = 3600`.

At `t=100`, `cacheManager.getOrCompute("orders", "1", 100, ...)` finds the existing entry for `"orders::1"`, but checks `100 < entry.expiresAt (60)` — this is `false`, so the entry is treated as expired: it's a miss, `loadOrder("1")` runs again (incrementing `ordersCallCount` to `2`, producing `"Order-1-v2"`), and a fresh entry is stored with a new `expiresAt = 100 + 60 = 160`. The equivalent call for `"products::1"` checks `100 < 3600` — `true` — so it hits and returns the original `"Product-1-v1"` without recomputing.

```
  [orders MISS for 1]
Order-1-v1
  [products MISS for 1]
Product-1-v1
--- at t=100s ---
  [orders MISS for 1]
Order-1-v2
  [products HIT for 1]
Product-1-v1
```

In real Spring Data Redis, this is configured with `RedisCacheManager.builder(connectionFactory).withCacheConfiguration("orders", RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofSeconds(60))).withCacheConfiguration("products", RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofHours(1))).build()` — each named cache gets its own TTL (and can even get its own serializer), and every `@Cacheable(value = "orders", ...)` or `@Cacheable(value = "products", ...)`-annotated method automatically uses the matching configuration, with zero cache-specific logic in the annotated methods themselves.

## 7. Gotchas & takeaways

> Gotcha: `@Cacheable`'s default key generation uses all method parameters combined — for a method with multiple parameters, this can produce a key that's more specific than intended, or two logically-equivalent calls (same data, different parameter order in a varargs call, for instance) that don't share a cache entry. Use an explicit `key = "#orderId"` (SpEL) whenever the default key generator's behavior isn't obviously correct for your method's signature.

> Gotcha: `@Cacheable` caches the return value unconditionally by default, including `null` — a method that legitimately returns `null` for "not found" will cache that `null`, and (depending on `RedisCacheManager` configuration) every subsequent call may skip re-checking the source entirely; use `unless`/`condition` on the annotation, or `cacheNullValues(false)` on the cache configuration, to avoid caching absence indefinitely.

- `RedisCacheManager` plugs Redis into Spring's generic `@Cacheable`/`@CacheEvict`/`@CachePut` caching abstraction — no manual `RedisTemplate` calls needed in cached methods.
- On a cache hit, the annotated method's body never executes at all — that's the entire performance benefit.
- `@CacheEvict` must accompany any write path that changes the underlying data, or the cache will keep serving stale values indefinitely.
- Different named caches can have independently configured TTLs (and serializers) via `RedisCacheManager.builder().withCacheConfiguration(name, config)`, matching each cache's own freshness requirements.
