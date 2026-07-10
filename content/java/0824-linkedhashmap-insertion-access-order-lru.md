---
card: java
gi: 824
slug: linkedhashmap-insertion-access-order-lru
title: LinkedHashMap (insertion & access order, LRU)
---

## 1. What it is

`LinkedHashMap` is a [`HashMap`](0823-hashmap-internals-buckets-hashing-load-factor-treeify.md) subclass that additionally maintains a doubly-linked list running through all its entries, giving predictable iteration order — just like [`LinkedHashSet`](0818-linkedhashset.md) does for sets. It supports two ordering modes, chosen via a constructor flag: **insertion order** (the default — entries iterate in the order they were first inserted, and re-inserting an existing key doesn't move it) and **access order** (entries iterate from least-recently-accessed to most-recently-accessed, where "accessed" means `get()`, `put()`, or `putIfAbsent()` touched that entry — every touch moves the entry to the end of the order). `LinkedHashMap` also exposes a protected `removeEldestEntry(Map.Entry)` hook, overridable to automatically evict the oldest entry whenever a new one is added — the foundation for building a bounded LRU (least-recently-used) cache with almost no extra code.

## 2. Why & when

Plain `HashMap` gives no iteration order guarantee at all, which is fine for pure lookup but wrong whenever a map's contents are displayed to a user or need deterministic, reproducible ordering for logging or testing. `LinkedHashMap` in insertion-order mode fixes that with the same O(1) average performance as `HashMap`. Access-order mode exists specifically to support LRU eviction: combined with an overridden `removeEldestEntry` that returns `true` once the map exceeds a target size, a `LinkedHashMap` in access-order mode becomes a complete, correct, size-bounded LRU cache — every read or write "refreshes" an entry's position, and the genuinely least-recently-used entry is always the one automatically evicted when the cache is full. This is a small enough amount of code (a constructor call plus one overridden method) that it's the standard way to build a simple in-memory LRU cache in Java without a third-party library.

## 3. Core concept

```java
// true as the third constructor argument selects ACCESS order instead of insertion order.
LinkedHashMap<String, Integer> accessOrdered = new LinkedHashMap<>(16, 0.75f, true);
accessOrdered.put("a", 1);
accessOrdered.put("b", 2);
accessOrdered.put("c", 3);
// iteration order right now: a, b, c (insertion order, since nothing's been touched again yet)

accessOrdered.get("a"); // "touching" a moves it to the END of the order
// iteration order now: b, c, a
```

Overriding `removeEldestEntry` turns this into automatic eviction:

```java
LinkedHashMap<String, Integer> lru = new LinkedHashMap<>(16, 0.75f, true) {
    protected boolean removeEldestEntry(Map.Entry<String, Integer> eldest) {
        return size() > 3; // evict the least-recently-used entry once the cache exceeds 3 entries
    }
};
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="In access-order mode, every get or put moves that entry to the end of the linked list; the entry at the front is always the least recently used">
  <g font-family="sans-serif">
    <rect x="40" y="60" width="90" height="45" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
    <text x="85" y="87" fill="#e6edf3" font-size="11" text-anchor="middle">b (LRU)</text>

    <rect x="150" y="60" width="90" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="195" y="87" fill="#e6edf3" font-size="11" text-anchor="middle">c</text>

    <rect x="260" y="60" width="90" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="305" y="87" fill="#e6edf3" font-size="11" text-anchor="middle">a (MRU)</text>
  </g>

  <text x="85" y="45" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">evicted first</text>
  <text x="305" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">just touched</text>

  <line x1="130" y1="82" x2="150" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a824)"/>
  <line x1="240" y1="82" x2="260" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a824)"/>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">get("a") moved it from front to back — the entry now at the front is the true least-recently-used one</text>

  <defs><marker id="a824" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Each access moves an entry to the "most recently used" end; the front of the list is always the true least-recently-used entry.*

## 5. Runnable example

Scenario: a small in-memory cache for expensive-to-compute values, growing from basic insertion-order iteration, to access-order mode revealing how touches reorder entries, to a complete bounded LRU cache that evicts automatically.

### Level 1 — Basic

```java
import java.util.*;

public class CacheInsertionOrder {
    public static void main(String[] args) {
        LinkedHashMap<String, Integer> cache = new LinkedHashMap<>(); // default: insertion order
        cache.put("user:1", 100);
        cache.put("user:2", 200);
        cache.put("user:3", 300);

        cache.get("user:1"); // a plain get() in INSERTION-order mode does NOT reorder anything

        System.out.println("iteration order: " + cache.keySet());
    }
}
```

**How to run:** `java CacheInsertionOrder.java` (JDK 17+).

Expected output:
```
iteration order: [user:1, user:2, user:3]
```

In the default insertion-order mode, `get("user:1")` has no effect on ordering at all — the map behaves exactly like a `LinkedHashSet`'s ordering guarantee applied to keys.

### Level 2 — Intermediate

```java
import java.util.*;

public class CacheAccessOrder {
    public static void main(String[] args) {
        // true as the third constructor argument switches to ACCESS order.
        LinkedHashMap<String, Integer> cache = new LinkedHashMap<>(16, 0.75f, true);
        cache.put("user:1", 100);
        cache.put("user:2", 200);
        cache.put("user:3", 300);

        System.out.println("order right after inserting: " + cache.keySet());

        cache.get("user:1"); // "touching" user:1 moves it to the END of the order
        System.out.println("order after get(\"user:1\"): " + cache.keySet());

        cache.get("user:2");
        System.out.println("order after also get(\"user:2\"): " + cache.keySet());
    }
}
```

**How to run:** `java CacheAccessOrder.java`.

Expected output:
```
order right after inserting: [user:1, user:2, user:3]
order after get("user:1"): [user:2, user:3, user:1]
order after also get("user:2"): [user:3, user:1, user:2]
```

The real-world concern added: access-order mode makes every `get()` move the touched key to the end of the iteration order — `"user:3"`, never touched, drifts toward the front, becoming the least-recently-used entry, exactly the property an LRU cache needs to identify what to evict.

### Level 3 — Advanced

```java
import java.util.*;

public class LruCache<K, V> extends LinkedHashMap<K, V> {
    private final int maxEntries;

    public LruCache(int maxEntries) {
        super(16, 0.75f, true); // access-order mode
        this.maxEntries = maxEntries;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > maxEntries; // auto-evict the least-recently-used entry once over capacity
    }

    public static void main(String[] args) {
        LruCache<String, Integer> cache = new LruCache<>(3);
        cache.put("user:1", 100);
        cache.put("user:2", 200);
        cache.put("user:3", 300);
        System.out.println("cache after 3 inserts: " + cache.keySet());

        cache.get("user:1"); // touch user:1 -- it's no longer the least-recently-used
        cache.put("user:4", 400); // cache is now over capacity -- evicts the ACTUAL least-recently-used entry

        System.out.println("cache after touching user:1 and adding user:4: " + cache.keySet());
        System.out.println("user:2 still present? " + cache.containsKey("user:2"));
    }
}
```

**How to run:** `java LruCache.java`.

Expected output:
```
cache after 3 inserts: [user:1, user:2, user:3]
cache after touching user:1 and adding user:4: [user:3, user:1, user:4]
user:2 still present? false
```

This adds the production-flavored hard case: a **complete, correct LRU cache** built by extending `LinkedHashMap`, enabling access-order mode in the constructor, and overriding `removeEldestEntry` to signal eviction once the cache exceeds `maxEntries`. Note that `"user:2"` — not `"user:1"` — is the one evicted: even though `"user:1"` was inserted first, touching it with `get("user:1")` moved it to the most-recently-used end, leaving `"user:2"` as the genuine least-recently-used entry once `"user:3"` and `"user:4"` had also been touched more recently.

## 6. Walkthrough

Tracing `LruCache.main`:

1. `cache = new LruCache<>(3)` constructs a `LinkedHashMap` in access-order mode (via `super(16, 0.75f, true)`) with `maxEntries = 3`.
2. Three `put` calls insert `"user:1"`, `"user:2"`, `"user:3"` in that order. After each `put`, `removeEldestEntry` is checked automatically; `size() > 3` is false all three times, so nothing is evicted. Order is `[user:1, user:2, user:3]`.
3. `cache.get("user:1")` is an access-order-mode read: it locates `"user:1"`'s entry and moves it to the end of the internal linked list. Order becomes `[user:2, user:3, user:1]` internally (not yet printed).
4. `cache.put("user:4", 400)` inserts a new entry (moving it to the end too, since insertion also counts as an access), bringing size to 4. Immediately after, `LinkedHashMap`'s internal machinery calls `removeEldestEntry(eldest)`, passing the entry currently at the *front* of the list — which, after step 3, is `"user:2"` (the actual least-recently-used entry, since `"user:1"` was touched more recently than it, and `"user:3"`/`"user:4"` are more recent still). `removeEldestEntry` returns `size() > maxEntries` (4 > 3, true), so `"user:2"` is automatically removed.
5. Printing `cache.keySet()` confirms the final order `[user:3, user:1, user:4]` — three entries, with `"user:2"` correctly gone — and `cache.containsKey("user:2")` confirms `false`, verifying the eviction targeted the true least-recently-used entry rather than simply the oldest-inserted one.

## 7. Gotchas & takeaways

> **Gotcha:** in access-order mode, even a `get()` call that only reads a value **mutates** the map's internal linked-list structure (by moving that entry to the end). This means a `LinkedHashMap` in access-order mode is **not safe to iterate with a plain for-each loop while also calling `get()`** on it elsewhere concurrently — that combination can trigger `ConcurrentModificationException` even though `get()` looks like a read-only operation from the caller's perspective.

- `LinkedHashMap` extends [`HashMap`](0823-hashmap-internals-buckets-hashing-load-factor-treeify.md), adding a linked list for predictable iteration order, in either insertion order (default) or access order (opt-in via the three-argument constructor).
- In access-order mode, every `get`/`put`/`putIfAbsent` moves the touched entry to the "most recently used" end of the order.
- Overriding `removeEldestEntry` to return `size() > maxEntries` turns a `LinkedHashMap` into a complete, correct, automatically-evicting LRU cache with minimal code.
- Because `get()` mutates internal state in access-order mode, treat such a map as **not** safe for unsynchronized concurrent access, even for reads.
- For a thread-safe LRU-style cache, external synchronization (or a purpose-built caching library) is needed — `LinkedHashMap` itself carries no concurrency guarantees at all.
