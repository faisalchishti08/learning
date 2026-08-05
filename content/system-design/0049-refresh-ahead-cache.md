---
card: system-design
gi: 49
slug: refresh-ahead-cache
title: Refresh-ahead cache
---

## 1. What it is

A **refresh-ahead cache** proactively reloads a cache entry from the database shortly before it expires, in the background, instead of waiting for a request to arrive after expiry and forcing that unlucky caller to pay the full database-lookup cost.

## 2. Why & when

Every time-to-live (TTL) based cache has the same problem: the request that happens to arrive right after an entry expires gets a slow response, because it triggers a synchronous reload. Refresh-ahead removes that penalty for frequently accessed keys by refreshing them just before they expire, so almost every request — including the one that would otherwise have caused the reload — sees a cache hit. Use it for hot keys with predictable, frequent access, where the extra background work is worth eliminating tail latency.

## 3. Core concept

**The refresh trigger:** each entry is stored with an expiry time. Refresh-ahead defines a threshold — for example, "when 75% of an entry's TTL has elapsed" — and, when a read for that entry crosses the threshold, the cache serves the still-valid cached value immediately but also kicks off a background reload to refresh it before it actually expires.

**Why this differs from a plain TTL cache:** a plain TTL cache lets an entry go fully stale and only reloads it on the next request after expiry, so that request pays full database latency. Refresh-ahead shifts the reload earlier, off the request path entirely, so the entry is fresh again well before it would have expired.

**The trade-off:** refresh-ahead only pays off for keys that keep getting read; if a key is refreshed ahead of time but then never read again before its new expiry, the refresh was wasted work. It is a poor fit for cold or rarely accessed keys.

## 4. Diagram

```
TTL = 100ms, refresh threshold = 75ms

  t=0 ----------------- t=75 ------------- t=100
  entry stored          READ HERE:          (plain TTL: entry
                         value still valid,   would expire here,
                         age >= threshold,    forcing a slow
                         so a BACKGROUND      synchronous reload
                         refresh starts       on the next read)
                         now, ahead of time

  Result with refresh-ahead: entry is renewed before t=100, so requests
  right after t=100 still hit a fresh cached value, not a slow reload.
```
*Caption: crossing the refresh threshold triggers a background reload, so the entry never actually goes stale under steady traffic.*

## 5. Runnable example

**Level 1 — Basic.** An entry with a TTL and an "age" tracked via a logical clock, read normally.

**Level 2 — Threshold check.** A `get` that detects when an entry has crossed the refresh threshold and reloads it in place before returning.

**Level 3 — Comparing costs.** Count reload calls under refresh-ahead versus a plain TTL cache to show the tail-latency reload is avoided.

```java
// RefreshAheadCache.java
import java.util.HashMap;
import java.util.Map;

public class RefreshAheadCache {

    static final Map<String, String> database = new HashMap<>();
    static int reloadsOnRequestPath = 0; // reloads that a real caller had to wait on

    static class Entry {
        String value;
        int storedAtTick;
        Entry(String value, int storedAtTick) { this.value = value; this.storedAtTick = storedAtTick; }
    }

    static final Map<String, Entry> cache = new HashMap<>();
    static final int ttl = 100;
    static final int refreshThreshold = 75; // refresh once age crosses this

    static String reload(String key) {
        return database.get(key); // stands in for a real database query
    }

    // Level 1 & 2: refresh-ahead get, using a logical clock "now".
    static String get(String key, int now) {
        Entry entry = cache.get(key);
        if (entry == null) {
            reloadsOnRequestPath++; // cold start: caller waits
            String value = reload(key);
            cache.put(key, new Entry(value, now));
            return value;
        }
        int age = now - entry.storedAtTick;
        if (age >= ttl) {
            reloadsOnRequestPath++; // fully expired: caller waits (the case refresh-ahead avoids)
            String value = reload(key);
            cache.put(key, new Entry(value, now));
            return value;
        }
        if (age >= refreshThreshold) {
            // still valid: serve immediately, refresh happens "in the background" (simulated inline here)
            String value = reload(key);
            cache.put(key, new Entry(value, now));
            return entry.value; // caller gets the still-fresh old value, not a wait
        }
        return entry.value; // well within TTL: plain hit
    }

    public static void main(String[] args) {
        database.put("trending:topics", "v1");

        System.out.println(get("trending:topics", 0)); // cold start
        System.out.println(get("trending:topics", 50)); // hit, before threshold

        database.put("trending:topics", "v2");
        System.out.println(get("trending:topics", 80)); // past threshold: background-style refresh, still fast
        System.out.println(get("trending:topics", 90)); // now sees v2, still no request-path wait

        System.out.println("reloads on the request path (caller had to wait): " + reloadsOnRequestPath);
    }
}
```

**How to run:** save as `RefreshAheadCache.java`, then run `java RefreshAheadCache.java`.

## 6. Walkthrough

1. `get("trending:topics", 0)` finds no entry, so it reloads (`reloadsOnRequestPath` becomes `1`) and stores `"v1"` with `storedAtTick = 0`.
2. `get("trending:topics", 50)` computes `age = 50`, below the `75` threshold, so it returns `"v1"` directly — a plain hit.
3. The database is updated to `"v2"`, simulating new data arriving.
4. `get("trending:topics", 80)` computes `age = 80`, past the threshold but under the `100` TTL, so it still returns the old cached value `"v1"` to the caller immediately, while also reloading and re-storing the entry with the fresh value and a new `storedAtTick = 80`.
5. `get("trending:topics", 90)` now sees the refreshed entry (`age = 10`, well under threshold) and returns `"v2"` — the newer value — without the caller ever having waited on a synchronous reload.
6. `reloadsOnRequestPath` stays at `1` for the whole run: only the very first, cold-start call actually forced a caller to wait on `reload`.

## 7. Gotchas & takeaways

> Gotcha: refresh-ahead only triggers on a read that happens to land after the threshold; if traffic to a key stops entirely, nothing refreshes it, and the entry simply expires like a plain TTL entry on the next request.

- Refresh-ahead eliminates the "unlucky request right after expiry pays full latency" problem, but only for keys that keep receiving reads.
- It adds background load (extra database reads) in exchange for smoother tail latency — a poor trade for cold or rarely read keys.
- Related concepts: [Eviction policies (LRU, LFU, FIFO, TTL)](0050-eviction-policies-lru-lfu-fifo-ttl.md) (TTL is the baseline this pattern improves on), [Thundering herd / cache stampede & mitigation](0053-thundering-herd-cache-stampede-mitigation.md) (a related problem when many keys expire and reload at once).
