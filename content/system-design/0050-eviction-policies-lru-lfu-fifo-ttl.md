---
card: system-design
gi: 50
slug: eviction-policies-lru-lfu-fifo-ttl
title: "Eviction policies (LRU, LFU, FIFO, TTL)"
---

## 1. What it is

An **eviction policy** is the rule a cache uses to decide which entry to remove when it is full and a new entry needs space. **LRU** (Least Recently Used) evicts the entry that has not been accessed for the longest time. **LFU** (Least Frequently Used) evicts the entry accessed the fewest times. **FIFO** (First In, First Out) evicts the oldest entry by insertion order, regardless of access. **TTL** (Time To Live) evicts an entry once a fixed amount of time has passed since it was stored, regardless of how popular it is.

## 2. Why & when

A cache always has a fixed memory budget, so it must have a rule for what to drop once that budget is full — this choice directly determines the cache's hit rate. LRU is the most common general-purpose default because recently used data tends to be used again soon. LFU suits access patterns with a small set of consistently hot keys. FIFO is the simplest and cheapest to implement, useful when recency and frequency do not matter. TTL is used whenever data has a natural freshness window, such as an authentication token or a stock price.

## 3. Core concept

**LRU:** every access (read or write) moves an entry to the "most recently used" end of an ordering. When the cache is full, the entry at the "least recently used" end is evicted. This is typically implemented with a hash map for O(1) lookup plus a doubly linked list for O(1) reordering — Java's `LinkedHashMap` supports this directly with its access-order mode.

**LFU:** each entry keeps a hit counter. When full, the entry with the lowest counter is evicted. LFU can be slower to adapt: a key that was popular yesterday but is cold today can keep a high count and resist eviction, unless the policy also decays old counts over time.

**FIFO:** entries are evicted purely by insertion order, in a simple queue. It ignores whether an entry was just accessed, which is both its main weakness (a hot entry can be evicted right after being read) and its appeal (no bookkeeping on every access).

**TTL:** independent of the other three, TTL evicts on elapsed time rather than on space pressure. It is often combined with one of the others — for example, an LRU cache where entries also expire after a fixed TTL even if they stay popular.

## 4. Diagram

```
Capacity = 3. Access order shown left (most recent) to right (least recent).

LRU:  access A -> [A]
      access B -> [B, A]
      access C -> [C, B, A]
      access A -> [A, C, B]     (A moves to the front on access)
      insert D -> evict B (least recently used) -> [D, A, C]

FIFO: insert A, B, C -> [A, B, C] (insertion order)
      access A does NOT change order
      insert D -> evict A (oldest by insertion, regardless of access) -> [B, C, D]
```
*Caption: LRU reorders on every access; FIFO never reorders, so a just-read entry can still be the next one evicted.*

## 5. Runnable example

**Level 1 — Basic.** An LRU cache built on `LinkedHashMap`'s access-order mode, capped at a fixed capacity.

**Level 2 — FIFO comparison.** The same capacity and insertion sequence, but with insertion order instead of access order, showing a different eviction result.

**Level 3 — LFU.** A frequency-counting cache that evicts the least-used entry, demonstrating a third outcome from the same access pattern.

```java
// EvictionPolicies.java
import java.util.LinkedHashMap;
import java.util.Map;

public class EvictionPolicies {

    // Level 1: LRU via LinkedHashMap's access-order constructor flag.
    static class LruCache<K, V> extends LinkedHashMap<K, V> {
        private final int capacity;
        LruCache(int capacity) {
            super(16, 0.75f, true); // true = order by access, not insertion
            this.capacity = capacity;
        }
        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity; // evict the least-recently-used entry
        }
    }

    // Level 2: FIFO, plain insertion order, never reordered on access.
    static class FifoCache<K, V> extends LinkedHashMap<K, V> {
        private final int capacity;
        FifoCache(int capacity) {
            super(16, 0.75f, false); // false = insertion order
            this.capacity = capacity;
        }
        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity;
        }
    }

    // Level 3: LFU, evicts the lowest hit count.
    static class LfuCache<K, V> {
        private final int capacity;
        private final Map<K, V> values = new java.util.HashMap<>();
        private final Map<K, Integer> hits = new java.util.HashMap<>();
        LfuCache(int capacity) { this.capacity = capacity; }

        V get(K key) {
            if (values.containsKey(key)) hits.merge(key, 1, Integer::sum);
            return values.get(key);
        }
        void put(K key, V value) {
            if (!values.containsKey(key) && values.size() >= capacity) {
                K leastUsed = hits.entrySet().stream()
                    .min(Map.Entry.comparingByValue()).get().getKey();
                values.remove(leastUsed);
                hits.remove(leastUsed);
            }
            values.put(key, value);
            hits.merge(key, 1, Integer::sum);
        }
    }

    public static void main(String[] args) {
        LruCache<String, Integer> lru = new LruCache<>(3);
        lru.put("A", 1); lru.put("B", 2); lru.put("C", 3);
        lru.get("A"); // A becomes most-recently-used
        lru.put("D", 4); // evicts B, the least recently used
        System.out.println("LRU after inserting D: " + lru.keySet());

        FifoCache<String, Integer> fifo = new FifoCache<>(3);
        fifo.put("A", 1); fifo.put("B", 2); fifo.put("C", 3);
        fifo.get("A"); // access does NOT change FIFO order
        fifo.put("D", 4); // evicts A, the oldest by insertion
        System.out.println("FIFO after inserting D: " + fifo.keySet());

        LfuCache<String, Integer> lfu = new LfuCache<>(3);
        lfu.put("A", 1); lfu.put("B", 2); lfu.put("C", 3);
        lfu.get("A"); lfu.get("A"); lfu.get("B"); // A:3 hits, B:2 hits, C:1 hit
        lfu.put("D", 4); // evicts C, the least frequently used
        System.out.println("LFU after inserting D: " + lfu.values.keySet());
    }
}
```

**How to run:** save as `EvictionPolicies.java`, then run `java EvictionPolicies.java`.

## 6. Walkthrough

1. In `lru`, inserting `A`, `B`, `C` fills the cache to capacity `3`. Calling `lru.get("A")` moves `A` to the most-recently-used position, leaving `B` as the least recently used.
2. Inserting `D` triggers `removeEldestEntry`, which evicts `B` — the result is `[C, A, D]` in access order, and `B` is gone.
3. In `fifo`, the same insertions and the same `get("A")` call happen, but access never changes FIFO's order — it only tracks insertion order.
4. Inserting `D` into `fifo` evicts `A`, the oldest inserted entry, even though `A` was just read — proving FIFO ignores recency entirely.
5. In `lfu`, after two extra reads of `A` and one of `B`, the hit counts are `A:3, B:2, C:1` (each `put` also counts as a hit). Inserting `D` evicts `C`, the entry with the lowest count.
6. The same access pattern produces three different survivors (`B` evicted under LRU, `A` evicted under FIFO, `C` evicted under LFU) — the policy you choose directly changes what stays cached.

## 7. Gotchas & takeaways

> Gotcha: LFU can trap a key that was popular only briefly — a viral post from yesterday can keep a high hit count and resist eviction long after it stops being read, unless the policy decays counts over time.

- LRU is the safest general-purpose default: it adapts automatically to changing access patterns with O(1) bookkeeping per access.
- FIFO is the cheapest to implement but can evict hot data purely because it happened to be inserted early.
- TTL is orthogonal to the other three and is usually combined with one of them for data that must expire regardless of popularity.
- Related concepts: [Refresh-ahead cache](0049-refresh-ahead-cache.md) (builds on TTL expiry), [Hot keys & key distribution](0052-hot-keys-key-distribution.md) (what happens when one key dominates access, regardless of eviction policy).
