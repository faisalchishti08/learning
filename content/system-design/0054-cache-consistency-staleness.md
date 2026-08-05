---
card: system-design
gi: 54
slug: cache-consistency-staleness
title: Cache consistency & staleness
---

## 1. What it is

**Cache consistency** is how closely a cached value matches the current value in the database at any given moment. **Staleness** is the gap between them when they briefly disagree — a cached value that has not yet caught up with a more recent database write. Every cache accepts some staleness in exchange for speed; the design question is how much staleness is tolerable and for how long.

## 2. Why & when

A cache is, by definition, a second copy of data that can fall out of sync with the original. Understanding this trade-off matters because different data has very different tolerance for it: a product's star rating can be a few minutes stale with no real harm, but an account balance or an inventory count being stale can cause real problems (overselling, incorrect charges). The strategies covered elsewhere in this section — TTL, explicit invalidation, write-through — are all different ways of controlling how much staleness a system allows and for how long.

## 3. Core concept

**Where staleness comes from:** any time data is written to the database without also, atomically, updating every cached copy of it, a window opens where the cache is wrong. That window closes when the cache entry is invalidated, refreshed, or naturally expires.

**Strong-ish consistency, at a cost:** write-through caching (writing the database and cache together, synchronously) minimizes staleness for the writer's own reads, but it does nothing for other cache instances that hold their own copy, and it adds write latency. True strong consistency across a distributed cache generally requires coordination (e.g. cache invalidation broadcast, or reading straight from the database), which costs latency or throughput.

**Eventual consistency, the common default:** most caches accept **eventual consistency** — the cache will catch up to the database's true value at some point, bounded by the invalidation strategy in use (usually the TTL), but not instantly. This is the right default whenever a brief staleness window causes no real harm.

**Measuring the staleness window:** the maximum staleness a cache can produce is bounded by whichever invalidation mechanism is weakest. If a system relies purely on a 60-second TTL, then 60 seconds is the worst-case staleness window, full stop — no matter how fast explicit invalidation runs elsewhere, TTL sets the outer bound.

## 4. Diagram

```
t=0    Database write: balance = 100 -> 90
t=0    Cache still holds:  balance = 100        <- STALE from this instant
t=0..T Any read during this window sees the WRONG value (100, not 90)
t=T    Cache entry invalidated/expires/refreshes -> now holds 90
t=T+   Reads are correct again

  T = the staleness window; its maximum length is bounded by the
  weakest invalidation mechanism in use (often the TTL).
```
*Caption: staleness is the time between a database write and the cache catching up; every caching strategy is really a choice about how long, and how bounded, that window is.*

## 5. Runnable example

**Level 1 — Basic.** A cache and database that can independently disagree, with a method to check whether they currently match.

**Level 2 — Measuring the staleness window.** Track the tick at which the database changes and the tick at which the cache catches up, then compute the gap.

**Level 3 — Comparing strategies.** Compare the staleness window under a TTL-only strategy versus explicit invalidation on the same write.

```java
// CacheConsistency.java
import java.util.HashMap;
import java.util.Map;

public class CacheConsistency {

    static final Map<String, Integer> database = new HashMap<>();

    static class TtlEntry {
        int value; long expiresAtTick;
        TtlEntry(int value, long expiresAtTick) { this.value = value; this.expiresAtTick = expiresAtTick; }
    }

    // Level 1 & 2: TTL-only cache, no explicit invalidation on write.
    static final Map<String, TtlEntry> ttlOnlyCache = new HashMap<>();
    static final long ttl = 60;

    static Integer readTtlOnly(String key, long now) {
        TtlEntry e = ttlOnlyCache.get(key);
        if (e == null || now >= e.expiresAtTick) {
            int fresh = database.get(key);
            ttlOnlyCache.put(key, new TtlEntry(fresh, now + ttl));
            return fresh;
        }
        return e.value; // may be stale if database changed since e was stored
    }

    // Level 3: explicit invalidation, database write deletes the entry immediately.
    static final Map<String, Integer> explicitCache = new HashMap<>();
    static void writeExplicit(String key, int value, long now) {
        database.put(key, value);
        explicitCache.remove(key); // staleness window closes immediately
    }
    static Integer readExplicit(String key) {
        Integer cached = explicitCache.get(key);
        if (cached == null) {
            cached = database.get(key);
            explicitCache.put(key, cached);
        }
        return cached;
    }

    public static void main(String[] args) {
        database.put("balance:acct1", 100);

        long writeTick = 10;
        System.out.println("TTL cache, initial read at t=0: " + readTtlOnly("balance:acct1", 0)); // 100, caches until t=60

        database.put("balance:acct1", 90); // write happens at t=10, TTL cache does not know yet
        System.out.println("TTL cache, read at t=" + writeTick + " right after write (STALE): " + readTtlOnly("balance:acct1", writeTick));
        System.out.println("TTL cache, read at t=59 (still STALE): " + readTtlOnly("balance:acct1", 59));
        System.out.println("TTL cache, read at t=60 (expired, now correct): " + readTtlOnly("balance:acct1", 60));
        System.out.println("TTL staleness window length: " + (60 - writeTick) + " ticks");

        database.put("balance:acct2", 100);
        explicitCache.put("balance:acct2", readExplicit("balance:acct2")); // warm the cache
        writeExplicit("balance:acct2", 90, writeTick); // write + invalidate together
        System.out.println("explicit cache, read right after write: " + readExplicit("balance:acct2")); // correct immediately
    }
}
```

**How to run:** save as `CacheConsistency.java`, then run `java CacheConsistency.java`.

## 6. Walkthrough

1. `readTtlOnly("balance:acct1", 0)` misses, loads `100` from `database`, and caches it with `expiresAtTick = 60`.
2. `database.put("balance:acct1", 90)` changes the true value at `t=10`, but nothing tells `ttlOnlyCache` — it still holds the old entry with `expiresAtTick = 60`.
3. Reading at `t=10` and again at `t=59` both return the stale `100`, because `now < 60` in both cases, so the TTL entry is still considered valid even though it is wrong.
4. Reading at `t=60` finally sees `now >= expiresAtTick`, triggers a reload, and returns the correct `90` — the staleness window lasted exactly `60 - 10 = 50` ticks.
5. For `balance:acct2`, `writeExplicit` updates the database and removes the cache entry in the same call, at `t=10`; the very next read misses, reloads, and returns `90` immediately — a staleness window of effectively zero.

## 7. Gotchas & takeaways

> Gotcha: explicit invalidation only closes the staleness window for the cache the writer directly touches; in a system with multiple cache instances, each one still needs its own invalidation path (see event-based invalidation), or it stays stale exactly as long as a TTL-only cache would.

- Staleness is not a bug to eliminate; it is a parameter to bound deliberately, based on how much a wrong read actually costs for that specific data.
- The worst-case staleness window is set by the weakest invalidation mechanism protecting a key, not the strongest one.
- Related concepts: [Cache invalidation strategies](0051-cache-invalidation-strategies.md) (the mechanisms that bound staleness), [Write-through cache](0047-write-through-cache.md) (minimizes staleness for the writer's own subsequent reads).
