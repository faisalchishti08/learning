---
card: system-design
gi: 61
slug: spring-data-redis-for-distributed-caching
title: Spring Data Redis for distributed caching
---

## 1. What it is

**Spring Data Redis** is Spring's integration module for talking to a Redis server, offering both a low-level `RedisTemplate` for direct key-value operations and, combined with `@EnableCaching`, a Redis-backed `CacheManager` that plugs straight into the `@Cacheable` / `@CacheEvict` annotations covered earlier — so the exact same caching annotations now store their data in Redis instead of local memory.

## 2. Why & when

The Spring Cache abstraction by default (with no extra configuration) uses a simple in-process map, which only helps a single application instance. Wiring in Spring Data Redis's `RedisCacheManager` swaps that in-process store for a real, shared Redis instance, turning your existing `@Cacheable` methods into a properly distributed cache with no change to the annotations themselves — only the configuration changes. Reach for it the moment your application runs as more than one instance and needs those instances to share cached data.

## 3. Core concept

**Configuration swaps the cache backend, not the annotations:** the same `@Cacheable("users")` method from the previous tutorial works unchanged; only the `CacheManager` bean configuration changes, from an in-memory implementation to a Redis-backed one.

```java
@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        return new LettuceConnectionFactory("localhost", 6379);
    }

    @Bean
    public CacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(10)); // TTL applied to every entry in this cache
        return RedisCacheManager.builder(factory).cacheDefaults(config).build();
    }
}
```

**`RedisTemplate` for direct control:** beyond `@Cacheable`, `RedisTemplate<String, Object>` gives direct `opsForValue().set(key, value, ttl)` / `get(key)` access, useful when you need finer control than the annotation-based approach offers — a custom TTL per key, or a data structure Redis supports beyond simple key-value (like a sorted set for a leaderboard).

**Serialization matters:** Redis stores raw bytes, so Spring Data Redis must serialize your Java objects to bytes on write and deserialize them back on read. The default Java serialization is verbose and not human-readable in Redis; a `GenericJackson2JsonRedisSerializer` (storing values as JSON) is a common, more practical choice.

## 4. Diagram

```
Service method: @Cacheable("users") findById(42)
        |
        v
Spring-generated proxy (same as before)
        |
   check cache "users", key=42
        |
        v
RedisCacheManager -----network call-----> Redis server
        |                                      |
   HIT: deserialize bytes -> User        MISS: proxy calls real method,
   return, real method skipped                  serializes result, SETs it in Redis
```
*Caption: the same `@Cacheable` proxy now checks Redis over the network instead of an in-process map — visible to every application instance.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling a Redis-backed `CacheManager`, contrasted with the in-process version

```java
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

public class RedisCacheManagerSim {

    // Stands in for a Redis server: ONE shared store, reachable "over the network"
    // by every simulated application instance - unlike a plain in-process HashMap.
    static class FakeRedisServer {
        private final Map<String, String> store = new HashMap<>();
        int networkCalls = 0;

        String get(String key) {
            networkCalls++;
            return store.get(key);
        }
        void set(String key, String value) {
            networkCalls++;
            store.put(key, value);
        }
    }

    // The proxy Spring generates for @Cacheable, now backed by the (fake) Redis server
    // instead of an in-process map - this is what RedisCacheManager changes.
    static class RedisCacheableProxy<V> {
        private final FakeRedisServer redis;
        private final String cacheName;
        private final Function<String, V> realMethod;
        int realMethodCalls = 0;

        RedisCacheableProxy(FakeRedisServer redis, String cacheName, Function<String, V> realMethod) {
            this.redis = redis; this.cacheName = cacheName; this.realMethod = realMethod;
        }

        @SuppressWarnings("unchecked")
        V cacheable(String id) {
            String redisKey = cacheName + "::" + id;
            String cached = redis.get(redisKey);
            if (cached != null) {
                return (V) cached; // hit: deserialized "from Redis"
            }
            realMethodCalls++;
            V value = realMethod.apply(id);
            redis.set(redisKey, String.valueOf(value)); // serialized "to Redis"
            return value;
        }
    }

    public static void main(String[] args) {
        FakeRedisServer sharedRedis = new FakeRedisServer(); // ONE Redis, shared by both instances

        RedisCacheableProxy<String> instanceA = new RedisCacheableProxy<>(sharedRedis, "users", id -> {
            System.out.println("  [instance A] querying database for " + id);
            return "Alice";
        });
        RedisCacheableProxy<String> instanceB = new RedisCacheableProxy<>(sharedRedis, "users", id -> {
            System.out.println("  [instance B] querying database for " + id);
            return "Alice";
        });

        System.out.println("instance A findById(42): " + instanceA.cacheable("42")); // miss, hits DB, writes to Redis
        System.out.println("instance B findById(42): " + instanceB.cacheable("42")); // HIT in Redis, instance B's own DB never called

        System.out.println("instance A real method calls: " + instanceA.realMethodCalls);
        System.out.println("instance B real method calls: " + instanceB.realMethodCalls); // 0 - Redis already had it
        System.out.println("total Redis network calls: " + sharedRedis.networkCalls);
    }
}
```

**How to run:** save as `RedisCacheManagerSim.java`, run `java RedisCacheManagerSim.java` (JDK 17+). A real setup needs a running Redis server and the `spring-boot-starter-data-redis` dependency; the `CacheConfig` class above wires `RedisCacheManager` to it.

## 6. Walkthrough

1. `sharedRedis` is created once and passed into *both* `instanceA` and `instanceB` — modeling one real Redis server reachable by every application instance, unlike the local in-process caches from the plain Spring Cache abstraction tutorial.
2. `instanceA.cacheable("42")` checks `sharedRedis` for `"users::42"`, finds nothing, calls its own real method (printing the `[instance A]` query line), and writes the result to `sharedRedis`.
3. `instanceB.cacheable("42")` checks the *same* `sharedRedis` for `"users::42"` and finds it already there — from instance A's write — so it returns immediately without ever calling its own real method or printing a query line.
4. `instanceA.realMethodCalls` is `1` and `instanceB.realMethodCalls` is `0`, directly showing that instance B's database was never queried at all — the cache entry populated by instance A was immediately usable by instance B, because both talk to the same Redis-backed store.
5. `sharedRedis.networkCalls` counts every `get`/`set` — each one now models a real network round trip to Redis, the cost this pattern trades for cross-instance cache sharing.

## 7. Gotchas & takeaways

> Gotcha: forgetting to configure serialization explicitly means Spring Data Redis falls back to Java's default serialization, which stores opaque, non-human-readable bytes in Redis — making the cached data impossible to inspect with `redis-cli` and fragile across class changes; configure a JSON serializer explicitly for anything you might need to debug.

- Swapping the `CacheManager` bean from in-memory to Redis-backed changes zero application code — the same `@Cacheable` / `@CacheEvict` annotations now operate on a shared, distributed store.
- Every cache access now costs a real network round trip to Redis, so it is slower than an in-process cache per-access but avoids the "different instances disagree" problem entirely.
- Related concepts: [Spring Cache abstraction (@Cacheable / @CacheEvict)](0059-spring-cache-abstraction-cacheable-cacheevict.md) (the annotations this configuration plugs into), [Redis / Memcached as a cache provider](0060-redis-memcached-as-a-cache-provider.md) (why a shared cache provider is needed in the first place).
