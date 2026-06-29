---
card: spring-boot
gi: 274
slug: hazelcast-auto-config
title: Hazelcast auto-config
---

## 1. What it is

**Hazelcast** is an in-memory data grid (IMDG) — a distributed caching and computing platform. Spring Boot auto-configures a `HazelcastInstance` bean when:

1. `hazelcast-spring` (or `hazelcast`) is on the classpath, AND
2. Either a `hazelcast.xml`/`hazelcast.yaml` config file is found on the classpath, OR a `HazelcastClientConfig` / `HazelcastConfig` bean is defined.

The auto-configured `HazelcastInstance` can be used as:
- A **Spring Cache** provider (`@Cacheable`, `@CacheEvict`) — via `HazelcastCacheManager`.
- A **Spring Session** store — distributed HTTP sessions across multiple instances.
- A **distributed Map, Queue, Topic, or Lock** — Hazelcast's native data structures.

## 2. Why & when

Use Hazelcast when:

- You need **distributed caching** that survives one node going down (Hazelcast replicates across nodes).
- You need **session stickiness-free clustering** — HTTP sessions stored in Hazelcast survive a pod restart or rolling update.
- You need **distributed coordination** — distributed locks, leader election, or cluster-wide pub/sub.
- You're already running Hazelcast as an infrastructure component and want Spring Boot to connect to it.

Hazelcast comes in two topologies:
- **Embedded** — the Spring Boot process is also a Hazelcast member; the grid lives inside your JVM.
- **Client** — the Spring Boot process is a Hazelcast client; the grid runs as separate server processes.

For production, client mode is preferred: the cluster is stable, and app deployments don't affect cluster membership.

## 3. Core concept

Spring Boot's `HazelcastAutoConfiguration` tries the following in order:

1. If a `HazelcastConfig` bean exists → use it for embedded mode.
2. If a `HazelcastClientConfig` bean exists → use it for client mode.
3. If `hazelcast.xml` or `hazelcast-client.xml` is on the classpath → parse it.
4. If `spring.hazelcast.config` property points to a file → load it.

Once a `HazelcastInstance` bean is created:
- `HazelcastCacheAutoConfiguration` detects it and configures `HazelcastCacheManager` as the `CacheManager` bean (if `spring.cache.type=hazelcast` or Hazelcast is the only available cache provider).
- Add `@EnableCaching` + `@Cacheable` annotations to use it.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hazelcast auto-config: HazelcastInstance created from config, used as Spring Cache or distributed data structure">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Config sources -->
  <rect x="10" y="30" width="160" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="55" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">hazelcast.xml / .yaml</text>

  <rect x="10" y="85" width="160" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">HazelcastConfig @Bean</text>

  <rect x="10" y="140" width="160" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">spring.hazelcast.config</text>

  <!-- HazelcastInstance -->
  <rect x="230" y="80" width="170" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="108" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">HazelcastInstance</text>
  <text x="315" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Bean (auto-configured)</text>
  <text x="315" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">embedded or client mode</text>

  <!-- Uses -->
  <rect x="460" y="40" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">HazelcastCacheManager → @Cacheable</text>

  <rect x="460" y="100" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="125" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Session → distributed sessions</text>

  <rect x="460" y="160" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="185" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">IMap / IQueue / ITopic / ILock</text>

  <line x1="170" y1="50" x2="228" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="170" y1="105" x2="228" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="170" y1="160" x2="228" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="400" y1="100" x2="458" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="400" y1="120" x2="458" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="400" y1="140" x2="458" y2="178" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
</svg>

One `HazelcastInstance` bean powers distributed caching, sessions, and raw data structures.

## 5. Runnable example

```java
// HazelcastAutoConfigDemo.java — run with: java HazelcastAutoConfigDemo.java
// Shows Hazelcast configuration patterns, @Cacheable integration,
// and key distributed data structure usage.

import java.util.Map;
import java.util.concurrent.TimeUnit;

public class HazelcastAutoConfigDemo {

    // Simulated distributed cache (Hazelcast IMap in production)
    static final Map<String, String> CACHE = new java.util.concurrent.ConcurrentHashMap<>();

    public static void main(String[] args) throws Exception {
        System.out.println("=== Hazelcast Auto-config Demo ===\n");
        printDependency();
        printConfig();
        printSpringCacheIntegration();
        simulateDistributedCache();
    }

    static void printDependency() {
        System.out.println("--- pom.xml ---");
        System.out.println("""
            <dependency>
              <groupId>com.hazelcast</groupId>
              <artifactId>hazelcast-spring</artifactId>
              <!-- version managed by Spring Boot BOM -->
            </dependency>
            """);
    }

    static void printConfig() {
        System.out.println("--- hazelcast.yaml (place in src/main/resources/) ---");
        System.out.println("""
            hazelcast:
              cluster-name: my-cluster
              network:
                join:
                  multicast:
                    enabled: false      # disable for production
                  tcp-ip:
                    enabled: true
                    members:            # list cluster members explicitly
                      - 10.0.0.1
                      - 10.0.0.2
              map:
                products:
                  time-to-live-seconds: 300   # cache TTL
                  max-idle-seconds: 60
                  eviction:
                    eviction-policy: LRU
                    max-size-policy: PER_NODE
                    size: 10000

            # Client mode (hazelcast-client.yaml):
            # hazelcast-client:
            #   cluster-name: my-cluster
            #   network:
            #     cluster-members:
            #       - hazelcast-server-1:5701
            #       - hazelcast-server-2:5701
            """);
    }

    static void printSpringCacheIntegration() {
        System.out.println("--- Spring Cache integration ---");
        System.out.println("""
            // application.properties:
            spring.cache.type=hazelcast

            // Enable caching:
            @SpringBootApplication
            @EnableCaching
            public class App { ... }

            // Use caching:
            @Service
            public class ProductService {

                @Cacheable(value = "products", key = "#id")
                public Product findById(long id) {
                    // Only executes on cache miss; result stored in Hazelcast 'products' map
                    return productRepository.findById(id).orElseThrow();
                }

                @CachePut(value = "products", key = "#product.id")
                public Product update(Product product) {
                    return productRepository.save(product);
                }

                @CacheEvict(value = "products", key = "#id")
                public void delete(long id) {
                    productRepository.deleteById(id);
                }
            }
            """);
    }

    static void simulateDistributedCache() throws InterruptedException {
        System.out.println("--- Simulated cache behaviour ---");

        // First call — cache miss
        String key = "product:42";
        if (!CACHE.containsKey(key)) {
            System.out.println("  Cache MISS for " + key);
            // Simulate DB load
            Thread.sleep(50);
            CACHE.put(key, "{\"id\":42,\"name\":\"Widget Pro\",\"price\":29.99}");
            System.out.println("  Loaded from DB → stored in Hazelcast IMap 'products'");
        }

        // Second call — cache hit
        String cached = CACHE.get(key);
        System.out.println("  Cache HIT for " + key + " → " + cached);
        System.out.println("  (In Hazelcast: map.get() ~ 0.2ms vs DB query ~ 5–50ms)");

        System.out.println();
        System.out.println("--- Distributed lock example ---");
        System.out.println("""
            // Hazelcast distributed lock (cross-JVM, cross-node):
            HazelcastInstance hz = ...;
            FencedLock lock = hz.getCPSubsystem().getLock("order-processing-lock");
            lock.lock();
            try {
                // Only ONE instance in the cluster executes this at a time
                processOrder(orderId);
            } finally {
                lock.unlock();
            }

            // Useful for: scheduled jobs that must not run concurrently on multiple nodes
            """);
    }
}
```

**How to run:** `java HazelcastAutoConfigDemo.java`

## 6. Walkthrough

- **`hazelcast.yaml` on classpath** — the simplest configuration approach. Spring Boot's `HazelcastAutoConfiguration` calls `Hazelcast.newHazelcastInstance(config)` or `HazelcastClient.newHazelcastClient(clientConfig)` using the parsed YAML. No Java configuration class needed.
- **`spring.cache.type=hazelcast`** — explicitly selects Hazelcast as the cache manager. If Hazelcast is the only cache provider on the classpath, Spring Boot selects it automatically. The `value="products"` in `@Cacheable` maps to a Hazelcast `IMap` named "products" — define its eviction policy in `hazelcast.yaml` under `map.products`.
- **`@CachePut` vs `@Cacheable`** — `@Cacheable` skips the method body on a cache hit. `@CachePut` always runs the method AND updates the cache entry. Use `@CachePut` on update operations to keep the cache consistent without a read-then-write cycle.
- **Distributed lock** — Hazelcast's CP (consensus-based) subsystem provides `FencedLock`. Unlike Java's `synchronized` (single JVM), this lock is visible across all cluster members. Ensures that `processOrder()` runs on exactly one node at a time, even with 10 pods.
- **Client vs embedded** — embedded Hazelcast is simpler (no separate server) but couples app lifecycle to cluster lifecycle. Client mode is better for production: the Hazelcast cluster is a stable, independent service; app pods connect and disconnect without affecting cluster stability.

## 7. Gotchas & takeaways

> **Embedded Hazelcast in a Spring Boot app means every deployment restarts a cluster member.** If you have 3 pods and you roll out a new version, the old members leave the cluster as new members join. Data is migrated (it's distributed), but there's extra network traffic and temporary reduced redundancy. Client mode avoids this entirely.

> **Hazelcast's `IMap` serialises values to bytes.** Your cached objects must be `Serializable` (Java serialisation) or registered with a custom `Serializer` (Hazelcast's DataSerializable, Portable, or custom). If you cache JPA entities, ensure they're `Serializable` or use DTOs.

- `spring.hazelcast.config=classpath:hazelcast-client.yaml` explicitly points to a client config file.
- For Spring Session: add `spring-session-hazelcast` dependency and `@EnableHazelcastHttpSession` — HTTP sessions are stored in Hazelcast automatically.
- Hazelcast's Jet engine (`HazelcastJetService`) is for stream processing — not covered by auto-config but available in the same dependency.
- Monitor cluster health: Hazelcast Management Center (free for dev) shows member count, map sizes, and operation rates.
- `hazelcast.map.products.time-to-live-seconds=300` sets automatic expiry — critical for correctness; stale cache entries cause bugs.
