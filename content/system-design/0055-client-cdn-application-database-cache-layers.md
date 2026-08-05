---
card: system-design
gi: 55
slug: client-cdn-application-database-cache-layers
title: "Client / CDN / application / database cache layers"
---

## 1. What it is

Real systems rarely cache in just one place. A request typically passes through several **cache layers**, each catching a different fraction of traffic: the **client cache** (browser or mobile app, on the user's own device), the **Content Delivery Network (CDN)** cache (at edge locations near the user), the **application cache** (in-process or a shared cache like Redis, close to the application servers), and the **database cache** (the database engine's own internal buffer of recently used data).

## 2. Why & when

Each layer is progressively closer to the origin database and progressively more expensive to serve from. A request that stops at the client cache costs nothing — no network trip at all. One that reaches the CDN costs a short trip to a nearby edge server. One that reaches the application cache costs a trip to your own servers. One that reaches the database costs the most: a full query on the most contended, hardest-to-scale layer. Combining layers means only the requests that truly need fresh or uncached data pay the full cost, and every layer above it absorbs everything it can first.

## 3. Core concept

**Client cache:** controlled by HTTP caching headers (`Cache-Control`, `ETag`) or app-level storage. It serves repeat requests from the exact same device with zero network trip at all — the fastest possible cache, but only useful to that one user.

**CDN cache:** a network of edge servers geographically distributed near users. It caches responses (especially static assets — images, CSS, JavaScript — but also cacheable API responses) so many different users near the same location share one cached copy, without any request reaching your origin servers at all.

**Application cache:** an in-memory store (in-process, or a shared service like Redis or Memcached) that your application servers check before querying the database. This is where the patterns in this section — cache-aside, write-through, eviction policies — most directly apply.

**Database cache:** the database engine itself keeps a buffer pool of recently accessed pages in memory, so even a "cache miss" at the application layer might still be served from the database's own memory rather than hitting disk.

**The funnel effect:** each layer only has to handle the traffic the layer before it did not absorb. A well-tuned CDN can eliminate 90%+ of requests for static content before they ever reach the application; a well-tuned application cache can eliminate most of the rest before they reach the database.

## 4. Diagram

```
User's browser
   |  1. check CLIENT cache (local, zero network) -- HIT: done, fastest path
   v  MISS
CDN edge server (near the user)
   |  2. check CDN cache -- HIT: return from edge, origin never contacted
   v  MISS
Application server
   |  3. check APPLICATION cache (Redis / in-process) -- HIT: return, no query
   v  MISS
Database
   |  4. check DATABASE's own buffer pool (in memory) -- HIT: served from memory
   v  MISS
   Read from disk  (the slowest, most expensive path -- reached only when
                     every layer above missed)
```
*Caption: each layer only serves the traffic the layer before it could not absorb; the request only reaches disk when all four layers miss.*

## 5. Runnable example

**Level 1 — Basic.** Simulate the four layers as nested lookups, with a cost counter per layer.

**Level 2 — Populating on miss.** Each layer that misses populates itself from the layer below, exactly like a chain of read-through caches.

**Level 3 — Layer effectiveness.** Run many requests through the chain and report what fraction each layer absorbed.

```java
// CacheLayers.java
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public class CacheLayers {

    static final Map<String, String> database = Map.of("home:hero-image", "image-bytes");

    static final Map<String, String> clientCache = new HashMap<>();
    static final Map<String, String> cdnCache = new HashMap<>();
    static final Map<String, String> appCache = new HashMap<>();

    static int clientHits = 0, cdnHits = 0, appHits = 0, databaseHits = 0;

    // Level 1 & 2: each layer checks itself, then falls through and populates on miss.
    static String fetch(String key) {
        if (clientCache.containsKey(key)) { clientHits++; return clientCache.get(key); }

        if (cdnCache.containsKey(key)) {
            cdnHits++;
            String value = cdnCache.get(key);
            clientCache.put(key, value); // client learns it too, for next time
            return value;
        }

        if (appCache.containsKey(key)) {
            appHits++;
            String value = appCache.get(key);
            cdnCache.put(key, value);
            clientCache.put(key, value);
            return value;
        }

        // final fallback: the database (the "disk" layer, most expensive)
        databaseHits++;
        String value = database.get(key);
        appCache.put(key, value);
        cdnCache.put(key, value);
        clientCache.put(key, value);
        return value;
    }

    public static void main(String[] args) {
        // Level 3: 100 "different users" request the same popular key.
        // Only the CLIENT cache is per-user, so simulate a fresh client each time,
        // but a SHARED cdnCache and appCache (as real infrastructure would be).
        int users = 100;
        for (int i = 0; i < users; i++) {
            clientCache.clear(); // new device: nothing cached locally yet
            fetch("home:hero-image");
        }

        System.out.println("client hits (would only ever be >0 on repeat visits by the SAME user): " + clientHits);
        System.out.println("cdn hits: " + cdnHits);
        System.out.println("application cache hits: " + appHits);
        System.out.println("database hits: " + databaseHits);
    }
}
```

**How to run:** save as `CacheLayers.java`, then run `java CacheLayers.java`.

## 6. Walkthrough

1. The first simulated user calls `fetch("home:hero-image")`; `clientCache` is empty (fresh device), `cdnCache` is empty (nothing cached at the edge yet), and `appCache` is empty too, so it falls all the way through to `database`, incrementing `databaseHits`, and populates `appCache`, `cdnCache`, and `clientCache` on the way back up.
2. The second simulated user clears their own `clientCache` (a different device) but shares the same `cdnCache` and `appCache` as before — this models the CDN and application cache being shared infrastructure, while the client cache is per-device.
3. That second user's `fetch` misses `clientCache` (empty for this "device") but hits `cdnCache`, which was populated by the first user — `cdnHits` increments, and the value is copied into this user's `clientCache` and returned, without touching `appCache` or `database` at all.
4. Every subsequent simulated user follows the same path: miss at the (per-user) client layer, hit at the shared CDN layer.
5. The final counts show `databaseHits = 1` and `cdnHits = 99` — only the very first request of all 100 ever reached the database; the CDN absorbed everything after that.

## 7. Gotchas & takeaways

> Gotcha: because each layer independently decides when to invalidate, they can disagree — a CDN edge server might still serve an old version of a page for minutes after the application cache and database have both moved on, unless you explicitly purge the CDN (or set its cache duration much shorter) on that kind of update.

- Each layer should have its own appropriate TTL: client and CDN caches often hold static assets for a long time (with the URL itself changed to bust the cache on deploy), while the application cache holds more dynamic data for a much shorter window.
- Debugging "why am I seeing stale data" in a multi-layer system means checking each layer in order, from the client inward, since any one of them can be the culprit.
- Related concepts: [How a CDN works (edge PoPs)](0056-how-a-cdn-works-edge-pops.md) (a closer look at the CDN layer specifically), [Cache consistency & staleness](0054-cache-consistency-staleness.md) (the staleness question, now multiplied across every layer).
