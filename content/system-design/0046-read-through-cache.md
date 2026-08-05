---
card: system-design
gi: 46
slug: read-through-cache
title: Read-through cache
---

## 1. What it is

A **read-through cache** sits directly in the read path between the application and the database. The application only ever talks to the cache; on a miss, the cache library itself queries the database, stores the result, and returns it. The application code never sees a fallback branch to the database.

## 2. Why & when

Read-through gives the same benefit as cache-aside — the database is shielded from repeated reads of the same data — but centralizes the miss-handling logic in one place instead of scattering "check cache, else query database, else populate cache" across every call site. Use it when many parts of a codebase read the same entities, so you want that logic written once, in a caching layer or library, rather than duplicated in every caller.

## 3. Core concept

**The loader function:** a read-through cache is configured with a **loader**, a function that knows how to fetch a value for a key from the database. The application calls a single `get(key)` method on the cache; it never calls the database directly.

**What happens on a miss:** the cache itself invokes the loader, stores the returned value, and hands it back to the caller. On a hit, the loader is never invoked. From the application's point of view, `get(key)` always "just works" — the miss-handling is invisible.

**Cache-aside vs read-through:** the two patterns move the same logic to a different place. Cache-aside puts the "check cache, else query, else populate" logic in application code; read-through puts identical logic inside the cache abstraction, behind a single method call. The runtime behavior — same miss path, same population — is otherwise the same.

## 4. Diagram

```
App --get(key)--> Cache
                     |
                     | MISS: cache calls its own loader(key)
                     v
                  Database
                     |
                     v
                  Cache stores the row, then returns it
App <--row-- Cache          (application never called the database itself)
```
*Caption: the loader function lives inside the cache; the application only ever calls `get`.*

## 5. Runnable example

**Level 1 — Basic.** A `ReadThroughCache` wired with a loader function that queries a simulated database.

**Level 2 — Hit path.** Confirm the loader is not called again once a value is cached.

**Level 3 — Pluggable loader.** Swap in a different loader (a computed value) to show the cache logic is fully generic and independent of where data comes from.

```java
// ReadThroughCache.java
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

public class ReadThroughCache {

    // Level 1 & 2: a generic read-through cache wrapping any loader.
    static class Cache<K, V> {
        private final Map<K, V> store = new HashMap<>();
        private final Function<K, V> loader;
        int loaderCalls = 0;

        Cache(Function<K, V> loader) {
            this.loader = loader;
        }

        V get(K key) {
            if (store.containsKey(key)) {
                return store.get(key); // hit: loader not touched
            }
            loaderCalls++;
            V value = loader.apply(key); // miss: cache does the loading itself
            store.put(key, value);
            return value;
        }
    }

    public static void main(String[] args) {
        Map<String, String> database = new HashMap<>();
        database.put("user:1", "Alice");

        Cache<String, String> userCache = new Cache<>(database::get);

        System.out.println("first get: " + userCache.get("user:1"));
        System.out.println("second get: " + userCache.get("user:1"));
        System.out.println("loader calls: " + userCache.loaderCalls); // stays 1

        // Level 3: a different loader, computed rather than from a map.
        Cache<Integer, Integer> squareCache = new Cache<>(n -> n * n);
        System.out.println("square(7) = " + squareCache.get(7));
        System.out.println("square(7) again = " + squareCache.get(7));
        System.out.println("square loader calls: " + squareCache.loaderCalls); // stays 1
    }
}
```

**How to run:** save as `ReadThroughCache.java`, then run `java ReadThroughCache.java`.

## 6. Walkthrough

1. `userCache.get("user:1")` finds nothing in `store`, so it calls `loader.apply("user:1")`, which runs `database::get` and returns `"Alice"`; `loaderCalls` becomes `1`, and `store` is populated.
2. `userCache.get("user:1")` a second time finds `"Alice"` already in `store` and returns it without touching `loader`; `loaderCalls` stays at `1`.
3. `squareCache` is built with a completely different loader — a computation instead of a database lookup — proving the `Cache` class does not care what the loader does, only that it can produce a value for a key.
4. `squareCache.get(7)` calls the loader once, caches `49`, and the second call returns the cached value without recomputing.

## 7. Gotchas & takeaways

> Gotcha: because the loader is invoked from inside `get`, a slow or failing loader (a slow database, a network timeout) blocks the caller directly; production read-through caches usually add a timeout and a way to return stale data rather than hanging indefinitely.

- Read-through moves miss-handling into the cache layer, so every caller gets consistent behavior for free instead of re-implementing it.
- The write path is a separate concern: read-through by itself says nothing about how writes reach the database, which is why it is usually paired with write-through or write-back.
- Related concepts: [Cache-aside (lazy loading)](0045-cache-aside-lazy-loading.md) (the same miss-handling logic, written in the application instead), [Write-through cache](0047-write-through-cache.md) (the matching pattern for the write path).
