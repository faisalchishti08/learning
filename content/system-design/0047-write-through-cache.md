---
card: system-design
gi: 47
slug: write-through-cache
title: Write-through cache
---

## 1. What it is

A **write-through cache** writes every update to the cache and the database together, as one operation, before the write is considered complete. The cache is never allowed to hold a value the database does not also have, because both are updated synchronously on every write.

## 2. Why & when

Write-through keeps the cache always consistent with the database and always warm for the data your application actually writes, so reads right after a write are guaranteed to hit the cache with fresh data. Use it when read-after-write consistency matters — a user editing their own profile and immediately viewing it — and when the extra write latency (waiting on both the cache and the database) is acceptable. It trades write latency for read safety and read speed.

## 3. Core concept

**The write path, step by step:**

1. The application calls `write(key, value)`.
2. The cache layer writes the value to the database first.
3. Only after the database write succeeds does the cache layer also write the value into the cache.
4. The call returns to the caller only once both writes have completed.

**Why the database is written first:** if the cache were updated first and the database write then failed, the cache would hold a value the database never actually has — a correctness bug. Writing the database first and the cache second means a failure after step 2 simply leaves the cache stale (a cache miss on next read), which is safe, rather than the cache lying about what the database contains.

**Contrast with write-back:** write-through waits for the database write to finish before returning. Write-back (covered next) returns immediately after writing the cache and flushes to the database later, trading durability for lower write latency.

## 4. Diagram

```
App --write(key,value)--> Cache layer
                              |
                              | 1. write to Database first
                              v
                           Database  --OK-->
                              |
                              | 2. only then write to Cache
                              v
                            Cache
                              |
App <---------- OK -----------+     (write only completes after BOTH succeed)
```
*Caption: the database is written first; the cache is only updated once that write is confirmed.*

## 5. Runnable example

**Level 1 — Basic.** A `write` that updates the database, then the cache, in that order.

**Level 2 — Failure ordering.** Simulate a database write failure and show the cache is correctly left untouched.

**Level 3 — Read-after-write.** Confirm a read immediately after a successful write is always a cache hit with the fresh value.

```java
// WriteThroughCache.java
import java.util.HashMap;
import java.util.Map;

public class WriteThroughCache {

    static final Map<String, String> database = new HashMap<>();
    static final Map<String, String> cache = new HashMap<>();

    // Level 1 & 2: write-through, database first, cache second.
    static void write(String key, String value, boolean simulateDbFailure) {
        if (simulateDbFailure) {
            throw new RuntimeException("database write failed for " + key);
        }
        database.put(key, value); // 1. database is the source of truth
        cache.put(key, value);    // 2. only updated after the database confirms
    }

    static String read(String key) {
        return cache.get(key); // reads always go through the cache
    }

    public static void main(String[] args) {
        write("user:1", "Alice", false);
        System.out.println("read right after write: " + read("user:1")); // cache hit, fresh

        write("user:1", "Alice Smith", false);
        System.out.println("read after second write: " + read("user:1"));

        // Level 2: a failed database write must not corrupt the cache.
        try {
            write("user:2", "Bob", true);
        } catch (RuntimeException e) {
            System.out.println("write failed as expected: " + e.getMessage());
        }
        System.out.println("cache for user:2 (should be null): " + cache.get("user:2"));
        System.out.println("database for user:2 (should be null): " + database.get("user:2"));
    }
}
```

**How to run:** save as `WriteThroughCache.java`, then run `java WriteThroughCache.java`.

## 6. Walkthrough

1. `write("user:1", "Alice", false)` writes `"Alice"` to `database`, then to `cache`; both now agree.
2. `read("user:1")` returns `"Alice"` straight from `cache` — a hit, with data that is guaranteed fresh because the write just completed.
3. `write("user:1", "Alice Smith", false)` repeats the same two-step write, and the following read confirms the new value is visible immediately.
4. `write("user:2", "Bob", true)` simulates the database write throwing before `database.put` runs; because the method throws before reaching `cache.put`, neither `database` nor `cache` ever contains `"user:2"`, so both print `null` — the cache never diverges from the database, even on failure.

## 7. Gotchas & takeaways

> Gotcha: write-through only protects entries you actually write through this path; if some other process writes directly to the database and bypasses the cache layer, the cache goes stale for that key just like with any other pattern.

- Every write pays the latency of both the database and the cache, so write-through is a poor fit for write-heavy workloads where every millisecond of write latency matters.
- The ordering (database, then cache) is what keeps the cache from ever holding data the database does not have.
- Related concepts: [Write-back (write-behind) cache](0048-write-back-write-behind-cache.md) (trades this consistency guarantee for lower write latency), [Read-through cache](0046-read-through-cache.md) (the matching pattern for the read path).
