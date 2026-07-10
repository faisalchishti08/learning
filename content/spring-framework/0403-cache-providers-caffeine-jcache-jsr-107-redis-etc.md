---
card: spring-framework
gi: 403
slug: cache-providers-caffeine-jcache-jsr-107-redis-etc
title: "Cache providers (Caffeine, JCache/JSR-107, Redis, etc.)"
---

## 1. What it is

Cache providers are the actual storage engines that plug into Spring's `CacheManager` abstraction: **Caffeine** (a high-performance in-process Java cache), **JCache/JSR-107** (the standard Java caching API, implemented by providers like Ehcache or Hazelcast), and **Redis** (an external, distributed in-memory data store). Spring ships a dedicated `CacheManager` implementation for each, so the same `@Cacheable` code works against any of them just by swapping which `CacheManager` bean is configured.

```java
@Bean
CacheManager cacheManager(RedisConnectionFactory connectionFactory) {
    return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
                    .entryTtl(Duration.ofMinutes(10)))
            .build();
}
```

## 2. Why & when

The `CacheManager`/`Cache` interfaces (covered in the previous card) are deliberately storage-agnostic — but a real application still has to pick an actual technology to back them, and that choice has real consequences for consistency, scalability, and operational complexity.

- **Caffeine** — in-process, extremely fast (no network hop), but each application instance has its own independent cache. Right when cached data can tolerate being slightly different across instances, or when you're running a single instance, or when the cache exists purely to reduce load on a downstream system rather than to guarantee consistency.
- **JCache/JSR-107** — a vendor-neutral standard API; using it means you can switch underlying providers (Ehcache, Hazelcast) later with minimal code change, at the cost of some provider-specific features being harder to reach. Common in enterprises with existing Ehcache/Hazelcast infrastructure.
- **Redis** — an external, shared cache: every application instance sees the same cached values, cache survives individual instance restarts, and you can inspect/clear it independently of any one instance. Necessary once you're running more than one instance and need cache consistency across them, or want caching to survive a rolling deployment.

The decision usually comes down to: single instance or don't-care-about-cross-instance-consistency → Caffeine; existing enterprise caching infrastructure → JCache; horizontally scaled and need shared/consistent caching → Redis.

## 3. Core concept

```
                     @Cacheable("products")   <-- unchanged regardless of provider
                              |
                              v
                        CacheManager
                    /         |          \
           Caffeine      JCache/JSR-107    Redis
          (in-process,   (standard API,     (external,
           per-instance)  pluggable impl)    shared/distributed)
                |               |                  |
           JVM heap        Ehcache/Hazelcast    Redis server
                                                  (network hop)
```

Every provider satisfies the same `Cache` contract (`get`, `put`, `evict`, `clear`) — what differs is where the bytes actually live and whether that location is shared across process boundaries.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two application instances share one Redis cache versus each having its own separate Caffeine cache">
  <text x="160" y="24" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Caffeine (per-instance)</text>
  <rect x="30" y="40" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App instance A</text>
  <rect x="30" y="110" width="120" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">own cache</text>

  <rect x="200" y="40" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App instance B</text>
  <rect x="200" y="110" width="120" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="260" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">own cache (different!)</text>

  <text x="480" y="24" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Redis (shared)</text>
  <rect x="410" y="40" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App instance A</text>
  <rect x="550" y="40" width="70" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">B</text>
  <rect x="440" y="150" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="515" y="171" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">one shared cache</text>
  <line x1="470" y1="90" x2="500" y2="148" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="585" y1="90" x2="530" y2="148" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Caffeine gives every instance its own cold-started, independent cache; Redis gives every instance a view onto the same shared data.

## 5. Runnable example

### Level 1 — Basic

Configure Caffeine with a real eviction policy and observe entries being evicted once the size limit is exceeded — something the plain `ConcurrentMapCacheManager` from the previous card cannot do at all.

```java
import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.*;

public class ProvidersBasic {

    static class Service {
        @Cacheable("items")
        String load(int id) {
            System.out.println("Loading item " + id);
            return "item-" + id;
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        CacheManager cacheManager() {
            var manager = new CaffeineCacheManager("items");
            manager.setCaffeine(Caffeine.newBuilder().maximumSize(2)); // tiny, to force eviction
            return manager;
        }

        @Bean
        Service service() { return new Service(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        Service service = context.getBean(Service.class);

        service.load(1);
        service.load(2);
        service.load(3); // pushes the cache over maximumSize(2); Caffeine evicts an older entry

        System.out.println("Re-requesting item 1 (may have been evicted):");
        service.load(1); // could be a hit or a miss, depending on Caffeine's eviction choice

        context.close();
    }
}
```

How to run: add `com.github.ben-manes.caffeine:caffeine` and `spring-context-support` to the classpath, then `java ProvidersBasic.java`.

`Caffeine.newBuilder().maximumSize(2)` caps the cache at 2 entries; loading a third item forces Caffeine to evict one of the first two using its internal admission/eviction policy (a refined LRU variant). Re-requesting item 1 may print `"Loading item 1"` again if it was the one evicted — this size-bounded behavior is exactly what an unbounded `ConcurrentMapCacheManager` cannot provide.

### Level 2 — Intermediate

Configure `RedisCacheManager` against a real Redis connection and demonstrate the shared-cache property by using two separate `CacheManager`-backed service instances (simulating two application instances) that both read the same Redis-backed cache.

```java
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.*;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;

import java.time.Duration;

public class ProvidersIntermediate {

    static class Service {
        private final String label;
        Service(String label) { this.label = label; }

        @Cacheable(value = "items", cacheManager = "redisCacheManager")
        String load(int id) {
            System.out.println(label + " loading item " + id + " from the database");
            return "item-" + id;
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        LettuceConnectionFactory redisConnectionFactory() {
            return new LettuceConnectionFactory(new RedisStandaloneConfiguration("localhost", 6379));
        }

        @Bean
        CacheManager redisCacheManager(LettuceConnectionFactory connectionFactory) {
            return RedisCacheManager.builder(connectionFactory)
                    .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
                            .entryTtl(Duration.ofMinutes(5)))
                    .build();
        }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        CacheManager redisCacheManager = context.getBean(CacheManager.class);

        // Simulate two separate application instances, both pointed at the same Redis server.
        Service instanceA = new Service("instance-A");
        Service instanceB = new Service("instance-B");

        System.out.println(instanceA.load(1)); // instance A: miss, loads and caches in Redis
        System.out.println(instanceB.load(1)); // instance B: HIT — sees instance A's cached value!

        context.close();
    }
}
```

How to run: run a local Redis (`docker run -p 6379:6379 redis`), add `spring-data-redis` and `io.lettuce:lettuce-core` to the classpath, then `java ProvidersIntermediate.java`.

`@Cacheable`'s method interception applies per Spring-managed proxy, but since both `instanceA` and `instanceB` are just plain objects here calling into the same `redisCacheManager`-backed cache (via the annotation resolving to that shared `CacheManager` bean), `instanceB.load(1)` finds the entry `instanceA` already wrote to Redis — this is the defining property Caffeine cannot offer: genuinely shared state across independent instances.

### Level 3 — Advanced

Production Redis caching needs per-cache TTL overrides (not every cache should share the same expiration), a resilient fallback when Redis is temporarily unreachable, and explicit key/value serialization control so cached objects round-trip correctly across the network.

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.interceptor.CacheErrorHandler;
import org.springframework.context.annotation.*;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;

import java.time.Duration;
import java.util.Map;

public class ProvidersAdvanced {

    record Product(long id, String name) {}

    static class Service {
        @Cacheable("products")   // long TTL — product catalog changes rarely
        Product findProduct(long id) {
            System.out.println("Loading product " + id);
            return new Product(id, "Product #" + id);
        }

        @Cacheable("sessions")   // short TTL — session data goes stale fast
        String findSessionUser(String sessionId) {
            System.out.println("Loading session " + sessionId);
            return "user-" + sessionId;
        }
    }

    @Configuration
    @EnableCaching
    static class Config {
        @Bean
        LettuceConnectionFactory redisConnectionFactory() {
            return new LettuceConnectionFactory(new RedisStandaloneConfiguration("localhost", 6379));
        }

        @Bean
        CacheManager cacheManager(LettuceConnectionFactory connectionFactory) {
            var jsonSerializer = new GenericJackson2JsonRedisSerializer(new ObjectMapper());
            var defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
                    .entryTtl(Duration.ofMinutes(10))
                    .serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(jsonSerializer));

            // Per-cache TTL overrides: not every cache should expire at the same rate.
            Map<String, RedisCacheConfiguration> perCacheConfig = Map.of(
                    "products", defaultConfig.entryTtl(Duration.ofHours(6)),
                    "sessions", defaultConfig.entryTtl(Duration.ofMinutes(2))
            );

            return RedisCacheManager.builder(connectionFactory)
                    .cacheDefaults(defaultConfig)
                    .withInitialCacheConfigurations(perCacheConfig)
                    .build();
        }

        @Bean
        CacheErrorHandler cacheErrorHandler() {
            // Redis being briefly unreachable shouldn't break the request — log and fall through
            // to the (slower) underlying method instead of propagating a caching exception.
            return new org.springframework.cache.interceptor.SimpleCacheErrorHandler() {
                @Override
                public void handleCacheGetError(RuntimeException exception, org.springframework.cache.Cache cache, Object key) {
                    System.err.println("Cache unavailable, falling through: " + exception.getMessage());
                }
            };
        }

        @Bean
        Service service() { return new Service(); }
    }

    public static void main(String[] args) {
        var context = new AnnotationConfigApplicationContext(Config.class);
        Service service = context.getBean(Service.class);

        System.out.println(service.findProduct(1));       // 6-hour TTL cache
        System.out.println(service.findSessionUser("s1")); // 2-minute TTL cache

        context.close();
    }
}
```

How to run: run a local Redis instance, add `spring-data-redis`, `io.lettuce:lettuce-core`, and Jackson to the classpath, then `java ProvidersAdvanced.java`.

`withInitialCacheConfigurations(perCacheConfig)` gives `"products"` a 6-hour TTL and `"sessions"` a 2-minute TTL from the same `CacheManager`, reflecting how differently those two kinds of data actually go stale. `GenericJackson2JsonRedisSerializer` ensures cached Java objects serialize to JSON for storage in Redis and deserialize back correctly, instead of relying on Java's native (and less portable) serialization. The custom `CacheErrorHandler` prevents a transient Redis outage from turning into an application-level exception — a call falls through to the real method instead of failing outright.

## 6. Walkthrough

Trace `ProvidersAdvanced.main`'s first call, `service.findProduct(1)`:

1. **Cache manager resolves the cache.** `@Cacheable("products")` with no explicit `cacheManager` attribute uses the sole registered `CacheManager` bean, which is the `RedisCacheManager` configured with per-cache TTL overrides.
2. **Cache lookup by name.** The interceptor asks for the `"products"` `Cache`; because `"products"` was pre-configured in `perCacheConfig` with a 6-hour TTL, that specific configuration (not the 10-minute default) applies to this cache.
3. **Redis GET.** The manager issues a `GET` against Redis for the serialized key derived from the method arguments (`id = 1`). On a cold cache, this returns nothing.
4. **Cache miss, method runs.** `findProduct(1)` executes, printing `"Loading product 1"`, and returns `new Product(1, "Product #1")`.
5. **Serialization and Redis SET.** The `GenericJackson2JsonRedisSerializer` converts the `Product` record to a JSON byte array; the manager issues a Redis `SET` for that key with a 6-hour expiration attached (Redis's own `EXPIRE` mechanism, driven by the configured `entryTtl`).
6. **Return.** The `Product` object is returned to the caller — from the caller's point of view, indistinguishable from any other `CacheManager` implementation.
7. **Session call runs the same flow independently**, but resolves against `"sessions"`'s 2-minute TTL configuration instead — the two caches share the same Redis connection and manager bean but expire on entirely different schedules.

```
findProduct(1)
  -> CacheManager.getCache("products")   [TTL = 6h, from perCacheConfig]
  -> Redis GET key -> miss
  -> run method -> Product(1, "Product #1")
  -> Jackson serialize -> Redis SET key value EX 21600
  -> return Product

findSessionUser("s1")
  -> CacheManager.getCache("sessions")   [TTL = 2m, from perCacheConfig]
  -> Redis GET key -> miss -> run method -> Redis SET ... EX 120
  -> return "user-s1"
```

If Redis were unreachable during step 3, the `CacheErrorHandler` bean's `handleCacheGetError` would print the fallback message and let the call proceed straight to step 4 (running the method) rather than throwing — the caller gets a correct, if uncached, result instead of a failed request.

## 7. Gotchas & takeaways

> Gotcha: switching from an in-process cache (Caffeine) to a distributed one (Redis) is not a drop-in swap in practice — every cached object must now be serializable across the network (JSON via Jackson, or another serializer), which can silently break for types that don't serialize cleanly (records with non-serializable fields, classes with circular references) even though the exact same code worked fine with Caffeine's in-memory references.

- Choose Caffeine for single-instance or don't-need-cross-instance-consistency caching; choose Redis (or another distributed cache) once multiple instances must share cache state.
- Always configure explicit size limits (Caffeine `maximumSize`) or TTLs (Redis `entryTtl`) — an unbounded cache of either kind is a memory or storage growth risk.
- Different caches often deserve different TTLs based on how quickly their underlying data goes stale — configure per-cache overrides rather than one blanket default.
- A remote cache (Redis) introduces a new failure mode local caches don't have: the cache server itself can become unreachable. Configure a `CacheErrorHandler` so a cache outage degrades to "slower, but correct" rather than breaking requests outright.
