---
card: spring-boot
gi: 174
slug: caching-auto-configuration
title: Caching auto-configuration
---

## 1. What it is

Spring Boot auto-configures its caching abstraction when you add `spring-boot-starter-cache`. Adding `@EnableCaching` to a configuration class activates the annotation-driven cache proxy. From then on, `@Cacheable`, `@CacheEvict`, and `@CachePut` on service methods transparently cache return values — no manual `CacheManager` setup needed if you're happy with the defaults.

Spring's caching abstraction is a unified API; the storage back-end (Caffeine, Redis, Hazelcast, …) is swapped by adding a different dependency.

## 2. Why & when

**Why cache:** a database or remote API call might take 50–500 ms. If the same data is requested thousands of times per minute and changes rarely, serving it from an in-memory map takes microseconds and eliminates load on the downstream system.

**When to use:**
- Read-heavy data that changes infrequently: product catalogues, configuration lookups, user profiles.
- Expensive computations (reports, aggregations) called with the same inputs repeatedly.
- External API calls where rate limits or latency make repeated calls unacceptable.

**When to avoid:**
- Data that must always be fresh (balances, inventory counts).
- Write-heavy paths — cache churn wastes memory.
- Anything transactional that needs consistency guarantees.

## 3. Core concept

Three core annotations:

- **`@Cacheable(value="products", key="#id")`**: on a method — return the cached value if present; otherwise execute the method and store the result. The `key` SpEL expression determines the cache key.
- **`@CacheEvict(value="products", key="#id")`**: invalidate a cache entry (or `allEntries=true` to flush the whole cache). Put on update/delete methods.
- **`@CachePut(value="products", key="#id")`**: always execute the method **and** update the cache. Useful for write-through: the DB and cache stay in sync.

Spring Boot auto-config picks a `CacheManager` based on what's on the classpath (priority order: Caffeine > Hazelcast > Infinispan > Couchbase > Redis > Cache2k > JCache > Simple). The `Simple` provider (a `ConcurrentHashMap`) is the fallback — good enough for dev/test, not for production.

Key property: `spring.cache.type=caffeine` forces a specific provider even if multiple are present.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@Cacheable: first call hits DB and populates cache; second call returns from cache without hitting DB">
  <!-- First call -->
  <text x="20" y="30" fill="#e6edf3" font-size="11" font-family="sans-serif" font-weight="bold">First call (cache miss)</text>

  <rect x="20" y="42" width="100" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>

  <line x1="123" y1="60" x2="178" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ca)"/>

  <rect x="183" y="42" width="110" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="238" y="60" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Cacheable</text>
  <text x="238" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">proxy: miss</text>

  <line x1="296" y1="60" x2="348" y2="60" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#cb)"/>

  <rect x="353" y="42" width="110" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="408" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DB / API</text>
  <text x="408" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">executes method</text>

  <line x1="353" y1="68" x2="297" y2="68" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cb)"/>
  <text x="325" y="82" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">stores in cache</text>

  <!-- Cache store -->
  <rect x="183" y="96" width="110" height="36" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="238" y="114" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Cache Store</text>
  <text x="238" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Caffeine / Redis</text>
  <line x1="238" y1="96" x2="238" y2="80" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>

  <!-- Second call -->
  <text x="20" y="155" fill="#e6edf3" font-size="11" font-family="sans-serif" font-weight="bold">Second call (cache hit)</text>

  <rect x="20" y="167" width="100" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="190" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>

  <line x1="123" y1="185" x2="178" y2="185" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ca)"/>

  <rect x="183" y="167" width="110" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="238" y="185" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Cacheable</text>
  <text x="238" y="197" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">proxy: hit → return</text>

  <!-- Arrow back to caller, no DB call -->
  <line x1="183" y1="185" x2="128" y2="185" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cb)"/>
  <text x="450" y="190" fill="#8b949e" font-size="10" font-family="sans-serif">DB never called on hit</text>

  <defs>
    <marker id="ca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="cb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

On a cache miss the method runs and the result is stored; subsequent hits bypass the method entirely.

## 5. Runnable example

```java
// CachingDemo.java — implements @Cacheable/@CacheEvict/@CachePut behaviour from scratch
// How to run: java CachingDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add spring-boot-starter-cache + @EnableCaching; annotations do this transparently

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class CachingDemo {

    // --- Simulated cache store (ConcurrentHashMap, like Spring's Simple provider) ---
    static final Map<String, Map<Object, Object>> caches = new ConcurrentHashMap<>();

    static <T> T cacheable(String cacheName, Object key, java.util.function.Supplier<T> loader) {
        Map<Object, Object> cache = caches.computeIfAbsent(cacheName, k -> new ConcurrentHashMap<>());
        if (cache.containsKey(key)) {
            System.out.printf("  [@Cacheable] HIT  cache='%s' key=%s%n", cacheName, key);
            @SuppressWarnings("unchecked") T val = (T) cache.get(key);
            return val;
        }
        System.out.printf("  [@Cacheable] MISS cache='%s' key=%s — executing method%n", cacheName, key);
        T result = loader.get();
        cache.put(key, result);
        return result;
    }

    static void cacheEvict(String cacheName, Object key) {
        Map<Object, Object> cache = caches.get(cacheName);
        if (cache != null) cache.remove(key);
        System.out.printf("  [@CacheEvict] evicted cache='%s' key=%s%n", cacheName, key);
    }

    static <T> T cachePut(String cacheName, Object key, java.util.function.Supplier<T> writer) {
        T result = writer.get(); // always execute
        caches.computeIfAbsent(cacheName, k -> new ConcurrentHashMap<>()).put(key, result);
        System.out.printf("  [@CachePut] updated cache='%s' key=%s value=%s%n", cacheName, key, result);
        return result;
    }

    // --- Service methods (Spring proxies would intercept these) ---

    // @Cacheable("products")
    static String findProduct(int id) {
        return cacheable("products", id, () -> {
            System.out.println("    [DB] SELECT * FROM products WHERE id=" + id);
            return "Product-" + id;
        });
    }

    // @CacheEvict(value="products", key="#id")
    static void deleteProduct(int id) {
        System.out.println("    [DB] DELETE FROM products WHERE id=" + id);
        cacheEvict("products", id);
    }

    // @CachePut(value="products", key="#id")
    static String updateProduct(int id, String name) {
        return cachePut("products", id, () -> {
            System.out.println("    [DB] UPDATE products SET name='" + name + "' WHERE id=" + id);
            return name;
        });
    }

    public static void main(String[] args) {
        System.out.println("=== Caching Auto-configuration Demo ===\n");

        System.out.println("1. First call (MISS — DB is hit):");
        System.out.println("   Result: " + findProduct(42));

        System.out.println("\n2. Second call (HIT — DB is NOT hit):");
        System.out.println("   Result: " + findProduct(42));

        System.out.println("\n3. Third call for different key (MISS):");
        System.out.println("   Result: " + findProduct(99));

        System.out.println("\n4. Update product (always executes, updates cache):");
        System.out.println("   Result: " + updateProduct(42, "Super Widget"));

        System.out.println("\n5. Fetch updated product (HIT — returns updated value):");
        System.out.println("   Result: " + findProduct(42));

        System.out.println("\n6. Evict then fetch (MISS again):");
        deleteProduct(42);
        System.out.println("   Result: " + findProduct(42));

        System.out.println("\nCache state: " + caches);
    }
}
```

**How to run:** `java CachingDemo.java`

## 6. Walkthrough

- **`cacheable`** checks the map first; on a miss it calls the supplier (simulating the proxied method), stores the result, and returns it. This is exactly what Spring's `CacheInterceptor` does.
- **`findProduct(42)` called twice**: first call prints MISS and hits "DB"; second call prints HIT — the database supplier is never invoked.
- **`cachePut`** always calls the supplier (so the DB write happens) and then updates the cache — keeping store and cache in sync without a subsequent read.
- **`cacheEvict`** removes the key. The next `findProduct(42)` is a MISS again, showing the invalidation worked.
- In real Spring Boot, replace `cacheable(...)` calls with `@Cacheable("products")` on the method — the proxy intercepts the call transparently.

## 7. Gotchas & takeaways

> `@Cacheable` is **proxy-based**: if a method calls another `@Cacheable` method **within the same class**, the proxy is bypassed and caching doesn't happen. Extract cached methods into a separate Spring bean.

> The default `Simple` cache manager (`ConcurrentHashMap`) has **no eviction** — entries accumulate forever. Switch to Caffeine for TTL/max-size policies in production.

- Add `spring-boot-starter-cache` and `@EnableCaching` — that's the minimum.
- `@Cacheable(value="products", key="#id", unless="#result == null")` skips caching null results.
- `spring.cache.type=none` disables caching globally without removing annotations — useful in tests.
- `@CacheConfig(cacheNames="products")` at the class level avoids repeating the cache name on every method.
- Monitor cache hit/miss ratios via Actuator: `/actuator/metrics/cache.gets` (with `outcome=hit/miss` tags).
