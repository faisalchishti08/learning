---
card: microservices
gi: 247
slug: steady-state-limited-resources
title: "Steady-state & limited resources"
---

## 1. What it is

Steady state is the stability pattern of ensuring a long-running process's resource usage (memory, disk, connections, cache entries) stays bounded and stable over time — rather than growing indefinitely — by proactively cleaning up, rotating, or capping resources as part of normal operation, so a process can run indefinitely without needing periodic restarts just to reclaim leaked or accumulated resources.

## 2. Why & when

A process that grows unboundedly (an ever-growing in-memory cache with no eviction, log files never rotated, database connections opened but never closed) will eventually exhaust whatever resource it's consuming — memory, disk space, a connection pool's limit — no matter how healthy the rest of the system is. This kind of failure is often *slow*, developing over hours or days, which makes it easy to miss in short-lived testing and painful in production, since a service that worked fine for a week can suddenly start failing with no code change nearby, purely from accumulated resource growth finally crossing a limit. Steady-state design proactively bounds this growth — a cache with a maximum size and eviction policy, log rotation, connection pools with defined limits and leak detection — so the process's resource footprint plateaus rather than climbing indefinitely.

Design for steady state in any long-running process holding any kind of accumulating resource — nearly universal for a production service. A short-lived batch job that exits shortly after starting has much less exposure to this risk, since it never runs long enough for slow accumulation to matter.

## 3. Core concept

Steady state is achieved by pairing every resource-acquiring operation with a bounded lifecycle — a maximum size with an eviction policy for a cache, an explicit release for every acquired connection, a rotation policy for anything written continuously — so the resource's total footprint has a defined ceiling rather than growing without limit as the process runs longer.

```java
// WITHOUT steady state -- an UNBOUNDED cache that grows FOREVER as new keys are added
Map<String, Object> cache = new HashMap<>(); // NO eviction, NO size limit -- grows until memory is exhausted

// WITH steady state -- a BOUNDED cache with an EXPLICIT eviction policy
Cache<String, Object> boundedCache = Caffeine.newBuilder()
    .maximumSize(10_000) // a HARD ceiling on entry count
    .expireAfterWrite(Duration.ofMinutes(30)) // entries AGE OUT, even if under the size limit
    .build();
// this cache's memory footprint PLATEAUS -- it CANNOT grow beyond its defined bounds, no matter how long the process runs
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unbounded resource's usage climbs continuously over the process's uptime with no ceiling, eventually exhausting available capacity; a resource designed for steady state climbs initially but plateaus at a defined bound, remaining stable indefinitely" >
  <line x1="40" y1="140" x2="40" y2="20" stroke="#8b949e"/>
  <line x1="40" y1="140" x2="600" y2="140" stroke="#8b949e"/>
  <text x="20" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">usage</text>
  <text x="580" y="155" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">uptime</text>

  <path d="M 40 140 L 200 100 L 360 55 L 520 15" stroke="#8b949e" fill="none" stroke-width="1.5"/>
  <text x="500" y="30" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">unbounded -- climbs forever</text>

  <path d="M 40 140 L 150 95 L 260 75 L 600 72" stroke="#6db33f" fill="none" stroke-width="2"/>
  <text x="500" y="90" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">steady state -- plateaus at a bound</text>
</svg>

Bounded resources plateau at a defined ceiling; unbounded resources climb until something eventually breaks.

## 5. Runnable example

Scenario: a request-handling cache that starts unbounded (growing without limit as new keys accumulate over a simulated long uptime), refactored to a size-bounded cache with eviction that plateaus, and finally adding time-based expiration alongside the size bound so stale entries are proactively cleaned up even before the size limit is reached, matching a real steady-state cache configuration's dual bounding strategy.

### Level 1 — Basic

```java
// File: UnboundedGrowth.java -- a cache with NO size limit; simulating a
// long-running process reveals its usage climbing WITHOUT BOUND.
import java.util.*;

public class UnboundedGrowth {
    static Map<String, String> cache = new HashMap<>(); // UNBOUNDED

    static void handleRequest(String key) {
        cache.putIfAbsent(key, "cached-value-for-" + key); // NEVER evicted, EVER
    }

    public static void main(String[] args) {
        // simulate a LONG-running process handling MANY distinct requests over time
        for (int hour = 1; hour <= 5; hour++) {
            for (int i = 0; i < 1000; i++) handleRequest("key-" + (hour * 1000 + i)); // 1000 NEW distinct keys per "hour"
            System.out.println("After simulated hour " + hour + ": cache size = " + cache.size());
        }
        System.out.println("Cache size climbs WITHOUT BOUND -- eventually exhausts available memory.");
    }
}
```

**How to run:** `javac UnboundedGrowth.java && java UnboundedGrowth` (JDK 17+).

Expected output:
```
After simulated hour 1: cache size = 1000
After simulated hour 2: cache size = 2000
After simulated hour 3: cache size = 3000
After simulated hour 4: cache size = 4000
After simulated hour 5: cache size = 5000
Cache size climbs WITHOUT BOUND -- eventually exhausts available memory.
```

### Level 2 — Intermediate

```java
// File: SizeBoundedSteadyState.java -- a SIZE-BOUNDED cache with a simple
// eviction policy (evict OLDEST when at capacity) -- usage PLATEAUS.
import java.util.*;

public class SizeBoundedSteadyState {
    static final int MAX_SIZE = 2000; // a HARD ceiling
    static LinkedHashMap<String, String> cache = new LinkedHashMap<>(16, 0.75f, false) {
        protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
            return size() > MAX_SIZE; // EVICT the oldest entry once over the limit
        }
    };

    static void handleRequest(String key) {
        cache.putIfAbsent(key, "cached-value-for-" + key); // BOUNDED -- old entries evicted as new ones arrive
    }

    public static void main(String[] args) {
        for (int hour = 1; hour <= 5; hour++) {
            for (int i = 0; i < 1000; i++) handleRequest("key-" + (hour * 1000 + i));
            System.out.println("After simulated hour " + hour + ": cache size = " + cache.size());
        }
        System.out.println("Cache size PLATEAUS at " + MAX_SIZE + " -- stable regardless of how long the process runs.");
    }
}
```

**How to run:** `javac SizeBoundedSteadyState.java && java SizeBoundedSteadyState` (JDK 17+).

Expected output:
```
After simulated hour 1: cache size = 1000
After simulated hour 2: cache size = 2000
After simulated hour 3: cache size = 2000
After simulated hour 4: cache size = 2000
After simulated hour 5: cache size = 2000
Cache size PLATEAUS at 2000 -- stable regardless of how long the process runs.
```

### Level 3 — Advanced

```java
// File: SizeAndTimeBoundedSteadyState.java -- adds TIME-based expiration
// ALONGSIDE the size bound: entries are proactively cleaned up once
// STALE, even before the size limit is reached -- matching a REAL
// production cache's dual bounding strategy (e.g. Caffeine's).
import java.util.*;

public class SizeAndTimeBoundedSteadyState {
    static final int MAX_SIZE = 2000;
    static final long TTL_MILLIS = 100; // entries older than this are STALE, regardless of size pressure

    record Entry(String value, long insertedAt) {}
    static LinkedHashMap<String, Entry> cache = new LinkedHashMap<>(16, 0.75f, false) {
        protected boolean removeEldestEntry(Map.Entry<String, Entry> eldest) { return size() > MAX_SIZE; }
    };

    static void evictExpiredEntries(long now) { // PROACTIVE time-based cleanup, independent of the size bound
        cache.entrySet().removeIf(e -> now - e.getValue().insertedAt() > TTL_MILLIS);
    }

    static void handleRequest(String key, long now) {
        evictExpiredEntries(now); // clean up STALE entries on every request, not just when the size limit is hit
        cache.putIfAbsent(key, new Entry("cached-value-for-" + key, now));
    }

    public static void main(String[] args) throws InterruptedException {
        long t0 = System.currentTimeMillis();
        for (int i = 0; i < 500; i++) handleRequest("key-" + i, t0); // 500 entries, all inserted "at once"
        System.out.println("Immediately after 500 requests: cache size = " + cache.size());

        Thread.sleep(150); // let the TTL (100ms) pass -- these 500 entries are now STALE

        handleRequest("key-new", System.currentTimeMillis()); // a SINGLE new request triggers proactive cleanup
        System.out.println("After TTL passed and ONE new request: cache size = " + cache.size());
        System.out.println("The stale 500 entries were evicted by TIME, not just by hitting the SIZE limit.");
    }
}
```

**How to run:** `javac SizeAndTimeBoundedSteadyState.java && java SizeAndTimeBoundedSteadyState` (JDK 17+).

Expected output:
```
Immediately after 500 requests: cache size = 500
After TTL passed and ONE new request: cache size = 1
The stale 500 entries were evicted by TIME, not just by hitting the SIZE limit.
```

## 6. Walkthrough

1. **Level 1, the unbounded climb** — `cache` is a plain `HashMap` with no size limit or eviction logic anywhere; each simulated "hour" adds 1000 genuinely new keys, and `cache.size()` grows by exactly 1000 every time, with no mechanism anywhere in this program that could ever cause it to stop growing — over a real, much longer uptime, this is exactly the pattern that eventually exhausts available memory.
2. **Level 2, a size ceiling with eviction** — `SizeBoundedSteadyState`'s `LinkedHashMap` overrides `removeEldestEntry` to return `true` once the map exceeds `MAX_SIZE`, which `LinkedHashMap` then uses to automatically evict its oldest entry on every insertion past that point.
3. **Level 2, the plateau observed** — the printed sizes climb to `2000` by hour 2 and then stay flat at `2000` for every subsequent hour, even though 1000 more genuinely new keys are added each hour — the eviction policy is actively discarding the oldest entries to keep the total bounded, exactly the steady-state behavior a long-running process needs.
4. **Level 3, adding a second, independent bounding dimension** — `evictExpiredEntries` removes any entry older than `TTL_MILLIS`, entirely independent of whether the cache is anywhere near its `MAX_SIZE` limit; this models a real production cache's common dual strategy of bounding by *both* size and age, since a cache that's well under its size limit can still be holding entries that are simply too old to be useful or trustworthy.
5. **Level 3, staleness caught before the size limit is even relevant** — 500 entries are inserted at time `t0`, well under `MAX_SIZE` (2000), so the size-based eviction from Level 2 would never trigger on its own; but after `Thread.sleep(150)` passes the 100ms TTL, those 500 entries become stale purely by age.
6. **Level 3, proactive cleanup on the next access** — `handleRequest` calls `evictExpiredEntries` at the *start* of every call, before performing its own insertion; so the very next request after the TTL has passed triggers removal of all 500 now-stale entries, leaving only the one freshly inserted entry — demonstrating that steady state isn't only about capping a resource's maximum size, but also about proactively reclaiming resources that have simply outlived their usefulness, independent of whether size pressure alone would have caught them.

## 7. Gotchas & takeaways

> **Gotcha:** eviction and expiration policies themselves have a cost — checking every entry's age on every request (as `evictExpiredEntries` does here, in a simplified form) can become a real overhead at scale; production cache libraries like Caffeine implement expiration far more efficiently (amortized, batched cleanup) than a naive full-scan check on every access, which is why reaching for a well-tested caching library is usually preferable to hand-rolling steady-state logic for anything beyond a small, simple case.

- Steady state means a long-running process's resource usage (memory, connections, disk) stays bounded over time, rather than growing without limit as the process keeps running.
- Unbounded resource growth is a slow-developing failure mode — a process can run fine for a long time before finally exhausting a limit, making it easy to miss until it becomes a real production incident.
- Bounding by size (a maximum entry count with an eviction policy) and bounding by time (expiring entries after a fixed age) are two independent, complementary strategies, often combined in real production caches.
- Time-based expiration catches staleness that a size limit alone wouldn't — a cache well under its size ceiling can still be holding entries that are simply too old to be trustworthy.
- Hand-rolled eviction/expiration logic (as shown here for illustration) has real performance costs at scale; production-grade caching libraries implement these mechanisms far more efficiently and are generally preferable to a custom implementation.
