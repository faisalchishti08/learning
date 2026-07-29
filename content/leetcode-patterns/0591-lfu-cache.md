---
card: leetcode-patterns
gi: 591
slug: lfu-cache
title: LFU Cache
---

## 1. What it is

Design an `LFUCache` class with a fixed `capacity`. `get(key)` returns the value for `key` (or `-1` if absent) and increases its use count by one. `put(key, value)` inserts or updates a key (also increasing its use count) and, if this exceeds `capacity`, evicts the **least frequently used** (LFU) key; if several keys tie for the lowest use count, evict the **least recently used** (LRU) among that tied group. Both methods must run in O(1) average time. Example: `capacity=2`; `put(1,1)`, `put(2,2)`, `get(1)` → `1` (count(1)=2), `put(3,3)` evicts key `2` (count(2)=1 is the lowest), `get(2)` → `-1`.

## 2. Why & when

This extends [LRU Cache](0576-lru-cache.md)'s eviction rule from "oldest by time" to "lowest use count, tie-broken by oldest by time" — a strictly harder ordering to maintain in O(1). The key realization is that you do not need one global recency order (as LRU does); you need, for **each distinct frequency count**, its own LRU-ordered group, plus a way to instantly find the group with the current minimum frequency.

## 3. Core concept

**Key idea:** maintain three maps. `keyToValue` (key → value) and `keyToFreq` (key → its current use count) are simple lookups. `freqToKeys` (frequency count → an ordered structure of keys at that count, ordered by recency, e.g. a `LinkedHashSet`) groups keys by frequency; within each group, order still matters for the LRU tie-break. A single integer, `minFreq`, tracks the smallest frequency currently in use, so eviction never needs to search for it.

**Steps:**
1. `get(key)`: if absent, return `-1`. Otherwise, look up its value, then call a shared "touch" step (below) to bump its frequency, and return the value.
2. `put(key, value)`: if `key` already exists, update its value and "touch" it (bump frequency) — no eviction needed. Otherwise, if at `capacity`, evict: find `freqToKeys[minFreq]`'s least-recently-used key (the front of that group, since `LinkedHashSet` preserves insertion order), remove it from all three maps. Then insert the new key with frequency `1`, and set `minFreq = 1` (a brand-new key always starts the new minimum).
3. **Touch(key):** remove `key` from `freqToKeys[oldFreq]`; if that group becomes empty and `oldFreq == minFreq`, increment `minFreq` (the old minimum group is now empty, so the minimum must rise). Increment `keyToFreq[key]`. Add `key` to `freqToKeys[newFreq]` (at the end, marking it as most-recently-used within its new frequency group).

**Why `minFreq` only ever needs to increment during a touch, never decrease:** a touch always *increases* a key's frequency by exactly one, moving it out of its old frequency group and into the next one up. The only way the minimum frequency can rise is if the old minimum's group becomes completely empty — and a fresh `put` of a brand-new key always resets `minFreq` back down to `1`, so no other code path needs to search for a smaller minimum.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="freqToKeys groups keys by their use count, each group internally LRU-ordered, with minFreq pointing at the eviction target group">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">freqToKeys[1] (minFreq)</text>
    <rect x="30" y="30" width="240" height="30" fill="#161b22" stroke="#f0883e"/><text x="150" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">LinkedHashSet{key=2}</text>
    <text x="530" y="20" fill="#8b949e" text-anchor="middle">freqToKeys[2]</text>
    <rect x="410" y="30" width="240" height="30" fill="#161b22" stroke="#3fb950"/><text x="530" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">LinkedHashSet{key=1}</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">put(3,3) exceeding capacity evicts freqToKeys[minFreq]'s oldest entry -&gt; key 2</text>
    <text x="350" y="140" fill="#8b949e" text-anchor="middle" font-size="11">get(1) bumped key 1 from freq 1 to freq 2, leaving freqToKeys[1] holding only key 2</text>
  </g>
</svg>

`minFreq` always points directly at the group to evict from — no scanning across frequency groups is ever needed to find the eviction target.

## 5. Runnable example

**Level 1 — Brute force.** Store `(key, value, freq, lastUsedTime)` in a list; on eviction, scan the whole list for the minimum `(freq, lastUsedTime)` pair. O(n) per eviction.

**KEY INSIGHT:** pre-grouping keys by their frequency count, each group internally ordered by recency, plus tracking the single smallest frequency in a variable, turns "find the eviction target" from an O(n) scan into an O(1) lookup — `freqToKeys[minFreq]`'s oldest entry.

**Level 2 — Optimal.** Three maps (`keyToValue`, `keyToFreq`, `freqToKeys` using `LinkedHashSet` per frequency) plus a `minFreq` field, O(1) average per call.

**Level 3 — Hardened.** Correctly increments `minFreq` only when the old minimum's group becomes empty, and correctly resets `minFreq` to `1` whenever a brand-new key is inserted via `put`.

```java
// LFUCache.java
import java.util.*;

public class LFUCache {

    private final int capacity;
    private int minFreq;
    private final Map<Integer, Integer> keyToValue = new HashMap<>();
    private final Map<Integer, Integer> keyToFreq = new HashMap<>();
    private final Map<Integer, LinkedHashSet<Integer>> freqToKeys = new HashMap<>();

    public LFUCache(int capacity) {
        this.capacity = capacity;
    }

    private void touch(int key) {
        int oldFreq = keyToFreq.get(key);
        freqToKeys.get(oldFreq).remove(key);
        if (freqToKeys.get(oldFreq).isEmpty() && minFreq == oldFreq) {
            minFreq++;
        }
        int newFreq = oldFreq + 1;
        keyToFreq.put(key, newFreq);
        freqToKeys.computeIfAbsent(newFreq, k -> new LinkedHashSet<>()).add(key);
    }

    public int get(int key) {
        if (!keyToValue.containsKey(key)) return -1;
        touch(key);
        return keyToValue.get(key);
    }

    public void put(int key, int value) {
        if (capacity <= 0) return;
        if (keyToValue.containsKey(key)) {
            keyToValue.put(key, value);
            touch(key);
            return;
        }
        if (keyToValue.size() == capacity) {
            int evictKey = freqToKeys.get(minFreq).iterator().next(); // oldest in the min-freq group
            freqToKeys.get(minFreq).remove(evictKey);
            keyToValue.remove(evictKey);
            keyToFreq.remove(evictKey);
        }
        keyToValue.put(key, value);
        keyToFreq.put(key, 1);
        freqToKeys.computeIfAbsent(1, k -> new LinkedHashSet<>()).add(key);
        minFreq = 1;
    }

    public static void main(String[] args) {
        LFUCache cache = new LFUCache(2);
        cache.put(1, 1);
        cache.put(2, 2);
        System.out.println(cache.get(1)); // 1, freq(1) becomes 2
        cache.put(3, 3);                  // evicts key 2 (freq 1 is the minimum)
        System.out.println(cache.get(2)); // -1
        System.out.println(cache.get(3)); // 3
    }
}
```

**How to run:** save as `LFUCache.java`, then run `java LFUCache.java`.

## 6. Walkthrough

Trace `capacity=2`; `put(1,1)`, `put(2,2)`, `get(1)`, `put(3,3)`:

| call | keyToFreq | freqToKeys | minFreq | note |
|---|---|---|---|---|
| put(1,1) | {1:1} | {1:{1}} | 1 | — |
| put(2,2) | {1:1, 2:1} | {1:{1,2}} | 1 | — |
| get(1) | {1:2, 2:1} | {1:{2}, 2:{1}} | 1 | touch(1): moved from freq 1 to 2; freqToKeys[1] still has key 2, so minFreq stays 1 |
| put(3,3) | evict freqToKeys[1]'s oldest (key 2); {1:2, 3:1} | {1:{3}, 2:{1}} | 1 | evict key 2; insert key 3 at freq 1, minFreq reset to 1 |

After `put(3,3)`: key `2` is evicted since `freqToKeys[minFreq=1]` held only key `2` at that point; key `1` (freq 2) is untouched. `get(2)` afterward correctly returns `-1`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to reset `minFreq = 1` at the end of inserting a brand-new key in `put` leaves `minFreq` pointing at a stale (possibly higher, possibly empty) group — since every new key starts at frequency `1`, `minFreq` must always become `1` immediately after such an insert.

- Signal: "evict by lowest frequency, tie-broken by recency" is the frequency-grouped-LRU signal — group keys by count first, LRU-order within each group second.
- `LinkedHashSet` (not `HashSet`) is required per frequency group, since it preserves insertion order, giving the LRU tie-break within a frequency for free via `iterator().next()`.
- Related problems: LRU Cache (the simpler recency-only version this problem extends).
