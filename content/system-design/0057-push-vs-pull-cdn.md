---
card: system-design
gi: 57
slug: push-vs-pull-cdn
title: Push vs pull CDN
---

## 1. What it is

A **pull Content Delivery Network (CDN)** fetches content from your origin server automatically, the first time an edge location needs it, and caches it there. A **push CDN** works the other way around: you (or your deployment pipeline) proactively upload content to the CDN ahead of time, before any user ever requests it.

## 2. Why & when

The two modes trade automation for control. Pull is the default for most CDNs, because it needs no extra deployment step — you just point the CDN at your origin, and it fills its cache on demand as real traffic asks for content. Push suits content you know in advance needs to be available everywhere immediately (a video release, a major app update) and where you cannot accept the "first request pays the origin trip" cost that pull CDNs have at each edge location.

## 3. Core concept

**Pull CDN behavior:** the first request for a URL at a given edge location is a cache miss; the edge server fetches it from the origin, caches it according to the response's TTL, and serves it. Every later request to that edge location, until the TTL expires, is served from cache. Different, less-visited edge locations independently repeat this same "first request pays" pattern the first time *they* see the URL.

**Push CDN behavior:** content is uploaded directly to the CDN's storage ahead of time, typically to every edge location or to a set of regional origins the CDN then distributes internally. There is no "first request is slow" moment, because the content is already present before any user asks for it.

**The core trade-off:** pull needs no extra upload step and naturally only caches what is actually requested, saving storage for content nobody wants. Push guarantees availability everywhere from the very first request, but requires you to manage uploads, and it can waste storage caching content nobody ends up requesting in some regions.

**A common hybrid:** many CDNs are pull-based by default but let you **pre-warm** specific high-value URLs by manually triggering a pull ahead of expected demand — giving pull's low operational overhead with push's "ready before the first user" guarantee for the handful of URLs that need it.

## 4. Diagram

```
PULL:
  Origin: content exists, CDN has not touched it yet
  User 1 request -> Edge PoP: MISS -> fetch from Origin -> cache -> serve  (slow, first time)
  User 2 request (same PoP) -> HIT -> serve from cache                    (fast)

PUSH:
  Deploy step: YOU upload content -> distributed to Edge PoPs BEFORE any user asks
  User 1 request -> Edge PoP: HIT immediately -> serve                    (fast, every time)
```
*Caption: pull pays the origin-fetch cost on the first request per PoP; push pays that cost upfront, during deployment, for every PoP at once.*

## 5. Runnable example

**Level 1 — Basic.** A pull-based simulation: an edge cache filled lazily on the first request.

**Level 2 — Push simulation.** A push-based simulation: content is uploaded to every edge location before any request arrives.

**Level 3 — Comparing first-request latency.** Count how many requests hit a cold cache under each mode across multiple edge locations.

```java
// PushVsPullCdn.java
import java.util.HashMap;
import java.util.Map;
import java.util.List;

public class PushVsPullCdn {

    static final Map<String, String> origin = Map.of("release-video.mp4", "video-bytes");
    static final List<String> edgeLocations = List.of("tokyo", "virginia", "frankfurt");

    // Level 1: pull CDN, each edge fills its own cache lazily on first request.
    static final Map<String, Map<String, String>> pullEdges = new HashMap<>();
    static int pullColdMisses = 0;

    static String pullRequest(String edge, String key) {
        Map<String, String> cache = pullEdges.computeIfAbsent(edge, e -> new HashMap<>());
        if (!cache.containsKey(key)) {
            pullColdMisses++; // this request pays the origin-fetch cost
            cache.put(key, origin.get(key));
        }
        return cache.get(key);
    }

    // Level 2: push CDN, uploaded to every edge location up front.
    static final Map<String, Map<String, String>> pushEdges = new HashMap<>();
    static int pushColdMisses = 0;

    static void pushUpload(String key) {
        for (String edge : edgeLocations) {
            pushEdges.computeIfAbsent(edge, e -> new HashMap<>()).put(key, origin.get(key));
        }
    }
    static String pushRequest(String edge, String key) {
        Map<String, String> cache = pushEdges.get(edge);
        if (cache == null || !cache.containsKey(key)) {
            pushColdMisses++; // should never happen if pushUpload already ran
        }
        return cache.get(key);
    }

    public static void main(String[] args) {
        // Level 3: first request from every edge location, under each mode.
        for (String edge : edgeLocations) {
            pullRequest(edge, "release-video.mp4");
        }
        System.out.println("PULL: cold misses across " + edgeLocations.size() + " edges = " + pullColdMisses);

        pushUpload("release-video.mp4"); // uploaded to all edges before any request
        for (String edge : edgeLocations) {
            pushRequest(edge, "release-video.mp4");
        }
        System.out.println("PUSH: cold misses across " + edgeLocations.size() + " edges = " + pushColdMisses);
    }
}
```

**How to run:** save as `PushVsPullCdn.java`, then run `java PushVsPullCdn.java`.

## 6. Walkthrough

1. The loop over `edgeLocations` calls `pullRequest` for each location; every one of them finds an empty per-edge cache (`computeIfAbsent` creates a fresh map), so all three are cold misses — `pullColdMisses` ends at `3`.
2. This models pull's behavior exactly: each independent edge location pays the origin-fetch cost the first time it, specifically, is asked for that content, regardless of what other edges have already cached.
3. `pushUpload("release-video.mp4")` runs before any request and iterates every edge location, populating each one's cache directly from `origin`.
4. The subsequent loop of `pushRequest` calls finds the content already present at every edge, so `pushColdMisses` stays at `0`.
5. The comparison shows the core trade directly: pull pays 3 cold misses spread across real user requests (each one a slow, user-visible delay); push pays that same cost upfront, during the deploy step, so no user ever experiences it.

## 7. Gotchas & takeaways

> Gotcha: a push CDN that uploads content nobody in a given region ever requests wastes storage and upload bandwidth on that region; pull naturally avoids this because it only ever caches what real traffic actually asked for.

- Pull is the operationally simpler default: no upload pipeline to maintain, and storage is only used for content that is actually popular in each region.
- Push guarantees zero cold-cache latency everywhere, at the cost of needing an explicit upload step for every piece of content, whether or not it turns out to be popular in every region.
- Related concepts: [How a CDN works (edge PoPs)](0056-how-a-cdn-works-edge-pops.md) (the underlying edge-caching mechanism both modes build on), [Cache-Control, ETag & conditional requests](0058-cache-control-etag-conditional-requests.md) (the headers that control TTL for pulled content).
