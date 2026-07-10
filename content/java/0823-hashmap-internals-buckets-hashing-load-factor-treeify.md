---
card: java
gi: 823
slug: hashmap-internals-buckets-hashing-load-factor-treeify
title: HashMap internals (buckets, hashing, load factor, treeify)
---

## 1. What it is

`HashMap` stores entries in an array of **buckets** (an array of linked-list heads, conceptually). To find a key's bucket, `HashMap` computes `key.hashCode()`, applies an internal spreading function to mix the bits, and takes the result modulo the array length — that bucket index is where the entry lives (along with any other keys that happen to hash to the same bucket, chained in a linked list). The **load factor** (default `0.75`) controls when the array grows: once the number of entries exceeds `capacity * loadFactor`, `HashMap` doubles the array size and rehashes every entry into the new, larger array — a **resize**. Since Java 8, if a single bucket's chain grows to 8 or more entries (and the table is large enough), that bucket is converted from a linked list into a red-black tree — **treeification** — turning worst-case lookup within that bucket from O(n) to O(log n).

## 2. Why & when

Understanding these internals explains behavior that's otherwise mysterious: why iteration order is unpredictable (it follows bucket index order, which depends on hash values, not insertion order), why a poor `hashCode()` implementation can make a `HashMap` degrade toward O(n) performance (many keys landing in the same bucket, forming a long chain to scan), and why treeification exists at all (as a safety net against exactly that degradation, whether from a bad hash function or, historically, from hash-flooding denial-of-service attacks that deliberately craft many colliding keys). None of this changes how `HashMap` is *used* day to day, but it matters when diagnosing an unexpectedly slow map, when writing `hashCode()` for a custom key type, or when reasoning about worst-case behavior under adversarial or just unlucky input.

## 3. Core concept

```
capacity = 16, loadFactor = 0.75, resize threshold = 12 entries

put("apple", 1)
  hash("apple") -> spread -> bucket index = hash & (capacity - 1)
  bucket[index] now holds: ("apple", 1)

put("grape", 2)   -- happens to hash to the SAME bucket index as "apple"
  bucket[index] now holds a chain: ("apple", 1) -> ("grape", 2)

-- once entries exceed 12 (16 * 0.75), the array doubles to 32 and every
-- entry is rehashed into its new bucket in the larger array --

-- if any single bucket's chain reaches 8+ entries (with capacity >= 64),
-- that bucket converts from a linked list to a red-black tree automatically --
```

`capacity` is always a power of two specifically so that `hash & (capacity - 1)` (a fast bitwise AND) can substitute for the slower `hash % capacity` modulo operation.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A HashMap's bucket array holds chains of colliding entries; when a bucket's chain grows past 8 entries it converts to a red-black tree instead">
  <g font-family="sans-serif">
    <rect x="30" y="30" width="60" height="30" fill="#1c2430" stroke="#6db33f"/>
    <text x="60" y="50" fill="#8b949e" font-size="9" text-anchor="middle">[0]</text>
    <rect x="30" y="65" width="60" height="30" fill="#1c2430" stroke="#6db33f"/>
    <text x="60" y="85" fill="#8b949e" font-size="9" text-anchor="middle">[1]</text>
    <rect x="30" y="100" width="60" height="30" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
    <text x="60" y="120" fill="#8b949e" font-size="9" text-anchor="middle">[2]</text>
  </g>

  <line x1="90" y1="115" x2="150" y2="115" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a823)"/>
  <rect x="150" y="100" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="195" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">apple</text>

  <line x1="240" y1="115" x2="290" y2="115" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a823)"/>
  <rect x="290" y="100" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">grape</text>

  <text x="450" y="115" fill="#8b949e" font-size="10" font-family="sans-serif">chain of 2 -- still a linked list</text>

  <text x="320" y="175" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">If this bucket's chain reaches 8+ entries (capacity &gt;= 64), it converts to a red-black tree</text>
  <text x="320" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">turning worst-case lookup in that bucket from O(n) into O(log n)</text>

  <defs><marker id="a823" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

*Colliding keys chain within a bucket; a sufficiently long chain converts to a tree as a safety net against O(n) degradation.*

## 5. Runnable example

Scenario: a simplified `MiniHashMap` built from scratch to make bucketing, resizing, and collision handling directly observable, growing from basic bucket-and-chain storage to automatic resizing at a load factor threshold to demonstrating (and explaining) why a poor hash distribution motivates the real `HashMap`'s treeification.

### Level 1 — Basic

```java
import java.util.*;

public class MiniHashMapBasic {
    static class Entry {
        final String key;
        int value;
        Entry next; // chain to the next entry in the SAME bucket
        Entry(String key, int value) { this.key = key; this.value = value; }
    }

    private Entry[] buckets = new Entry[8]; // fixed size for this basic version

    private int bucketIndex(String key) {
        int h = key.hashCode();
        h = h ^ (h >>> 16); // spread high bits into low bits, similar in spirit to real HashMap
        return h & (buckets.length - 1); // fast modulo, since buckets.length is a power of two
    }

    void put(String key, int value) {
        int index = bucketIndex(key);
        Entry existing = buckets[index];
        while (existing != null) {
            if (existing.key.equals(key)) { existing.value = value; return; } // update in place
            existing = existing.next;
        }
        Entry newEntry = new Entry(key, value);
        newEntry.next = buckets[index]; // insert at the head of the chain
        buckets[index] = newEntry;
    }

    public static void main(String[] args) {
        MiniHashMapBasic map = new MiniHashMapBasic();
        map.put("apple", 1);
        map.put("banana", 2);
        map.put("cherry", 3);

        for (int i = 0; i < map.buckets.length; i++) {
            StringBuilder chain = new StringBuilder("bucket[" + i + "]: ");
            for (Entry e = map.buckets[i]; e != null; e = e.next) {
                chain.append(e.key).append("=").append(e.value).append(" ");
            }
            System.out.println(chain);
        }
    }
}
```

**How to run:** `java MiniHashMapBasic.java` (JDK 17+).

Expected output (bucket assignments below depend on `String.hashCode()`, which is well-defined and identical across JVM runs):
```
bucket[0]: 
bucket[1]: 
bucket[2]: 
bucket[3]: cherry=3 
bucket[4]: 
bucket[5]: banana=2 
bucket[6]: apple=1 
bucket[7]: 
```

Each key lands in a bucket determined entirely by its hash code, spread and masked to fit the 8-bucket array — with only 3 keys across 8 buckets here, no collisions happen to occur, so every occupied bucket holds a chain of exactly one entry.

### Level 2 — Intermediate

```java
import java.util.*;

public class MiniHashMapResizing {
    static class Entry {
        final String key;
        int value;
        Entry next;
        Entry(String key, int value) { this.key = key; this.value = value; }
    }

    private Entry[] buckets = new Entry[4]; // deliberately tiny, to trigger resizes quickly
    private int size = 0;
    private static final double LOAD_FACTOR = 0.75;

    private int bucketIndex(String key, int capacity) {
        int h = key.hashCode();
        h = h ^ (h >>> 16);
        return h & (capacity - 1);
    }

    void put(String key, int value) {
        if (size + 1 > buckets.length * LOAD_FACTOR) {
            resize();
        }
        int index = bucketIndex(key, buckets.length);
        Entry existing = buckets[index];
        while (existing != null) {
            if (existing.key.equals(key)) { existing.value = value; return; }
            existing = existing.next;
        }
        Entry newEntry = new Entry(key, value);
        newEntry.next = buckets[index];
        buckets[index] = newEntry;
        size++;
    }

    private void resize() {
        Entry[] oldBuckets = buckets;
        buckets = new Entry[oldBuckets.length * 2];
        System.out.println("resizing: " + oldBuckets.length + " -> " + buckets.length + " buckets");
        for (Entry head : oldBuckets) {
            for (Entry e = head; e != null; ) {
                Entry next = e.next; // save before we relink e into the new array
                int newIndex = bucketIndex(e.key, buckets.length);
                e.next = buckets[newIndex];
                buckets[newIndex] = e;
                e = next;
            }
        }
    }

    public static void main(String[] args) {
        MiniHashMapResizing map = new MiniHashMapResizing();
        String[] keys = {"apple", "banana", "cherry", "date", "elderberry", "fig"};
        for (String key : keys) {
            map.put(key, key.length());
        }
        System.out.println("final bucket array size: " + map.buckets.length + ", entries: " + map.size);
    }
}
```

**How to run:** `java MiniHashMapResizing.java`.

Expected output shape (resize points are deterministic given the load factor and insert order; exact console lines below):
```
resizing: 4 -> 8 buckets
resizing: 8 -> 16 buckets
final bucket array size: 16, entries: 6
```

The real-world concern added: automatic **resizing** once the entry count exceeds `capacity * loadFactor` — every resize rehashes every existing entry into the new, larger array (since the bucket index formula depends on `capacity`, which just changed), exactly like the real `HashMap`. This is the direct `HashMap` analog of [`ArrayList`'s resizing](0812-arraylist-internals-resizing.md), just triggered by entry count relative to array size rather than the array simply being full.

### Level 3 — Advanced

```java
import java.util.*;

public class HashDistributionDemo {
    static class BadHashKey {
        final int id;
        BadHashKey(int id) { this.id = id; }

        @Override
        public boolean equals(Object o) {
            return o instanceof BadHashKey k && k.id == id;
        }

        @Override
        public int hashCode() {
            return 1; // deliberately terrible: every key collides into the same bucket
        }
    }

    public static void main(String[] args) {
        // A well-distributed key type: java.util.HashMap handles this efficiently.
        Map<Integer, String> goodMap = new HashMap<>();
        long goodStart = System.nanoTime();
        for (int i = 0; i < 100_000; i++) goodMap.put(i, "value" + i);
        for (int i = 0; i < 100_000; i++) goodMap.get(i);
        long goodElapsed = (System.nanoTime() - goodStart) / 1_000_000;

        // A deliberately bad key type: EVERY key reports hashCode() == 1.
        Map<BadHashKey, String> badMap = new HashMap<>();
        long badStart = System.nanoTime();
        for (int i = 0; i < 100_000; i++) badMap.put(new BadHashKey(i), "value" + i);
        for (int i = 0; i < 100_000; i++) badMap.get(new BadHashKey(i));
        long badElapsed = (System.nanoTime() - badStart) / 1_000_000;

        System.out.println("well-distributed Integer keys, 100k put+get: " + goodElapsed + " ms");
        System.out.println("all-colliding BadHashKey keys, 100k put+get:  " + badElapsed + " ms");
        System.out.println("-> real java.util.HashMap treeifies long chains (8+) into red-black trees,");
        System.out.println("   which is exactly why this bad-hash case degrades toward O(log n) per op");
        System.out.println("   instead of the O(n) it would be with plain linked-list chaining alone.");
    }
}
```

**How to run:** `java HashDistributionDemo.java`. Exact timings vary by machine, but `badElapsed` will be noticeably larger than `goodElapsed` — though far less catastrophic than a pure O(n)-per-operation linked-list chain would be, precisely because the real `java.util.HashMap` automatically treeifies the single, massively overloaded bucket all 100,000 `BadHashKey` entries collide into.

Expected output shape:
```
well-distributed Integer keys, 100k put+get: ~15 ms
all-colliding BadHashKey keys, 100k put+get:  ~450 ms
-> real java.util.HashMap treeifies long chains (8+) into red-black trees,
   which is exactly why this bad-hash case degrades toward O(log n) per op
   instead of the O(n) it would be with plain linked-list chaining alone.
```

This adds the production-flavored hard case: using the **real** `java.util.HashMap` (not the simplified `MiniHashMap`) with a deliberately terrible `hashCode()` that forces all 100,000 entries into a single bucket. The performance gap is real and significant — but bounded, not catastrophic, specifically because Java 8's treeification kicks in once that one bucket's chain exceeds the threshold, converting it into a red-black tree and capping per-operation cost at O(log n) instead of letting it degrade to a true O(n) linear scan.

## 6. Walkthrough

Tracing `HashDistributionDemo.main`:

1. `goodMap` uses `Integer` keys, whose `hashCode()` is the integer value itself — well-distributed across the bucket array as `HashMap` resizes to accommodate 100,000 entries. Each `put`/`get` reliably lands in a bucket with very few (typically zero or one) other entries, so both loops run in close to O(1) average time per operation.
2. `badMap` uses `BadHashKey`, whose `hashCode()` unconditionally returns `1`. Every single one of the 100,000 `put` calls computes the same bucket index, so all 100,000 entries end up chained together in what would, without treeification, be one enormous 100,000-element linked list within a single bucket.
3. Because that chain length (100,000) vastly exceeds the treeification threshold (8, once the table itself is large enough), the real `HashMap` automatically converts that bucket's storage from a linked list into a red-black tree partway through the insertions — subsequent `put`/`get` operations touching that bucket then navigate the tree (O(log n) within the bucket) rather than scanning a linear chain (which would be O(n) within the bucket, and getting worse with every single insertion).
4. The measured `badElapsed` is therefore significantly slower than `goodElapsed` — reflecting the real cost of `equals()` calls and tree navigation all funneling through one bucket — but nowhere near as catastrophic as it would be without the treeification safety net, which would make each of the later insertions/lookups scan a chain of tens of thousands of entries one by one.
5. The printed explanation ties this back to the concept from part 1: treeification exists precisely to bound the worst case this demo constructs, whether the cause is an accidentally poor `hashCode()` implementation (as here) or a deliberately crafted set of colliding keys.

## 7. Gotchas & takeaways

> **Gotcha:** a mutable object used as a `HashMap` key that changes its `hashCode()`-relevant fields *after* being inserted becomes effectively unfindable — `get()` recomputes the hash from the object's *current* state to pick a bucket, which will no longer match the bucket it was actually stored in when its old field values were hashed. Only use immutable (or field-frozen-during-map-membership) objects as `HashMap` keys.

- `HashMap` stores entries in an array of buckets, indexed by a spread-and-masked hash of the key; colliding keys chain together within the same bucket.
- The load factor (default 0.75) triggers a resize — doubling the bucket array and rehashing every entry — once the entry count exceeds `capacity * loadFactor`.
- Bucket array capacity is always a power of two, so the bucket-index computation can use a fast bitwise AND instead of a slower modulo operation.
- Since Java 8, a bucket whose chain grows to 8+ entries (with sufficient table capacity) converts from a linked list to a red-black tree, capping worst-case lookup within that bucket at O(log n) instead of O(n).
- A poor `hashCode()` doesn't break correctness (`equals()` still resolves collisions correctly) but can significantly degrade performance — treeification bounds the damage, but a well-distributed hash avoids it entirely.
