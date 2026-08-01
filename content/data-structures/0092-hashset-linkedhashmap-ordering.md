---
card: data-structures
gi: 92
slug: hashset-linkedhashmap-ordering
title: HashSet & LinkedHashMap ordering
---

## 1. What it is

`HashSet` is a `Set` backed internally by a `HashMap` (storing elements as keys with a dummy value) — it gives no iteration order guarantee at all. `LinkedHashMap` (and its cousin `LinkedHashSet`) is a `HashMap` variant that *additionally* maintains a doubly linked list threading through all entries, giving predictable iteration order — either insertion order, or, optionally, access order.

## 2. Why & when

Use `HashMap`/`HashSet` when you never rely on iteration order — the default and usually fastest choice. Use `LinkedHashMap`/`LinkedHashSet` when you need predictable iteration order (most commonly insertion order) *and* still want hash-table lookup speed — for example, printing entries in the order they were added, or building a simple LRU cache using access-order mode.

## 3. Core concept

**What backs each.** `HashSet<E>` internally wraps a `HashMap<E, Object>`, using each set element as a map key and a shared dummy object as every value — so its ordering behavior is identical to `HashMap`'s: unspecified, and dependent on internal bucket layout. `LinkedHashMap` uses the same bucket array as `HashMap`, but every entry also has `before`/`after` references forming a doubly linked list across the whole map, independent of which bucket it lives in.

**Ordering guarantees, side by side.**

| Type | Iteration order |
|---|---|
| `HashMap` / `HashSet` | unspecified, can change between runs or after resizes |
| `LinkedHashMap` (default) | insertion order — the order keys were first put |
| `LinkedHashMap` (access-order mode) | least-recently-accessed first, most-recently-accessed last |
| `TreeMap` (not this topic, but worth knowing) | sorted by key |

**How access-order mode enables an LRU cache.** `new LinkedHashMap<>(capacity, loadFactor, true)` — the third argument, `true`, switches to access-order: every `get()` (and `put()` on an existing key) moves that entry to the end of the internal linked list. Combined with overriding `removeEldestEntry()` to return `true` once the map exceeds a target size, this gives a working least-recently-used eviction cache in a few lines, since the *front* of the list is always the least-recently-used entry.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A LinkedHashMap where three entries sit in unpredictable bucket positions but are also connected by a separate doubly linked list in insertion order, which iteration follows instead of bucket order">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">bucket array (scattered by hash) -- NOT the iteration order</text>
    <rect x="20" y="30" width="40" height="24" fill="#161b22" stroke="#8b949e"/><text x="40" y="46" fill="#e6edf3" text-anchor="middle" font-size="8">B</text>
    <rect x="200" y="30" width="40" height="24" fill="#161b22" stroke="#8b949e"/><text x="220" y="46" fill="#e6edf3" text-anchor="middle" font-size="8">A</text>
    <rect x="420" y="30" width="40" height="24" fill="#161b22" stroke="#8b949e"/><text x="440" y="46" fill="#e6edf3" text-anchor="middle" font-size="8">C</text>

    <text x="20" y="100" fill="#79c0ff">separate doubly linked list, in INSERTION order (A, B, C) -- this IS the iteration order</text>
    <rect x="20" y="115" width="40" height="24" fill="#0d1117" stroke="#79c0ff"/><text x="40" y="131" fill="#e6edf3" text-anchor="middle" font-size="8">A</text>
    <rect x="90" y="115" width="40" height="24" fill="#0d1117" stroke="#79c0ff"/><text x="110" y="131" fill="#e6edf3" text-anchor="middle" font-size="8">B</text>
    <rect x="160" y="115" width="40" height="24" fill="#0d1117" stroke="#79c0ff"/><text x="180" y="131" fill="#e6edf3" text-anchor="middle" font-size="8">C</text>
    <line x1="60" y1="127" x2="86" y2="127" stroke="#79c0ff" marker-end="url(#lm)"/>
    <line x1="130" y1="127" x2="156" y2="127" stroke="#79c0ff" marker-end="url(#lm)"/>
    <defs><marker id="lm" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
  </g>
</svg>

Bucket placement (top) is scattered by hash, exactly like `HashMap`; a separate linked list (bottom) tracks insertion order, and iteration follows that list, not the bucket array.

## 5. Runnable example

```java
// HashSetLinkedHashMapOrdering.java
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

public class HashSetLinkedHashMapOrdering {

    // Basic: HashSet gives no predictable order; LinkedHashSet preserves insertion order.
    static void basicLevel() {
        Set<String> hashSet = new HashSet<>();
        hashSet.add("zebra"); hashSet.add("apple"); hashSet.add("mango");
        System.out.println("basic: HashSet order (unspecified) -> " + hashSet);

        Set<String> linkedSet = new LinkedHashSet<>();
        linkedSet.add("zebra"); linkedSet.add("apple"); linkedSet.add("mango");
        System.out.println("basic: LinkedHashSet order (insertion order, guaranteed) -> " + linkedSet);
    }

    // Intermediate: same contrast on the Map side, plus re-inserting an existing key does NOT move it in LinkedHashMap's default mode.
    static void intermediateLevel() {
        Map<String, Integer> linkedMap = new LinkedHashMap<>();
        linkedMap.put("first", 1);
        linkedMap.put("second", 2);
        linkedMap.put("third", 3);
        linkedMap.put("first", 100); // updates the value, but does NOT move "first" to the end (default insertion-order mode)
        System.out.println("intermediate: LinkedHashMap order after re-inserting \"first\" -> " + linkedMap.keySet());
        System.out.println("intermediate: \"first\" stays at its original position; value updated -> " + linkedMap.get("first"));
    }

    // Advanced: access-order LinkedHashMap + removeEldestEntry -- a working LRU cache in a few lines.
    static class LruCache<K, V> extends LinkedHashMap<K, V> {
        private final int capacity;

        LruCache(int capacity) {
            super(16, 0.75f, true); // true = access-order: get() moves an entry to the end
            this.capacity = capacity;
        }

        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity; // evict the least-recently-used entry once over capacity
        }
    }

    static void advancedLevel() {
        LruCache<String, Integer> cache = new LruCache<>(3);
        cache.put("a", 1);
        cache.put("b", 2);
        cache.put("c", 3);
        cache.get("a"); // accessing "a" marks it most-recently-used, moving it to the end
        cache.put("d", 4); // over capacity -- evicts the least-recently-used entry, which is now "b"

        System.out.println("advanced: LRU cache contents after evicting the least-recently-used entry -> " + cache.keySet());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `HashSetLinkedHashMapOrdering.java`, then run `java HashSetLinkedHashMapOrdering.java`.

## 6. Walkthrough

1. `basicLevel()` adds the same three strings to a `HashSet` and a `LinkedHashSet`. The `HashSet`'s printed order reflects internal bucket placement (unpredictable, and not guaranteed stable across Java versions). The `LinkedHashSet`'s printed order exactly matches insertion order (`zebra, apple, mango`), guaranteed by its internal linked list.
2. `intermediateLevel()` shows `LinkedHashMap`'s default mode tracks *insertion* order specifically — re-inserting an existing key (`"first"`) updates its value but does not move it within the iteration order, since it was not newly inserted, just updated.
3. `advancedLevel()`'s `LruCache` switches to access-order mode (`true` as the third constructor argument), so `get("a")` moves `"a"` to the end of the internal list, marking it most-recently-used. `removeEldestEntry` is called automatically after every insert; returning `true` once `size() > capacity` evicts whatever is currently at the front of the list — the least-recently-used entry. After accessing `"a"` and then inserting `"d"` (pushing the cache over capacity `3`), `"b"` (never accessed, and inserted before `"a"` was last touched) is the one evicted.

## 7. Gotchas & takeaways

> Gotcha: `LinkedHashMap`'s extra linked-list bookkeeping means it has slightly higher memory overhead and marginally slower insert/remove than plain `HashMap` — a difference only worth caring about at very large scale, but worth knowing rather than reaching for `LinkedHashMap` by default when order genuinely does not matter.

- `HashSet` is backed by a `HashMap`, so it shares `HashMap`'s unpredictable iteration order.
- `LinkedHashMap`/`LinkedHashSet` add a separate doubly linked list to guarantee insertion order (or access order) while keeping hash-table lookup speed.
- Access-order mode plus overriding `removeEldestEntry()` is the standard way to build an LRU cache in Java without a custom doubly linked list.
- Related concepts: [HashMap internals (buckets, treeify at 8)](0091-hashmap-internals-buckets-treeify-at-8.md), [java.util.LinkedList (List + Deque)](0059-java-util-linkedlist-list-deque.md).
