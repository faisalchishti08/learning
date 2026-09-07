---
card: system-design
gi: 90
slug: range-based-sharding
title: Range-based sharding
---

## 1. What it is

**Range-based sharding** assigns rows to shards based on which contiguous range of the partition key's values they fall into. If the key is a user id, shard 1 might hold ids 1–1,000,000, shard 2 holds 1,000,001–2,000,000, and so on. It is like splitting a phone book into physical volumes by last-name range: "A–F", "G–M", "N–S", "T–Z".

## 2. Why & when

Use range-based sharding when your queries commonly need a contiguous range of keys — for example, "all events between 9am and 10am", or "all users with ids 1 to 100". Because keys near each other in value live on the same shard, a range query can be served by a small number of shards instead of scanning all of them. Avoid it when the partition key's write pattern is not evenly spread across its value range — for example, an auto-incrementing id or a timestamp — because every new row lands on the same "latest" shard, creating a hot spot.

## 3. Core concept

- **Shard map:** a table listing which key range belongs to which shard, e.g. `[1–1M) -> shard0`, `[1M–2M) -> shard1`.
- **Routing:** to find a row, look up its key in the shard map and go directly to that shard. No need to ask every shard.
- **Range queries are cheap:** `WHERE id BETWEEN 500000 AND 600000` touches only the shard(s) covering that range.
- **Growth means splitting a range:** when one shard grows too large, its range is split into two smaller ranges, each moved to (or kept as) its own shard. This requires updating the shard map and moving data — see [Rebalancing & resharding](0096-rebalancing-resharding.md).
- **The hot-spot risk:** if keys are monotonically increasing (auto-increment ids, timestamps), all new writes land in the highest range, overloading one shard while others sit idle. See [Hot spots & skew](0095-hot-spots-skew.md).

## 4. Diagram

```
Shard map:
  [    1 -  1,000,000)  ->  Shard 0
  [1,000,001 - 2,000,000)  ->  Shard 1
  [2,000,001 - 3,000,000)  ->  Shard 2

Query: SELECT * FROM users WHERE id BETWEEN 1,500,000 AND 1,600,000

  Router looks up range -> only Shard 1 is contacted:

  Shard 0            Shard 1 (queried)         Shard 2
  [idle]             [range scan here]         [idle]
```
*Caption: a range query touches only the shard(s) whose key range overlaps the query — the other shards are never contacted.*

## 5. Runnable example

**Level 1 — Basic.** Build a shard map of key ranges, and route a single key lookup to its shard.

**Level 2 — Range query.** Route a range query to only the shards that overlap it.

**Level 3 — Hot-spot exposure.** Show how a monotonically increasing key concentrates all new writes on one shard.

```java
// RangeSharding.java
import java.util.*;

public class RangeSharding {

    record Range(long lo, long hiExclusive, int shardId) {
        boolean contains(long key) { return key >= lo && key < hiExclusive; }
        boolean overlaps(long qLo, long qHi) { return lo < qHi && qLo < hiExclusive; }
    }

    static final List<Range> shardMap = List.of(
        new Range(1, 1_000_001, 0),
        new Range(1_000_001, 2_000_001, 1),
        new Range(2_000_001, 3_000_001, 2)
    );

    static int routeKey(long key) {
        for (Range r : shardMap) if (r.contains(key)) return r.shardId();
        throw new IllegalArgumentException("key out of range: " + key);
    }

    static List<Integer> routeRange(long qLo, long qHi) {
        List<Integer> shards = new ArrayList<>();
        for (Range r : shardMap) if (r.overlaps(qLo, qHi)) shards.add(r.shardId());
        return shards;
    }

    public static void main(String[] args) {
        // Level 1: single-key lookup.
        System.out.println("key 1,500,000 routes to shard " + routeKey(1_500_000));

        // Level 2: range query touches only overlapping shards.
        System.out.println("range [1,500,000, 1,600,000) routes to shards " + routeRange(1_500_000, 1_600_000));
        System.out.println("range [900,000, 2,100,000) routes to shards " + routeRange(900_000, 2_100_000));

        // Level 3: monotonically increasing key -> hot spot.
        Map<Integer, Integer> writesPerShard = new TreeMap<>();
        long nextId = 2_900_000; // near the top of the current range
        for (int i = 0; i < 5; i++) {
            int shard = routeKey(nextId);
            writesPerShard.merge(shard, 1, Integer::sum);
            nextId++; // auto-increment: every new row's key is higher than the last
        }
        System.out.println("writes per shard for 5 consecutive auto-increment inserts: " + writesPerShard);
        System.out.println("-> all 5 writes land on shard 2 alone, the other shards get none: a hot spot");
    }
}
```

**How to run:** save as `RangeSharding.java`, then run `java RangeSharding.java`.

## 6. Walkthrough

1. `shardMap` lists three contiguous, non-overlapping key ranges, each pointing to one shard id.
2. `routeKey(1_500_000)` scans the map and returns `1`, because `1,500,000` falls inside shard 1's range — this models a single-row lookup going directly to one shard.
3. `routeRange(1_500_000, 1_600_000)` returns only `[1]`, since that whole query range sits inside shard 1. `routeRange(900_000, 2_100_000)` returns `[0, 1, 2]`, since that wider range spans all three shards — a query is only ever sent to the shards it actually overlaps.
4. The Level 3 loop inserts 5 rows with consecutive, increasing keys (`2,900,000` upward), simulating an auto-increment primary key. Every single one routes to shard 2, because increasing keys always fall into the highest range.
5. The final map (`{2=5}`) shows all five writes concentrated on one shard — this is the hot-spot problem range-based sharding creates when the key grows monotonically instead of being spread across the key space.

## 7. Gotchas & takeaways

> Gotcha: range-based sharding is excellent for range queries but terrible for monotonically increasing keys, because every new row is written to whichever shard currently owns the highest range. If your key is a timestamp or an auto-increment id, consider [hash-based sharding](0091-hash-based-sharding.md) instead, or a key design that spreads writes (e.g. prefixing with a random or reversed component).

- Range-based sharding keeps a shard map of contiguous key ranges, and routes both single-key lookups and range queries directly to the shard(s) that own the relevant range.
- It makes range queries cheap because they touch only a few shards, not all of them.
- It creates a hot spot when the key increases monotonically, because all new writes land on the same "latest" shard.
- Related concepts: [Hash-based sharding](0091-hash-based-sharding.md) (spreads writes evenly, but loses cheap range queries), [Rebalancing & resharding](0096-rebalancing-resharding.md) (how a shard map's ranges are split as data grows).
