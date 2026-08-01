---
card: data-structures
gi: 85
slug: hash-functions-desirable-properties
title: Hash functions & desirable properties
---

## 1. What it is

A **hash function** takes a key (a string, a number, an object) and produces a fixed-size integer, called a **hash code**. That integer is then used to pick a **bucket** — a slot index in an underlying array — where the key's value gets stored. This is the mechanism that lets a hash table find a key's value without scanning every entry.

## 2. Why & when

Every hash-based structure — `HashMap`, `HashSet`, and their relatives — depends entirely on the quality of the hash function it uses. A bad hash function silently turns a hash table's average O(1) operations into O(n) ones, because it stops spreading keys evenly across buckets. Understanding what makes a hash function good tells you why `hashCode()` matters, and what can go wrong if you write your own.

## 3. Core concept

**Desirable property 1 — deterministic.** The same key must always produce the same hash code, for as long as that key is used in a hash table. If a key's hash code could change between calls, the table would look for it in the wrong bucket after the change and fail to find it, even though the key is still logically present.

**Desirable property 2 — uniform distribution.** A good hash function spreads keys evenly across the available buckets, so no single bucket accumulates far more entries than the others. Poor distribution — many keys landing in the same few buckets — degrades lookups toward O(n), since each bucket must then be searched linearly.

**Desirable property 3 — fast to compute.** Since the hash function runs on every insert, lookup, and delete, it must be cheap — proportional to the size of the key's data, not to the size of the whole table.

**Property 4 — small changes should produce very different outputs (avalanche effect).** Two keys that differ by a tiny amount (like `"cat"` and `"cbt"`) should ideally land in unrelated buckets, not adjacent ones — this prevents clusters of "almost identical" keys from all landing near each other.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three keys hashed to bucket indices, with a good hash function spreading them across separate buckets and a poor hash function clustering them into one bucket">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#79c0ff">good hash function -- spreads keys out</text>
    <text x="20" y="40" fill="#e6edf3">"cat" -&gt; hash -&gt; bucket 2</text>
    <text x="20" y="60" fill="#e6edf3">"dog" -&gt; hash -&gt; bucket 5</text>
    <text x="20" y="80" fill="#e6edf3">"bee" -&gt; hash -&gt; bucket 0</text>

    <text x="340" y="16" fill="#f0883e">poor hash function -- clusters keys</text>
    <text x="340" y="40" fill="#e6edf3">"cat" -&gt; hash -&gt; bucket 3</text>
    <text x="340" y="60" fill="#e6edf3">"dog" -&gt; hash -&gt; bucket 3</text>
    <text x="340" y="80" fill="#e6edf3">"bee" -&gt; hash -&gt; bucket 3</text>
    <text x="340" y="105" fill="#f0883e">all three collide -&gt; bucket 3 becomes a linear-scan list of 3</text>
  </g>
</svg>

A good hash function spreads keys across distinct buckets, so each bucket holds close to zero or one entries; a poor one clusters keys, degrading lookups toward a linear scan.

## 5. Runnable example

```java
// HashFunctionProperties.java
import java.util.HashMap;
import java.util.Map;

public class HashFunctionProperties {

    // Basic: hashCode() is deterministic -- the same object's hash code never changes across calls.
    static void basicLevel() {
        String key = "hello";
        int h1 = key.hashCode();
        int h2 = key.hashCode();
        System.out.println("basic: same string, same hash code both times -> " + (h1 == h2) + " (" + h1 + ")");
    }

    // A deliberately POOR hash function -- constant, so every key collides into bucket 0.
    static class PoorKey {
        String value;
        PoorKey(String value) { this.value = value; }
        @Override public int hashCode() { return 42; } // constant: every key hashes the same, defeating distribution
        @Override public boolean equals(Object o) { return o instanceof PoorKey p && p.value.equals(value); }
    }

    // A reasonable hash function -- delegates to the wrapped String's well-distributed hashCode().
    static class GoodKey {
        String value;
        GoodKey(String value) { this.value = value; }
        @Override public int hashCode() { return value.hashCode(); } // spreads out, same as String's own hash
        @Override public boolean equals(Object o) { return o instanceof GoodKey g && g.value.equals(value); }
    }

    static void intermediateLevel() {
        Map<PoorKey, Integer> poorMap = new HashMap<>();
        poorMap.put(new PoorKey("a"), 1);
        poorMap.put(new PoorKey("b"), 2);
        poorMap.put(new PoorKey("c"), 3);
        System.out.println("intermediate: all PoorKeys hash to the same bucket -> "
            + new PoorKey("a").hashCode() + ", " + new PoorKey("b").hashCode() + ", " + new PoorKey("c").hashCode());
        System.out.println("intermediate: still correct (equals() finds the right entry), just slower under load");

        Map<GoodKey, Integer> goodMap = new HashMap<>();
        goodMap.put(new GoodKey("a"), 1);
        goodMap.put(new GoodKey("b"), 2);
        System.out.println("intermediate: GoodKeys hash differently -> "
            + new GoodKey("a").hashCode() + " vs " + new GoodKey("b").hashCode());
    }

    // Advanced: measure the practical effect -- many poor-hash keys in one bucket vs spread out, via a crude collision count.
    static void advancedLevel() {
        int bucketCount = 16;
        int[] poorBuckets = new int[bucketCount];
        int[] goodBuckets = new int[bucketCount];

        for (int i = 0; i < 1000; i++) {
            int poorHash = 42; // constant, like PoorKey
            int goodHash = ("key" + i).hashCode();
            poorBuckets[Math.floorMod(poorHash, bucketCount)]++;
            goodBuckets[Math.floorMod(goodHash, bucketCount)]++;
        }

        System.out.println("advanced: poor hash -- bucket 0 holds -> " + poorBuckets[0] + " of 1000 keys (every key)");
        int maxGoodBucket = java.util.Arrays.stream(goodBuckets).max().getAsInt();
        System.out.println("advanced: good hash -- largest bucket holds -> " + maxGoodBucket + " of 1000 keys (roughly evenly spread)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `HashFunctionProperties.java`, then run `java HashFunctionProperties.java`.

## 6. Walkthrough

1. `basicLevel()` calls `hashCode()` on the same `String` twice and confirms both calls return the identical value — determinism, the first required property.
2. `intermediateLevel()` builds a `PoorKey` whose `hashCode()` always returns `42`. Every `PoorKey` instance lands in the exact same bucket, no matter its `value`. The map still works correctly — `equals()` still distinguishes different keys within that one crowded bucket — but every lookup now has to linearly scan that bucket instead of jumping straight to the right entry. `GoodKey` delegates to `String`'s own well-tested hash code, giving proper distribution instead.
3. `advancedLevel()` simulates 1,000 keys with both hash strategies, sorted into 16 buckets by `hash % 16`. The constant "poor" hash puts all 1,000 keys in bucket `0`. The "good" hash (based on distinct strings) spreads them so no single bucket holds dramatically more than `1000 / 16 ≈ 62` — a concrete before/after showing why hash quality matters.

## 7. Gotchas & takeaways

> Gotcha: a hash code being deterministic *within a single run* is not the same as being deterministic *across runs* — some hash codes (like `Object`'s default identity-based hash) can differ between JVM executions. Never persist a hash code to disk or send it across a network expecting it to mean the same thing later; only rely on it for the lifetime of the objects in memory.

- A hash function must be deterministic (same key, same hash, every time it is called) or lookups silently break.
- Good distribution across buckets is what keeps operations close to O(1); poor distribution degrades toward O(n).
- The hash function must be cheap to compute, since it runs on every insert, lookup, and delete.
- Related concepts: [hashCode/equals for correct keys](0093-hashcode-equals-for-correct-keys.md), [Collision resolution: separate chaining](0087-collision-resolution-separate-chaining.md).
