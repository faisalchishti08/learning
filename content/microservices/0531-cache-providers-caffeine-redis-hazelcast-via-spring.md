---
card: microservices
gi: 531
slug: cache-providers-caffeine-redis-hazelcast-via-spring
title: "Cache providers (Caffeine, Redis, Hazelcast) via Spring"
---

## 1. What it is

Spring's [`@Cacheable`/`@CacheEvict` abstraction](0530-spring-cache-abstraction-cacheable-cacheevict.md) is deliberately decoupled from any specific cache storage technology — the actual storage backend is a pluggable `CacheManager` bean, and three of the most common choices are **Caffeine** (a fast, in-memory, local Java cache), **Redis** (a shared, external, in-memory data store usable as a [distributed cache](0502-local-vs-distributed-cache.md)), and **Hazelcast** (an embeddable, distributed, clustered in-memory data grid). Which one you configure changes nothing about the `@Cacheable`-annotated business code — only the `CacheManager` bean definition — but changes everything about where the cached data actually lives and who can see it.

## 2. Why & when

You pick a specific cache provider based on where the cached data needs to live and how many service instances need to share it:

- **Caffeine is the right choice for a fast, per-instance, local cache** — it lives entirely in the JVM's own heap memory, has extremely low latency (no network hop at all), and is ideal when each service instance can maintain its own independent cache without needing to see what other instances have cached. The cost: it's not shared — five horizontally-scaled instances of the same service each maintain five separate, un-coordinated Caffeine caches.
- **Redis is the right choice when multiple service instances need to share one cache**, or when the cache needs to survive an individual instance restarting — since Redis runs as a separate process (or cluster) that every instance connects to over the network, a value cached by one instance is immediately visible to every other instance, at the cost of a network round-trip per cache access instead of an in-process lookup.
- **Hazelcast sits between the two**: it's a distributed, clustered cache, but one that can be embedded directly inside your application instances (each instance is itself a node in the Hazelcast cluster) rather than requiring a wholly separate server process like Redis — useful when you want cache sharing across instances without standing up and operating a separate Redis deployment.
- **The choice is purely about data-sharing and durability requirements, not about the `@Cacheable` code itself** — a method annotated `@Cacheable("orders")` behaves identically regardless of which of these three backs the `"orders"` cache; only the `CacheManager` configuration differs.

## 3. Core concept

Think of three ways a team might keep frequently-needed reference material handy. Each team member keeping their own personal sticky notes at their own desk (Caffeine) is fastest to check but means five team members have five potentially different sets of notes, with no way for one person's note to help another. A shared whiteboard in a common hallway that everyone walks to and reads from (Redis) means everyone sees the exact same, single, shared set of notes, at the cost of the walk to check it every time. A shared, synchronized notebook that gets replicated automatically between everyone's own desks, so each person has a local copy that's kept in sync with everyone else's (Hazelcast) is a middle ground — locally fast to read, but coordinated behind the scenes so everyone converges on the same content.

Concretely:

1. **A `CacheManager` bean is what Spring's `@Cacheable`/`@CacheEvict` machinery actually delegates to** — swap the `CacheManager` implementation (`CaffeineCacheManager`, `RedisCacheManager`, `HazelcastCacheManager`), and every annotated method's behavior with respect to storage changes, with zero changes to the annotated methods themselves.
2. **Caffeine's cache lives inside one JVM's heap** — fast, but private to that one instance; useless for coordinating cached state across a horizontally-scaled fleet.
3. **Redis's cache lives in a separate, shared process** — every instance connects to the same Redis deployment over the network, so cached values are immediately visible fleet-wide, at the cost of network latency per access and an additional piece of infrastructure to operate.
4. **Hazelcast's cache is distributed across the application instances themselves**, forming a cluster among them directly, without a separate cache server to deploy and operate — a middle ground trading some operational simplicity (no separate Redis deployment) for tighter coupling between your application's lifecycle and the cache cluster's membership.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Caffeine caches locally per instance with no sharing; Redis is one shared external store all instances hit over the network; Hazelcast clusters the instances themselves into a distributed cache">
  <rect x="10" y="20" width="200" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Caffeine</text>
  <text x="110" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instance A: local cache</text>
  <text x="110" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instance B: SEPARATE local cache</text>
  <text x="110" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no sharing between them</text>

  <rect x="230" y="20" width="200" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Redis</text>
  <text x="330" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instances A, B, C all connect</text>
  <text x="330" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">to ONE shared external store</text>
  <text x="330" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">network hop per access</text>

  <rect x="450" y="20" width="200" height="90" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="550" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Hazelcast</text>
  <text x="550" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">instances A, B, C ARE the</text>
  <text x="550" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">cluster nodes -- no separate server</text>
  <text x="550" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">data distributed among them</text>

  <text x="330" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">All three: same @Cacheable code, different CacheManager bean</text>
</svg>

The choice of provider changes where cached data lives and how it's shared, without touching any `@Cacheable`-annotated business method.

## 5. Runnable example

Scenario: caching an order lookup across a fleet of service instances. We start with the local-only Caffeine behavior modeled in plain Java to show the sharing gap, extend it to a shared-store model resembling Redis, then handle the hard case: configuring a real Spring `CacheManager` swap between Caffeine and Redis with zero change to the annotated service method.

### Level 1 — Basic

```java
// File: LocalCacheGap.java -- models the CAFFEINE-LIKE behavior: each
// "instance" has its OWN local cache, so one instance's cached value is
// INVISIBLE to another instance entirely.
import java.util.*;

public class LocalCacheGap {
    static class ServiceInstance {
        String name;
        Map<String, String> localCache = new HashMap<>(); // each instance's OWN cache
        ServiceInstance(String name) { this.name = name; }

        String getOrder(String orderId) {
            if (localCache.containsKey(orderId)) {
                System.out.println("[" + name + "] cache HIT for " + orderId);
                return localCache.get(orderId);
            }
            System.out.println("[" + name + "] cache MISS for " + orderId + " -- fetching from database");
            String result = "{\"orderId\":\"" + orderId + "\"}";
            localCache.put(orderId, result);
            return result;
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        instanceA.getOrder("42"); // MISS on A -- fetches and caches locally on A only
        instanceB.getOrder("42"); // MISS on B too! B has NO knowledge of A's cache
        System.out.println("Same order, fetched from the database TWICE -- local caches don't share.");
    }
}
```

How to run: `java LocalCacheGap.java`

Each `ServiceInstance` has its own private `localCache` map — exactly how Caffeine behaves per JVM. `instanceA` caching order `"42"` has zero effect on `instanceB`'s cache; `instanceB` independently misses and refetches the same data, demonstrating the fundamental limitation of a local-only cache across a horizontally-scaled fleet.

### Level 2 — Intermediate

```java
// File: SharedStoreModel.java -- models the REDIS-LIKE behavior: ONE
// shared store that every "instance" connects to, so a value cached by
// one instance IS visible to every other instance immediately.
import java.util.*;

public class SharedStoreModel {
    // ONE shared store, simulating a separate Redis process every instance connects to
    static Map<String, String> sharedStore = new HashMap<>();
    static int networkHopsToSharedStore = 0;

    static class ServiceInstance {
        String name;
        ServiceInstance(String name) { this.name = name; }

        String getOrder(String orderId) {
            networkHopsToSharedStore++; // every access, hit or miss, costs a network round-trip to the shared store
            if (sharedStore.containsKey(orderId)) {
                System.out.println("[" + name + "] cache HIT for " + orderId + " (via shared store)");
                return sharedStore.get(orderId);
            }
            System.out.println("[" + name + "] cache MISS for " + orderId + " -- fetching from database, then storing in SHARED store");
            String result = "{\"orderId\":\"" + orderId + "\"}";
            sharedStore.put(orderId, result); // written to the SHARED store, visible to every instance
            return result;
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        instanceA.getOrder("42"); // MISS on A -- fetches and stores in the SHARED store
        instanceB.getOrder("42"); // HIT on B! B sees A's cached value via the shared store
        System.out.println("Total network hops to shared store: " + networkHopsToSharedStore + " (both hit and miss cost one)");
    }
}
```

How to run: `java SharedStoreModel.java`

`sharedStore` is a single map shared across both `ServiceInstance` objects, modeling a separate Redis deployment every real instance would connect to over the network. `instanceB`'s call correctly hits, because `instanceA`'s earlier write is visible fleet-wide — the exact gap from Level 1 is closed, at the cost of every access (hit or miss) paying a simulated network round-trip, tracked here via `networkHopsToSharedStore`.

### Level 3 — Advanced

```java
// File: SwappableCacheManager.java -- the REAL Spring shape: the SAME
// @Cacheable service method works UNCHANGED whether backed by Caffeine
// (local) or Redis (shared) -- only the CacheManager BEAN CONFIGURATION differs.
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.stereotype.Service;

public class SwappableCacheManager {

    // the annotated service method is IDENTICAL regardless of which CacheManager is active
    @Service
    static class OrderService {
        @Cacheable(cacheNames = "orders", key = "#orderId")
        public String getOrder(String orderId) {
            System.out.println("[expensive call] fetching order " + orderId + " from the database");
            return "{\"orderId\":\"" + orderId + "\"}";
        }
    }

    @Configuration
    @EnableCaching
    static class LocalCacheConfig {
        @Bean
        @Profile("local") // active for single-instance local development
        public CacheManager caffeineCacheManager() {
            return new CaffeineCacheManager("orders"); // in-JVM, per-instance cache
        }
    }

    @Configuration
    @EnableCaching
    static class SharedCacheConfig {
        @Bean
        @Profile("production") // active when running as a horizontally-scaled fleet
        public CacheManager redisCacheManager(RedisConnectionFactory connectionFactory) {
            return RedisCacheManager.create(connectionFactory); // shared, external cache across all instances
        }
    }
}
```

How to run: requires `spring-boot-starter-cache` plus either `com.github.ben-manes.caffeine:caffeine` (for the `local` profile) or `spring-boot-starter-data-redis` and a running Redis instance (for the `production` profile); activate a profile via `spring.profiles.active=local` or `spring.profiles.active=production` and run via `mvn spring-boot:run` — `OrderService.getOrder` behaves identically either way from the calling code's point of view.

`OrderService.getOrder` contains no reference to Caffeine or Redis at all — `@Cacheable(cacheNames = "orders", ...)` just names a logical cache, and Spring resolves that name against whichever `CacheManager` bean is active for the current profile. Switching from local development (Caffeine, fast, per-instance, no extra infrastructure) to production (Redis, shared across the whole fleet) is purely a configuration and profile change, with zero modification to `OrderService` itself.

## 6. Walkthrough

Trace what happens when the `production` profile (Redis-backed) is active and two horizontally-scaled instances of the application both call `orderService.getOrder("42")`, end to end:

1. **Instance A calls `getOrder("42")`.** Spring's caching proxy checks the `"orders"` cache — which, because the `production` profile is active, is now backed by `RedisCacheManager` rather than an in-JVM map — for key `"42"`. Redis reports a miss (nothing cached yet fleet-wide).
2. **The proxy invokes the real method body on Instance A**, printing `[expensive call] fetching order 42...` and returning `{"orderId":"42"}`. The proxy then writes this value into Redis under the `"orders"::42` key — a write to the shared, external Redis process, not to any local, per-instance memory.
3. **Instance B (a completely separate JVM, possibly on a different host) calls `getOrder("42")`.** Its own caching proxy checks the same `"orders"` cache — because it's the *same* Redis deployment both instances are configured to connect to, this lookup finds the entry Instance A wrote in step 2.
4. **Instance B's proxy returns the cached value directly**, without ever invoking its own copy of the real method body — no "fetching order" log line prints on Instance B at all, even though Instance B never previously called `getOrder("42")` itself.

Contrast this directly with what would happen under the `local` (Caffeine) profile: at step 3, Instance B's own in-JVM Caffeine cache would have no knowledge of Instance A's cached entry (exactly as demonstrated in Level 1), so Instance B would also print `[expensive call] fetching order 42...` and hit the database independently — correct behavior for local development, but a fleet-wide cache-sharing gap in production, which is exactly why the `production` profile switches to Redis.

## 7. Gotchas & takeaways

> **Gotcha:** switching from Caffeine to Redis changes more than just "where the cache lives" — cached values now have to be serialized to cross the network to Redis and deserialized back, so every cached type needs to actually be serializable in whatever format the `RedisCacheManager` is configured to use (commonly JSON); a type that worked fine cached in-JVM with Caffeine can fail or behave unexpectedly once moved to Redis if it isn't properly serializable.

- Caffeine: fastest, in-JVM, per-instance — right when each instance can safely maintain its own independent cache with no cross-instance coordination needed.
- Redis: shared, external, network-hop-per-access — right when multiple instances must see the same cached values, or when cached data needs to survive an individual instance restarting.
- Hazelcast: distributed among the application instances themselves — a middle ground giving cross-instance sharing without a separately operated cache server, at the cost of coupling cache cluster membership to your application instances' own lifecycle.
- The provider choice lives entirely in the `CacheManager` bean configuration — well-designed `@Cacheable` business code never needs to change when moving between these three, which is the entire point of Spring's cache abstraction being decoupled from any specific backend.
