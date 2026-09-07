---
card: system-design
gi: 95
slug: hot-spots-skew
title: Hot spots & skew
---

## 1. What it is

A **hot spot** is a shard that receives far more traffic or data than the others, becoming a bottleneck even though the rest of the system has spare capacity. **Skew** is the underlying uneven distribution of keys or load that causes a hot spot — some values (or some shards) simply attract much more activity than others. A hot spot is the symptom; skew is the cause.

## 2. Why & when

You need to recognize hot spots because sharding only helps if load actually spreads across shards; a single overloaded shard behaves like a bottleneck for the whole system, no matter how many other shards sit idle. Skew shows up in several common ways: a sequential key under range sharding sends all new writes to the last shard (see [range-based sharding](0090-range-based-sharding.md)); a celebrity user or viral post gets far more reads than typical rows; or one tenant is simply much bigger than the others (see [geo / entity-based sharding](0093-geo-entity-based-sharding.md)). Watch for hot spots any time real-world data is not uniformly distributed — which is most of the time.

## 3. Core concept

- **Write skew:** caused by a monotonically increasing key (timestamp, auto-increment id) under range sharding — every new row goes to the same shard.
- **Read skew:** a small number of keys (a viral post, a celebrity's profile) get read far more often than the rest, overloading whichever shard holds them, even if data is otherwise evenly spread.
- **Size skew:** one logical group (a whale tenant, a popular region) has far more data or requests than others, even with a fair partitioning scheme.
- **Detecting it:** monitor request count and data volume per shard; a shard consistently far above the average is a hot spot.
- **Common fixes:**
  - **Salting the key:** append a random or rotating suffix to a hot key so its writes/reads spread across several shards, then merge results on read.
  - **Caching:** put a cache in front of hot read keys so most reads never reach the shard at all.
  - **Splitting the hot key further:** sub-shard a single overloaded entity by an additional attribute.
  - **Replication for hot reads:** replicate a hot row to multiple shards so reads can be served by any of them.

## 4. Diagram

```
Load per shard, without a fix:

  Shard 0  [############                    ]  low load
  Shard 1  [##                              ]  low load
  Shard 2  [##############################  ]  HOT SPOT (celebrity user's posts)
  Shard 3  [###                             ]  low load

  Fix: salt the celebrity's key -> writes/reads spread across
  Shard 2a, 2b, 2c (three salted copies), reader merges results:

  Shard 2a [##########]  Shard 2b [##########]  Shard 2c [##########]
```
*Caption: a single hot key overloads one shard; salting it into several sub-keys spreads the same load across multiple shards.*

## 5. Runnable example

**Level 1 — Basic.** Simulate skewed access counts across shards and detect which one is a hot spot.

**Level 2 — Salting.** Split a single hot key into several salted sub-keys, spreading its writes.

**Level 3 — Merged reads.** Read all salted sub-keys back and merge them into the original key's total.

```java
// HotSpotDemo.java
import java.util.*;

public class HotSpotDemo {

    public static void main(String[] args) {
        // Level 1: simulate access counts per key, mostly small, one key very popular (skew).
        Map<String, Integer> accessCounts = new LinkedHashMap<>();
        accessCounts.put("post-1", 50);
        accessCounts.put("post-2", 30);
        accessCounts.put("post-viral", 100_000); // one viral post dominates
        accessCounts.put("post-4", 20);

        int total = accessCounts.values().stream().mapToInt(Integer::intValue).sum();
        for (var e : accessCounts.entrySet()) {
            double share = 100.0 * e.getValue() / total;
            System.out.printf("%s: %,d accesses (%.1f%% of total)%n", e.getKey(), e.getValue(), share);
        }
        String hotKey = accessCounts.entrySet().stream()
            .max(Map.Entry.comparingByValue()).orElseThrow().getKey();
        System.out.println("detected hot spot key: " + hotKey);

        // Level 2: salt the hot key into 4 sub-keys, so writes spread across shards.
        int numSalts = 4;
        Map<String, Integer> saltedWrites = new TreeMap<>();
        int viralWrites = 100_000;
        for (int i = 0; i < viralWrites; i++) {
            String saltedKey = hotKey + "#" + (i % numSalts); // round-robin across salts
            saltedWrites.merge(saltedKey, 1, Integer::sum);
        }
        System.out.println("writes per salted sub-key: " + saltedWrites);
        System.out.println("-> each salted shard now handles roughly 1/" + numSalts + " of the original load");

        // Level 3: reading the hot key means reading all salts and summing them back together.
        int mergedTotal = saltedWrites.values().stream().mapToInt(Integer::intValue).sum();
        System.out.println("merged read total for '" + hotKey + "': " + mergedTotal + " (matches original " + viralWrites + ")");
    }
}
```

**How to run:** save as `HotSpotDemo.java`, then run `java HotSpotDemo.java`.

## 6. Walkthrough

1. `accessCounts` models four keys with wildly uneven popularity; the loop prints each key's share of total access, showing `post-viral` at roughly 99.8% of all traffic — an extreme skew.
2. The `max` stream call finds `post-viral` as the detected hot spot, the key any monitoring on real shard load would also flag.
3. Level 2 salts that one key into 4 sub-keys (`post-viral#0` through `post-viral#3`) using round-robin, and tallies how many writes land under each salted sub-key.
4. The printed `saltedWrites` map shows the 100,000 writes now split roughly evenly across 4 sub-keys — each one small enough for its own shard to handle comfortably.
5. Level 3 sums all four salted sub-key counts back together, and the result matches the original `100,000` — showing a read for "how popular is this post" still gets the right total, it just now requires reading (and merging) several shards instead of one.

## 7. Gotchas & takeaways

> Gotcha: salting fixes write and simple count-read hot spots, but it makes every read for that key more expensive, since the reader must now query every salt and merge the results, instead of reading one row from one shard. Only salt keys that are actually hot; salting every key by default adds needless read overhead everywhere.

- A hot spot is an overloaded shard; skew is the underlying uneven data or access pattern that causes it.
- Common causes are sequential keys, unusually popular individual keys, and naturally larger entities (tenants, regions).
- Salting, caching, further splitting, and targeted replication are the standard fixes, each trading extra read complexity for spread-out load.
- Related concepts: [Range-based sharding](0090-range-based-sharding.md) (a common source of write skew), [Geo / entity-based sharding](0093-geo-entity-based-sharding.md) (a common source of size skew).
