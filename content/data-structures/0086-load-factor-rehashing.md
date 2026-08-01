---
card: data-structures
gi: 86
slug: load-factor-rehashing
title: Load factor & rehashing
---

## 1. What it is

**Load factor** is the ratio of stored entries to the number of buckets in a hash table: `size / bucketCount`. **Rehashing** is the process of growing the bucket array (usually doubling it) and reinserting every existing entry into the new, larger array once the load factor crosses a threshold — Java's `HashMap` default threshold is `0.75`.

## 2. Why & when

Load factor directly controls the tradeoff between memory use and lookup speed. A low load factor means buckets are mostly empty — fast lookups, wasted memory. A high load factor means buckets are crowded — collisions pile up, lookups degrade toward O(n). Rehashing is what keeps a hash table's average O(1) guarantee true as it grows, by periodically restoring room to spread out.

## 3. Core concept

**Why load factor matters.** As more entries get packed into the same fixed number of buckets, more of them collide — multiple keys landing in the same bucket. More collisions mean each bucket holds more entries on average, and each lookup has to check more of them before finding (or ruling out) the target key. Load factor is the single number that predicts how crowded, on average, each bucket currently is.

**The rehashing trigger.** When `size` grows past `capacity * loadFactor`, the table rehashes: it allocates a new bucket array, usually double the old capacity, then walks every existing entry and recomputes which bucket it belongs to in the new, larger array — since the bucket count changed, almost every key's target bucket changes too (bucket index is typically `hash % capacity`, or a bitmask equivalent).

**Why rehashing is what makes amortized O(1) true.** Each individual rehash costs O(n), since every entry must be moved. But rehashes happen exponentially less often as the table grows (doubling means the *next* rehash is twice as far away in terms of entries added), so the total cost of all rehashes, spread out over all the inserts that ever happen, averages out to O(1) per insert — the exact same amortized argument as dynamic array resizing.

**Choosing a load factor.** Java's `HashMap` defaults to `0.75`, a balance between memory overhead and collision frequency, chosen empirically. A lower load factor (like `0.5`) means more memory used but fewer collisions; a higher one (like `0.9`) means less memory but more collisions. You can supply a custom load factor via `new HashMap<>(initialCapacity, loadFactor)`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A hash table with 4 buckets and 3 entries about to cross the 0.75 load factor threshold, triggering a rehash into 8 buckets with entries redistributed">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">before: capacity 4, size 3, load factor 0.75 -- inserting one more triggers rehash</text>
    <rect x="20" y="30" width="30" height="26" fill="#0d1117" stroke="#f0883e"/><text x="35" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">A</text>
    <rect x="55" y="30" width="30" height="26" fill="#0d1117" stroke="#f0883e"/><text x="70" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">B</text>
    <rect x="90" y="30" width="30" height="26" fill="#161b22" stroke="#8b949e"/>
    <rect x="125" y="30" width="30" height="26" fill="#0d1117" stroke="#f0883e"/><text x="140" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">C</text>
    <text x="90" y="90" fill="#79c0ff" text-anchor="middle" font-size="9">rehash: double capacity to 8, reinsert every entry</text>
    <text x="20" y="120" fill="#8b949e">after: capacity 8, size 3, load factor 0.375</text>
    <rect x="20" y="135" width="26" height="24" fill="#161b22" stroke="#8b949e"/>
    <rect x="46" y="135" width="26" height="24" fill="#0d1117" stroke="#79c0ff"/><text x="59" y="151" fill="#e6edf3" text-anchor="middle" font-size="8">A</text>
    <rect x="72" y="135" width="26" height="24" fill="#161b22" stroke="#8b949e"/>
    <rect x="98" y="135" width="26" height="24" fill="#0d1117" stroke="#79c0ff"/><text x="111" y="151" fill="#e6edf3" text-anchor="middle" font-size="8">B</text>
    <rect x="124" y="135" width="26" height="24" fill="#161b22" stroke="#8b949e"/>
    <rect x="150" y="135" width="26" height="24" fill="#161b22" stroke="#8b949e"/>
    <rect x="176" y="135" width="26" height="24" fill="#0d1117" stroke="#79c0ff"/><text x="189" y="151" fill="#e6edf3" text-anchor="middle" font-size="8">C</text>
    <rect x="202" y="135" width="26" height="24" fill="#161b22" stroke="#8b949e"/>
  </g>
</svg>

Growing the bucket array from `4` to `8` roughly halves the load factor, spreading the same entries out and reducing collision likelihood.

## 5. Runnable example

```java
// LoadFactorRehashingDemo.java
import java.util.HashMap;
import java.util.Map;

public class LoadFactorRehashingDemo {

    // Basic: default load factor (0.75) -- observe capacity growth as entries are added.
    static void basicLevel() {
        Map<Integer, String> map = new HashMap<>(4); // initial capacity 4, default load factor 0.75
        for (int i = 1; i <= 3; i++) map.put(i, "v" + i); // 3/4 = 0.75, right at the threshold
        System.out.println("basic: 3 entries in capacity-4 map, size -> " + map.size());
        map.put(4, "v4"); // pushes past 0.75 -- triggers a rehash to capacity 8 internally
        System.out.println("basic: after 4th insert (triggers rehash internally), size -> " + map.size());
        System.out.println("basic: map still returns correct values -> " + map.get(1) + ", " + map.get(4));
    }

    // Intermediate: custom load factor -- a lower load factor rehashes sooner (more memory, fewer collisions).
    static void intermediateLevel() {
        Map<Integer, String> denseMap = new HashMap<>(4, 0.5f); // rehashes once size/capacity exceeds 0.5
        for (int i = 1; i <= 2; i++) denseMap.put(i, "v" + i); // 2/4 = 0.5, at the threshold already
        System.out.println("intermediate: custom 0.5 load factor map, size -> " + denseMap.size());
        denseMap.put(3, "v3"); // triggers rehash sooner than the default 0.75 would have
        System.out.println("intermediate: after 3rd insert, still correct -> " + denseMap.get(2));
    }

    // Advanced: pre-sizing to AVOID rehashing entirely, when the final size is known upfront -- a real optimization.
    static void advancedLevel() {
        int expectedEntries = 1000;
        int safeCapacity = (int) (expectedEntries / 0.75) + 1; // size upfront so load factor never crosses 0.75
        Map<Integer, Integer> preSized = new HashMap<>(safeCapacity);

        long t0 = System.nanoTime();
        for (int i = 0; i < expectedEntries; i++) preSized.put(i, i * i);
        long preSizedMs = (System.nanoTime() - t0) / 1_000_000;

        Map<Integer, Integer> defaultSized = new HashMap<>(); // starts small, rehashes multiple times as it grows
        long t1 = System.nanoTime();
        for (int i = 0; i < expectedEntries; i++) defaultSized.put(i, i * i);
        long defaultMs = (System.nanoTime() - t1) / 1_000_000;

        System.out.println("advanced: pre-sized insert time -> " + preSizedMs + " ms, default-sized -> " + defaultMs + " ms");
        System.out.println("advanced: pre-sizing avoids repeated rehash-and-copy work when the final size is known");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `LoadFactorRehashingDemo.java`, then run `java LoadFactorRehashingDemo.java`.

## 6. Walkthrough

1. `basicLevel()` starts with capacity `4`. Three entries give a load factor of exactly `0.75`. The fourth `put` pushes the count to `4`, and `4 / 4 = 1.0 > 0.75`, so `HashMap` internally doubles its bucket array to `8` and reinserts every existing entry (recomputing each one's bucket for the new capacity) before completing the insert. This is invisible from the outside — `map.get(1)` and `map.get(4)` both still return the correct values afterward.
2. `intermediateLevel()` sets a lower load factor of `0.5`, meaning the map rehashes sooner (at half the density) than the default. This trades more memory (more buckets sitting empty on average) for fewer collisions.
3. `advancedLevel()` shows the practical payoff of knowing the final size upfront: pre-sizing the initial capacity so the load factor never crosses the threshold avoids every intermediate rehash-and-copy step entirely, since there is only ever one bucket array allocated. The default-sized map, by contrast, rehashes repeatedly as it grows from its small starting capacity — each rehash an O(n) pass at that point in its growth.

## 7. Gotchas & takeaways

> Gotcha: rehashing after a `HashMap` has been iterated concurrently by another thread (without synchronization) can produce a `ConcurrentModificationException`, or in older Java versions, even corrupt the internal bucket structure — `HashMap` is not thread-safe, and rehashing is exactly the kind of structural change that makes concurrent access dangerous.

- Load factor (`size / capacity`) predicts how crowded, on average, each bucket is — higher load factor means more collisions and slower lookups.
- Rehashing doubles the bucket array and reinserts every entry once load factor crosses the threshold (default `0.75` in Java).
- Each rehash is O(n), but rehashes become exponentially rarer as the table grows, giving amortized O(1) inserts overall — the same argument as dynamic array resizing.
- Pre-sizing a `HashMap`'s initial capacity avoids repeated rehashing when the final size is known in advance.
- Related concepts: [Array resizing / amortized append](0020-array-resizing-amortized-append.md), [Average O(1) insert/lookup/delete](0089-average-o-1-insert-lookup-delete.md).
