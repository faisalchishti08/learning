---
card: system-design
gi: 94
slug: consistent-hashing-virtual-nodes
title: Consistent hashing & virtual nodes
---

## 1. What it is

**Consistent hashing** arranges shards on a conceptual ring of hash values (0 to some maximum), instead of using a fixed `hash(key) % numShards` formula. A key is placed on the first shard found by walking clockwise from the key's own hash position on the ring. Adding or removing a shard only moves the keys between that shard and its neighbor on the ring, not every key in the system. **Virtual nodes** improve this further by placing each physical shard at many points around the ring (not just one), which spreads load more evenly and makes rebalancing smoother.

## 2. Why & when

Plain [hash-based sharding](0091-hash-based-sharding.md) with `hash(key) % numShards` has a serious flaw: changing `numShards` changes the modulo result for almost every key, forcing nearly all data to move. Consistent hashing solves exactly this problem, so use it whenever a system expects to add or remove shards over its lifetime — which is nearly every growing distributed system, including databases like Cassandra and DynamoDB, and load balancers distributing requests across changing sets of servers.

## 3. Core concept

- **The ring:** imagine hash values laid out on a circle from `0` to `MAX`. Both shards and keys are hashed onto positions on this same circle.
- **Placement rule:** a key belongs to the first shard whose position is reached by moving clockwise from the key's position.
- **Adding a shard:** insert its position on the ring. Only the keys between the new shard's position and the previous shard (going counter-clockwise) move to it — every other key's shard is unaffected.
- **Removing a shard:** its keys move to the next shard clockwise. Again, only that one segment moves.
- **The uneven-ring problem:** with only one point per shard, some shards can end up owning a much bigger arc of the ring than others, by chance, causing load imbalance.
- **Virtual nodes fix this:** each physical shard is hashed onto many points on the ring (e.g. 100 virtual points per shard), so its total owned arc-length averages out close to `1/numShards` of the ring, no matter how the random hash positions fall.

## 4. Diagram

```
                    Ring (hash space 0..359, drawn as a clock face)

              0/360
          Key "a" (hash 10)
               |
    Shard C(340) *        * Shard A (30)
                            \
                             \
   Shard B (250) *            (walk clockwise from key "a"'s
                             /  position 10 -> first shard found
                            /   going clockwise is Shard A at 30)
              * Shard D (160)

  Adding Shard E at position 20: only keys between position
  340 (Shard C) and 20 now move to Shard E; Shards A, B, D untouched.
```
*Caption: only the ring segment next to a change moves; every other shard's keys stay exactly where they were.*

## 5. Runnable example

**Level 1 — Basic.** Place shards on a ring and route keys to the first shard clockwise.

**Level 2 — Adding a shard.** Add one new shard position and count how few keys move, compared to plain modulo hashing.

**Level 3 — Virtual nodes.** Give each shard multiple ring positions and compare load balance to one-position-per-shard.

```java
// ConsistentHashing.java
import java.util.*;

public class ConsistentHashing {

    static int hashOf(String s) { return Math.abs(s.hashCode()) % 360; } // ring of 360 positions

    static String routeKey(TreeMap<Integer, String> ring, String key) {
        int h = hashOf(key);
        Map.Entry<Integer, String> entry = ring.ceilingEntry(h); // first shard clockwise
        if (entry == null) entry = ring.firstEntry(); // wrap around the ring
        return entry.getValue();
    }

    public static void main(String[] args) {
        // Level 1: three shards placed on the ring by their own hash.
        TreeMap<Integer, String> ring = new TreeMap<>();
        ring.put(hashOf("shardA"), "shardA");
        ring.put(hashOf("shardB"), "shardB");
        ring.put(hashOf("shardC"), "shardC");

        List<String> keys = new ArrayList<>();
        for (int i = 1; i <= 12; i++) keys.add("key-" + i);

        Map<String, String> before = new HashMap<>();
        for (String k : keys) before.put(k, routeKey(ring, k));
        System.out.println("routing with 3 shards: " + before);

        // Level 2: add shardD - count how many keys change shard.
        ring.put(hashOf("shardD"), "shardD");
        int moved = 0;
        for (String k : keys) {
            String newShard = routeKey(ring, k);
            if (!newShard.equals(before.get(k))) moved++;
        }
        System.out.println("keys that moved after adding shardD: " + moved + " out of " + keys.size());
        System.out.println("(plain modulo hashing would move almost all of them - see hash-based sharding)");

        // Level 3: virtual nodes - give each of 2 shards 50 positions and check load balance.
        TreeMap<Integer, String> vnodeRing = new TreeMap<>();
        String[] shards = {"shardX", "shardY"};
        for (String shard : shards) {
            for (int v = 0; v < 50; v++) {
                vnodeRing.put(hashOf(shard + "#vnode" + v), shard);
            }
        }
        Map<String, Integer> loadCount = new TreeMap<>();
        for (int i = 1; i <= 10_000; i++) {
            String shard = routeKey(vnodeRing, "key-" + i);
            loadCount.merge(shard, 1, Integer::sum);
        }
        System.out.println("load with 50 virtual nodes per shard (2 shards, 10,000 keys): " + loadCount);
        System.out.println("-> close to a 50/50 split, thanks to many ring positions per shard");
    }
}
```

**How to run:** save as `ConsistentHashing.java`, then run `java ConsistentHashing.java`.

## 6. Walkthrough

1. `ring` is a `TreeMap`, keeping shard positions sorted by their hash value; `routeKey` finds the first shard at or after a key's hash using `ceilingEntry`, wrapping to `firstEntry` if the key's hash is past the last shard — this is "walk clockwise from the key".
2. Level 1 routes 12 keys across 3 shards and records the result in `before`.
3. Level 2 inserts `shardD` at its own hash position, then re-routes the same 12 keys. Only the keys whose position falls between `shardD` and its counter-clockwise neighbor change shard — the printed `moved` count is small, nowhere near all 12.
4. Level 3 builds a second ring where `shardX` and `shardY` each get 50 ring positions (virtual nodes) instead of one, then routes 10,000 keys.
5. The resulting `loadCount` comes out close to an even 50/50 split between the two shards — with only one position per shard, random placement could easily give one shard a much larger arc; many virtual nodes per shard average that randomness out.

## 7. Gotchas & takeaways

> Gotcha: consistent hashing with too few virtual nodes per shard can still leave a noticeably uneven ring, since a shard's single random position might land in a way that gives it a much larger or smaller arc than its fair share. More virtual nodes reduce this variance but add memory and lookup overhead — production systems commonly use somewhere between 100 and a few hundred virtual nodes per physical shard.

- Consistent hashing places shards and keys on a shared ring, so adding or removing a shard only moves the keys in the affected ring segment.
- This fixes plain hash-based sharding's expensive full-reshuffle problem when the shard count changes.
- Virtual nodes give each physical shard many ring positions, smoothing out load imbalance that a single position per shard can suffer from.
- Related concepts: [Hash-based sharding](0091-hash-based-sharding.md) (the plain modulo approach this replaces), [Rebalancing & resharding](0096-rebalancing-resharding.md) (the operational process of actually moving the affected keys' data).
