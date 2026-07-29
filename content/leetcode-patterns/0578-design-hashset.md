---
card: leetcode-patterns
gi: 578
slug: design-hashset
title: Design HashSet
---

## 1. What it is

Design a `MyHashSet` class supporting `add(key)`, `remove(key)`, and `contains(key)` (returns `true`/`false`), **without using any built-in hash map or hash set type**. Example: `add(1)`, `add(2)`, `contains(1)` → `true`, `contains(3)` → `false`, `add(2)` (no-op, already present), `remove(2)`, `contains(2)` → `false`.

## 2. Why & when

This is [Design HashMap](0577-design-hashmap.md)'s twin: the same bucket-array-plus-hashing mechanism, but tracking only whether a key is present, not an associated value. Constraints: keys are non-negative integers up to `10^6`, up to `10^4` calls — the same scale that makes a fixed bucket array with chaining fast enough.

## 3. Core concept

**Key idea:** reuse the exact same structure as a hash map — an array of buckets, each a small list, indexed by `key % numBuckets` — but each bucket stores only the keys themselves, since there is no value to associate.

**Steps:**
1. `add(key)`: compute `bucket = key % numBuckets`. Scan the bucket's list; if `key` is already present, do nothing (a set has no duplicates). Otherwise, add it.
2. `contains(key)`: compute the same `bucket`. Scan its list for `key`; return whether it is found.
3. `remove(key)`: compute the bucket, scan for `key`, and remove it if found; otherwise, do nothing.

**Why this is simpler than the map version, not different:** a hash set is a hash map where every value is implicitly "present" — you can build one by wrapping a hash map and ignoring the value, or, as below, by storing keys directly with no paired value, saving a small amount of memory per entry.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bucket array storing only keys, no values, for a hash set">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="60" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="50" y="40" fill="#8b949e" text-anchor="middle" font-size="10">bucket 0</text>
    <rect x="90" y="20" width="60" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="40" fill="#8b949e" text-anchor="middle" font-size="10">bucket 1</text>
    <line x1="120" y1="50" x2="120" y2="80" stroke="#79c0ff"/>
    <rect x="80" y="80" width="80" height="30" rx="4" fill="#161b22" stroke="#79c0ff"/>
    <text x="120" y="100" fill="#e6edf3" text-anchor="middle" font-size="11">key 1</text>
    <line x1="160" y1="95" x2="210" y2="95" stroke="#79c0ff" marker-end="url(#a5)"/>
    <rect x="210" y="80" width="90" height="30" rx="4" fill="#161b22" stroke="#79c0ff"/>
    <text x="255" y="100" fill="#e6edf3" text-anchor="middle" font-size="11">key 1001</text>
    <defs><marker id="a5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
    <text x="350" y="135" fill="#8b949e" text-anchor="middle">only presence is tracked - no value slot per entry</text>
  </g>
</svg>

Identical bucket-and-chain layout to a hash map, but each entry is just a key — presence in a bucket's list is the entire piece of information stored.

## 5. Runnable example

**Level 1 — Brute force.** Scan a plain `List<Integer>` on every call. O(n) per call.

**KEY INSIGHT:** hashing splits the keys into short independent chains, exactly as with a hash map, so each call only scans a small fraction of all stored keys.

**Level 2 — Optimal.** Bucket array of size 1000, each bucket a small chained list of keys. O(n / numBuckets) average per call.

**Level 3 — Hardened.** Correctly no-ops when `add` targets an already-present key (no duplicates) and when `remove` targets an absent key.

```java
// MyHashSet.java
import java.util.*;

public class MyHashSet {

    private static final int BUCKETS = 1000;
    private final List<Integer>[] buckets;

    @SuppressWarnings("unchecked")
    public MyHashSet() {
        buckets = new List[BUCKETS];
        for (int i = 0; i < BUCKETS; i++) buckets[i] = new ArrayList<>();
    }

    private int bucketIndex(int key) {
        return key % BUCKETS;
    }

    public void add(int key) {
        List<Integer> bucket = buckets[bucketIndex(key)];
        if (!bucket.contains(key)) {
            bucket.add(key);
        }
    }

    public void remove(int key) {
        buckets[bucketIndex(key)].remove(Integer.valueOf(key));
    }

    public boolean contains(int key) {
        return buckets[bucketIndex(key)].contains(key);
    }

    public static void main(String[] args) {
        MyHashSet set = new MyHashSet();
        set.add(1);
        set.add(2);
        System.out.println(set.contains(1)); // true
        System.out.println(set.contains(3)); // false
        set.add(2);                           // no-op, already present
        System.out.println(set.contains(2)); // true
        set.remove(2);
        System.out.println(set.contains(2)); // false
    }
}
```

**How to run:** save as `MyHashSet.java`, then run `java MyHashSet.java`.

## 6. Walkthrough

Trace `add(1)`, `add(1001)`, `contains(1001)`, `remove(1001)`, `contains(1001)`:

1. `add(1)`: `bucketIndex(1) = 1`. Bucket 1 is empty, `contains(1)` on the bucket list is `false`, so add `1`. Bucket 1: `[1]`.
2. `add(1001)`: `bucketIndex(1001) = 1`, same bucket as before. `1001` is not in `[1]`, so add it. Bucket 1: `[1, 1001]`.
3. `contains(1001)`: `bucketIndex(1001) = 1`. Scan `[1, 1001]`: found. Return `true`.
4. `remove(1001)`: same bucket, `List.remove(Integer.valueOf(1001))` removes it. Bucket 1: `[1]`.
5. `contains(1001)`: scan `[1]`: not found. Return `false`.

## 7. Gotchas & takeaways

> Gotcha: calling `bucket.remove(key)` on a `List<Integer>` with an `int` argument calls the **remove-by-index** overload, not remove-by-value — you must box it as `Integer.valueOf(key)` (or `(Integer) key`) to call the correct remove-by-object overload, or you will silently remove the wrong element (or throw an `IndexOutOfBoundsException`).
- Signal: "design a set from scratch" is the same bucket-and-hash mechanism as a hash map, minus the stored value.
- `add` must check for an existing key first, since a set must never store duplicates.
- Related problems: Design HashMap (identical mechanism, plus a value per key).
