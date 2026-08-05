---
card: system-design
gi: 56
slug: how-a-cdn-works-edge-pops
title: "How a CDN works (edge PoPs)"
---

## 1. What it is

A **Content Delivery Network (CDN)** is a geographically distributed network of servers that cache and serve content from locations physically close to users, instead of every user's request traveling all the way to one origin server. Each of these locations is called a **Point of Presence (PoP)**, or an **edge** location, because it sits at the edge of the network, nearest to users.

## 2. Why & when

Network latency is bounded by physical distance — a request from Tokyo to a server in Virginia takes meaningfully longer than one to a server in Tokyo, no matter how fast the origin server itself is. A CDN removes that distance for cacheable content by keeping copies at PoPs all over the world, so a user's request only has to travel to the nearest PoP, not across the planet. Use a CDN for anything that does not change per-request: images, video, CSS, JavaScript bundles, and any API response that is the same for many users at once.

## 3. Core concept

**Anycast routing to the nearest PoP:** a CDN typically uses DNS or anycast IP routing so that when a user requests `cdn.example.com`, they are automatically routed to whichever PoP is network-closest to them, without the user or the application needing to know which physical server actually answers.

**Cache hit at the edge:** if the requested content is already cached at that PoP (because another nearby user requested it recently), the PoP serves it directly — the origin server is never contacted, and the response is as fast as the user's distance to that PoP allows.

**Cache miss and origin pull:** if the PoP does not have the content cached (a **cold** PoP for that URL, or the cached copy expired), it fetches it from the **origin server** — your actual application or storage — caches a copy locally, and then serves it. This is why a piece of content is often slower on its very first request to a given region, then fast afterward.

**TTL and purging:** each cached object at the edge has a TTL, set by `Cache-Control` headers from the origin. When content changes before its TTL expires, you must explicitly **purge** (invalidate) the CDN's cached copy, or users keep seeing the old version until it naturally expires.

## 4. Diagram

```
User in Tokyo requests https://cdn.example.com/logo.png
        |
        v
  Anycast/DNS routes to nearest PoP: Tokyo edge server
        |
        +-- CACHE HIT (logo.png already cached here)
        |       -> served directly from Tokyo PoP, origin never contacted
        |
        +-- CACHE MISS (not cached, or expired)
                -> Tokyo PoP fetches from Origin server (e.g. in Virginia)
                -> Tokyo PoP caches a copy locally
                -> serves it to the user
                -> the NEXT Tokyo-area user requesting logo.png gets a cache hit
```
*Caption: only the first request in a region pays the full trip to the origin; every subsequent nearby request is served from that region's edge PoP.*

## 5. Runnable example

**Level 1 — Basic.** Simulate several PoPs, each with its own local cache, and one shared origin.

**Level 2 — Routing to the nearest PoP.** Route each simulated user to the PoP matching their region, showing the cache is local per-PoP, not global.

**Level 3 — TTL and purge.** Show a cached object expiring by TTL, and an explicit purge forcing an immediate re-fetch from origin.

```java
// CdnEdgePops.java
import java.util.HashMap;
import java.util.Map;

public class CdnEdgePops {

    static final Map<String, String> origin = Map.of("logo.png", "logo-bytes-v1");
    static int originFetches = 0;

    static class CachedObject {
        String value; long expiresAtTick;
        CachedObject(String value, long expiresAtTick) { this.value = value; this.expiresAtTick = expiresAtTick; }
    }

    // Level 1: each PoP is an independent cache keyed by region.
    static final Map<String, Map<String, CachedObject>> pops = new HashMap<>();
    static final long ttl = 100;

    static String requestFromRegion(String region, String key, long now) {
        Map<String, CachedObject> pop = pops.computeIfAbsent(region, r -> new HashMap<>());
        CachedObject cached = pop.get(key);
        if (cached != null && now < cached.expiresAtTick) {
            return cached.value; // edge cache hit: origin never contacted
        }
        // miss (cold PoP, or TTL expired): pull from origin
        originFetches++;
        String value = origin.get(key);
        pop.put(key, new CachedObject(value, now + ttl));
        return value;
    }

    static void purge(String region, String key) {
        Map<String, CachedObject> pop = pops.get(region);
        if (pop != null) pop.remove(key); // force next request in this region to re-fetch
    }

    public static void main(String[] args) {
        // Level 2: two regions, each with independent edge caches.
        System.out.println("tokyo user 1, t=0: " + requestFromRegion("tokyo", "logo.png", 0)); // cold PoP, origin pull
        System.out.println("tokyo user 2, t=1: " + requestFromRegion("tokyo", "logo.png", 1)); // hit, no origin pull
        System.out.println("virginia user 1, t=1: " + requestFromRegion("virginia", "logo.png", 1)); // different PoP, still cold
        System.out.println("origin fetches so far: " + originFetches); // 2, one per region's first request

        // Level 3: TTL expiry forces a re-fetch even in a warm region.
        System.out.println("tokyo user 3, t=150 (TTL expired): " + requestFromRegion("tokyo", "logo.png", 150));
        System.out.println("origin fetches after TTL expiry: " + originFetches); // 3

        // Level 3: explicit purge forces an immediate re-fetch, ignoring remaining TTL.
        requestFromRegion("virginia", "logo.png", 160); // re-warm virginia's TTL window
        purge("virginia", "logo.png");
        System.out.println("virginia user 2, right after purge: " + requestFromRegion("virginia", "logo.png", 161));
        System.out.println("total origin fetches: " + originFetches);
    }
}
```

**How to run:** save as `CdnEdgePops.java`, then run `java CdnEdgePops.java`.

## 6. Walkthrough

1. The first Tokyo request at `t=0` finds no entry in the `tokyo` PoP's map, so it is a cold-PoP miss: `originFetches` becomes `1`, and the Tokyo PoP caches the value with `expiresAtTick = 100`.
2. The second Tokyo request at `t=1` finds the cached entry, and `now=1 < 100`, so it is served directly from the edge — `originFetches` stays at `1`.
3. The Virginia request is checked against a completely separate map (`pops.get("virginia")`), which has never been populated, so it is also a cold-PoP miss — proving PoP caches are independent per region, not shared globally.
4. At `t=150`, Tokyo's cached entry has `expiresAtTick = 100`, and `150 >= 100`, so it is treated as expired; the request falls through to `origin` again, incrementing `originFetches` to `3`.
5. `purge("virginia", "logo.png")` removes Virginia's cached entry directly, regardless of its remaining TTL; the very next Virginia request at `t=161` therefore misses and re-fetches from `origin`, even though it had just been re-cached at `t=160` with a TTL that would otherwise last until `t=260`.

## 7. Gotchas & takeaways

> Gotcha: a purge only clears the PoP(s) you target; a global CDN purge that has to propagate to every PoP worldwide is not instantaneous, so users in different regions can briefly see different versions of the same content right after a purge is issued.

- The first request to any given region always pays the full trip to the origin; every subsequent nearby request, until the TTL expires, is served from that region's edge.
- Correct `Cache-Control` headers from the origin (setting the right TTL) matter as much as the CDN itself — too long a TTL delays users seeing updates, too short a TTL sends unnecessary traffic back to the origin.
- Related concepts: [Client / CDN / application / database cache layers](0055-client-cdn-application-database-cache-layers.md) (where the CDN sits in the full caching chain), [Global server load balancing (GeoDNS, anycast)](0036-global-server-load-balancing-geodns-anycast.md) (the routing mechanism that sends users to their nearest PoP).
