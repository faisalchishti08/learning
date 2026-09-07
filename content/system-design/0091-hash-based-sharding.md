---
card: system-design
gi: 91
slug: hash-based-sharding
title: Hash-based sharding
---

## 1. What it is

**Hash-based sharding** decides a row's shard by running its partition key through a hash function, then taking the result modulo the number of shards: `shard = hash(key) % numShards`. Because a good hash function scatters similar or sequential keys across very different output values, rows land on shards in an evenly spread, unpredictable pattern — unlike range-based sharding, where nearby keys stay together.

## 2. Why & when

Use hash-based sharding when your write pattern would otherwise create a hot spot with range-based sharding — for example, an auto-incrementing id or a timestamp, where every new row's key is higher than the last. Hashing spreads those sequential keys uniformly across every shard, so no single shard absorbs all new writes. The trade-off: because the hash scrambles key order, a range query ("all ids between 100 and 200") can no longer be served by a few shards — it must be sent to every shard, since rows in that range are now scattered everywhere.

## 3. Core concept

- **Hash function:** takes the key (e.g. a `userId` string) and produces a number, e.g. via `key.hashCode()` or a cryptographic hash like MD5.
- **Modulo routing:** `shardId = hash(key) % numShards` picks one of `numShards` shards.
- **Even distribution:** a good hash function spreads outputs roughly uniformly, so shards get roughly equal row counts even if the input keys were sequential.
- **The resharding problem:** if you change `numShards` (say from 4 to 5), the modulo result changes for almost every key, meaning almost every row must move to a different shard. This is the central weakness hash sharding must solve — see [Consistent hashing & virtual nodes](0094-consistent-hashing-virtual-nodes.md).
- **No cheap range queries:** since hashing destroys key ordering, a range scan must fan out to every shard and merge results, unlike range-based sharding.

## 4. Diagram

```
numShards = 4

  key "user-1"  -> hash = 91  -> 91 % 4 = 3  -> Shard 3
  key "user-2"  -> hash = 44  -> 44 % 4 = 0  -> Shard 0
  key "user-3"  -> hash = 77  -> 77 % 4 = 1  -> Shard 1
  key "user-4"  -> hash = 12  -> 12 % 4 = 0  -> Shard 0

  Sequential keys (user-1, user-2, user-3, user-4) land on DIFFERENT,
  unpredictable shards - no hot spot, but "give me user-1..user-4 in
  order" now needs all 4 shards, not one contiguous range.
```
*Caption: hashing scatters sequential keys evenly across shards, trading away cheap range scans for even write distribution.*

## 5. Runnable example

**Level 1 — Basic.** Hash a set of sequential keys and route each to a shard using modulo.

**Level 2 — Even distribution.** Insert many sequential keys and count rows per shard, comparing to the range-sharding hot spot.

**Level 3 — Resharding pain.** Change `numShards` and show how many keys move to a different shard as a result.

```java
// HashSharding.java
import java.util.*;

public class HashSharding {

    static int routeKey(String key, int numShards) {
        int h = Math.abs(key.hashCode());
        return h % numShards;
    }

    public static void main(String[] args) {
        // Level 1: route a few sequential keys.
        for (int i = 1; i <= 4; i++) {
            String key = "user-" + i;
            System.out.println(key + " -> shard " + routeKey(key, 4));
        }

        // Level 2: distribution over many sequential inserts (contrast with range sharding's hot spot).
        int numShards = 4;
        Map<Integer, Integer> counts = new TreeMap<>();
        for (int i = 1; i <= 10_000; i++) {
            int shard = routeKey("user-" + i, numShards);
            counts.merge(shard, 1, Integer::sum);
        }
        System.out.println("row counts per shard for 10,000 sequential inserts: " + counts);
        System.out.println("-> roughly even across all shards, unlike range sharding's single hot shard");

        // Level 3: resharding from 4 to 5 shards - count how many keys change shard.
        int oldShards = 4, newShards = 5;
        int moved = 0;
        for (int i = 1; i <= 10_000; i++) {
            String key = "user-" + i;
            if (routeKey(key, oldShards) != routeKey(key, newShards)) moved++;
        }
        System.out.println("keys that must move when going from " + oldShards + " to " + newShards + " shards: "
            + moved + " out of 10,000 (" + (moved / 100) + "%)");
    }
}
```

**How to run:** save as `HashSharding.java`, then run `java HashSharding.java`.

## 6. Walkthrough

1. `routeKey` hashes the key's string with `hashCode()`, takes the absolute value to avoid a negative result, then applies `% numShards` to pick a shard.
2. Level 1 routes `"user-1"` through `"user-4"` — four sequential keys — and prints their shards, which land in a scattered, non-sequential order (unlike range sharding, where they would stay adjacent).
3. Level 2 inserts 10,000 sequential keys and tallies how many land on each of 4 shards. The counts come out close to 2,500 each, showing the hash spreads sequential writes evenly instead of piling them onto one shard.
4. Level 3 recomputes every key's shard under `numShards = 5` instead of `4`, and counts how many keys now get a *different* answer than before.
5. The result shows the vast majority of keys move to a new shard purely because the shard count changed — this is the expensive resharding problem that plain modulo hashing has, and that consistent hashing is designed to avoid.

## 7. Gotchas & takeaways

> Gotcha: plain `hash(key) % numShards` makes adding or removing a shard extremely expensive, because almost every key's target shard changes at once, forcing a near-total data reshuffle. Production systems that expect to grow their shard count use [consistent hashing](0094-consistent-hashing-virtual-nodes.md) instead, which moves only a small fraction of keys per resize.

- Hash-based sharding spreads writes evenly, fixing the hot-spot problem that sequential keys cause under range-based sharding.
- It gives up cheap range queries: since key order is scrambled, a range scan must contact every shard.
- Changing the shard count under plain modulo hashing reshuffles almost all data — a serious operational cost.
- Related concepts: [Range-based sharding](0090-range-based-sharding.md) (the opposite trade-off), [Consistent hashing & virtual nodes](0094-consistent-hashing-virtual-nodes.md) (fixes the resharding cost).
