---
card: system-design
gi: 92
slug: directory-based-sharding
title: Directory-based sharding
---

## 1. What it is

**Directory-based sharding** looks up each key's shard in an explicit lookup table (the "directory"), instead of computing it from a formula like a range check or a hash. The directory is itself a small, fast data store mapping `key -> shardId` (or `keyGroup -> shardId`) directly. Think of it as a phone operator who checks a switchboard list for exactly which line to connect you to, rather than working it out from your name.

## 2. Why & when

Use directory-based sharding when you need full control over exactly where each piece of data lives — for example, to move one specific customer's data to a dedicated shard for compliance reasons, or to rebalance load by moving only a few hot keys, without touching a formula that affects every key at once. It is more flexible than range or hash sharding because moving one key only means updating one row in the directory, not recomputing a range boundary or rehashing everything. The cost is the directory itself: every request now needs an extra lookup, and the directory must be fast, and highly available, since it sits in front of every query.

## 3. Core concept

- **The directory:** a mapping table, often a small and heavily cached key-value store, e.g. `{"cust-42": shard3, "cust-99": shard1, ...}`.
- **Lookup-then-route:** every request first asks the directory "which shard owns this key?", then sends the actual query to that shard.
- **Arbitrary placement:** unlike range or hash sharding, any key can be placed on any shard, for any reason — load balancing, compliance (data residency), or isolating a noisy customer onto their own shard.
- **Fine-grained rebalancing:** moving load off an overloaded shard means updating only the directory entries for the keys you choose to move, then migrating just those rows — not the whole shard's range or every hashed key.
- **New failure point:** the directory becomes critical infrastructure. If it is slow or unavailable, no query can be routed at all, so it is usually replicated and cached aggressively.

## 4. Diagram

```
                +----------------------+
   Query for    |      Directory       |
   "cust-42" -> | cust-42 -> Shard 3   | -> route actual query to Shard 3
                | cust-99 -> Shard 1   |
                | cust-7  -> Shard 3   |
                +----------------------+

  Rebalance: move cust-7 off overloaded Shard 3 ->
  update ONE row: cust-7 -> Shard 2. No range or hash formula touched.
```
*Caption: every request is routed by a table lookup, not a formula — so moving one key is a one-row update.*

## 5. Runnable example

**Level 1 — Basic.** Build a directory map from key to shard, and route a lookup through it.

**Level 2 — Targeted rebalancing.** Move a single hot key to a different shard by updating only its directory entry.

**Level 3 — Directory-driven isolation.** Give one customer a dedicated shard, and confirm no other key is affected.

```java
// DirectorySharding.java
import java.util.*;

public class DirectorySharding {

    static final Map<String, Integer> directory = new HashMap<>();

    static int routeKey(String key) {
        Integer shard = directory.get(key);
        if (shard == null) throw new NoSuchElementException("key not in directory: " + key);
        return shard;
    }

    public static void main(String[] args) {
        // Level 1: initial placement, decided freely (not by a formula).
        directory.put("cust-42", 3);
        directory.put("cust-99", 1);
        directory.put("cust-7", 3);
        directory.put("cust-15", 1);

        System.out.println("cust-42 routes to shard " + routeKey("cust-42"));
        System.out.println("cust-7 routes to shard " + routeKey("cust-7"));

        // Level 2: shard 3 is overloaded (2 keys); move only cust-7 off it.
        System.out.println("before rebalance, shard 3 holds: cust-42, cust-7");
        directory.put("cust-7", 2); // single-row update, no formula recomputation
        System.out.println("cust-7 now routes to shard " + routeKey("cust-7"));
        System.out.println("cust-42 still routes to shard " + routeKey("cust-42") + " (untouched)");

        // Level 3: give a sensitive customer a fully dedicated shard for isolation.
        directory.put("cust-compliance-1", 9); // shard 9 reserved solely for this customer
        System.out.println("cust-compliance-1 isolated on shard " + routeKey("cust-compliance-1"));
        System.out.println("all other keys unaffected: cust-99 -> " + routeKey("cust-99")
            + ", cust-15 -> " + routeKey("cust-15"));
    }
}
```

**How to run:** save as `DirectorySharding.java`, then run `java DirectorySharding.java`.

## 6. Walkthrough

1. `directory` starts with four keys pointing at shards `3`, `1`, `3`, `1` — placements chosen directly, not derived from a range or a hash.
2. `routeKey("cust-42")` and `routeKey("cust-7")` both look up the map and return `3`, confirming both keys currently live on the same shard.
3. Because shard 3 now holds two keys and is treated as overloaded, the program updates only `cust-7`'s directory entry to point at shard `2` — a single map write, with no recomputation of any formula.
4. Re-routing `cust-7` now returns `2`, while `cust-42` still returns `3` unchanged — proof that moving one key did not disturb any other key's placement.
5. Finally, `cust-compliance-1` is placed on a dedicated shard `9`, and the other keys (`cust-99`, `cust-15`) are re-checked to confirm they still route exactly where they did before — directory-based sharding lets you make one-off placement decisions without any ripple effect.

## 7. Gotchas & takeaways

> Gotcha: the directory sits in front of every single query, so if it is slow, unavailable, or its own storage becomes a bottleneck, the entire system stops routing requests. Production directories are usually small, heavily replicated, and cached at every application server to avoid becoming a single point of failure.

- Directory-based sharding routes by an explicit lookup table, giving full, arbitrary control over where each key lives.
- Moving or isolating individual keys costs one directory update, not a range split or a full rehash.
- The directory itself becomes critical shared infrastructure and must be fast and highly available.
- Related concepts: [Range-based sharding](0090-range-based-sharding.md) and [Hash-based sharding](0091-hash-based-sharding.md) (formula-based alternatives with less flexibility), [Rebalancing & resharding](0096-rebalancing-resharding.md) (the general problem directory sharding makes easier for individual keys).
