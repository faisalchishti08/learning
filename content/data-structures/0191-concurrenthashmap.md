---
card: data-structures
gi: 191
slug: concurrenthashmap
title: ConcurrentHashMap
---

## 1. What it is

`ConcurrentHashMap` is a thread-safe hash map designed for high concurrency. Unlike wrapping a `HashMap` with `Collections.synchronizedMap` (which locks the entire map for every operation), `ConcurrentHashMap` allows many threads to read and write **different parts** of the map at the same time, without blocking each other.

## 2. Why & when

Use `ConcurrentHashMap` whenever multiple threads need shared read/write access to a map — a cache shared across request-handling threads, counters updated concurrently, or any shared lookup table in multi-threaded code. A plain `HashMap` is not thread-safe at all: concurrent modification from multiple threads can corrupt its internal structure (in the worst case, causing an infinite loop during resize in older Java versions). `Collections.synchronizedMap(new HashMap<>())` fixes the safety problem but forces every operation through one lock, serializing all access even between threads touching unrelated keys.

## 3. Core concept

**What backs it.** The same bucket-array-plus-chaining design as `HashMap`, but with fine-grained internal synchronization. Modern `ConcurrentHashMap` (Java 8+) synchronizes at the level of individual bucket nodes during writes, rather than locking the whole map — so a write to one bucket does not block a read or write to a different bucket.

**Read behavior needs no locking at all.** Reads (`get`) use `volatile`-guaranteed visibility on the underlying array and node references, letting them proceed without acquiring any lock — this is why reads scale extremely well under concurrent load, even while writes are happening elsewhere in the map.

**Atomic compound operations.** `ConcurrentHashMap` provides methods that combine "check" and "act" into one atomic step, avoiding the race condition of doing them as two separate calls: `putIfAbsent(key, value)` (insert only if the key is not already present), `computeIfAbsent(key, function)` (compute and insert a value only if absent, useful for lazy-initializing a per-key structure), `merge(key, value, function)` (combine a new value with any existing one — the standard idiom for thread-safe counting).

**Why "check then act" with separate calls is unsafe even with a thread-safe map.** `if (!map.containsKey(k)) map.put(k, v)` is thread-safe map calls used unsafely together — two threads can both pass the `containsKey` check before either calls `put`, and both then overwrite each other's intended insert. `putIfAbsent` performs the same logic as one indivisible operation, closing that gap.

**Iteration is weakly consistent.** Iterators do not throw `ConcurrentModificationException`. They reflect the state of the map at some point during iteration — possibly including some, all, or none of concurrent modifications — but never re-visit an element or crash. This is fail-safe behavior, contrasted with `HashMap`'s fail-fast iterators.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ConcurrentHashMap allowing two threads to write to different buckets simultaneously without blocking each other, unlike a fully synchronized map">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20" fill="#f44336">Collections.synchronizedMap: one lock for everything</text>
    <rect x="20" y="30" width="300" height="30" fill="#161b22" stroke="#f44336"/>
    <text x="170" y="50" text-anchor="middle" font-size="9">Thread A writes bucket 3 -- Thread B BLOCKS on bucket 7</text>

    <text x="10" y="90" fill="#3fb950">ConcurrentHashMap: per-bucket synchronization</text>
    <rect x="20" y="100" width="140" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="90" y="120" text-anchor="middle" font-size="9">Thread A writes bucket 3</text>
    <rect x="180" y="100" width="140" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="250" y="120" text-anchor="middle" font-size="9">Thread B writes bucket 7</text>
    <text x="170" y="150" text-anchor="middle" font-size="9" fill="#3fb950">both proceed simultaneously -- no shared lock</text>
  </g>
</svg>

Fine-grained locking lets unrelated writes proceed in parallel instead of queueing behind one map-wide lock.

## 5. Runnable example

```java
// ConcurrentHashMapDemo.java
import java.util.concurrent.*;
import java.util.*;

public class ConcurrentHashMapDemo {

    // Basic: basic thread-safe put/get, usable directly across threads without external synchronization.
    static void basicLevel() throws InterruptedException {
        ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
        Runnable writer = () -> {
            for (int i = 0; i < 1000; i++) map.put("key-" + i, i);
        };
        Thread t1 = new Thread(writer);
        Thread t2 = new Thread(writer);
        t1.start(); t2.start();
        t1.join(); t2.join();

        System.out.println("basic: map size after concurrent writes -> " + map.size());
    }

    // Intermediate: safe concurrent counting with merge(), avoiding the check-then-act race.
    static void intermediateLevel() throws InterruptedException {
        ConcurrentHashMap<String, Integer> wordCounts = new ConcurrentHashMap<>();
        String[] words = {"a", "b", "a", "c", "b", "a"};

        List<Thread> threads = new ArrayList<>();
        for (String word : words) {
            Thread t = new Thread(() -> wordCounts.merge(word, 1, Integer::sum));
            threads.add(t);
            t.start();
        }
        for (Thread t : threads) t.join();

        System.out.println("intermediate: word counts (expect a=3, b=2, c=1) -> " + wordCounts);
    }

    // Advanced: computeIfAbsent for thread-safe lazy initialization of a per-key structure.
    static void advancedLevel() throws InterruptedException {
        ConcurrentHashMap<String, List<Integer>> groupedByCategory = new ConcurrentHashMap<>();
        String[] categories = {"fruit", "veg", "fruit", "veg", "fruit"};

        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < categories.length; i++) {
            int itemId = i;
            String category = categories[i];
            Thread t = new Thread(() ->
                groupedByCategory.computeIfAbsent(category, k -> Collections.synchronizedList(new ArrayList<>())).add(itemId));
            threads.add(t);
            t.start();
        }
        for (Thread t : threads) t.join();

        System.out.println("advanced: grouped items -> " + groupedByCategory);
    }

    public static void main(String[] args) throws InterruptedException {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ConcurrentHashMapDemo.java`

## 6. Walkthrough

Two threads each insert 1000 entries with distinct keys (`"key-0"` through `"key-999"`, written by both threads, so the same keys get overwritten — this is safe, just not distinct data). The final `map.size()` is `1000`, and the map never throws or corrupts, because every `put` call is internally synchronized at the bucket level, safely handling concurrent writes even to the same key.

For word counting: six threads each call `wordCounts.merge(word, 1, Integer::sum)` concurrently for words `["a","b","a","c","b","a"]`. `merge` is atomic per key: for each call, it reads the current count (or treats it as absent), applies `Integer::sum` to combine it with `1`, and writes the result back, all as one indivisible step per key. Even with three separate threads all calling `merge("a", 1, ...)` around the same time, none of their increments are lost — the final count for `"a"` is correctly `3`, not fewer due to a lost update.

For `computeIfAbsent`: five threads each want to add an item to a list keyed by category (`"fruit"` or `"veg"`). The first thread to reach a given category atomically creates and inserts a new `synchronizedList` for that key; every other thread calling `computeIfAbsent` on the same key sees the list is already present and simply reuses it, rather than each thread creating and inserting its own separate list and overwriting the others' work.

**Complexity.** `get`, `put`, `putIfAbsent`, `computeIfAbsent`, `merge`: `O(1)` average, matching `HashMap`, with additional (small) synchronization overhead per call. Iteration: `O(n)`, weakly consistent, no locking required for the traversal itself.

## 7. Gotchas & takeaways

> `ConcurrentHashMap` guarantees each **individual** method call is atomic and thread-safe — it does **not** make a sequence of separate calls atomic together. `if (!map.containsKey(k)) map.put(k, v)` is still a race condition even on a `ConcurrentHashMap`; use `putIfAbsent`, `computeIfAbsent`, or `merge` instead for check-then-act patterns.

- `ConcurrentHashMap` does not allow `null` keys or `null` values (unlike `HashMap`), because a `null` return from `get` would be ambiguous between "the key maps to `null`" and "the key is absent" — a distinction that matters far more under concurrent access, where another thread could be inserting the key at the same instant.
- Prefer `ConcurrentHashMap` over `Collections.synchronizedMap(new HashMap<>())` for nearly all concurrent use cases — its finer-grained locking scales far better under contention.
- For a thread-safe `List`, see [CopyOnWriteArrayList](0192-copyonwritearraylist.md) — a very different tradeoff, optimized for read-heavy, write-rare scenarios rather than `ConcurrentHashMap`'s balanced read/write concurrency.
