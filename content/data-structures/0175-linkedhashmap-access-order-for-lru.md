---
card: data-structures
gi: 175
slug: linkedhashmap-access-order-for-lru
title: LinkedHashMap access-order for LRU
---

## 1. What it is

`java.util.LinkedHashMap` is a `HashMap` that also keeps its entries in a doubly linked list, giving predictable iteration order. By default that order is **insertion order**, but a constructor flag switches it to **access order**: every `get` (and every `put` on an existing key) moves that entry to the end of the iteration order. Combined with one overridable method, this gives a working LRU cache in a few lines.

## 2. Why & when

Building an [LRU cache from scratch](0173-lru-cache-hashmap-doubly-linked-list.md) with a manual hash map and doubly linked list is the right exercise for understanding *why* it works, and the expected answer in most interviews. But in real production Java code, `LinkedHashMap` already implements that exact mechanism internally — reach for it directly when you need a working LRU cache and do not need custom eviction logic beyond capacity.

## 3. Core concept

**What backs it.** `LinkedHashMap` extends `HashMap`, so it keeps the same `O(1)` average lookup, insert, and delete. It adds a doubly linked list threading through all entries, maintaining either insertion order or access order depending on a constructor flag.

**The access-order constructor.** `new LinkedHashMap<>(initialCapacity, loadFactor, true)` — the third argument, `accessOrder`, set to `true`, switches the linked list to reorder on every access: `get(key)` moves that entry to the **end** of the list (marking it most recently used), and `put(key, value)` on an existing key does the same.

**The eviction hook.** `LinkedHashMap` defines a protected method, `removeEldestEntry(Map.Entry eldest)`, called automatically after every `put`. Its default implementation always returns `false` (never evict). Overriding it to return `true` once `size() > capacity` turns the map into a fixed-capacity LRU cache: the map itself calls this method and removes the eldest (least recently used, in access-order mode) entry whenever it returns `true`.

**Why this matches the from-scratch version exactly.** The "eldest" entry in access-order mode is, by construction, the one at the front of the internal linked list — the one that has gone longest without being accessed. That is precisely the least-recently-used entry, the same one a hand-built LRU cache would evict from its list's tail.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LinkedHashMap in access-order mode reordering entries on every get, and removeEldestEntry evicting the front entry once capacity is exceeded">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">accessOrder=true: internal list reorders on get()</text>
    <rect x="20" y="30" width="60" height="30" fill="#161b22" stroke="#8b949e"/><text x="50" y="49" text-anchor="middle">A (eldest)</text>
    <rect x="90" y="30" width="60" height="30" fill="#161b22" stroke="#8b949e"/><text x="120" y="49" text-anchor="middle">B</text>
    <rect x="160" y="30" width="60" height="30" fill="#161b22" stroke="#8b949e"/><text x="190" y="49" text-anchor="middle">C</text>

    <text x="300" y="20" fill="#f0883e">get("A") called-&gt;</text>
    <rect x="240" y="80" width="60" height="30" fill="#161b22" stroke="#8b949e"/><text x="270" y="99" text-anchor="middle">B (eldest)</text>
    <rect x="310" y="80" width="60" height="30" fill="#161b22" stroke="#8b949e"/><text x="340" y="99" text-anchor="middle">C</text>
    <rect x="380" y="80" width="60" height="30" fill="#161b22" stroke="#3fb950"/><text x="410" y="99" text-anchor="middle">A (moved)</text>

    <text x="10" y="140" fill="#8b949e">put() call when size &gt; capacity -&gt;</text>
    <text x="10" y="160" fill="#f44336">removeEldestEntry(eldest=B) returns true -&gt; B is auto-evicted</text>
  </g>
</svg>

`get` moves an entry to the end; `removeEldestEntry` decides whether the front entry gets dropped.

## 5. Runnable example

```java
// LinkedHashMapLRU.java
import java.util.*;

public class LinkedHashMapLRU {

    // Basic: plain LinkedHashMap in access-order mode, observing reordering without eviction.
    static void basicLevel() {
        LinkedHashMap<Integer, String> map = new LinkedHashMap<>(16, 0.75f, true);
        map.put(1, "one");
        map.put(2, "two");
        map.put(3, "three");

        map.get(1); // moves key 1 to the end (most recently used)

        System.out.println("basic: iteration order after get(1) -> " + map.keySet());
    }

    // Intermediate: a working fixed-capacity LRU cache via removeEldestEntry.
    static class LRUCache<K, V> extends LinkedHashMap<K, V> {
        int capacity;

        LRUCache(int capacity) {
            super(capacity, 0.75f, true);
            this.capacity = capacity;
        }

        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity;
        }
    }

    static void intermediateLevel() {
        LRUCache<Integer, String> cache = new LRUCache<>(2);
        cache.put(1, "one");
        cache.put(2, "two");
        cache.get(1);           // 1 becomes most recently used
        cache.put(3, "three");  // evicts 2 (least recently used), not 1

        System.out.println("intermediate: contains 1 (expect true) -> " + cache.containsKey(1));
        System.out.println("intermediate: contains 2 (expect false, evicted) -> " + cache.containsKey(2));
        System.out.println("intermediate: contains 3 (expect true) -> " + cache.containsKey(3));
    }

    // Advanced: use the LRU cache as a real memoization layer for an expensive computation.
    static Map<Integer, Long> memoCache = new LRUCache<>(5);

    static long expensiveComputation(int n) {
        if (memoCache.containsKey(n)) {
            return memoCache.get(n);
        }
        long result = 1;
        for (int i = 2; i <= n; i++) result *= i; // factorial, standing in for "expensive"
        memoCache.put(n, result);
        return result;
    }

    static void advancedLevel() {
        int[] requests = {5, 6, 7, 8, 9, 5, 10}; // "5" is requested again after 6 other distinct keys
        for (int n : requests) {
            long result = expensiveComputation(n);
            System.out.println("advanced: factorial(" + n + ") -> " + result + ", cache size -> " + memoCache.size());
        }
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java LinkedHashMapLRU.java`

## 6. Walkthrough

Create a plain access-ordered `LinkedHashMap` and insert keys `1, 2, 3`. Their internal iteration order starts as insertion order: `[1, 2, 3]`. Call `get(1)`: because `accessOrder` is `true`, this access moves key `1` to the end of the internal list. The new iteration order is `[2, 3, 1]` — printed directly by `keySet()`.

Now wrap this behavior in `LRUCache`, overriding `removeEldestEntry` to return `true` once `size() > capacity`. Insert `1` and `2` into a capacity-`2` cache. Call `get(1)`, moving it to the end (`[2, 1]` internally). Call `put(3, "three")`: this insert makes `size() == 3 > capacity == 2`, so Java calls `removeEldestEntry` with the eldest entry, which is now key `2` (the front of the list) — it returns `true`, and `LinkedHashMap` automatically removes key `2` before `put` returns.

The advanced example uses this as a memoization cache for a stand-in "expensive" computation. Requesting `5, 6, 7, 8, 9` fills a capacity-`5` cache exactly full. Requesting `5` again marks it as recently used, moving it away from eviction risk. Requesting `10` next pushes the cache over capacity, evicting whichever key is currently least recently used — not `5`, since it was just re-accessed.

**Complexity.** `get` and `put`: `O(1)` average, same as the underlying `HashMap`, plus `O(1)` for the linked-list reordering. Space: `O(capacity)` once bounded by `removeEldestEntry`.

## 7. Gotchas & takeaways

> The third constructor argument (`accessOrder`) defaults to `false` if omitted — using `new LinkedHashMap<>()` with no arguments gives you insertion-order iteration, **not** LRU behavior. Forgetting the `true` flag is the most common mistake when reaching for this pattern.

- `removeEldestEntry` must compare against the cache's own tracked `capacity` field — comparing against a hardcoded number, or forgetting the override entirely (which defaults to always returning `false`), silently turns off eviction and lets the map grow unbounded.
- This built-in approach is not thread-safe by default, same as `HashMap` — wrap it with `Collections.synchronizedMap(...)` or use an external library's concurrent LRU cache for multi-threaded use.
- Use this when you want LRU behavior with minimal code; use the [hand-built HashMap + doubly linked list version](0173-lru-cache-hashmap-doubly-linked-list.md) when an interview or a library constraint requires you to implement it without relying on `LinkedHashMap` internals.
