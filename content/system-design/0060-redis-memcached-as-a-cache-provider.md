---
card: system-design
gi: 60
slug: redis-memcached-as-a-cache-provider
title: Redis / Memcached as a cache provider
---

## 1. What it is

**Redis** and **Memcached** are standalone, in-memory data stores commonly used as a **shared cache** — a cache that lives outside any single application server, so every instance of your application reads and writes the same cached data. Memcached is a simple, distributed key-value store built purely for caching. Redis is also an in-memory key-value store but supports richer data structures (lists, sets, sorted sets, hashes) and optional persistence to disk.

## 2. Why & when

An in-process cache (a plain `HashMap` inside your application) is only visible to that one application instance; with multiple instances behind a load balancer, each one builds up its own separate, inconsistent cache, and a cache warmed on one instance is cold on every other. A shared cache like Redis or Memcached solves this: every application instance talks to the same external cache, so a value cached by one instance is immediately visible, as a hit, to every other instance. Use one whenever your application runs as more than one process or server.

## 3. Core concept

**Why a shared, external cache is necessary at scale:** picture three application servers behind a load balancer, each with its own in-process cache. A request for `user:42` might hit server A (cache miss, queries the database), then a later request for the same key hits server B (also a miss — server B's cache knows nothing about server A's). With a shared Redis or Memcached instance instead, server A's cache population is immediately visible to server B, C, and every other instance.

**Memcached's model:** a simple, multi-threaded key-value store, purely in memory, with no built-in persistence — if it restarts, the cache is empty again. Its simplicity makes it fast and easy to reason about for pure caching use cases.

**Redis's model:** also primarily in-memory, but Redis supports richer data structures beyond plain key-value pairs (useful for things like leaderboards using sorted sets, or rate limiting using counters with expiry), and can optionally persist data to disk (so a restart does not necessarily mean starting from an empty cache). This flexibility is why Redis is often chosen even for pure caching use cases, despite Memcached being simpler.

**Network cost, still real:** a shared cache removes the "different instances disagree" problem, but every cache access now costs a network round trip to the Redis or Memcached server, instead of an in-process memory read — still far cheaper than a database query, but not free.

## 4. Diagram

```
WITHOUT a shared cache (each instance has its own):
  App Server A: local cache { }         App Server B: local cache { }
  Request 1 -> A -> MISS -> DB -> A's cache: {user:42}
  Request 2 -> B -> MISS (B's cache never heard about A's write) -> DB again

WITH a shared cache (Redis / Memcached):
  App Server A ---\
                    +---> Shared Cache (Redis/Memcached) ---> Database (on miss)
  App Server B ---/
  Request 1 -> A -> shared cache MISS -> DB -> shared cache: {user:42}
  Request 2 -> B -> shared cache HIT (A's write is visible to B immediately)
```
*Caption: a shared cache makes one instance's cache population immediately visible to every other instance.*

## 5. Runnable example

**Level 1 — Basic.** Simulate two application instances each with their own local cache, showing they duplicate database load.

**Level 2 — Shared cache.** The same two instances now share one external cache, showing one instance's write becomes visible to the other.

**Level 3 — Network cost model.** Add a simulated cost per cache access, to compare total cost between the local and shared approaches.

```java
// SharedCacheProvider.java
import java.util.HashMap;
import java.util.Map;

public class SharedCacheProvider {

    static final Map<String, String> database = Map.of("user:42", "Alice");
    static int databaseHits = 0;

    static String queryDb(String key) {
        databaseHits++;
        return database.get(key);
    }

    // Level 1: each app instance has its own local, in-process cache.
    static final Map<String, String> localCacheA = new HashMap<>();
    static final Map<String, String> localCacheB = new HashMap<>();

    static String getViaLocalCache(Map<String, String> localCache, String key) {
        if (localCache.containsKey(key)) return localCache.get(key);
        String value = queryDb(key);
        localCache.put(key, value);
        return value;
    }

    // Level 2: one shared cache, standing in for Redis/Memcached, used by BOTH instances.
    static final Map<String, String> sharedCache = new HashMap<>();

    static String getViaSharedCache(String key) {
        if (sharedCache.containsKey(key)) return sharedCache.get(key);
        String value = queryDb(key);
        sharedCache.put(key, value);
        return value;
    }

    public static void main(String[] args) {
        // Level 1 & 3: two isolated local caches - server B repeats server A's database work.
        System.out.println("local cache A: " + getViaLocalCache(localCacheA, "user:42")); // miss
        System.out.println("local cache B: " + getViaLocalCache(localCacheB, "user:42")); // ALSO a miss
        System.out.println("database hits with local (per-instance) caches: " + databaseHits); // 2

        databaseHits = 0; // reset for the shared-cache comparison

        // Level 2: both "instances" now call the SAME shared cache.
        System.out.println("instance A via shared cache: " + getViaSharedCache("user:42")); // miss, populates shared
        System.out.println("instance B via shared cache: " + getViaSharedCache("user:42")); // HIT, A's write is visible
        System.out.println("database hits with a shared cache: " + databaseHits); // 1
    }
}
```

**How to run:** save as `SharedCacheProvider.java`, then run `java SharedCacheProvider.java`.

## 6. Walkthrough

1. `getViaLocalCache(localCacheA, "user:42")` misses (an empty `HashMap`), queries the database (`databaseHits` becomes `1`), and populates only `localCacheA`.
2. `getViaLocalCache(localCacheB, "user:42")` checks a completely separate map, `localCacheB`, which knows nothing about `localCacheA`'s write — it also misses, querying the database again (`databaseHits` becomes `2`).
3. This models exactly what happens with per-instance, in-process caches behind a load balancer: the same logical data gets fetched from the database once per instance, not once total.
4. After resetting the counter, `getViaSharedCache("user:42")` (standing in for "instance A") misses once, queries the database (`databaseHits` becomes `1`), and populates `sharedCache`.
5. `getViaSharedCache("user:42")` again (standing in for "instance B") now finds the entry already present in the *same* `sharedCache` map that "instance A" populated, so it returns a hit — `databaseHits` stays at `1`.
6. The comparison shows the exact benefit: a shared cache provider turns N instances' worth of duplicate database load, for the same popular key, into a single database query shared by all of them.

## 7. Gotchas & takeaways

> Gotcha: a shared cache is a new single point of failure and a new network hop — if Redis or Memcached goes down or becomes slow, every application instance loses its cache at once (unlike in-process caches, which fail independently), so production deployments typically run it as a highly available cluster, not a single instance.

- A shared cache is what makes patterns like cache-aside, write-through, and eviction policies actually work consistently across multiple application servers, not just within one process.
- Memcached is simpler and purely for caching; Redis trades a little simplicity for richer data structures and optional persistence, which is why it is the more common default choice today even for plain caching.
- Related concepts: [Spring Data Redis for distributed caching](0061-spring-data-redis-for-distributed-caching.md) (the Spring integration for using Redis as a `CacheManager` backend), [Hot keys & key distribution](0052-hot-keys-key-distribution.md) (a problem that appears specifically once a cache is shared and sharded across nodes).
