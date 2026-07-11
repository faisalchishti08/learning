---
card: spring-data
gi: 189
slug: region-template-configuration
title: "Region & template configuration"
---

## 1. What it is

Apache Geode (and its commercial distribution, GemFire) is an in-memory data grid: a distributed, partitioned key-value store designed for extremely low-latency access at large scale, often used as a caching and compute layer in front of a slower system of record. A "Region" is Geode's core storage concept — roughly analogous to a table or collection — and `GemfireTemplate` is Spring Data Geode's low-level access API over it, configured declaratively.

```java
@Configuration
class GeodeConfig {
    @Bean
    ClientRegionFactoryBean<String, Customer> customersRegion(GemFireCache cache) {
        ClientRegionFactoryBean<String, Customer> region = new ClientRegionFactoryBean<>();
        region.setCache(cache);
        region.setShortcut(ClientRegionShortcut.PROXY);
        return region;
    }
}

@Autowired GemfireTemplate customersTemplate;
```

## 2. Why & when

This card opens a short final section covering Spring Data for Apache Geode/GemFire — an in-memory, distributed data grid rather than a disk-backed database. Where Redis (covered earlier in this course) is a single logical in-memory store typically accessed over the network, Geode is built to be partitioned and replicated across many nodes as a genuinely distributed compute grid, often colocating application logic with the data itself for extremely low-latency processing.

Reach for Geode/GemFire's Region and template configuration when:

- The application needs an in-memory data grid for extremely low-latency, high-throughput access — session state, real-time pricing data, computed aggregates — at a scale beyond a single machine's memory.
- You're configuring how data is stored and distributed: a `PROXY` region delegates entirely to a server cluster, while other shortcuts configure local caching layered on top.
- `GemfireTemplate` is needed as the direct access API before reaching for the (next card's) repository abstraction on top of it.

## 3. Core concept

```
 Region "customers"  -- Geode's core storage concept, like a table or a Map

 ClientRegionShortcut.PROXY          -- no local storage, every operation goes to the server cluster
 ClientRegionShortcut.CACHING_PROXY  -- local cache layered in front of the server cluster

 GemfireTemplate customersTemplate = new GemfireTemplate(customersRegion);
 customersTemplate.put("c1", new Customer("c1", "Amara"));
 Customer found = customersTemplate.get("c1");
```

A Region is configured once, declaratively, and the template provides the same put/get access pattern seen for Redis's `opsForValue()` earlier in this course, just backed by a distributed grid instead of a single logical store.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client application accesses a customers Region through a GemfireTemplate, which is backed by a distributed server cluster">
  <rect x="20" y="45" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">GemfireTemplate</text>
  <text x="110" y="86" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.put / .get</text>

  <line x1="200" y1="70" x2="260" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a22)"/>

  <rect x="270" y="45" width="150" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Region "customers"</text>

  <line x1="420" y1="70" x2="480" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a22)"/>

  <rect x="490" y="30" width="130" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">distributed</text>
  <text x="555" y="70" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">server</text>
  <text x="555" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">cluster</text>

  <defs><marker id="a22" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The template provides a simple put/get API over a Region backed by a distributed cluster.

## 5. Runnable example

The scenario: storing customer data in a Geode-style Region, evolving from a bare `put`/`get` baseline against an in-memory stand-in, to a `PROXY`-style region configuration that delegates every operation to a simulated server cluster, to a `CACHING_PROXY`-style configuration that layers a local cache in front of the server, reducing network round trips for repeated reads.

### Level 1 — Basic

Model the bare `GemfireTemplate` put/get API against an in-memory stand-in for a Region.

```java
import java.util.*;

public class RegionConfigLevel1 {
    public static void main(String[] args) {
        GemfireTemplate template = new GemfireTemplate();
        template.put("c1", new Customer("c1", "Amara"));
        template.put("c2", new Customer("c2", "Bilal"));

        Customer found = template.get("c1");
        System.out.println("Found: " + found.name);
    }
}

class Customer { String id, name; Customer(String id, String name) { this.id = id; this.name = name; } }

// Stands in for org.springframework.data.gemfire.GemfireTemplate over a configured Region.
class GemfireTemplate {
    private final Map<String, Customer> region = new HashMap<>();
    void put(String key, Customer value) { region.put(key, value); }
    Customer get(String key) { return region.get(key); }
}
```

How to run: `java RegionConfigLevel1.java`

`put`/`get` mirror `GemfireTemplate`'s core operations directly against a Region — the same simple key-value shape seen for Redis's basic operations, just conceptually backed by an in-memory grid rather than a single Redis instance.

### Level 2 — Intermediate

Model a `PROXY` region: every operation delegates entirely to a (simulated) remote server cluster — no local storage on the client side at all.

```java
import java.util.*;

public class RegionConfigLevel2 {
    public static void main(String[] args) {
        ServerCluster cluster = new ServerCluster(); // stands in for the actual Geode server-side cluster
        GemfireTemplate template = new GemfireTemplate(cluster, RegionShortcut.PROXY);

        template.put("c1", new Customer("c1", "Amara"));
        System.out.println("Written directly to cluster: " + cluster.contains("c1"));

        Customer found = template.get("c1"); // EVERY get also goes straight to the cluster -- no local cache
        System.out.println("Found via cluster round trip: " + found.name);
    }
}

class Customer { String id, name; Customer(String id, String name) { this.id = id; this.name = name; } }
enum RegionShortcut { PROXY, CACHING_PROXY }

class ServerCluster {
    private final Map<String, Customer> data = new HashMap<>();
    void write(String key, Customer value) { data.put(key, value); }
    Customer read(String key) { return data.get(key); }
    boolean contains(String key) { return data.containsKey(key); }
}

class GemfireTemplate {
    private final ServerCluster cluster;
    private final RegionShortcut shortcut;
    GemfireTemplate(ServerCluster cluster, RegionShortcut shortcut) { this.cluster = cluster; this.shortcut = shortcut; }

    void put(String key, Customer value) { cluster.write(key, value); } // PROXY: always writes through
    Customer get(String key) { return cluster.read(key); }               // PROXY: always reads through, no local cache
}
```

How to run: `java RegionConfigLevel2.java`

Every `put` and `get` on a `PROXY`-configured region goes straight to `cluster` — there's no local storage layer at all, which minimizes memory use on the client but means every single read pays the network round-trip cost to the server cluster.

### Level 3 — Advanced

Add a `CACHING_PROXY`-style region: a local cache layered in front of the server cluster, checked first on reads, invalidated correctly on writes — reducing repeated round trips for hot keys.

```java
import java.util.*;

public class RegionConfigLevel3 {
    public static void main(String[] args) {
        ServerCluster cluster = new ServerCluster();
        GemfireTemplate template = new GemfireTemplate(cluster, RegionShortcut.CACHING_PROXY);

        template.put("c1", new Customer("c1", "Amara")); // writes through to the cluster AND populates local cache

        System.out.println("First get (cache hit, no cluster round trip): " + template.get("c1").name);
        System.out.println("Cluster reads so far: " + cluster.readCount);

        template.get("c1"); // second read -- should hit the LOCAL cache, not the cluster again
        System.out.println("Cluster reads after second get: " + cluster.readCount); // unchanged
    }
}

class Customer { String id, name; Customer(String id, String name) { this.id = id; this.name = name; } }
enum RegionShortcut { PROXY, CACHING_PROXY }

class ServerCluster {
    private final Map<String, Customer> data = new HashMap<>();
    int readCount = 0;
    void write(String key, Customer value) { data.put(key, value); }
    Customer read(String key) { readCount++; return data.get(key); }
}

class GemfireTemplate {
    private final ServerCluster cluster;
    private final RegionShortcut shortcut;
    private final Map<String, Customer> localCache = new HashMap<>(); // only used in CACHING_PROXY mode

    GemfireTemplate(ServerCluster cluster, RegionShortcut shortcut) { this.cluster = cluster; this.shortcut = shortcut; }

    void put(String key, Customer value) {
        cluster.write(key, value); // always write through to the cluster -- it's the source of truth
        if (shortcut == RegionShortcut.CACHING_PROXY) localCache.put(key, value); // also populate local cache
    }
    Customer get(String key) {
        if (shortcut == RegionShortcut.CACHING_PROXY && localCache.containsKey(key)) {
            return localCache.get(key); // cache hit -- no cluster round trip at all
        }
        Customer value = cluster.read(key); // cache miss (or PROXY mode) -- go to the cluster
        if (shortcut == RegionShortcut.CACHING_PROXY) localCache.put(key, value);
        return value;
    }
}
```

How to run: `java RegionConfigLevel3.java`

The first `get("c1")` is actually a cache miss too (nothing was in `localCache` yet from a prior read — `put` populated it directly, so this one *does* hit the local cache), but the second `get("c1")` demonstrably reuses the cached value: `cluster.readCount` stays the same across both calls, showing the local cache successfully avoided a second network round trip to the server cluster.

## 6. Walkthrough

Execution starts in `main` for Level 3. `template.put("c1", ...)` writes to `cluster` (the source of truth) and also populates `localCache`, mirroring how a `CACHING_PROXY` region keeps its local cache consistent with every write it makes.

The first `template.get("c1")` call checks `localCache` first, finds the entry already there (from the `put` above), and returns it without ever calling `cluster.read` — `cluster.readCount` remains at its starting value of `0`:

```
First get (cache hit, no cluster round trip): Amara
Cluster reads so far: 0
```

The second `get("c1")` call repeats the same cache check, finds the same cached entry, and again avoids the cluster entirely:

```
Cluster reads after second get: 0
```

In a real Geode/GemFire deployment, this local-cache layering is exactly what makes `CACHING_PROXY` valuable for hot, frequently-read keys: the client-side JVM keeps a working set of recently accessed data in local memory, only paying the network cost to the distributed server cluster on a genuine cache miss or an explicit invalidation, while `PROXY` (Level 2) pays that cost on every single operation, trading memory for consistency guarantees and simplicity.

## 7. Gotchas & takeaways

> Gotcha: a `CACHING_PROXY` region's local cache can become stale if the underlying data changes on the server cluster through a path that doesn't go through this same client's `put` — e.g. another application instance writing to the same Region — unless the region is also configured with appropriate expiration or invalidation listeners to keep the local cache in sync with cluster-side changes made elsewhere.

> Gotcha: choosing `PROXY` when the access pattern is actually read-heavy on a small set of hot keys leaves easy latency savings on the table, while choosing `CACHING_PROXY` for a huge, rarely-repeated key space just wastes local memory on entries that are unlikely to be read again before being evicted — the shortcut choice should match the actual access pattern, not just default to whichever seems safer.

- A Region is Geode's core storage abstraction — conceptually similar to a table or a distributed `Map` — configured declaratively and accessed through `GemfireTemplate`.
- `PROXY` regions have no local storage and delegate every operation to the server cluster; `CACHING_PROXY` regions layer a local cache in front, trading memory for reduced network round trips on repeated reads.
- Geode/GemFire is built for distributed, in-memory, extremely low-latency access at a scale beyond what a single-instance in-memory store (like Redis, covered earlier) is typically designed for.
- The right region shortcut depends on the actual access pattern — read-heavy on hot keys favors caching, while access patterns with little repetition gain little from a local cache layer.
