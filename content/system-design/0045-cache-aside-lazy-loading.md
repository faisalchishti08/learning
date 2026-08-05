---
card: system-design
gi: 45
slug: cache-aside-lazy-loading
title: "Cache-aside (lazy loading)"
---

## 1. What it is

**Cache-aside**, also called **lazy loading**, is a caching pattern where the application code — not the cache itself — is responsible for reading from and writing to the cache. On a read, the application checks the cache first; only if the data is missing does it fetch from the database and then store a copy in the cache for next time.

## 2. Why & when

Cache-aside is the most common caching pattern because it is simple and the cache only ever holds data that was actually requested, avoiding wasted memory on data nobody reads. Use it when reads greatly outnumber writes and some staleness is acceptable, such as product catalog pages or user profile lookups. The main alternative, read-through caching (covered next), moves this same logic behind a library so the application code stays simpler.

## 3. Core concept

**The read path, step by step:**

1. The application asks the cache for the key.
2. **Cache hit:** the cache returns the value immediately; the database is never touched.
3. **Cache miss:** the application queries the database itself, then writes the result into the cache before returning it to the caller.

**The write path:** on an update, the application writes to the database and then either updates or deletes the matching cache entry, so the next read is forced to reload fresh data. Deleting (rather than updating) the cache entry on write is the safer default, because it avoids a race where a stale value gets written back into the cache after a concurrent read already reloaded it.

**Why "aside":** the cache sits beside the application, not between the application and the database. The application explicitly decides when to populate it, unlike read-through caching where the cache library does that automatically.

## 4. Diagram

```
READ (cache miss):
  App --get(key)--> Cache --MISS--> App --query--> Database
                                      App <--row-- Database
  App --put(key,row)--> Cache
  App <--row-- (returned to caller)

READ (cache hit):
  App --get(key)--> Cache --HIT: row--> App   (database never touched)

WRITE:
  App --update--> Database
  App --delete(key)--> Cache   (next read reloads fresh data)
```
*Caption: the application owns every cache read and write; the cache never talks to the database on its own.*

## 5. Runnable example

**Level 1 — Basic.** A cache-aside `get` that falls back to a simulated database on a miss.

**Level 2 — Write path.** Add `update`, which writes the database first and then invalidates the cache entry.

**Level 3 — Hit/miss counters.** Track hit and miss counts to show the cache actually reduces database load over repeated reads.

```java
// CacheAside.java
import java.util.HashMap;
import java.util.Map;

public class CacheAside {

    static final Map<String, String> database = new HashMap<>();
    static final Map<String, String> cache = new HashMap<>();
    static int dbReads = 0;

    static String dbQuery(String key) {
        dbReads++;
        return database.get(key);
    }

    // Level 1: cache-aside read.
    static String get(String key) {
        String value = cache.get(key);
        if (value != null) {
            return value; // cache hit
        }
        value = dbQuery(key); // cache miss: go to the database
        if (value != null) {
            cache.put(key, value);
        }
        return value;
    }

    // Level 2: write path invalidates the cache entry.
    static void update(String key, String newValue) {
        database.put(key, newValue); // database is the source of truth
        cache.remove(key); // force next read to reload
    }

    public static void main(String[] args) {
        database.put("user:1", "Alice");

        System.out.println("first get: " + get("user:1")); // miss
        System.out.println("second get: " + get("user:1")); // hit
        System.out.println("db reads so far: " + dbReads);

        update("user:1", "Alice Smith");
        System.out.println("after update: " + get("user:1")); // miss again, fresh value
        System.out.println("total db reads: " + dbReads);
    }
}
```

**How to run:** save as `CacheAside.java`, then run `java CacheAside.java`.

## 6. Walkthrough

1. `get("user:1")` finds nothing in `cache`, so it calls `dbQuery`, incrementing `dbReads` to `1`, and stores `"Alice"` in `cache` before returning it.
2. The second `get("user:1")` finds `"Alice"` already in `cache` and returns it directly; `dbReads` stays at `1`.
3. `update("user:1", "Alice Smith")` writes the new value to `database` first, then removes `"user:1"` from `cache`, leaving the cache empty for that key.
4. The next `get("user:1")` misses again, so it reloads `"Alice Smith"` from `database` (`dbReads` becomes `2`) and re-populates `cache`.

## 7. Gotchas & takeaways

> Gotcha: if the application crashes or is slow between the database write and the cache invalidation in `update`, a reader can briefly see a stale cached value; this window is usually acceptable but is not eliminated by cache-aside alone.

- The cache only ever contains data that has actually been requested, so cold caches naturally warm up from real traffic.
- A crashed cache is not fatal: every read simply falls through to the database, at the cost of higher latency until the cache is repopulated.
- Related concepts: [Read-through cache](0046-read-through-cache.md) (the same idea moved into a library), [Cache invalidation strategies](0051-cache-invalidation-strategies.md) (deeper look at the delete-vs-update choice on write).
