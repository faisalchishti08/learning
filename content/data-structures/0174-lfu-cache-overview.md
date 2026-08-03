---
card: data-structures
gi: 174
slug: lfu-cache-overview
title: LFU cache (overview)
---

## 1. What it is

An **LFU (Least Frequently Used) cache** evicts the item with the **lowest access count** when it is full, breaking ties by least-recently-used. This differs from an [LRU cache](0173-lru-cache-hashmap-doubly-linked-list.md), which only tracks recency and ignores how often an item has actually been used overall.

## 2. Why & when

Use an LFU cache when access frequency is a better predictor of future use than recency alone — a popular item accessed 1000 times should probably not be evicted just because it was accessed a moment before a different item that has only ever been accessed once. LRU can be fooled by a single burst of accesses to a rarely-used item right before eviction time; LFU resists that pattern by weighting long-term frequency instead.

## 3. Core concept

**The shape.** Three data structures working together:
- `Map<Key, Node>` for `O(1)` lookup of any item and its current frequency count.
- `Map<Integer, LinkedHashSet<Key>>` (frequency to a set of keys), grouping all keys that currently share the same access count. A `LinkedHashSet` (or a doubly linked list) inside each frequency bucket preserves insertion order, so ties break by least-recently-used within that frequency.
- A tracked `minFrequency` value, always pointing at the lowest non-empty frequency bucket — this is where eviction happens.

**The invariant.** Every key lives in exactly one frequency bucket, matching its current access count. When a key's count increases, it must move from its old bucket to the new (count+1) bucket. `minFrequency` always reflects the true lowest frequency among all present keys.

**Eviction rule.** When the cache is full and a new key must be inserted, evict the **least recently used** key within the **`minFrequency`** bucket — the bucket holding the least-used keys overall, tie-broken by recency inside that bucket.

**Why `minFrequency` needs careful updating.** Every `get` or `put` on an existing key increases its frequency by `1`, moving it out of its current bucket. If that key was the *only* member of the `minFrequency` bucket, and the bucket is now empty, `minFrequency` must increment by `1` too — otherwise it would point at a stale, empty bucket. A brand-new key inserted after an eviction always resets `minFrequency` back to `1`, since a fresh key starts with frequency `1`, which is always the new lowest.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Frequency buckets for an LFU cache, with keys grouped by access count and minFrequency pointing at the lowest non-empty bucket">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">freq=1:</text>
    <rect x="70" y="8" width="60" height="24" fill="#161b22" stroke="#79c0ff"/><text x="100" y="24" text-anchor="middle">D</text>

    <text x="10" y="60">freq=2:</text>
    <rect x="70" y="48" width="60" height="24" fill="#0d1117" stroke="#8b949e"/><text x="100" y="64" text-anchor="middle">B</text>
    <rect x="140" y="48" width="60" height="24" fill="#0d1117" stroke="#8b949e"/><text x="170" y="64" text-anchor="middle">C</text>

    <text x="10" y="100">freq=3:</text>
    <rect x="70" y="88" width="60" height="24" fill="#0d1117" stroke="#8b949e"/><text x="100" y="104" text-anchor="middle">A</text>

    <text x="10" y="150" fill="#f0883e">minFrequency = 1 -&gt; points at the freq=1 bucket</text>
    <text x="10" y="170" fill="#8b949e">bucket order within freq=2: B before C (B used less recently)</text>
    <text x="10" y="190" fill="#f0883e">next eviction (if full): remove D (only key at minFrequency=1)</text>
  </g>
</svg>

Keys grouped by frequency; `minFrequency` always tracks where the next eviction will happen.

## 5. Runnable example

```java
// LFUCache.java
import java.util.*;

public class LFUCache {

    // Basic: an LFU cache using frequency buckets, each an insertion-ordered LinkedHashSet for tie-breaking by recency.
    static class Cache {
        int capacity;
        int minFrequency = 0;
        Map<Integer, Integer> keyToValue = new HashMap<>();
        Map<Integer, Integer> keyToFreq = new HashMap<>();
        Map<Integer, LinkedHashSet<Integer>> freqToKeys = new HashMap<>();

        Cache(int capacity) { this.capacity = capacity; }

        void touch(int key) {
            int freq = keyToFreq.get(key);
            freqToKeys.get(freq).remove(key);
            if (freqToKeys.get(freq).isEmpty()) {
                freqToKeys.remove(freq);
                if (minFrequency == freq) minFrequency++;
            }
            keyToFreq.put(key, freq + 1);
            freqToKeys.computeIfAbsent(freq + 1, k -> new LinkedHashSet<>()).add(key);
        }

        int get(int key) {
            if (!keyToValue.containsKey(key)) return -1;
            touch(key);
            return keyToValue.get(key);
        }

        void put(int key, int value) {
            if (capacity == 0) return;
            if (keyToValue.containsKey(key)) {
                keyToValue.put(key, value);
                touch(key);
                return;
            }
            if (keyToValue.size() == capacity) {
                int evictKey = freqToKeys.get(minFrequency).iterator().next();
                freqToKeys.get(minFrequency).remove(evictKey);
                if (freqToKeys.get(minFrequency).isEmpty()) freqToKeys.remove(minFrequency);
                keyToValue.remove(evictKey);
                keyToFreq.remove(evictKey);
            }
            keyToValue.put(key, value);
            keyToFreq.put(key, 1);
            freqToKeys.computeIfAbsent(1, k -> new LinkedHashSet<>()).add(key);
            minFrequency = 1;
        }
    }

    static void basicLevel() {
        Cache cache = new Cache(2);
        cache.put(1, 100);
        cache.put(2, 200);
        cache.get(1);          // freq(1)=2, freq(2)=1
        cache.put(3, 300);     // evicts key 2 (lowest frequency)

        System.out.println("basic: get(2) after eviction (expect -1) -> " + cache.get(2));
        System.out.println("basic: get(1) (expect 100) -> " + cache.get(1));
        System.out.println("basic: get(3) (expect 300) -> " + cache.get(3));
    }

    // Intermediate: tie-breaking by recency when two keys share the same lowest frequency.
    static void intermediateLevel() {
        Cache cache = new Cache(2);
        cache.put(1, 10); // freq(1)=1
        cache.put(2, 20); // freq(2)=1, both tied at freq=1
        cache.put(3, 30); // evicts key 1 (same freq as 2, but 1 was inserted/used first -> less recent)

        System.out.println("intermediate: get(1) after eviction (expect -1) -> " + cache.get(1));
        System.out.println("intermediate: get(2) (expect 20, survived tie) -> " + cache.get(2));
    }

    // Advanced: a longer sequence mixing gets and puts, tracking frequency growth explicitly.
    static void advancedLevel() {
        Cache cache = new Cache(3);
        cache.put(1, 1);
        cache.put(2, 2);
        cache.put(3, 3);
        cache.get(1); cache.get(1); // freq(1) = 3
        cache.get(2);               // freq(2) = 2
        // freq(3) still = 1, lowest -> next insert evicts key 3
        cache.put(4, 4);

        System.out.println("advanced: get(3) after eviction (expect -1) -> " + cache.get(3));
        System.out.println("advanced: get(1) (expect 1, highest frequency, survived) -> " + cache.get(1));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java LFUCache.java`

## 6. Walkthrough

Create a cache with `capacity = 2`. `put(1, 100)`: key `1` is new, so `keyToFreq[1] = 1`, added to the `freq=1` bucket, and `minFrequency = 1`. `put(2, 200)`: same, key `2` also lands in the `freq=1` bucket alongside `1`.

Call `get(1)`. Found in the map, so `touch(1)` runs: remove `1` from the `freq=1` bucket (it becomes empty, but `2` is still there so `minFrequency` stays); `keyToFreq[1]` becomes `2`; add `1` to the `freq=2` bucket. Now `freq=1` holds `{2}`, `freq=2` holds `{1}`.

Call `put(3, 300)`. Cache is full (`2` items, capacity `2`). Evict from the bucket at `minFrequency = 1`, which holds `{2}` — evict key `2`. Insert `3` fresh at frequency `1`, and reset `minFrequency` to `1`.

Now `get(2)` correctly returns `-1` (evicted), while `get(1)` (frequency `2`, never evicted) and `get(3)` (freshly inserted) both succeed.

**Complexity.** `get` and `put`: `O(1)` — every step (map lookups, `LinkedHashSet` add/remove, bucket lookups) is constant time. Space: `O(capacity)`.

## 7. Gotchas & takeaways

> Forgetting to update `minFrequency` when a bucket becomes empty is the most common LFU bug — it leaves `minFrequency` pointing at a bucket with no keys, and the next eviction either crashes or silently picks the wrong key. Always check "did this bucket just become empty, and was it the minimum?" on every `touch`.

- LFU is more complex to implement correctly than LRU, precisely because of the extra bucket-and-minFrequency bookkeeping — reach for it only when access frequency genuinely matters more than recency for your workload.
- A `LinkedHashSet` (or an ordered doubly linked list) inside each frequency bucket is what gives the tie-break "least recently used within this frequency" behavior — a plain `HashSet` would pick an arbitrary tied key instead.
- LFU has a known weakness: an item that was extremely popular in the past but has stopped being used can still occupy a high-frequency bucket indefinitely, resisting eviction long after it stopped being useful ("cache pollution") — some production systems add frequency decay over time to address this.
