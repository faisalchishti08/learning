---
card: spring-boot
gi: 175
slug: supported-cache-providers-generic-jcache-hazelcast-infinispa
title: Supported cache providers (Generic, JCache, Hazelcast, Infinispan, Couchbase, Redis, Caffeine, Cache2k, Simple)
---

## 1. What it is

Spring Boot's caching abstraction supports **nine cache provider back-ends**. When `@EnableCaching` is active, Spring Boot auto-detects which provider to use based on classpath presence and a strict **priority order**. You declare caches and set TTLs against the provider's native API; Spring wraps it behind a uniform `CacheManager` interface so your `@Cacheable` annotations work identically regardless of the back-end.

## 2. Why & when

**Why so many providers:** different use cases have different needs — an in-process JVM cache (Caffeine) is fastest but dies with the JVM; a distributed cache (Redis, Hazelcast, Infinispan) survives restarts and scales horizontally; a standards-based layer (JCache/JSR-107) lets you swap providers without changing Spring config.

| Provider | Best for |
|---|---|
| **Caffeine** | High-performance in-process cache with eviction policies |
| **Redis** | Distributed cache shared across multiple JVM instances |
| **Hazelcast** | Distributed in-memory data grid with embedded or client mode |
| **Infinispan** | Distributed cache with transactional and persistence support |
| **Couchbase** | Document store doubling as distributed cache |
| **JCache (JSR-107)** | Vendor-neutral API; use any JSR-107-compliant implementation |
| **Cache2k** | High-performance in-process cache with Java-native design |
| **Generic** | Any `CacheManager` bean you declare manually |
| **Simple** | `ConcurrentHashMap` fallback for dev/test only |

## 3. Core concept

**Auto-detection priority** (highest to lowest):
1. Generic (a `CacheManager` bean is present)
2. JCache (a `javax.cache.CacheManager` bean or `cache.jcache.config` property)
3. Hazelcast
4. Infinispan
5. Couchbase
6. Redis
7. Caffeine
8. Cache2k
9. Simple (always available as fallback)

Force a provider by setting `spring.cache.type=<name>`.

**Configuration pattern** for each provider:
- **Caffeine:** `spring.cache.caffeine.spec=maximumSize=500,expireAfterWrite=10m` — spec string controls eviction.
- **Redis:** `spring.cache.redis.time-to-live=10m` — uses `RedisCacheManager`; Spring auto-configures if `spring-boot-starter-data-redis` is present.
- **Hazelcast:** provide a `hazelcast.yaml` or `HazelcastClientConfiguration` bean.
- **JCache:** `spring.cache.jcache.config=classpath:ehcache.xml` for Ehcache 3 as the JSR-107 provider.
- **Simple:** zero config — works out of the box, no eviction.

## 4. Diagram

<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring cache abstraction with CacheManager in the middle and nine provider options radiating outward">
  <!-- Central CacheManager -->
  <rect x="270" y="88" width="180" height="55" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="111" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">CacheManager</text>
  <text x="360" y="127" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Abstraction</text>

  <!-- Spoke labels - left side -->
  <line x1="270" y1="100" x2="200" y2="55" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="100" y="40" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="148" y="59" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Caffeine</text>

  <line x1="270" y1="110" x2="190" y2="110" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="90" y="97" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="138" y="116" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Redis</text>

  <line x1="270" y1="125" x2="200" y2="165" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="100" y="152" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="148" y="171" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Hazelcast</text>

  <line x1="310" y1="88" x2="285" y2="42" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="230" y="18" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="278" y="37" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Infinispan</text>

  <line x1="360" y1="88" x2="360" y2="38" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="313" y="18" width="94" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="360" y="37" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Couchbase</text>

  <line x1="405" y1="88" x2="435" y2="42" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="400" y="18" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="448" y="37" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JCache</text>

  <!-- Right side -->
  <line x1="450" y1="100" x2="525" y2="65" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="528" y="52" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="576" y="71" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Cache2k</text>

  <line x1="450" y1="115" x2="530" y2="115" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="533" y="102" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="581" y="121" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Generic</text>

  <line x1="450" y1="130" x2="525" y2="165" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="528" y="152" width="96" height="28" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="576" y="171" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Simple</text>

  <!-- Application above -->
  <rect x="295" y="185" width="130" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="207" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Cacheable</text>
  <line x1="360" y1="185" x2="360" y2="145" stroke="#6db33f" stroke-width="2" marker-end="url(#spa)"/>

  <defs>
    <marker id="spa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`@Cacheable` talks only to `CacheManager`; swapping the provider requires only a dependency change and properties.

## 5. Runnable example

```java
// CacheProviderDemo.java — compares all nine provider types by their characteristics
// How to run: java CacheProviderDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: add the matching dependency; Spring Boot auto-detects the provider

import java.util.*;

public class CacheProviderDemo {

    record Provider(String name, String springCacheType, String dependency,
                    boolean distributed, boolean persistent, boolean eviction, String configHint) {}

    public static void main(String[] args) {
        List<Provider> providers = List.of(
            new Provider("Generic",    "generic",    "any CacheManager @Bean",
                false, false, true,  "spring.cache.type=generic — use your own CacheManager bean"),
            new Provider("JCache",     "jcache",     "any JSR-107 impl (Ehcache 3, etc.)",
                false, false, true,  "spring.cache.jcache.config=classpath:ehcache.xml"),
            new Provider("Hazelcast",  "hazelcast",  "hazelcast-spring",
                true,  false, true,  "hazelcast.yaml or HazelcastClientConfiguration bean"),
            new Provider("Infinispan", "infinispan",  "infinispan-spring-boot-starter-embedded",
                true,  true,  true,  "infinispan.xml or programmatic ConfigurationBuilder"),
            new Provider("Couchbase",  "couchbase",  "spring-boot-starter-data-couchbase",
                true,  true,  true,  "spring.couchbase.* properties"),
            new Provider("Redis",      "redis",      "spring-boot-starter-data-redis",
                true,  false, true,  "spring.cache.redis.time-to-live=10m"),
            new Provider("Caffeine",   "caffeine",   "caffeine",
                false, false, true,  "spring.cache.caffeine.spec=maximumSize=500,expireAfterWrite=5m"),
            new Provider("Cache2k",    "cache2k",    "cache2k-spring",
                false, false, true,  "Cache2kBuilderCustomizer bean for TTL/max-size"),
            new Provider("Simple",     "simple",     "(built-in fallback)",
                false, false, false, "No config needed — ConcurrentHashMap, no eviction")
        );

        System.out.println("=== Spring Boot Supported Cache Providers ===\n");
        System.out.printf("%-12s %-11s %-11s %-9s %s%n",
                "Provider", "Distributed", "Persistent", "Eviction", "spring.cache.type");
        System.out.println("-".repeat(72));
        providers.forEach(p ->
            System.out.printf("%-12s %-11s %-11s %-9s %s%n",
                    p.name(),
                    p.distributed()  ? "yes" : "no",
                    p.persistent()   ? "yes" : "no",
                    p.eviction()     ? "yes" : "NO (!)  ",
                    p.springCacheType()));

        System.out.println("\n=== Auto-detection priority (first wins) ===");
        providers.forEach(p ->
            System.out.printf("  spring.cache.type=%-12s  dependency: %s%n",
                    p.springCacheType(), p.dependency()));

        System.out.println("\n=== Config hints ===");
        providers.forEach(p ->
            System.out.printf("  %-12s  %s%n", p.name(), p.configHint()));

        System.out.println("\nRecommendation: Caffeine for single-node; Redis for multi-instance.");
    }
}
```

**How to run:** `java CacheProviderDemo.java` — prints a comparison table of all nine providers.

## 6. Walkthrough

- The `Provider` record models the key differentiators: `distributed` (survives across JVM instances), `persistent` (survives restart), `eviction` (TTL / max-size policies).
- **Simple** has `eviction=false` — the only provider with no built-in eviction. This is a production footgun: the cache grows without bound.
- **Caffeine** and **Cache2k** are in-process but have rich eviction (LRU, LFU, TTL, max-size) — ideal for single-node applications.
- **Redis**, **Hazelcast**, and **Infinispan** are distributed — entries survive a single JVM restart and are shared across scaled-out instances.
- **JCache (JSR-107)** is the standards layer — you can back it with Ehcache 3, Hazelcast, or Infinispan without changing Spring code.
- The `springCacheType` column maps directly to `spring.cache.type=<value>` in `application.properties`.

## 7. Gotchas & takeaways

> If **both Caffeine and Redis** are on the classpath, Spring Boot picks Caffeine (it's higher in priority). Set `spring.cache.type=redis` explicitly when you need the distributed back-end.

> `Simple` (the default fallback) has **no eviction** — every cached value lives forever until the JVM restarts. Never use it in production for data that changes.

- `spring.cache.cache-names=products,users` pre-creates named caches at startup (required for Caffeine/Simple before they can be used).
- Caffeine spec: `maximumSize=10000,expireAfterWrite=5m,recordStats` — `recordStats` enables `/actuator/metrics/cache.*`.
- Redis TTL: `spring.cache.redis.time-to-live=PT10M` (ISO-8601 duration) applies globally; per-cache TTL requires a `RedisCacheManagerBuilderCustomizer` bean.
- Hazelcast embedded vs client mode: embedded is simpler but keeps data in the application process; client mode connects to a standalone Hazelcast cluster.
- Infinispan's strength is **transactional caching** and **persistence to a store** (JDBC, RocksDB) — useful when cache entries must survive cluster restarts.
