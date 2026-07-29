---
card: leetcode-patterns
gi: 577
slug: design-hashmap
title: Design HashMap
---

## 1. What it is

Design a `MyHashMap` class supporting `put(key, value)` (insert or overwrite), `get(key)` (return the value, or `-1` if absent), and `remove(key)`, **without using any built-in hash map or hash set type**. Example: `put(1,1)`, `put(2,2)`, `get(1)` → `1`, `get(3)` → `-1`, `put(2,1)` (overwrite), `get(2)` → `1`, `remove(2)`, `get(2)` → `-1`.

## 2. Why & when

This problem asks you to build, by hand, the exact structure a language's built-in `HashMap` normally hides from you: an array of "buckets," a hash function that maps a key to a bucket index, and a collision-resolution strategy for keys that land in the same bucket. Constraints: keys and values are non-negative integers up to `10^6`, up to `10^4` calls — small enough that a straightforward bucket array with chaining comfortably meets the time limit.

## 3. Core concept

**Key idea:** allocate a fixed-size array of buckets (for example, 1000 buckets). Map each key to a bucket index with `key % numBuckets`. Because different keys can map to the same bucket (a **collision**), store each bucket as a small list of `(key, value)` pairs, and scan that short list on `get`/`put`/`remove`.

**Steps:**
1. `put(key, value)`: compute `bucket = key % numBuckets`. Scan that bucket's list; if `key` is already present, overwrite its value. Otherwise, append `(key, value)`.
2. `get(key)`: compute the same `bucket` index. Scan its list for `key`; return the matching value, or `-1` if not found.
3. `remove(key)`: compute the bucket, scan for `key`, and remove that pair if found.

**Why a fixed bucket count with chaining is enough here:** with `10^4` calls spread across 1000 buckets, each bucket holds on average about 10 entries — a short list scan stays fast in practice, even though its worst-case is O(n) if every key happened to collide into one bucket. A production `HashMap` avoids that worst case by resizing (growing the bucket array) as entries accumulate, keeping the average bucket size small regardless of total size.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array of buckets, each holding a short chained list of key-value pairs for keys that collide">
  <g font-family="sans-serif" font-size="12">
    <rect x="20" y="20" width="60" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="50" y="40" fill="#8b949e" text-anchor="middle" font-size="10">bucket 0</text>
    <rect x="90" y="20" width="60" height="30" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="40" fill="#8b949e" text-anchor="middle" font-size="10">bucket 1</text>
    <rect x="160" y="20" width="60" height="30" fill="#161b22" stroke="#30363d"/>
    <text x="190" y="40" fill="#8b949e" text-anchor="middle" font-size="10">bucket 2</text>
    <line x1="120" y1="50" x2="120" y2="80" stroke="#79c0ff"/>
    <rect x="70" y="80" width="100" height="30" rx="4" fill="#161b22" stroke="#79c0ff"/>
    <text x="120" y="100" fill="#e6edf3" text-anchor="middle" font-size="11">(1, "a")</text>
    <line x1="170" y1="95" x2="220" y2="95" stroke="#79c0ff" marker-end="url(#a4)"/>
    <rect x="220" y="80" width="100" height="30" rx="4" fill="#161b22" stroke="#79c0ff"/>
    <text x="270" y="100" fill="#e6edf3" text-anchor="middle" font-size="11">(1001, "b")</text>
    <defs><marker id="a4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
    <text x="350" y="150" fill="#8b949e" text-anchor="middle">keys 1 and 1001 both hash to bucket 1 (1 % 1000 == 1001 % 1000): chained together</text>
  </g>
</svg>

Two different keys that hash to the same bucket index are chained into that bucket's list — a collision, resolved by scanning the short chain instead of the whole map.

## 5. Runnable example

**Level 1 — Brute force.** Scan a plain `List<int[]>` of all `(key, value)` pairs on every call. O(n) per call regardless of key.

**KEY INSIGHT:** hashing (`key % numBuckets`) splits one long list into many short ones, so each call only scans the handful of entries that share the same bucket, not every entry ever inserted.

**Level 2 — Optimal.** Bucket array of size 1000, each bucket a small chained list. O(n / numBuckets) average per call.

**Level 3 — Hardened.** Correctly overwrites an existing key on `put` rather than duplicating it, and correctly no-ops when `remove` targets a key that is not present.

```java
// MyHashMap.java
import java.util.*;

public class MyHashMap {

    private static final int BUCKETS = 1000;
    private final List<int[]>[] buckets;

    @SuppressWarnings("unchecked")
    public MyHashMap() {
        buckets = new List[BUCKETS];
        for (int i = 0; i < BUCKETS; i++) buckets[i] = new ArrayList<>();
    }

    private int bucketIndex(int key) {
        return key % BUCKETS;
    }

    public void put(int key, int value) {
        List<int[]> bucket = buckets[bucketIndex(key)];
        for (int[] pair : bucket) {
            if (pair[0] == key) {
                pair[1] = value;
                return;
            }
        }
        bucket.add(new int[]{key, value});
    }

    public int get(int key) {
        List<int[]> bucket = buckets[bucketIndex(key)];
        for (int[] pair : bucket) {
            if (pair[0] == key) return pair[1];
        }
        return -1;
    }

    public void remove(int key) {
        List<int[]> bucket = buckets[bucketIndex(key)];
        bucket.removeIf(pair -> pair[0] == key);
    }

    public static void main(String[] args) {
        MyHashMap map = new MyHashMap();
        map.put(1, 1);
        map.put(2, 2);
        System.out.println(map.get(1)); // 1
        System.out.println(map.get(3)); // -1
        map.put(2, 1);                  // overwrite
        System.out.println(map.get(2)); // 1
        map.remove(2);
        System.out.println(map.get(2)); // -1
    }
}
```

**How to run:** save as `MyHashMap.java`, then run `java MyHashMap.java`.

## 6. Walkthrough

Trace `put(1,1)`, `put(1001,1)`, `get(1)`:

1. `put(1,1)`: `bucketIndex(1) = 1 % 1000 = 1`. Bucket 1's list is empty, so append `[1,1]`.
2. `put(1001,1)`: `bucketIndex(1001) = 1001 % 1000 = 1`. Same bucket as key `1` — a collision. Scan bucket 1's list: no entry has key `1001`, so append `[1001,1]`. Bucket 1 now holds `[[1,1],[1001,1]]`.
3. `get(1)`: `bucketIndex(1) = 1`. Scan bucket 1's list: the first entry, `[1,1]`, matches key `1`. Return `1`.

Even with a collision, `get` only scans the two entries in bucket 1, not the whole map — the hash function keeps each bucket's chain short.

## 7. Gotchas & takeaways

> Gotcha: forgetting to check for an existing key inside `put` (and instead always appending) silently creates duplicate entries for the same key — later `get` calls would return whichever duplicate the scan hits first, not necessarily the most recent value.

- Signal: "design a hash map/set from scratch" means implement the bucket-array-plus-hash-function mechanism yourself, not just wrap a built-in `HashMap`.
- `key % numBuckets` is the hash function here; a good hash function spreads keys evenly so chains stay short.
- Related problems: Design HashSet (the same mechanism, without storing a value — only presence matters).
