---
card: system-design
gi: 48
slug: write-back-write-behind-cache
title: "Write-back (write-behind) cache"
---

## 1. What it is

A **write-back cache**, also called **write-behind**, writes an update to the cache immediately and returns to the caller right away, without waiting for the database. The write to the database happens later, asynchronously, often batched together with other pending writes.

## 2. Why & when

Write-back gives the lowest possible write latency, since the caller only waits on an in-memory cache write, not a database round trip. It also lets you batch many writes into fewer, larger database operations, which is efficient for very write-heavy workloads (metrics counters, activity logs, view counts) where losing a small, recent window of data on a crash is an acceptable trade for speed. Do not use it where every write must be durable immediately, such as a financial transaction.

## 3. Core concept

**The write path, step by step:**

1. The application calls `write(key, value)`.
2. The value is written to the cache only, and marked **dirty** (meaning "not yet saved to the database").
3. The call returns immediately.
4. A background process later flushes dirty entries to the database, either on a timer, when a batch size is reached, or when an entry is evicted from the cache.

**The durability gap:** between step 3 and the background flush, the only copy of the latest value lives in the cache. If the cache process crashes before flushing, that update is lost — this is the fundamental trade write-back makes for speed.

**Why batching helps:** if the same key is written multiple times before the flush runs, only the final value needs to be sent to the database, collapsing many writes into one. This is why write-back suits high-frequency updates to the same keys, such as a "like counter."

## 4. Diagram

```
App --write(key,value)--> Cache      (marks entry dirty)
App <---------- OK -----------+       (returns immediately, database not touched yet)

  ... later, on a timer or batch threshold ...

Background flusher --reads all dirty entries--> Cache
Background flusher --batched write--> Database
Cache: entries marked clean
```
*Caption: the caller only waits on the cache; the database catch-up happens later, in the background.*

## 5. Runnable example

**Level 1 — Basic.** A cache that marks entries dirty on write and returns immediately.

**Level 2 — Batched flush.** A `flush` method that writes all dirty entries to the database in one pass and clears the dirty flags.

**Level 3 — Collapsed writes.** Show that writing the same key three times before a flush only produces one database write, with the final value.

```java
// WriteBackCache.java
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;

public class WriteBackCache {

    static final Map<String, String> database = new HashMap<>();
    static final Map<String, String> cache = new HashMap<>();
    static final Set<String> dirtyKeys = new HashSet<>();
    static int databaseWrites = 0;

    // Level 1: write only touches the cache; returns immediately.
    static void write(String key, String value) {
        cache.put(key, value);
        dirtyKeys.add(key); // mark for later flush
    }

    // Level 2 & 3: flush all dirty entries in one batched pass.
    static void flush() {
        for (String key : dirtyKeys) {
            database.put(key, cache.get(key)); // one write per key, final value only
            databaseWrites++;
        }
        dirtyKeys.clear();
    }

    public static void main(String[] args) {
        write("likes:post42", "1");
        write("likes:post42", "2"); // same key, overwrites before any flush
        write("likes:post42", "3");
        write("views:post42", "100");

        System.out.println("database before flush: " + database); // empty, nothing flushed yet
        System.out.println("cache before flush: " + cache);

        flush();

        System.out.println("database after flush: " + database);
        System.out.println("database writes performed: " + databaseWrites); // 2, not 4
    }
}
```

**How to run:** save as `WriteBackCache.java`, then run `java WriteBackCache.java`.

## 6. Walkthrough

1. Three calls to `write("likes:post42", ...)` each update `cache` and re-add `"likes:post42"` to `dirtyKeys`; `database` is never touched by any of them.
2. `write("views:post42", "100")` similarly only updates `cache`.
3. Printing `database` before `flush()` shows it is still empty — every write so far only reached the cache.
4. `flush()` iterates `dirtyKeys` (now just two distinct keys: `likes:post42` and `views:post42`) and writes each one's current cached value to `database`, so `databaseWrites` ends at `2` even though `write` was called four times — the three overwrites of `likes:post42` collapsed into a single database write of its final value, `"3"`.

## 7. Gotchas & takeaways

> Gotcha: if the process holding the cache crashes before `flush()` runs, every dirty entry is lost permanently; production systems mitigate this with a durable write-ahead log or by replicating the cache, but the risk is never fully zero.

- Write-back trades durability for write speed and for batching efficiency on hot keys.
- The size of the durability gap is a direct function of how often you flush — flushing more often shrinks potential data loss but reduces the batching benefit.
- Related concepts: [Write-through cache](0047-write-through-cache.md) (the safer, synchronous alternative), [Refresh-ahead cache](0049-refresh-ahead-cache.md) (a different background-process pattern, for reads instead of writes).
