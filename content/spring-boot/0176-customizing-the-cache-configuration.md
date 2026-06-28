---
card: spring-boot
gi: 176
slug: customizing-the-cache-configuration
title: Customizing the cache configuration
---

## 1. What it is

Spring Boot's caching auto-configuration provides working defaults, but real applications need per-cache TTLs, max sizes, serialisation control, and metrics. **Customizing cache configuration** means going beyond `spring.cache.*` properties by declaring `*CacheManagerBuilderCustomizer` beans, `CacheManagerCustomizer<T>` beans, or replacing the auto-configured `CacheManager` entirely with your own `@Bean` — without disabling the rest of the auto-configuration.

## 2. Why & when

**Default cache config is often wrong for production:**
- All caches share one TTL — a user-profile cache (10 min) and a config-lookup cache (1 h) should not expire at the same rate.
- Default serialisation is Java serialisation — incompatible across JVM versions, bloated, not human-readable.
- No max-size means unbounded growth.

**When to customise:**
- Different caches in the same application need different TTLs or max-sizes.
- You need JSON serialisation in Redis so other languages can read cache entries.
- You want statistics exposed via Actuator (`recordStats` in Caffeine, `enableStatistics` in JCache).
- You need to hook into cache events (creation, eviction, expiry).

## 3. Core concept

Three customisation layers, from least to most invasive:

**Layer 1 — Properties:** `spring.cache.caffeine.spec`, `spring.cache.redis.time-to-live`. One value applies to all caches.

**Layer 2 — Customizer beans:** Spring Boot's auto-config calls customizer beans *after* building its default manager, letting you tweak it without replacing it.
- Caffeine: `CaffeineCacheManager` → inject `CacheManagerCustomizer<CaffeineCacheManager>`.
- Redis: `RedisCacheManager.RedisCacheManagerBuilder` → declare `RedisCacheManagerBuilderCustomizer`.

**Layer 3 — Own `@Bean`:** declare a `CacheManager` bean. Spring Boot backs off from its auto-configuration. Full control, full responsibility.

For **per-cache configuration** in Redis, `RedisCacheManagerBuilderCustomizer` lets you set `RedisCacheConfiguration` per cache name:
```java
builder.withCacheConfiguration("products",
    RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofMinutes(10)));
```

For **Caffeine**, declare a `CaffeineCacheManager` bean with individual `Caffeine` spec per cache:
```java
manager.registerCustomCache("products",
    Caffeine.newBuilder().maximumSize(500).expireAfterWrite(10, MINUTES).build());
```

## 4. Diagram

<svg viewBox="0 0 720 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three layers of cache customisation: properties at top, customizer beans in middle, own CacheManager bean at bottom">
  <!-- Layer 1 -->
  <rect x="20" y="15" width="680" height="44" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="360" y="33" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Layer 1 — Properties (one value, all caches)</text>
  <text x="360" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spring.cache.caffeine.spec=maximumSize=500,expireAfterWrite=5m  |  spring.cache.redis.time-to-live=10m</text>

  <!-- Arrow down -->
  <line x1="360" y1="62" x2="360" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cca)"/>

  <!-- Layer 2 -->
  <rect x="20" y="82" width="680" height="58" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="101" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Layer 2 — Customizer Beans (per-cache config, keep auto-config)</text>
  <text x="200" y="120" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">CacheManagerCustomizer&lt;CaffeineCacheManager&gt;</text>
  <text x="200" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">registerCustomCache("products", spec)</text>
  <text x="520" y="120" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">RedisCacheManagerBuilderCustomizer</text>
  <text x="520" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">withCacheConfiguration("products", ttl=10m)</text>

  <!-- Arrow down -->
  <line x1="360" y1="143" x2="360" y2="158" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cca)"/>

  <!-- Layer 3 -->
  <rect x="20" y="162" width="680" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="181" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Layer 3 — Own @Bean CacheManager (full control; auto-config backs off)</text>
  <text x="360" y="197" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Bean CacheManager cacheManager() { return new CaffeineCacheManager(); }</text>

  <defs>
    <marker id="cca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Prefer the lowest invasive layer that meets your needs; reach for Layer 3 only when the customizer API is insufficient.

## 5. Runnable example

```java
// CacheCustomizationDemo.java — demonstrates per-cache config, serialisation choice, and stats
// How to run: java CacheCustomizationDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: declare RedisCacheManagerBuilderCustomizer or CaffeineCacheManager @Bean

import java.time.Duration;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class CacheCustomizationDemo {

    // Simulated per-cache configuration (mirrors RedisCacheConfiguration per cache)
    record CacheConfig(String name, Duration ttl, int maxSize, boolean jsonSerialization) {}

    // Simulated cache store with config applied
    static class ConfiguredCache {
        final CacheConfig config;
        final Map<Object, CacheEntry> store = new ConcurrentHashMap<>();
        int hits, misses;

        record CacheEntry(Object value, long expiresAt) {}

        ConfiguredCache(CacheConfig config) { this.config = config; }

        Object get(Object key) {
            CacheEntry e = store.get(key);
            if (e != null && System.currentTimeMillis() < e.expiresAt()) {
                hits++;
                System.out.printf("  [HIT]  cache='%s' key=%s ttl-remaining=%dms%n",
                        config.name(), key,
                        e.expiresAt() - System.currentTimeMillis());
                return e.value();
            }
            if (e != null) store.remove(key); // expired
            misses++;
            return null;
        }

        void put(Object key, Object value) {
            long expires = System.currentTimeMillis() + config.ttl().toMillis();
            if (store.size() >= config.maxSize()) {
                // Evict oldest entry (simplified)
                store.remove(store.keySet().iterator().next());
                System.out.printf("  [EVICT] cache='%s' exceeded maxSize=%d%n",
                        config.name(), config.maxSize());
            }
            store.put(key, new CacheEntry(
                config.jsonSerialization() ? "{\"value\":\"" + value + "\"}" : value, expires));
            System.out.printf("  [PUT]   cache='%s' key=%s serial=%s expires=%dms%n",
                    config.name(), key,
                    config.jsonSerialization() ? "JSON" : "native",
                    config.ttl().toMillis());
        }

        void printStats() {
            System.out.printf("  Stats[%s]: hits=%d misses=%d size=%d%n",
                    config.name(), hits, misses, store.size());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Cache Customization Demo ===\n");

        // --- RedisCacheManagerBuilderCustomizer equivalent: per-cache config ---
        Map<String, ConfiguredCache> manager = new LinkedHashMap<>();
        manager.put("products",      new ConfiguredCache(new CacheConfig("products",     Duration.ofSeconds(2), 1000, true)));
        manager.put("user-sessions", new ConfiguredCache(new CacheConfig("user-sessions",Duration.ofSeconds(1), 500,  false)));
        manager.put("config",        new ConfiguredCache(new CacheConfig("config",       Duration.ofSeconds(10),100,  true)));

        System.out.println("1. Per-cache TTL and serialisation:");
        manager.get("products").put("sku-42", "Widget");
        manager.get("user-sessions").put("sess-abc", "userId=7");
        manager.get("config").put("feature.enabled", "true");

        System.out.println("\n2. Cache hits (within TTL):");
        manager.get("products").get("sku-42");
        manager.get("config").get("feature.enabled");

        System.out.println("\n3. Max-size eviction:");
        ConfiguredCache small = new ConfiguredCache(new CacheConfig("small", Duration.ofSeconds(30), 2, false));
        small.put("k1", "v1");
        small.put("k2", "v2");
        small.put("k3", "v3"); // triggers eviction of k1

        System.out.println("\n4. TTL expiry:");
        Thread.sleep(1100); // user-sessions TTL = 1s
        Object expired = manager.get("user-sessions").get("sess-abc");
        System.out.println("  Result after TTL expiry: " + expired);

        System.out.println("\n5. Cache statistics (Caffeine recordStats / JCache enableStatistics):");
        manager.values().forEach(ConfiguredCache::printStats);
    }
}
```

**How to run:** `java CacheCustomizationDemo.java` — demonstrates per-cache TTL, max-size eviction, JSON serialisation flag, and statistics.

## 6. Walkthrough

- **`CacheConfig` per name** mirrors `RedisCacheManagerBuilderCustomizer`: in Spring Boot, you call `builder.withCacheConfiguration("products", RedisCacheConfiguration.defaultCacheConfig().entryTtl(Duration.ofSeconds(2)).serializeValuesWith(json))`.
- **`ConfiguredCache.put`** enforces `maxSize` with eviction — Caffeine does this automatically when you set `maximumSize(...)` in the spec.
- **JSON serialisation flag** (`jsonSerialization=true`) simulates `serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer()))` — making Redis cache entries human-readable and cross-language.
- **`Thread.sleep(1100)`** demonstrates TTL expiry — `user-sessions` TTL is 1 s, so the entry is gone. In Caffeine this is lazy expiry; in Redis it's server-side TTL.
- **Stats output** simulates Caffeine's `CacheStats` (hits, misses, eviction count) exposed via `CaffeineCache.getNativeCache().stats()` and Actuator at `/actuator/metrics/cache.gets`.

## 7. Gotchas & takeaways

> Declaring your **own `CacheManager` @Bean** disables **all** cache auto-configuration (factory, type detection, property binding). If you only need to tweak one setting, use the `*CacheManagerBuilderCustomizer` approach instead — it stays within auto-config.

> Redis cache entries serialised with **Java serialisation** (the default) **cannot be read by non-Java consumers** and break when class structure changes. Always configure `Jackson2JsonRedisSerializer` or `GenericJackson2JsonRedisSerializer` for Redis in production.

- `CaffeineCacheManager.setCacheSpecification(spec)` applies a global spec; `registerCustomCache(name, cache)` gives per-cache control.
- `RedisCacheManagerBuilderCustomizer` is a functional interface — a lambda works: `builder -> builder.withCacheConfiguration(...)`.
- Set `spring.cache.type=none` in tests to skip cache completely — `@MockBean CacheManager` still lets you verify interactions.
- `@Caching(evict = {@CacheEvict("products"), @CacheEvict("search")})` evicts from multiple caches in one method.
- Caffeine `recordStats()` must be in the spec string for `/actuator/metrics/cache.*` tags to appear.
